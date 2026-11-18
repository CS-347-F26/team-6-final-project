from django.test import SimpleTestCase, TestCase

from .georef import apply_georeference, fit_affine
from .models import ControlPoint, HistoricalMap


# A known rotated + scaled transform (pixel -> lat, lng) used to fake control points
def _true_latlng(x, y):
    return (38.46 + 2e-6 * x - 1.1e-5 * y, -78.88 + 1.3e-5 * x + 3e-6 * y)


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
    def test_stores_corners_bounds_and_error(self):
        # Reuses the real Harrisonburg scan (452 x 768 pixels) from media/
        hmap = HistoricalMap.objects.create(
            title="Test map",
            year=1878,
            image="historical_maps/HarrisonburgMap.jpg",
            north=0,
            south=0,
            east=0,
            west=0,
        )
        for x, y in [(10, 20), (400, 50), (60, 700)]:
            lat, lng = _true_latlng(x, y)
            ControlPoint.objects.create(map=hmap, x=x, y=y, lat=lat, lng=lng)

        apply_georeference(hmap)
        hmap.refresh_from_db()

        self.assertTrue(hmap.is_georeferenced)
        for got, want in zip(hmap.corners["topleft"], _true_latlng(0, 0)):
            self.assertAlmostEqual(got, want, places=9)
        # Bounding box covers the rotated image; error is ~0 for perfect points
        self.assertGreater(hmap.north, hmap.south)
        self.assertGreater(hmap.east, hmap.west)
        self.assertLess(hmap.rms_error, 0.01)


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
        response = self.client.get("/")

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
        response = self.client.post(
            "/i18n/setlang/",
            {"language": "es", "next": "/settings/"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Idioma")
        self.assertContains(response, "Guardar idioma")
        self.assertContains(response, "Más preferencias próximamente")
        homepage = self.client.get("/")
        self.assertEqual(homepage.status_code, 200)
        self.assertContains(homepage, "Historia, justo donde estás.")
        self.assertContains(homepage, "Estamos agregando mapas")

    def test_homepage_shows_empty_state_without_maps(self):
        response = self.client.get("/")

        self.assertContains(response, "Maps are being added")

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

        response = self.client.get("/")

        self.assertContains(response, "Downtown Harrisonburg")
        self.assertContains(response, "1885")


# Checks migration 0004 corrected the seeded maps (the test DB runs every migration)
class SeedMapTests(TestCase):
    def test_seed_maps_are_corrected(self):
        harrisonburg = HistoricalMap.objects.get(title="Harrisonburg Map")
        self.assertEqual(harrisonburg.year, 1877)
        self.assertFalse(harrisonburg.is_georeferenced)
        quad = HistoricalMap.objects.get(title="Quadrangle for Harrisonburg, VA")
        self.assertFalse(quad.is_georeferenced)
