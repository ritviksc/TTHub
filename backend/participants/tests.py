from datetime import date, datetime, timezone as datetime_timezone
from unittest.mock import patch
from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Branch, UserAccount

from .models import Participant


class ConsentDateTests(TestCase):
    @patch("django.utils.timezone.now", return_value=datetime(2026, 9, 20, 13, tzinfo=datetime_timezone.utc))
    def test_consent_dates_for_each_authorized_role_use_new_zealand_today(self, now):
        branch = Branch.objects.create(name="Dunedin")
        participant = Participant.objects.create(first_name="Aroha", last_name="Ngata", branch=branch)
        client = APIClient()
        for role in ("super_admin", "branch_manager", "instructor"):
            user = UserAccount.objects.create_user(
                username=f"{role}@example.com", email=f"{role}@example.com", role=role, branch=branch,
            )
            client.force_authenticate(user)
            for consent in (["photo"] if role == "instructor" else ["gp", "photo"]):
                for day, expected in (("2026-09-20", 200), ("2026-09-21", 200), ("2026-09-22", 400)):
                    with self.subTest(role=role, consent=consent, day=day):
                        response = client.patch(f"/api/participants/{participant.pk}/", {
                            f"{consent}_consent_given": "true", f"{consent}_consent_date": day,
                        }, format="multipart")
                        self.assertEqual(response.status_code, expected, response.data)
                        if expected == 400:
                            self.assertIn(f"{consent}_consent_date", response.data)
                            participant.refresh_from_db()
                            self.assertEqual(getattr(participant, f"{consent}_consent_date"), date(2026, 9, 21))


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

        self.assertTrue(response.data[0]["photo"].endswith(f"/api/participants/{self.participant.pk}/photo/"))


class ParticipantDocumentTests(ParticipantConsentTests):
    def setUp(self):
        super().setUp()
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        settings = override_settings(STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "private": {"BACKEND": "django.core.files.storage.FileSystemStorage", "OPTIONS": {"location": directory.name}},
        })
        settings.enable()
        self.addCleanup(settings.disable)
        self.admin = UserAccount.objects.create_user(
            username="admin@example.com", email="admin@example.com", role="super_admin",
        )
        self.other_branch = Branch.objects.create(name="Other branch")
        self.other_manager = UserAccount.objects.create_user(
            username="other@example.com", email="other@example.com",
            role="branch_manager", branch=self.other_branch,
        )
        self.url = f"/api/participants/{self.participant.pk}/"

    def upload(self, user, name="consent.pdf", content=b"%PDF-1.4\n%%EOF"):
        self.client.force_authenticate(user)
        return self.client.patch(self.url, {
            "gp_consent_document": SimpleUploadedFile(name, content),
        }, format="multipart")

    def test_manager_and_admin_can_upload_and_download_without_setting_consent(self):
        for user in (self.manager, self.admin):
            with self.subTest(role=user.role):
                response = self.upload(user)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertTrue(response.data["gp_document_available"])
                self.assertNotIn("gp_consent_document", response.data)
                self.assertFalse(response.data["gp_consent_given"])
                self.participant.refresh_from_db()
                self.assertEqual(self.participant.gp_document_uploaded_by, user)
                self.assertIsNotNone(self.participant.gp_document_uploaded_at)
                download = self.client.get(self.url + "gp-document/")
                self.assertEqual(download.status_code, 200)
                self.assertEqual(b"".join(download.streaming_content), b"%PDF-1.4\n%%EOF")
                self.assertEqual(download["Cache-Control"], "private, no-store")
                self.assertIn("attachment", download["Content-Disposition"])
                download.close()

    def test_document_access_is_role_and_branch_scoped(self):
        self.upload(self.manager)
        for user, expected in ((self.instructor, 403), (self.other_manager, 404), (None, 403)):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url + "gp-document/").status_code, expected)
        self.assertEqual(self.upload(self.instructor).status_code, 400)
        self.assertNotIn("gp_document_available", self.client.get(self.url).data)
        self.assertEqual(self.upload(self.other_manager).status_code, 404)

    def test_rejects_bad_type_content_and_oversize_without_replacing_document(self):
        self.upload(self.manager)
        self.participant.refresh_from_db()
        original = self.participant.gp_consent_document.name
        for name, content in (("file.svg", b"<svg/>"), ("file.pdf", b"not PDF"),
                              ("file.jpg", b"not JPEG"), ("file.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024))):
            self.assertEqual(self.upload(self.manager, name, content).status_code, 400)
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.gp_consent_document.name, original)

    def test_accepts_png_and_jpeg_documents(self):
        for extension, format in (("png", "PNG"), ("jpg", "JPEG")):
            content = BytesIO()
            Image.new("RGB", (2, 2)).save(content, format=format)
            self.assertEqual(self.upload(self.manager, f"consent.{extension}", content.getvalue()).status_code, 200)

    def test_optional_dates_and_consent_remain_editable_with_multipart(self):
        self.client.force_authenticate(self.manager)
        response = self.client.patch(self.url, {
            "first_name": "New name", "date_of_birth": "", "joined_on": "",
            "gp_consent_given": "false", "gp_consent_date": "",
            "photo_consent_given": "false", "photo_consent_date": "",
        }, format="multipart")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(response.data["gp_consent_date"])

    def test_photo_requests_check_consent_and_branch_and_have_no_public_route(self):
        self.participant.photo.save("photo.jpg", SimpleUploadedFile("photo.jpg", b"image"))
        self.participant.photo_consent_given = True
        self.participant.save()
        photo_url = self.url + "photo/"
        self.client.force_authenticate(self.instructor)
        response = self.client.get(photo_url)
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertEqual(self.client.get(self.participant.photo.url).status_code, 404)
        self.client.force_authenticate(self.other_manager)
        self.assertEqual(self.client.get(photo_url).status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(photo_url).status_code, 403)
        self.participant.photo_consent_given = False
        self.participant.save()
        self.client.force_authenticate(self.instructor)
        self.assertEqual(self.client.get(photo_url).status_code, 404)

    def test_history_preserves_inactive_participant_and_scopes_session_branch(self):
        from sessions.models import AttendanceRecord, ProgrammeSession
        for branch in (self.branch, self.other_branch):
            session = ProgrammeSession.objects.create(
                branch=branch, created_by=self.instructor, date=date.today(), time="09:00", activity="Class",
            )
            AttendanceRecord.objects.create(session=session, participant=self.participant, status="present")
        self.participant.is_active = False
        self.participant.save()
        self.client.force_authenticate(self.manager)
        response = self.client.get(self.url + "attendance/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "present")
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get(self.url + "attendance/").data), 2)
        self.client.force_authenticate(self.other_manager)
        self.assertEqual(self.client.get(self.url + "attendance/").status_code, 404)


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
        self.photo_url = f"/api/participants/{self.participant.pk}/photo/"
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


class ParticipantHistoryRegressionTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="History regressions")
        self.user = UserAccount.objects.create_user(username="history-user", email="history-user@example.com", role="instructor", branch=self.branch)
        self.participant = Participant.objects.create(first_name="History", last_name="Person", branch=self.branch)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f"/api/participants/{self.participant.pk}/"

    def test_history_exposes_finalisation_to_distinguish_default_absences(self):
        from sessions.models import AttendanceRecord, ProgrammeSession
        for finalised in (True, False):
            session = ProgrammeSession.objects.create(branch=self.branch, created_by=self.user, date=date(2026, 1, 1), time="10:00", activity="Class", attendance_finalised=finalised)
            AttendanceRecord.objects.create(session=session, participant=self.participant, status="absent")
        response = self.client.get(self.url + "attendance/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(row["attendance_finalised"] for row in response.data), [False, True])

    @patch("participants.serializers.timezone.localdate", return_value=date(2030, 1, 2))
    def test_birth_date_uses_programme_today(self, localdate):
        for value, expected in [("2030-01-02", 200), ("2030-01-03", 400)]:
            response = self.client.patch(self.url, {"date_of_birth": value}, format="json")
            self.assertEqual(response.status_code, expected, response.data)
