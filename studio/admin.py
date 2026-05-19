from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "is_archived", "updated_at")
    list_filter = ("is_archived",)
    search_fields = ("title", "description")
