import uuid
from django.db import models


class AuditQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValueError("Audit events cannot be edited.")

    def delete(self):
        raise ValueError("Audit events cannot be deleted.")


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    action = models.CharField(max_length=100, db_index=True)
    outcome = models.CharField(max_length=16, default="success")
    source = models.CharField(max_length=16, default="api")
    # Snapshots, not foreign keys: deleting or renaming an account/branch must
    # not erase or rewrite the identity recorded at the time of the action.
    actor_id = models.UUIDField(null=True, db_index=True)
    actor_email = models.CharField(max_length=254, blank=True)
    actor_role = models.CharField(max_length=30, blank=True)
    branch_id = models.UUIDField(null=True, db_index=True)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True, db_index=True)
    target_label = models.CharField(max_length=255, blank=True)
    request_id = models.UUIDField(null=True, db_index=True)
    details = models.JSONField(default=dict)

    objects = AuditQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Audit events cannot be edited.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit events cannot be deleted.")
