import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def job_deadline():
    return timezone.now() + timedelta(minutes=15)


class AnalysisJob(models.Model):
    class Meta:
        abstract = True

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Protect the scope so a deleted branch cannot turn a scoped job into a national one.
    branch = models.ForeignKey("users.Branch", null=True, on_delete=models.PROTECT)
    statistics = models.JSONField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    model_name = models.CharField(max_length=200, blank=True, default="")
    narrative = models.TextField(null=True, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=job_deadline)

    def can_access(self, user):
        if not user.is_active or user.pk != self.requested_by_id:
            return False
        return user.role == "super_admin" or (
            user.role == "branch_manager" and self.branch_id is not None
            and user.branch_id == self.branch_id
        )

    def expire_if_needed(self, source="system"):
        if self.expires_at <= timezone.now():
            from audit.services import transition_job
            transition_job(self, type(self).objects.filter(
                pk=self.pk, status__in=[self.Status.QUEUED, self.Status.RUNNING],
            ), "failed", source=source, reason="timeout", error="Analysis timed out. Please try again.")
            self.refresh_from_db()


class AttendanceAnalysisJob(AnalysisJob):
    pass


class PhysicalAnalysisJob(AnalysisJob):
    pass
