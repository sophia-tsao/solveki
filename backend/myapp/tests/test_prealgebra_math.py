"""Math-correctness tests for the pre-algebra generators.

Each test parses the generated problem, recomputes the expected answer
independently, and asserts the generator's stated solution matches. Every
generator is exercised over 2000 random samples under a fixed seed.
"""
import math
import re
from fractions import Fraction

from django.test import TestCase

from myapp.generators import prealgebra  # noqa: F401 - registers pre_* gens
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000

# Inequality relation tokens and their reversal. Problems render LaTeX
# (``\leq``/``\geq``); solutions use typeable ASCII (``<=``/``>=``).
FLIP = {"<": ">", ">": "<", "\\leq": "\\geq", "\\geq": "\\leq"}
OP_RE = r"(?:<|>|\\leq|\\geq)"          # relation as it appears in the problem
ASCII_OF = {"<": "<", ">": ">", "\\leq": "<=", "\\geq": ">="}
SOL_OP_RE = r"(?:<=|>=|<|>)"            # relation as it appears in the solution


def parse_frac_solution(solution):
    """Parse a typeable ``$p/q$`` or ``$n$`` solution into a ``Fraction``."""
    m = re.search(r"\$(-?\d+)/(-?\d+)\$", solution)
    if m:
        return Fraction(int(m.group(1)), int(m.group(2)))
    m = re.search(r"\$(-?\d+)\$", solution)
    return Fraction(int(m.group(1)))


# Polynomial term: optional sign, optional magnitude, optional x / x^n.
_TERM = re.compile(r"([+-]?)(\d*)x\^(\d+)|([+-]?)(\d*)x(?!\^)|([+-]?\d+)(?!x)")


def parse_poly(poly):
    terms = []
    for m in _TERM.finditer(poly):
        if m.group(3) is not None:
            sign = -1 if m.group(1) == "-" else 1
            mag = int(m.group(2)) if m.group(2) else 1
            terms.append((sign * mag, int(m.group(3))))
        elif m.group(0).endswith("x"):
            sign = -1 if m.group(4) == "-" else 1
            mag = int(m.group(5)) if m.group(5) else 1
            terms.append((sign * mag, 1))
        elif m.group(6):
            terms.append((int(m.group(6)), 0))
    return terms


def normalize_sci(fr):
    """Same convention as the generator: mantissa in [1,10), 3 dp; int exp."""
    ten = Fraction(10)
    x = fr
    exp = 0
    while x >= ten:
        x /= ten
        exp += 1
    while x < 1:
        x *= ten
        exp -= 1
    return round(float(x), 3), exp


class UnitRateTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_unit_rate"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"travels \$(\d+)\$ miles in \$(\d+)\$ hours", problem)
            d, t = int(m.group(1)), int(m.group(2))
            self.assertEqual(d % t, 0)
            self.assertEqual(int(re.search(r"\$(-?\d+)\$", solution).group(1)), d // t)


class EquivalentRatioTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_equivalent_ratio"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"\$(\d+):(\d+) = (\d+):\\square\$", problem)
            a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
            d = int(re.search(r"\$(\d+)\$", solution).group(1))
            # a/b == c/d
            self.assertEqual(a * d, b * c)


class SolveProportionTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_solve_proportion"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"\\frac\{(\d+)\}\{(\d+)\} = \\frac\{x\}\{(\d+)\}", problem)
            a, b, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            x = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(a * d, b * x)


class IntegerOperationsTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_integer_operations"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"\((-?\d+)\) (\+|-|\\times|\\div) \((-?\d+)\)", problem)
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            if op == "+":
                expected = a + b
            elif op == "-":
                expected = a - b
            elif op == "\\times":
                expected = a * b
            else:
                self.assertEqual(a % b, 0)
                expected = a // b
            result = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(result, expected)


class RationalOperationsTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_rational_operations"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"\\frac\{(-?\d+)\}\{(\d+)\} (\+|-|\\times|\\div) "
                r"\\frac\{(-?\d+)\}\{(\d+)\}",
                problem,
            )
            f1 = Fraction(int(m.group(1)), int(m.group(2)))
            f2 = Fraction(int(m.group(4)), int(m.group(5)))
            op = m.group(3)
            if op == "+":
                expected = f1 + f2
            elif op == "-":
                expected = f1 - f2
            elif op == "\\times":
                expected = f1 * f2
            else:
                expected = f1 / f2
            self.assertEqual(parse_frac_solution(solution), expected)


class AbsoluteValueTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_absolute_value"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            result = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            m = re.search(r"\|(-?\d+) - (-?\d+)\|", problem)
            if m:
                expected = abs(int(m.group(1)) - int(m.group(2)))
            else:
                m2 = re.search(r"\|(-?\d+)\| \+ \|(-?\d+)\|", problem)
                expected = abs(int(m2.group(1))) + abs(int(m2.group(2)))
            self.assertEqual(result, expected)


class OneStepInequalityTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_one_step_inequality"]
        sol_re = re.compile(rf"x ({SOL_OP_RE}) (-?\d+)")
        for _ in range(SAMPLES):
            problem, solution = gen()
            sm = sol_re.search(solution)
            sol_op, sol_c = sm.group(1), int(sm.group(2))

            add = re.search(rf"x ([+-]) (\d+) ({OP_RE}) (-?\d+)", problem)
            mul = re.search(rf"(-?\d+)x ({OP_RE}) (-?\d+)", problem)
            if add:
                a = int(add.group(2)) * (1 if add.group(1) == "+" else -1)
                op = add.group(3)
                b = int(add.group(4))
                self.assertEqual(sol_op, ASCII_OF[op])
                self.assertEqual(sol_c, b - a)
            else:
                k = int(mul.group(1))
                op = mul.group(2)
                b = int(mul.group(3))
                self.assertEqual(b % k, 0)
                expected_op = FLIP[op] if k < 0 else op
                self.assertEqual(sol_op, ASCII_OF[expected_op])
                self.assertEqual(sol_c, b // k)


class MultiStepInequalityTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_multi_step_inequality"]
        sol_re = re.compile(rf"x ({SOL_OP_RE}) (-?\d+)")
        prob_re = re.compile(rf"(-?\d+)x ([+-]) (\d+) ({OP_RE}) (-?\d+)")
        for _ in range(SAMPLES):
            problem, solution = gen()
            sm = sol_re.search(solution)
            sol_op, sol_c = sm.group(1), int(sm.group(2))
            pm = prob_re.search(problem)
            a = int(pm.group(1))
            b = int(pm.group(3)) * (1 if pm.group(2) == "+" else -1)
            op = pm.group(4)
            c = int(pm.group(5))
            self.assertEqual((c - b) % a, 0)
            expected_op = FLIP[op] if a < 0 else op
            self.assertEqual(sol_op, ASCII_OF[expected_op])
            self.assertEqual(sol_c, (c - b) // a)


class ScientificNotationTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_scientific_notation_ops"]
        ten = Fraction(10)
        prob_re = re.compile(
            r"(\d+\.\d) \\times 10\^\{(-?\d+)\} (\+|-|\\div) "
            r"(\d+\.\d) \\times 10\^\{(-?\d+)\}"
        )
        sol_re = re.compile(r"\$([\d.]+)\*10\^(-?\d+)\$")
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = prob_re.search(problem)
            m1 = Fraction(pm.group(1))
            e1 = int(pm.group(2))
            op = pm.group(3)
            m2 = Fraction(pm.group(4))
            e2 = int(pm.group(5))
            f1 = m1 * (ten ** e1)
            f2 = m2 * (ten ** e2)
            if op == "+":
                value = f1 + f2
            elif op == "-":
                value = f1 - f2
            else:
                value = f1 / f2
            mant, exp = normalize_sci(value)
            sm = sol_re.search(solution)
            self.assertAlmostEqual(float(sm.group(1)), mant, places=3)
            self.assertEqual(int(sm.group(2)), exp)


class IntegerExponentRulesTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_integer_exponent_rules"]
        sol_re = re.compile(r"\$(\d+)\^(-?\d+)\$")
        for _ in range(SAMPLES):
            problem, solution = gen()
            sm = sol_re.search(solution)
            base, r = int(sm.group(1)), int(sm.group(2))
            mult = re.search(r"(\d+)\^\{(-?\d+)\} \\times (\d+)\^\{(-?\d+)\}", problem)
            div = re.search(r"(\d+)\^\{(-?\d+)\} \\div (\d+)\^\{(-?\d+)\}", problem)
            power = re.search(r"\((\d+)\^\{(-?\d+)\}\)\^\{(-?\d+)\}", problem)
            if mult:
                self.assertEqual(int(mult.group(1)), base)
                self.assertEqual(int(mult.group(3)), base)
                self.assertEqual(r, int(mult.group(2)) + int(mult.group(4)))
            elif div:
                self.assertEqual(r, int(div.group(2)) - int(div.group(4)))
            else:
                self.assertEqual(r, int(power.group(2)) * int(power.group(3)))


class ConstantOfProportionalityTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_constant_of_proportionality"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"When \$x = (-?\d+)\$, \$y = (-?\d+)\$", problem)
            x, y = int(m.group(1)), int(m.group(2))
            k = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(k * x, y)


class EvaluateFunctionTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_evaluate_function"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"f\(x\)=(.+?)\$, evaluate \$f\((-?\d+)\)", problem)
            terms = parse_poly(m.group(1))
            v = int(m.group(2))
            expected = sum(coeff * (v ** exp) for coeff, exp in terms)
            result = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(result, expected)


class SlopeFromTwoPointsTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_slope_from_two_points"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"\$\((-?\d+), (-?\d+)\)\$ and \$\((-?\d+), (-?\d+)\)\$", problem
            )
            x1, y1, x2, y2 = (int(m.group(i)) for i in range(1, 5))
            self.assertNotEqual(x1, x2)
            expected = Fraction(y2 - y1, x2 - x1)
            self.assertEqual(parse_frac_solution(solution), expected)


class LinearFunctionValueTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_linear_function_value"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"slope \$m = (-?\d+)\$ and y-intercept \$b = (-?\d+)\$\. "
                r"Find \$y\$ when \$x = (-?\d+)\$",
                problem,
            )
            mm, b, x = int(m.group(1)), int(m.group(2)), int(m.group(3))
            y = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(y, mm * x + b)


class MeanAbsoluteDeviationTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_mean_absolute_deviation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"data set: \$([\d, ]+)\$", problem)
            data = [int(v) for v in m.group(1).split(", ")]
            mean = sum(data) / len(data)
            expected = round(sum(abs(v - mean) for v in data) / len(data), 3)
            stated = float(re.search(r"\$([\d.]+)\$", solution).group(1))
            self.assertAlmostEqual(stated, expected, places=3)


class InterquartileRangeTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_interquartile_range"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"data set: \$([\d, ]+)\$", problem)
            data = sorted(int(v) for v in m.group(1).split(", "))
            self.assertEqual(len(data), 7)
            expected = data[5] - data[1]  # Q3 - Q1
            stated = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(stated, expected)


class ApproximateIrrationalTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_approximate_irrational"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            n = int(re.search(r"\\sqrt\{(\d+)\}", problem).group(1))
            root = math.sqrt(n)
            self.assertNotEqual(root, int(root))  # not a perfect square
            expected = round(root, 1)
            stated = float(re.search(r"\$([\d.]+)\$", solution).group(1))
            self.assertAlmostEqual(stated, expected, places=3)


class RangeTests(TestCase):
    PROBLEM = re.compile(r"range of the data set: \$(?P<data>[\d, ]+)\$")
    SOLUTION = re.compile(r"\$(?P<ans>\d+)\$")

    def test_range_matches(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_range"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            data = [int(v) for v in m.group("data").split(",")]
            expected = max(data) - min(data)
            self.assertEqual(int(self.SOLUTION.search(solution).group("ans")), expected,
                             f"{problem!r} -> {solution!r}")


class ModeTests(TestCase):
    PROBLEM = re.compile(r"mode of the data set: \$(?P<data>[\d, ]+)\$")
    SOLUTION = re.compile(r"\$(?P<ans>\d+)\$")

    def test_mode_matches(self):
        import random
        from collections import Counter
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_mode"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            data = [int(v) for v in m.group("data").split(",")]
            counts = Counter(data)
            top = max(counts.values())
            winners = [v for v, c in counts.items() if c == top]
            # The generator must produce a single unambiguous mode.
            self.assertEqual(len(winners), 1,
                             f"mode not unique: {problem!r} -> {solution!r}")
            stated = int(self.SOLUTION.search(solution).group("ans"))
            self.assertEqual(stated, winners[0], f"{problem!r} -> {solution!r}")


def parse_rational_token(tok):
    """Parse one ordered-list token into a Fraction (a/b, decimal, or int)."""
    tok = tok.strip()
    m = re.match(r"(-?\d+)/(\d+)$", tok)
    if m:
        return Fraction(int(m.group(1)), int(m.group(2)))
    return Fraction(tok)


class ConvertFdpTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_convert_fdp"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            # Recover the source value independently of its notation.
            mf = re.search(r"the fraction \$(-?\d+)/(\d+)\$", problem)
            md = re.search(r"the decimal \$(-?[\d.]+)\$", problem)
            mp = re.search(r"the percent \$(-?[\d.]+)\\%\$", problem)
            if mf:
                value = Fraction(int(mf.group(1)), int(mf.group(2)))
            elif md:
                value = Fraction(md.group(1))
            else:
                value = Fraction(mp.group(1)) / 100
            if "to a decimal" in problem:
                stated = Fraction(re.search(r"\$(-?[\d.]+)\$", solution).group(1))
                self.assertEqual(stated, value)
            elif "to a percent" in problem:
                sm = re.search(r"(-?[\d.]+)%", solution)
                self.assertEqual(Fraction(sm.group(1)) / 100, value)
            else:
                stated = parse_frac_solution(solution)
                self.assertEqual(stated, value)


class EvaluateExpressionTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_evaluate_expression"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"Evaluate \$(.+?)\$ when \$x = (-?\d+)\$", problem)
            terms = parse_poly(m.group(1))
            v = int(m.group(2))
            expected = sum(coeff * (v ** exp) for coeff, exp in terms)
            result = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(result, expected)


class DistributivePropertyTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_distributive_property"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"Expand \$(-?\d+)\((.+?)\)\$", problem)
            a = int(m.group(1))
            inner = parse_poly(m.group(2))
            sol_terms = parse_poly(re.search(r"\$(.+?)\$", solution).group(1))
            # Expression-valued: verify by numeric evaluation at sample points.
            for x in (-3, -1, 0, 2, 5):
                lhs = a * sum(c * (x ** e) for c, e in inner)
                rhs = sum(c * (x ** e) for c, e in sol_terms)
                self.assertEqual(lhs, rhs)


class OrderRationalTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_order_rational"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            prob = re.search(
                r"least to greatest: \$(.+?)\$\. Separate", problem
            ).group(1)
            sol = re.search(r"\$(.+?)\$", solution).group(1)
            p_vals = [parse_rational_token(t) for t in prob.split(",")]
            s_vals = [parse_rational_token(t) for t in sol.split(",")]
            # Solution is ascending and a permutation of the problem's values.
            self.assertEqual(s_vals, sorted(s_vals))
            self.assertEqual(sorted(p_vals), s_vals)


class CoordinateDistanceTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_coordinate_distance"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"\$\((-?\d+), (-?\d+)\)\$ and \$\((-?\d+), (-?\d+)\)\$", problem
            )
            x1, y1, x2, y2 = (int(m.group(i)) for i in range(1, 5))
            self.assertTrue(x1 == x2 or y1 == y2)
            expected = abs(y2 - y1) if x1 == x2 else abs(x2 - x1)
            self.assertNotEqual(expected, 0)
            stated = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            self.assertEqual(stated, expected)


class TwoStepEquationTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_two_step_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"Solve \$(-?\d+)x ([+-]) (\d+) = (-?\d+)\$", problem)
            a = int(m.group(1))
            b = int(m.group(3)) * (1 if m.group(2) == "+" else -1)
            c = int(m.group(4))
            expected = Fraction(c - b, a)
            self.assertEqual(parse_frac_solution(solution), expected)


class MultiStepEquationTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_multi_step_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"Solve \$(-?\d+)\(x ([+-]) (\d+)\) = (-?\d+)\$", problem
            )
            a = int(m.group(1))
            b = int(m.group(3)) * (1 if m.group(2) == "+" else -1)
            c = int(m.group(4))
            expected = Fraction(c, a) - b
            self.assertEqual(parse_frac_solution(solution), expected)


class PercentChangeTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_percent_change"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(r"changes from \$(-?\d+)\$ to \$(-?\d+)\$", problem)
            a, b = int(m.group(1)), int(m.group(2))
            expected = Fraction(b - a, a) * 100
            sm = re.search(r"(-?\d+(?:/\d+)?)%", solution)
            self.assertEqual(Fraction(sm.group(1)), expected)


class DiscountTaxTipTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_discount_tax_tip"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            price = int(re.search(r"\$(\d+)\$ dollars", problem).group(1))
            pct = int(re.search(r"\$(\d+)\\%\$", problem).group(1))
            if "discounted" in problem:
                expected_cents = price * (100 - pct)
            else:
                expected_cents = price * (100 + pct)
            sm = re.search(r"\$(\d+)\.(\d\d)", solution)
            stated_cents = int(sm.group(1)) * 100 + int(sm.group(2))
            self.assertEqual(stated_cents, expected_cents)


class ScaleLengthTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_scale_length"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            k = int(re.search(r"represents \$(\d+)\$ km", problem).group(1))
            stated = int(re.search(r"\$(-?\d+)\$", solution).group(1))
            if "measures" in problem:
                d = int(re.search(r"measures \$(\d+)\$ cm", problem).group(1))
                self.assertEqual(stated, d * k)
            else:
                actual = int(re.search(r"is \$(\d+)\$ km long", problem).group(1))
                self.assertEqual(stated * k, actual)


class CompoundProbabilityTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_compound_probability"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"Bag A has \$(\d+)\$ marbles, \$(\d+)\$ red\. "
                r"Bag B has \$(\d+)\$ marbles, \$(\d+)\$ blue",
                problem,
            )
            a, red, b, blue = (int(m.group(i)) for i in range(1, 5))
            expected = Fraction(red, a) * Fraction(blue, b)
            self.assertEqual(parse_frac_solution(solution), expected)


class VariablesBothSidesTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_variables_both_sides"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"Solve \$(-?\d+)x ([+-]) (\d+) = (-?\d+)x ([+-]) (\d+)\$",
                problem,
            )
            a = int(m.group(1))
            b = int(m.group(3)) * (1 if m.group(2) == "+" else -1)
            c = int(m.group(4))
            d = int(m.group(6)) * (1 if m.group(5) == "+" else -1)
            self.assertNotEqual(a, c)
            expected = Fraction(d - b, a - c)
            self.assertEqual(parse_frac_solution(solution), expected)


_LINE_RE = re.compile(
    r"\$y = (-?\d+/\d+|-?\d+|-)?x(?: ([+-]) (\d+/\d+|\d+))?\$"
)


def parse_line(solution):
    """Parse a ``$y = mx + b$`` solution into ``(m, b)`` Fractions."""
    m = _LINE_RE.search(solution)
    coef = m.group(1)
    if coef is None:
        slope = Fraction(1)
    elif coef == "-":
        slope = Fraction(-1)
    else:
        slope = Fraction(coef)
    if m.group(2) is None:
        intercept = Fraction(0)
    else:
        mag = Fraction(m.group(3))
        intercept = mag if m.group(2) == "+" else -mag
    return slope, intercept


class SlopeInterceptFormTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_slope_intercept_form"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"Rewrite \$(-?\d+)x ([+-]) (\d+)y = (-?\d+)\$", problem
            )
            A = int(m.group(1))
            B = int(m.group(3)) * (1 if m.group(2) == "+" else -1)
            C = int(m.group(4))
            slope, intercept = parse_line(solution)
            self.assertEqual(slope, Fraction(-A, B))
            self.assertEqual(intercept, Fraction(C, B))


class LineFromSlopePointTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_line_from_slope_point"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = re.search(
                r"slope \$(-?\d+(?:/\d+)?)\$ and passes through the point "
                r"\$\((-?\d+), (-?\d+)\)\$",
                problem,
            )
            slope_in = Fraction(m.group(1))
            x0, y0 = int(m.group(2)), int(m.group(3))
            expected_b = Fraction(y0) - slope_in * x0
            slope, intercept = parse_line(solution)
            self.assertEqual(slope, slope_in)
            self.assertEqual(intercept, expected_b)


class CompareFunctionsTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_compare_functions"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            slope_a, _ = parse_line(problem)  # A's equation is the only $y=...$
            pts = re.search(
                r"points \$\((-?\d+), (-?\d+)\)\$ and \$\((-?\d+), (-?\d+)\)\$",
                problem,
            )
            x1, y1, x2, y2 = (int(pts.group(i)) for i in range(1, 5))
            self.assertNotEqual(x1, x2)
            slope_b = Fraction(y2 - y1, x2 - x1)
            self.assertNotEqual(slope_a, slope_b)
            expected = "A" if slope_a > slope_b else "B"
            self.assertEqual(solution, expected)


class SystemSolutionCountTests(TestCase):
    def test(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_system_solution_count"]
        eq_re = re.compile(r"(-?\d+)x ([+-]) (\d+)y = (-?\d+)")
        for _ in range(SAMPLES):
            problem, solution = gen()
            eqs = eq_re.findall(problem)
            self.assertEqual(len(eqs), 2)
            (a1, s1, b1, c1), (a2, s2, b2, c2) = eqs
            a1, c1, a2, c2 = int(a1), int(c1), int(a2), int(c2)
            b1 = int(b1) * (1 if s1 == "+" else -1)
            b2 = int(b2) * (1 if s2 == "+" else -1)
            det = a1 * b2 - a2 * b1
            if det != 0:
                expected = "one"
            elif a1 * c2 - a2 * c1 == 0 and b1 * c2 - b2 * c1 == 0:
                expected = "infinite"
            else:
                expected = "none"
            self.assertEqual(solution, expected)


class AreaOfTrapezoidTests(TestCase):
    PROBLEM = re.compile(
        r"bases of length \$(?P<b1>\d+)\$ and \$(?P<b2>\d+)\$ and "
        r"height \$(?P<h>\d+)\$"
    )
    SOLUTION = re.compile(r"\$(?P<ans>\d+)\$")

    def test_area_of_trapezoid(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["pre_area_of_trapezoid"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            b1, b2, h = int(m.group("b1")), int(m.group("b2")), int(m.group("h"))
            # Bases/height are chosen so the area is a whole number.
            self.assertEqual((b1 + b2) * h % 2, 0, f"area not integral: {problem!r}")
            expected = (b1 + b2) * h // 2
            stated = int(self.SOLUTION.search(solution).group("ans"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")
