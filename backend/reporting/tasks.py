"""Background report generation. Only job IDs travel through the broker."""

from celery import shared_task
from django.core.exceptions import PermissionDenied

from .models import AttendanceAnalysisJob
from .services.attendance import explain_attendance


@shared_task(ignore_result=True, soft_time_limit=240, time_limit=270)
def generate_attendance_analysis(job_id):
    job = AttendanceAnalysisJob.objects.select_related("requested_by").filter(pk=job_id).first()
    if job is None:
        return
    job.expire_if_needed()
    # Claim once so duplicate task delivery does not repeat a paid model request.
    claimed = AttendanceAnalysisJob.objects.filter(
        pk=job.pk, status=AttendanceAnalysisJob.Status.QUEUED,
    ).update(status=AttendanceAnalysisJob.Status.RUNNING)
    if not claimed:
        return
    try:
        if not job.can_access(job.requested_by):
            raise PermissionDenied("Report permissions changed.")
        narrative = explain_attendance(job.statistics)
    except Exception:
        # Persist a safe message; the task still fails visibly in Celery worker logs.
        AttendanceAnalysisJob.objects.filter(pk=job.pk, status="running").update(
            status="failed", error="AI analysis could not be completed. Please try again.",
        )
        raise
    AttendanceAnalysisJob.objects.filter(pk=job.pk, status="running").update(
        status="succeeded", narrative=narrative,
    )
