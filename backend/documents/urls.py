from django.urls import path

from . import views

"""
GET    /api/documents/                list, filtered by ?scope= ?branch= ?participant=
POST   /api/documents/                upload
DELETE /api/documents/<uuid>/         delete
GET    /api/documents/<uuid>/download/ download the file
"""

urlpatterns = [
    path("", views.DocumentListCreateView.as_view()),
    path("<uuid:pk>/", views.DocumentDetailView.as_view()),
    path("<uuid:pk>/download/", views.DocumentDownloadView.as_view()),
]
