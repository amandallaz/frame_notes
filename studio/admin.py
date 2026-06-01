from django.contrib import admin

from .models import FilmRoll, FrameNote, Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "is_archived", "updated_at")
    list_filter = ("is_archived",)
    search_fields = ("title", "description")

@admin.register(FilmRoll)
class FilmRollAdmin(admin.ModelAdmin):
    list_display = ("__str__", "projects_display", "stock", "status", "updated_at")
    list_filter = ("status", "format", "projects")
    filter_horizontal = ("projects",)

    @admin.display(description="Projects")
    def projects_display(self, obj):
        titles = obj.project_titles()
        return ", ".join(titles) if titles else "—"

@admin.register(FrameNote)
class FrameNoteAdmin(admin.ModelAdmin):
    list_display = ("frame_number", "roll", "is_favorite", "note", "scan_filename", "image", "created_at")
    list_filter = ("roll", "is_favorite")