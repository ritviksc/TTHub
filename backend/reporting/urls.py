from django.urls import path

from .views import AttendanceAnalysisView, AttendanceReportView, AttendanceAnalysisStatusView

urlpatterns = [
    path("attendance/jobs/<uuid:pk>/", AttendanceAnalysisStatusView.as_view(), name="attendance-analysis-status"),
    path("attendance/", AttendanceReportView.as_view(), name="attendance-report"),
    path("attendance/analyse/", AttendanceAnalysisView.as_view(), name="attendance-analysis"),
]
