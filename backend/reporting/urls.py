from django.urls import path

from .views import AttendanceAnalysisView, AttendanceReportView

urlpatterns = [
    path("attendance/", AttendanceReportView.as_view(), name="attendance-report"),
    path("attendance/analyse/", AttendanceAnalysisView.as_view(), name="attendance-analysis"),
]
