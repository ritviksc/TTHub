from django.contrib import admin

from .models import AttendanceRecord, ProgrammeSession


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ["updated_at"]


@admin.register(ProgrammeSession)
class ProgrammeSessionAdmin(admin.ModelAdmin):
    list_display = ["branch", "date", "time", "activity", "created_by"]
    list_filter = ["branch", "date"]
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ["session", "participant", "status", "absence_reason", "updated_at"]
    list_filter = ["status", "absence_reason"]
