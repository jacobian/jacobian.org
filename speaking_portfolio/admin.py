from django.contrib import admin
from .models import Presentation, Conference, Coverage


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    ordering = ["-start_date", "title"]
    list_display = ["title", "link", "start_date"]


class CoverageInline(admin.TabularInline):
    model = Coverage
    extra = 1
    fields = ["type", "url"]


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    ordering = ["-date"]
    list_display = ["title", "date", "type", "conference"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [CoverageInline]
