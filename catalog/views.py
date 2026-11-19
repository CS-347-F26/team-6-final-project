import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _

from .forms import MapSearchForm
from .georef import apply_georeference
from .models import ControlPoint, HistoricalMap


def home(request):
    # Only bind the form data if the user has actually submitted a search (request.GET contains data).
    # Otherwise, display a fresh, unbound form.
    if request.GET:
        form = MapSearchForm(request.GET)
    else:
        form = MapSearchForm()

    maps = HistoricalMap.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get("query")
        year = form.cleaned_data.get("year")
        lat = form.cleaned_data.get("lat")
        lng = form.cleaned_data.get("lng")

        # Filter by name/location text in the title or source
        if query:
            maps = maps.filter(Q(title__icontains=query) | Q(source__icontains=query))

        # Filter by exact year
        if year:
            maps = maps.filter(year=year)

        # Filter by coordinates (is the point inside the map's bounding box?)
        if lat is not None and lng is not None:
            maps = maps.filter(
                south__lte=lat, north__gte=lat, west__lte=lng, east__gte=lng
            )

    return render(request, "catalog/home.html", {"maps": maps, "form": form})


def settings(request):
    return render(request, "catalog/settings.html")


def index(request):
    """View function for home page of site."""

    # Generate total count of Historical Maps
    num_maps = HistoricalMap.objects.count()

    # Count maps based on their georeferenced status
    num_georeferenced = HistoricalMap.objects.filter(is_georeferenced=True).count()
    num_pending = HistoricalMap.objects.filter(is_georeferenced=False).count()

    context = {
        "num_maps": num_maps,
        "num_georeferenced": num_georeferenced,
        "num_pending": num_pending,
    }

    # Render the HTML template with the data in the context variable
    return render(request, "index.html", context=context)


def help_page(request):
    """View function for the Help/Tooltips page."""
    return render(request, "catalog/help.html")


# === GEOREFERENCE TOOL (staff only) ===
# GET: shows the scan next to a live map so staff can click matching points.
# POST: receives the points as JSON, replaces the map's control points, fits the
# alignment, and answers with the overlay corners and error (or a 400 + message).
@staff_member_required
def georeference(request, pk):
    hmap = get_object_or_404(HistoricalMap, pk=pk)

    if request.method == "POST":
        # Parse and check every point before touching the database
        try:
            raw_points = json.loads(request.body)["points"]
            points = [_clean_point(p, hmap) for p in raw_points]
        except (ValueError, KeyError, TypeError) as error:
            return JsonResponse({"error": str(error) or "Invalid points."}, status=400)

        # All-or-nothing: if the fit fails, the old points are kept
        try:
            with transaction.atomic():
                hmap.control_points.all().delete()
                ControlPoint.objects.bulk_create(
                    ControlPoint(map=hmap, **point) for point in points
                )
                apply_georeference(hmap)
        except ValueError as error:
            return JsonResponse({"error": str(error)}, status=400)

        return JsonResponse({"corners": hmap.corners, "rms_error": hmap.rms_error})

    # Everything the page's JavaScript needs, passed safely via json_script
    tool_data = {
        "imageUrl": hmap.image.url,
        "width": hmap.image.width,
        "height": hmap.image.height,
        "corners": hmap.corners,
        "points": list(hmap.control_points.values("x", "y", "lat", "lng")),
        "saveUrl": reverse("georeference", args=[hmap.pk]),
        # Script status messages, translated here so json_script escapes them
        "messages": {
            "pickScan": _("Click a spot on the scanned map."),
            "pickWorld": _("Now click the same spot on today's map."),
            "needMore": _("Add at least 3 pairs to fit the map."),
            "ready": _("Ready to fit. Press Fit & save."),
            "saving": _("Fitting…"),
            "saved": _("Saved. Average error: ± %s m"),
            "savedNoError": _(
                "Saved. Add a 4th pair to measure how accurate the fit is."
            ),
            "failed": _("Could not save:"),
            "remove": _("Remove pair"),
        },
    }
    return render(
        request, "catalog/georeference.html", {"map": hmap, "tool_data": tool_data}
    )


# Turns one posted point into clean floats, rejecting anything off the image or
# off the globe. Raises ValueError with a message the tool can show.
def _clean_point(point, hmap):
    x, y = float(point["x"]), float(point["y"])
    lat, lng = float(point["lat"]), float(point["lng"])
    if not (0 <= x <= hmap.image.width and 0 <= y <= hmap.image.height):
        raise ValueError("A point is outside the scanned image.")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError("A point has an impossible latitude or longitude.")
    return {"x": x, "y": y, "lat": lat, "lng": lng}
