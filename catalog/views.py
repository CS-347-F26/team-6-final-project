from django.shortcuts import render

from .models import HistoricalMap


def home(request):
    maps = HistoricalMap.objects.all()
    return render(request, "catalog/home.html", {"maps": maps})


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