from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Branch, UserAccount

from .models import Participant


class ParticipantConsentTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Dunedin")
        self.manager = UserAccount.objects.create_user(
            username="manager@example.com",
            email="manager@example.com",
            password="SafePass123!",
            role=UserAccount.Role.BRANCH_MANAGER,
            branch=self.branch,
        )
        self.instructor = UserAccount.objects.create_user(
            username="instructor@example.com",
            email="instructor@example.com",
            password="SafePass123!",
            role=UserAccount.Role.INSTRUCTOR,
            branch=self.branch,
        )
        self.participant = Participant.objects.create(
            first_name="Aroha", last_name="Ngata", branch=self.branch,
        )
        self.client = APIClient()

    def test_instructor_cannot_record_gp_consent(self):
        self.client.force_authenticate(self.instructor)

        response = self.client.patch(
            f"/api/participants/{self.participant.id}/",
            {"gp_consent_given": True, "gp_consent_date": str(date.today())},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("gp_consent_given", response.data)

    def test_manager_must_record_date_with_gp_consent(self):
        self.client.force_authenticate(self.manager)

        response = self.client.patch(
            f"/api/participants/{self.participant.id}/",
            {"gp_consent_given": True},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("gp_consent_date", response.data)

    def test_list_hides_photo_without_consent(self):
        self.participant.photo.name = "participant_photos/aroha.jpg"
        self.participant.save(update_fields=["photo"])
        self.client.force_authenticate(self.instructor)

        response = self.client.get("/api/participants/")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data[0]["photo"])

        self.participant.photo_consent_given = True
        self.participant.photo_consent_date = date.today()
        self.participant.save(update_fields=["photo_consent_given", "photo_consent_date"])

        response = self.client.get("/api/participants/")

        self.assertTrue(response.data[0]["photo"].endswith("/media/participant_photos/aroha.jpg"))


class ParticipantAccessTests(TestCase):
    def setUp(self):
        import tempfile
        from django.test import override_settings
        from django.core.files.base import ContentFile
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.branch = Branch.objects.create(name="Photo branch")
        self.other = Branch.objects.create(name="Other branch")
        self.instructor = UserAccount.objects.create_user(
            username="photo@example.com", email="photo@example.com",
            role=UserAccount.Role.INSTRUCTOR, branch=self.branch,
        )
        self.participant = Participant.objects.create(
            first_name="Test", last_name="Participant", branch=self.branch,
            photo_consent_given=True, photo_consent_date=date.today(),
        )
        self.participant.photo.save("test.gif", ContentFile(b"test-image-bytes"))
        self.photo_url = self.participant.photo.url
        self.client = APIClient()

    def test_direct_photo_requires_login_branch_access_and_consent(self):
        self.assertEqual(self.client.get(self.photo_url).status_code, 403)
        self.client.force_authenticate(self.instructor)
        response = self.client.get(self.photo_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"test-image-bytes")
        response.close()
        self.assertIn("no-store", response["Cache-Control"])
        self.instructor.branch = self.other
        self.instructor.save()
        self.assertEqual(self.client.get(self.photo_url).status_code, 404)
        self.instructor.branch = self.branch
        self.instructor.save()
        self.participant.photo_consent_given = False
        self.participant.save()
        self.assertEqual(self.client.get(self.photo_url).status_code, 404)

    def test_unassigned_staff_cannot_create_participant(self):
        self.instructor.branch = None
        self.instructor.save()
        self.client.force_authenticate(self.instructor)
        response = self.client.post("/api/participants/", {
            "first_name": "New", "last_name": "Person",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("branch", response.data)
