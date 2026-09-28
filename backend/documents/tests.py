from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from participants.models import Participant
from users.models import Branch, UserAccount

from .models import Document, Folder


def _gif_bytes():
    buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="GIF")
    return buffer.getvalue()


class DocumentsTestCase(TestCase):
    """Shared fixtures for documents.tests: two branches, one of each role, and
    private storage pointed at a temporary directory."""

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


class DocumentAccessTests(DocumentsTestCase):
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


class FolderTests(DocumentsTestCase):
    def _create_folder(self, name="Policies", **extra):
        return self.client.post("/api/folders/", {"name": name, **extra}, format="json")

    # -- Create -----------------------------------------------------------

    def test_branch_manager_can_create_rename_and_delete_empty_folder(self):
        self.client.force_authenticate(self.manager)
        response = self._create_folder(name="Policies", branch=self.branch.pk)
        self.assertEqual(response.status_code, 201, response.data)
        folder_id = response.data["id"]

        rename = self.client.patch(f"/api/folders/{folder_id}/", {"name": "Old Policies"}, format="json")
        self.assertEqual(rename.status_code, 200, rename.data)
        self.assertEqual(rename.data["name"], "Old Policies")

        delete = self.client.delete(f"/api/folders/{folder_id}/")
        self.assertEqual(delete.status_code, 204)

    def test_instructor_cannot_create_rename_or_move_folders(self):
        folder = Folder.objects.create(name="Policies", branch=self.branch)
        self.client.force_authenticate(self.instructor)
        self.assertEqual(self._create_folder(name="Other plans", branch=self.branch.pk).status_code, 403)
        self.assertEqual(
            self.client.patch(f"/api/folders/{folder.pk}/", {"name": "Renamed"}, format="json").status_code, 403,
        )

    def test_branch_manager_cannot_create_organisation_folder(self):
        self.client.force_authenticate(self.manager)
        response = self._create_folder(name="Org policies")
        self.assertEqual(response.status_code, 403)

    def test_super_admin_can_create_organisation_folder(self):
        self.client.force_authenticate(self.super_admin)
        response = self._create_folder(name="Org policies")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data["branch"])

    def test_duplicate_sibling_folder_name_is_rejected(self):
        Folder.objects.create(name="Policies", branch=self.branch)
        self.client.force_authenticate(self.manager)
        response = self._create_folder(name="policies", branch=self.branch.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data)

    def test_subfolder_inherits_parent_branch(self):
        parent = Folder.objects.create(name="Policies", branch=self.branch)
        self.client.force_authenticate(self.manager)
        response = self._create_folder(name="H&S", parent=parent.pk)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["branch"], self.branch.pk)

    # -- Delete: blocked while not empty -----------------------------------

    def test_deleting_folder_with_a_document_is_blocked(self):
        folder = Folder.objects.create(name="Policies", branch=self.branch)
        Document.objects.create(file="documents/p.pdf", name="Policy.pdf", size=1, branch=self.branch, folder=folder)
        self.client.force_authenticate(self.manager)
        response = self.client.delete(f"/api/folders/{folder.pk}/")
        self.assertEqual(response.status_code, 409)

    def test_deleting_folder_with_a_subfolder_is_blocked(self):
        parent = Folder.objects.create(name="Policies", branch=self.branch)
        Folder.objects.create(name="H&S", branch=self.branch, parent=parent)
        self.client.force_authenticate(self.manager)
        response = self.client.delete(f"/api/folders/{parent.pk}/")
        self.assertEqual(response.status_code, 409)

    # -- Move: folders ------------------------------------------------------

    def test_moving_folder_into_its_own_descendant_is_rejected(self):
        parent = Folder.objects.create(name="Policies", branch=self.branch)
        child = Folder.objects.create(name="H&S", branch=self.branch, parent=parent)
        self.client.force_authenticate(self.manager)
        response = self.client.patch(f"/api/folders/{parent.pk}/", {"parent": child.pk}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_moving_folder_into_another_branch_is_rejected(self):
        folder = Folder.objects.create(name="Policies", branch=self.branch)
        other_folder = Folder.objects.create(name="Other plans", branch=self.other_branch)
        self.client.force_authenticate(self.super_admin)
        response = self.client.patch(f"/api/folders/{folder.pk}/", {"parent": other_folder.pk}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_other_branchs_folders_are_hidden(self):
        Folder.objects.create(name="Other plans", branch=self.other_branch)
        self.client.force_authenticate(self.manager)
        response = self.client.get(f"/api/folders/?branch={self.branch.pk}")
        self.assertEqual(response.data, [])

    # -- Documents inside folders --------------------------------------------

    def test_uploading_into_a_folder_sets_its_branch(self):
        folder = Folder.objects.create(name="Policies", branch=self.branch)
        self.client.force_authenticate(self.instructor)
        response = self._upload(folder=folder.pk)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["branch"], self.branch.pk)
        self.assertEqual(response.data["folder"], folder.pk)

    def test_folder_filter_root_and_specific_folder(self):
        folder = Folder.objects.create(name="Policies", branch=self.branch)
        Document.objects.create(file="documents/a.pdf", name="Loose.pdf", size=1, branch=self.branch)
        Document.objects.create(file="documents/b.pdf", name="Filed.pdf", size=1, branch=self.branch, folder=folder)
        self.client.force_authenticate(self.manager)

        root = self.client.get(f"/api/documents/?branch={self.branch.pk}&folder=root")
        self.assertEqual([d["name"] for d in root.data], ["Loose.pdf"])

        in_folder = self.client.get(f"/api/documents/?branch={self.branch.pk}&folder={folder.pk}")
        self.assertEqual([d["name"] for d in in_folder.data], ["Filed.pdf"])

    def test_moving_document_to_another_branchs_folder_is_rejected(self):
        document = Document.objects.create(file="documents/a.pdf", name="Plan.pdf", size=1, branch=self.branch)
        other_folder = Folder.objects.create(name="Other plans", branch=self.other_branch)
        self.client.force_authenticate(self.super_admin)
        response = self.client.patch(f"/api/documents/{document.pk}/", {"folder": other_folder.pk}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_participant_document_cannot_be_filed_in_a_folder(self):
        folder = Folder.objects.create(name="Policies", branch=self.branch)
        document = Document.objects.create(
            file="documents/p.pdf", name="Referral.pdf", size=1, participant=self.participant,
        )
        self.client.force_authenticate(self.manager)
        response = self.client.patch(f"/api/documents/{document.pk}/", {"folder": folder.pk}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_renaming_document_keeps_its_extension(self):
        document = Document.objects.create(file="documents/a.pdf", name="Plan.pdf", size=1, branch=self.branch)
        self.client.force_authenticate(self.manager)
        response = self.client.patch(f"/api/documents/{document.pk}/", {"name": "Renamed"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["name"], "Renamed.pdf")

    def test_instructor_can_rename_but_not_move_document(self):
        folder = Folder.objects.create(name="Policies", branch=self.branch)
        document = Document.objects.create(file="documents/a.pdf", name="Plan.pdf", size=1, branch=self.branch)
        self.client.force_authenticate(self.instructor)
        rename = self.client.patch(f"/api/documents/{document.pk}/", {"name": "Renamed"}, format="json")
        self.assertEqual(rename.status_code, 403)
        move = self.client.patch(f"/api/documents/{document.pk}/", {"folder": folder.pk}, format="json")
        self.assertEqual(move.status_code, 403)
