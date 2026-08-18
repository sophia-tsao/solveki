"""Math-correctness tests for the arithmetic generators.

Each test parses the generated problem statement with a regex, independently
recomputes the expected answer, and asserts the generator's stated solution
matches. Run over many random samples so the check covers the whole input
space, not a single lucky draw.
"""
import random
import re
from decimal import Decimal
from fractions import Fraction

from django.test import TestCase

# Import the module first to trigger @register side effects, then pull the
# populated registry.
from myapp.generators import arithmetic  # noqa: F401
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000


class PlaceValueTests(TestCase):
    PROBLEM = re.compile(
        r"value of the digit (?P<digit>\d) in the number (?P<number>\d+)"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_place_value(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_place_value"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            digit = m.group("digit")
            number = m.group("number")
            idx = number.index(digit)
            place = 10 ** (len(number) - 1 - idx)
            expected = int(digit) * place
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class RoundingTests(TestCase):
    PROBLEM = re.compile(
        r"Round (?P<n>\d+) to the nearest (?P<place>ten|hundred|thousand)"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_rounding(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_rounding"]
        places = {"ten": 10, "hundred": 100, "thousand": 1000}
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            n = int(m.group("n"))
            p = places[m.group("place")]
            expected = ((n + p // 2) // p) * p
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class AddFractionsTests(TestCase):
    PROBLEM = re.compile(
        r"\\frac\{(?P<a>\d+)\}\{(?P<b>\d+)\} \+ \\frac\{(?P<c>\d+)\}\{(?P<d>\d+)\}"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+(?:/\d+)?)\$")

    def test_add_fractions(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_add_fractions"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = (
                Fraction(int(m.group("a")), int(m.group("b")))
                + Fraction(int(m.group("c")), int(m.group("d")))
            )
            stated = Fraction(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class SubtractFractionsTests(TestCase):
    PROBLEM = re.compile(
        r"\\frac\{(?P<a>\d+)\}\{(?P<b>\d+)\} - \\frac\{(?P<c>\d+)\}\{(?P<d>\d+)\}"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+(?:/\d+)?)\$")

    def test_subtract_fractions(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_subtract_fractions"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = (
                Fraction(int(m.group("a")), int(m.group("b")))
                - Fraction(int(m.group("c")), int(m.group("d")))
            )
            self.assertGreaterEqual(expected, 0, f"negative result: {problem!r}")
            stated = Fraction(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class CompareDecimalsTests(TestCase):
    PROBLEM = re.compile(
        r"Which is greater: \$(?P<x>[\d.]+)\$ or \$(?P<y>[\d.]+)\$"
    )
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_compare_decimals(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_compare_decimals"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            x = Decimal(m.group("x"))
            y = Decimal(m.group("y"))
            self.assertNotEqual(x, y, f"equal decimals: {problem!r}")
            expected = max(x, y)
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class AddDecimalsTests(TestCase):
    PROBLEM = re.compile(r"Calculate \$(?P<x>[\d.]+) \+ (?P<y>[\d.]+)\$")
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_add_decimals(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_add_decimals"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = Decimal(m.group("x")) + Decimal(m.group("y"))
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class SubtractDecimalsTests(TestCase):
    PROBLEM = re.compile(r"Calculate \$(?P<x>[\d.]+) - (?P<y>[\d.]+)\$")
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_subtract_decimals(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_subtract_decimals"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = Decimal(m.group("x")) - Decimal(m.group("y"))
            self.assertGreaterEqual(expected, 0, f"negative: {problem!r}")
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class MultiplyDecimalsTests(TestCase):
    PROBLEM = re.compile(r"Calculate \$(?P<x>[\d.]+) \\times (?P<y>[\d.]+)\$")
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_multiply_decimals(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_multiply_decimals"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = Decimal(m.group("x")) * Decimal(m.group("y"))
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class OrderOfOperationsTests(TestCase):
    PROBLEM = re.compile(r"Evaluate \$(?P<expr>.+?)\$")
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_order_of_operations(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_order_of_operations"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expr = m.group("expr").replace("\\times", "*")
            expected = eval(expr, {"__builtins__": {}}, {})
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class NthMultipleTests(TestCase):
    PROBLEM = re.compile(
        r"What is the (?P<n>\d+)(?:st|nd|rd|th) multiple of (?P<base>\d+)"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_nth_multiple(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_nth_multiple"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = int(m.group("n")) * int(m.group("base"))
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class PowersOfTenTests(TestCase):
    PROBLEM = re.compile(
        r"Calculate \$(?P<n>\d+) \\(?P<op>times|div) 10\^\{(?P<k>\d+)\}\$"
    )
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_powers_of_ten(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_powers_of_ten"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            n = Decimal(m.group("n"))
            p = Decimal(10 ** int(m.group("k")))
            expected = n * p if m.group("op") == "times" else n / p
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class LengthConversionTests(TestCase):
    PROBLEM = re.compile(
        r"Convert (?P<v>\d+) (?P<from>\w+) to (?P<to>\w+)\."
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")
    FACTORS = {
        "km": 100000, "m": 100, "cm": 1,
        "yd": 36, "ft": 12, "in": 1,
    }

    def test_length_conversion(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_length_conversion"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            value = int(m.group("v"))
            f_from = self.FACTORS[m.group("from")]
            f_to = self.FACTORS[m.group("to")]
            self.assertEqual((value * f_from) % f_to, 0,
                             f"non-integer conversion: {problem!r}")
            expected = value * f_from // f_to
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class ElapsedTimeTests(TestCase):
    PROBLEM = re.compile(
        r"departs at (?P<h>\d+):(?P<m>\d{2}) and travels for (?P<dur>\d+) minutes"
    )
    SOLUTION = re.compile(r"\$(?P<h>\d+):(?P<m>\d{2})\$")

    def test_elapsed_time(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_elapsed_time"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            total = (int(m.group("h")) * 60 + int(m.group("m"))
                     + int(m.group("dur"))) % (24 * 60)
            eh, em = divmod(total, 60)
            sm = self.SOLUTION.search(solution)
            self.assertEqual((int(sm.group("h")), int(sm.group("m"))), (eh, em),
                             f"{problem!r} -> {solution!r}")


class MoneyTests(TestCase):
    PROBLEM = re.compile(
        r"in dollars: \$(?P<a>[\d.]+) (?P<op>[+-]) (?P<b>[\d.]+)\$"
    )
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_money(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_money"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = Decimal(m.group("a"))
            b = Decimal(m.group("b"))
            expected = a + b if m.group("op") == "+" else a - b
            self.assertGreaterEqual(expected, 0, f"negative money: {problem!r}")
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class AreaOfRectangleTests(TestCase):
    PROBLEM = re.compile(
        r"length (?P<l>\d+) units and width (?P<w>\d+) units"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_area_of_rectangle(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_area_of_rectangle"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = int(m.group("l")) * int(m.group("w"))
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class MinutesToHoursTests(TestCase):
    PROBLEM = re.compile(r"Convert (?P<total>\d+) minutes")
    SOLUTION = re.compile(r"(?P<h>\d+) hr (?P<m>\d+) min")

    def test_conversion(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_minutes_to_hours"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            total = int(m.group("total"))
            s = self.SOLUTION.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            h, mm = int(s.group("h")), int(s.group("m"))
            self.assertEqual(h * 60 + mm, total, f"{problem!r} -> {solution!r}")
            self.assertGreaterEqual(h, 1, f"should have an hours part: {solution!r}")
            self.assertTrue(0 <= mm < 60, f"minutes out of range: {solution!r}")


class ElapsedTimeTests(TestCase):
    PROBLEM = re.compile(r"starts at (?P<h>\d+):(?P<m>\d{2}) and lasts (?P<dur>\d+) minutes")
    SOLUTION = re.compile(r"\$(?P<eh>\d+):(?P<em>\d{2})\$")

    def test_arrival_time(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_elapsed_time"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            h, mm, dur = int(m.group("h")), int(m.group("m")), int(m.group("dur"))
            total = h * 60 + mm + dur
            s = self.SOLUTION.search(solution)
            eh, em = int(s.group("eh")), int(s.group("em"))
            self.assertEqual(eh * 60 + em, total, f"{problem!r} -> {solution!r}")
            # Grade-2 friendly: small starting hour and duration, no 12-hour wrap.
            self.assertTrue(1 <= h <= 9, f"start hour too large: {problem!r}")
            self.assertTrue(5 <= dur <= 55, f"duration out of range: {problem!r}")
            self.assertLessEqual(eh, 11, f"arrival wraps past 12: {solution!r}")


class CompareNumbersTests(TestCase):
    PROBLEM = re.compile(
        r">, <, or =: \$(?P<a>\d+) \\,\\square\\, (?P<b>\d+)\$"
    )

    def test_compare_numbers(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_compare_numbers"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b = int(m.group("a")), int(m.group("b"))
            expected = ">" if a > b else "<" if a < b else "="
            self.assertEqual(solution, expected, f"{problem!r} -> {solution!r}")


class MissingNumberSequenceTests(TestCase):
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_missing_number_sequence(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_missing_number_sequence"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            body = problem.split(":", 1)[1].strip().rstrip(".")
            tokens = [t.strip() for t in body.split(",")]
            idx = tokens.index("?")
            # Interior blank -> average of its two numeric neighbours.
            left = int(tokens[idx - 1])
            right = int(tokens[idx + 1])
            self.assertEqual((left + right) % 2, 0, f"non-integer: {problem!r}")
            expected = (left + right) // 2
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class EvenOrOddTests(TestCase):
    PROBLEM = re.compile(r"Is \$(?P<n>\d+)\$ even or odd")

    def test_even_or_odd(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_even_or_odd"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = "even" if int(m.group("n")) % 2 == 0 else "odd"
            self.assertEqual(solution, expected, f"{problem!r} -> {solution!r}")


class OrdinalNumberTests(TestCase):
    PROBLEM = re.compile(r"ordinal number for \$(?P<n>\d+)\$")

    def _ordinal(self, n):
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def test_ordinal_number(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_ordinal_number"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = self._ordinal(int(m.group("n")))
            self.assertEqual(solution, expected, f"{problem!r} -> {solution!r}")


class WordProblemWithin20Tests(TestCase):
    ADD = re.compile(r"(?P<a>\d+) red apples and (?P<b>\d+) green apples")
    SUB = re.compile(r"(?P<a>\d+) ducks in a pond. (?P<b>\d+) ducks swim away")
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_word_problem_within_20(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_word_problem_within_20"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            add = self.ADD.search(problem)
            sub = self.SUB.search(problem)
            self.assertTrue(add or sub, f"could not parse: {problem!r}")
            if add:
                expected = int(add.group("a")) + int(add.group("b"))
            else:
                expected = int(sub.group("a")) - int(sub.group("b"))
            self.assertTrue(0 <= expected <= 20, f"out of range: {problem!r}")
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class AddSubtractWithin1000Tests(TestCase):
    PROBLEM = re.compile(r"Calculate \$(?P<a>\d+) (?P<op>[+-]) (?P<b>\d+)\$")
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_add_subtract_within_1000(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_add_subtract_within_1000"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b = int(m.group("a")), int(m.group("b"))
            expected = a + b if m.group("op") == "+" else a - b
            self.assertTrue(0 <= expected <= 1000, f"out of range: {problem!r}")
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class TellTimeFiveMinTests(TestCase):
    PROBLEM = re.compile(r"'(?P<m>\d+) minutes past (?P<h>\d+) o'clock'")
    SOLUTION = re.compile(r"\$(?P<h>\d+):(?P<m>\d{2})\$")

    def test_tell_time_five_min(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_tell_time_five_min"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            h, mins = int(m.group("h")), int(m.group("m"))
            self.assertEqual(mins % 5, 0, f"not multiple of 5: {problem!r}")
            s = self.SOLUTION.search(solution)
            self.assertEqual((int(s.group("h")), int(s.group("m"))), (h, mins),
                             f"{problem!r} -> {solution!r}")


class CountMoneyValueTests(TestCase):
    PROBLEM = re.compile(
        r"(?P<q>\d+) quarters, (?P<d>\d+) dimes, (?P<n>\d+) nickels, "
        r"and (?P<p>\d+) pennies"
    )
    SOLUTION = re.compile(r"\$(?P<d>\d+)\.(?P<c>\d{2})")

    def test_count_money_value(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_count_money_value"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            cents = (int(m.group("q")) * 25 + int(m.group("d")) * 10
                     + int(m.group("n")) * 5 + int(m.group("p")))
            s = self.SOLUTION.search(solution)
            stated = int(s.group("d")) * 100 + int(s.group("c"))
            self.assertEqual(stated, cents, f"{problem!r} -> {solution!r}")


class ArrayRepeatedAdditionTests(TestCase):
    PROBLEM = re.compile(
        r"(?P<r>\d+) rows with (?P<c>\d+) dots in each row"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_array_repeated_addition(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_array_repeated_addition"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = int(m.group("r")) * int(m.group("c"))
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class CompareThreeDigitTests(TestCase):
    PROBLEM = re.compile(
        r">, <, or =: \$(?P<a>\d{3}) \\,\\square\\, (?P<b>\d{3})\$"
    )

    def test_compare_three_digit(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_compare_three_digit"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b = int(m.group("a")), int(m.group("b"))
            expected = ">" if a > b else "<" if a < b else "="
            self.assertEqual(solution, expected, f"{problem!r} -> {solution!r}")


class EquivalentFractionTests(TestCase):
    PROBLEM = re.compile(
        r"\\frac\{(?P<a>\d+)\}\{(?P<b>\d+)\} = "
        r"\\frac\{\\square\}\{(?P<d>\d+)\}"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_equivalent_fraction(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_equivalent_fraction"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b, d = int(m.group("a")), int(m.group("b")), int(m.group("d"))
            self.assertEqual((a * d) % b, 0, f"non-integer: {problem!r}")
            expected = a * d // b
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class MissingFactorTests(TestCase):
    PROBLEM = re.compile(
        r"\$(?P<a>\d+) \\times \\square = (?P<c>\d+)\$"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_missing_factor(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_missing_factor"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, c = int(m.group("a")), int(m.group("c"))
            self.assertEqual(c % a, 0, f"non-integer: {problem!r}")
            expected = c // a
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class FractionOnNumberLineTests(TestCase):
    PROBLEM = re.compile(
        r"divided into (?P<b>\d+) equal parts. What fraction does the "
        r"(?P<a>\d+)(?:st|nd|rd|th) tick mark"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+(?:/\d+)?)\$")

    def test_fraction_on_number_line(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_fraction_on_number_line"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = Fraction(int(m.group("a")), int(m.group("b")))
            stated = Fraction(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class TwoStepWordProblemTests(TestCase):
    PROBLEM = re.compile(
        r"had (?P<start>\d+) apples. It received (?P<crates>\d+) crates with "
        r"(?P<per>\d+) apples in each crate"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_two_step_word_problem(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_two_step_word_problem"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = (int(m.group("start"))
                        + int(m.group("crates")) * int(m.group("per")))
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class FractionTimesWholeTests(TestCase):
    PROBLEM = re.compile(
        r"\$(?P<k>\d+) \\times \\frac\{(?P<a>\d+)\}\{(?P<b>\d+)\}\$"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+(?:/\d+)?)\$")

    def test_fraction_times_whole(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_fraction_times_whole"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = (int(m.group("k"))
                        * Fraction(int(m.group("a")), int(m.group("b"))))
            stated = Fraction(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class MixedToImproperTests(TestCase):
    PROBLEM = re.compile(
        r"mixed number (?P<a>\d+) (?P<b>\d+)/(?P<c>\d+) to an improper"
    )
    SOLUTION = re.compile(r"\$(?P<p>\d+)/(?P<q>\d+)\$")

    def test_mixed_to_improper(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_mixed_to_improper"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b, c = int(m.group("a")), int(m.group("b")), int(m.group("c"))
            self.assertTrue(0 < b < c, f"bad fraction part: {problem!r}")
            expected_p = a * c + b
            s = self.SOLUTION.search(solution)
            self.assertEqual((int(s.group("p")), int(s.group("q"))),
                             (expected_p, c), f"{problem!r} -> {solution!r}")


class LongDivisionRemainderTests(TestCase):
    PROBLEM = re.compile(r"\$(?P<a>\d+) \\div (?P<b>\d+)\$")
    SOLUTION = re.compile(r"\$(?P<q>\d+) R (?P<r>\d+)\$")

    def test_long_division_remainder(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_long_division_remainder"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b = int(m.group("a")), int(m.group("b"))
            eq, er = divmod(a, b)
            s = self.SOLUTION.search(solution)
            self.assertEqual((int(s.group("q")), int(s.group("r"))), (eq, er),
                             f"{problem!r} -> {solution!r}")
            self.assertLess(er, b, f"remainder too large: {solution!r}")


class AngleAdditionTests(TestCase):
    PROBLEM = re.compile(
        r"angle ABC = (?P<total>\d+) degrees and angle ABD = (?P<known>\d+)"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_angle_addition(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_angle_addition"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = int(m.group("total")) - int(m.group("known"))
            self.assertGreater(expected, 0, f"non-positive angle: {problem!r}")
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class FactorPairsCountTests(TestCase):
    PROBLEM = re.compile(r"factor pairs does \$(?P<n>\d+)\$ have")
    SOLUTION = re.compile(r"\$(?P<v>\d+)\$")

    def test_factor_pairs_count(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_factor_pairs_count"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            n = int(m.group("n"))
            divisors = sum(1 for k in range(1, n + 1) if n % k == 0)
            expected = (divisors + 1) // 2
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class AddUnlikeFractionsTests(TestCase):
    PROBLEM = re.compile(
        r"\\frac\{(?P<a>\d+)\}\{(?P<b>\d+)\} (?P<op>[+-]) "
        r"\\frac\{(?P<c>\d+)\}\{(?P<d>\d+)\}"
    )
    SOLUTION = re.compile(r"\$(?P<v>\d+(?:/\d+)?)\$")

    def test_add_unlike_fractions(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_add_unlike_fractions"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            b, d = int(m.group("b")), int(m.group("d"))
            self.assertNotEqual(b, d, f"like denominators: {problem!r}")
            left = Fraction(int(m.group("a")), b)
            right = Fraction(int(m.group("c")), d)
            expected = left + right if m.group("op") == "+" else left - right
            self.assertGreaterEqual(expected, 0, f"negative: {problem!r}")
            stated = Fraction(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class RoundDecimalTests(TestCase):
    PROBLEM = re.compile(
        r"Round \$(?P<x>[\d.]+)\$ to the nearest (?P<place>tenth|hundredth)"
    )
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_round_decimal(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_round_decimal"]
        quants = {"tenth": Decimal("0.1"), "hundredth": Decimal("0.01")}
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            from decimal import ROUND_HALF_UP
            expected = Decimal(m.group("x")).quantize(
                quants[m.group("place")], rounding=ROUND_HALF_UP)
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class MetricUnitConversionTests(TestCase):
    PROBLEM = re.compile(
        r"Convert (?P<v>\d+) (?P<from>\w+) to (?P<to>\w+)\."
    )
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")
    MULTIPLIERS = {
        ("kg", "g"): Decimal("1000"), ("g", "kg"): Decimal("0.001"),
        ("L", "mL"): Decimal("1000"), ("mL", "L"): Decimal("0.001"),
        ("km", "m"): Decimal("1000"), ("m", "km"): Decimal("0.001"),
        ("m", "cm"): Decimal("100"), ("cm", "m"): Decimal("0.01"),
    }

    def test_metric_unit_conversion(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_metric_unit_conversion"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            mult = self.MULTIPLIERS[(m.group("from"), m.group("to"))]
            expected = Decimal(m.group("v")) * mult
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class DivideDecimalsTests(TestCase):
    PROBLEM = re.compile(r"Calculate \$(?P<a>[\d.]+) \\div (?P<b>\d+)\$")
    SOLUTION = re.compile(r"\$(?P<v>[\d.]+)\$")

    def test_divide_decimals(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["arith_divide_decimals"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            expected = Decimal(m.group("a")) / Decimal(m.group("b"))
            stated = Decimal(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")
