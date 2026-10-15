from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from participants.models import Participant
from users.models import Branch, UserAccount
from .models import AttendanceRecord, ProgrammeSession


class NationalSessionAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserAccount.objects.create_user(username="national", email="national@example.nz", role="super_admin")
        cls.sessions = []
        cls.instructors = []
        for index, name in enumerate(["Harbour", "Hills"]):
            branch = Branch.objects.create(name=name)
            instructor = UserAccount.objects.create_user(
                username=f"instructor-{index}", email=f"instructor-{index}@example.nz", role="instructor", branch=branch,
            )
            participant = Participant.objects.create(first_name=name, last_name="Participant", branch=branch)
            session = ProgrammeSession.objects.create(
                branch=branch, created_by=instructor, date=date(2026, 10, 1), time="09:00", activity=f"{name} class",
            )
            AttendanceRecord.objects.create(session=session, participant=participant, status="absent", absence_reason="transport_issue")
            cls.sessions.append(session)
            cls.instructors.append(instructor)

    def setUp(self):
        self.client = APIClient()

    def test_super_admin_can_list_and_open_sessions_in_every_branch(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/sessions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["id"] for item in response.data}, {str(session.pk) for session in self.sessions})
        self.assertEqual({item["branch_name"] for item in response.data}, {"Harbour", "Hills"})
        for session in self.sessions:
            detail = self.client.get(f"/api/sessions/{session.pk}/")
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.data["roster_count"], 1)
            self.assertEqual(detail.data["attendance"][0]["absence_reason"], "transport_issue")

    def test_national_view_does_not_grant_attendance_or_delete_permissions(self):
        self.client.force_authenticate(self.admin)
        session = self.sessions[0]
        record = session.attendance.get()
        url = f"/api/sessions/{session.pk}/"
        self.assertEqual(self.client.patch(url + f"attendance/{record.pk}/", {"status": "present"}, format="json").status_code, 403)
        self.assertEqual(self.client.patch(url + "attendance-state/", {"attendance_finalised": True}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        record.refresh_from_db()
        self.assertEqual(record.status, "absent")
        self.assertTrue(ProgrammeSession.objects.filter(pk=session.pk).exists())

    def test_branch_staff_stay_scoped_even_with_a_foreign_branch_query(self):
        for role in ("instructor", "branch_manager"):
            user = self.instructors[0]
            user.role = role
            user.save()
            self.client.force_authenticate(user)
            response = self.client.get("/api/sessions/", {"branch": str(self.sessions[1].branch_id)})
            self.assertEqual(response.status_code, 200)
            self.assertEqual([row["id"] for row in response.data], [str(self.sessions[0].pk)])
            self.assertEqual(self.client.get(f"/api/sessions/{self.sessions[1].pk}/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/sessions/").status_code, 403)
