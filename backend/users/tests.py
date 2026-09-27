from django.test import TestCase
from rest_framework.test import APIClient

from .models import Branch, UserAccount


class EmailLoginTests(TestCase):
    def setUp(self):
        self.user = UserAccount.objects.create_user(
            username="staff@example.org",
            email="staff@example.org",
            password="SafePass123!",
            role=UserAccount.Role.INSTRUCTOR,
        )
        self.client = APIClient()

    def test_login_uses_normalized_email(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": " STAFF@EXAMPLE.ORG ", "password": "SafePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], UserAccount.Role.INSTRUCTOR)

    def test_login_does_not_accept_the_legacy_username_field(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "staff@example.org", "password": "SafePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_staff_email_edit_preserves_login_and_rejects_duplicate_email(self):
        admin = UserAccount.objects.create_user(
            username="admin@example.org", email="admin@example.org",
            role=UserAccount.Role.SUPER_ADMIN,
        )
        self.user.branch = Branch.objects.create(name="Dunedin")
        self.user.save(update_fields=["branch"])
        self.client.force_authenticate(admin)
        url = f"/api/auth/staff/{self.user.pk}/"
        response = self.client.patch(url, {"email": " MixedCase@Example.ORG "}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "mixedcase@example.org")
        self.assertEqual(self.user.username, "mixedcase@example.org")
        response = self.client.patch(url, {"email": "ADMIN@EXAMPLE.ORG"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "mixedcase@example.org")
        self.client.force_authenticate(None)
        response = self.client.post("/api/auth/login/", {
            "email": "MIXEDCASE@EXAMPLE.ORG", "password": "SafePass123!",
        }, format="json")
        self.assertEqual(response.status_code, 200, response.data)



class AccountBoundaryTests(TestCase):
    def setUp(self):
        from .models import Branch
        self.branch = Branch.objects.create(name="Old branch")
        self.admin = UserAccount.objects.create_user(
            username="admin@example.com", email="admin@example.com",
            role=UserAccount.Role.SUPER_ADMIN, password="SafePass123!",
        )
        self.manager = UserAccount.objects.create_user(
            username="manager@example.com", email="manager@example.com",
            role=UserAccount.Role.BRANCH_MANAGER,
        )
        self.instructor = UserAccount.objects.create_user(
            username="instructor@example.com", email="instructor@example.com",
            role=UserAccount.Role.INSTRUCTOR,
        )
        self.client = APIClient()

    def test_malformed_credentials_return_bad_request(self):
        for field in ("email", "password"):
            for value in (None, 42, [], {}):
                with self.subTest(field=field, value=value):
                    payload = {"email": "admin@example.com", "password": "SafePass123!", field: value}
                    response = self.client.post("/api/auth/login/", payload, format="json")
                    self.assertEqual(response.status_code, 400)

    def test_login_rejects_non_object_payloads(self):
        for payload in (["unexpected"], 42, "unexpected"):
            with self.subTest(payload=payload):
                response = self.client.post("/api/auth/login/", payload, format="json")
                self.assertEqual(response.status_code, 400)

    def test_anonymous_login_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        payload = {"email": "admin@example.com", "password": "SafePass123!"}
        self.assertEqual(client.post("/api/auth/login/", payload, format="json").status_code, 403)
        client.get("/api/auth/csrf/")
        token = client.cookies["csrftoken"].value
        response = client.post("/api/auth/login/", payload, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)

    def test_unassigned_manager_cannot_list_or_deactivate_unassigned_staff(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/auth/staff/list/")
        self.assertEqual(response.data, [])
        response = self.client.post(f"/api/auth/staff/{self.instructor.pk}/deactivate/")
        self.assertEqual(response.status_code, 404)
        self.instructor.refresh_from_db()
        self.assertTrue(self.instructor.is_active)

    def test_branch_with_historical_sessions_returns_conflict_on_delete(self):
        from datetime import date, time
        from sessions.models import ProgrammeSession
        ProgrammeSession.objects.create(
            branch=self.branch, created_by=self.instructor,
            date=date(2026, 1, 1), time=time(10), activity="Historical class",
        )
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f"/api/branches/{self.branch.pk}/")
        self.assertEqual(response.status_code, 409)
        self.assertIn("session", response.data["detail"])

    def test_super_admin_creation_clears_branch_assignment(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/auth/staff/", {
            "email": "new-admin@example.com", "password": "SafePass123!",
            "role": "super_admin", "branch": str(self.branch.pk),
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(UserAccount.objects.get(email="new-admin@example.com").branch_id)
