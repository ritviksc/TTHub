from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from participants.models import Participant
from users.models import Branch, UserAccount

from .models import Document


def _gif_bytes():
    buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="GIF")
    return buffer.getvalue()


class DocumentAccessTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
            "private": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {"location": self.directory.name},
            },
        })
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.branch = Branch.objects.create(name="Branch A")
        self.other_branch = Branch.objects.create(name="Branch B")

        self.super_admin = UserAccount.objects.create_user(
            username="admin@example.com", email="admin@example.com",
            role=UserAccount.Role.SUPER_ADMIN,
        )
        self.manager = UserAccount.objects.create_user(
            username="manager@example.com", email="manager@example.com",
            role=UserAccount.Role.BRANCH_MANAGER, branch=self.branch,
        )
        self.other_manager = UserAccount.objects.create_user(
            username="other-manager@example.com", email="other-manager@example.com",
            role=UserAccount.Role.BRANCH_MANAGER, branch=self.other_branch,
        )
        self.instructor = UserAccount.objects.create_user(
            username="instructor@example.com", email="instructor@example.com",
            role=UserAccount.Role.INSTRUCTOR, branch=self.branch,
        )
        self.unassigned_instructor = UserAccount.objects.create_user(
            username="floating@example.com", email="floating@example.com",
            role=UserAccount.Role.INSTRUCTOR,
        )
        self.participant = Participant.objects.create(
            first_name="Test", last_name="Participant", branch=self.branch,
        )

        self.client = APIClient()

    def _upload(self, filename="notes.pdf", content=b"%PDF-1.4 test", **extra):
        upload = SimpleUploadedFile(filename, content)
        return self.client.post("/api/documents/", {"file": upload, **extra}, format="multipart")

    # -- Listing scope --------------------------------------------------

    def test_organisation_documents_are_visible_to_everyone(self):
        Document.objects.create(file="documents/org.pdf", name="Policy.pdf", size=1)
        for user in (self.super_admin, self.manager, self.instructor):
            self.client.force_authenticate(user)
            response = self.client.get("/api/documents/?scope=organisation")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 1)

    def test_other_branchs_documents_are_hidden(self):
        Document.objects.create(file="documents/b.pdf", name="Branch B plan.pdf", size=1, branch=self.other_branch)
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/documents/?scope=branch")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_other_branchs_participant_documents_are_hidden(self):
        other_participant = Participant.objects.create(
            first_name="Other", last_name="Person", branch=self.other_branch,
        )
        Document.objects.create(
            file="documents/p.pdf", name="Referral.pdf", size=1, participant=other_participant,
        )
        self.client.force_authenticate(self.instructor)
        response = self.client.get(f"/api/documents/?participant={other_participant.pk}")
        self.assertEqual(response.data, [])

    def test_super_admin_sees_every_branch(self):
        Document.objects.create(file="documents/b.pdf", name="Branch B plan.pdf", size=1, branch=self.other_branch)
        self.client.force_authenticate(self.super_admin)
        response = self.client.get("/api/documents/?scope=branch")
        self.assertEqual(len(response.data), 1)

    def test_malformed_branch_filter_returns_empty_list_not_500(self):
        self.client.force_authenticate(self.manager)
        response = self.client.get("/api/documents/?branch=not-a-uuid")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    # -- Upload rules -----------------------------------------------------

    def test_instructor_can_upload_to_own_branch_and_own_participant(self):
        self.client.force_authenticate(self.instructor)
        response = self._upload(branch=self.branch.pk)
        self.assertEqual(response.status_code, 201, response.data)
        response = self._upload(participant=self.participant.pk)
        self.assertEqual(response.status_code, 201, response.data)

    def test_instructor_cannot_upload_organisation_document(self):
        self.client.force_authenticate(self.instructor)
        response = self._upload()
        self.assertEqual(response.status_code, 403)

    def test_instructor_cannot_upload_to_another_branch(self):
        self.client.force_authenticate(self.instructor)
        response = self._upload(branch=self.other_branch.pk)
        self.assertEqual(response.status_code, 403)

    def test_unassigned_instructor_cannot_upload_anywhere_scoped(self):
        self.client.force_authenticate(self.unassigned_instructor)
        self.assertEqual(self._upload(branch=self.branch.pk).status_code, 403)
        self.assertEqual(self._upload(participant=self.participant.pk).status_code, 403)

    def test_super_admin_can_upload_organisation_document(self):
        self.client.force_authenticate(self.super_admin)
        response = self._upload()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["scope"], "organisation")

    def test_branch_manager_can_upload_to_own_branch_not_others(self):
        self.client.force_authenticate(self.manager)
        self.assertEqual(self._upload(branch=self.branch.pk).status_code, 201)
        self.assertEqual(self._upload(branch=self.other_branch.pk).status_code, 403)

    # -- Download -----------------------------------------------------------

    def test_download_hidden_outside_scope_returns_404(self):
        document = Document.objects.create(
            file="documents/b.pdf", name="Branch B plan.pdf", size=1, branch=self.other_branch,
        )
        self.client.force_authenticate(self.manager)
        response = self.client.get(f"/api/documents/{document.pk}/download/")
        self.assertEqual(response.status_code, 404)

    def test_download_sends_no_store_header(self):
        upload = SimpleUploadedFile("photo.gif", _gif_bytes())
        document = Document.objects.create(
            file=upload, name="photo.gif", size=len(_gif_bytes()), branch=self.branch,
        )
        self.client.force_authenticate(self.manager)
        response = self.client.get(f"/api/documents/{document.pk}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        response.close()

    # -- Delete ---------------------------------------------------------

    def test_instructor_cannot_delete(self):
        document = Document.objects.create(
            file="documents/p.pdf", name="Referral.pdf", size=1, participant=self.participant,
        )
        self.client.force_authenticate(self.instructor)
        response = self.client.delete(f"/api/documents/{document.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_branch_manager_can_delete_own_branch_document_not_organisation(self):
        branch_document = Document.objects.create(
            file="documents/b.pdf", name="Branch plan.pdf", size=1, branch=self.branch,
        )
        org_document = Document.objects.create(file="documents/org.pdf", name="Policy.pdf", size=1)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.delete(f"/api/documents/{branch_document.pk}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/documents/{org_document.pk}/").status_code, 403)

    def test_branch_manager_cannot_delete_another_branchs_document(self):
        document = Document.objects.create(
            file="documents/b.pdf", name="Branch plan.pdf", size=1, branch=self.other_branch,
        )
        self.client.force_authenticate(self.manager)
        # Out of scope, so it is not visible to fetch at all.
        response = self.client.delete(f"/api/documents/{document.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_super_admin_can_delete_anything(self):
        document = Document.objects.create(file="documents/org.pdf", name="Policy.pdf", size=1)
        self.client.force_authenticate(self.super_admin)
        self.assertEqual(self.client.delete(f"/api/documents/{document.pk}/").status_code, 204)

    # -- Validation -------------------------------------------------------

    def test_upload_rejects_file_over_size_limit(self):
        self.client.force_authenticate(self.super_admin)
        big_content = b"%PDF-1.4 " + b"a" * (10 * 1024 * 1024 + 1)
        response = self._upload(filename="big.pdf", content=big_content)
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data)

    def test_upload_rejects_extension_mismatch(self):
        self.client.force_authenticate(self.super_admin)
        response = self._upload(filename="fake.pdf", content=b"not really a pdf")
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data)

    def test_upload_rejects_unsupported_extension(self):
        self.client.force_authenticate(self.super_admin)
        response = self._upload(filename="notes.txt", content=b"hello")
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data)

    def test_anonymous_request_is_rejected(self):
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, 403)
