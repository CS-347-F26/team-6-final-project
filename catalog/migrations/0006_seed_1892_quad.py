from django.db import migrations

# Aligns the 1892 USGS "Harrisonburg Sheet" (1:125,000 reconnaissance map).
# 1. Browsers can't show the original .tif, so the map now points at a JPEG copy
#    (same scan, shrunk to 2500 px wide with Pillow, 2026-11-21).
# 2. The sheet covers exactly 38°00'-38°30' N and 78°30'-79°00' W, printed at its
#    corners. The control points are those four neatline corners, located on the
#    JPEG to about one pixel (~20 m), so no hand clicking was needed.
# ponytail: corners are NAD27 (as printed), used as if WGS84; the datum shift
# here is tens of meters, far below the 1892 survey's own accuracy.
OLD_IMAGE = "historical_maps/VA_Harrisonburg_189001_1892_125000_geo_q3EPDW0.tif"
NEW_IMAGE = "historical_maps/harrisonburg_1892_quad.jpg"

# Control points: (x, y) pixel on the JPEG -> (lat, lng) of that neatline corner
QUAD_POINTS = [
    (200.5, 162.0, 38.5, -79.0),  # top-left: 38°30' N, 79°00' W
    (2294.3, 162.0, 38.5, -78.5),  # top-right: 38°30' N, 78°30' W
    (200.8, 2807.3, 38.0, -79.0),  # bottom-left: 38°00' N, 79°00' W
    (2295.0, 2807.3, 38.0, -78.5),  # bottom-right: 38°00' N, 78°30' W
]

# What catalog.georef.apply_georeference() computes from those points for a
# 2500 x 3032 image, copied here so the migration doesn't depend on app code
QUAD_FIT = {
    "corners": {
        "topleft": [38.5306203, -79.0478437],
        "topright": [38.5306203, -78.4509],
        "bottomleft": [37.9575284, -79.0479805],
    },
    "north": 38.5306203,
    "south": 37.9575284,
    "east": -78.4509,
    "west": -79.0479805,
    "rms_error": 2.1,
}


# Swaps in the JPEG and adds the points + fit (skips DBs where someone already
# aligned the quad by hand, so their work isn't overwritten)
def seed_quad(apps, schema_editor):
    # Always fetch models via apps.get_model() so they are history-aware
    HistoricalMap = apps.get_model("catalog", "HistoricalMap")
    ControlPoint = apps.get_model("catalog", "ControlPoint")
    quad = HistoricalMap.objects.filter(title="Quadrangle for Harrisonburg, VA").first()
    if quad is None or ControlPoint.objects.filter(map=quad).exists():
        return

    quad.image = NEW_IMAGE
    ControlPoint.objects.bulk_create(
        ControlPoint(map=quad, x=x, y=y, lat=lat, lng=lng)
        for x, y, lat, lng in QUAD_POINTS
    )
    for field, value in QUAD_FIT.items():
        setattr(quad, field, value)
    quad.is_georeferenced = True
    quad.save()


# Undo: remove just these points and put the .tif back, so it can be rolled back
def unseed_quad(apps, schema_editor):
    HistoricalMap = apps.get_model("catalog", "HistoricalMap")
    ControlPoint = apps.get_model("catalog", "ControlPoint")
    quad = HistoricalMap.objects.filter(title="Quadrangle for Harrisonburg, VA").first()
    if quad is None:
        return
    for x, y, lat, lng in QUAD_POINTS:
        ControlPoint.objects.filter(map=quad, x=x, y=y, lat=lat, lng=lng).delete()
    if not ControlPoint.objects.filter(map=quad).exists():
        quad.image = OLD_IMAGE
        quad.corners = None
        quad.rms_error = None
        quad.is_georeferenced = False
        quad.save()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_seed_harrisonburg_georeference"),
    ]

    operations = [
        migrations.RunPython(seed_quad, unseed_quad),
    ]
