import pathlib

# I solemnly swear I'm not pasting this where I pasted the several preceding pastes!
# this is in locallibrary/catalog/urls.py which I *just* created
# the current file is definitely NOT locallibrary/locallibrary_config/urls.py!
_this_dir = pathlib.Path(__file__).resolve().parent
assert not (_this_dir / "settings.py").exists(), (
    "catalog/urls.py should NOT have a sibling named settings.py"
)
assert (_this_dir / "models.py").exists(), (
    "catalog/urls.py should have a sibling named models.py"
)

from django.urls import path
from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    path("", views.home, name="home"),  # Ensure home is mapped
    path("settings/", views.settings, name="settings"),  # Ensure settings is mapped
    path("help/", views.help_page, name="help"),
    # Staff-only tool for aligning a scanned map to the real world
    path("maps/<int:pk>/georeference/", views.georeference, name="georeference"),
    path("map/", views.map_view, name="map"),
]
