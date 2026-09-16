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
