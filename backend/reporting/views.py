from django.core.exceptions import ImproperlyConfigured, ValidationError as DjangoValidationError
from openai import APIError
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsBranchManager, IsSuperAdmin
from .serializers import AttendanceReportRequestSerializer
from .services.attendance import analyse_attendance, attendance_statistics


class AttendanceReportView(APIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def report_arguments(self, request, data):
        serializer = AttendanceReportRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return {"user": request.user, **serializer.validated_data}

    def get(self, request):
        arguments = self.report_arguments(request, request.query_params)
        try:
            return Response(attendance_statistics(**arguments))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": " ".join(exc.messages)}) from exc


class AttendanceAnalysisView(AttendanceReportView):
    http_method_names = ["post", "options"]

    def post(self, request):
        arguments = self.report_arguments(request, request.data)
        try:
            return Response(analyse_attendance(**arguments))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": " ".join(exc.messages)}) from exc
        except ImproperlyConfigured:
            return Response({"detail": "AI analysis is not configured. Attendance statistics are still available."}, status=503)
        except (APIError, ValueError):
            # Do not expose provider URLs, credentials, or raw response bodies.
            return Response({"detail": "AI analysis could not be completed. Please try again. Attendance statistics are still available."}, status=502)
