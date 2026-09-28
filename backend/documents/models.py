import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q

from participants.storage import consent_storage


def document_upload_path(instance, filename):
    # The original filename is kept on the row; on disk it is only a random name.
    return f"documents/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


class Folder(models.Model):
    """A folder in the organisation area (no branch) or in one branch's area.

    Folders nest through `parent`. PROTECT on `parent` and on Document.folder
    means a folder can only be deleted once it is empty.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
    )
    branch = models.ForeignKey(
        "users.Branch", null=True, blank=True, on_delete=models.CASCADE,
        related_name="folders",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_folders",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    """A file kept for the organisation, one branch, or one participant.

    Neither foreign key set means an organisation-wide document. Files live in
    private storage and are only ever served through the download endpoint.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(storage=consent_storage, upload_to=document_upload_path)
    name = models.CharField(max_length=255, help_text="Original filename shown to staff.")
    size = models.PositiveIntegerField()

    branch = models.ForeignKey(
        "users.Branch", null=True, blank=True, on_delete=models.CASCADE,
        related_name="documents",
    )
    participant = models.ForeignKey(
        "participants.Participant", null=True, blank=True, on_delete=models.CASCADE,
        related_name="documents",
    )

    # Participant documents are a flat list, so only these two scopes use folders.
    folder = models.ForeignKey(
        Folder, null=True, blank=True, on_delete=models.PROTECT, related_name="documents",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="uploaded_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(branch__isnull=True) | Q(participant__isnull=True),
                name="document_single_scope",
            ),
            models.CheckConstraint(
                condition=Q(folder__isnull=True) | Q(participant__isnull=True),
                name="document_participant_has_no_folder",
            ),
        ]

    @property
    def scope(self):
        if self.participant_id:
            return "participant"
        if self.branch_id:
            return "branch"
        return "organisation"

    @property
    def owning_branch_id(self):
        """The branch whose staff this document belongs to, if any."""
        if self.participant_id:
            return self.participant.branch_id
        return self.branch_id

    def __str__(self):
        return self.name
