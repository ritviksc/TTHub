from django.urls import path

from . import views
from .quarters import BranchQuartersView
from .models import UserAccount

"""
GET    /api/branches/                           list, filtered by ?search= and ?no_manager=true
POST   /api/branches/                           create (Super Admin only)
GET    /api/branches/<uuid>/                    retrieve
PATCH  /api/branches/<uuid>/                    edit (Super Admin only)
DELETE /api/branches/<uuid>/                    delete, refused while staff or participants remain

POST   /api/branches/<uuid>/managers/           assign a branch manager
DELETE /api/branches/<uuid>/managers/<uuid>/    unassign a branch manager
POST   /api/branches/<uuid>/instructors/        assign an instructor
DELETE /api/branches/<uuid>/instructors/<uuid>/ unassign an instructor

The staff routes are the same two views bound to a different role, so both
roles get identical rules rather than two implementations that can drift.
"""

MANAGER = UserAccount.Role.BRANCH_MANAGER
INSTRUCTOR = UserAccount.Role.INSTRUCTOR

urlpatterns = [
    path("<uuid:pk>/quarters/<int:year>/", BranchQuartersView.as_view()),
    path("", views.BranchListCreateView.as_view()),
    path("<uuid:pk>/", views.BranchDetailView.as_view()),

    path("<uuid:pk>/managers/", views.BranchStaffView.as_view(role=MANAGER)),
    path("<uuid:pk>/managers/<uuid:user_id>/", views.BranchStaffDetailView.as_view(role=MANAGER)),

    path("<uuid:pk>/instructors/", views.BranchStaffView.as_view(role=INSTRUCTOR)),
    path("<uuid:pk>/instructors/<uuid:user_id>/", views.BranchStaffDetailView.as_view(role=INSTRUCTOR)),
]
