"""Tests for "Finish it now": doing the rest of an assignment ahead of its due date.

An assignment due in several days spreads its cards over them. Once the student
finishes today's share, the finished deck reports the cards still left
(`cards_left`), and `POST /deck/finish-now/` moves them all into today's deck.

The `gcd` generator the test topic uses is mocked so deck generation is
deterministic, mirroring test_classes_assignments.py.
"""
import json
from unittest import mock

from django.test import TestCase, Client
from django.utils import timezone

from myapp.models import DailyDeck, Settings, StudentAssignment
from .factories import make_user, make_course, make_topic
from .test_classes_assignments import make_teacher


@mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "4"))
class FinishNowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        topic = make_topic(make_course(), topic_name="Picked", generator_name="gcd")
        # Keep pool practice out of the way: the deck is just the assignment's share.
        settings = Settings.load(self.student)
        settings.questions_per_day = 4
        settings.save(update_fields=["questions_per_day"])
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        self.assignment = self.client.post(
            "/assignments/",
            data=json.dumps({"title": "HW", "deck_size": 12, "topics": [{"topic_id": topic.id}]}),
            content_type="application/json",
        ).json()
        self.cls = cls
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )

    def _assign(self, days_until_due):
        """Assign to the class, due at the end of the day `days_until_due` from today."""
        due = timezone.localtime().replace(hour=23, minute=59, second=0, microsecond=0)
        due += timezone.timedelta(days=days_until_due)
        self.client.force_login(self.teacher)
        self.client.post(
            f"/assignments/{self.assignment['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": self.cls["id"], "due_at": due.isoformat()}]}),
            content_type="application/json",
        )
        self.client.force_login(self.student)

    def _url(self, path):
        return f"{path}?assignment={self.assignment['id']}"

    def _deck(self):
        return self.client.get(self._url("/deck/")).json()

    def _answer_all(self):
        """Answer every card left in the deck correctly; returns the last payload."""
        data = self._deck()
        while not data.get("completed"):
            data = self.client.post(
                self._url("/deck/advance/"), data=json.dumps({"outcome": "correct_first"}),
                content_type="application/json",
            ).json()
        return data

    def _finish_now(self):
        return self.client.post(self._url("/deck/finish-now/"))

    def _row(self):
        return StudentAssignment.objects.get(assignment_id=self.assignment["id"], student=self.student)

    def test_finished_share_offers_the_rest(self, _gen):
        # 12 cards over 3 days: 4 today, 8 left.
        self._assign(days_until_due=2)
        self.assertEqual(self._deck()["total"], 4)
        data = self._answer_all()
        self.assertEqual(data["cards_left"], 8)
        self.assertEqual(data["assignment"]["id"], self.assignment["id"])

    def test_finish_now_adds_the_rest_to_today(self, _gen):
        self._assign(days_until_due=2)
        self._answer_all()
        res = self._finish_now()
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["current_number"], 5)
        self.assertEqual(data["total"], 12)
        self.assertEqual(self._row().finish_on, timezone.localdate())
        done = self._answer_all()
        self.assertNotIn("cards_left", done)
        self.assertEqual(self._row().status, StudentAssignment.COMPLETED)

    def test_finish_now_survives_a_deck_rebuild(self, _gen):
        # A topic change later in the day rebuilds the unanswered tail; the
        # rest of the assignment must still be scheduled for today.
        self._assign(days_until_due=2)
        self._answer_all()
        self._finish_now()
        DailyDeck.objects.filter(user=self.student).update(needs_regen=True)
        self.assertEqual(self._deck()["total"], 12)

    def test_last_day_offers_nothing(self, _gen):
        # Due today: today's deck already holds everything left.
        self._assign(days_until_due=0)
        data = self._answer_all()
        self.assertTrue(data["completed"])
        self.assertNotIn("cards_left", data)

    def test_needs_an_open_assignment(self, _gen):
        # With none open, the default deck has no assignment to finish.
        self.assertEqual(self.client.post("/deck/finish-now/").status_code, 400)
        self._assign(days_until_due=2)
        # Nor does a completed one.
        row = self._row()
        row.status = StudentAssignment.COMPLETED
        row.save(update_fields=["status"])
        self.assertEqual(self._finish_now().status_code, 400)
