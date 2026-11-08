"""Tests for the SM-2 scheduling math in `myapp.srs`.

The functions under test are pure (no DB, no clock), so these use SimpleTestCase.
"""
from django.test import SimpleTestCase

from myapp import srs


class UpdateEaseTests(SimpleTestCase):
    def test_perfect_recall_raises_ease(self):
        # q=5 applies the full +0.1 bonus.
        self.assertAlmostEqual(srs.update_ease(2.5, 5), 2.6)

    def test_passing_but_hard_lowers_ease(self):
        # q=3 (correct but hard) pulls ease down.
        self.assertAlmostEqual(srs.update_ease(2.5, 3), 2.36)

    def test_ease_never_drops_below_floor(self):
        # Repeated failures from a low starting ease clamp at 1.3, not below.
        self.assertEqual(srs.update_ease(1.3, 0), srs.MIN_EASE)
        self.assertEqual(srs.update_ease(1.4, 0), srs.MIN_EASE)


class UpdateTests(SimpleTestCase):
    def test_first_success_schedules_one_day(self):
        ease, interval, reps = srs.update(2.5, 0, 0, 5)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 1)

    def test_second_success_multiplies_by_ease(self):
        # No fixed second rung: 1 day * ease 2.6 -> 3 days.
        ease, interval, reps = srs.update(2.5, 1, 1, 5)
        self.assertEqual(interval, round(1 * ease))
        self.assertEqual(interval, 3)
        self.assertEqual(reps, 2)

    def test_third_success_multiplies_by_ease(self):
        # After two reviews: interval 3, reps 2. Third success -> round(3 * ease).
        ease, interval, reps = srs.update(2.6, 3, 2, 5)
        self.assertEqual(interval, round(3 * ease))
        self.assertEqual(reps, 3)

    def test_success_grows_interval_by_at_least_a_day(self):
        # At the ease floor, round(1 * 1.3) would stay at 1; a success still
        # pushes the review out a day further.
        ease, interval, reps = srs.update(srs.MIN_EASE, 1, 1, 3)
        self.assertEqual(interval, 2)

    def test_perfect_ladder_takes_four_reviews_to_reach_three_weeks(self):
        # Answered perfectly on each due day: 1 -> 3 -> 8 -> 23 days.
        state, intervals = (srs.INITIAL_EASE, 0, 0), []
        for _ in range(4):
            state = srs.update(*state, 5)
            intervals.append(state[1])
        self.assertEqual(intervals, [1, 3, 8, 23])

    def test_lapse_resets_repetitions_and_interval(self):
        # A wrong answer on a mature item collapses it back to a 1-day interval.
        ease, interval, reps = srs.update(2.5, 30, 5, 1)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)

    def test_lapse_still_lowers_ease(self):
        # The ease update applies on a lapse too, so a missed item grows slower later.
        ease, interval, reps = srs.update(2.5, 30, 5, 1)
        self.assertLess(ease, 2.5)

    def test_lapse_respects_ease_floor(self):
        ease, interval, reps = srs.update(1.3, 30, 5, 0)
        self.assertEqual(ease, srs.MIN_EASE)

    def test_interval_capped_at_max(self):
        # A success on an already-huge interval is clamped, not multiplied past
        # the cap, so a mastered topic still resurfaces.
        ease, interval, reps = srs.update(2.5, srs.MAX_INTERVAL, 10, 5)
        self.assertEqual(interval, srs.MAX_INTERVAL)

    def test_interval_just_below_cap_does_not_exceed_it(self):
        # round(interval * ease) would overshoot; the cap holds it at MAX_INTERVAL.
        big = srs.MAX_INTERVAL - 1
        ease, interval, reps = srs.update(2.5, big, 10, 5)
        self.assertLessEqual(interval, srs.MAX_INTERVAL)

    def test_inputs_not_mutated(self):
        # Pure function: returns new values, leaves the caller's state alone.
        args = (2.5, 6, 2)
        srs.update(*args, 5)
        self.assertEqual(args, (2.5, 6, 2))


class GradeThresholdTests(SimpleTestCase):
    """The pass/lapse boundary sits at PASSING_GRADE (q=3): q>=3 succeeds, q<3 lapses."""

    def test_lowest_passing_grade_advances(self):
        # q=3 is the lowest passing grade: a fresh item advances (reps 0 -> 1,
        # interval to 1 day) rather than lapsing.
        ease, interval, reps = srs.update(2.5, 0, 0, srs.PASSING_GRADE)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 1)

    def test_highest_failing_grade_lapses(self):
        # q=2 is just below the threshold: a mature item still collapses to a
        # relearn (reps -> 0, interval -> 1), confirming the boundary is q>=3.
        ease, interval, reps = srs.update(2.5, 30, 5, srs.PASSING_GRADE - 1)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)

    def test_passing_grade_advances_the_success_ladder(self):
        # A passing grade at repetitions==1 grows the interval past 1 day.
        ease, interval, reps = srs.update(2.5, 1, 1, srs.PASSING_GRADE)
        self.assertGreater(interval, 1)
        self.assertEqual(reps, 2)

    def test_lapse_from_reps_one_resets_not_advances(self):
        # A lapse at the reps==1 boundary must reset (interval 1, reps 0), never
        # grow the interval — the pass/lapse branch wins over the repetitions
        # branch.
        ease, interval, reps = srs.update(2.5, 6, 1, srs.PASSING_GRADE - 1)
        self.assertEqual(interval, 1)
        self.assertEqual(reps, 0)


class EarlyReviewTests(SimpleTestCase):
    """An item reviewed before it's due: passes don't advance it, lapses reset it."""

    def test_early_pass_leaves_state_unchanged(self):
        for quality in (srs.PASSING_GRADE, 5):
            self.assertEqual(srs.update(2.6, 3, 2, quality, early=True), (2.6, 3, 2))

    def test_early_lapse_still_resets(self):
        self.assertEqual(
            srs.update(2.6, 8, 3, 1, early=True), srs.update(2.6, 8, 3, 1),
        )
        ease, interval, reps = srs.update(2.6, 8, 3, 1, early=True)
        self.assertEqual((interval, reps), (1, 0))


F, S, X = "correct_first", "correct_second", "incorrect"


class DayQualityTests(SimpleTestCase):
    """The day's accuracy picks the quality, like Anki's answer buttons."""

    def test_accuracy_credits_second_tries_half(self):
        self.assertEqual(srs.accuracy([F, S, X, F]), 0.625)
        self.assertEqual(srs.accuracy([]), 0.0)

    def test_tier_boundaries(self):
        cases = [(1.0, 5), (0.9, 5), (0.89, 4), (0.75, 4), (0.74, 3), (0.6, 3),
                 (0.59, 2), (0.4, 2), (0.39, 1), (0.2, 1), (0.19, 0), (0.0, 0)]
        for day_accuracy, quality in cases:
            self.assertEqual(srs.day_quality(day_accuracy), quality, day_accuracy)


class GradeDayTests(SimpleTestCase):
    """One day's answers on a topic -> the next SM-2 state."""

    def test_clean_day_is_a_normal_pass_with_ease_up(self):
        ease, interval, reps, quality = srs.grade_day(2.5, 3, 2, [F, F])
        self.assertEqual((interval, reps, quality), (8, 3, 5))
        self.assertAlmostEqual(ease, 2.6)

    def test_one_slip_in_four_keeps_ease_and_passes(self):
        ease, interval, reps, quality = srs.grade_day(2.5, 3, 2, [F, X, F, F])
        self.assertEqual((interval, reps, quality), (8, 3, 4))
        self.assertAlmostEqual(ease, 2.5)

    def test_hard_pass_barely_stretches_the_interval(self):
        # 2 of 3 right is 67%: a pass, but the interval grows 1.2x, not by ease.
        ease, interval, reps, quality = srs.grade_day(2.5, 10, 3, [F, X, F])
        self.assertEqual((interval, reps, quality), (12, 4, 3))
        self.assertAlmostEqual(ease, 2.36)

    def test_hard_pass_still_grows_a_short_interval_by_a_day(self):
        _, interval, _, _ = srs.grade_day(2.5, 1, 1, [F, X, F])
        self.assertEqual(interval, 2)

    def test_mostly_wrong_day_lapses(self):
        ease, interval, reps, quality = srs.grade_day(2.5, 10, 3, [F, X, X])
        self.assertEqual((interval, reps, quality), (1, 0, 1))
        self.assertAlmostEqual(ease, 1.96)

    def test_learning_day_judges_only_the_last_answers(self):
        # A new topic: early misses while working it out don't count.
        outcomes = [X, X, X, X] + [F] * srs.LEARNING_TAIL
        ease, interval, reps, quality = srs.grade_day(2.5, 0, 0, outcomes)
        self.assertEqual((interval, reps, quality), (1, 1, 5))
        self.assertGreater(ease, 2.5)

    def test_learning_day_ending_wrong_still_lapses(self):
        _, interval, reps, quality = srs.grade_day(2.5, 0, 0, [F, F, F, X, X, X, X, X])
        self.assertEqual((interval, reps), (1, 0))
        self.assertLess(quality, srs.PASSING_GRADE)

    def test_review_day_judges_every_answer(self):
        # Not a learning day: the early misses do count.
        _, interval, reps, _ = srs.grade_day(2.5, 10, 3, [X, X, X, X] + [F] * 5)
        self.assertEqual((interval, reps), (1, 0))

    def test_volume_scales_ease_recovery_up_to_three_times(self):
        base = srs.update_ease(1.5, 5) - 1.5  # one clean day's gain: +0.1
        few = srs.grade_day(1.5, 3, 2, [F] * 4)[0] - 1.5
        many = srs.grade_day(1.5, 3, 2, [F] * 8)[0] - 1.5
        lots = srs.grade_day(1.5, 3, 2, [F] * 40)[0] - 1.5
        self.assertAlmostEqual(few, base)
        self.assertAlmostEqual(many, 2 * base)
        self.assertAlmostEqual(lots, srs.MAX_RECOVERY * base)

    def test_ease_losses_are_not_scaled_by_volume(self):
        one = srs.grade_day(2.5, 10, 3, [X])[0]
        many = srs.grade_day(2.5, 10, 3, [X] * 20)[0]
        self.assertEqual(one, many)

    def test_early_pass_leaves_state_unchanged(self):
        self.assertEqual(srs.grade_day(2.6, 3, 2, [F, F], early=True), (2.6, 3, 2, 5))

    def test_early_lapse_still_resets(self):
        _, interval, reps, _ = srs.grade_day(2.6, 8, 3, [X, X], early=True)
        self.assertEqual((interval, reps), (1, 0))
