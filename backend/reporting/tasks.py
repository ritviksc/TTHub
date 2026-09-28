"""Background report generation. Only job IDs travel through the broker."""

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
    job.expire_if_needed()
    # Claim once so duplicate task delivery does not repeat a paid model request.
    claimed = job_model.objects.filter(
        pk=job.pk, status=job_model.Status.QUEUED, expires_at__gt=timezone.now(),
    ).update(status=job_model.Status.RUNNING)
    if not claimed:
        job.expire_if_needed()
        return
    try:
        if not job.can_access(job.requested_by):
            raise PermissionDenied("Report permissions changed.")
        narrative = explain(job.statistics)
    except Exception:
        # Persist a safe message; the task still fails visibly in Celery worker logs.
        job_model.objects.filter(pk=job.pk, status="running").update(
            status="failed", error="AI analysis could not be completed. Please try again.",
        )
        raise
    # Expiry must not depend on whether a browser happens to poll during generation.
    finished_at = timezone.now()
    job_model.objects.filter(pk=job.pk, status="running", expires_at__lte=finished_at).update(
        status="failed", error="Analysis timed out. Please try again.",
    )
    job_model.objects.filter(pk=job.pk, status="running", expires_at__gt=finished_at).update(
        status="succeeded", narrative=narrative,
    )


@shared_task(ignore_result=True, soft_time_limit=240, time_limit=270)
def generate_attendance_analysis(job_id):
    run_analysis_job(AttendanceAnalysisJob, explain_attendance, job_id)


@shared_task(ignore_result=True, soft_time_limit=240, time_limit=270)
def generate_physical_analysis(job_id):
    run_analysis_job(PhysicalAnalysisJob, explain_physical, job_id)
