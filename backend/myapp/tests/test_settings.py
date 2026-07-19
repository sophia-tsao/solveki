"""Tests for the per-user settings endpoint."""
import json

from django.test import TestCase, Client

from myapp.models import Settings
from .factories import make_user


class SettingsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def _patch(self, body):
        return self.client.patch(
            "/settings/", data=json.dumps(body), content_type="application/json"
        )

    def test_get_creates_defaults(self):
        response = self.client.get("/settings/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["language"], "en")
        self.assertEqual(data["questions_per_day"], 10)

    def test_update_language_and_count(self):
        response = self._patch({"language": "es", "questions_per_day": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["language"], "es")
        self.assertEqual(data["questions_per_day"], 5)
        settings = Settings.load(self.user)
        self.assertEqual(settings.questions_per_day, 5)

    def test_questions_per_day_must_be_integer(self):
        response = self._patch({"questions_per_day": "lots"})
        self.assertEqual(response.status_code, 400)

    def test_questions_per_day_must_be_positive(self):
        response = self._patch({"questions_per_day": 0})
        self.assertEqual(response.status_code, 400)

    def test_partial_update_leaves_other_fields(self):
        self._patch({"language": "fr", "questions_per_day": 7})
        self._patch({"language": "de"})
        settings = Settings.load(self.user)
        self.assertEqual(settings.language, "de")
        self.assertEqual(settings.questions_per_day, 7)
