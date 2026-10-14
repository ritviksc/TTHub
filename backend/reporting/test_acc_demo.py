import io
from datetime import date, timedelta

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import F
from django.test import TestCase, override_settings

from participants.models import Feedback, Participant
from sessions.models import AttendanceRecord, ProgrammeSession
from users.models import Branch, UserAccount
from .management.commands.seed_reporting_demo import demo_id
from .services.acc import acc_snapshot


@override_settings(ALLOW_DEMO_SEEDING=True)
class ACCDemoTests(TestCase):
    def test_seed_adds_reportable_samples_and_preserves_existing_records_and_edits(self):
        unrelated = Branch.objects.create(name="Existing branch")
        Participant.objects.create(branch=unrelated, first_name="Existing", last_name="Person")
        end = date(2026, 3, 31)
        start = end - timedelta(weeks=11)
        call_command("seed_acc_demo", as_of=end, stdout=io.StringIO())
        self.assertEqual(Branch.objects.count(), 4)
        self.assertEqual(Participant.objects.count(), 76)
        self.assertEqual(ProgrammeSession.objects.count(), 36)
        self.assertEqual(Feedback.objects.count(), 30)
        self.assertFalse(Feedback.objects.filter(consent=False).exists())
        self.assertFalse(Feedback.objects.exclude(source__startswith="DEMO").exists())
        self.assertEqual(set(Feedback.objects.values_list('speaker', flat=True)), {'kaumātua', 'kaimahi'})
        self.assertFalse(AttendanceRecord.objects.filter(participant__joined_on__gt=F("session__date")).exists())
        for record in AttendanceRecord.objects.all():
            record.clean()
        admin = UserAccount.objects.get(pk=demo_id("staff-admin"))
        feedback = Feedback.objects.get(pk=demo_id("acc-whangarei-feedback-0"))
        snapshot = acc_snapshot(user=admin, start_date=start, end_date=end,
                                sources=[{"id": feedback.pk, "text": feedback.quote, "speaker": "participant"}],
                                approved_for_acc_and_ai=True)
        rows = {row["entity"]: row for row in snapshot["aggregates"]["S-engagement"]["branches"]}
        rates = []
        for location, count, new_count in [("Whangārei", 20, 6), ("Heretaunga", 25, 5), ("Ōtepoti", 30, 8)]:
            row = rows[f"DEMO {location}"]
            self.assertEqual(row["location"], location)
            self.assertEqual(row["participants"], count)
            self.assertEqual(row["new_participants"], new_count)
            self.assertEqual(row["total_sessions"], 12)
            self.assertEqual(row["finalised_sessions"], 12)
            self.assertGreater(row["engagement_percent"], 50)
            self.assertLess(row["engagement_percent"], 95)
            rates.append(row["engagement_percent"])
        self.assertEqual(len(set(rates)), 3)
        person = Participant.objects.get(pk=demo_id("acc-whangarei-person-0"))
        person.notes = "Keep my edit"
        person.save()
        feedback.quote = "Keep my reviewed feedback"
        feedback.consent = False
        feedback.save()
        attendance = AttendanceRecord.objects.filter(status="present").first()
        attendance.status = "absent"
        attendance.absence_reason = "transport_issue"
        attendance.save()
        counts = [model.objects.count() for model in (Branch, Participant, ProgrammeSession, AttendanceRecord, Feedback)]
        call_command("seed_acc_demo", stdout=io.StringIO())
        self.assertEqual(counts, [model.objects.count() for model in (Branch, Participant, ProgrammeSession, AttendanceRecord, Feedback)])
        person.refresh_from_db()
        feedback.refresh_from_db()
        attendance.refresh_from_db()
        self.assertEqual(person.notes, "Keep my edit")
        self.assertEqual(feedback.quote, "Keep my reviewed feedback")
        self.assertFalse(feedback.consent)
        self.assertEqual(attendance.status, "absent")
        self.assertEqual(attendance.absence_reason, "transport_issue")
        self.assertEqual(ProgrammeSession.objects.order_by("-date").first().date, end)
        self.assertTrue(Branch.objects.filter(pk=unrelated.pk, name="Existing branch").exists())
        with self.assertRaises(CommandError):
            call_command("seed_acc_demo", as_of=end + timedelta(days=1), stdout=io.StringIO())

    @override_settings(ALLOW_DEMO_SEEDING=False)
    def test_seed_requires_explicit_opt_in(self):
        with self.assertRaises(CommandError):
            call_command("seed_acc_demo", stdout=io.StringIO())
        self.assertFalse(Branch.objects.exists())
