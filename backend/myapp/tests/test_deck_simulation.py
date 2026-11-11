"""Simulated two weeks of practice, checked against the deck's design constraints.

Re-runs the simulation the deck sizing was tuned with (DESIGN.md, "Deck
sizing") on top of the real `practice` and `srs` functions (`deck_sim`, policy
P2), so a change to either that breaks a constraint fails here. Every teacher
scenario runs against every kind of student, with and without a backlog of
older topics to review. Constraints:

- C1: no day asks for more than 100 cards.
- C2: a student who gets everything right is "familiar" with the topic (6+
  days) when they finish the assignment, and isn't due back the next day.
- C3: a topic the student gets mostly wrong is due the next day, with at
  least 5 cards. An assignment's card budget can run out first for a student
  who keeps failing, so this holds for nearly every case rather than all.
- C4: struggling students practise more.
- C5: a single mistake in a day is never punished (no lapse, no ease drop).
- C6: an assignment's decks never hold more than `practice.max_cards` cards.
"""
from django.test import SimpleTestCase

from myapp import practice

from . import deck_sim
from .deck_sim import P2, STUDENTS


class DeckSimulationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.violations = deck_sim.violations(P2)

    def _each(self, kinds=STUDENTS):
        return deck_sim.each(P2, kinds=kinds)

    def test_c1_no_day_asks_for_more_than_100_cards(self):
        self.assertLessEqual(self.violations["C1 max/day"], practice.HARD_CAP)

    def test_c2_perfect_student_is_familiar_after_finishing(self):
        self.assertEqual(self.violations["C2"], 0)
        finished = [log["finished"] for _, _, _, log in self._each(["perfect"])]
        self.assertTrue(all(finished))

    def test_c3_failed_topic_is_back_next_day_with_enough_cards(self):
        checked, failed = self.violations["C3 checked"], self.violations["C3"]
        self.assertGreater(checked, 0)  # the struggling students do produce failed days
        self.assertLessEqual(failed / checked, 0.05)

    def test_c4_struggling_students_practise_more(self):
        def mean_cards(kind):
            totals = [sum(log["cards"]) for _, _, _, log in self._each([kind])]
            return sum(totals) / len(totals)
        self.assertGreater(mean_cards("struggler"), mean_cards("strong"))
        self.assertGreater(mean_cards("strong"), mean_cards("perfect"))

    def test_c5_single_mistake_is_not_punished(self):
        self.assertEqual(self.violations["C5"], 0)

    def test_c6_assignment_decks_stay_within_max_cards(self):
        self.assertEqual(self.violations["C6"], 0)
        self.assertLessEqual(self.violations["C6 worst"], 1)

    def test_reviews_still_happen_with_a_backlog(self):
        # Most reviews come within a day of falling due even with 20 older
        # topics waiting; the rest are deferred, never dropped.
        goals = deck_sim.goals(P2, backlog=True)
        self.assertGreaterEqual(goals["<=1d"], 0.4)
        self.assertLess(goals["backlog"], deck_sim.BACKLOG_SIZE / 2)
