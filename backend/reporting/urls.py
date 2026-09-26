from django.urls import path

from .views import (AttendanceAnalysisView, AttendanceReportView, AttendanceAnalysisStatusView,
                    PhysicalReportView, PhysicalAnalysisView, PhysicalAnalysisStatusView)

urlpatterns = [
    path("physical/", PhysicalReportView.as_view(), name="physical-report"),
    path("physical/analyse/", PhysicalAnalysisView.as_view(), name="physical-analysis"),
    path("physical/jobs/<uuid:pk>/", PhysicalAnalysisStatusView.as_view(), name="physical-analysis-status"),
    path("attendance/jobs/<uuid:pk>/", AttendanceAnalysisStatusView.as_view(), name="attendance-analysis-status"),
    path("attendance/", AttendanceReportView.as_view(), name="attendance-report"),
    path("attendance/analyse/", AttendanceAnalysisView.as_view(), name="attendance-analysis"),
]
