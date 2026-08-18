"""Math-correctness tests for the Algebra: Concepts & Connections generators.

Each test parses the generated problem statement, independently recomputes the
expected answer, and asserts the generator's stated solution matches. Every
generator is exercised over many random samples under a fixed seed so the check
covers its whole input space deterministically.
"""
import random
import re
from fractions import Fraction

from django.test import TestCase

from myapp.generators import algebra1  # noqa: F401 - registers the generators
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000


def _frac(text):
    """Parse ``'n'`` or ``'p/q'`` into a Fraction."""
    text = text.strip()
    if "/" in text:
        num, den = text.split("/")
        return Fraction(int(num), int(den))
    return Fraction(int(text))


class AbsoluteValueEquationTests(TestCase):
    PROBLEM = re.compile(r"\|(?P<a>\d+)x(?P<b>[+-]\d+)?\|=(?P<c>-?\d+)")
    ROOT = re.compile(r"x = (-?\d+(?:/\d+)?)")

    def test_roots_match(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_absolute_value_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = int(m.group("a"))
            b = int(m.group("b")) if m.group("b") else 0
            c = int(m.group("c"))

            if c < 0:
                self.assertEqual(solution, "no solution", problem)
                continue

            expected = {Fraction(c - b, a), Fraction(-c - b, a)}
            stated = {_frac(t) for t in self.ROOT.findall(solution)}
            self.assertEqual(
                stated, expected,
                f"roots wrong for {problem!r} -> {solution!r}",
            )


class ExponentialGrowthDecayTests(TestCase):
    PROBLEM = re.compile(
        r"amount of \$(?P<p>\d+)\$ (?P<verb>grows|decays) at a rate of "
        r"\$(?P<rate>\d+)\\%\$ per period. Find the amount after "
        r"\$(?P<n>\d+)\$ periods"
    )
    SOLUTION = re.compile(r"\$(?P<amt>-?[\d.]+)\$")

    def test_final_amount_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_exponential_growth_decay"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            principal = int(m.group("p"))
            rate = int(m.group("rate"))
            periods = int(m.group("n"))
            factor = (
                1 + rate / 100 if m.group("verb") == "grows" else 1 - rate / 100
            )
            expected = principal * factor ** periods
            stated = float(self.SOLUTION.search(solution).group("amt"))
            self.assertAlmostEqual(
                stated, expected, places=2,
                msg=f"amount wrong for {problem!r} -> {solution!r}",
            )


class EvaluateExponentialTests(TestCase):
    PROBLEM = re.compile(
        r"f\(x\)=(?P<a>\d+) \\cdot (?P<b>\d+)\^x\$, evaluate \$f\((?P<x>-?\d+)\)"
    )
    SOLUTION = re.compile(r"\$(?P<val>-?\d+(?:/\d+)?)\$")

    def test_value_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_evaluate_exponential"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = int(m.group("a"))
            b = int(m.group("b"))
            x = int(m.group("x"))
            expected = Fraction(a) * Fraction(b) ** x
            stated = _frac(self.SOLUTION.search(solution).group("val"))
            self.assertEqual(
                stated, expected,
                f"value wrong for {problem!r} -> {solution!r}",
            )


class DomainOfFunctionTests(TestCase):
    SQRT = re.compile(r"\\sqrt\{x(?P<b>[+-]\d+)?\}")
    RATIONAL = re.compile(r"\\frac\{1\}\{x(?P<b>[+-]\d+)?\}")
    GEQ = re.compile(r"x >= (?P<v>-?\d+)")
    NEQ = re.compile(r"x != (?P<v>-?\d+)")

    def test_domain_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_domain_of_function"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            sqrt = self.SQRT.search(problem)
            rational = self.RATIONAL.search(problem)
            if sqrt is not None:
                b = int(sqrt.group("b")) if sqrt.group("b") else 0
                m = self.GEQ.search(solution)
                self.assertIsNotNone(m, f"expected >= for {problem!r}")
                self.assertEqual(int(m.group("v")), -b, problem)
            else:
                self.assertIsNotNone(rational, f"could not parse: {problem!r}")
                b = int(rational.group("b")) if rational.group("b") else 0
                m = self.NEQ.search(solution)
                self.assertIsNotNone(m, f"expected != for {problem!r}")
                self.assertEqual(int(m.group("v")), -b, problem)


class DiscriminantTests(TestCase):
    PROBLEM = re.compile(r"discriminant of \$(?P<quad>[^$]+)\$")
    SOLUTION = re.compile(r"D=(?P<d>-?\d+)\$, (?P<n>\d+) real")

    def test_discriminant_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_discriminant"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            quad = self.PROBLEM.search(problem).group("quad")
            a, b, c = _parse_quad(quad)
            expected_d = b * b - 4 * a * c
            expected_n = 2 if expected_d > 0 else (1 if expected_d == 0 else 0)
            m = self.SOLUTION.search(solution)
            self.assertIsNotNone(m, f"could not parse: {solution!r}")
            self.assertEqual(int(m.group("d")), expected_d, problem)
            self.assertEqual(int(m.group("n")), expected_n, problem)


class AxisOfSymmetryTests(TestCase):
    PROBLEM = re.compile(r"axis of symmetry of \$(?P<quad>[^$]+)\$")
    SOLUTION = re.compile(r"x = (?P<v>-?\d+(?:/\d+)?)")

    def test_axis_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_axis_of_symmetry"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            quad = self.PROBLEM.search(problem).group("quad")
            a, b, c = _parse_quad(quad)
            expected = Fraction(-b, 2 * a)
            stated = _frac(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(
                stated, expected,
                f"axis wrong for {problem!r} -> {solution!r}",
            )


class SumProductRootsTests(TestCase):
    PROBLEM = re.compile(r"For \$(?P<quad>[^$]+)\$")
    SOLUTION = re.compile(
        r"sum=(?P<s>-?\d+(?:/\d+)?), product=(?P<p>-?\d+(?:/\d+)?)"
    )

    def test_sum_and_product_match(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_sum_product_roots"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            quad = self.PROBLEM.search(problem).group("quad")
            a, b, c = _parse_quad(quad)
            expected_sum = Fraction(-b, a)
            expected_product = Fraction(c, a)
            m = self.SOLUTION.search(solution)
            self.assertIsNotNone(m, f"could not parse: {solution!r}")
            self.assertEqual(_frac(m.group("s")), expected_sum, problem)
            self.assertEqual(_frac(m.group("p")), expected_product, problem)


class LinearInequalityTests(TestCase):
    PROBLEM = re.compile(
        r"\$(?P<a>-?\d+)x(?P<b>[+-]\d+)? (?P<op>\S+) (?P<c>-?\d+)\$"
    )
    # Solutions render relations in typeable ASCII; problems keep LaTeX.
    SOLUTION = re.compile(r"x (?P<op><=|>=|<|>) (?P<v>-?\d+(?:/\d+)?)")
    FLIP = {"<": ">", ">": "<", "\\leq": "\\geq", "\\geq": "\\leq"}
    ASCII_OF = {"<": "<", ">": ">", "\\leq": "<=", "\\geq": ">="}

    def test_inequality_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_linear_inequality_solve"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = int(m.group("a"))
            b = int(m.group("b")) if m.group("b") else 0
            c = int(m.group("c"))
            op = m.group("op")
            expected_threshold = Fraction(c - b, a)
            expected_op = self.FLIP[op] if a < 0 else op

            sol = self.SOLUTION.search(solution)
            self.assertIsNotNone(sol, f"could not parse: {solution!r}")
            self.assertEqual(sol.group("op"), self.ASCII_OF[expected_op], problem)
            self.assertEqual(
                _frac(sol.group("v")), expected_threshold,
                f"threshold wrong for {problem!r} -> {solution!r}",
            )


# Strict quadratic parser for "ax^2+bx+c" strings (a != 0), handling omitted
# unit/zero coefficients exactly as alg1._quadratic renders them.
_QUAD_RE = re.compile(
    r"^(?P<a>-?\d*)x\^2"
    r"(?:(?P<bsign>[+-])(?P<bmag>\d*)x)?"
    r"(?:(?P<csign>[+-])(?P<cmag>\d+))?$"
)


def _parse_quad(text):
    m = _QUAD_RE.match(text.strip())
    assert m is not None, f"could not parse quadratic: {text!r}"
    a_raw = m.group("a")
    a = 1 if a_raw == "" else (-1 if a_raw == "-" else int(a_raw))
    if m.group("bsign") is None:
        b = 0
    else:
        mag = int(m.group("bmag")) if m.group("bmag") else 1
        b = mag if m.group("bsign") == "+" else -mag
    if m.group("csign") is None:
        c = 0
    else:
        c = int(m.group("cmag")) if m.group("csign") == "+" else -int(m.group("cmag"))
    return a, b, c


class FactoringTests(TestCase):
    """The stated factorization must expand back to the quadratic in the prompt,
    and its two binomials must be ordered by constant term (least to greatest),
    as the problem instructs — the answer box matches the string exactly."""

    PROBLEM = re.compile(r"Factor the quadratic \$(?P<quad>[^$]+)\$")
    SOLUTION = re.compile(r"^\$\(x(?P<p>[+-]\d+)\)\(x(?P<q>[+-]\d+)\)\$$")

    def test_factors_expand_to_quadratic(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["factoring"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.PROBLEM.search(problem)
            self.assertIsNotNone(pm, f"could not parse problem: {problem!r}")
            a, b, c = _parse_quad(pm.group("quad"))
            self.assertEqual(a, 1, f"expected monic quadratic: {problem!r}")

            sm = self.SOLUTION.match(solution)
            self.assertIsNotNone(sm, f"unexpected solution form: {solution!r}")
            p = int(sm.group("p"))
            q = int(sm.group("q"))

            # (x+p)(x+q) = x^2 + (p+q)x + pq must match the prompt's b, c.
            self.assertEqual(p + q, b, f"middle term wrong: {problem!r} -> {solution!r}")
            self.assertEqual(p * q, c, f"constant term wrong: {problem!r} -> {solution!r}")
            # Canonical order: constant terms ascending.
            self.assertLessEqual(p, q, f"factors not ordered: {solution!r}")


class ProductOfPowersTests(TestCase):
    PROBLEM = re.compile(r"Simplify \$(?P<a>\d+)\^\{(?P<m>\d+)\} \\cdot (?P=a)\^\{(?P<n>\d+)\}\$")
    SOLUTION = re.compile(r"(?P<base>\d+)\^(?P<exp>\d+)")

    def test_exponents_add(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_product_of_powers"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, mm, nn = int(m.group("a")), int(m.group("m")), int(m.group("n"))
            s = self.SOLUTION.search(solution)
            self.assertEqual(int(s.group("base")), a, f"{problem!r} -> {solution!r}")
            self.assertEqual(int(s.group("exp")), mm + nn, f"{problem!r} -> {solution!r}")


class PowerOfProductTests(TestCase):
    PROBLEM = re.compile(r"Simplify \$\(xy\)\^\{(?P<n>\d+)\}\$")
    SOLUTION = re.compile(r"x\^(?P<a>\d+)\*y\^(?P<b>\d+)")

    def test_exponent_distributes(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_power_of_product"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            n = int(m.group("n"))
            s = self.SOLUTION.search(solution)
            self.assertEqual(int(s.group("a")), n, f"{problem!r} -> {solution!r}")
            self.assertEqual(int(s.group("b")), n, f"{problem!r} -> {solution!r}")


class NegativeExponentTests(TestCase):
    PROBLEM = re.compile(r"Evaluate \$(?P<a>\d+)\^\{-(?P<n>\d+)\}\$")

    def test_reciprocal_power(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_negative_exponent"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, n = int(m.group("a")), int(m.group("n"))
            self.assertEqual(_frac(solution.strip()), Fraction(1, a ** n),
                             f"{problem!r} -> {solution!r}")


class CompleteTheSquareTests(TestCase):
    PROBLEM = re.compile(r"Write \$(?P<quad>[^$]+)\$ in vertex form")
    SOLUTION = re.compile(r"\$\(x(?P<s>[+-]\d+)?\)\^2(?P<k>[+-]\d+)?\$")

    def test_vertex_form_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_complete_the_square"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.PROBLEM.search(problem)
            self.assertIsNotNone(pm, f"could not parse: {problem!r}")
            a, b, c = _parse_quad(pm.group("quad"))
            self.assertEqual(a, 1, f"expected monic quadratic: {problem!r}")

            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"unexpected solution form: {solution!r}")
            shift = int(sm.group("s")) if sm.group("s") else 0
            k = int(sm.group("k")) if sm.group("k") else 0

            # (x + shift)^2 + k must equal x^2 + bx + c for all x.
            for x in (-3, 0, 2, 5):
                lhs = (x + shift) ** 2 + k
                rhs = x * x + b * x + c
                self.assertEqual(
                    lhs, rhs,
                    f"vertex form wrong for {problem!r} -> {solution!r}",
                )


def _to_python(expr):
    """Insert explicit ``*`` for implicit multiplication so the expression can
    be ``eval``'d. Single letters are variables; sequences like ``lw`` and
    ``2w`` and ``V/(lw)`` become products."""
    expr = re.sub(r"(?<=\d)(?=[A-Za-z(])", "*", expr)      # 2w, 2(  -> 2*w, 2*(
    expr = re.sub(r"(?<=[A-Za-z])(?=[A-Za-z])", "*", expr)  # lw     -> l*w
    expr = re.sub(r"(?<=[A-Za-z])(?=\()", "*", expr)        # a(     -> a*(
    expr = re.sub(r"(?<=\))(?=[A-Za-z\d(])", "*", expr)     # )l     -> )*l
    return expr


class LiteralEquationTests(TestCase):
    PROBLEM = re.compile(
        r"Solve the formula \$(?P<eq>[^$]+)\$ for \$(?P<var>[A-Za-z])\$"
    )
    SOLUTION = re.compile(r"\$(?P<ans>[^$]+)\$")

    def test_rearrangement_satisfies_equation(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_literal_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.PROBLEM.search(problem)
            self.assertIsNotNone(pm, f"could not parse: {problem!r}")
            eq = pm.group("eq")
            var = pm.group("var")
            ans = self.SOLUTION.search(solution).group("ans")

            lhs, rhs = eq.split("=")
            variables = sorted(set(re.findall(r"[A-Za-z]", eq)))
            others = [v for v in variables if v != var]

            # Assign nonzero values to every variable except the solved one.
            env = {v: random.randint(1, 9) for v in others}
            # Compute the solved variable from the stated answer expression.
            env[var] = eval(_to_python(ans), {"__builtins__": {}}, env)

            left = eval(_to_python(lhs), {"__builtins__": {}}, dict(env))
            right = eval(_to_python(rhs), {"__builtins__": {}}, dict(env))
            self.assertAlmostEqual(
                left, right, places=6,
                msg=f"rearrangement wrong for {problem!r} -> {solution!r}",
            )


class PointSlopeFormTests(TestCase):
    PROBLEM = re.compile(
        r"through \$\((?P<x1>-?\d+), (?P<y1>-?\d+)\)\$ with slope \$(?P<m>-?\d+)\$"
    )
    SOLUTION = re.compile(r"\$(?P<left>[^=]+)=(?P<right>[^$]+)\$")

    def test_equation_matches_point_slope(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_point_slope_form"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.PROBLEM.search(problem)
            self.assertIsNotNone(pm, f"could not parse: {problem!r}")
            x1 = int(pm.group("x1"))
            y1 = int(pm.group("y1"))
            m = int(pm.group("m"))

            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse: {solution!r}")
            left = _to_python(sm.group("left"))
            right = _to_python(sm.group("right"))

            # left is "y (+/-) c"; the constant is left evaluated at y = 0.
            left0 = eval(left, {"__builtins__": {}}, {"y": 0})
            for x in (-4, -1, 0, 3, 7):
                right_val = eval(right, {"__builtins__": {}}, {"x": x})
                # Solve left(y) = right_val for y: y - left0 = right_val.
                y = right_val - left0
                expected = m * (x - x1) + y1
                self.assertAlmostEqual(
                    y, expected, places=6,
                    msg=f"line wrong for {problem!r} -> {solution!r}",
                )


class MultiplyBinomialsTests(TestCase):
    FACTOR = re.compile(r"\((?P<c>-?\d*)x(?P<k>[+-]\d+)\)")
    QUAD = re.compile(r"Expand \$(?P<factors>[^$]+)\$")
    SOLUTION = re.compile(r"\$(?P<quad>[^$]+)\$")

    @staticmethod
    def _coef(raw):
        return 1 if raw == "" else (-1 if raw == "-" else int(raw))

    def test_expansion_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_multiply_binomials"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            factors = self.QUAD.search(problem).group("factors")
            pairs = self.FACTOR.findall(factors)
            self.assertEqual(len(pairs), 2, f"could not parse: {problem!r}")
            a = self._coef(pairs[0][0])
            b = int(pairs[0][1])
            c = self._coef(pairs[1][0])
            d = int(pairs[1][1])

            quad = self.SOLUTION.search(solution).group("quad")
            P, Q, R = _parse_quad(quad)

            # (ax + b)(cx + d) must agree with Px^2 + Qx + R for all x.
            for x in (-3, -1, 0, 2, 4):
                lhs = (a * x + b) * (c * x + d)
                rhs = P * x * x + Q * x + R
                self.assertEqual(
                    lhs, rhs,
                    f"expansion wrong for {problem!r} -> {solution!r}",
                )


class SolveSystemTests(TestCase):
    LINE = re.compile(
        r"(?P<a>-?\d*)x (?P<bs>[+-]) (?P<b>\d*)y = (?P<e>-?\d+)"
    )
    SOLUTION = re.compile(r"\((?P<x>-?\d+), (?P<y>-?\d+)\)")

    @staticmethod
    def _coef(raw):
        return 1 if raw == "" else (-1 if raw == "-" else int(raw))

    def test_solution_satisfies_both_equations(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_solve_system"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            lines = self.LINE.findall(problem)
            self.assertEqual(len(lines), 2, f"could not parse: {problem!r}")

            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse: {solution!r}")
            x = int(sm.group("x"))
            y = int(sm.group("y"))

            for a_raw, bs, b_raw, e_raw in lines:
                a = self._coef(a_raw)
                b = self._coef(b_raw)
                if bs == "-":
                    b = -b
                e = int(e_raw)
                self.assertEqual(
                    a * x + b * y, e,
                    f"solution fails equation for {problem!r} -> {solution!r}",
                )


class VariationTests(TestCase):
    POINT = re.compile(
        r"varies (?P<kind>directly|inversely) with \$x\$\. "
        r"When \$x = (?P<x1>-?\d+)\$, \$y = (?P<y1>-?\d+)\$"
    )
    FIND_VALUE = re.compile(r"Find \$y\$ when \$x = (?P<x2>-?\d+)\$")
    SOLUTION = re.compile(r"\$(?P<v>-?\d+(?:/\d+)?)\$")

    def test_variation_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_variation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.POINT.search(problem)
            self.assertIsNotNone(pm, f"could not parse: {problem!r}")
            kind = pm.group("kind")
            x1 = int(pm.group("x1"))
            y1 = int(pm.group("y1"))

            if kind == "directly":
                const = Fraction(y1, x1)
            else:
                const = Fraction(x1 * y1)

            fv = self.FIND_VALUE.search(problem)
            if fv is not None:
                x2 = int(fv.group("x2"))
                expected = const * x2 if kind == "directly" else const / x2
            else:
                expected = const

            stated = _frac(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(
                stated, expected,
                f"variation wrong for {problem!r} -> {solution!r}",
            )


class SimplifyRationalTests(TestCase):
    PROBLEM = re.compile(r"\\frac\{(?P<num>[^}]+)\}\{(?P<den>[^}]+)\}")
    SOLUTION = re.compile(r"\$(?P<expr>[^$]+)\$")

    @staticmethod
    def _poly(a, b, c):
        return lambda x: a * x * x + b * x + c

    def test_simplification_agrees_numerically(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_simplify_rational"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.PROBLEM.search(problem)
            self.assertIsNotNone(pm, f"could not parse: {problem!r}")
            num = self._poly(*_parse_quad(pm.group("num")))
            den = self._poly(*_parse_quad(pm.group("den")))

            expr = _to_python(self.SOLUTION.search(solution).group("expr"))

            for x in (-6, -4, -1, 0, 3, 5, 8, 11):
                if den(x) == 0:
                    continue
                original = num(x) / den(x)
                simplified = eval(expr, {"__builtins__": {}}, {"x": x})
                self.assertAlmostEqual(
                    original, simplified, places=6,
                    msg=f"simplify wrong for {problem!r} -> {solution!r}",
                )


class AbsValueInequalityTests(TestCase):
    PROBLEM = re.compile(
        r"\|(?P<a>-?\d*)x(?P<b>[+-]\d+)?\| (?P<op>[<>]) (?P<c>\d+)"
    )
    LESS = re.compile(
        r"^\$(?P<lo>-?\d+(?:/\d+)?) < x < (?P<hi>-?\d+(?:/\d+)?)\$$"
    )
    GREATER = re.compile(
        r"^\$x < (?P<lo>-?\d+(?:/\d+)?) U x > (?P<hi>-?\d+(?:/\d+)?)\$$"
    )

    @staticmethod
    def _coef(raw):
        return 1 if raw == "" else (-1 if raw == "-" else int(raw))

    def test_boundaries_match(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_abs_value_inequality"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = self._coef(m.group("a"))
            b = int(m.group("b")) if m.group("b") else 0
            c = int(m.group("c"))
            op = m.group("op")

            expected = sorted([Fraction(-c - b, a), Fraction(c - b, a)])

            sm = (self.LESS if op == "<" else self.GREATER).match(solution)
            self.assertIsNotNone(
                sm, f"unexpected solution form: {problem!r} -> {solution!r}"
            )
            self.assertEqual(_frac(sm.group("lo")), expected[0], problem)
            self.assertEqual(_frac(sm.group("hi")), expected[1], problem)


class SimplifyRadicalTests(TestCase):
    PROBLEM = re.compile(r"Simplify \$\\sqrt\{(?P<n>\d+)\}\$")
    SOLUTION = re.compile(r"\$(?P<a>\d+)\*sqrt\((?P<b>\d+)\)\$")

    @staticmethod
    def _squarefree(k):
        i = 2
        while i * i <= k:
            if k % (i * i) == 0:
                return False
            i += 1
        return True

    def test_simplify_radical(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg1_simplify_radical"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.PROBLEM.search(problem)
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(pm, f"could not parse: {problem!r}")
            self.assertIsNotNone(sm, f"bad answer form: {solution!r}")
            n = int(pm.group("n"))
            a, b = int(sm.group("a")), int(sm.group("b"))
            # a*sqrt(b) squared must recover the radicand.
            self.assertEqual(a * a * b, n, f"{problem!r} -> {solution!r}")
            self.assertGreaterEqual(a, 2, "answer not actually simplified")
            self.assertGreaterEqual(b, 2, "radicand should stay > 1")
            self.assertTrue(
                self._squarefree(b), f"b not square-free: {solution!r}"
            )
