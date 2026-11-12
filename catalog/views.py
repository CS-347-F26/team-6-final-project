from django.shortcuts import render
from django.db.models import Q
from .models import HistoricalMap
from .forms import MapSearchForm


def home(request):
    # Only bind the form data if the user has actually submitted a search (request.GET contains data).
    # Otherwise, display a fresh, unbound form.
    if request.GET:
        form = MapSearchForm(request.GET)
    else:
        form = MapSearchForm()
        
    maps = HistoricalMap.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get('query')
        year = form.cleaned_data.get('year')
        lat = form.cleaned_data.get('lat')
        lng = form.cleaned_data.get('lng')

        # Filter by name/location text in the title or source
        if query:
            maps = maps.filter(
                Q(title__icontains=query) | 
                Q(source__icontains=query)
            )
        
        # Filter by exact year
        if year:
            maps = maps.filter(year=year)

        # Filter by coordinates (is the point inside the map's bounding box?)
        if lat is not None and lng is not None:
            maps = maps.filter(
                south__lte=lat, north__gte=lat,
                west__lte=lng, east__gte=lng
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
        'num_maps': num_maps,
        'num_georeferenced': num_georeferenced,
        'num_pending': num_pending,
    }

    # Render the HTML template with the data in the context variable
    return render(request, 'index.html', context=context)