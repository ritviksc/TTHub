"""Calculate attendance statistics independently of the optional AI narrative."""

from datetime import date

from django.db.models import Count, Q
from django.utils import timezone

from llm.services.client import generate, get_client
from reporting.prompts.attendance import SYSTEM_PROMPT, build_attendance_prompt
from sessions.models import AttendanceRecord, ProgrammeSession
from .scope import resolve_report_scope


def _session_scope(user, start_date, end_date, branch_id):
    branch_id = resolve_report_scope(user, start_date, end_date, branch_id)
    sessions = ProgrammeSession.objects.filter(date__range=(start_date, end_date))
    if branch_id is not None:
        sessions = sessions.filter(branch_id=branch_id)
    return sessions, branch_id


def _empty_totals():
    return {
        "total_sessions": 0,
        "finalised_sessions": 0,
        "incomplete_sessions": 0,
        "empty_sessions": 0,
        "total_attendances": 0,
        "total_roster_places": 0,
    }


def _add_session(totals, session):
    totals["total_sessions"] += 1
    if not session["attendance_finalised"]:
        totals["incomplete_sessions"] += 1
        return
    totals["finalised_sessions"] += 1
    totals["empty_sessions"] += int(session["present"] == 0)
    totals["total_attendances"] += session["present"]
    totals["total_roster_places"] += session["roster"]


def _add_rates(totals):
    # Weight the rate by roster places, rather than averaging session percentages.
    totals["attendance_rate_percent"] = (
        round(100 * totals["total_attendances"] / totals["total_roster_places"], 2)
        if totals["total_roster_places"] else None
    )
    totals["average_attendance"] = (
        round(totals["total_attendances"] / totals["finalised_sessions"], 2)
        if totals["finalised_sessions"] else None
    )


def attendance_statistics(*, user, start_date, end_date, branch_id=None):
    """Return JSON-ready statistics for inclusive dates and authorised branches.

    Finalised zero-attendance sessions contribute to the averages. Incomplete
    sessions contribute only to session/completeness counts. Null rates mean
    there is no denominator; they do not mean zero attendance.
    """
    sessions, branch_id = _session_scope(user, start_date, end_date, branch_id)
    # Two attendance queries regardless of session count: grouped session counts
    # and a distinct-person count. Never fetch an entire register per session.
    rows = list(sessions.order_by("date", "id").values(
        "id", "date", "attendance_finalised",
    ).annotate(
        present=Count("attendance", filter=Q(attendance__status=AttendanceRecord.Status.PRESENT)),
        roster=Count("attendance"),
    ))
    totals = _empty_totals()
    buckets = {}
    month = start_date.replace(day=1)
    while month <= end_date:
        buckets[month.strftime("%Y-%m")] = _empty_totals()
        if month.year == end_date.year and month.month == end_date.month:
            break
        month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)

    session_summaries = []
    finalised_ids = []
    for session in rows:
        _add_session(totals, session)
        _add_session(buckets[session["date"].strftime("%Y-%m")], session)
        if session["attendance_finalised"]:
            finalised_ids.append(session["id"])
            session_summaries.append({
                "session_id": str(session["id"]),
                "date": session["date"].isoformat(),
                "present": session["present"],
                "roster": session["roster"],
            })

    totals["distinct_attendees"] = AttendanceRecord.objects.filter(
        session_id__in=finalised_ids, status=AttendanceRecord.Status.PRESENT,
    ).values("participant_id").distinct().count()
    _add_rates(totals)
    monthly = []
    previous = None
    for month, values in buckets.items():
        _add_rates(values)
        # Missing finalised data is not evidence of a decrease to zero.
        comparable = previous is not None and previous["finalised_sessions"] and values["finalised_sessions"]
        values["attendances_change"] = (
            values["total_attendances"] - previous["total_attendances"] if comparable else None
        )
        current_rate = values["attendance_rate_percent"]
        previous_rate = previous["attendance_rate_percent"] if previous else None
        values["attendance_rate_change_percentage_points"] = (
            round(current_rate - previous_rate, 2)
            if comparable and current_rate is not None and previous_rate is not None else None
        )
        monthly.append({"month": month, **values})
        previous = values

    return {
        "generated_at": timezone.now().isoformat(),
        "scope": {
            "branch_id": str(branch_id) if branch_id is not None else None,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "totals": totals,
        "sessions": session_summaries,
        "monthly": monthly,
        "limitations": [
            "Incomplete registers are counted but excluded from attendance calculations.",
            "Finalised sessions with zero attendees are included, including sessions with no roster.",
            "Attendance rate uses roster places across finalised sessions; null means no denominator.",
            "Monthly buckets cover only dates in the selected range; boundary months may be partial.",
            "Changes describe recorded attendance, not causes or programme effectiveness.",
            "This is a live-data report; later edits or deletions can change subsequent results.",
        ],
    }


def analyse_attendance(*, user, start_date, end_date, branch_id=None, client=None, model=None):
    """Return statistics and an AI explanation; provider failures propagate.

    Call attendance_statistics directly for dashboards or reports without AI.
    No provider request is made when there are no finalised sessions to analyse.
    """
    statistics = attendance_statistics(
        user=user, start_date=start_date, end_date=end_date, branch_id=branch_id,
    )
    return {
        "statistics": statistics,
        "narrative": explain_attendance(statistics, client=client, model=model),
    }


def explain_attendance(statistics, *, client=None, model=None):
    """Explain a fixed statistics snapshot, whether called by a task or a test."""
    if not statistics["totals"]["finalised_sessions"]:
        return None
    return generate(
        client=client if client is not None else get_client(),
        prompt=build_attendance_prompt(statistics),
        sys_prompt=SYSTEM_PROMPT,
        model=model,
        max_tokens=1000,
        temperature=0.2,
    )
