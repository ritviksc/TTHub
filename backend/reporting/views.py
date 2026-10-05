from django.db import transaction
from audit.services import report_event, transition_job
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from kombu.exceptions import OperationalError
from redis.exceptions import RedisError
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsBranchManager, IsSuperAdmin
from .models import AttendanceAnalysisJob, PhysicalAnalysisJob
from .serializers import AttendanceReportRequestSerializer
from .services.attendance import attendance_statistics
from .tasks import generate_attendance_analysis, generate_physical_analysis
from .services.physical import physical_statistics


def job_response(job):
    data = {"job_id": str(job.pk), "status": job.status}
    if job.status == job.Status.SUCCEEDED:
        data.update(statistics=job.statistics, narrative=job.narrative)
    elif job.status == job.Status.FAILED:
        data["detail"] = job.error
    return data


class ReportView(APIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def report_statistics(self, request, data):
        serializer = AttendanceReportRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            return self.statistics_service(user=request.user, **serializer.validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": " ".join(exc.messages)}) from exc

    def get(self, request):
        return Response(self.report_statistics(request, request.query_params))


class AttendanceReportView(ReportView):
    statistics_service = staticmethod(attendance_statistics)


class AttendanceAnalysisView(AttendanceReportView):
    http_method_names = ["post", "options"]

    def post(self, request):
        # Validate permissions and save the exact figures before queueing any AI work.
        statistics = self.report_statistics(request, request.data)
        return queue_analysis(request.user, statistics, AttendanceAnalysisJob, generate_attendance_analysis,
                              statistics["totals"]["finalised_sessions"], request=request)


def queue_analysis(user, statistics, job_model, task, has_data, request=None):
    with transaction.atomic():
        job = job_model.objects.create(
            requested_by=user, branch_id=statistics["scope"]["branch_id"], statistics=statistics,
            status="queued" if has_data else "succeeded",
        )
        report_event(job, "report.requested", request=request, source="api")
        if not has_data:
            report_event(job, "report.succeeded", request=request, source="api", reason="no_data")
    if job.status == job.Status.SUCCEEDED:
        return Response(job_response(job))
    try:
        task.apply_async(args=[str(job.pk)], expires=job.expires_at)
    except (OperationalError, RedisError, OSError):
        transition_job(job, job_model.objects.filter(pk=job.pk, status="queued"), "failed",
                       source="api", reason="queue_unavailable",
                       error="The analysis queue is unavailable. Please try again.")
        job.refresh_from_db()
        return Response(job_response(job), status=503)
    return Response(job_response(job), status=202)



class AnalysisStatusView(APIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def get(self, request, pk):
        job = get_object_or_404(self.job_model, pk=pk, requested_by=request.user)
        if not job.can_access(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You no longer have access to this report's branch.")
        job.expire_if_needed(source="api")
        return Response(job_response(job))


class AttendanceAnalysisStatusView(AnalysisStatusView):
    job_model = AttendanceAnalysisJob


class PhysicalReportView(ReportView):
    statistics_service = staticmethod(physical_statistics)


class PhysicalAnalysisView(PhysicalReportView):
    http_method_names = ["post", "options"]

    def post(self, request):
        statistics = self.report_statistics(request, request.data)
        return queue_analysis(request.user, statistics, PhysicalAnalysisJob, generate_physical_analysis,
                              statistics["totals"]["completed_assessments"], request=request)


class PhysicalAnalysisStatusView(AnalysisStatusView):
    job_model = PhysicalAnalysisJob
