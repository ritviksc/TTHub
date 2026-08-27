from django.urls import path

from . import views

"""
GET  /api/kapa/   list, filtered by ?search= and ?no_manager=true
POST /api/kapa/   create (Super Admin only)
"""

urlpatterns = [
    path("", views.KapaListCreateView.as_view()),
]
