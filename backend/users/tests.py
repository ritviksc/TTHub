from django.test import TestCase
from rest_framework.test import APIClient

from .models import UserAccount


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
