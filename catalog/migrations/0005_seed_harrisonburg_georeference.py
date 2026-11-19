from django.db import migrations

# Harrisonburg's alignment, made with the staff georeferencing tool on 2026-11-19
# and copied here so every teammate's database (and the deployed site) gets the
# aligned map without clicking anything.
# Control points: (x, y) pixel on the scan -> (lat, lng) on today's map.
HARRISONBURG_POINTS = [
    (203.4, 388.03, 38.4493913, -78.8686041),
    (211.8, 356.05, 38.4504279, -78.8683262),
    (161.3, 345.04, 38.4506969, -78.8702788),
]

# The fit those points produced (same values the tool saved)
HARRISONBURG_FIT = {
    "corners": {
        "topleft": [38.4614661, -78.8769457],
        "topright": [38.4622086, -78.8596053],
        "bottomleft": [38.4369061, -78.8758800],
    },
    "north": 38.4622086,
    "south": 38.4369061,
    "east": -78.8585396,
    "west": -78.8769457,
    # 3 points always fit exactly, so the error can't be measured yet
    "rms_error": None,
}


# Adds the points and the fit, unless the map already has points (so this never
# overwrites someone's own georeferencing work in their local database)
def seed_harrisonburg(apps, schema_editor):
    HistoricalMap = apps.get_model("catalog", "HistoricalMap")
    ControlPoint = apps.get_model("catalog", "ControlPoint")
    hmap = HistoricalMap.objects.filter(title="Harrisonburg Map").first()
    if hmap is None or ControlPoint.objects.filter(map=hmap).exists():
        return

    ControlPoint.objects.bulk_create(
        ControlPoint(map=hmap, x=x, y=y, lat=lat, lng=lng)
        for x, y, lat, lng in HARRISONBURG_POINTS
    )
    for field, value in HARRISONBURG_FIT.items():
        setattr(hmap, field, value)
    hmap.is_georeferenced = True
    hmap.save()


# Undo: removes only the points this migration added, and clears the fit if no
# other points are left
def unseed_harrisonburg(apps, schema_editor):
    HistoricalMap = apps.get_model("catalog", "HistoricalMap")
    ControlPoint = apps.get_model("catalog", "ControlPoint")
    hmap = HistoricalMap.objects.filter(title="Harrisonburg Map").first()
    if hmap is None:
        return
    for x, y, lat, lng in HARRISONBURG_POINTS:
        ControlPoint.objects.filter(map=hmap, x=x, y=y, lat=lat, lng=lng).delete()
    if not ControlPoint.objects.filter(map=hmap).exists():
        hmap.corners = None
        hmap.rms_error = None
        hmap.is_georeferenced = False
        hmap.save()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_fix_seed_maps"),
    ]

    operations = [
        migrations.RunPython(seed_harrisonburg, unseed_harrisonburg),
    ]
