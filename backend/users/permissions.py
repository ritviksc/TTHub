from rest_framework.permissions import BasePermission
from .models import UserAccount

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserAccount.Role.SUPER_ADMIN
        )