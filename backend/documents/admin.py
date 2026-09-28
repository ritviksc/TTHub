from django.contrib import admin

from .models import Document, Folder


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["name", "branch", "participant", "folder", "uploaded_by", "uploaded_at"]
    search_fields = ["name"]


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ["name", "branch", "parent", "created_by", "created_at"]
    search_fields = ["name"]
