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
