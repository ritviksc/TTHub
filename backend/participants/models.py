import uuid

from django.db import models


class Participant(models.Model):
    """Someone who attends a branch. Not a system user: participants never log in,
    so this deliberately does not extend UserAccount."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    preferred_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="What the branch actually calls them, if different.",
    )

    date_of_birth = models.DateField(null=True, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)

    # Referenced by label rather than imported, so this app depends on users
    # only through the migration graph.
    branch = models.ForeignKey(
        "users.Branch",
        on_delete=models.PROTECT,
        related_name="participants",
        help_text="The branch this participant attends.",
    )

    joined_on = models.DateField(null=True, blank=True)
    # Participants are deactivated rather than deleted, so their attendance
    # history stays intact. Mirrors how UserAccount.is_active is used.
    is_active = models.BooleanField(default=True)

    notes = models.TextField(
        blank=True,
        help_text="General notes only. Not a clinical record.",
    )
    
    # Medical clearance to take part in activities
    gp_consent_given = models.BooleanField(default=False)
    gp_consent_date = models.DateField(null=True, blank=True)

    # Consent to allow use of their photos for attendance marking
    photo = models.ImageField(upload_to="participant_photos/", null=True, blank=True)
    photo_consent_given = models.BooleanField(default=False)
    photo_consent_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name 

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
