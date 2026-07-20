"""Tests for authentication endpoints and the shared auth guard.

The Google login flow is exercised with `verify_oauth2_token` mocked, so no
network call or real Google token is needed.
"""
import json
from unittest import mock

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model

from .factories import make_user

User = get_user_model()


class MeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_me_anonymous(self):
        response = self.client.get("/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"authenticated": False})

    def test_me_authenticated(self):
        user = make_user(first_name="Ada", last_name="Lovelace")
        self.client.force_login(user)
        response = self.client.get("/auth/me/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user"]["email"], user.email)
        self.assertEqual(data["user"]["name"], "Ada Lovelace")


@override_settings(GOOGLE_OAUTH_CLIENT_ID="test-client-id")
class GoogleLoginTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _post(self, body):
        return self.client.post(
            "/auth/google/",
            data=json.dumps(body),
            content_type="application/json",
        )

    def test_missing_credential(self):
        response = self._post({})
        self.assertEqual(response.status_code, 400)

    def test_invalid_json(self):
        response = self.client.post(
            "/auth/google/", data="not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="")
    def test_not_configured(self):
        response = self._post({"credential": "abc"})
        self.assertEqual(response.status_code, 500)

    @mock.patch("myapp.views.google_id_token.verify_oauth2_token")
    def test_invalid_token(self, mock_verify):
        mock_verify.side_effect = ValueError("bad token")
        response = self._post({"credential": "abc"})
        self.assertEqual(response.status_code, 401)

    @mock.patch("myapp.views.google_id_token.verify_oauth2_token")
    def test_unverified_email(self, mock_verify):
        mock_verify.return_value = {
            "email": "user@example.com",
            "email_verified": False,
            "sub": "google-sub-1",
        }
        response = self._post({"credential": "abc"})
        self.assertEqual(response.status_code, 401)

    @mock.patch("myapp.views.google_id_token.verify_oauth2_token")
    def test_creates_user_on_first_login(self, mock_verify):
        mock_verify.return_value = {
            "email": "new@example.com",
            "email_verified": True,
            "sub": "google-sub-42",
            "given_name": "New",
            "family_name": "User",
        }
        response = self._post({"credential": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        user = User.objects.get(username="google-sub-42")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.first_name, "New")

    @mock.patch("myapp.views.google_id_token.verify_oauth2_token")
    def test_returning_user_email_refreshed(self, mock_verify):
        User.objects.create_user(username="google-sub-42", email="old@example.com")
        mock_verify.return_value = {
            "email": "fresh@example.com",
            "email_verified": True,
            "sub": "google-sub-42",
        }
        response = self._post({"credential": "abc"})
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="google-sub-42")
        self.assertEqual(user.email, "fresh@example.com")
        # No duplicate account created.
        self.assertEqual(User.objects.filter(username="google-sub-42").count(), 1)


class TestLoginTests(TestCase):
    """The E2E test-login endpoint is invisible unless explicitly enabled."""

    def setUp(self):
        self.client = Client()

    def test_disabled_by_default(self):
        # ENABLE_TEST_LOGIN is off by default, so the route 404s.
        response = self.client.post("/auth/test-login/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.client.get("/auth/me/").json()["authenticated"])

    @override_settings(ENABLE_TEST_LOGIN=True)
    def test_logs_in_when_enabled(self):
        response = self.client.post("/auth/test-login/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user"]["email"], "e2e@example.com")
        # A real session is established: the follow-up request is authenticated.
        self.assertTrue(self.client.get("/auth/me/").json()["authenticated"])

    @override_settings(ENABLE_TEST_LOGIN=True)
    def test_reuses_same_user(self):
        self.client.post("/auth/test-login/")
        self.client.post("/auth/test-login/")
        self.assertEqual(User.objects.filter(username="e2e-user").count(), 1)

    @override_settings(ENABLE_TEST_LOGIN=True)
    def test_resets_state_on_login(self):
        from myapp.models import Course, Topic, UserTopicSelection, Settings, DailyDeck
        from django.utils import timezone

        # First login creates the user; seed some state onto it.
        self.client.post("/auth/test-login/")
        user = User.objects.get(username="e2e-user")
        course = Course.objects.create(course_name="C", grade_level=1)
        topic = Topic.objects.create(topic_name="T", course=course, generator_name="addition")
        UserTopicSelection.objects.create(user=user, topic=topic)
        Settings.objects.update_or_create(user=user, defaults={"questions_per_day": 3})
        DailyDeck.objects.create(user=user, date=timezone.localdate(), problems=[], current_index=0)

        # A fresh login wipes selections, decks, and settings.
        self.client.post("/auth/test-login/")
        self.assertFalse(UserTopicSelection.objects.filter(user=user).exists())
        self.assertFalse(DailyDeck.objects.filter(user=user).exists())
        self.assertFalse(Settings.objects.filter(user=user).exists())


class LogoutAndDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_logout(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.post("/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        # Subsequent request is anonymous.
        self.assertFalse(self.client.get("/auth/me/").json()["authenticated"])

    def test_delete_account_requires_auth(self):
        response = self.client.delete("/auth/delete/")
        self.assertEqual(response.status_code, 401)

    def test_delete_account(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.delete("/auth/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=user.id).exists())


class AuthGuardTests(TestCase):
    """Every protected endpoint must 401 for anonymous callers."""

    def setUp(self):
        self.client = Client()

    def test_protected_endpoints_reject_anonymous(self):
        cases = [
            ("get", "/problem/"),
            ("get", "/deck/"),
            ("post", "/deck/advance/"),
            ("get", "/settings/"),
            ("get", "/courses/"),
            ("get", "/courses/1/topics"),
        ]
        for method, url in cases:
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 401)
