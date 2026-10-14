"""Demo dataset that gives every feature a year of realistic data.

Five branches with staff, participants (with photos and consent), weekly
sessions and attendance, quarterly physical assessments, feedback of every
shape, documents and folders, custom reporting quarters and saved report
history. It covers the last 365 days plus a few weeks of upcoming sessions,
which is enough to prepare a yearly ACC report.

`seed_reporting_demo` is a separate, smaller fixture with stable IDs; this
command does not touch it. Fixed text and the folder layout live in
`participants/management/seed_content.py`.
"""
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.utils import timezone

from documents.models import Document, Folder
from participants.management import seed_content as content
from participants.models import Feedback, Participant
from physical_tests.models import Assessment, ExerciseResult
from physical_tests.serializers import BALANCE, GroupSerializer
from reporting.models import ACCAnalysisJob, AttendanceAnalysisJob, PhysicalAnalysisJob
from reporting.services.attendance import attendance_statistics
from reporting.services.physical import physical_statistics
from sessions.models import AttendanceRecord, ProgrammeSession
from users.models import Branch, BranchQuarter, UserAccount
from users.quarters import QuarterYearSerializer

NAMESPACE = uuid5(NAMESPACE_URL, "cosc345-seed-test-data")
PASSWORD = "TestPass123!"
PHOTO_DIR = Path(__file__).resolve().parent.parent / "seed_photos"
DAYS_BACK = 365
UPCOMING_DAYS = 21
BATCH_SIZE = 2000

ABSENCE_REASON_WEIGHTS = [
    (AttendanceRecord.AbsenceReason.NO_SHOW, 0.33),
    (AttendanceRecord.AbsenceReason.MEDICAL_APPOINTMENT, 0.32),
    (AttendanceRecord.AbsenceReason.TRANSPORT_ISSUE, 0.2),
    (AttendanceRecord.AbsenceReason.OTHER, 0.1),
    ("", 0.05),  # absent with no reason recorded
]

ROLE_LABELS = dict(UserAccount.Role.choices)


def seed_id(*parts):
    return uuid5(NAMESPACE, "/".join(parts))


def walk_tree(tree, path, years):
    """Yield ("folder" | "file", path, name, parent_path) for a document tree."""
    for name in tree.get("_files", []):
        yield "file", f"{path}/{name}", name, path
    for key, subtree in tree.items():
        if key == "_files":
            continue
        name = key.format(**years)
        folder_path = f"{path}/{name}"
        yield "folder", folder_path, name, path
        yield from walk_tree(subtree, folder_path, years)


class Command(BaseCommand):
    help = (
        "Seed five branches with a year of staff, participants, sessions, attendance, "
        "assessments, feedback, documents, quarters and report history "
        "(requires ALLOW_DEMO_SEEDING=True). Use --reset to wipe and reseed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete everything belonging to the seeded branches and accounts first, then reseed.",
        )
        parser.add_argument(
            "--seed", type=int, default=345,
            help="Random seed, for reproducible output (default: 345).",
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DEMO_SEEDING:
            raise CommandError("Demo seeding is disabled. Set ALLOW_DEMO_SEEDING=True to enable it.")
        self.photos = {
            "female": [PHOTO_DIR / name for name in content.FEMALE_PHOTOS],
            "male": [PHOTO_DIR / name for name in content.MALE_PHOTOS],
        }
        missing = [path.name for paths in self.photos.values() for path in paths if not path.exists()]
        if missing:
            raise CommandError(f"Missing participant photos in {PHOTO_DIR}: {', '.join(missing)}")

        self.rng = random.Random(options["seed"])
        self.today = timezone.localdate()
        self.start = self.today - timedelta(days=DAYS_BACK)
        self.years = {"year": self.today.year, "last_year": self.today.year - 1}
        self.cycles = {}
        self.login_rows = []

        try:
            with transaction.atomic():
                if options["reset"]:
                    self._reset()
                elif Branch.objects.filter(pk__in=self._branch_ids()).exists():
                    raise CommandError(
                        "Seeded data already exists. Re-run with --reset to wipe it and seed again."
                    )
                self._check_email_clashes()
                self._seed()
        except ProtectedError as exc:
            raise CommandError(
                "Could not reset: records outside the seeded data still point at it "
                f"({len(exc.protected_objects)} protected object(s))."
            ) from exc

    # -- IDs and helpers -------------------------------------------------------

    def _branch_ids(self):
        return [seed_id("branch", slug) for slug, *_ in content.BRANCHES]

    def _super_admin_ids(self):
        return [seed_id("staff", key) for key, _, _ in content.SUPER_ADMINS]

    def _org_ids(self):
        folders, files = [], []
        for kind, path, _, _ in walk_tree(content.ORG_TREE, "org", self.years):
            (folders if kind == "folder" else files).append(seed_id("folder" if kind == "folder" else "document", path))
        return folders, files

    def _at(self, day, hour=10, minute=0):
        return timezone.make_aware(datetime.combine(day, time(hour, minute)))

    def _cycle(self, name, pool):
        """Hand out items from a pool in shuffled order, reshuffling when it runs out."""
        queue = self.cycles.get(name)
        if not queue:
            queue = list(pool)
            self.rng.shuffle(queue)
            self.cycles[name] = queue
        return queue.pop()

    def _weighted(self, weights):
        roll = self.rng.random()
        total = 0
        for value, weight in weights:
            total += weight
            if roll <= total:
                return value
        return weights[-1][0]

    def _random_day(self, first, last):
        return first + timedelta(days=self.rng.randint(0, max(0, (last - first).days)))

    @staticmethod
    def _on_staff(staff, day):
        """Staff who still worked at the branch on a given day."""
        return [s for s in staff if s.left_on is None or day < s.left_on] or staff[:1]

    @staticmethod
    def _enrolled(participant, day, *, upcoming=False):
        """Whether a participant was on the branch roster on a given day."""
        if participant.joined_on and participant.joined_on > day:
            return False
        if participant.is_active:
            return True
        return not upcoming and participant.left_on is not None and day < participant.left_on

    def _check_email_clashes(self):
        emails = [f"{key}@example.com" for key, _, _ in content.SUPER_ADMINS]
        for slug, *_ in content.BRANCHES:
            emails += [f"{role}{n}.{slug}@example.com" for role in ("manager", "instructor") for n in range(1, 5)]
        clashes = UserAccount.objects.filter(email__in=emails).values_list("email", flat=True)
        if clashes:
            raise CommandError(
                "These emails already belong to accounts this command did not create: "
                + ", ".join(sorted(clashes))
            )

    # -- Reset -----------------------------------------------------------------

    def _reset(self):
        # Scoped strictly to our own uuid5 IDs and everything attached to the
        # seeded branches. Never match on names: a real database may have
        # unrelated branches or staff with the same names.
        branch_ids = self._branch_ids()
        if not Branch.objects.filter(pk__in=branch_ids).exists():
            self.stdout.write("Nothing to reset.")
            return
        staff_ids = list(UserAccount.objects.filter(
            Q(branch_id__in=branch_ids) | Q(pk__in=self._super_admin_ids())
        ).values_list("pk", flat=True))
        in_branches = Q(branch_id__in=branch_ids)

        Feedback.objects.filter(in_branches | Q(recorded_by_id__in=staff_ids)).delete()

        org_folder_ids, org_document_ids = self._org_ids()
        self._delete_documents(Document.objects.filter(
            in_branches | Q(participant__branch_id__in=branch_ids) | Q(pk__in=org_document_ids)
        ))
        self._delete_folders(Folder.objects.filter(in_branches | Q(pk__in=org_folder_ids)))

        for job_model in (AttendanceAnalysisJob, PhysicalAnalysisJob, ACCAnalysisJob):
            job_model.objects.filter(in_branches | Q(requested_by_id__in=staff_ids)).delete()

        ExerciseResult.objects.filter(recorded_by_id__in=staff_ids).delete()
        Assessment.objects.filter(
            in_branches | Q(participant__branch_id__in=branch_ids) | Q(recorded_by_id__in=staff_ids)
        ).delete()
        ProgrammeSession.objects.filter(in_branches | Q(created_by_id__in=staff_ids)).delete()
        AttendanceRecord.objects.filter(participant__branch_id__in=branch_ids).delete()

        participants = Participant.objects.filter(in_branches)
        for participant in participants:
            if participant.photo:
                participant.photo.delete(save=False)
            if participant.gp_consent_document:
                participant.gp_consent_document.delete(save=False)
        participants.delete()

        UserAccount.objects.filter(pk__in=staff_ids).delete()
        Branch.objects.filter(pk__in=branch_ids).delete()  # quarters cascade
        self.stdout.write(f"Reset the seeded branches and {len(staff_ids)} staff account(s).")

    def _delete_documents(self, queryset):
        documents = list(queryset)
        for document in documents:
            document.file.delete(save=False)
        Document.objects.filter(pk__in=[d.pk for d in documents]).delete()

    def _delete_folders(self, queryset):
        # Include any subfolders someone added inside a seeded folder, then
        # delete from the leaves up because Folder.parent is PROTECT.
        ids = set(queryset.values_list("pk", flat=True))
        frontier = set(ids)
        while frontier:
            frontier = set(Folder.objects.filter(parent_id__in=frontier).values_list("pk", flat=True)) - ids
            ids |= frontier
        self._delete_documents(Document.objects.filter(folder_id__in=ids))
        while ids:
            leaves = set(Folder.objects.filter(pk__in=ids).exclude(children__pk__in=ids).values_list("pk", flat=True))
            if not leaves:
                break
            Folder.objects.filter(pk__in=leaves).delete()
            ids -= leaves

    # -- Seed ------------------------------------------------------------------

    def _seed(self):
        manager_names = self.rng.sample(content.MANAGER_FIRST_NAMES, len(content.MANAGER_FIRST_NAMES))
        instructor_names = self.rng.sample(content.INSTRUCTOR_FIRST_NAMES, len(content.INSTRUCTOR_FIRST_NAMES))

        super_admins = [
            self._staff(key, first, last, UserAccount.Role.SUPER_ADMIN, None)
            for key, first, last in content.SUPER_ADMINS
        ]

        summaries = []
        managers_by_slug = {}
        for slug, name, region, size, manager_count, instructor_count in content.BRANCHES:
            branch = Branch.objects.create(pk=seed_id("branch", slug), name=name, region=region)
            managers = [
                self._staff(f"manager{n}.{slug}", manager_names.pop(), self.rng.choice(content.LAST_NAMES),
                            UserAccount.Role.BRANCH_MANAGER, branch)
                for n in range(1, manager_count + 1)
            ]
            instructors = [
                self._staff(f"instructor{n}.{slug}", instructor_names.pop(), self.rng.choice(content.LAST_NAMES),
                            UserAccount.Role.INSTRUCTOR, branch)
                for n in range(1, instructor_count + 1)
            ]
            if slug == content.DEACTIVATED_INSTRUCTOR_BRANCH:
                # Ran classes for the first part of the year, then left.
                instructors.append(self._staff(
                    f"instructor{instructor_count + 1}.{slug}", instructor_names.pop(),
                    self.rng.choice(content.LAST_NAMES), UserAccount.Role.INSTRUCTOR, branch,
                    left_on=self.today - timedelta(days=150),
                ))
            managers_by_slug[slug] = managers

            participants = self._participants(branch, slug, size, instructors)
            sessions, present_by_session = self._sessions(branch, instructors, participants)
            assessments = self._assessments(branch, participants, instructors)
            feedback = self._feedback(branch, participants, sessions, present_by_session, managers + instructors)
            documents = self._branch_documents(branch, slug, managers[0], participants, managers + instructors)
            if slug in content.CUSTOM_QUARTER_BRANCHES:
                self._quarters(branch)
            summaries.append(
                f"{name}: {len(participants)} participants, {len(sessions)} sessions, "
                f"{assessments} assessments, {feedback} feedback, {documents} documents."
            )

        org_documents = self._org_documents(super_admins[0])
        reports = self._report_history(super_admins[0], managers_by_slug)

        for line in summaries:
            self.stdout.write(line)
        self.stdout.write(f"Organisation: {org_documents} documents. Report history: {reports} saved reports.")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done. All accounts use password: {PASSWORD}"))
        self.stdout.write(f"{'Role':<16}{'Name':<26}Email")
        for role, full_name, email, note in self.login_rows:
            self.stdout.write(f"{role:<16}{full_name:<26}{email}{note}")

    # -- Staff -----------------------------------------------------------------

    def _staff(self, key, first_name, last_name, role, branch, left_on=None):
        email = f"{key}@example.com"
        account = UserAccount(
            pk=seed_id("staff", key), username=email, email=email,
            first_name=first_name, last_name=last_name, role=role, branch=branch,
            is_active=left_on is None,
        )
        account.set_password(PASSWORD)
        account.save()
        account.left_on = left_on
        self.login_rows.append((
            ROLE_LABELS[role], account.get_full_name(), email,
            "  (deactivated)" if left_on else "",
        ))
        return account

    # -- Participants ----------------------------------------------------------

    def _participants(self, branch, slug, count, instructors):
        rng = self.rng
        participants = []
        for index in range(count):
            gender = rng.choice(["female", "male"])
            first_name = rng.choice(content.FEMALE_FIRST_NAMES if gender == "female" else content.MALE_FIRST_NAMES)
            last_name = rng.choice(content.LAST_NAMES)
            # Most people were already coming before the year started; the rest
            # join through the year, so every quarter has new enrolments.
            if rng.random() < 0.6:
                joined_on = self.start - timedelta(days=rng.randint(14, 700))
            else:
                joined_on = self.start + timedelta(days=rng.randint(0, DAYS_BACK - 14))
            roll = rng.random()
            tier = "complete" if roll < 0.4 else ("partial" if roll < 0.8 else "minimal")

            participant = Participant(
                pk=seed_id("participant", slug, str(index)),
                first_name=first_name, last_name=last_name, branch=branch,
                date_of_birth=self.today - timedelta(days=rng.randint(60 * 365, 92 * 365)),
                joined_on=joined_on,
            )
            if tier == "minimal":
                if rng.random() < 0.3:
                    participant.date_of_birth = None
                if rng.random() < 0.15:
                    participant.joined_on = None
            else:
                participant.email = f"{first_name.lower()}.{last_name.lower()}{index}@example.com"
                participant.phone = f"02{rng.randint(1, 9)} {rng.randint(100, 999)} {rng.randint(1000, 9999)}"
                if tier == "complete" or rng.random() < 0.5:
                    participant.emergency_contact_name = f"{rng.choice(content.FIRST_NAMES)} {last_name}"
                    participant.emergency_contact_phone = f"02{rng.randint(1, 9)} {rng.randint(100, 999)} {rng.randint(1000, 9999)}"
                if rng.random() < 0.25:
                    participant.preferred_name = first_name[:4]
                if rng.random() < 0.35:
                    participant.notes = rng.choice(content.PARTICIPANT_NOTES)

            # About 8% have since left and been deactivated (not deleted).
            participant.left_on = None
            if rng.random() < 0.08:
                earliest = max(participant.joined_on or self.start, self.start) + timedelta(days=30)
                latest = self.today - timedelta(days=14)
                if earliest < latest:
                    participant.is_active = False
                    participant.left_on = self._random_day(earliest, latest)

            self._consents_and_photo(participant, tier, gender, instructors)
            participant.save()
            participants.append(participant)
        return participants

    def _consents_and_photo(self, participant, tier, gender, instructors):
        rng = self.rng
        gp_given = tier == "complete" or (tier == "partial" and rng.random() < 0.6)
        window_start = participant.joined_on or self.start

        if gp_given:
            participant.gp_consent_given = True
            participant.gp_consent_date = min(window_start + timedelta(days=rng.randint(0, 30)), self.today)
            if tier == "complete" or rng.random() < 0.7:
                pdf = content.make_pdf("GP Consent Form", [
                    f"Participant: {participant.full_name}",
                    f"Consent date: {participant.gp_consent_date:%d %B %Y}",
                    "Cleared to take part in strength and balance classes.",
                ])
                participant.gp_consent_document.save("gp-consent.pdf", ContentFile(pdf), save=False)
                participant.gp_document_uploaded_by = rng.choice(instructors)
                participant.gp_document_uploaded_at = self._at(participant.gp_consent_date, 9)

        # Everyone has a profile photo, which the app treats as photo consent.
        # Photos repeat across participants; _cycle spreads them evenly.
        participant.photo_consent_given = True
        participant.photo_consent_date = min(window_start + timedelta(days=rng.randint(0, 30)), self.today)
        photo = self._cycle(f"photo-{gender}", self.photos[gender])
        with open(photo, "rb") as image:
            participant.photo.save(photo.name, File(image), save=False)

    # -- Sessions and attendance -------------------------------------------------

    def _sessions(self, branch, instructors, participants):
        rng = self.rng
        weekdays = rng.sample(range(5), 2 if len(participants) >= 30 else 1)
        start_times = {weekday: time(*rng.choice(content.SESSION_TIMES)) for weekday in weekdays}

        sessions = []
        day = self.start
        while day <= self.today + timedelta(days=UPCOMING_DAYS):
            if day.weekday() in weekdays and not self._christmas_break(day):
                if day < self.today - timedelta(days=10):
                    finalised = True
                elif day < self.today:
                    finalised = rng.random() < 0.5  # a few recent registers still open
                else:
                    finalised = False
                sessions.append(ProgrammeSession(
                    branch=branch, created_by=rng.choice(self._on_staff(instructors, day)),
                    date=day, time=start_times[day.weekday()],
                    activity=rng.choice(content.ACTIVITIES), attendance_finalised=finalised,
                ))
            day += timedelta(days=1)
        ProgrammeSession.objects.bulk_create(sessions)

        rates = {p.pk: rng.uniform(0.55, 0.95) for p in participants}
        present_by_session = {}
        records = []
        for session in sessions:
            upcoming = session.date > self.today
            present_by_session[session.pk] = []
            for participant in participants:
                if not self._enrolled(participant, session.date, upcoming=upcoming):
                    continue
                if upcoming:
                    # Same as the session API: one blank roster row per active participant.
                    records.append(AttendanceRecord(session=session, participant=participant))
                    continue
                rate = rates[participant.pk] - (0.1 if session.date.month in (6, 7, 8) else 0)
                if rng.random() < rate:
                    records.append(AttendanceRecord(
                        session=session, participant=participant, status=AttendanceRecord.Status.PRESENT,
                    ))
                    present_by_session[session.pk].append(participant)
                else:
                    reason = self._weighted(ABSENCE_REASON_WEIGHTS)
                    records.append(AttendanceRecord(
                        session=session, participant=participant, status=AttendanceRecord.Status.ABSENT,
                        absence_reason=reason,
                        absence_reason_other=(
                            rng.choice(content.OTHER_ABSENCE_TEXTS)
                            if reason == AttendanceRecord.AbsenceReason.OTHER else ""
                        ),
                    ))
        AttendanceRecord.objects.bulk_create(records, batch_size=BATCH_SIZE)
        return sessions, present_by_session

    @staticmethod
    def _christmas_break(day):
        return (day.month == 12 and day.day >= 20) or (day.month == 1 and day.day <= 10)

    # -- Physical assessments ------------------------------------------------

    def _assessments(self, branch, participants, instructors):
        rng = self.rng
        assessments, results = [], []
        for participant in participants:
            if rng.random() < 0.12:
                continue  # never tested, so completion rates are below 100%
            last_day = self.today if participant.is_active else participant.left_on
            if last_day is None:
                continue
            day = max(participant.joined_on or self.start, self.start) + timedelta(days=rng.randint(0, 14))
            dates = []
            while day <= last_day:
                dates.append(day)
                day += timedelta(days=rng.randint(80, 100))  # about once a quarter

            profile = {
                "step": {"improve": 1, "stable": 0, "decline": -1}[
                    rng.choices(["improve", "stable", "decline"], weights=[60, 25, 15])[0]
                ],
                "tug": rng.uniform(8, 20),
                "chair": rng.randint(5, 15),
                "balance": rng.randint(0, 3),
            }
            # A walking aid stays the same between tests so changes stay comparable.
            profile["aid"] = rng.choice(content.WALKING_AIDS) if profile["tug"] > 15 and rng.random() < 0.6 else ""

            for visit, assessed_on in enumerate(dates):
                instructor = rng.choice(self._on_staff(instructors, assessed_on))
                assessment = Assessment(
                    participant=participant, branch=branch, recorded_by=instructor,
                    assessed_on=assessed_on, completed_at=self._at(assessed_on, 11, rng.randint(0, 59)),
                )
                assessments.append(assessment)
                results += self._results(assessment, instructor, profile, visit)

            # A few people have an assessment in progress.
            if participant.is_active and dates and dates[-1] < self.today - timedelta(days=7) and rng.random() < 0.06:
                instructor = rng.choice(self._on_staff(instructors, self.today))
                draft = Assessment(
                    participant=participant, branch=branch, recorded_by=instructor,
                    assessed_on=self.today - timedelta(days=rng.randint(0, 5)),
                )
                assessments.append(draft)
                results.append(ExerciseResult(
                    assessment=draft, exercise="tug", outcome="measured",
                    value=round(profile["tug"], 2), walking_aid=profile["aid"], recorded_by=instructor,
                ))

        Assessment.objects.bulk_create(assessments, batch_size=BATCH_SIZE)
        ExerciseResult.objects.bulk_create(results, batch_size=BATCH_SIZE)
        return len(assessments)

    def _results(self, assessment, instructor, profile, visit):
        rng = self.rng
        change = profile["step"] * visit

        if rng.random() < 0.03:
            tug = {"exercise": "tug", "outcome": "unable", "value": None,
                   "notes": rng.choice(content.TUG_UNABLE_NOTES), "walking_aid": profile["aid"]}
        else:
            seconds = max(4.5, profile["tug"] - change * rng.uniform(0.4, 1.0) + rng.uniform(-0.6, 0.6))
            tug = {"exercise": "tug", "outcome": "measured", "value": round(seconds, 2), "walking_aid": profile["aid"]}

        if profile["chair"] <= 6 and visit == 0:
            chair = {"exercise": "chair", "outcome": "arms_used", "value": 0}
        elif rng.random() < 0.03:
            chair = {"exercise": "chair", "outcome": "not_attempted", "value": None,
                     "notes": rng.choice(content.CHAIR_NOT_ATTEMPTED_NOTES)}
        else:
            stands = max(1, profile["chair"] + change * rng.randint(1, 2) + rng.randint(-1, 1))
            chair = {"exercise": "chair", "outcome": "measured", "value": stands}

        # Balance stages run in order; each needs a 10-second hold to unlock the next.
        balance = []
        if rng.random() < 0.03:
            balance.append({"exercise": BALANCE[0], "outcome": "not_attempted", "value": None,
                            "notes": rng.choice(content.BALANCE_NOT_ATTEMPTED_NOTES)})
            balance += [{"exercise": e, "outcome": "skipped", "value": None} for e in BALANCE[1:]]
        else:
            level = min(4, max(0, profile["balance"] + (change + 1) // 2))
            stopped = False
            for stage, exercise in enumerate(BALANCE):
                if stopped:
                    balance.append({"exercise": exercise, "outcome": "skipped", "value": None})
                elif stage < level:
                    balance.append({"exercise": exercise, "outcome": "measured", "value": 10})
                else:
                    balance.append({"exercise": exercise, "outcome": "measured", "value": round(rng.uniform(1.5, 9.5), 2)})
                    stopped = True

        rows = []
        for group, group_rows in (("tug", [tug]), ("chair", [chair]), ("balance", balance)):
            # Check through the app's own rules so seeded results are ones staff could enter.
            serializer = GroupSerializer(data={"version": 0, "results": group_rows}, context={"group": group})
            serializer.is_valid(raise_exception=True)
            rows += [
                ExerciseResult(assessment=assessment, recorded_by=instructor, **row)
                for row in serializer.validated_data["results"]
            ]
        return rows

    # -- Feedback ----------------------------------------------------------------

    def _feedback(self, branch, participants, sessions, present_by_session, staff):
        rng = self.rng
        finalised = [s for s in sessions if s.attendance_finalised]
        items = []
        month = self.start.replace(day=1)
        while month <= self.today:
            next_month = (month + timedelta(days=32)).replace(day=1)
            first, last = max(month, self.start), min(next_month - timedelta(days=1), self.today)
            for _ in range(rng.randint(2, 4)):
                day = self._random_day(first, last)
                shape = rng.choices(["participant", "session", "both"], weights=[40, 30, 30])[0]
                participant = session = None
                if shape != "participant":
                    recent = [s for s in finalised if day - timedelta(days=14) <= s.date <= day]
                    session = rng.choice(recent) if recent else None
                    if session and shape == "both":
                        present = present_by_session[session.pk]
                        participant = rng.choice(present) if present else None
                        shape = "both" if participant else "session"
                    if session is None:
                        shape = "participant"
                if shape == "participant":
                    enrolled = [p for p in participants if self._enrolled(p, day)]
                    if not enrolled:
                        continue
                    participant = rng.choice(enrolled)

                quotes, sources = {
                    "participant": (content.PARTICIPANT_QUOTES, content.PARTICIPANT_SOURCES),
                    "session": (content.SESSION_QUOTES, content.SESSION_SOURCES),
                    "both": (content.PARTICIPANT_SESSION_QUOTES, content.PARTICIPANT_SESSION_SOURCES),
                }[shape]
                items.append(Feedback(
                    branch=branch, participant=participant, session=session,
                    quote=self._cycle(f"{branch.pk}-{shape}", quotes), source=rng.choice(sources),
                    date=day, consent=rng.random() < 0.75,
                    recorded_by=rng.choice(self._on_staff(staff, day)),
                ))
            month = next_month

        Feedback.objects.bulk_create(items)
        for item in items:
            Feedback.objects.filter(pk=item.pk).update(created_at=self._at(item.date, 15, rng.randint(0, 59)))
        return len(items)

    # -- Quarters ------------------------------------------------------------------

    def _quarters(self, branch):
        # Offset by half a month from calendar quarters, so custom and default
        # dates are easy to tell apart.
        for year in (self.today.year - 1, self.today.year):
            quarters = [
                (1, date(year, 1, 1), date(year, 4, 15)),
                (2, date(year, 4, 16), date(year, 7, 15)),
                (3, date(year, 7, 16), date(year, 10, 15)),
                (4, date(year, 10, 16), date(year, 12, 31)),
            ]
            serializer = QuarterYearSerializer(data={"quarters": [
                {"quarter": q, "start_date": s.isoformat(), "end_date": e.isoformat()} for q, s, e in quarters
            ]}, context={"year": year})
            serializer.is_valid(raise_exception=True)
            BranchQuarter.objects.bulk_create([
                BranchQuarter(branch=branch, year=year, **item) for item in serializer.validated_data["quarters"]
            ])

    # -- Documents -----------------------------------------------------------------

    def _org_documents(self, owner):
        return self._document_tree(content.ORG_TREE, "org", None, owner, "Organisation")

    def _branch_documents(self, branch, slug, owner, participants, staff):
        count = self._document_tree(content.BRANCH_TREE, f"branch/{slug}", branch, owner, branch.name)
        for participant in participants:
            if self.rng.random() < 0.15:
                for name in self.rng.sample(content.PARTICIPANT_DOCUMENTS, self.rng.randint(1, 2)):
                    self._document(
                        f"participant/{participant.pk}/{name}", name, owner=self.rng.choice(staff),
                        participant=participant, lines=[f"Participant: {participant.full_name}"],
                        earliest=participant.joined_on,
                    )
                    count += 1
        return count

    def _document_tree(self, tree, root, branch, owner, scope_label):
        folders = {root: None}
        count = 0
        for kind, path, name, parent_path in walk_tree(tree, root, self.years):
            if kind == "folder":
                folders[path] = Folder.objects.create(
                    pk=seed_id("folder", path), name=name, parent=folders[parent_path],
                    branch=branch, created_by=owner,
                )
            else:
                self._document(path, name, owner=owner, branch=branch, folder=folders[parent_path],
                               lines=[scope_label])
                count += 1
        return count

    def _document(self, key, name, *, owner, branch=None, participant=None, folder=None, lines=(), earliest=None):
        pdf = content.make_pdf(name.removesuffix(".pdf"), lines)
        document = Document(
            pk=seed_id("document", key), name=name, size=len(pdf),
            branch=branch, participant=participant, folder=folder, uploaded_by=owner,
        )
        document.file.save(name, ContentFile(pdf), save=False)
        document.save()
        uploaded = self._random_day(max(earliest or self.start, self.start), self.today)
        Document.objects.filter(pk=document.pk).update(uploaded_at=self._at(uploaded, 14, self.rng.randint(0, 59)))

    # -- Report history ------------------------------------------------------------

    def _report_history(self, admin, managers_by_slug):
        # The three most recent complete calendar quarters.
        quarter_start = date(self.today.year, 3 * ((self.today.month - 1) // 3) + 1, 1)
        ranges = []
        for _ in range(3):
            end = quarter_start - timedelta(days=1)
            quarter_start = date(end.year, 3 * ((end.month - 1) // 3) + 1, 1)
            ranges.append((quarter_start, end))

        branches = {slug: seed_id("branch", slug) for slug in content.CUSTOM_QUARTER_BRANCHES}
        count = 0
        for start, end in ranges:
            for branch_id in (None, *branches.values()):
                self._saved_report(AttendanceAnalysisJob, attendance_statistics, admin, start, end, branch_id)
                count += 1
            self._saved_report(PhysicalAnalysisJob, physical_statistics, admin, start, end, None)
            count += 1

        # A branch manager's own report, and one that failed.
        start, end = ranges[0]
        manager = managers_by_slug[content.CUSTOM_QUARTER_BRANCHES[0]][0]
        self._saved_report(PhysicalAnalysisJob, physical_statistics, manager, start, end, manager.branch_id)
        self._saved_report(AttendanceAnalysisJob, attendance_statistics, admin, start, end, None, failed=True)
        return count + 1

    def _saved_report(self, job_model, statistics_service, user, start, end, branch_id, failed=False):
        statistics = statistics_service(user=user, start_date=start, end_date=end, branch_id=branch_id)
        job = job_model.objects.create(
            requested_by=user, branch_id=branch_id, statistics=statistics, model_name="seed-demo",
            status=job_model.Status.FAILED if failed else job_model.Status.SUCCEEDED,
            narrative=None if failed else self._summary(job_model, statistics, branch_id),
            error=content.FAILED_REPORT_ERROR if failed else "",
        )
        created = self._at(min(end + timedelta(days=self.rng.randint(2, 9)), self.today), 16)
        job_model.objects.filter(pk=job.pk).update(created_at=created, expires_at=created + timedelta(minutes=15))

    def _summary(self, job_model, statistics, branch_id):
        def shown(value):
            return "n/a" if value is None else value

        scope = statistics["scope"]
        fields = {
            "scope": Branch.objects.get(pk=branch_id).name if branch_id else "All branches",
            "start": scope["start_date"], "end": scope["end_date"], "note": content.SEEDED_NOTE,
        }
        if job_model is AttendanceAnalysisJob:
            totals = statistics["totals"]
            top = max(statistics["absence_reasons"]["breakdown"], key=lambda row: row["count"])
            return content.ATTENDANCE_SUMMARY.format(
                **fields, finalised=totals["finalised_sessions"], attendances=totals["total_attendances"],
                distinct=totals["distinct_attendees"], rate=shown(totals["attendance_rate_percent"]),
                average=shown(totals["average_attendance"]), incomplete=totals["incomplete_sessions"],
                top_reason=top["label"], top_percent=shown(top["percent_of_absences"]),
            )
        totals = statistics["totals"]
        means = {row["exercise"]: row["mean"] for row in statistics["metrics"]}
        tug_pairs = next(row for row in statistics["paired_changes"] if row["exercise"] == "tug")
        return content.PHYSICAL_SUMMARY.format(
            **fields, tested=totals["tested_participants"], eligible=totals["eligible_participants"],
            completion=shown(totals["completion_percent"]), completed=totals["completed_assessments"],
            drafts=totals["draft_assessments"], tug=shown(means.get("tug")), chair=shown(means.get("chair")),
            tug_change=shown(tug_pairs["mean_change"]), tug_pairs=tug_pairs["participants"],
        )
