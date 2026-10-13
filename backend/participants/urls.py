from django.urls import path

from . import views

"""
GET    /api/participants/                    list, filtered by ?branch= ?is_active= ?search=
POST   /api/participants/                    create
GET    /api/participants/<uuid>/             retrieve
PATCH  /api/participants/<uuid>/             edit
POST   /api/participants/<uuid>/deactivate/  soft delete
POST   /api/participants/<uuid>/reactivate/  restore active status
"""

urlpatterns = [
    path("feedback/", views.FeedbackListCreateView.as_view()),
    path("<uuid:pk>/gp-document/", views.ParticipantFileView.as_view(document=True)),
    path("<uuid:pk>/photo/", views.ParticipantFileView.as_view(), name="participant-photo"),
    path("<uuid:pk>/attendance/", views.ParticipantAttendanceView.as_view()),
    path("", views.ParticipantListCreateView.as_view()),
    path("<uuid:pk>/", views.ParticipantDetailView.as_view()),
    path("<uuid:pk>/deactivate/", views.ParticipantDeactivateView.as_view()),
    path("<uuid:pk>/reactivate/", views.ParticipantReactivateView.as_view()),
]
