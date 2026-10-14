import json
import re
from math import floor

from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import serializers

from llm.services.client import generate, get_client
from participants.models import Feedback, Participant
from sessions.models import AttendanceRecord, ProgrammeSession
from users.models import Branch
from ..prompts.acc import SYSTEM_PROMPT, SECTION_TITLES, build_acc_prompt
from .attendance import attendance_statistics
from .physical import physical_statistics
from .scope import resolve_report_scope


def acc_feedback(*, user, start_date, end_date, branch_id=None):
    if user.role != "super_admin":
        raise PermissionDenied("Only super admins can prepare ACC reports.")
    branch_id = resolve_report_scope(user, start_date, end_date, branch_id)
    sources = Feedback.objects.filter(consent=True, date__range=(start_date, end_date))
    if branch_id is not None:
        sources = sources.filter(branch_id=branch_id)
    return sources.select_related("branch").order_by("-date", "-created_at", "pk")


def _engagement_statistics(*, start_date, end_date, branch_id):
    branches = Branch.objects.all()
    sessions = ProgrammeSession.objects.filter(date__range=(start_date, end_date))
    if branch_id is not None:
        branches = branches.filter(pk=branch_id)
        sessions = sessions.filter(branch_id=branch_id)
    # Separate branch/participant and session/attendance joins avoid multiplying counts.
    branches = branches.annotate(
        participants_count=Count("participants", filter=Q(participants__is_active=True) &
                                 (Q(participants__joined_on__lte=end_date) | Q(participants__joined_on__isnull=True))),
        new_participants=Count("participants", filter=Q(participants__joined_on__range=(start_date, end_date))),
    ).order_by("name", "pk")
    finalised = Q(attendance_finalised=True)
    attendance = {str(row["branch_id"]): row for row in sessions.order_by().values("branch_id").annotate(
        total_sessions=Count("pk", distinct=True),
        finalised_sessions=Count("pk", filter=finalised, distinct=True),
        total_roster_places=Count("attendance", filter=finalised),
        total_attendances=Count("attendance", filter=finalised & Q(attendance__status=AttendanceRecord.Status.PRESENT)),
    )}
    rows = []
    for branch in branches:
        counts = attendance.get(str(branch.pk), {})
        roster = counts.get("total_roster_places", 0)
        present = counts.get("total_attendances", 0)
        rate = 100 * present / roster if roster else None
        rows.append({
            "branch_id": str(branch.pk), "entity": branch.name, "location": branch.region.strip() or None,
            "participants": branch.participants_count, "new_participants": branch.new_participants,
            "engagement_percent": floor(rate / 5 + 0.5) * 5 if rate is not None else None,
            "total_attendances": present, "total_roster_places": roster,
            "total_sessions": counts.get("total_sessions", 0),
            "finalised_sessions": counts.get("finalised_sessions", 0),
        })
    return {
        "branches": rows,
        "limitations": [
            "Participants counts currently active registrations joined by the reporting end date; unknown joined dates are included. This is not a count of distinct attendees.",
            "Participant counts use current branch membership and active status; historical transfers and exit dates cannot be reconstructed.",
            "New participants counts recorded joined dates within the inclusive reporting period, including registrations now inactive; unknown joined dates are excluded.",
            "Engagement is attendance rate: total attendances divided by total roster places across finalised sessions, multiplied by 100. Incomplete registers are excluded; repeated session places count separately.",
            "Engagement percentages are rounded to the nearest 5 percentage points; halfway values round up. The underlying attendance counts are retained.",
            "Not available means there are no finalised roster places, not zero engagement. Location uses the branch's recorded region; missing locations are not inferred.",
            "Attendance rates describe recorded participation and do not establish reduced falls risk, improved wellbeing or programme causation.",
        ],
    }


def acc_snapshot(*, user, start_date, end_date, branch_id=None, sources, approved_for_acc_and_ai):
    eligible = {str(item.pk): item for item in acc_feedback(
        user=user, start_date=start_date, end_date=end_date, branch_id=branch_id,
    ).filter(pk__in=[source["id"] for source in sources])}
    if len(eligible) != len(sources):
        raise serializers.ValidationError("Selected feedback is outside this scope or no longer has reporting consent. Reload feedback.")
    reviewed = []
    for source in sources:
        original = eligible[str(source["id"])]
        reviewed.append({"id": f"F-{original.pk}", "feedback_id": str(original.pk),
                         "text": source["text"], "speaker": original.speaker,
                         "original_text": original.quote, "date": original.date.isoformat(),
                         "branch": original.branch.name})
    scope = dict(user=user, start_date=start_date, end_date=end_date, branch_id=branch_id)
    attendance = attendance_statistics(**scope)
    physical = physical_statistics(**scope)
    enrolled = Participant.objects.filter(joined_on__range=(start_date, end_date))
    if branch_id:
        enrolled = enrolled.filter(branch_id=branch_id)
    return {
        "scope": attendance["scope"],
        "scope_label": Branch.objects.get(pk=branch_id).name if branch_id else "All branches",
        "sources": reviewed,
        "approval": {"approved_for_acc_and_ai": approved_for_acc_and_ai, "by": str(user.pk), "at": timezone.now().isoformat()},
        "aggregates": {
            "S-engagement": _engagement_statistics(start_date=start_date, end_date=end_date,
                                                   branch_id=attendance["scope"]["branch_id"]),
            "S-attendance": {key: attendance["totals"][key] for key in (
                "total_sessions", "finalised_sessions", "incomplete_sessions", "total_attendances", "distinct_attendees")},
            "S-enrolments": {"new_enrolments": enrolled.count(),
                             "limitations": "Recorded joined dates and current branch membership; unknown joined dates are excluded. This is not a count of first-time attendees."},
            "S-physical": {key: physical[key] for key in ("totals", "metrics", "paired_changes", "limitations")},
        },
        "limitations": [
            "Attendance counts use finalised registers; total sessions also includes incomplete registers.",
            "Distinct attendees are people marked present, not a count of all enrolled participants.",
            "Only selected, consented feedback is included. It may not represent all participants or branches.",
            "Reporting copies were reviewed by the requesting super admin; speaker types were recorded with the original feedback. Unknown attribution remains unknown.",
            "This is a saved snapshot. Later changes to source records do not update the report.",
            "Engagement means recorded attendance rate, not evidence of health outcomes. The draft requires human review before use.",
        ],
    }


class QuoteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000, trim_whitespace=False)
    source_id = serializers.CharField()


class SectionSerializer(serializers.Serializer):
    title = serializers.ChoiceField(choices=SECTION_TITLES)
    text = serializers.CharField(max_length=10000)
    source_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True, max_length=104)
    quotes = QuoteSerializer(many=True, allow_empty=True)


class DraftSerializer(serializers.Serializer):
    sections = SectionSerializer(many=True, allow_empty=False, max_length=6)
    review_notes = serializers.ListField(child=serializers.CharField(max_length=2000), max_length=20)


def render_acc_draft(raw, snapshot):
    output = DraftSerializer(data=json.loads(raw))
    output.is_valid(raise_exception=True)
    draft = output.validated_data
    sources = {source["id"]: source["text"] for source in snapshot["sources"]}
    allowed = set(sources) | set(snapshot["aggregates"])
    titles = [section["title"] for section in draft["sections"]]
    if len(set(titles)) != len(titles):
        raise ValueError("Duplicate report sections.")
    if not any(section["source_ids"] for section in draft["sections"]):
        raise ValueError("ACC draft has no sections with source references.")
    parts = ["Draft for human review."]
    def citation(source_id):
        return f"[{source_id}](#acc-source-{source_id})"
    for section in draft["sections"]:
        if not section["source_ids"]:
            # Do not publish uncited prose, even if it looks like a missing-data note.
            draft["review_notes"].append(f"{section['title']}: section omitted because the AI supplied no source references.")
            continue
        if not set(section["source_ids"]) <= allowed:
            raise ValueError("Unknown source in ACC draft.")
        if not section["quotes"]:
            raise ValueError("ACC section has no supporting quotations.")
        parts.append(f"## {section['title']}\n\n**Supporting quotations**")
        for quote in section["quotes"]:
            text = quote["text"]
            if not text.strip() or quote["source_id"] not in sources or text not in sources[quote["source_id"]]:
                raise ValueError("ACC quote does not match its reviewed source.")
            if quote["source_id"] not in section["source_ids"]:
                raise ValueError("ACC quote is not a supporting source for its section.")
            # Escape Markdown so punctuation in the original quote renders literally.
            escaped = re.sub(r"([\\`*_{}\[\]()<>#+.!|~-])", r"\\\1", text)
            parts.append("> " + escaped.replace("\n", "\n> ") + "\n\n" + citation(quote["source_id"]))
        parts.append(f"**Summary**\n\n{section['text']}\n\nSources: " + ", ".join(map(citation, section["source_ids"])))
    if draft["review_notes"]:
        parts.append("## Review notes\n\n" + "\n".join(f"- {note}" for note in draft["review_notes"]))
    return "\n\n".join(parts)


def explain_acc(snapshot, *, client=None, model=None):
    # Recheck consent/scope just before sending the queued snapshot to the provider.
    sources = snapshot["sources"]
    eligible = Feedback.objects.filter(consent=True, pk__in=[s["feedback_id"] for s in sources],
                                      date__range=(snapshot["scope"]["start_date"], snapshot["scope"]["end_date"]))
    if snapshot["scope"]["branch_id"]:
        eligible = eligible.filter(branch_id=snapshot["scope"]["branch_id"])
    if eligible.count() != len(sources) or not snapshot["approval"]["approved_for_acc_and_ai"]:
        raise PermissionDenied("Feedback approval changed. Prepare a new draft.")
    raw = generate(client=client if client is not None else get_client(), model=model,
                   sys_prompt=SYSTEM_PROMPT, prompt=build_acc_prompt(snapshot), max_tokens=6000, temperature=0.2)
    return render_acc_draft(raw, snapshot)
