from django.urls import path

from . import views

"""
GET    /api/folders/                          list, filtered by ?scope=organisation or ?branch=
POST   /api/folders/                          create, {name, parent?, branch?}
GET    /api/folders/<uuid>/                   retrieve
PATCH  /api/folders/<uuid>/                   rename (name) or move (parent)
DELETE /api/folders/<uuid>/                   delete, refused while it has folders or documents in it
"""

urlpatterns = [
    path("", views.FolderListCreateView.as_view()),
    path("<uuid:pk>/", views.FolderDetailView.as_view()),
]
