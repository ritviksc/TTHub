from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Branch, UserAccount


@admin.register(UserAccount)
class UserAccountAdmin(UserAdmin):
    model = UserAccount
    list_display = ["username", "email", "role", "branch", "is_active"]

    fieldsets = UserAdmin.fieldsets + (
        ("Taurite Tū", {"fields": ("role", "branch")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Taurite Tū", {"fields": ("role", "branch")}),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "region"]