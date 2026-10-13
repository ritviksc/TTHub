from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AuditEvent
from .models import Branch, UserAccount


class StaffReactivationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(name="Harbour")
        cls.other = Branch.objects.create(name="Hills")
        cls.admin = UserAccount.objects.create_user(username="admin", email="admin@example.nz", role="super_admin")
        cls.manager = UserAccount.objects.create_user(username="manager", email="manager@example.nz", role="branch_manager", branch=cls.branch)
        cls.instructor = UserAccount.objects.create_user(
            username="instructor@example.nz", email="instructor@example.nz", password="SafePass123!",
            role="instructor", branch=cls.branch, is_active=False,
        )

    def setUp(self):
        self.client = APIClient()
        self.url = f"/api/auth/staff/{self.instructor.pk}/reactivate/"

    def test_manager_reactivation_restores_login_and_audits_once(self):
        login = {"email": self.instructor.email, "password": "SafePass123!"}
        self.assertEqual(self.client.post("/api/auth/login/", login).status_code, 401)
        self.client.force_authenticate(self.manager)
        for _ in range(2):
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertTrue(response.data["is_active"])
        self.instructor.refresh_from_db()
        self.assertTrue(self.instructor.is_active)
        self.assertEqual(self.instructor.branch, self.branch)
        self.assertEqual(self.instructor.role, "instructor")
        event = AuditEvent.objects.get(action="staff.reactivated")
        self.assertEqual(event.actor_id, self.manager.pk)
        self.assertEqual(event.target_id, str(self.instructor.pk))
        self.assertEqual(event.details["changes"]["is_active"], {"before": False, "after": True})
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/auth/login/", login).status_code, 200)

    def test_super_admin_can_reactivate_every_other_staff_role_and_branch(self):
        self.client.force_authenticate(self.admin)
        for role in ("super_admin", "branch_manager", "instructor"):
            with self.subTest(role=role):
                target = UserAccount.objects.create_user(
                    username=f"other-{role}", email=f"other-{role}@example.nz", role=role,
                    branch=None if role == "super_admin" else self.other, is_active=False,
                )
                response = self.client.post(f"/api/auth/staff/{target.pk}/reactivate/")
                self.assertEqual(response.status_code, 200, response.data)
                target.refresh_from_db()
                self.assertTrue(target.is_active)

    def test_reactivation_keeps_existing_role_and_branch_access_rules(self):
        self.client.force_authenticate(self.manager)
        for index, (role, branch) in enumerate([
            ("instructor", self.other), ("instructor", None),
            ("branch_manager", self.branch), ("super_admin", None),
        ]):
            target = UserAccount.objects.create_user(
                username=f"denied-{index}", email=f"denied-{index}@example.nz",
                role=role, branch=branch, is_active=False,
            )
            with self.subTest(role=role, branch=branch):
                self.assertEqual(self.client.post(f"/api/auth/staff/{target.pk}/reactivate/").status_code, 404)
                target.refresh_from_db()
                self.assertFalse(target.is_active)
        self.assertEqual(self.client.post(f"/api/auth/staff/{self.manager.pk}/reactivate/").status_code, 404)
        self.manager.branch = None
        self.manager.save()
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.client.force_authenticate(self.instructor)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertFalse(AuditEvent.objects.filter(action="staff.reactivated").exists())
