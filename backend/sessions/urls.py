from django.urls import path

from . import views


urlpatterns = [
    path("", views.SessionListCreateView.as_view()),
    path("<uuid:pk>/", views.SessionDetailView.as_view()),
    path(
        "<uuid:pk>/attendance/<uuid:attendance_id>/",
        views.AttendanceRecordDetailView.as_view(),
    ),
]
