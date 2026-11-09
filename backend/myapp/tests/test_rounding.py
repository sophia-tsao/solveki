"""Round once, at the end, and accept a truncated answer as well as a rounded one.

`num` rounds half up for display; inside `track_rounding` it also records the
truncated form of every value it rounds, and `_make_problem_for_topic` turns
those into the card's accepted `alternatives`.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators._format import num, track_rounding, truncations
from myapp.views.problems import _make_problem_for_topic, _truncated_alternatives


class _Topic:
    id = 1

    def __init__(self, generator_name):
        self.generator_name = generator_name


class TrackRoundingTests(SimpleTestCase):
    def test_records_the_truncated_form_of_a_rounded_value(self):
        with track_rounding() as record:
            self.assertEqual(num(Fraction(8, 3)), "2.667")
            self.assertEqual(num(-2 / 3), "-0.667")
            self.assertEqual(num(math.sqrt(50), 1), "7.1")
        self.assertEqual(truncations(record), {"2.667": "2.666", "0.667": "0.666", "7.1": "7"})

    def test_exact_and_rounded_down_values_need_no_alternative(self):
        with track_rounding() as record:
            num(Fraction(3, 2))
            num(Fraction(1, 3))  # 0.333 either way
        self.assertEqual(truncations(record), {})

    def test_float_noise_is_not_truncated(self):
        # sin(30 deg) is 0.49999999999999994 as a float; it is 0.5, not 0.499...
        with track_rounding() as record:
            self.assertEqual(num(math.sin(math.radians(30))), "0.5")
            self.assertEqual(num(0.1 * 3), "0.3")
        self.assertEqual(truncations(record), {})

    def test_text_from_two_different_values_is_ambiguous(self):
        with track_rounding() as record:
            num(Fraction(8, 3))  # 2.666...
            num(2.6671)
        self.assertEqual(truncations(record), {})

    def test_showing_a_rounded_value_again_keeps_its_truncation(self):
        with track_rounding() as record:
            num(Fraction(num(Fraction(8, 3))))
        self.assertEqual(truncations(record), {"2.667": "2.666"})

    def test_nothing_is_recorded_outside_the_block(self):
        with track_rounding() as record:
            pass
        num(Fraction(8, 3))
        self.assertEqual(record, {})


class TruncatedAlternativesTests(SimpleTestCase):
    def test_every_combination_of_rounded_or_truncated(self):
        self.assertEqual(
            _truncated_alternatives("(1.667, -2.667)", {"1.667": "1.666", "2.667": "2.666"}),
            ["(1.667, -2.666)", "(1.666, -2.667)", "(1.666, -2.666)"],
        )

    def test_numbers_without_a_truncation_are_kept(self):
        self.assertEqual(_truncated_alternatives("1.616*10^-7", {"1.616": "1.615"}), ["1.615*10^-7"])
        self.assertEqual(_truncated_alternatives("y = 2x + 1", {}), [])


class ServedAlternativesTests(SimpleTestCase):
    """Every generator's alternatives really are its answers, truncated."""

    SAMPLES = 40

    def test_alternatives_differ_from_the_solution_only_by_truncation(self):
        random.seed(0)
        failures = []
        for name in LOCAL_GENERATORS:
            for _ in range(self.SAMPLES):
                made = _make_problem_for_topic(_Topic(name))
                for alt in made["alternatives"]:
                    if alt == made["solution"] or not self._is_truncation(made["solution"], alt):
                        failures.append(f"{name}: {alt!r} for {made['solution']!r}")
                        break
        self.assertEqual(failures, [])

    @staticmethod
    def _is_truncation(solution, alt):
        """Whether `alt` is `solution` with some numbers one unit lower in their last place."""
        number = re.compile(r"\d+(?:\.\d+)?")
        if number.split(solution) != number.split(alt):
            return False
        for s, a in zip(number.findall(solution), number.findall(alt)):
            if s == a:
                continue
            places = len(s.split(".")[1]) if "." in s else 0
            unit = Fraction(1, 10 ** places)
            # "3" from 2.9996 truncates to "2.999": below by at most one unit.
            if not 0 < Fraction(s) - Fraction(a) <= unit:
                return False
        return True
