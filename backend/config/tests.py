from django.conf import settings
from django.test import SimpleTestCase, override_settings


@override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
class HealthTests(SimpleTestCase):
    # SimpleTestCase rejects database queries, including session lookups.
    def test_liveness_with_session_cookie_does_not_use_database(self):
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "a" * 32
        for path in ("/health", "/health/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "ok"})
                self.assertIn("no-store", response["Cache-Control"])

    def test_head_probe(self):
        response = self.client.head("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_writes_are_not_supported(self):
        self.assertEqual(self.client.post("/health").status_code, 405)
