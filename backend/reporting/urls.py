from django.urls import path

from .views import (ReportModelsView, AttendanceAnalysisView, AttendanceReportView, AttendanceAnalysisStatusView,
                    PhysicalReportView, PhysicalAnalysisView, PhysicalAnalysisStatusView, ReportHistoryView)
from .models import AttendanceAnalysisJob, PhysicalAnalysisJob

urlpatterns = [
    path("attendance/history/", ReportHistoryView.as_view(job_model=AttendanceAnalysisJob)),
    path("attendance/history/<uuid:pk>/", ReportHistoryView.as_view(job_model=AttendanceAnalysisJob)),
    path("physical/history/", ReportHistoryView.as_view(job_model=PhysicalAnalysisJob)),
    path("physical/history/<uuid:pk>/", ReportHistoryView.as_view(job_model=PhysicalAnalysisJob)),
    path("models/", ReportModelsView.as_view(), name="report-models"),
    path("physical/", PhysicalReportView.as_view(), name="physical-report"),
    path("physical/analyse/", PhysicalAnalysisView.as_view(), name="physical-analysis"),
    path("physical/jobs/<uuid:pk>/", PhysicalAnalysisStatusView.as_view(), name="physical-analysis-status"),
    path("attendance/jobs/<uuid:pk>/", AttendanceAnalysisStatusView.as_view(), name="attendance-analysis-status"),
    path("attendance/", AttendanceReportView.as_view(), name="attendance-report"),
    path("attendance/analyse/", AttendanceAnalysisView.as_view(), name="attendance-analysis"),
]
