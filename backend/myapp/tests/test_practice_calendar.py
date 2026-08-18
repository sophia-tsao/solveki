"""Tests for the practice-calendar dashboard endpoint."""
import datetime

from django.test import TestCase, Client

from myapp.models import DailyPractice, Settings
from .factories import make_user, make_course, make_topic, select


class PracticeCalendarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def _record(self, date, answered, total):
        return DailyPractice.objects.create(
            user=self.user, date=date, answered=answered, total=total
        )

    def test_requires_auth(self):
        anon = Client()
        self.assertEqual(anon.get("/practice-calendar/").status_code, 401)

    def test_classifies_completed_and_partial(self):
        self._record(datetime.date(2026, 8, 3), answered=10, total=10)
        self._record(datetime.date(2026, 8, 5), answered=4, total=10)
        data = self.client.get("/practice-calendar/?month=2026-08").json()
        self.assertEqual(data["year"], 2026)
        self.assertEqual(data["month"], 8)
        self.assertEqual(
            data["days"],
            {"2026-08-03": "completed", "2026-08-05": "partial"},
        )

    def test_only_returns_requested_month(self):
        self._record(datetime.date(2026, 8, 31), answered=10, total=10)
        self._record(datetime.date(2026, 9, 1), answered=10, total=10)
        data = self.client.get("/practice-calendar/?month=2026-08").json()
        self.assertEqual(list(data["days"]), ["2026-08-31"])

    def test_only_returns_current_users_days(self):
        other = make_user()
        DailyPractice.objects.create(
            user=other, date=datetime.date(2026, 8, 4), answered=10, total=10
        )
        data = self.client.get("/practice-calendar/?month=2026-08").json()
        self.assertEqual(data["days"], {})

    def test_defaults_to_month_of_today(self):
        self._record(datetime.date(2026, 8, 10), answered=2, total=10)
        data = self.client.get("/practice-calendar/?today=2026-08-16").json()
        self.assertEqual(data["month"], 8)
        self.assertEqual(data["days"], {"2026-08-10": "partial"})

    def test_malformed_month_falls_back_to_today(self):
        data = self.client.get("/practice-calendar/?today=2026-08-16&month=bogus").json()
        self.assertEqual((data["year"], data["month"]), (2026, 8))

    def _set_questions_per_day(self, n):
        s = Settings.load(self.user)
        s.questions_per_day = n
        s.save()

    def test_advancing_deck_records_practice(self):
        """An advance writes a DailyPractice row the calendar can read."""
        topic = make_topic(make_course(), topic_name="Linear")
        select(self.user, topic)
        # Build today's deck, then answer the first card.
        self.client.get("/deck/?today=2026-08-16")
        self.client.post(
            "/deck/advance/?today=2026-08-16",
            data={"from_number": 1, "outcome": "correct_first"},
            content_type="application/json",
        )
        rec = DailyPractice.objects.get(user=self.user, date=datetime.date(2026, 8, 16))
        self.assertEqual(rec.answered, 1)
        self.assertGreater(rec.total, 0)
        # One of several cards answered -> the day reads as partial.
        data = self.client.get("/practice-calendar/?today=2026-08-16").json()
        self.assertEqual(data["days"]["2026-08-16"], "partial")

    def test_completing_deck_marks_day_completed(self):
        """Answering every card records answered == total and reads completed."""
        topic = make_topic(make_course(), topic_name="Linear")
        select(self.user, topic)
        self._set_questions_per_day(2)  # small deck so we can finish it
        self.client.get("/deck/?today=2026-08-16")
        for n in (1, 2):
            self.client.post(
                "/deck/advance/?today=2026-08-16",
                data={"from_number": n, "outcome": "correct_first"},
                content_type="application/json",
            )
        rec = DailyPractice.objects.get(user=self.user, date=datetime.date(2026, 8, 16))
        self.assertEqual((rec.answered, rec.total), (2, 2))
        data = self.client.get("/practice-calendar/?today=2026-08-16").json()
        self.assertEqual(data["days"]["2026-08-16"], "completed")
