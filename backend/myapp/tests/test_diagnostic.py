"""Tests for the diagnostic onboarding flow.

Two layers: the pure unit-taxonomy/seeding logic in ``myapp.diagnostic_config``
(no DB), and the three HTTP endpoints that resolve it against real courses/topics
and write selections + SM-2 schedule.
"""
import json
from unittest import mock

from django.test import TestCase, SimpleTestCase, Client

from myapp.models import UserTopicSelection, TopicReview
from myapp.diagnostic_config import (
    COURSE_UNITS,
    aggregate_learned_band,
    current_unit_topic_names,
    learned_unit_topic_names,
    seed_state_for_band,
    topic_order_key,
    units_for_course,
)
from myapp.management.commands.seed_courses import CURRICULUM
from .factories import make_user, make_course, make_topic


class SeedBandTests(SimpleTestCase):
    """The pure SM-2 seeding bands, exercised without a database."""

    def test_seed_state_lands_each_band_in_its_bucket(self):
        # Intervals must land each band in its dashboard mastery bucket
        # (New <=1, Learning 2-5, Familiar 6-20, Proficient >=21).
        self.assertEqual(seed_state_for_band("new"), (2.5, 0, 0))
        _, learning_interval, _ = seed_state_for_band("learning")
        self.assertTrue(2 <= learning_interval <= 5)
        _, familiar_interval, _ = seed_state_for_band("familiar")
        self.assertTrue(6 <= familiar_interval <= 20)
        _, proficient_interval, _ = seed_state_for_band("proficient")
        self.assertGreaterEqual(proficient_interval, 21)

    def test_aggregate_band_from_outcomes(self):
        # No problems -> the neutral default.
        self.assertEqual(aggregate_learned_band([]), "learning")
        # Acing them bumps the earlier units up to familiar.
        self.assertEqual(
            aggregate_learned_band(["correct_first", "correct_first", "correct_first"]),
            "familiar",
        )
        # Mostly missing them drops the earlier units to new.
        self.assertEqual(
            aggregate_learned_band(["incorrect", "incorrect", "correct_second"]),
            "new",
        )
        # A middling run stays at the learning default.
        self.assertEqual(
            aggregate_learned_band(["correct_first", "correct_second", "incorrect"]),
            "learning",
        )
        # Unknown/garbage outcome strings are ignored, not scored as 0.
        self.assertEqual(aggregate_learned_band(["bogus"]), "learning")


class UnitTaxonomyTests(SimpleTestCase):
    """The Georgia-curriculum unit taxonomy — pure, no database."""

    def test_every_curriculum_topic_lands_in_exactly_one_unit(self):
        # The taxonomy must stay in lockstep with the seeded curriculum: every
        # topic of every course belongs to exactly one unit, with no strays.
        for course_name, _grade, topic_names in CURRICULUM:
            units = COURSE_UNITS.get(course_name)
            self.assertIsNotNone(units, f"{course_name} has no authored units")
            unit_topics = [t for u in units for t in u["topics"]]
            self.assertEqual(
                len(unit_topics), len(set(unit_topics)),
                f"{course_name} lists a topic in more than one unit",
            )
            self.assertEqual(
                set(unit_topics), set(topic_names),
                f"{course_name} units don't cover its curriculum topics exactly",
            )

    def test_unit_keys_are_globally_unique(self):
        keys = [u["key"] for units in COURSE_UNITS.values() for u in units]
        self.assertEqual(len(keys), len(set(keys)))

    def test_learned_topics_accumulate_up_to_the_reported_unit(self):
        # The reported unit is the frontier: its topics and every earlier unit's
        # topics count as learned; later units do not.
        learned = learned_unit_topic_names("Grade 8", "g8-u2")
        self.assertIn("Square Root", learned)          # unit 1
        self.assertIn("Linear Equations", learned)     # unit 2 (the reported one)
        self.assertNotIn("Evaluate a Function", learned)   # unit 3, not yet reached
        self.assertNotIn("Pythagorean Theorem", learned)   # unit 4, not yet reached

    def test_current_unit_topics_are_just_the_reported_unit(self):
        current = current_unit_topic_names("Grade 8", "g8-u2")
        self.assertEqual(current, set(units_for_course("Grade 8")[1]["topics"]))
        self.assertIn("Linear Equations", current)         # unit 2
        self.assertNotIn("Square Root", current)           # unit 1, already behind

    def test_topic_order_key_follows_unit_sequence(self):
        # Topics sort by their flattened unit order: unit 1's topics before
        # unit 2's, regardless of how they'd sort alphabetically or by id.
        flat = [t for u in units_for_course("Grade 8") for t in u["topics"]]
        shuffled = sorted(flat, reverse=True)
        ordered = sorted(shuffled, key=lambda n: topic_order_key("Grade 8", n))
        self.assertEqual(ordered, flat)
        # A stray not in the taxonomy sorts after everything known.
        self.assertGreater(
            topic_order_key("Grade 8", "Not A Real Topic"),
            topic_order_key("Grade 8", flat[-1]),
        )

    def test_unknown_unit_treats_the_whole_course_as_learned(self):
        # A missing/blank unit key falls back to the whole course, so the current
        # course is never left empty.
        all_g8 = {t for u in units_for_course("Grade 8") for t in u["topics"]}
        self.assertEqual(learned_unit_topic_names("Grade 8", None), all_g8)
        self.assertEqual(learned_unit_topic_names("Grade 8", "nope"), all_g8)


# Grade 8 topics laid out across its four units, in unit order (ascending id =
# curriculum order), so the "learned up to unit N" slice is observable.
_G8_TOPICS = [
    "Square Root", "Cube Root",                      # g8-u1
    "Linear Equations", "Slope from Two Points",     # g8-u2
    "Evaluate a Function",                           # g8-u3
    "Pythagorean Theorem",                           # g8-u4
]


def _build_courses():
    """Create real-named courses/topics for the middle-school band the tests use.

    Topic names must match the unit taxonomy, so they're drawn verbatim from the
    curriculum. Grades 6 and 7 get a couple of topics each (review material);
    Grade 8 spans all four of its units so the learned-frontier slice is testable.
    """
    courses = {}
    specs = {
        "Grade 6": (6, ["Absolute difference between two numbers", "Percentage of a number"]),
        "Grade 7": (7, ["Solve a Proportion", "Simple Interest"]),
        "Grade 8": (8, _G8_TOPICS),
    }
    for name, (grade, topic_names) in specs.items():
        course = make_course(course_name=name, grade_level=grade)
        for tname in topic_names:
            make_topic(course, topic_name=tname, generator_name="addition")
        courses[name] = course
    return courses


class DiagnosticConfigTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.courses = _build_courses()

    def test_returns_courses_and_units_per_course(self):
        data = self.client.get("/diagnostic/config/").json()
        self.assertTrue(any(c["course_name"] == "Grade 8" for c in data["courses"]))

        g8 = self.courses["Grade 8"]
        g8_units = data["units_by_course"][str(g8.id)]
        # All four Grade 8 units have a seeded topic, so all are offered, in order.
        self.assertEqual([u["key"] for u in g8_units],
                         ["g8-u1", "g8-u2", "g8-u3", "g8-u4"])
        self.assertEqual(g8_units[0]["name"], "Real Numbers, Exponents & Scientific Notation")

    def test_units_without_a_seeded_topic_are_omitted(self):
        # Grade 6 only seeds a topic in units 1 and 2, so units 3-5 are omitted.
        data = self.client.get("/diagnostic/config/").json()
        g6 = self.courses["Grade 6"]
        self.assertEqual([u["key"] for u in data["units_by_course"][str(g6.id)]],
                         ["g6-u1", "g6-u2"])

    def test_courses_ordered_by_curriculum_not_alphabet(self):
        # Add the grade-12 trio that alphabetizes wrongly (AP Calculus < Pre-Calculus).
        for name in ("Statistical Reasoning", "Pre-Calculus", "AP Calculus"):
            make_course(course_name=name, grade_level=12)
        names = [c["course_name"] for c in self.client.get("/diagnostic/config/").json()["courses"]]
        self.assertLess(names.index("Pre-Calculus"), names.index("AP Calculus"))
        self.assertLess(names.index("Statistical Reasoning"), names.index("Pre-Calculus"))

    def test_requires_auth(self):
        self.client.logout()
        self.assertEqual(self.client.get("/diagnostic/config/").status_code, 401)


class TopicOrderingTests(TestCase):
    """The topic-list endpoints serve topics in curriculum unit order."""

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def test_course_topics_returned_in_unit_order(self):
        # Seed Grade 8 topics in reverse unit order; the endpoint must still hand
        # them back in unit order (unit 1's topics first).
        unit_order = [t for u in units_for_course("Grade 8") for t in u["topics"]]
        course = make_course(course_name="Grade 8", grade_level=8)
        for tname in reversed(unit_order):
            make_topic(course, topic_name=tname, generator_name="addition")

        data = self.client.get(f"/courses/{course.id}/topics").json()
        self.assertEqual([t["topic_name"] for t in data["topics"]], unit_order)

    def test_all_topics_endpoint_orders_within_each_course(self):
        g8_order = [t for u in units_for_course("Grade 8") for t in u["topics"]]
        course = make_course(course_name="Grade 8", grade_level=8)
        for tname in reversed(g8_order):
            make_topic(course, topic_name=tname, generator_name="addition")

        rows = self.client.get("/topics/").json()["topics"]
        g8_names = [t["topic_name"] for t in rows if t["course_id"] == course.id]
        self.assertEqual(g8_names, g8_order)


class DiagnosticStartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.courses = _build_courses()

    def _start(self, body):
        return self.client.post(
            "/diagnostic/start/", data=json.dumps(body), content_type="application/json"
        )

    @mock.patch("myapp.views.mathgenerator.addition", return_value=("$1+1=$", "$2$"))
    def test_problems_drawn_only_from_learned_units(self, _mock_add):
        # Current unit g8-u2 -> learned = units 1 and 2 (four topics). The three
        # problems must all come from those, never the not-yet-reached units.
        learned_names = learned_unit_topic_names("Grade 8", "g8-u2")
        learned_ids = set(
            self.courses["Grade 8"].topics
            .filter(topic_name__in=learned_names)
            .values_list("id", flat=True)
        )
        body = {"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u2"}
        problems = self._start(body).json()["problems"]

        self.assertEqual(len(problems), 3)  # capped at NUM_CALIBRATION_PROBLEMS
        for p in problems:
            self.assertTrue(p["problem"])
            self.assertIn("solution", p)
            self.assertIn(p["topic_id"], learned_ids)


class DiagnosticSubmitTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.courses = _build_courses()

    def _submit(self, body):
        return self.client.post(
            "/diagnostic/submit/", data=json.dumps(body), content_type="application/json"
        )

    def _selected_course_names(self):
        rows = UserTopicSelection.objects.filter(user=self.user).select_related("topic__course")
        return {r.topic.course.course_name for r in rows}

    def _selected_in(self, course):
        return set(
            UserTopicSelection.objects
            .filter(user=self.user, topic__course=course)
            .values_list("topic__topic_name", flat=True)
        )

    def test_selects_current_course_learned_units_plus_prior_year(self):
        body = {"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u2"}
        data = self._submit(body).json()
        # Current course + the prior-year course (Grade 7) only. Grade 6 (two
        # years below) is not selected.
        self.assertEqual(self._selected_course_names(), {"Grade 7", "Grade 8"})
        # Grade 8: the learned units (4 topics); Grade 7 in full (2 topics).
        self.assertEqual(data["selected_count"], 4 + 2)
        self.assertEqual(data["by_course"], {"Grade 8": 4, "Grade 7": 2})

    def test_current_course_selects_only_learned_units(self):
        body = {"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u2"}
        self._submit(body)
        selected = self._selected_in(self.courses["Grade 8"])
        # Only the seeded topics of the learned units (u1 + u2) — the taxonomy
        # names without a topic row in this test course don't appear.
        self.assertEqual(
            selected,
            {"Square Root", "Cube Root", "Linear Equations", "Slope from Two Points"},
        )
        # The not-yet-reached units are left out.
        self.assertNotIn("Evaluate a Function", selected)   # unit 3
        self.assertNotIn("Pythagorean Theorem", selected)   # unit 4

    def test_prior_year_course_is_fully_selected_and_two_below_is_not(self):
        body = {"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u2"}
        self._submit(body)
        g7 = self.courses["Grade 7"]
        self.assertEqual(
            UserTopicSelection.objects.filter(user=self.user, topic__course=g7).count(),
            g7.topics.count(),
        )
        self.assertEqual(self._selected_in(self.courses["Grade 6"]), set())

    def test_current_unit_is_new_earlier_units_follow_results(self):
        # Ace all three calibration problems -> earlier units land in "familiar".
        results = [{"topic_id": 1, "outcome": "correct_first"}] * 3
        body = {
            "current_course_id": self.courses["Grade 8"].id,
            "current_unit_key": "g8-u2",
            "results": results,
        }
        self._submit(body)
        reviews = {
            r.topic.topic_name: r
            for r in TopicReview.objects.filter(user=self.user).select_related("topic")
        }
        # Current unit (g8-u2) topics are seeded "new" (due now).
        self.assertEqual(reviews["Linear Equations"].interval, 0)
        self.assertEqual(reviews["Slope from Two Points"].interval, 0)
        # Earlier unit (g8-u1) topics land in the "familiar" band (interval 6..20).
        self.assertTrue(6 <= reviews["Square Root"].interval <= 20)
        # Prior-year course is proficient (interval >= 21).
        self.assertGreaterEqual(reviews["Solve a Proportion"].interval, 21)

    def test_bombed_results_push_earlier_units_to_new(self):
        results = [{"topic_id": 1, "outcome": "incorrect"}] * 3
        body = {
            "current_course_id": self.courses["Grade 8"].id,
            "current_unit_key": "g8-u2",
            "results": results,
        }
        self._submit(body)
        review = TopicReview.objects.get(user=self.user, topic__topic_name="Square Root")
        self.assertEqual(review.interval, 0)  # "new" band

    def test_rerun_is_idempotent_and_preserves_history(self):
        body = {"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u2"}
        self._submit(body)
        # Simulate real practice moving a topic's schedule forward.
        review = TopicReview.objects.filter(user=self.user).first()
        review.interval = 99
        review.save(update_fields=["interval"])

        self._submit(body)  # run again
        self.assertEqual(UserTopicSelection.objects.filter(user=self.user).count(), 6)
        review.refresh_from_db()
        self.assertEqual(review.interval, 99)  # existing history untouched

    def test_retake_with_an_earlier_unit_shrinks_the_current_course_slice(self):
        # First run near the end of the course (unit 4 -> all six topics learned).
        self._submit({"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u4"})
        self.assertEqual(len(self._selected_in(self.courses["Grade 8"])), 6)

        # Retake reporting an earlier unit (unit 1 -> only two topics learned). The
        # stale selections must be cleared, not accumulated.
        self._submit({"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u1"})
        selected = self._selected_in(self.courses["Grade 8"])
        self.assertEqual(selected, {"Square Root", "Cube Root"})
        self.assertNotIn("Linear Equations", selected)  # unit 2, now beyond the frontier

    def test_retake_clears_a_manually_selected_topic(self):
        # A topic the user picked by hand outside the diagnostic's plan is cleared
        # on submit, since the diagnostic owns the whole selection set.
        algebra2 = make_course(course_name="Algebra II", grade_level=11)
        stray_topic = make_topic(algebra2, topic_name="Logarithm", generator_name="addition")
        UserTopicSelection.objects.create(user=self.user, topic=stray_topic)

        self._submit({"current_course_id": self.courses["Grade 8"].id, "current_unit_key": "g8-u2"})
        self.assertFalse(
            UserTopicSelection.objects.filter(user=self.user, topic=stray_topic).exists()
        )
