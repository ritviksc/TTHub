from django.urls import path
from . import views

"""
Frontend
GET  /login                show login page
POST /api/auth/login/      submit credentials

Backend
POST /api/auth/login/      authenticate + create session
"""


urlpatterns = [    
    path("login/", views.login_view),
    path("csrf/", views.csrf_view),
    path("logout/", views.logout),
    path("staff/", views.StaffCreateView.as_view()),
]
