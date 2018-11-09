from django.contrib import admin
from .models import Presentation


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    ordering = ["-date"]
    list_display = ["title", "date", "type", "conference_title"]
    prepopulated_fields = {"slug": ["title"]}
