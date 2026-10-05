"""Explicit audit payloads only. Never pass request bodies or serializer data."""
from django.db import transaction
from .models import AuditEvent


def record(action, *, request=None, actor=None, branch_id=None, target_type="", target_id="",
           target_label="", details=None, outcome="success", source="api"):
    actor = actor if actor is not None else getattr(request, "user", None)
    authenticated = actor is not None and actor.is_authenticated
    return AuditEvent.objects.create(
        action=action, outcome=outcome, source=source,
        actor_id=actor.pk if authenticated else None,
        actor_email=actor.email if authenticated else "",
        actor_role=actor.role if authenticated else "",
        branch_id=branch_id, target_type=target_type, target_id=str(target_id or ""),
        target_label=target_label, request_id=getattr(request, "audit_request_id", None),
        details=details or {},
    )


def staff_snapshot(user):
    return {"email": user.email, "first_name": user.first_name, "last_name": user.last_name,
            "role": user.role, "branch_id": str(user.branch_id) if user.branch_id else None,
            "is_active": user.is_active}


def staff_changed(request, user, before=None):
    after = staff_snapshot(user)
    if before == after:
        return
    changes = {key: {"before": before.get(key) if before else None, "after": value}
               for key, value in after.items() if before is None or before.get(key) != value}
    if before is None:
        action = "staff.created"
    elif before["is_active"] != after["is_active"]:
        action = "staff.reactivated" if after["is_active"] else "staff.deactivated"
    elif before["role"] != after["role"]:
        action = "staff.role_changed"
    elif before["branch_id"] != after["branch_id"]:
        action = "staff.branch_changed"
    else:
        action = "staff.updated"
    record(action, request=request, branch_id=user.branch_id,
           target_type="staff", target_id=user.pk, target_label=user.email, details={"changes": changes})


def report_event(job, action, *, source="worker", request=None, outcome="success", reason=None):
    scope = job.statistics.get("scope", {})
    details = {"report_type": "attendance" if job._meta.model_name == "attendanceanalysisjob" else "physical",
               "start_date": scope.get("start_date"), "end_date": scope.get("end_date"),
               "model": job.model_name or None}
    if reason:
        details["reason"] = reason
    record(action, request=request, actor=job.requested_by, branch_id=job.branch_id,
           target_type="report", target_id=job.pk, details=details, source=source, outcome=outcome)


@transaction.atomic
def transition_job(job, queryset, status, *, source="worker", reason=None, **updates):
    # Conditional update and audit insert commit together. Duplicate deliveries
    # and competing expiry checks cannot produce a second transition event.
    changed = queryset.update(status=status, **updates)
    if changed:
        report_event(job, f"report.{status}", source=source,
                     outcome="failed" if status == "failed" else "success", reason=reason)
    return changed
