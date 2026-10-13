from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from sessions.models import AttendanceRecord, ProgrammeSession
from users.models import Branch, UserAccount
from .models import Participant


class ParticipantReactivationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(name="Harbour")
        cls.other = Branch.objects.create(name="Hills")
        cls.participant = Participant.objects.create(
            first_name="Aroha", last_name="Example", branch=cls.branch, is_active=False,
        )
        cls.users = {
            role: UserAccount.objects.create_user(
                username=role, email=f"{role}@example.nz", role=role, branch=cls.branch,
            ) for role in ("super_admin", "branch_manager", "instructor")
        }
        cls.session = ProgrammeSession.objects.create(
            branch=cls.branch, created_by=cls.users["instructor"], date=date(2026, 10, 1),
            time="09:00", activity="Historical class", attendance_finalised=True,
        )
        cls.attendance = AttendanceRecord.objects.create(
            participant=cls.participant, session=cls.session, status="absent", absence_reason="transport_issue",
        )

    def setUp(self):
        self.client = APIClient()
        self.url = f"/api/participants/{self.participant.pk}/reactivate/"

    def test_all_staff_roles_can_restore_participant_without_changing_history(self):
        for role, user in self.users.items():
            with self.subTest(role=role):
                self.client.force_authenticate(user)
                self.assertEqual(self.client.post(self.url.replace("reactivate/", "deactivate/")).status_code, 200)
                for _ in range(2):
                    response = self.client.post(self.url)
                    self.assertEqual(response.status_code, 200, response.data)
                    self.assertTrue(response.data["is_active"])
                self.participant.refresh_from_db()
                self.assertTrue(self.participant.is_active)
                self.assertEqual(self.participant.branch, self.branch)
                self.attendance.refresh_from_db()
                self.assertEqual(self.attendance.status, "absent")
                self.assertEqual(self.attendance.absence_reason, "transport_issue")
                response = self.client.get(f"/api/participants/{self.participant.pk}/attendance/")
                self.assertEqual(len(response.data), 1)
                self.assertTrue(response.data[0]["attendance_finalised"])

    def test_branch_scope_is_enforced_and_super_admin_can_restore_other_branches(self):
        for role in ("branch_manager", "instructor"):
            user = self.users[role]
            for branch in (self.other, None):
                with self.subTest(role=role, branch=branch):
                    user.branch = branch
                    user.save()
                    self.client.force_authenticate(user)
                    self.assertEqual(self.client.post(self.url).status_code, 404)
                    self.participant.refresh_from_db()
                    self.assertFalse(self.participant.is_active)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.participant.branch = self.other
        self.participant.save()
        self.client.force_authenticate(self.users["super_admin"])
        self.assertEqual(self.client.post(self.url).status_code, 200)
        self.participant.refresh_from_db()
        self.assertTrue(self.participant.is_active)
