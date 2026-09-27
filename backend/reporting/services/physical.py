"""Physical-testing counts and paired changes, computed without an LLM."""
from collections import defaultdict
from datetime import date
from statistics import mean

from django.db.models import F, Q
from django.utils import timezone

from llm.services.client import generate, get_client
from participants.models import Participant
from physical_tests.models import Assessment, ExerciseResult
from reporting.prompts.physical import SYSTEM_PROMPT, build_physical_prompt
from .scope import resolve_report_scope

EXERCISES = list(ExerciseResult.Exercise.values)
SCORED = {"measured", "arms_used"}


def average(values):
    return round(mean(values), 2) if values else None


def metric_summary(rows):
    return [{
        "exercise": exercise,
        "count": len(values := [r["value"] for r in rows if r["exercise"] == exercise and r["outcome"] in SCORED and r["value"] is not None]),
        "mean": average(values),
        "outcomes": {outcome: sum(r["exercise"] == exercise and r["outcome"] == outcome for r in rows)
                     for outcome in ExerciseResult.Outcome.values},
    } for exercise in EXERCISES]


def paired_changes(history):
    changes = []
    for exercise in EXERCISES:
        points = [(assessment["date"], row) for assessment in history for row in assessment["results"]
                  if row["exercise"] == exercise and row["outcome"] in SCORED and row["value"] is not None]
        change = {"exercise": exercise, "first_date": None, "last_date": None, "first": None, "last": None, "change": None}
        if len(points) >= 2:
            (first_date, first), (last_date, last) = points[0], points[-1]
            comparable = (first_date != last_date and first["outcome"] == last["outcome"]
                          and (exercise != "tug" or first["walking_aid"].strip().casefold() == last["walking_aid"].strip().casefold()))
            if comparable:
                change.update(first_date=first_date, last_date=last_date, first=first["value"], last=last["value"],
                              change=round(last["value"] - first["value"], 2))
        changes.append(change)
    return changes


def physical_statistics(*, user, start_date, end_date, branch_id=None):
    branch_id = resolve_report_scope(user, start_date, end_date, branch_id)
    # A current roster report cannot reconstruct historical enrolment or transfers.
    assessments = Assessment.objects.filter(assessed_on__range=(start_date, end_date), branch_id=F("participant__branch_id"))
    people = Participant.objects.filter(Q(joined_on__lte=end_date) | Q(joined_on__isnull=True))
    if branch_id is not None:
        people = people.filter(branch_id=branch_id)
        assessments = assessments.filter(branch_id=branch_id)
    people = people.filter(Q(is_active=True) | Q(pk__in=assessments.filter(completed_at__isnull=False).values("participant_id")))
    people = list(people.select_related("branch").order_by("last_name", "first_name", "id"))
    assessments = list(assessments.filter(participant_id__in=[p.pk for p in people]).prefetch_related("results").order_by("assessed_on", "created_at", "id"))
    histories = defaultdict(list)
    drafts = defaultdict(int)
    month_rows = defaultdict(list)
    month_people = defaultdict(set)
    month_counts = defaultdict(int)
    all_results = []
    for assessment in assessments:
        if assessment.completed_at is None:
            drafts[assessment.participant_id] += 1
            continue
        results = [{"exercise": r.exercise, "outcome": r.outcome, "value": float(r.value) if r.value is not None else None,
                    "walking_aid": r.walking_aid} for r in assessment.results.all()]
        histories[assessment.participant_id].append({"id": str(assessment.pk), "date": assessment.assessed_on.isoformat(), "results": results})
        month = assessment.assessed_on.strftime("%Y-%m")
        month_rows[month].extend(results)
        month_counts[month] += 1
        month_people[month].add(assessment.participant_id)
        all_results.extend(results)
    participants = []
    for person in people:
        history = histories[person.pk]
        participants.append({"id": str(person.pk), "name": person.full_name, "branch": person.branch.name,
                             "testing_completed": bool(history), "completed_assessments": len(history),
                             "draft_assessments": drafts[person.pk], "history": history, "changes": paired_changes(history)})
    monthly = []
    month = start_date.replace(day=1)
    while month <= end_date:
        key = month.strftime("%Y-%m")
        monthly.append({"month": key, "completed_assessments": month_counts[key], "tested_participants": len(month_people[key]),
                        "metrics": metric_summary(month_rows[key])})
        if month.year == end_date.year and month.month == end_date.month:
            break
        month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
    paired = []
    for exercise in EXERCISES:
        values = [c["change"] for p in participants for c in p["changes"] if c["exercise"] == exercise and c["change"] is not None]
        paired.append({"exercise": exercise, "participants": len(values), "mean_change": average(values)})
    tested = sum(p["testing_completed"] for p in participants)
    return {
        "generated_at": timezone.now().isoformat(),
        "scope": {"branch_id": str(branch_id) if branch_id else None, "start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "totals": {"eligible_participants": len(people), "tested_participants": tested, "untested_participants": len(people) - tested,
                   "completion_percent": round(100 * tested / len(people), 2) if people else None,
                   "completed_assessments": sum(len(h) for h in histories.values()), "draft_assessments": sum(drafts.values())},
        "participants": participants, "metrics": metric_summary(all_results), "paired_changes": paired, "monthly": monthly,
        "limitations": [
            "Yes means at least one completed assessment in the inclusive selected dates; drafts are excluded from measurements.",
            "The roster includes currently active participants enrolled by the end date (unknown enrolment dates included), plus inactive participants with completed assessments in the period.",
            "This uses current branch membership; assessments recorded at a different branch before a transfer are excluded. Historical enrolment and exit dates are not fully available.",
            "Completion records an assessment outcome, not success at every exercise. Unable and skipped outcomes have no numeric value; chair stands needing arms score zero.",
            "Monthly means use all scored assessments, including repeated assessments and chair-arm zeros. The participants contributing to each month can differ.",
            "Paired changes use each person's first and last scored results on different dates within the selection. Outcomes must match; TUG walking-aid descriptions must also match. Null means no comparable pair.",
            "Changes are last minus first, in seconds or repetitions; they are descriptive, not clinical ratings or evidence of programme causation. Balance values are capped at 10 seconds.",
            "Boundary months can be partial. Live records and membership changes can change subsequent reports.",
        ],
    }


def explain_physical(statistics, *, client=None, model=None):
    if not statistics["totals"]["completed_assessments"]:
        return None
    return generate(client=client if client is not None else get_client(), prompt=build_physical_prompt(statistics),
                    sys_prompt=SYSTEM_PROMPT, model=model, max_tokens=1200, temperature=0.2)
