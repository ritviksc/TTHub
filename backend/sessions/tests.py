from datetime import date, time, datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from participants.models import Participant
from users.models import Branch, UserAccount

from .models import AttendanceRecord, ProgrammeSession
from .serializers import AttendanceRecordSerializer


class SessionModelTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Dunedin")
        self.instructor = UserAccount.objects.create_user(
            username="instructor@example.com",
            email="instructor@example.com",
            password="SafePass123!",
            role=UserAccount.Role.INSTRUCTOR,
            branch=self.branch,
        )
        self.participant = Participant.objects.create(
            first_name="Aroha", last_name="Ngata", branch=self.branch
        )
        self.session = ProgrammeSession.objects.create(
            branch=self.branch,
            created_by=self.instructor,
            date=date.today(),
            time=time(10, 0),
            activity="Strength and mobility",
        )

    def test_marking_present_clears_an_absence_reason(self):
        AttendanceRecord.objects.create(session=self.session, participant=self.participant)
        serializer = AttendanceRecordSerializer(
            data={"status": "present", "absence_reason": "no_show"}
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["absence_reason"], "")


class SessionDateTests(TestCase):
    def setUp(self):
        branch = Branch.objects.create(name="Dunedin")
        instructor = UserAccount.objects.create_user(
            username="instructor@example.com", email="instructor@example.com",
            role=UserAccount.Role.INSTRUCTOR, branch=branch,
        )
        self.client = APIClient()
        self.client.force_authenticate(instructor)

    @patch("django.utils.timezone.now", return_value=datetime(2026, 9, 20, 13, tzinfo=datetime_timezone.utc))
    def test_rejects_previous_day_using_new_zealand_date(self, now):
        response = self.client.post("/api/sessions/", {
            "date": "2026-09-20", "time": "23:59", "activity": "Class",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("date", response.data)
        self.assertFalse(ProgrammeSession.objects.exists())
        self.assertFalse(AttendanceRecord.objects.exists())

    @patch("django.utils.timezone.now", return_value=datetime(2026, 9, 20, 13, tzinfo=datetime_timezone.utc))
    def test_accepts_today_and_future_dates(self, now):
        for day in ("2026-09-21", "2026-09-22"):
            with self.subTest(day=day):
                response = self.client.post("/api/sessions/", {
                    "date": day, "time": "09:00", "activity": "Class",
                }, format="json")
                self.assertEqual(response.status_code, 201, response.data)


class AttendanceFinalisationTests(TestCase):
    def setUp(self):
        SessionModelTests.setUp(self)
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.client.force_authenticate(self.instructor)
        self.record = AttendanceRecord.objects.create(
            session=self.session, participant=self.participant,
        )
        self.state_url = f"/api/sessions/{self.session.pk}/attendance-state/"
        self.record_url = f"/api/sessions/{self.session.pk}/attendance/{self.record.pk}/"

    def test_empty_session_can_be_finalised_and_reopened(self):
        self.assertFalse(self.session.attendance_finalised)
        response = self.client.patch(self.state_url, {"attendance_finalised": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertTrue(self.session.attendance_finalised)
        detail = self.client.get(f"/api/sessions/{self.session.pk}/")
        self.assertTrue(detail.data["attendance_finalised"])
        self.assertEqual(detail.data["present_count"], 0)
        self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 409)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, "absent")
        self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": False}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 200)
        self.session.refresh_from_db()
        self.assertFalse(self.session.attendance_finalised)

    def test_other_branch_cannot_finalise(self):
        self.instructor.branch = Branch.objects.create(name="Other branch")
        self.instructor.save()
        self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": True}, format="json").status_code, 404)
        self.session.refresh_from_db()
        self.assertFalse(self.session.attendance_finalised)

    def test_manager_cannot_finalise(self):
        self.instructor.role = UserAccount.Role.BRANCH_MANAGER
        self.instructor.save()
        self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": True}, format="json").status_code, 403)

    def test_state_is_required(self):
        self.assertEqual(self.client.patch(self.state_url, {}, format="json").status_code, 400)
