from django.urls import path

from . import views

"""
GET    /api/participants/                    list, filtered by ?branch= ?is_active= ?search=
POST   /api/participants/                    create
GET    /api/participants/<uuid>/             retrieve
PATCH  /api/participants/<uuid>/             edit
POST   /api/participants/<uuid>/deactivate/  soft delete
"""

urlpatterns = [
    path("", views.ParticipantListCreateView.as_view()),
    path("<uuid:pk>/", views.ParticipantDetailView.as_view()),
    path("<uuid:pk>/deactivate/", views.ParticipantDeactivateView.as_view()),
]
