"""Math-correctness tests for the Algebra I variants (algebra1_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently (brute force where uniqueness matters), and checks the served
solution, over 2000 seeded samples.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.tests.test_prealgebra_variants_math import INT, frac, parse_xy, table_rows

SAMPLES = 2000


def linear(text):
    """(a, b) of a LaTeX linear expression ``ax + b`` such as ``-3x - 4`` or ``x``."""
    m = re.fullmatch(r"(-?\d*)x(?: ([+-]) (\d+))?", text.strip())
    a = {"": 1, "-": -1}[m[1]] if m[1] in ("", "-") else int(m[1])
    b = int(m[3]) * (1 if m[2] == "+" else -1) if m[2] else 0
    return a, b


def quadratic(text):
    """(a, b, c) of an algebra1-style ``ax^2+bx+c`` (no spaces)."""
    m = re.fullmatch(r"(-?\d*)x\^2(?:([+-]\d*)x)?([+-]\d+)?", text.strip())
    a = {"": 1, "-": -1}[m[1]] if m[1] in ("", "-") else int(m[1])
    b = 0 if m[2] is None else {"+": 1, "-": -1}.get(m[2], None)
    if m[2] is not None and b is None:
        b = int(m[2])
    c = int(m[3]) if m[3] else 0
    return a, b, c


class _Base(SimpleTestCase):
    name = variant = None

    def samples(self, name=None):
        random.seed(0)
        gen = LOCAL_GENERATORS[name or self.name]
        for _ in range(SAMPLES):
            problem, solution, _steps = gen(variant=self.variant)
            yield problem, solution.replace("$", "").strip()

    def search(self, pattern, problem):
        m = re.search(pattern, problem)
        self.assertIsNotNone(m, problem)
        return m


SYSTEM_TOPICS = ["alg1_solve_system", "system_of_equations", "linear_equations",
                 "alg2_solve_system_matrix"]


class SystemSumWithoutSolving(_Base):
    variant = "sum_without_solving"

    def test(self):
        for name in SYSTEM_TOPICS:
            for problem, solution in self.samples(name):
                m = self.search(r"If \$([^$]+)\$ and \$([^$]+)\$, what is", problem)
                a1, b1, c1 = parse_xy(m[1])
                a2, b2, c2 = parse_xy(m[2])
                det = a1 * b2 - a2 * b1
                x = Fraction(c1 * b2 - c2 * b1, det)
                y = Fraction(a1 * c2 - a2 * c1, det)
                self.assertEqual(Fraction(solution), x + y, problem)


class SystemNoSolutionParameter(_Base):
    variant = "no_solution_parameter"

    def test(self):
        for name in SYSTEM_TOPICS:
            for problem, solution in self.samples(name):
                m = self.search(r"system \$([^$]+)\$ and \$kx ([+-]) (\d*)y = " + INT, problem)
                a1, b1, c1 = parse_xy(m[1])
                b2 = int(m[3] or 1) * (1 if m[2] == "+" else -1)
                ks = [k for k in range(-100, 101) if a1 * b2 - b1 * k == 0]
                self.assertEqual(ks, [int(solution)], problem)
                self.assertNotEqual(Fraction(b2, b1) * c1, int(m[4]), problem)


class IntersectionLineThroughPoints(_Base):
    name, variant = "intersection_of_two_lines", "line_through_points"

    def test(self):
        for problem, solution in self.samples():
            pts = self.search(r"\$\(" + INT + ", " + INT + r"\)\$ and \$\(" + INT + ", " + INT, problem)
            xa, ya, xb, yb = (int(g) for g in pts.groups())
            m2, b2 = linear(self.search(r"is \$y = ([^$]+)\$", problem)[1])
            m1 = Fraction(yb - ya, xb - xa)
            b1 = ya - m1 * xa
            x = (b2 - b1) / (m1 - m2)
            self.assertEqual(solution, f"({x}, {m2 * x + b2})", problem)


class BasicAlgebraThinkOfANumber(_Base):
    name, variant = "basic_algebra", "think_of_a_number"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"by \$(\d+)\$, and then (add|subtract) \$(\d+)\$\. The result is \$" + INT,
                            problem)
            b = int(m[3]) * (1 if m[2] == "add" else -1)
            self.assertEqual(int(m[1]) * int(solution) + b, int(m[4]), problem)


class AbsSumOfSolutions(_Base):
    name, variant = "alg1_absolute_value_equation", "sum_of_solutions"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$\|([^|]+)\| = (\d+)\$", problem)
            a, b = linear(m[1])
            c = int(m[2])
            roots = {Fraction(c - b, a), Fraction(-c - b, a)}
            self.assertEqual(len(roots), 2)
            self.assertEqual(frac(solution), sum(roots), problem)


class AbsCountSolutions(_Base):
    name, variant = "alg1_absolute_value_equation", "count_solutions"

    def test(self):
        seen = set()
        for problem, solution in self.samples():
            m = self.search(r"\$\|([^|]+)\|(?: ([+-]) (\d+))? = " + INT + r"\$", problem)
            a, b = linear(m[1])
            d = int(m[3]) * (1 if m[2] == "+" else -1) if m[2] else 0
            c = int(m[4]) - d
            # Count real solutions exactly from |ax + b| = c.
            count = 0 if c < 0 else (1 if c == 0 else 2)
            self.assertEqual(int(solution), count, problem)
            seen.add(count)
        self.assertEqual(seen, {0, 1, 2})


class InequalityCountIntegers(_Base):
    name, variant = "alg1_linear_inequality_solve", "count_integers"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$" + INT + r" < ([^\\]+) \\leq " + INT + r"\$", problem)
            lo, (a, b), hi = int(m[1]), linear(m[2]), int(m[3])
            self.assertEqual(int(solution), sum(1 for x in range(-200, 201) if lo < a * x + b <= hi))


class AbsInequalityWriteAsAbsolute(_Base):
    name, variant = "alg1_abs_value_inequality", "write_as_absolute"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$" + INT + r" < x < " + INT + r"\$.*What is \$(c|r)\$", problem)
            lo, hi = int(m[1]), int(m[2])
            # Brute force: the unique (c, r) whose |x - c| < r is exactly (lo, hi).
            fits = [(c, r) for c in range(-30, 31) for r in range(1, 30) if (c - r, c + r) == (lo, hi)]
            self.assertEqual(len(fits), 1)
            c, r = fits[0]
            self.assertEqual(int(solution), c if m[3] == "c" else r, problem)


class ProductMissingExponent(_Base):
    name, variant = "alg1_product_of_powers", "missing_exponent"

    def test(self):
        for problem, solution in self.samples():
            a, m, n = (int(g) for g in self.search(
                r"\$(\d+)\^\{(\d+)\} \\cdot \d+\^\{\\square\} = \d+\^\{(\d+)\}", problem).groups())
            self.assertEqual(a ** m * a ** int(solution), a ** n, problem)


class PowerOfProductMissing(_Base):
    name, variant = "alg1_power_of_product", "missing_power"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$\((\d+)x(?:\^\{(\d+)\})?\)\^\{\\square\} = (\d+)x\^\{(\d+)\}\$", problem)
            c, p, coef, e = int(m[1]), int(m[2] or 1), int(m[3]), int(m[4])
            n = int(solution)
            self.assertEqual((c ** n, p * n), (coef, e), problem)


class NegativeExponentAsPower(_Base):
    name, variant = "alg1_negative_exponent", "as_power"

    def test(self):
        for problem, solution in self.samples():
            d, a = map(int, self.search(r"\\frac\{1\}\{(\d+)\} = (\d+)\^", problem).groups())
            self.assertEqual(Fraction(a) ** int(solution), Fraction(1, d), problem)


class RadicalAdd(_Base):
    name, variant = "alg1_simplify_radical", "add_radicals"

    def test(self):
        for problem, solution in self.samples():
            u, v, b = map(int, self.search(
                r"\\sqrt\{(\d+)\} \+ \\sqrt\{(\d+)\} = \\square\\sqrt\{(\d+)\}", problem).groups())
            n = int(solution)
            self.assertAlmostEqual(math.sqrt(u) + math.sqrt(v), n * math.sqrt(b), places=9)


class PowerOfPowersRewriteBase(_Base):
    name, variant = "power_of_powers", "rewrite_base"

    def test(self):
        for problem, solution in self.samples():
            v, n, base = map(int, self.search(r"\$(\d+)\^\{(\d+)\} = (\d+)\^", problem).groups())
            self.assertEqual(base ** int(solution), v ** n, problem)


class QuotientMissingExponent(_Base):
    name, variant = "quotient_of_power_same_base", "missing_exponent"

    def test(self):
        for problem, solution in self.samples():
            a, m, n = map(int, self.search(
                r"\\frac\{(\d+)\^\{(\d+)\}\}\{\d+\^\{\\square\}\} = \d+\^\{(\d+)\}", problem).groups())
            self.assertEqual(Fraction(a ** m, a ** int(solution)), a ** n, problem)


class QuotientSamePowerEvaluate(_Base):
    name, variant = "quotient_of_power_same_power", "evaluate_base_first"

    def test(self):
        for problem, solution in self.samples():
            a, n, b, n2 = map(int, self.search(
                r"\\frac\{(\d+)\^\{(\d+)\}\}\{(\d+)\^\{(\d+)\}\}", problem).groups())
            self.assertEqual(Fraction(a ** n, b ** n2), int(solution), problem)


class SciProductMissingFactor(_Base):
    name, variant = "product_of_scientific_notations", "missing_factor"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\((\d+) \\times 10\^\{" + INT + r"\}\)\(\\square \\times 10\^\{" + INT
                            + r"\}\) = (\d+) \\times 10\^\{" + INT, problem)
            m1, e1, e2, p, e = (int(g) for g in m.groups())
            self.assertEqual(e1 + e2, e)
            self.assertEqual(m1 * int(solution), p, problem)


class BinomialMissingConstant(_Base):
    variant = "missing_constant"

    def test(self):
        for name in ("alg1_multiply_binomials", "expanding"):
            for problem, solution in self.samples(name):
                m = self.search(r"\$\(([^)]+)\)\(x \+ k\) = ([^$]+)\$", problem)
                a, b = linear(m[1])
                qa, qb, qc = quadratic(m[2])
                ks = [k for k in range(-50, 51) if (a, a * k + b, b * k) == (qa, qb, qc)]
                self.assertEqual(ks, [int(solution)], problem)


class FactoringCountFactorable(_Base):
    name, variant = "factoring", "count_factorable"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"x\^2 \+ bx ([+-]) (\d+)\$", problem)
            c = int(m[2]) * (1 if m[1] == "+" else -1)
            bs = {p + q for p in range(-40, 41) for q in range(-40, 41) if p * q == c}
            self.assertEqual(int(solution), len(bs), problem)


class CombineCoefficient(_Base):
    name, variant = "combine_like_terms", "coefficient_after_distributing"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d+)\(x ([+-]) (\d+)\) - (\d+)\(x ([+-]) (\d+)\) ([+-]) (\d*)x\$", problem)
            a, c = int(m[1]), int(m[4])
            e = int(m[8] or 1) * (1 if m[7] == "+" else -1)
            # Evaluate the expression's slope numerically: f(1) - f(0).
            b = int(m[3]) * (1 if m[2] == "+" else -1)
            d = int(m[6]) * (1 if m[5] == "+" else -1)
            f = lambda x: a * (x + b) - c * (x + d) + e * x  # noqa: E731
            self.assertEqual(int(solution), f(1) - f(0), problem)


class CompleteSquareMissingConstant(_Base):
    name, variant = "alg1_complete_the_square", "missing_constant"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$x\^2 ([+-]) (\d*)x \+ \\square\$", problem)
            b = int(m[2] or 1) * (1 if m[1] == "+" else -1)
            c = frac(solution)
            # x^2 + bx + c is a perfect square iff its discriminant is 0.
            self.assertEqual(b * b - 4 * c, 0, problem)


class RationalMissingFactor(_Base):
    name, variant = "alg1_simplify_rational", "missing_factor"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{([^}]+)\}\{([^}]+)\}", problem)
            qa, qb, qc = quadratic(m[1])
            a1, b1 = linear(m[2])
            n = int(solution)
            # (x + b1)(x + n) == numerator
            self.assertEqual((1, b1 + n, b1 * n), (qa, qb, qc), problem)


class DiscriminantLargestC(_Base):
    name, variant = "alg1_discriminant", "largest_c"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d*)x\^2 ([+-]) (\d*)x \+ c = 0\$", problem)
            a = int(m[1] or 1)
            b = int(m[3] or 1) * (1 if m[2] == "+" else -1)
            two_roots = [c for c in range(-200, 200) if b * b - 4 * a * c > 0]
            self.assertEqual(int(solution), max(two_roots), problem)


class AxisFromSymmetricPoints(_Base):
    name, variant = "alg1_axis_of_symmetry", "from_symmetric_points"

    def test(self):
        for problem, solution in self.samples():
            p, v1, q, v2 = map(int, self.search(r"\(" + INT + ", " + INT + r"\)\$ and \$\(" + INT + ", "
                                                + INT, problem).groups())
            self.assertEqual(v1, v2)
            self.assertEqual(frac(solution.replace("x = ", "")), Fraction(p + q, 2), problem)


class RootsSymmetricExpression(_Base):
    name, variant = "alg1_sum_product_roots", "symmetric_expression"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = quadratic(self.search(r"roots of \$([^$]+) = 0\$", problem)[1])
            s, p = Fraction(-b, a), Fraction(c, a)
            if r"\frac{1}{r}" in problem:
                expected = s / p
            else:
                expected = s * s - 2 * p
            self.assertEqual(frac(solution), expected, problem)


class VertexLeadingCoefficient(_Base):
    name, variant = "vertex_form", "leading_coefficient"

    def test(self):
        for problem, solution in self.samples():
            h, k, x, y = map(int, self.search(r"vertex at \$\(" + INT + ", " + INT + r"\)\$ and passes "
                                              r"through \$\(" + INT + ", " + INT, problem).groups())
            self.assertEqual(int(solution) * (x - h) ** 2 + k, y, problem)


class AroCTable(_Base):
    name, variant = "aroc_over_interval", "table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, row)) for row in table_rows(problem))
            f = dict(zip(xs, ys))
            a, b = map(int, self.search(r"from \$x = " + INT + r"\$ to \$x = " + INT, problem).groups())
            self.assertEqual(frac(solution), Fraction(f[b] - f[a], b - a), problem)


class ExponentialSolveForX(_Base):
    name, variant = "alg1_evaluate_exponential", "solve_for_x"

    def test(self):
        for problem, solution in self.samples():
            a, b, v = map(int, self.search(r"\$f\(x\) = (\d+) \\cdot (\d+)\^x\$ and \$f\(x\) = (\d+)",
                                           problem).groups())
            self.assertEqual(a * b ** int(solution), v, problem)


class GrowthDoublingPeriod(_Base):
    name, variant = "alg1_exponential_growth_decay", "doubling_period"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"(doubles|triples) every \$(\d+)\$ years", problem)
            k = 2 if m[1] == "doubles" else 3
            self.assertAlmostEqual(float(solution), k ** (1 / int(m[2])), delta=0.0005)


class DomainSmallestInteger(_Base):
    name, variant = "alg1_domain_of_function", "smallest_integer"

    def test(self):
        for problem, solution in self.samples():
            a, b = linear(self.search(r"\\sqrt\{([^}]+)\}", problem)[1])
            self.assertEqual(int(solution), min(x for x in range(-50, 50) if a * x + b >= 0), problem)


class PointSlopeYIntercept(_Base):
    name, variant = "alg1_point_slope_form", "y_intercept"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"line \$y(?: ([+-]) (\d+))? = ([^$]+)\$", problem)
            y_shift = int(m[2]) * (1 if m[1] == "+" else -1) if m[1] else 0
            rhs = m[3]
            pm = re.fullmatch(r"(-?\d+)\(x(?: ([+-]) (\d+))?\)", rhs)
            if pm:
                slope = int(pm[1])
                x_shift = int(pm[3]) * (1 if pm[2] == "+" else -1) if pm[2] else 0
                at_zero = slope * x_shift
            else:
                at_zero = 0
            # y + y_shift = rhs  =>  at x = 0, y = rhs(0) - y_shift
            self.assertEqual(int(solution), at_zero - y_shift, problem)


class LiteralScaling(_Base):
    name, variant = "alg1_literal_equation", "scaling"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"formula \$([^$]+)\$, \$(\w)\$ is multiplied by \$(\d+)\$ while .*? "
                            r"stays? the same\. By what number is \$(\w)\$", problem)
            formula, varied, k, target = m[1], m[2], int(m[3]), m[4]
            lhs, rhs = formula.split(" = ")
            # Every other variable stays 1; `varied` becomes k. Solve for `target`.
            values = {v: Fraction(k if v == varied else 1) for v in [lhs, *rhs]}
            if target == lhs:
                new = math.prod(values[v] for v in rhs)
            else:
                new = values[lhs] / math.prod(values[v] for v in rhs if v != target)
            self.assertEqual(frac(solution), new, problem)


class VariationScaling(_Base):
    name, variant = "alg1_variation", "scaling"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"varies (directly|inversely) with (the square of )?\$x\$\. If \$x\$ is "
                            r"multiplied by \$(\d+)\$", problem)
            k = int(m[3])
            power = (2 if m[2] else 1) * (1 if m[1] == "directly" else -1)
            self.assertEqual(frac(solution), Fraction(k) ** power, problem)


class DivideHowManyServings(_Base):
    name, variant = "divide_fractions", "how_many_servings"

    def test(self):
        for problem, solution in self.samples():
            unit = frac(self.search(r"uses \$([^$]+)\$ cup", problem)[1])
            total = frac(self.search(r"from \$([^$]+)\$ cups", problem)[1])
            self.assertEqual(frac(solution), total / unit, problem)
            self.assertEqual((total / unit).denominator, 1)


class MultiplyFractionOfFraction(_Base):
    name, variant = "fraction_multiplication", "fraction_of_a_fraction"

    def test(self):
        for problem, solution in self.samples():
            second = frac(self.search(r"^\$([^$]+)\$ of a garden", problem)[1])
            first = frac(self.search(r"vegetables\. \$([^$]+)\$ of the", problem)[1])
            self.assertEqual(frac(solution), first * second, problem)


class FactorsCount(_Base):
    name, variant = "factors", "count"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"does \$(\d+)\$ have", problem)[1])
            self.assertEqual(int(solution), sum(1 for d in range(1, n + 1) if n % d == 0))


class CommonFactorsCount(_Base):
    name, variant = "common_factors", "count"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"do \$(\d+)\$ and \$(\d+)\$ have", problem).groups())
            self.assertEqual(int(solution), sum(1 for d in range(1, 101) if a % d == 0 and b % d == 0))


# --- Further variants -----------------------------------------------------------

def signed(sign, magnitude):
    return int(magnitude) * (1 if sign == "+" else -1)


def coef(text):
    return {"": 1, "-": -1}[text] if text in ("", "-") else int(text)


def roots_of(a, b, c):
    """Real roots of ax^2 + bx + c, exactly when rational (else floats)."""
    disc = b * b - 4 * a * c
    if disc < 0:
        return []
    r = math.isqrt(disc)
    if r * r == disc:
        return sorted({Fraction(-b - r, 2 * a), Fraction(-b + r, 2 * a)})
    return sorted({(-b - math.sqrt(disc)) / (2 * a), (-b + math.sqrt(disc)) / (2 * a)})


class SystemPurchase(_Base):
    variant = "purchase"

    def test(self):
        for name in SYSTEM_TOPICS:
            for problem, solution in self.samples(name):
                m = self.search(r"bought \$(\d+)\$ \w+\. .*? cost \$(\d+)\$ dollars each and .*? cost "
                                r"\$(\d+)\$ dollars each\. The total was \$(\d+)\$", problem)
                total, p1, p2, cost = (int(g) for g in m.groups())
                fits = [a for a in range(0, total + 1) if p1 * a + p2 * (total - a) == cost]
                self.assertEqual(fits, [int(solution)], problem)


class SystemCoefficientFromSolution(_Base):
    variant = "coefficient_from_solution"

    def test(self):
        for name in SYSTEM_TOPICS:
            for problem, solution in self.samples(name):
                m = self.search(r"point \$\(" + INT + ", " + INT + r"\)\$ is a solution of \$ax ([+-]) (\d*)y = "
                                + INT, problem)
                x, y = int(m[1]), int(m[2])
                b, c = signed(m[3], m[4] or 1), int(m[5])
                self.assertEqual(int(solution) * x + b * y, c, problem)


class BinomialCoefficientOfX(_Base):
    variant = "coefficient_of_x"

    def test(self):
        for name in ("alg1_multiply_binomials", "expanding"):
            for problem, solution in self.samples(name):
                m = self.search(r"\$\(([^)]+)\)\(([^)]+)\)\$", problem)
                (a, b), (c, d) = linear(m[1]), linear(m[2])
                f = lambda x: (a * x + b) * (c * x + d)  # noqa: E731
                # coefficient of x = (f(1) - f(-1)) / 2
                self.assertEqual(int(solution), (f(1) - f(-1)) // 2, problem)


class BinomialDifferenceOfSquares(_Base):
    variant = "difference_of_squares"

    def test(self):
        for name in ("alg1_multiply_binomials", "expanding"):
            for problem, solution in self.samples(name):
                p, q = map(int, self.search(r"to find \$(\d+) \\times (\d+)\$", problem).groups())
                self.assertEqual(int(solution), p * q, problem)


class BinomialRectangleArea(_Base):
    variant = "rectangle_area"

    def test(self):
        for name in ("alg1_multiply_binomials", "expanding"):
            for problem, solution in self.samples(name):
                m = self.search(r"is \$([^$]+)\$ units long and \$([^$]+)\$ units wide", problem)
                (a, b), (c, d) = linear(m[1]), linear(m[2])
                self.assertEqual(quadratic(solution), (a * c, a * d + b * c, b * d), problem)


class FactoringMiddleCoefficient(_Base):
    name, variant = "factoring", "middle_coefficient"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"= \(x(?: ([+-] \d+))?\)\(x(?: ([+-] \d+))?\)\$", problem)
            p = int(m[1].replace(" ", "")) if m[1] else 0
            q = int(m[2].replace(" ", "")) if m[2] else 0
            self.assertEqual(int(solution), p + q, problem)


class FactoringLargerRoot(_Base):
    name, variant = "factoring", "larger_root"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = quadratic(self.search(r"solution of \$([^$]+) = 0\$", problem)[1])
            self.assertEqual(Fraction(solution), max(roots_of(a, b, c)), problem)


class FactoringOtherSide(_Base):
    name, variant = "factoring", "other_side"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = quadratic(self.search(r"has area \$([^$]+)\$", problem)[1])
            p = int(self.search(r"length \$x \+ (\d+)\$", problem)[1])
            q = int(re.fullmatch(r"x\+(\d+)", solution)[1])
            self.assertEqual((a, b, c), (1, p + q, p * q), problem)


class QuadraticDoubleRoot(_Base):
    name, variant = "quadratic_equation", "double_root"

    def test(self):
        for problem, solution in self.samples():
            b = signed(*self.search(r"\$x\^2 ([+-]) (\d+)x \+ c = 0\$", problem).groups())
            self.assertEqual(len(roots_of(1, b, int(solution))), 1, problem)


class QuadraticProjectile(_Base):
    name, variant = "quadratic_equation", "projectile"

    def test(self):
        for problem, solution in self.samples():
            v, h = map(int, self.search(r"-16t\^2 \+ (\d+)t \+ (\d+)\$", problem).groups())
            t = max(roots_of(-16, v, h))
            self.assertAlmostEqual(float(solution), float(t), delta=0.0005)


class QuadraticPositiveRoot(_Base):
    name, variant = "quadratic_equation", "positive_root"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = quadratic(self.search(r"solution of \$([^$]+) = 0\$", problem)[1])
            positive = [r for r in roots_of(a, b, c) if r > 0]
            self.assertEqual(len(positive), 1)
            self.assertEqual(Fraction(solution), positive[0], problem)


class VertexExtremeValue(_Base):
    name, variant = "vertex_form", "extreme_value"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"the (minimum|maximum) value of \$y = (-?\d*)\(x(?: ([+-] \d+))?\)\^2(?: ([+-] \d+))?\$",
                            problem)
            a = coef(m[2])
            h = -int(m[3].replace(" ", "")) if m[3] else 0
            k = int(m[4].replace(" ", "")) if m[4] else 0
            self.assertEqual(m[1], "minimum" if a > 0 else "maximum")
            values = [a * (x - h) ** 2 + k for x in range(h - 5, h + 6)]
            self.assertEqual(int(solution), min(values) if a > 0 else max(values), problem)


class VertexMaxHeight(_Base):
    name, variant = "vertex_form", "max_height"

    def test(self):
        for problem, solution in self.samples():
            a, t, top = self.search(r"= (-[\d.]+)\(t - (\d+)\)\^2 \+ (\d+)\$", problem).groups()
            h = lambda x: Fraction(a) * (x - int(t)) ** 2 + int(top)  # noqa: E731
            best = max(h(Fraction(i, 10)) for i in range(0, 200))
            self.assertEqual(Fraction(solution), best, problem)


class AroCEndpointFromRate(_Base):
    name, variant = "aroc_over_interval", "endpoint_from_rate"

    def test(self):
        for problem, solution in self.samples():
            a, rate = map(int, self.search(r"from \$x = " + INT + r"\$ to \$x = b\$ is \$" + INT, problem).groups())
            fits = [b for b in range(a + 1, a + 50) if Fraction(b * b - a * a, b - a) == rate]
            self.assertEqual(fits, [int(solution)], problem)


class AroCAverageSpeed(_Base):
    name, variant = "aroc_over_interval", "average_speed"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$d\(t\) = (\d*)t\^2(?: \+ (\d+)t)?\$.*from \$t = (\d+)\$ to \$t = (\d+)\$", problem)
            p, q = coef(m[1]), int(m[2] or 0)
            t1, t2 = int(m[3]), int(m[4])
            d = lambda t: p * t * t + q * t  # noqa: E731
            self.assertEqual(frac(solution), Fraction(d(t2) - d(t1), t2 - t1), problem)


class DiscriminantOneRootParameter(_Base):
    name, variant = "alg1_discriminant", "one_root_parameter"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d*)x\^2 \+ kx \+ (\d+) = 0\$", problem)
            a, c = coef(m[1]), int(m[2])
            ks = [k for k in range(1, 200) if k * k - 4 * a * c == 0]
            self.assertEqual(ks, [int(solution)], problem)


class DiscriminantXIntercepts(_Base):
    name, variant = "alg1_discriminant", "x_intercepts"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = quadratic(self.search(r"graph of \$y = ([^$]+)\$", problem)[1])
            self.assertEqual(int(solution), len(roots_of(a, b, c)), problem)


class DiscriminantReachesHeight(_Base):
    name, variant = "alg1_discriminant", "reaches_height"

    def test(self):
        for problem, solution in self.samples():
            v, h0 = map(int, self.search(r"-16t\^2 \+ (\d+)t \+ (\d+)\$", problem).groups())
            target = int(self.search(r"reach \$(\d+)\$ feet", problem)[1])
            top = Fraction(v * v, 64) + h0   # height at the vertex t = v/32
            self.assertEqual(solution, "yes" if target <= top else "no", problem)


class AxisFactoredForm(_Base):
    name, variant = "alg1_axis_of_symmetry", "factored_form"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$y = (-?\d*)\(x(?: ([+-] \d+))?\)\(x(?: ([+-] \d+))?\)\$", problem)
            r = -int(m[2].replace(" ", "")) if m[2] else 0
            q = -int(m[3].replace(" ", "")) if m[3] else 0
            self.assertEqual(frac(solution.replace("x = ", "")), Fraction(r + q, 2), problem)


class AxisMissingCoefficient(_Base):
    name, variant = "alg1_axis_of_symmetry", "missing_coefficient"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$y = (-?\d*)x\^2 \+ bx.*is \$x = " + INT, problem)
            a, h = coef(m[1]), int(m[2])
            self.assertEqual(Fraction(-int(solution), 2 * a), h, problem)


class RootsBuildFromSumProduct(_Base):
    name, variant = "alg1_sum_product_roots", "build_from_sum_product"

    def test(self):
        for problem, solution in self.samples():
            total, product = map(int, self.search(r"add up to \$" + INT + r"\$ and multiply to \$" + INT,
                                                  problem).groups())
            want = self.search(r"What is \$(b|c)\$", problem)[1]
            self.assertEqual(int(solution), -total if want == "b" else product, problem)


class CompleteSquareMinimum(_Base):
    name, variant = "alg1_complete_the_square", "minimum_value"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = quadratic(self.search(r"\$y = ([^$]+)\$", problem)[1])
            self.assertEqual(Fraction(solution), Fraction(4 * a * c - b * b, 4 * a), problem)


class CompleteSquareSolve(_Base):
    name, variant = "alg1_complete_the_square", "solve"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = quadratic(self.search(r"Solve \$([^$]+) = 0\$", problem)[1])
            self.assertEqual(Fraction(solution), max(roots_of(a, b, c)), problem)


class LiteralUseFormula(_Base):
    name, variant = "alg1_literal_equation", "use_formula"

    def test(self):
        for problem, solution in self.samples():
            x = Fraction(solution)
            if "P = 2l + 2w" in problem:
                P, l = map(int, self.search(r"If \$P = (\d+)\$ and \$l = (\d+)\$", problem).groups())
                self.assertEqual(2 * l + 2 * x, P)
            elif "d = rt" in problem:
                d, t = map(int, self.search(r"If \$d = (\d+)\$ and \$t = (\d+)\$", problem).groups())
                self.assertEqual(x * t, d)
            elif "F = " in problem:
                f = Fraction(self.search(r"If \$F = (-?[\d.]+)\$", problem)[1])
                self.assertEqual(Fraction(9, 5) * x + 32, f)
            else:
                I, P, r = self.search(r"If \$I = (\d+)\$, \$P = (\d+)\$, and \$r = (\d+)\\%\$", problem).groups()
                self.assertEqual(int(P) * Fraction(int(r), 100) * x, int(I), problem)


class PointSlopePointOnLine(_Base):
    name, variant = "alg1_point_slope_form", "point_on_line"

    def test(self):
        for problem, solution in self.samples():
            x = int(self.search(r"point \$\(" + INT + r", k\)\$", problem)[1])
            m = self.search(r"line \$y(?: ([+-]) (\d+))? = " + INT + r"\(x(?: ([+-]) (\d+))?\)\$", problem)
            y_shift = signed(m[1], m[2]) if m[1] else 0
            slope = int(m[3])
            x_shift = signed(m[4], m[5]) if m[4] else 0
            self.assertEqual(int(solution) + y_shift, slope * (x + x_shift), problem)


class VariationTablePredict(_Base):
    name, variant = "alg1_variation", "table_predict"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = table_rows(problem)
            xs, ys = [int(v) for v in xs], [Fraction(v) for v in ys]
            target = int(self.search(r"when \$x = (\d+)\$", problem)[1])
            if len({y / x for x, y in zip(xs, ys)}) == 1:
                expected = ys[0] / xs[0] * target
            else:
                products = {x * y for x, y in zip(xs, ys)}
                self.assertEqual(len(products), 1, problem)
                expected = products.pop() / target
            self.assertEqual(frac(solution), expected, problem)


class VariationWorkers(_Base):
    name, variant = "alg1_variation", "workers"

    def test(self):
        for problem, solution in self.samples():
            w1, d1, w2 = map(int, self.search(r"\$(\d+)\$ workers can paint a building in \$(\d+)\$ days.*"
                                              r"would \$(\d+)\$ workers", problem).groups())
            self.assertEqual(int(solution) * w2, w1 * d1, problem)


class RationalHole(_Base):
    name, variant = "alg1_simplify_rational", "hole"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{([^}]+)\}\{([^}]+)\}", problem)
            top, bottom = roots_of(*quadratic(m[1])), roots_of(*quadratic(m[2]))
            common = set(top) & set(bottom)
            self.assertEqual(common, {Fraction(solution)}, problem)


class AbsInequalityCount(_Base):
    name, variant = "alg1_abs_value_inequality", "count_integers"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$\|([^|]+)\| (<|\\leq) (\d+)\$", problem)
            (a, b), op, c = linear(m[1]), m[2], int(m[3])
            count = sum(1 for x in range(-300, 301) if (abs(a * x + b) < c if op == "<" else abs(a * x + b) <= c))
            self.assertEqual(int(solution), count, problem)


class AbsInequalityTolerance(_Base):
    name, variant = "alg1_abs_value_inequality", "tolerance"

    def test(self):
        for problem, solution in self.samples():
            target, tol = map(int, self.search(r"\$\|T - (\d+)\| \\leq (\d+)\$", problem).groups())
            allowed = [t for t in range(0, 200) if abs(t - target) <= tol]
            want = min(allowed) if "lowest" in problem else max(allowed)
            self.assertEqual(int(solution), want, problem)


class RadicalMissingRadicand(_Base):
    name, variant = "alg1_simplify_radical", "missing_radicand"

    def test(self):
        for problem, solution in self.samples():
            n, a = map(int, self.search(r"\\sqrt\{(\d+)\} = (\d+)\\sqrt", problem).groups())
            self.assertEqual(a * a * int(solution), n, problem)


class RadicalMoveInside(_Base):
    name, variant = "alg1_simplify_radical", "move_inside"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"If \$(\d+)\\sqrt\{(\d+)\}", problem).groups())
            self.assertEqual(int(solution), a * a * b, problem)


class NegativeExponentFractionBase(_Base):
    name, variant = "alg1_negative_exponent", "fraction_base"

    def test(self):
        for problem, solution in self.samples():
            p, q, n = map(int, self.search(r"\\frac\{(\d+)\}\{(\d+)\}\\right\)\^\{-(\d+)\}", problem).groups())
            self.assertEqual(frac(solution), Fraction(p, q) ** -n, problem)


class GrowthFactorFromTable(_Base):
    name, variant = "alg1_exponential_growth_decay", "factor_from_table"

    def test(self):
        for problem, solution in self.samples():
            _, ys = table_rows(problem)
            ys = [Fraction(v) for v in ys]
            ratios = {ys[i + 1] / ys[i] for i in range(len(ys) - 1)}
            self.assertEqual(ratios, {frac(solution)}, problem)


class GrowthHalfLife(_Base):
    name, variant = "alg1_exponential_growth_decay", "half_life"

    def test(self):
        for problem, solution in self.samples():
            period = int(self.search(r"half-life of \$(\d+)\$ years", problem)[1])
            elapsed = int(self.search(r"after \$(\d+)\$ years", problem)[1])
            start = re.search(r"A \$(\d+)\$-gram sample", problem)
            amount = Fraction(int(start[1]) if start else 1) * Fraction(1, 2) ** (elapsed // period)
            self.assertEqual(elapsed % period, 0)
            self.assertEqual(frac(solution), amount, problem)


class ExponentialReadParameters(_Base):
    name, variant = "alg1_evaluate_exponential", "read_parameters"

    def test(self):
        for problem, solution in self.samples():
            pts = [tuple(map(int, p)) for p in re.findall(r"\$f\((\d+)\) = (\d+)\$", problem)]
            want = self.search(r"What is \$(a|b)\$", problem)[1]
            fits = [(a, b) for a in range(1, 50) for b in range(2, 10)
                    if all(a * b ** x == y for x, y in pts)]
            self.assertEqual(len(fits), 1, problem)
            a, b = fits[0]
            self.assertEqual(int(solution), a if want == "a" else b, problem)


class DomainCountExcluded(_Base):
    name, variant = "alg1_domain_of_function", "count_excluded"

    def test(self):
        for problem, solution in self.samples():
            lo, hi, k2 = map(int, self.search(r"from \$" + INT + r"\$ to \$" + INT
                                              + r"\$ are not in the domain of .*x\^2 - (\d+)\}", problem).groups())
            self.assertEqual(int(solution), sum(1 for x in range(lo, hi + 1) if x * x == k2), problem)
