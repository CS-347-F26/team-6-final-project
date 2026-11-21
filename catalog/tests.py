import json

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .georef import apply_georeference, fit_affine
from .models import ControlPoint, HistoricalMap


# A known rotated + scaled transform (pixel -> lat, lng) used to fake control points
def _true_latlng(x, y):
    return (38.46 + 2e-6 * x - 1.1e-5 * y, -78.88 + 1.3e-5 * x + 3e-6 * y)


# A new, unaligned map that reuses the real Harrisonburg scan (452 x 768 px).
# Tests use this because migration 0005 already aligns the seeded Harrisonburg map.
def _blank_map(title="Test map"):
    return HistoricalMap.objects.create(
        title=title,
        year=1877,
        image="historical_maps/HarrisonburgMap_6dzXitZ.jpg",
        north=0,
        south=0,
        east=0,
        west=0,
    )


# Checks the affine fit recovers a known transform and rejects bad input
class FitAffineTests(SimpleTestCase):
    def test_recovers_known_transform(self):
        points = [
            (x, y, *_true_latlng(x, y))
            for x, y in [(10, 20), (400, 50), (60, 700), (300, 500)]
        ]
        to_latlng = fit_affine(points)
        # Check a spot that wasn't one of the control points
        for got, want in zip(to_latlng(452, 768), _true_latlng(452, 768)):
            self.assertAlmostEqual(got, want, places=9)

    def test_needs_three_points(self):
        with self.assertRaises(ValueError):
            fit_affine([(0, 0, 38.4, -78.8), (10, 10, 38.5, -78.9)])

    def test_rejects_points_in_a_line(self):
        with self.assertRaises(ValueError):
            fit_affine(
                [(0, 0, 38.4, -78.8), (10, 10, 38.5, -78.9), (20, 20, 38.6, -79.0)]
            )


# Checks apply_georeference stores corners, bounds, and error on the map
class ApplyGeoreferenceTests(TestCase):
    def setUp(self):
        self.hmap = _blank_map()

    # Adds perfect control points generated from the known transform
    def add_points(self, pixels):
        for x, y in pixels:
            lat, lng = _true_latlng(x, y)
            ControlPoint.objects.create(map=self.hmap, x=x, y=y, lat=lat, lng=lng)

    def test_stores_corners_bounds_and_error(self):
        self.add_points([(10, 20), (400, 50), (60, 700), (300, 500)])
        apply_georeference(self.hmap)
        self.hmap.refresh_from_db()

        self.assertTrue(self.hmap.is_georeferenced)
        for got, want in zip(self.hmap.corners["topleft"], _true_latlng(0, 0)):
            self.assertAlmostEqual(got, want, places=9)
        # Bounding box covers the rotated image; error is ~0 for perfect points
        self.assertGreater(self.hmap.north, self.hmap.south)
        self.assertGreater(self.hmap.east, self.hmap.west)
        self.assertLess(self.hmap.rms_error, 0.01)

    # 3 points always fit exactly, so no error is reported (None = unknown)
    def test_three_points_have_no_error_value(self):
        self.add_points([(10, 20), (400, 50), (60, 700)])
        apply_georeference(self.hmap)
        self.hmap.refresh_from_db()
        self.assertIsNone(self.hmap.rms_error)


# Checks the custom middleware logs each request with method, path, and status
class RequestLoggingMiddlewareTests(TestCase):
    def test_request_is_logged(self):
        with self.assertLogs("catalog", level="INFO") as logs:
            self.client.get("/")
        # Columns: method, status, time, path
        self.assertRegex(logs.output[0], r"GET\s+200\s+\d+ms\s+/\s")

    # Static file requests should not be logged at all
    def test_static_request_is_skipped(self):
        with self.assertNoLogs("catalog", level="INFO"):
            self.client.get("/static/missing.css")


class HomePageTests(TestCase):
    def test_homepage_loads(self):
        response = self.client.get("/about/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "History, right where you are.")
        self.assertContains(response, "Historical maps")
        self.assertContains(response, 'href="/settings/"')
        self.assertNotContains(response, ">Explore maps</a>")

    def test_settings_page_loads(self):
        response = self.client.get("/settings/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Settings")
        self.assertContains(response, "Language")
        self.assertContains(response, 'action="/i18n/setlang/"')

    def test_selecting_spanish_translates_settings_and_homepage(self):
        # The homepage only shows the empty-state text when there are no maps
        HistoricalMap.objects.all().delete()
        response = self.client.post(
            "/i18n/setlang/",
            {"language": "es", "next": "/settings/"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Idioma")
        self.assertContains(response, "Guardar idioma")
        self.assertContains(response, "Más preferencias próximamente")
        homepage = self.client.get("/about/")
        self.assertEqual(homepage.status_code, 200)
        self.assertContains(homepage, "Historia, justo donde estás.")
        self.assertContains(homepage, "Estamos agregando mapas")

    def test_homepage_shows_empty_state_without_maps(self):
        # Migration 0002 seeds two maps; remove them to see the empty state
        HistoricalMap.objects.all().delete()
        response = self.client.get("/about/")

        self.assertContains(response, "Maps are being added")

    def test_map_search_fields_have_visible_labels(self):
        response = self.client.get("/about/")

        self.assertContains(
            response,
            '<form class="search-form" method="GET" action="/about/" aria-label="Search historical maps">',
        )
        for field_id, label in (
            ("id_query", "Search by place:"),
            ("id_year", "Year:"),
            ("id_lat", "Latitude:"),
            ("id_lng", "Longitude:"),
        ):
            self.assertContains(response, f'<label for="{field_id}">{label}</label>')
            self.assertContains(response, f'id="{field_id}"')

    def test_map_search_field_labels_are_translated(self):
        self.client.post("/i18n/setlang/", {"language": "es", "next": "/"})
        response = self.client.get("/about/")

        self.assertContains(
            response, '<label for="id_query">Buscar por lugar:</label>'
        )
        self.assertContains(response, '<label for="id_year">Año:</label>')
        self.assertContains(response, '<label for="id_lat">Latitud:</label>')
        self.assertContains(response, '<label for="id_lng">Longitud:</label>')

    def test_homepage_lists_historical_maps(self):
        HistoricalMap.objects.create(
            title="Downtown Harrisonburg",
            year=1885,
            image="historical_maps/harrisonburg.png",
            north=38.5,
            south=38.4,
            east=-78.8,
            west=-78.9,
        )

        response = self.client.get("/about/")

        self.assertContains(response, "Downtown Harrisonburg")
        self.assertContains(response, "1885")


# Checks the seed migrations (the test DB runs every migration):
# 0004 corrected the year, 0005 aligned Harrisonburg; the 1892 quad isn't aligned yet
class SeedMapTests(TestCase):
    def setUp(self):
        self.harrisonburg = HistoricalMap.objects.get(title="Harrisonburg Map")

    def test_seed_maps_are_corrected(self):
        self.assertEqual(self.harrisonburg.year, 1877)
        quad = HistoricalMap.objects.get(title="Quadrangle for Harrisonburg, VA")
        self.assertFalse(quad.is_georeferenced)

    def test_harrisonburg_is_aligned_out_of_the_box(self):
        self.assertTrue(self.harrisonburg.is_georeferenced)
        self.assertEqual(self.harrisonburg.control_points.count(), 3)
        # It shows up on the main map page with no clicking needed
        self.assertContains(self.client.get("/"), "Harrisonburg Map")

    # The corners stored in 0005 must match a fresh fit of its points (within ~1 m)
    def test_seeded_corners_match_seeded_points(self):
        points = list(
            self.harrisonburg.control_points.values_list("x", "y", "lat", "lng")
        )
        to_latlng = fit_affine(points)
        width, height = self.harrisonburg.image.width, self.harrisonburg.image.height
        pixels = {"topleft": (0, 0), "topright": (width, 0), "bottomleft": (0, height)}
        for name, (x, y) in pixels.items():
            for got, want in zip(self.harrisonburg.corners[name], to_latlng(x, y)):
                self.assertAlmostEqual(got, want, delta=1e-5)


# Checks the staff-only georeferencing tool: who can open it, saving, and bad input
class GeoreferenceToolTests(TestCase):
    def setUp(self):
        self.hmap = _blank_map()
        self.url = reverse("georeference", args=[self.hmap.pk])
        User = get_user_model()
        self.staff = User.objects.create_user("staff", password="pw", is_staff=True)
        self.regular = User.objects.create_user("regular", password="pw")

    # Posts points as JSON the same way the page script does
    def post_points(self, points):
        return self.client.post(
            self.url, json.dumps({"points": points}), content_type="application/json"
        )

    def test_anonymous_and_regular_users_are_redirected(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.regular)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_staff_sees_the_tool(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertContains(response, 'id="scan-map"')
        self.assertContains(response, self.hmap.image.url)

    def test_staff_can_save_points(self):
        self.client.force_login(self.staff)
        points = [
            {"x": x, "y": y, "lat": lat, "lng": lng}
            for x, y in [(10, 20), (400, 50), (60, 700)]
            for lat, lng in [_true_latlng(x, y)]
        ]
        response = self.post_points(points)

        self.assertEqual(response.status_code, 200)
        self.assertIn("topleft", response.json()["corners"])
        self.hmap.refresh_from_db()
        self.assertTrue(self.hmap.is_georeferenced)
        self.assertEqual(self.hmap.control_points.count(), 3)

    def test_bad_points_are_rejected_and_old_points_kept(self):
        ControlPoint.objects.create(map=self.hmap, x=1, y=1, lat=38.4, lng=-78.8)
        self.client.force_login(self.staff)

        # Points in a straight line can't be fitted
        line = [{"x": i, "y": i, "lat": 38.4 + i, "lng": -78.8} for i in (0, 10, 20)]
        self.assertEqual(self.post_points(line).status_code, 400)
        # A latitude of 200 is impossible
        bad = [{"x": 1, "y": 1, "lat": 200, "lng": -78.8}] * 3
        self.assertEqual(self.post_points(bad).status_code, 400)

        # The original point survived both failed saves
        self.assertEqual(self.hmap.control_points.count(), 1)


# Checks the public map viewer (the main page), its nav link, and the homepage "View on map" links
class MapViewerTests(TestCase):
    # Swap the already-aligned seeded Harrisonburg map for a blank one; the
    # unaligned 1892 quad stays, so tests can check it is left out
    def setUp(self):
        HistoricalMap.objects.filter(title="Harrisonburg Map").delete()
        self.hmap = _blank_map()

    # Aligns the test map with perfect synthetic points
    def align_harrisonburg(self):
        for x, y in [(10, 20), (400, 50), (60, 700), (300, 500)]:
            lat, lng = _true_latlng(x, y)
            ControlPoint.objects.create(map=self.hmap, x=x, y=y, lat=lat, lng=lng)
        apply_georeference(self.hmap)

    # The main page still shows today's map when no historical map is aligned
    def test_empty_state_when_nothing_is_aligned(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No maps are aligned yet")
        self.assertContains(response, 'id="viewer-map"')

    # Maps are picked with buttons (built by map.js), not the old dropdown
    def test_map_buttons_replace_dropdown(self):
        self.align_harrisonburg()
        response = self.client.get("/")
        self.assertContains(response, 'id="map-buttons"')
        self.assertNotContains(response, 'id="map-select"')
        self.assertNotContains(response, "No maps are aligned yet")

    def test_aligned_map_is_offered_and_preselected(self):
        self.align_harrisonburg()
        response = self.client.get(f"/?map={self.hmap.pk}")
        self.assertContains(response, 'id="viewer-map"')
        self.assertContains(response, self.hmap.image.url)
        self.assertEqual(response.context["selected"], self.hmap.pk)
        # The unaligned 1892 quad is not offered
        self.assertNotContains(response, "Quadrangle for Harrisonburg")

    # No (or a bad) ?map= means nothing is preselected; the page shows all maps' buttons
    def test_bad_map_parameter_selects_nothing(self):
        self.align_harrisonburg()
        for bad in ["", "999", "abc", "\u00b2"]:
            response = self.client.get("/", {"map": bad})
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(response.context["selected"])

    def test_nav_and_view_on_map_links(self):
        # "View on map" only appears once a map is aligned
        self.assertNotContains(self.client.get("/about/"), "View on map")
        self.align_harrisonburg()
        response = self.client.get("/about/")
        self.assertContains(response, 'href="/"')
        self.assertContains(response, f'href="/?map={self.hmap.pk}"')
