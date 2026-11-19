from django.db import migrations


# Corrects the two maps seeded in 0002:
# - Gray's New Map of Harrisonburg was surveyed in 1877 (David Rumsey catalog),
#   not 1867.
# - Neither map is really aligned yet: their bounds were placeholders and they
#   have no control points. Each gets is_georeferenced=True again once it is
#   georeferenced (Harrisonburg by hand, the 1892 quad from its GeoTIFF).
def fix_seed_maps(apps, schema_editor):
    # Always fetch the model via apps.get_model() so it is history-aware
    HistoricalMap = apps.get_model("catalog", "HistoricalMap")
    HistoricalMap.objects.filter(title="Harrisonburg Map", year=1867).update(year=1877)
    HistoricalMap.objects.filter(
        title__in=["Harrisonburg Map", "Quadrangle for Harrisonburg, VA"]
    ).update(is_georeferenced=False)


# Undo, so the migration can be rolled back cleanly
def unfix_seed_maps(apps, schema_editor):
    HistoricalMap = apps.get_model("catalog", "HistoricalMap")
    HistoricalMap.objects.filter(title="Harrisonburg Map", year=1877).update(year=1867)
    HistoricalMap.objects.filter(
        title__in=["Harrisonburg Map", "Quadrangle for Harrisonburg, VA"]
    ).update(is_georeferenced=True)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_control_points"),
    ]

    operations = [
        migrations.RunPython(fix_seed_maps, unfix_seed_maps),
    ]
