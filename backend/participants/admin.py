from django.contrib import admin

from .models import Participant


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "branch", "is_active"]
    list_filter = ["branch", "is_active"]
    search_fields = ["first_name", "last_name", "preferred_name"]
