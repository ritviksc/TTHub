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
