"""Tests for problem generation and the daily deck lifecycle.

The `gcd` generator (which the test topics use) is mocked so problem
text/solutions are deterministic and the rounding logic can be asserted
precisely.
"""
import datetime
import json
from collections import Counter
from fractions import Fraction
from unittest import mock

from django.test import TestCase, Client

from myapp.models import (
    DailyDeck, Settings, Topic, TopicReview, DailyTopicGrade, UserTopicSelection,
    AnswerRecord, ProblemReport,
)
from myapp import views
from myapp.generators._format import num
from myapp.views.deck import _select_deck_topics, _generate_problems, _grade_topic
from myapp.views.problems import _make_problem_for_topic
from .factories import make_user, make_course, make_topic, select


class MakeProblemForTopicTests(TestCase):
    def setUp(self):
        self.topic = make_topic(make_course(), generator_name="gcd")

    def test_topic_without_generator_returns_none(self):
        topic = make_topic(make_course(), generator_name=None)
        self.assertIsNone(_make_problem_for_topic(topic))

    @mock.patch("myapp.views.mathgenerator.gcd")
    def test_integer_solution_not_rounded(self, mock_gen):
        # An integer solution is stripped of its '$' delimiters but not rounded.
        mock_gen.return_value = ("$2+2=$", "$4$")
        result = _make_problem_for_topic(self.topic)
        self.assertEqual(result["solution"], "4")
        self.assertNotIn("Round", result["problem"])

    @mock.patch("myapp.views.mathgenerator.gcd")
    def test_long_decimal_is_rounded_and_annotated(self, mock_gen):
        mock_gen.return_value = ("What is 1/3?", "0.3333333")
        result = _make_problem_for_topic(self.topic)
        self.assertEqual(result["solution"], "0.333")
        self.assertIn("Round to the nearest thousandth", result["problem"])

    @mock.patch("myapp.views.mathgenerator.gcd")
    def test_short_decimal_not_annotated(self, mock_gen):
        mock_gen.return_value = ("Q", "0.5")
        result = _make_problem_for_topic(self.topic)
        self.assertEqual(result["solution"], "0.5")
        self.assertNotIn("Round", result["problem"])

    @mock.patch("myapp.views.mathgenerator.gcd")
    def test_nonnumeric_solution_passes_through(self, mock_gen):
        mock_gen.return_value = ("Simplify", "$x + 1$")
        result = _make_problem_for_topic(self.topic)
        self.assertEqual(result["solution"], "x + 1")

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_problem_carries_source_topic_id(self, mock_gen):
        # Each generated problem records which topic it came from, so an answer
        # can later be attributed to that topic for spaced-repetition scheduling.
        result = _make_problem_for_topic(self.topic)
        self.assertEqual(result["topic_id"], self.topic.id)


class DeckTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.course = make_course()
        self.topic = make_topic(self.course, generator_name="gcd")

    def test_deck_empty_when_no_topics(self):
        response = self.client.get("/deck/")
        self.assertTrue(response.json()["no_topics"])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_deck_built_and_paged(self, mock_gen):
        select(self.user, self.topic)
        Settings.load(self.user)  # default questions_per_day = 10
        Settings.objects.filter(user=self.user).update(questions_per_day=3)

        data = self.client.get("/deck/").json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["current_number"], 1)

        # Advance through the deck.
        data = self.client.post("/deck/advance/").json()
        self.assertEqual(data["current_number"], 2)
        self.client.post("/deck/advance/")
        data = self.client.post("/deck/advance/").json()
        self.assertTrue(data.get("completed"))
        self.assertEqual(data["total"], 3)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_stored_deck_entries_carry_topic_id(self, mock_gen):
        # Stored problems remember their source topic so answers can be graded
        # against it; the client-facing payload still omits it (see _deck_payload).
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 2}
        )
        self.client.get("/deck/")
        deck = DailyDeck.objects.get(user=self.user)
        self.assertTrue(all(p["topic_id"] == self.topic.id for p in deck.problems))

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_card_carries_its_topics_learn_more_url(self, mock_gen):
        # The card shows whatever link is stored on the topic (admin-editable),
        # not a value computed from the generator.
        self.topic.learn_more_url = "https://www.khanacademy.org/math/some-lesson"
        self.topic.save()
        select(self.user, self.topic)
        data = self.client.get("/deck/").json()
        self.assertEqual(data["topic_name"], self.topic.topic_name)
        self.assertEqual(data["learn_more_url"], "https://www.khanacademy.org/math/some-lesson")

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_admin_link_change_shows_on_the_existing_deck(self, mock_gen):
        # The link is looked up at display time, so editing it in the admin
        # updates a deck that was already built today.
        select(self.user, self.topic)
        self.client.get("/deck/")
        self.topic.learn_more_url = "https://www.youtube.com/watch?v=_LDR1_Prveo"
        self.topic.save()
        data = self.client.get("/deck/").json()
        self.assertEqual(data["learn_more_url"], "https://www.youtube.com/watch?v=_LDR1_Prveo")

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_card_for_topic_with_blank_link_has_no_learn_more_url(self, mock_gen):
        # No search fallback: a topic whose link is blank sends no link.
        select(self.user, self.topic)
        data = self.client.get("/deck/").json()
        self.assertIsNone(data["learn_more_url"])

    def test_legacy_card_without_topic_id_has_no_learn_more_url(self):
        # A deck entry stored before topic attribution has no topic to look up.
        # A one-card deck at questions_per_day=1 isn't topped up, so the legacy
        # entry is the card shown.
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 1}
        )
        DailyDeck.objects.create(
            user=self.user,
            date=datetime.date(2026, 7, 21),
            problems=[{"problem": "old", "solution": "1"}],  # no topic_id
            current_index=0,
        )
        data = self.client.get("/deck/?today=2026-07-21").json()
        self.assertIsNone(data["topic_name"])
        self.assertIsNone(data["learn_more_url"])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_legacy_deck_without_topic_id_tops_up_without_error(self, mock_gen):
        # A deck persisted before topic attribution existed has entries with no
        # topic_id. Topping it up must not crash reading the in-deck topic ids.
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 3}
        )
        DailyDeck.objects.create(
            user=self.user,
            date=datetime.date(2026, 7, 21),
            problems=[{"problem": "old", "solution": "1"}],  # no topic_id
            current_index=0,
        )
        data = self.client.get("/deck/?today=2026-07-21").json()
        self.assertEqual(data["total"], 3)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_new_day_rebuilds_deck(self, mock_gen):
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 2}
        )
        # Simulate a stale deck from yesterday.
        yesterday = datetime.date(2020, 1, 1)
        DailyDeck.objects.create(
            user=self.user, date=yesterday, problems=[{"problem": "old", "solution": "1"}]
        )
        self.client.get("/deck/")
        self.assertFalse(DailyDeck.objects.filter(user=self.user, date=yesterday).exists())
        deck = DailyDeck.objects.get(user=self.user)
        self.assertEqual(len(deck.problems), 2)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_advance_on_new_day_does_not_skip_past_card_one(self, mock_gen):
        # Regression: advancing must never *build* a deck. The "correct answer"
        # handler advances on a timer, so finishing a problem just before
        # midnight can make the day's first backend call an advance. If advance
        # created-then-stepped the new day's deck, the student would land on
        # "2 of N" having answered nothing today. It must leave them on card 1.
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 3}
        )
        # Finish yesterday's deck.
        self.client.get("/deck/?today=2026-07-19")
        for _ in range(3):
            self.client.post("/deck/advance/?today=2026-07-19")
        # New day, first call is an advance (no deck exists yet for today).
        data = self.client.post("/deck/advance/?today=2026-07-20").json()
        self.assertFalse(data.get("completed"))
        self.assertEqual(data["current_number"], 1)
        self.assertEqual(data["total"], 3)
        deck = DailyDeck.objects.get(user=self.user, date=datetime.date(2026, 7, 20))
        self.assertEqual(deck.current_index, 0)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_new_day_get_then_stray_advance_stays_on_card_one(self, mock_gen):
        # The real new-day sequence: the SPA mounts and GETs the deck (building
        # a fresh one at index 0), and *then* a leftover advance timer from
        # finishing yesterday's last card fires. That stray advance must not
        # step the fresh deck to card 2 — the student answered nothing today.
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 3}
        )
        # Finish yesterday's deck.
        self.client.get("/deck/?today=2026-07-19")
        for _ in range(3):
            self.client.post("/deck/advance/?today=2026-07-19")

        # New day: GET builds the fresh deck at card 1...
        got = self.client.get("/deck/?today=2026-07-20").json()
        self.assertEqual(got["current_number"], 1)
        # ...then the stray advance timer fires. It was scheduled while the
        # student was finishing yesterday's last card (card 3), so it carries
        # from_number=3, which no longer matches the fresh deck on card 1. The
        # backend must ignore it and leave the student on card 1.
        advanced = self.client.post(
            "/deck/advance/?today=2026-07-20",
            data=json.dumps({"outcome": "correct_first", "from_number": 3}),
            content_type="application/json",
        ).json()
        self.assertEqual(advanced["current_number"], 1)
        deck = DailyDeck.objects.get(user=self.user, date=datetime.date(2026, 7, 20))
        self.assertEqual(deck.current_index, 0)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_deck_resets_on_client_local_day_not_server_utc_day(self, mock_gen):
        # The server clock is UTC, but the deck must reset at the *user's* local
        # midnight. A user ahead of UTC can be a calendar day ahead of the
        # server; the client sends that day as ?today=. Yesterday's finished
        # deck must not be what they see on their new morning.
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 2}
        )
        # A completed deck dated to the server's current day.
        from django.utils import timezone
        server_today = timezone.localdate()
        DailyDeck.objects.create(
            user=self.user,
            date=server_today,
            problems=[{"problem": "old", "solution": "1"}],
            current_index=1,  # finished
        )
        # The client is already on the next calendar day.
        client_tomorrow = server_today + datetime.timedelta(days=1)
        data = self.client.get(f"/deck/?today={client_tomorrow.isoformat()}").json()

        # A fresh deck for the client's day — on card 1, not the finished deck.
        self.assertFalse(data.get("completed"))
        self.assertEqual(data["current_number"], 1)
        self.assertEqual(data["total"], 2)
        # The stale server-day deck is discarded.
        self.assertFalse(
            DailyDeck.objects.filter(user=self.user, date=server_today).exists()
        )

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_malformed_today_param_falls_back_to_server_date(self, mock_gen):
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 2}
        )
        # A garbage ?today= must not 500; it falls back to the server date.
        data = self.client.get("/deck/?today=not-a-date").json()
        self.assertEqual(data["current_number"], 1)
        self.assertEqual(data["total"], 2)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_empty_deck_rebuilt_once_topics_selected(self, mock_gen):
        # First visit with no topics yields an empty deck for today.
        self.client.get("/deck/")
        deck = DailyDeck.objects.get(user=self.user)
        self.assertEqual(deck.problems, [])

        # After selecting a topic, revisiting fills today's existing deck.
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 2}
        )
        data = self.client.get("/deck/").json()
        self.assertEqual(data["total"], 2)


class SelectDeckTopicsTests(TestCase):
    """The spaced-repetition topic selector (Option A due order + Option 2 fill)."""

    def setUp(self):
        self.user = make_user()
        self.course = make_course()
        self.today = datetime.date(2026, 7, 21)

    def _topic(self, name, generator_name="gcd", selected=True):
        topic = make_topic(self.course, topic_name=name, generator_name=generator_name)
        if selected:
            select(self.user, topic)
        return topic

    def _review(self, topic, due_date, **kwargs):
        return TopicReview.objects.create(
            user=self.user, topic=topic, due_date=due_date, **kwargs
        )

    def test_empty_when_no_topics_selected(self):
        # A topic exists but isn't selected -> nothing to review.
        self._topic("Unselected", selected=False)
        self.assertEqual(_select_deck_topics(self.user, self.today, 5), [])

    def test_ignores_topics_without_a_generator(self):
        self._topic("No generator", generator_name=None)
        self.assertEqual(_select_deck_topics(self.user, self.today, 5), [])

    def test_never_reviewed_topic_is_due_now(self):
        # No TopicReview row => treated as due today, so it's selected.
        t = self._topic("Fresh")
        self.assertEqual(_select_deck_topics(self.user, self.today, 5), [t])

    def test_orders_most_overdue_first(self):
        recent = self._topic("Recent")
        old = self._topic("Old")
        middle = self._topic("Middle")
        self._review(recent, self.today - datetime.timedelta(days=1))
        self._review(old, self.today - datetime.timedelta(days=10))
        self._review(middle, self.today - datetime.timedelta(days=5))
        result = _select_deck_topics(self.user, self.today, 5)
        self.assertEqual(result, [old, middle, recent])

    def test_tops_up_with_next_soonest_when_few_are_due(self):
        # One overdue, two not-yet-due. count=3 pulls the due one first, then
        # the soonest future topic, then the later one.
        due = self._topic("Due")
        soon = self._topic("Soon")
        later = self._topic("Later")
        self._review(due, self.today - datetime.timedelta(days=2))
        self._review(soon, self.today + datetime.timedelta(days=3))
        self._review(later, self.today + datetime.timedelta(days=30))
        result = _select_deck_topics(self.user, self.today, 3)
        self.assertEqual(result, [due, soon, later])

    def test_full_deck_even_when_nothing_is_due(self):
        # Key invariant: "nothing due" still yields a full deck via top-up, so
        # an empty result means "no topics", never "nothing to review today".
        a = self._topic("A")
        b = self._topic("B")
        self._review(a, self.today + datetime.timedelta(days=5))
        self._review(b, self.today + datetime.timedelta(days=10))
        result = _select_deck_topics(self.user, self.today, 5)
        self.assertEqual(result, [a, b])

    def test_caps_at_count(self):
        for i in range(5):
            self._topic(f"T{i}")
        result = _select_deck_topics(self.user, self.today, 3)
        self.assertEqual(len(result), 3)

    def test_excludes_given_topic_ids(self):
        a = self._topic("A")
        b = self._topic("B")
        result = _select_deck_topics(self.user, self.today, 5, exclude={a.id})
        self.assertEqual(result, [b])

    def test_excluding_all_yields_empty(self):
        a = self._topic("A")
        result = _select_deck_topics(self.user, self.today, 5, exclude={a.id})
        self.assertEqual(result, [])

    def test_zero_count_yields_empty(self):
        self._topic("A")
        self.assertEqual(_select_deck_topics(self.user, self.today, 0), [])

    def test_only_selecting_users_topics(self):
        # Another user's selection must not leak into this user's deck.
        other = make_user()
        mine = self._topic("Mine")
        theirs = make_topic(self.course, topic_name="Theirs", generator_name="gcd")
        select(other, theirs)
        result = _select_deck_topics(self.user, self.today, 5)
        self.assertEqual(result, [mine])


class GenerateProblemsTests(TestCase):
    """Filling a deck to exactly `count`: distinct topics first, then repeats.

    The `gcd` generator echoes its topic id back as the problem text so a
    generated problem can be traced to its source topic without a real generator.
    """

    def setUp(self):
        self.user = make_user()
        self.course = make_course()
        self.today = datetime.date(2026, 7, 21)

    def _topic(self, name, generator_name="gcd"):
        topic = make_topic(self.course, topic_name=name, generator_name=generator_name)
        select(self.user, topic)
        return topic

    def _review(self, topic, due_date):
        return TopicReview.objects.create(user=self.user, topic=topic, due_date=due_date)

    def test_empty_when_no_topics(self):
        self.assertEqual(_generate_problems(self.user, 5, self.today), [])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_distinct_topics_used_before_repeating(self, mock_gen):
        # Three topics, count 3 -> each appears exactly once.
        topics = [self._topic(f"T{i}") for i in range(3)]
        problems = _generate_problems(self.user, 3, self.today)
        self.assertEqual(len(problems), 3)
        self.assertEqual(
            sorted(p["topic_id"] for p in problems),
            sorted(t.id for t in topics),
        )

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_repeats_to_fill_when_fewer_topics_than_count(self, mock_gen):
        # One topic, count 3 -> the deck still reaches 3, repeating that topic.
        topic = self._topic("Only")
        problems = _generate_problems(self.user, 3, self.today)
        self.assertEqual(len(problems), 3)
        self.assertTrue(all(p["topic_id"] == topic.id for p in problems))

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_fills_in_due_order_most_overdue_first(self, mock_gen):
        old = self._topic("Old")
        recent = self._topic("Recent")
        self._review(old, self.today - datetime.timedelta(days=10))
        self._review(recent, self.today - datetime.timedelta(days=1))
        problems = _generate_problems(self.user, 2, self.today)
        self.assertEqual([p["topic_id"] for p in problems], [old.id, recent.id])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_topup_adds_fresh_topic_before_repeating(self, mock_gen):
        # A deck already holding topic A, topped up by 2, with topics A and B
        # selected: B (fresh) comes before A repeats.
        a = self._topic("A")
        b = self._topic("B")
        extra = _generate_problems(self.user, 2, self.today, existing=[a.id])
        self.assertEqual([p["topic_id"] for p in extra], [b.id, a.id])

    def test_broken_generator_does_not_loop_forever(self):
        # An unresolvable generator name yields no problems rather than hanging.
        self._topic("Broken", generator_name="not_a_real_generator")
        self.assertEqual(_generate_problems(self.user, 3, self.today), [])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_overdue_topic_gets_more_slots_than_not_due_one(self, mock_gen):
        # The SM-2 dose signal: with two topics filling a 10-card deck, the
        # topic that's due today should occupy far more of the deck than one
        # whose next review is a week out — not an even 5/5 split.
        due = self._topic("Due")
        scheduled = self._topic("Scheduled")
        self._review(due, self.today)  # due today
        self._review(scheduled, self.today + datetime.timedelta(days=6))
        problems = _generate_problems(self.user, 10, self.today)
        self.assertEqual(len(problems), 10)
        counts = Counter(p["topic_id"] for p in problems)
        # Both still appear (variety floor), but the due topic dominates.
        self.assertGreater(counts[due.id], counts[scheduled.id])
        self.assertGreaterEqual(counts[scheduled.id], 1)
        self.assertEqual(counts[due.id] + counts[scheduled.id], 10)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_more_overdue_topic_outweighs_less_overdue_one(self, mock_gen):
        # Among two overdue topics, the more overdue gets the larger share.
        very = self._topic("VeryOverdue")
        slightly = self._topic("SlightlyOverdue")
        self._review(very, self.today - datetime.timedelta(days=9))
        self._review(slightly, self.today - datetime.timedelta(days=1))
        problems = _generate_problems(self.user, 10, self.today)
        counts = Counter(p["topic_id"] for p in problems)
        self.assertGreater(counts[very.id], counts[slightly.id])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_equally_due_topics_split_evenly(self, mock_gen):
        # Equal priority => equal dose: two topics both due today split a
        # 10-card deck 5/5 (the weighting reduces to the old round-robin).
        a = self._topic("A")
        b = self._topic("B")
        self._review(a, self.today)
        self._review(b, self.today)
        problems = _generate_problems(self.user, 10, self.today)
        counts = Counter(p["topic_id"] for p in problems)
        self.assertEqual(counts[a.id], 5)
        self.assertEqual(counts[b.id], 5)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "1"))
    def test_every_selected_topic_keeps_at_least_one_slot(self, mock_gen):
        # Even a topic scheduled far into the future keeps its variety-floor
        # slot, so a full deck never silently drops a selected topic.
        due = self._topic("Due")
        far = self._topic("Far")
        self._review(due, self.today)
        self._review(far, self.today + datetime.timedelta(days=365))
        problems = _generate_problems(self.user, 10, self.today)
        counts = Counter(p["topic_id"] for p in problems)
        self.assertGreaterEqual(counts[far.id], 1)
        self.assertEqual(sum(counts.values()), 10)


class GradeTopicTests(TestCase):
    """Grading a topic once per day from all of that day's answers on it."""

    def setUp(self):
        self.user = make_user()
        self.course = make_course()
        self.today = datetime.date(2026, 7, 21)
        self.topic = make_topic(self.course, generator_name="gcd")
        select(self.user, self.topic)

    def _review(self, topic=None):
        return TopicReview.objects.get(user=self.user, topic=topic or self.topic)

    def _answer(self, *outcomes, topic=None):
        # The advance endpoint logs the answer, then regrades from today's log.
        topic = topic or self.topic
        for outcome in outcomes:
            AnswerRecord.objects.create(user=self.user, topic=topic, date=self.today, outcome=outcome)
            _grade_topic(self.user, topic.id, self.today)

    def _mature(self, **fields):
        defaults = {"ease": 2.5, "interval": 10, "repetitions": 3, "due_date": self.today}
        TopicReview.objects.update_or_create(
            user=self.user, topic=self.topic, defaults={**defaults, **fields}
        )

    def test_first_correct_answer_creates_review_due_in_the_future(self):
        self._answer("correct_first")
        review = self._review()
        # First success: interval 1 day, so due tomorrow.
        self.assertEqual(review.interval, 1)
        self.assertEqual(review.due_date, self.today + datetime.timedelta(days=1))
        self.assertEqual(review.repetitions, 1)

    def test_wrong_answer_schedules_for_tomorrow(self):
        self._answer("incorrect")
        review = self._review()
        self.assertEqual(review.interval, 1)
        self.assertEqual(review.repetitions, 0)
        self.assertEqual(review.due_date, self.today + datetime.timedelta(days=1))

    def test_no_answers_today_grades_nothing(self):
        _grade_topic(self.user, self.topic.id, self.today)
        self.assertFalse(TopicReview.objects.filter(user=self.user, topic=self.topic).exists())

    def test_grade_records_one_daily_grade_row(self):
        self._answer("correct_first", "correct_first", "incorrect")
        self.assertEqual(
            DailyTopicGrade.objects.filter(
                user=self.user, topic=self.topic, date=self.today
            ).count(),
            1,
        )

    def test_repeats_count_as_one_review(self):
        # Mature topic: two right answers in a day climb the ladder one rung,
        # the same as one right answer.
        self._mature()
        self._answer("correct_first")
        after_one = self._review()
        self._answer("correct_first")
        after_two = self._review()
        self.assertEqual(after_two.repetitions, 4)
        self.assertEqual(after_two.interval, after_one.interval)
        self.assertEqual(after_two.due_date, after_one.due_date)

    def test_single_slip_among_right_answers_is_a_pass(self):
        # 3 of 4 right is 75%: a normal pass that keeps ease, not a lapse.
        self._mature()
        self._answer("correct_first", "incorrect", "correct_first", "correct_first")
        review = self._review()
        self.assertEqual(review.repetitions, 4)
        self.assertGreater(review.interval, 10)
        self.assertAlmostEqual(review.ease, 2.5)

    def test_mostly_wrong_day_lapses(self):
        self._mature()
        self._answer("correct_first", "incorrect", "incorrect")
        review = self._review()
        self.assertEqual((review.interval, review.repetitions), (1, 0))

    def test_repeated_misses_do_not_compound_from_snapshot(self):
        # Two misses in a day must equal one miss — recomputed from the snapshot,
        # not applied twice (which would drop ease twice).
        self._mature()
        self._answer("incorrect")
        ease_after_one = self._review().ease
        self._answer("incorrect")
        self.assertEqual(self._review().ease, ease_after_one)

    def test_second_attempt_grades_lower_than_first(self):
        # A day of second-try answers (50%) grades lower than a first-try day.
        other = make_topic(self.course, topic_name="Other", generator_name="gcd")
        select(self.user, other)
        self._answer("correct_first")
        self._answer("correct_second", topic=other)
        self.assertGreater(self._review().ease, self._review(other).ease)

    def test_early_miss_then_recovery_restores_the_schedule(self):
        # Not due for 5 days: an early miss resets it, but answering well for
        # the rest of the day makes it an early pass, which leaves the
        # morning's schedule, due date included, as it was.
        due = self.today + datetime.timedelta(days=5)
        self._mature(due_date=due)
        self._answer("incorrect")
        self.assertEqual(self._review().due_date, self.today + datetime.timedelta(days=1))
        self._answer("correct_first", "correct_first", "correct_first", "correct_first")
        review = self._review()
        self.assertEqual((review.interval, review.repetitions, review.due_date), (10, 3, due))

    def test_learning_day_is_judged_by_its_last_answers(self):
        # A new topic missed while being worked out, then answered right: the
        # last five answers are all right, so it passes and ease goes up.
        self._answer("incorrect", "incorrect", "incorrect", *["correct_first"] * 5)
        review = self._review()
        self.assertEqual((review.interval, review.repetitions), (1, 1))
        self.assertGreater(review.ease, 2.5)

    def test_graduation_floor_survives_regrading(self):
        self._answer("correct_first")
        grade = DailyTopicGrade.objects.get(user=self.user, topic=self.topic, date=self.today)
        grade.floor_interval = 6
        grade.save()
        self._answer("correct_first")
        review = self._review()
        self.assertEqual(review.interval, 6)
        self.assertEqual(review.due_date, self.today + datetime.timedelta(days=6))


@mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
class AddPracticeTests(TestCase):
    """Cards the deck adds during the day: learning steps and confirming a slip."""

    DAY = "2026-07-21"

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.topic = make_topic(make_course(), generator_name="gcd")
        select(self.user, self.topic)
        Settings.objects.update_or_create(user=self.user, defaults={"questions_per_day": 1})

    def _advance(self, outcome):
        return self.client.post(
            f"/deck/advance/?today={self.DAY}",
            data=json.dumps({"outcome": outcome}), content_type="application/json",
        ).json()

    def test_new_topic_keeps_coming_back_until_three_of_four_right(self, _gen):
        self.assertEqual(self.client.get(f"/deck/?today={self.DAY}").json()["total"], 1)
        for outcome in ("correct_first", "incorrect", "correct_first"):
            data = self._advance(outcome)
            self.assertNotIn("completed", data)  # not enough yet: another card
        data = self._advance("correct_first")  # 3 of the last 4 right
        self.assertEqual(data, {"completed": True, "total": 4})
        kinds = [p.get("kind") for p in DailyDeck.objects.get(user=self.user).problems]
        self.assertEqual(kinds, ["pool", "extra", "extra", "extra"])

    def test_learning_cards_stop_at_the_daily_topic_limit(self, _gen):
        from myapp import practice
        self.client.get(f"/deck/?today={self.DAY}")
        for _ in range(practice.MAX_TOPIC_CARDS_PER_DAY):
            data = self._advance("incorrect")
        self.assertEqual(data, {"completed": True, "total": practice.MAX_TOPIC_CARDS_PER_DAY})

    def test_slip_on_a_lone_review_card_gets_a_confirming_card(self, _gen):
        TopicReview.objects.create(
            user=self.user, topic=self.topic, ease=2.5, interval=8, repetitions=3,
            due_date=datetime.date(2026, 7, 21),
        )
        self.client.get(f"/deck/?today={self.DAY}")
        self._advance("incorrect")  # a lapse on one card: confirm before it sticks
        for _ in range(3):
            data = self._advance("correct_first")
        self.assertEqual(data, {"completed": True, "total": 4})
        review = TopicReview.objects.get(user=self.user, topic=self.topic)
        # 3 of 4: a normal pass, not a lapse, and no ease lost to the slip.
        self.assertEqual(review.repetitions, 4)
        self.assertAlmostEqual(review.ease, 2.5)

    def test_known_topic_answered_right_gets_no_extra_cards(self, _gen):
        TopicReview.objects.create(
            user=self.user, topic=self.topic, ease=2.5, interval=8, repetitions=3,
            due_date=datetime.date(2026, 7, 21),
        )
        self.client.get(f"/deck/?today={self.DAY}")
        self.assertEqual(self._advance("correct_first"), {"completed": True, "total": 1})


class AdvanceGradingTests(TestCase):
    """The advance endpoint grading the card being left."""

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.course = make_course()
        self.topic = make_topic(self.course, generator_name="gcd")
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 3}
        )

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_advance_with_outcome_grades_the_current_card(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self.client.post(
            "/deck/advance/?today=2026-07-21",
            data=json.dumps({"outcome": "correct_first"}),
            content_type="application/json",
        )
        review = TopicReview.objects.get(user=self.user, topic=self.topic)
        self.assertEqual(review.due_date, datetime.date(2026, 7, 22))

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_advance_logs_answer_with_capped_seconds(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        for outcome, seconds in (("incorrect", 42), ("correct_second", 99999)):
            self.client.post(
                "/deck/advance/?today=2026-07-21",
                data=json.dumps({"outcome": outcome, "seconds": seconds}),
                content_type="application/json",
            )
        rows = list(
            AnswerRecord.objects.filter(user=self.user)
            .order_by("id").values_list("topic_id", "date", "outcome", "seconds")
        )
        self.assertEqual(rows, [
            (self.topic.id, datetime.date(2026, 7, 21), "incorrect", 42),
            (self.topic.id, datetime.date(2026, 7, 21), "correct_second", 600),
        ])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_advance_without_outcome_logs_no_answer(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self.client.post(
            "/deck/advance/?today=2026-07-21",
            data=json.dumps({"seconds": 5}), content_type="application/json",
        )
        self.assertFalse(AnswerRecord.objects.filter(user=self.user).exists())

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_advance_without_body_does_not_grade(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self.client.post("/deck/advance/?today=2026-07-21")
        self.assertFalse(TopicReview.objects.filter(user=self.user).exists())

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_stray_advance_on_new_day_does_not_grade(self, mock_gen):
        # No deck exists yet for the new day: the advance builds one at index 0
        # and must not grade (nothing was answered).
        self.client.post(
            "/deck/advance/?today=2026-07-21",
            data=json.dumps({"outcome": "correct_first"}),
            content_type="application/json",
        )
        self.assertFalse(TopicReview.objects.filter(user=self.user).exists())


_STEPS = [{"text": "Add $1$ and $1$.", "math": "1+1=2"}]


class ProblemReportTests(TestCase):
    """Filing a "Report issue" report alongside a deck advance."""

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.topic = make_topic(make_course(), generator_name="gcd")
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 3}
        )

    def _advance(self, body):
        return self.client.post(
            "/deck/advance/?today=2026-07-21",
            data=json.dumps(body), content_type="application/json",
        ).json()

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_report_snapshots_the_served_card_and_grades_it_correct(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        data = self._advance({
            "outcome": "correct_first", "from_number": 1,
            "report": {"reason": "answer_marked_wrong", "user_answer": " 2.0 "},
        })
        self.assertEqual(data["current_number"], 2)
        report = ProblemReport.objects.get(user=self.user)
        self.assertEqual(report.topic, self.topic)
        self.assertEqual(report.reason, ProblemReport.ANSWER_MARKED_WRONG)
        self.assertEqual(report.problem, "$1+1=$")
        self.assertEqual(report.solution, "2")
        self.assertEqual(report.user_answer, "2.0")
        self.assertEqual(report.date, datetime.date(2026, 7, 21))
        self.assertFalse(report.resolved)
        # Scheduled as a clean first-try success, not a lapse.
        review = TopicReview.objects.get(user=self.user, topic=self.topic)
        self.assertEqual((review.repetitions, review.interval), (1, 1))

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$", _STEPS))
    def test_report_snapshots_the_steps_shown(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self._advance({"outcome": "correct_first", "report": {"reason": "solution_incorrect"}})
        self.assertEqual(ProblemReport.objects.get(user=self.user).steps, _STEPS)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_other_reason_keeps_its_description(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self._advance({
            "outcome": "correct_first",
            "report": {"reason": "other", "details": "  The question is ambiguous.  "},
        })
        report = ProblemReport.objects.get(user=self.user)
        self.assertEqual(report.details, "The question is ambiguous.")

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_invalid_reports_are_dropped_but_still_advance(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        data = self._advance({"outcome": "correct_first", "report": {"reason": "bogus"}})
        self.assertEqual(data["current_number"], 2)
        # "Other" needs a description.
        self._advance({"outcome": "correct_first", "report": {"reason": "other", "details": "  "}})
        self._advance({"outcome": "correct_first", "report": "not a dict"})
        self.assertFalse(ProblemReport.objects.exists())

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_details_are_capped(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self._advance({
            "outcome": "correct_first",
            "report": {"reason": "other", "details": "x" * 5000, "user_answer": "y" * 900},
        })
        report = ProblemReport.objects.get(user=self.user)
        self.assertEqual(len(report.details), 2000)
        self.assertEqual(len(report.user_answer), 500)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_stale_advance_files_no_report(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self._advance({
            "outcome": "correct_first", "from_number": 3,
            "report": {"reason": "solution_incorrect"},
        })
        self.assertFalse(ProblemReport.objects.exists())

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_report_survives_its_topic_being_deleted(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self._advance({"outcome": "correct_first", "report": {"reason": "solution_incorrect"}})
        self.topic.delete()
        report = ProblemReport.objects.get(user=self.user)
        self.assertIsNone(report.topic)
        self.assertEqual(report.problem, "$1+1=$")


class CheckAnswerTests(TestCase):
    """Server-side answer checking: the deck never ships the solution."""

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.topic = make_topic(make_course(), generator_name="gcd")
        select(self.user, self.topic)
        Settings.objects.update_or_create(
            user=self.user, defaults={"questions_per_day": 3}
        )

    def _check(self, answer, from_number=1):
        return self.client.post(
            "/deck/check/?today=2026-07-21",
            data=json.dumps({"answer": answer, "from_number": from_number}),
            content_type="application/json",
        )

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_deck_payloads_omit_the_solution(self, mock_gen):
        data = self.client.get("/deck/?today=2026-07-21").json()
        self.assertNotIn("solution", data)
        self.assertEqual(data["attempt"], 1)
        data = self.client.post(
            "/deck/advance/?today=2026-07-21",
            data=json.dumps({"from_number": 1}), content_type="application/json",
        ).json()
        self.assertNotIn("solution", data)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_correct_answer_text_or_number(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        for answer in ("2", " 2 ", "2.0"):
            self.assertEqual(self._check(answer).json(), {"correct": True, "attempts_left": 2})

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_solution_revealed_only_when_attempts_run_out(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self.assertEqual(self._check("3").json(), {"correct": False, "attempts_left": 1})
        # A reload resumes the second attempt instead of handing out fresh ones.
        self.assertEqual(self.client.get("/deck/?today=2026-07-21").json()["attempt"], 2)
        self.assertEqual(
            self._check("4").json(), {"correct": False, "attempts_left": 0, "solution": "2", "steps": []}
        )
        # No guessing after the reveal: even the right answer is now refused.
        self.assertEqual(
            self._check("2").json(), {"correct": False, "attempts_left": 0, "solution": "2", "steps": []}
        )

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$", _STEPS))
    def test_reload_after_the_reveal_reopens_the_revealed_card(self, mock_gen):
        self.assertNotIn("revealed", self.client.get("/deck/?today=2026-07-21").json())
        self._check("3")
        self.assertNotIn("revealed", self.client.get("/deck/?today=2026-07-21").json())
        self._check("4")
        data = self.client.get("/deck/?today=2026-07-21").json()
        self.assertEqual(data["current_number"], 1)
        self.assertEqual(data["revealed"], {"solution": "2", "steps": _STEPS})
        # Moving on clears it for the next card.
        data = self.client.post(
            "/deck/advance/?today=2026-07-21",
            data=json.dumps({"outcome": "incorrect", "from_number": 1}),
            content_type="application/json",
        ).json()
        self.assertNotIn("revealed", data)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$", _STEPS))
    def test_steps_revealed_with_the_solution(self, mock_gen):
        data = self.client.get("/deck/?today=2026-07-21").json()
        self.assertNotIn("steps", data)
        self.assertNotIn("steps", self._check("3").json())
        self.assertEqual(self._check("4").json()["steps"], _STEPS)
        self.assertEqual(self._check("2").json()["steps"], _STEPS)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_card_from_before_steps_reveals_no_steps(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        deck = DailyDeck.objects.get(user=self.user)
        for card in deck.problems:
            del card["steps"]
        deck.save()
        self._check("3")
        self.assertEqual(self._check("4").json()["steps"], [])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_advance_resets_attempts(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self._check("3")
        self._check("4")
        data = self.client.post(
            "/deck/advance/?today=2026-07-21",
            data=json.dumps({"outcome": "incorrect", "from_number": 1}),
            content_type="application/json",
        ).json()
        self.assertEqual(data["attempt"], 1)
        self.assertEqual(self._check("2", from_number=2).json()["correct"], True)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1/2=$", "1/3"))
    def test_numbers_must_parse_in_full(self, mock_gen):
        # parseFloat would read both "1/2" and "1/3" as 1 and call them equal.
        self.client.get("/deck/?today=2026-07-21")
        self.assertFalse(self._check("1/2").json()["correct"])

    @mock.patch("myapp.views.mathgenerator.gcd",
                side_effect=lambda: ("$8/3$", f"${num(Fraction(8, 3))}$"))
    def test_truncated_answer_is_also_correct(self, mock_gen):
        # 8/3 = 2.6666...: rounded is 2.667, truncated is 2.666; nothing else.
        self.client.get("/deck/?today=2026-07-21")
        self.assertTrue(self._check("2.667").json()["correct"])
        self.assertTrue(self._check("2.666").json()["correct"])
        self.assertFalse(self._check("2.665").json()["correct"])

    @mock.patch("myapp.views.mathgenerator.gcd",
                side_effect=lambda: ("$(5/3, 3/2)$", f"({num(Fraction(5, 3))}, {num(Fraction(3, 2))})"))
    def test_each_number_may_be_truncated(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        self.assertTrue(self._check("(1.666, 1.5)").json()["correct"])
        self.assertTrue(self._check("(1.667, 1.5)").json()["correct"])
        # 1.5 is exact, so there's nothing to truncate: 1.4 is just wrong.
        self.assertFalse(self._check("(1.666, 1.4)").json()["correct"])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_card_from_before_alternatives_still_grades(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        deck = DailyDeck.objects.get(user=self.user)
        for card in deck.problems:
            del card["alternatives"]
        deck.save()
        self.assertTrue(self._check("2").json()["correct"])

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_stale_card_and_bad_input(self, mock_gen):
        self.assertEqual(self._check("2").status_code, 409)  # no deck yet
        self.client.get("/deck/?today=2026-07-21")
        self.assertEqual(self._check("2", from_number=2).status_code, 409)
        self.assertEqual(self._check("   ").status_code, 400)
        self.assertEqual(DailyDeck.objects.get(user=self.user).attempts, 0)

    @mock.patch("myapp.views.mathgenerator.gcd", return_value=("$1+1=$", "$2$"))
    def test_test_solution_endpoint_is_hidden_unless_enabled(self, mock_gen):
        self.client.get("/deck/?today=2026-07-21")
        url = "/deck/test-solution/?today=2026-07-21"
        with self.settings(ENABLE_TEST_LOGIN=False):
            self.assertEqual(self.client.get(url).status_code, 404)
        with self.settings(ENABLE_TEST_LOGIN=True):
            self.assertEqual(self.client.get(url).json(), {"solution": "2"})


class PruneOrphanedTopicsTests(TestCase):
    """The 0010 migration must delete topics no longer in the seed and purge
    their frozen cards from cached decks, keeping the student on the same
    remaining card. A topic removed from the seed used to linger in the DB,
    still selected and still served from cached decks — that's how untypeable
    matrix/complex answers kept surfacing, and how a user with only removed
    topics selected still saw cards while the Courses page showed nothing."""

    def setUp(self):
        self.user = make_user()
        self.course = make_course()

    def test_orphaned_topic_and_its_cards_are_removed(self):
        # `addition` is in the seed (valid); a made-up name is not (orphaned).
        valid = make_topic(self.course, topic_name="Addition of two numbers",
                            generator_name="addition")
        orphan = make_topic(self.course, topic_name="Old Matrix Topic",
                            generator_name="matrix_multiplication_removed")
        select(self.user, valid)
        select(self.user, orphan)

        # A cached deck interleaving valid and orphaned cards, cursor at index 2.
        DailyDeck.objects.create(
            user=self.user,
            date=datetime.date(2026, 7, 22),
            current_index=2,
            problems=[
                {"problem": "v0", "solution": "1", "topic_id": valid.id},
                {"problem": "orphan1", "solution": r"\begin{bmatrix}1\end{bmatrix}",
                 "topic_id": orphan.id},
                {"problem": "v1", "solution": "2", "topic_id": valid.id},
                {"problem": "orphan2", "solution": r"\frac{1}{2}", "topic_id": orphan.id},
            ],
        )

        from django.apps import apps
        import importlib
        migration = importlib.import_module(
            "myapp.migrations.0010_prune_orphaned_topics"
        )
        migration.prune_orphaned_topics(apps, None)

        # Orphaned topic and its selection are gone; valid topic remains.
        self.assertFalse(Topic.objects.filter(id=orphan.id).exists())
        self.assertTrue(Topic.objects.filter(id=valid.id).exists())
        self.assertFalse(
            UserTopicSelection.objects.filter(topic_id=orphan.id).exists()
        )

        # The cached deck keeps only the valid cards, and the cursor shifts back
        # by the one orphaned card that sat before it (index 2 -> 1).
        deck = DailyDeck.objects.get(user=self.user)
        self.assertEqual([p["problem"] for p in deck.problems], ["v0", "v1"])
        self.assertEqual(deck.current_index, 1)
