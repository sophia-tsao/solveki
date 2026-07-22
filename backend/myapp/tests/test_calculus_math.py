"""Math-correctness tests for the Solveki-local calculus generators.

Each test parses a generated problem, recomputes the expected answer
independently (with small polynomial helpers below), and asserts the stated
solution matches. Exact answers use ``assertEqual`` on ints/Fractions; floats
use ``assertAlmostEqual`` at 3 decimal places.
"""
import math
import random
import re
from fractions import Fraction

from django.test import TestCase

from myapp.generators import calculus  # noqa: F401  (import registers generators)
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000


# ------------------------- polynomial parsing helpers ---------------------

# optional sign, optional magnitude, then x^n / x / bare constant.
_TERM = re.compile(r"([+-]?)(\d*)x\^(\d+)|([+-]?)(\d*)x(?!\^)|([+-]?\d+)(?!x)")


def parse_poly(s):
    """Parse a rendered polynomial string into ``{exponent: coefficient}``."""
    poly = {}
    for m in _TERM.finditer(s):
        if m.group(3) is not None:  # x^n
            sign = -1 if m.group(1) == "-" else 1
            mag = int(m.group(2)) if m.group(2) else 1
            exp = int(m.group(3))
            poly[exp] = poly.get(exp, 0) + sign * mag
        elif m.group(0).endswith("x"):  # linear
            sign = -1 if m.group(4) == "-" else 1
            mag = int(m.group(5)) if m.group(5) else 1
            poly[1] = poly.get(1, 0) + sign * mag
        elif m.group(6):  # constant
            poly[0] = poly.get(0, 0) + int(m.group(6))
    return poly


def poly_eval(poly, x):
    return sum(coeff * (x ** exp) for exp, coeff in poly.items())


def poly_deriv(poly):
    return {exp - 1: coeff * exp for exp, coeff in poly.items() if exp >= 1}


def poly_norm(poly):
    """Drop zero coefficients for equality comparison."""
    return {e: c for e, c in poly.items() if c != 0}


def poly_integrate_definite(poly, a, b):
    return sum(
        Fraction(coeff * (b ** (exp + 1) - a ** (exp + 1)), exp + 1)
        for exp, coeff in poly.items()
    )


def parse_frac(s):
    m = re.search(r"(-?\d+)(?:/(-?\d+))?", s)
    num = int(m.group(1))
    den = int(m.group(2)) if m.group(2) else 1
    return Fraction(num, den)


def synth_div_linear(poly, c):
    """Divide ``poly`` by ``(x - c)``; return (quotient dict, remainder)."""
    deg = max(poly)
    coeffs = [poly.get(i, 0) for i in range(deg, -1, -1)]
    out = []
    carry = 0
    for coef in coeffs:
        carry = coef + carry * c
        out.append(carry)
    rem = out.pop()
    quotient = {deg - 1 - i: val for i, val in enumerate(out)}
    return quotient, rem


def solve_deriv_roots(deriv):
    """Return sorted list of (rational) roots of a linear/quadratic deriv."""
    A, B, C = deriv.get(2, 0), deriv.get(1, 0), deriv.get(0, 0)
    if A == 0:  # linear: B x + C = 0
        return [Fraction(-C, B)]
    disc = B * B - 4 * A * C
    r = math.isqrt(disc)
    root1 = Fraction(-B - r, 2 * A)
    root2 = Fraction(-B + r, 2 * A)
    return sorted({root1, root2})


gen = LOCAL_GENERATORS.get  # convenience


# --------------------------------- tests ----------------------------------

class LimitRationalTests(TestCase):
    P = re.compile(r"\\lim_\{x \\to (-?\d+)\} \\frac\{([^{}]+)\}\{([^{}]+)\}")

    def test_limit_matches(self):
        random.seed(0)
        g = gen("calc_limit_rational")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            c = int(m.group(1))
            num, den = parse_poly(m.group(2)), parse_poly(m.group(3))
            if poly_eval(den, c) != 0:
                expected = Fraction(poly_eval(num, c), poly_eval(den, c))
            else:
                qn, _ = synth_div_linear(num, c)
                qd, _ = synth_div_linear(den, c)
                expected = Fraction(poly_eval(qn, c), poly_eval(qd, c))
            self.assertEqual(parse_frac(solution), expected,
                             f"{problem!r} -> {solution!r}")


class DerivativePolynomialTests(TestCase):
    P = re.compile(r"f\(x\) = ([^$]+)\$")

    def test_derivative_matches(self):
        random.seed(0)
        g = gen("calc_derivative_polynomial")
        for _ in range(SAMPLES):
            problem, solution = g()
            poly = parse_poly(self.P.search(problem).group(1))
            stated = parse_poly(solution)
            self.assertEqual(poly_norm(stated), poly_norm(poly_deriv(poly)),
                             f"{problem!r} -> {solution!r}")


class ProductRuleTests(TestCase):
    P = re.compile(r"f\(x\) = \(([^)]+)\)\(([^)]+)\)\$ at \$x = (-?\d+)\$")

    def test_product_rule_matches(self):
        random.seed(0)
        g = gen("calc_product_rule")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            f1, f2 = parse_poly(m.group(1)), parse_poly(m.group(2))
            c = int(m.group(3))
            product = {}
            for e1, c1 in f1.items():
                for e2, c2 in f2.items():
                    product[e1 + e2] = product.get(e1 + e2, 0) + c1 * c2
            expected = poly_eval(poly_deriv(product), c)
            self.assertEqual(int(parse_frac(solution)), expected,
                             f"{problem!r} -> {solution!r}")


class QuotientRuleTests(TestCase):
    P = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}\$ at \$x = (-?\d+)\$")

    def test_quotient_rule_matches(self):
        random.seed(0)
        g = gen("calc_quotient_rule")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            num, den = parse_poly(m.group(1)), parse_poly(m.group(2))
            c = int(m.group(3))
            top = (poly_eval(poly_deriv(num), c) * poly_eval(den, c)
                   - poly_eval(num, c) * poly_eval(poly_deriv(den), c))
            expected = Fraction(top, poly_eval(den, c) ** 2)
            self.assertEqual(parse_frac(solution), expected,
                             f"{problem!r} -> {solution!r}")


class ChainRuleTests(TestCase):
    P = re.compile(r"f\(x\) = \(([^)]+)\)\^\{(\d+)\}\$ at \$x = (-?\d+)\$")

    def test_chain_rule_matches(self):
        random.seed(0)
        g = gen("calc_chain_rule")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            inner = parse_poly(m.group(1))
            n, c = int(m.group(2)), int(m.group(3))
            a = inner.get(1, 0)
            expected = n * a * (poly_eval(inner, c) ** (n - 1))
            self.assertEqual(int(parse_frac(solution)), expected,
                             f"{problem!r} -> {solution!r}")


class ExpLogTrigTests(TestCase):
    C = re.compile(r"at \$x = (-?\d+)\$")
    LN = re.compile(r"(-?\d+) \\ln\(x\)")
    EXP = re.compile(r"(-?\d+) e\^\{(-?\d+) x\}")
    SIN = re.compile(r"(-?\d+) \\sin\((-?\d+) x\)")
    COS = re.compile(r"(-?\d+) \\cos\((-?\d+) x\)")
    VAL = re.compile(r"\$(-?[\d.]+)\$")

    def test_exp_log_trig_matches(self):
        random.seed(0)
        g = gen("calc_derivative_exp_log_trig")
        for _ in range(SAMPLES):
            problem, solution = g()
            c = int(self.C.search(problem).group(1))
            if self.LN.search(problem):
                a = int(self.LN.search(problem).group(1))
                value = a / c
            elif self.EXP.search(problem):
                a, k = map(int, self.EXP.search(problem).groups())
                value = a * k * math.exp(k * c)
            elif self.SIN.search(problem):
                a, k = map(int, self.SIN.search(problem).groups())
                value = a * k * math.cos(k * c)
            elif self.COS.search(problem):
                a, k = map(int, self.COS.search(problem).groups())
                value = -a * k * math.sin(k * c)
            else:
                self.fail(f"could not parse: {problem!r}")
            stated = float(self.VAL.search(solution).group(1))
            self.assertAlmostEqual(stated, round(value, 3), places=6,
                                   msg=f"{problem!r} -> {solution!r}")


class HigherOrderTests(TestCase):
    P = re.compile(r"the (\d)(?:st|nd|rd|th) derivative of \$f\(x\) = "
                   r"([^$]+)\$ at \$x = (-?\d+)\$")

    def test_higher_order_matches(self):
        random.seed(0)
        g = gen("calc_higher_order_derivative")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            order = int(m.group(1))
            poly = parse_poly(m.group(2))
            c = int(m.group(3))
            d = poly
            for _ in range(order):
                d = poly_deriv(d)
            expected = poly_eval(d, c) if d else 0
            self.assertEqual(int(parse_frac(solution)), expected,
                             f"{problem!r} -> {solution!r}")


class TangentLineTests(TestCase):
    P = re.compile(r"to \$f\(x\) = ([^$]+)\$ at \$x = (-?\d+)\$")
    S = re.compile(r"\$y = ([^$]+)\$")

    def test_tangent_line_matches(self):
        random.seed(0)
        g = gen("calc_tangent_line")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            poly = parse_poly(m.group(1))
            c = int(m.group(2))
            m_exp = poly_eval(poly_deriv(poly), c)
            b_exp = poly_eval(poly, c) - m_exp * c
            line = parse_poly(self.S.search(solution).group(1))
            self.assertEqual(line.get(1, 0), m_exp,
                             f"slope wrong: {problem!r} -> {solution!r}")
            self.assertEqual(line.get(0, 0), b_exp,
                             f"intercept wrong: {problem!r} -> {solution!r}")


class ExtremaTests(TestCase):
    P = re.compile(r"critical points of \$f\(x\) = ([^$]+)\$")
    S = re.compile(r"\$x = ([^$]+)\$")

    def test_extrema_matches(self):
        random.seed(0)
        g = gen("calc_extrema")
        for _ in range(SAMPLES):
            problem, solution = g()
            poly = parse_poly(self.P.search(problem).group(1))
            expected = solve_deriv_roots(poly_deriv(poly))
            stated = [Fraction(x.strip())
                      for x in self.S.search(solution).group(1).split(",")]
            self.assertEqual(stated, expected,
                             f"{problem!r} -> {solution!r}")
            # each stated x is genuinely a critical point.
            for x in stated:
                self.assertEqual(poly_eval(poly_deriv(poly), x), 0,
                                 f"not a critical point: {problem!r} -> {x}")


class InflectionTests(TestCase):
    P = re.compile(r"inflection point of \$f\(x\) = ([^$]+)\$")
    S = re.compile(r"\$x = ([^$]+)\$")

    def test_inflection_matches(self):
        random.seed(0)
        g = gen("calc_inflection_point")
        for _ in range(SAMPLES):
            problem, solution = g()
            poly = parse_poly(self.P.search(problem).group(1))
            a, b = poly.get(3, 0), poly.get(2, 0)
            expected = Fraction(-b, 3 * a)
            self.assertEqual(parse_frac(self.S.search(solution).group(1)),
                             expected, f"{problem!r} -> {solution!r}")


class DefiniteIntegralTests(TestCase):
    P = re.compile(r"\\int_\{(-?\d+)\}\^\{(-?\d+)\} (.+?) \\, dx\$")

    def test_definite_integral_matches(self):
        random.seed(0)
        g = gen("calc_definite_integral_poly")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b = int(m.group(1)), int(m.group(2))
            poly = parse_poly(m.group(3))
            expected = poly_integrate_definite(poly, a, b)
            self.assertEqual(parse_frac(solution), expected,
                             f"{problem!r} -> {solution!r}")


class IndefiniteIntegralTests(TestCase):
    P = re.compile(r"\\int (.+?) \\, dx\$")
    S = re.compile(r"\$(.+) \+ C\$")

    def test_indefinite_integral_matches(self):
        random.seed(0)
        g = gen("calc_indefinite_integral_poly")
        for _ in range(SAMPLES):
            problem, solution = g()
            integrand = parse_poly(self.P.search(problem).group(1))
            anti = parse_poly(self.S.search(solution).group(1))
            self.assertEqual(poly_norm(poly_deriv(anti)), poly_norm(integrand),
                             f"{problem!r} -> {solution!r}")


class USubIntegralTests(TestCase):
    P = re.compile(r"\\int_\{(-?\d+)\}\^\{(-?\d+)\} \(([^)]+)\)\^\{(\d+)\} \\, dx")

    def test_usub_integral_matches(self):
        random.seed(0)
        g = gen("calc_usub_integral")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            p, q = int(m.group(1)), int(m.group(2))
            inner = parse_poly(m.group(3))
            n = int(m.group(4))
            a, b = inner.get(1, 0), inner.get(0, 0)
            expected = Fraction((a * q + b) ** (n + 1) - (a * p + b) ** (n + 1),
                                a * (n + 1))
            self.assertEqual(parse_frac(solution), expected,
                             f"{problem!r} -> {solution!r}")


class AreaBetweenCurvesTests(TestCase):
    P = re.compile(r"between \$f\(x\) = ([^$]+)\$ and \$g\(x\) = ([^$]+)\$ "
                   r"over \$\[(-?\d+), (-?\d+)\]\$")

    def test_area_matches(self):
        random.seed(0)
        g = gen("calc_area_between_curves")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            f = parse_poly(m.group(1))
            gpoly = parse_poly(m.group(2))
            a, b = int(m.group(3)), int(m.group(4))
            diff = dict(f)
            for e, c in gpoly.items():
                diff[e] = diff.get(e, 0) - c
            expected = abs(poly_integrate_definite(diff, a, b))
            self.assertEqual(parse_frac(solution), expected,
                             f"{problem!r} -> {solution!r}")


class AverageValueTests(TestCase):
    P = re.compile(r"average value of \$f\(x\) = ([^$]+)\$ on "
                   r"\$\[(-?\d+), (-?\d+)\]\$")

    def test_average_value_matches(self):
        random.seed(0)
        g = gen("calc_average_value")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            poly = parse_poly(m.group(1))
            a, b = int(m.group(2)), int(m.group(3))
            expected = poly_integrate_definite(poly, a, b) / (b - a)
            self.assertEqual(parse_frac(solution), expected,
                             f"{problem!r} -> {solution!r}")


class RiemannSumTests(TestCase):
    P = re.compile(r"the (left|right) Riemann sum of \$f\(x\) = ([^$]+)\$ on "
                   r"\$\[(-?\d+), (-?\d+)\]\$ using \$(\d+)\$ rectangles")

    def test_riemann_sum_matches(self):
        random.seed(0)
        g = gen("calc_riemann_sum")
        for _ in range(SAMPLES):
            problem, solution = g()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            side = m.group(1)
            poly = parse_poly(m.group(2))
            a, b, n = int(m.group(3)), int(m.group(4)), int(m.group(5))
            dx = Fraction(b - a, n)
            indices = range(n) if side == "left" else range(1, n + 1)
            expected = dx * sum(poly_eval(poly, a + i * dx) for i in indices)
            self.assertEqual(parse_frac(solution), expected,
                             f"{problem!r} -> {solution!r}")
