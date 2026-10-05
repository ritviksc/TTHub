"""Background report generation. Only job IDs travel through the broker."""

from audit.services import transition_job

from celery import shared_task
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import AttendanceAnalysisJob, PhysicalAnalysisJob
from .services.physical import explain_physical
from .services.attendance import explain_attendance


def run_analysis_job(job_model, explain, job_id):
    job = job_model.objects.select_related("requested_by").filter(pk=job_id).first()
    if job is None:
        return
    job.expire_if_needed(source="worker")
    # Claim once so duplicate task delivery does not repeat a paid model request.
    claimed = transition_job(job, job_model.objects.filter(
        pk=job.pk, status=job_model.Status.QUEUED, expires_at__gt=timezone.now(),
    ), "running")
    if not claimed:
        job.expire_if_needed(source="worker")
        return
    try:
        if not job.can_access(job.requested_by):
            raise PermissionDenied("Report permissions changed.")
        narrative = explain(job.statistics)
    except Exception:
        # Persist a safe message; the task still fails visibly in Celery worker logs.
        transition_job(job, job_model.objects.filter(pk=job.pk, status="running"),
            "failed", reason="generation_failed", error="AI analysis could not be completed. Please try again.",
        )
        raise
    # Expiry must not depend on whether a browser happens to poll during generation.
    finished_at = timezone.now()
    transition_job(job, job_model.objects.filter(pk=job.pk, status="running", expires_at__lte=finished_at),
        "failed", reason="timeout", error="Analysis timed out. Please try again.",
    )
    transition_job(job, job_model.objects.filter(pk=job.pk, status="running", expires_at__gt=finished_at),
        "succeeded", narrative=narrative,
    )


@shared_task(ignore_result=True, soft_time_limit=240, time_limit=270)
def generate_attendance_analysis(job_id):
    run_analysis_job(AttendanceAnalysisJob, explain_attendance, job_id)


@shared_task(ignore_result=True, soft_time_limit=240, time_limit=270)
def generate_physical_analysis(job_id):
    run_analysis_job(PhysicalAnalysisJob, explain_physical, job_id)
