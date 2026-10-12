import json
import re

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework import serializers

from llm.services.client import generate, get_client
from participants.models import Feedback, Participant
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
                         "text": source["text"], "speaker": source["speaker"],
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
            "Reporting copies were reviewed by the requesting super admin; speaker labels are their attribution.",
            "This is a saved snapshot. Later changes to source records do not update the report.",
            "Engagement percentages are excluded. The draft requires human review before use.",
        ],
    }


class SectionSerializer(serializers.Serializer):
    title = serializers.ChoiceField(choices=SECTION_TITLES)
    text = serializers.CharField(max_length=10000)
    source_ids = serializers.ListField(child=serializers.CharField(), allow_empty=True, max_length=103)


class QuoteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000, trim_whitespace=False)
    source_id = serializers.CharField()


class DraftSerializer(serializers.Serializer):
    sections = SectionSerializer(many=True, allow_empty=False, max_length=6)
    quotes = QuoteSerializer(many=True, max_length=4)
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
        parts.append(f"## {section['title']}\n\n{section['text']}\n\nSources: " + ", ".join(map(citation, section["source_ids"])))
    if draft["quotes"]:
        parts.append("## Supporting quotations")
    for quote in draft["quotes"]:
        text = quote["text"]
        if not text.strip() or quote["source_id"] not in sources or text not in sources[quote["source_id"]]:
            raise ValueError("ACC quote does not match its reviewed source.")
        # Escape Markdown so punctuation in the original quote renders literally.
        escaped = re.sub(r"([\\`*_{}\[\]()<>#+.!|~-])", r"\\\1", text)
        parts.append("> " + escaped.replace("\n", "\n> ") + "\n\n" + citation(quote["source_id"]))
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
                   sys_prompt=SYSTEM_PROMPT, prompt=build_acc_prompt(snapshot), max_tokens=3000, temperature=0.2)
    return render_acc_draft(raw, snapshot)
