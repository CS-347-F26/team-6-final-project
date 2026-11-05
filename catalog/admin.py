from django.contrib import admin
from .models import User, HistoricalMap

# Register your models here.
admin.site.register(User)

# Use a decorator to register and customize the HistoricalMap admin view
@admin.register(HistoricalMap)
class HistoricalMapAdmin(admin.ModelAdmin):
    # Define which columns appear in the list view
    list_display = ('title', 'year', 'is_georeferenced', 'created_at')
    # Add a sidebar to filter maps by status or year
    list_filter = ('is_georeferenced', 'year')

    # New addition: Grouping fields into sections in the detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'year', 'source')
        }),
        ('Map File', {
            'fields': ('image', 'is_georeferenced')
        }),
        ('Bounding Box Coordinates', {
            'fields': ('north', 'south', 'east', 'west')
        }),
    )
