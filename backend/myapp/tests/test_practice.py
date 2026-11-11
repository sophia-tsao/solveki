"""Tests for deck sizing and assignment completion in `myapp.practice`.

The functions under test are pure (no DB, no clock), so these use SimpleTestCase.
"""
from django.test import SimpleTestCase

from myapp import practice

F, S, X = "correct_first", "correct_second", "incorrect"


class EnoughTodayTests(SimpleTestCase):
    """A topic being learned needs 3 of its last 4 answers today right."""

    def test_one_right_answer_is_not_enough(self):
        self.assertFalse(practice.is_enough_today([F]))
        self.assertFalse(practice.is_enough_today([F, F]))

    def test_three_of_the_last_four(self):
        self.assertTrue(practice.is_enough_today([F, F, F]))
        self.assertTrue(practice.is_enough_today([X, X, F, X, F, S, F]))
        self.assertFalse(practice.is_enough_today([F, F, F, X, X]))

    def test_second_tries_count_as_right(self):
        self.assertTrue(practice.is_enough_today([S, S, S]))


class SolidTests(SimpleTestCase):
    """An assignment topic is solid: all right so far, or 3 of the last 4."""

    def test_no_answers_is_not_solid(self):
        self.assertFalse(practice.is_solid([]))

    def test_short_history_must_be_all_right(self):
        self.assertTrue(practice.is_solid([F]))
        self.assertTrue(practice.is_solid([F, S]))
        self.assertFalse(practice.is_solid([F, X, F]))

    def test_longer_history_needs_three_of_the_last_four(self):
        self.assertTrue(practice.is_solid([X, F, F, F]))
        self.assertFalse(practice.is_solid([F, F, X, X]))

    def test_cards_to_solid(self):
        self.assertEqual(practice.cards_to_solid([]), 1)
        self.assertEqual(practice.cards_to_solid([F, F]), 0)
        self.assertEqual(practice.cards_to_solid([F, X]), 2)
        self.assertEqual(practice.cards_to_solid([X, X, X, X]), 3)


class CompletionTests(SimpleTestCase):
    """The teacher's count is a minimum; struggling students get up to 1.5x."""

    def test_max_cards_rounds_up(self):
        self.assertEqual(practice.max_cards(10), 15)
        self.assertEqual(practice.max_cards(5), 8)

    def test_proficient_student_finishes_at_the_count(self):
        # Ten cards over five topics, two each, all right: done at exactly 10.
        outcomes = {t: [F, F] for t in range(5)}
        self.assertEqual(practice.cards_needed(10, 10, outcomes), 10)
        self.assertEqual(practice.is_complete(10, 10, outcomes), (True, False))

    def test_not_done_before_the_count_even_when_solid(self):
        self.assertEqual(practice.is_complete(10, 6, {1: [F] * 6}), (False, False))
        self.assertEqual(practice.cards_needed(10, 6, {1: [F] * 6}), 10)

    def test_shaky_topic_raises_cards_needed(self):
        outcomes = {1: [F] * 8 + [X, X], 2: [F, F]}
        self.assertEqual(practice.cards_needed(10, 10, outcomes), 13)
        self.assertEqual(practice.is_complete(10, 10, outcomes), (False, False))

    def test_cards_needed_never_passes_the_maximum(self):
        self.assertEqual(practice.cards_needed(4, 5, {1: [X] * 5}), 6)

    def test_maximum_completes_and_flags_needs_help(self):
        self.assertEqual(practice.is_complete(4, 6, {1: [X] * 6}), (True, True))
        # Reaching the maximum while solid isn't "needs help".
        self.assertEqual(practice.is_complete(4, 6, {1: [X, X, F, F, F, F]}), (True, False))

    def test_completion_pct_never_goes_down(self):
        self.assertEqual(practice.completion_pct(3, 4), 75)
        self.assertEqual(practice.completion_pct(4, 7, previous=75), 75)
        self.assertEqual(practice.completion_pct(6, 7, previous=75), 85)
        self.assertEqual(practice.completion_pct(9, 6), 100)


class AssignmentCardsTests(SimpleTestCase):
    """An assignment's share of today: remaining cards over days left."""

    def test_spread_over_days_left(self):
        self.assertEqual(practice.assignment_cards(20, 3, [1]), {1: 7})
        self.assertEqual(practice.assignment_cards(50, 1, [1]), {1: 50})

    def test_at_least_a_sitting_even_when_little_is_left(self):
        self.assertEqual(practice.assignment_cards(2, 5, [1]), {1: practice.MIN_SESSION})

    def test_nothing_left_or_no_topics(self):
        self.assertEqual(practice.assignment_cards(0, 3, [1]), {})
        self.assertEqual(practice.assignment_cards(10, 3, []), {})

    def test_split_across_as_few_topics_as_keep_a_sitting_each(self):
        # 10 cards today over three topics: two topics of 5, the third waits.
        self.assertEqual(practice.assignment_cards(10, 1, [7, 8, 9]), {7: 5, 8: 5})
        self.assertEqual(practice.assignment_cards(13, 1, [7, 8, 9]), {7: 5, 8: 4, 9: 4})


class PlanRequiredTests(SimpleTestCase):
    """Combining assignments, reviews and lapses under the daily caps."""

    def test_review_cards_rise_as_ease_falls(self):
        self.assertEqual(practice.review_cards(2.5), 8)
        self.assertEqual(practice.review_cards(1.3), 15)
        self.assertEqual(practice.review_cards(9.0), practice.MIN_SESSION)

    def test_assigned_and_due_topic_gets_the_larger_count_not_the_sum(self):
        plan = practice.plan_required({1: 4}, {1: 1.3}, {})
        self.assertEqual(plan, {1: 15})

    def test_everything_fits_under_the_cap(self):
        plan = practice.plan_required({1: 10}, {2: 2.5, 3: 2.5}, {})
        self.assertEqual(plan, {1: 10, 2: 8, 3: 8})

    def test_reviews_scale_down_to_fit_lowest_ease_first(self):
        reviews = {t: 1.3 for t in range(10, 20)}  # 15 cards each, 150 wanted
        plan = practice.plan_required({1: 50}, reviews, {})
        self.assertEqual(plan[1], 50)
        self.assertLessEqual(sum(plan.values()), practice.DAILY_CAP)
        self.assertTrue(all(plan[t] >= practice.MIN_SESSION for t in plan if t != 1))

    def test_lapsed_topics_get_their_review_ahead_of_the_rest(self):
        reviews = {t: 1.3 for t in range(10, 20)}
        lapsed = {10: 1.3, 11: 1.3}
        plan = practice.plan_required({1: 50}, reviews, lapsed)
        self.assertEqual((plan[10], plan[11]), (15, 15))

    def test_lapsed_topics_squeezed_to_the_minimum_but_under_the_hard_cap(self):
        lapsed = {t: 1.3 for t in range(10, 30)}  # 20 lapsed topics
        plan = practice.plan_required({1: 75}, dict(lapsed), lapsed)
        self.assertEqual({plan[t] for t in plan if t != 1}, {practice.LAPSE_REVIEW_CARDS})
        self.assertLessEqual(sum(plan.values()), practice.HARD_CAP)
        self.assertGreater(sum(plan.values()), practice.DAILY_CAP)


class AssignmentBudgetTests(SimpleTestCase):
    """An open assignment's decks hold at most max_cards cards; its own topics come first."""

    def test_review_limit_leaves_a_reserve_for_the_assignment(self):
        # N=20: 30 cards in all, 10 beyond the count; reviews get 3/4 of those.
        self.assertEqual(practice.review_limit(20), 7)
        self.assertEqual(practice.review_room(20, 0, 0, 20), 7)

    def test_review_room_shrinks_as_the_assignment_needs_more(self):
        self.assertEqual(practice.review_room(20, 10, 0, 18), 2)  # 30 - 10 - 18
        self.assertEqual(practice.review_room(20, 10, 0, 25), 0)
        self.assertEqual(practice.review_room(20, 5, 7, 0), 0)  # review limit used up

    def test_extra_fits_never_past_max_cards(self):
        self.assertTrue(practice.extra_fits(10, 14, 0, 0, review=False))
        self.assertFalse(practice.extra_fits(10, 15, 0, 0, review=False))
        # A review card also needs review room.
        self.assertFalse(practice.extra_fits(10, 10, 3, 0, review=True))
        self.assertTrue(practice.extra_fits(10, 10, 2, 0, review=True))

    def test_budget_spent_once_a_session_no_longer_fits(self):
        self.assertFalse(practice.budget_spent(10, 11))
        self.assertTrue(practice.budget_spent(10, 12))

    def test_urgency_puts_lapses_then_the_most_overdue_for_their_interval_first(self):
        keys = {
            "lapsed": practice.review_urgency(2.5, 1, 0, True),
            "3 late on 2": practice.review_urgency(2.5, 2, 3, False),
            "3 late on 30": practice.review_urgency(1.3, 30, 3, False),
        }
        self.assertEqual(sorted(keys, key=keys.get), ["lapsed", "3 late on 2", "3 late on 30"])

    def test_plan_keeps_within_the_cap_and_reviews_the_most_urgent(self):
        due = {t: (4, practice.review_urgency(2.0, 3, t, False)) for t in range(10, 30)}
        plan, reviews = practice.plan_assignment_deck({1: 4}, due, {1}, cap=18, room=6, still_needed=12)
        self.assertEqual(plan, {1: 4})
        self.assertEqual(list(reviews), [29])  # most overdue; one 4-card review fits 6
        self.assertLessEqual(sum(plan.values()) + sum(reviews.values()), 18)

    def test_own_due_topic_gets_a_lapse_review_without_spending_review_room(self):
        due = {1: (practice.LAPSE_REVIEW_CARDS, practice.review_urgency(1.7, 1, 0, True)),
               2: (4, practice.review_urgency(2.5, 3, 1, False))}
        plan, reviews = practice.plan_assignment_deck({1: 4}, due, {1}, cap=20, room=4, still_needed=10)
        self.assertEqual(plan, {1: 5})
        self.assertEqual(reviews, {2: 4})

    def test_trim_never_leaves_a_topic_under_a_session(self):
        plan, reviews = practice.plan_assignment_deck({1: 4, 2: 4}, {}, {1, 2}, cap=6, room=0, still_needed=8)
        self.assertEqual(plan, {1: 4})
        self.assertEqual(reviews, {})

    def test_a_deck_too_small_for_a_session_still_gets_what_fits(self):
        # A 2-card assignment holds 3 cards: a 4-card sitting is cut to 3.
        plan, _ = practice.plan_assignment_deck({1: 4}, {}, {1}, cap=3, room=0, still_needed=2)
        self.assertEqual(plan, {1: 3})

    def test_a_lapse_that_does_not_fully_fit_gets_a_session(self):
        due = {1: (practice.LAPSE_REVIEW_CARDS, practice.review_urgency(1.7, 1, 0, True))}
        plan, _ = practice.plan_assignment_deck({2: 4}, due, {1, 2}, cap=8, room=0, still_needed=4)
        self.assertEqual(plan, {2: 4, 1: 4})
