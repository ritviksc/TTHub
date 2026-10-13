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
    path("logout/", views.logout_view),
    path("staff/", views.StaffCreateView.as_view()),
    path("staff/list/", views.StaffListView.as_view()),
    path(
    "staff/<uuid:pk>/",
    views.StaffDetailView.as_view()
    ),
    path("staff/<uuid:pk>/deactivate/", views.StaffDeactivateView.as_view()),
    path("staff/<uuid:pk>/reactivate/", views.StaffReactivateView.as_view()),
    path("me/", views.me_view),
]
