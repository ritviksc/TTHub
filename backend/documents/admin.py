from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["name", "branch", "participant", "uploaded_by", "uploaded_at"]
    search_fields = ["name"]
