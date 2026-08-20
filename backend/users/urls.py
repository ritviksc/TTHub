from django.urls import path
from . import views

"""
/api/v1/auth/login/
/api/v1/auth/me/
/api/v1/dashboard/
"""

urlpatterns = [
    path('api/set-crsf-token', views.set_crsf_token, name='set_crsf_token'),
    path('api/login', views.login_view, name="login"),
    path('api/logout', views.logout_view, name='logout'),
    path('api/user', views.user, name='user'),
    path('api/register', views.register, name='register'),
]
