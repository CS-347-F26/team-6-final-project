from django.shortcuts import render

from .models import HistoricalMap


def home(request):
    maps = HistoricalMap.objects.all()
    return render(request, "catalog/home.html", {"maps": maps})


def settings(request):
    return render(request, "catalog/settings.html")
