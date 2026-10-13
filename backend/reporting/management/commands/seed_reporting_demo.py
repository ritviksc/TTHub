"""TEMPORARY demo fixtures: use real enrolment, attendance and testing data in production."""
import random
from datetime import date, datetime, time, timedelta
from uuid import UUID, uuid5

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from participants.models import Participant
from physical_tests.models import Assessment, ExerciseResult
from physical_tests.serializers import BALANCE, GroupSerializer
from sessions.models import ProgrammeSession, AttendanceRecord
from users.models import Branch, UserAccount

NAMESPACE = UUID("987a1892-17a6-4e1f-89a2-270f96529b77")
PASSWORD = "DemoReports123!"
BRANCHES = [("harbour", "DEMO Harbour"), ("hills", "DEMO Hills")]


def demo_id(key):
    return uuid5(NAMESPACE, key)


class Command(BaseCommand):
    help = "Create clearly labelled fictional reporting data without overwriting existing records (requires ALLOW_DEMO_SEEDING=True)."

    def add_arguments(self, parser):
        parser.add_argument("--as-of", type=date.fromisoformat, help="Last session date for the initial dataset, YYYY-MM-DD; defaults to today.")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.ALLOW_DEMO_SEEDING:
            raise CommandError("Demo seeding is disabled. Set ALLOW_DEMO_SEEDING=True to enable it.")
        end = options["as_of"] or timezone.localdate()
        if end > timezone.localdate():
            raise CommandError("The demo date cannot be in the future.")
        existing = ProgrammeSession.objects.filter(pk=demo_id("harbour-session-11")).first()
        if existing:
            if options["as_of"] and end != existing.date:
                raise CommandError("This demo already exists with a different date. Existing records are preserved.")
            end = existing.date
        rng = random.Random(345)
        self.staff("admin", "super_admin", None)
        for slug, name in BRANCHES:
            branch, _ = Branch.objects.get_or_create(pk=demo_id(slug), defaults={"name": name, "region": "Fictional demo region"})
            self.staff(f"manager.{slug}", "branch_manager", branch)
            instructor = self.staff(f"instructor.{slug}", "instructor", branch)
            people = []
            for index in range(12):
                person, _ = Participant.objects.get_or_create(pk=demo_id(f"{slug}-person-{index}"), defaults={
                    "first_name": "Demo", "last_name": f"{slug.title()} {index + 1:02d}",
                    "date_of_birth": date(end.year - 55 - index * 2, 1, 15),
                    "email": f"participant.{slug}.{index + 1}@example.com", "branch": branch,
                    "joined_on": end - timedelta(days=100), "notes": "FICTIONAL reporting demonstration participant.",
                })
                people.append(person)
            for index in range(12):
                session, created = ProgrammeSession.objects.get_or_create(pk=demo_id(f"{slug}-session-{index}"), defaults={
                    "branch": branch, "created_by": instructor, "date": end - timedelta(weeks=11-index),
                    "time": time(10, 0), "activity": "DEMO — strength and balance class",
                    "attendance_finalised": index not in (9, 11),
                })
                # Advance the seeded random stream even on a rerun; existing rows are never overwritten.
                for person in people:
                    present = rng.random() < (0.45 + index * 0.03) and index != 4
                    reason = rng.choice(AttendanceRecord.AbsenceReason.values)
                    if created:
                        AttendanceRecord.objects.create(session=session, participant=person,
                            status="present" if present else "absent", absence_reason="" if present else reason,
                            absence_reason_other="Fictional demo reason" if not present and reason == "other" else "")
            for index, person in enumerate(people):
                if index < 9:
                    periods = range(3) if index < 8 else [2]
                    for period in periods:
                        day = end - timedelta(days=[70, 35, 7][period])
                        assessment, created = Assessment.objects.get_or_create(pk=demo_id(f"{slug}-assessment-{index}-{period}"), defaults={
                            "participant": person, "branch": branch, "recorded_by": instructor, "assessed_on": day,
                            "completed_at": timezone.make_aware(datetime.combine(day, time(12))),
                        })
                        if created:
                            tug = {"exercise": "tug", "outcome": "measured", "value": round(11 + index + period * (0.7 if index % 3 == 0 else -0.8), 2), "walking_aid": "Walking stick" if index % 4 == 0 else ""}
                            if index == 4 and period == 1:
                                tug.update(outcome="unable", value=None, notes="Fictional safety stop")
                            chair = {"exercise": "chair", "outcome": "arms_used" if index == 2 else "measured",
                                     "value": 0 if index == 2 else 8 + index + period * (1 if index % 3 else -1)}
                            balance = []
                            stopped = False
                            for stage, exercise in enumerate(BALANCE):
                                value = 10 if stage <= (index + period) % 4 else round(3 + period + (index % 3), 2)
                                balance.append({"exercise": exercise, "outcome": "skipped" if stopped else "measured", "value": None if stopped else value})
                                stopped = stopped or value < 10
                            for group, rows in [("tug", [tug]), ("chair", [chair]), ("balance", balance)]:
                                validation = GroupSerializer(data={"version": 0, "results": rows}, context={"group": group})
                                validation.is_valid(raise_exception=True)
                                for row in validation.validated_data["results"]:
                                    ExerciseResult.objects.create(assessment=assessment, recorded_by=instructor, **row)
                elif index == 9:
                    key = demo_id(f"{slug}-draft-{index}")
                    if not Assessment.objects.filter(participant=person, completed_at=None).exclude(pk=key).exists():
                        draft, created = Assessment.objects.get_or_create(pk=key, defaults={"participant": person, "branch": branch,
                            "recorded_by": instructor, "assessed_on": end - timedelta(days=3)})
                        if created:
                            ExerciseResult.objects.create(assessment=draft, exercise="tug", outcome="measured", value=16, recorded_by=instructor)
            self.stdout.write(f"{name}: 12 participants, 12 sessions, 25 completed assessments and one initial draft.")
        self.stdout.write(self.style.SUCCESS(f"Demo ready. Report dates: {end - timedelta(days=77)} to {end}."))
        self.stdout.write(f"New demo accounts use password: {PASSWORD}. Existing passwords are unchanged.")

    def staff(self, name, role, branch):
        email = f"demo.{name}@example.com"
        user, created = UserAccount.objects.get_or_create(pk=demo_id(f"staff-{name}"), defaults={
            "username": email, "email": email, "first_name": "Demo", "last_name": name,
            "role": role, "branch": branch,
        })
        if created:
            user.set_password(PASSWORD)
            user.save(update_fields=["password"])
        self.stdout.write(f"{role}: {user.email}")
        return user
