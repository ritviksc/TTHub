from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from kombu.exceptions import OperationalError
from redis.exceptions import RedisError
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsBranchManager, IsSuperAdmin
from .models import AttendanceAnalysisJob
from .serializers import AttendanceReportRequestSerializer
from .services.attendance import attendance_statistics
from .tasks import generate_attendance_analysis


def job_response(job):
    data = {"job_id": str(job.pk), "status": job.status}
    if job.status == job.Status.SUCCEEDED:
        data.update(statistics=job.statistics, narrative=job.narrative)
    elif job.status == job.Status.FAILED:
        data["detail"] = job.error
    return data


class AttendanceReportView(APIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def report_statistics(self, request, data):
        serializer = AttendanceReportRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            return attendance_statistics(user=request.user, **serializer.validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": " ".join(exc.messages)}) from exc

    def get(self, request):
        return Response(self.report_statistics(request, request.query_params))


class AttendanceAnalysisView(AttendanceReportView):
    http_method_names = ["post", "options"]

    def post(self, request):
        # Validate permissions and save the exact figures before queueing any AI work.
        statistics = self.report_statistics(request, request.data)
        job = AttendanceAnalysisJob.objects.create(
            requested_by=request.user, branch_id=statistics["scope"]["branch_id"],
            statistics=statistics,
            status="queued" if statistics["totals"]["finalised_sessions"] else "succeeded",
        )
        if job.status == job.Status.SUCCEEDED:
            return Response(job_response(job))
        try:
            generate_attendance_analysis.apply_async(args=[str(job.pk)], expires=job.expires_at)
        except (OperationalError, RedisError, OSError):
            job.status = job.Status.FAILED
            job.error = "The analysis queue is unavailable. Please try again."
            job.save(update_fields=["status", "error"])
            return Response(job_response(job), status=503)
        return Response(job_response(job), status=202)


class AttendanceAnalysisStatusView(APIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def get(self, request, pk):
        job = get_object_or_404(AttendanceAnalysisJob, pk=pk, requested_by=request.user)
        if not job.can_access(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You no longer have access to this report's branch.")
        job.expire_if_needed()
        return Response(job_response(job))
