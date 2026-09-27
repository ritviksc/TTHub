import uuid

from django.core.exceptions import ValidationError
from django.db import models


class ProgrammeSession(models.Model):
    """One class at a branch, with its roster fixed when it is created."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        "users.Branch", on_delete=models.PROTECT, related_name="programme_sessions"
    )
    created_by = models.ForeignKey(
        "users.UserAccount", on_delete=models.PROTECT, related_name="created_sessions"
    )
    date = models.DateField()
    time = models.TimeField()
    activity = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    attendance_finalised = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.branch} — {self.date} {self.time}"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    class AbsenceReason(models.TextChoices):
        NO_SHOW = "no_show", "No show"
        MEDICAL_APPOINTMENT = "medical_appointment", "Medical appointment"
        TRANSPORT_ISSUE = "transport_issue", "Transport issue"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ProgrammeSession, on_delete=models.CASCADE, related_name="attendance"
    )
    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.PROTECT, related_name="attendance_records"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ABSENT)
    absence_reason = models.CharField(
        max_length=30, choices=AbsenceReason.choices, blank=True
    )
    absence_reason_other = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "participant"], name="one_attendance_record_per_participant"
            ),
        ]
        ordering = ["participant__last_name", "participant__first_name"]

    def clean(self):
        errors = {}
        if self.status == self.Status.PRESENT and (
            self.absence_reason or self.absence_reason_other
        ):
            errors["absence_reason"] = "A present participant cannot have an absence reason."
        if self.absence_reason == self.AbsenceReason.OTHER and not self.absence_reason_other:
            errors["absence_reason_other"] = "Describe the other absence reason."
        if self.absence_reason != self.AbsenceReason.OTHER and self.absence_reason_other:
            errors["absence_reason_other"] = "Only use this field when the reason is Other."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.participant} — {self.get_status_display()}"
