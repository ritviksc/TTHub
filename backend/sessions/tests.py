from datetime import date, time

from django.test import TestCase

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
