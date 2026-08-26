from django.contrib import admin
from .models import Branch, UserAccount

admin.site.register(UserAccount)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "region"]