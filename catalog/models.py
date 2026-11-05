from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# === USER ===
# Custom user model. It's empty on purpose. Django's AbstractUser already gives us
# id, username, email, a hashed password, and date_joined, which covers everything
# in the project plan's User object. Having our own class means we can add fields
# later without a painful migration.
# IMPORTANT: set AUTH_USER_MODEL = "<your_app_name>.User" in settings.py BEFORE
# running your first migration.
class User(AbstractUser):
    pass


# === HISTORICAL MAP ===
# One historical map image for a specific year. The four bounds fields tell the
# front end where to stretch the image over the live map (the corners of the
# overlay, in latitude and longitude).
class HistoricalMap(models.Model):
    # Basic info about the map
    title = models.CharField(max_length=200)
    year = models.PositiveIntegerField(db_index=True)  # the year the map shows
    source = models.CharField(max_length=300, blank=True)  # where the map came from

    # The map image itself (ImageField needs Pillow installed)
    image = models.ImageField(upload_to="historical_maps/")

    # Bounding box: north and south are latitudes, east and west are longitudes
    north = models.FloatField()
    south = models.FloatField()
    east = models.FloatField()
    west = models.FloatField()

    # False means the image is stored but not aligned to the real world yet
    is_georeferenced = models.BooleanField(default=False)

    # Set automatically when the map is first added
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Show maps oldest to newest, then alphabetically
        ordering = ["year", "title"]
        # Speeds up the "which maps cover this spot" lookup
        indexes = [models.Index(fields=["south", "north", "west", "east"])]

    # Rejects flipped bounds (for example north below south) in the admin site
    def clean(self):
        if self.north is not None and self.south is not None and self.north <= self.south:
            raise ValidationError("North must be greater than south.")
        if self.east is not None and self.west is not None and self.east <= self.west:
            raise ValidationError("East must be greater than west.")

    # How the map shows up in the admin list, like "Downtown Harrisonburg (1885)"
    def __str__(self):
        return f"{self.title} ({self.year})"
