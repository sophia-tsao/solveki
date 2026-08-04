"""Tests for the spaced-repetition dashboard endpoint."""
import datetime

from django.test import TestCase, Client

from myapp.models import TopicReview, Settings
from .factories import make_user, make_course, make_topic, select


class DashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.course = make_course(course_name="Algebra")
        self.t1 = make_topic(self.course, topic_name="Linear")
        self.t2 = make_topic(self.course, topic_name="Quadratic")

    def test_requires_auth(self):
        anon = Client()
        self.assertEqual(anon.get("/dashboard/").status_code, 401)

    def test_lists_only_selected_topics(self):
        select(self.user, self.t1)
        data = self.client.get("/dashboard/").json()
        names = [t["topic_name"] for t in data["selected"]]
        self.assertEqual(names, ["Linear"])

    def test_never_reviewed_topic_uses_srs_defaults(self):
        select(self.user, self.t1)
        stats = self.client.get("/dashboard/").json()["selected"][0]
        self.assertEqual(stats["repetitions"], 0)
        self.assertEqual(stats["interval"], 0)
        self.assertEqual(stats["ease"], 2.5)

    def test_includes_review_state_and_course(self):
        select(self.user, self.t1)
        TopicReview.objects.create(
            user=self.user, topic=self.t1, ease=2.36, interval=6, repetitions=2,
            due_date=datetime.date(2026, 8, 10),
        )
        stats = self.client.get("/dashboard/").json()["selected"][0]
        self.assertEqual(stats["repetitions"], 2)
        self.assertEqual(stats["interval"], 6)
        self.assertEqual(stats["ease"], 2.36)
        self.assertEqual(stats["course_name"], "Algebra")

    def test_selected_ordered_by_due_date_most_due_first(self):
        select(self.user, self.t1)
        select(self.user, self.t2)
        # t1 due later than t2, so t2 should come first.
        TopicReview.objects.create(
            user=self.user, topic=self.t1, due_date=datetime.date(2026, 9, 1)
        )
        TopicReview.objects.create(
            user=self.user, topic=self.t2, due_date=datetime.date(2026, 8, 5)
        )
        names = [t["topic_name"] for t in self.client.get("/dashboard/").json()["selected"]]
        self.assertEqual(names, ["Quadratic", "Linear"])

    def test_upcoming_limited_to_questions_per_day(self):
        select(self.user, self.t1)
        select(self.user, self.t2)
        settings = Settings.load(self.user)
        settings.questions_per_day = 1
        settings.save()
        data = self.client.get("/dashboard/").json()
        self.assertEqual(len(data["selected"]), 2)
        self.assertEqual(len(data["upcoming"]), 1)

    def test_upcoming_excludes_topics_without_generator(self):
        select(self.user, self.t1)
        broken = make_topic(self.course, topic_name="Broken", generator_name=None)
        select(self.user, broken)
        data = self.client.get("/dashboard/").json()
        # Selected shows both; upcoming (deck draw) skips the unusable one.
        self.assertEqual(len(data["selected"]), 2)
        upcoming_names = [t["topic_name"] for t in data["upcoming"]]
        self.assertNotIn("Broken", upcoming_names)
