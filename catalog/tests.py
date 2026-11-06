from django.test import TestCase

from .models import HistoricalMap


# Checks the custom middleware logs each request with method, path, and status
class RequestLoggingMiddlewareTests(TestCase):
    def test_request_is_logged(self):
        with self.assertLogs("catalog", level="INFO") as logs:
            self.client.get("/")
        self.assertIn("GET / -> 200", logs.output[0])


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
