from django.contrib import admin
from .models import FilmRoll, FrameNote, Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "is_archived", "updated_at")
    list_filter = ("is_archived",)
    search_fields = ("title", "description")

@admin.register(FilmRoll)
class FilmRollAdmin(admin.ModelAdmin):
    list_display = ("__str__", "project", "stock", "status", "updated_at")
    list_filter = ("status", "format")

@admin.register(FrameNote)
class FrameNoteAdmin(admin.ModelAdmin):
    list_display = ("frame_number", "roll", "note", "created_at")
    list_filter = ("roll",)