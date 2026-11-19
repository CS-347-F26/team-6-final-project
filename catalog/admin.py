from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import ControlPoint, HistoricalMap, User

# Register your models here.
admin.site.register(User)


# Control points edited right inside a map's admin page
class ControlPointInline(admin.TabularInline):
    model = ControlPoint
    extra = 0


# Use a decorator to register and customize the HistoricalMap admin view
@admin.register(HistoricalMap)
class HistoricalMapAdmin(admin.ModelAdmin):
    # Define which columns appear in the list view
    list_display = ("title", "year", "is_georeferenced", "rms_error", "created_at")
    inlines = (ControlPointInline,)
    # Fitted values are computed by the georeference tool, so they're read-only here
    readonly_fields = ("georeference_link", "corners", "rms_error")
    # Add a sidebar to filter maps by status or year
    list_filter = ("is_georeferenced", "year")

    # New addition: Grouping fields into sections in the detail view
    fieldsets = (
        ("Basic Information", {"fields": ("title", "year", "source")}),
        ("Map File", {"fields": ("image", "is_georeferenced")}),
        ("Bounding Box Coordinates", {"fields": ("north", "south", "east", "west")}),
        (
            "Georeferencing",
            {"fields": ("georeference_link", "corners", "rms_error")},
        ),
    )

    # A link from the admin page to the click-to-align tool
    @admin.display(description="Georeference tool")
    def georeference_link(self, obj):
        if not obj.pk:
            return "Save the map first."
        url = reverse("georeference", args=[obj.pk])
        return format_html('<a href="{}">Open the georeferencing tool</a>', url)
