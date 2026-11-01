"""Tests for OriginCheckMiddleware (CSRF guard for the csrf_exempt API)."""
import json

from django.test import TestCase, Client

from myapp.models import Settings
from .factories import make_user


class OriginCheckTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def _patch(self, **headers):
        return self.client.patch(
            "/settings/",
            data=json.dumps({"questions_per_day": 7}),
            content_type="application/json",
            headers=headers,
        )

    def test_untrusted_origin_is_blocked(self):
        response = self._patch(Origin="https://evil.example")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Settings.load(self.user).questions_per_day, 10)

    def test_null_origin_is_blocked(self):
        self.assertEqual(self._patch(Origin="null").status_code, 403)

    def test_allowed_frontend_origin_passes(self):
        # http://localhost:5173 is the default CORS_ALLOWED_ORIGINS entry.
        response = self._patch(Origin="http://localhost:5173")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Settings.load(self.user).questions_per_day, 7)

    def test_same_origin_passes(self):
        # The test client's host is "testserver" over http.
        self.assertEqual(self._patch(Origin="http://testserver").status_code, 200)

    def test_no_origin_passes(self):
        # Non-browser clients (curl, Bruno) send no Origin and carry no victim cookies.
        self.assertEqual(self._patch().status_code, 200)

    def test_safe_methods_ignore_origin(self):
        response = self.client.get("/settings/", headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 200)
