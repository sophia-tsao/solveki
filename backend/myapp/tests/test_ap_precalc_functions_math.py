"""Math-correctness tests for the AP Precalculus Units 1-2 generators.

Each test parses the generated problem, recomputes the answer independently
(finite differences, Lagrange interpolation, logarithms, ...), and asserts the
stated solution matches, over many random samples under a fixed seed.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import ap_precalc_functions  # noqa: F401  (registers generators)
from myapp.generators import LOCAL_GENERATORS
from myapp.generators._variants import classic

SAMPLES = 2000

_TABLE = re.compile(r"\\begin\{array\}\{[^}]*\} (.*?) \\\\ \\hline (.*?) \\end\{array\}")
_FRAC = re.compile(r"(-?)\\frac\{(\d+)\}\{(\d+)\}")


def _table(problem):
    """The (xs, ys) rows of the problem's table as Fractions."""
    m = _TABLE.search(problem)
    rows = []
    for row in m.groups():
        rows.append([Fraction(cell.strip()) for cell in row.split("&")[1:]])
    return rows


def _diffs(values):
    return [b - a for a, b in zip(values, values[1:])]


def _value(tex):
    """A LaTeX number (``-3``, ``\\frac{1}{2}``, ``-\\frac{1}{2}``) as a Fraction."""
    tex = tex.strip()
    m = _FRAC.fullmatch(tex)
    if m:
        return Fraction(int(m.group(2)), int(m.group(3))) * (-1 if m.group(1) else 1)
    return Fraction(tex)


def _coef(tex):
    """A coefficient in front of a symbol: '' -> 1, '-' -> -1, else its value."""
    if tex == "":
        return Fraction(1)
    if tex == "-":
        return Fraction(-1)
    return _value(tex)


_TERM = re.compile(r"([+-]?)(\d*)(x(?:\^(\d+))?)?")


def _poly(text):
    """Parse ``3x^4 - 2x^2 + 5`` into ``{exponent: coefficient}``."""
    poly = {}
    for m in _TERM.finditer(text.replace(" ", "")):
        if not m.group(0) or (not m.group(2) and not m.group(3)):
            continue
        sign = -1 if m.group(1) == "-" else 1
        mag = int(m.group(2)) if m.group(2) else 1
        exp = (int(m.group(4)) if m.group(4) else 1) if m.group(3) else 0
        poly[exp] = poly.get(exp, 0) + sign * mag
    return poly


def _eval(poly, x):
    return sum(c * x ** e for e, c in poly.items())


def _lagrange(points, x):
    total = Fraction(0)
    for i, (xi, yi) in enumerate(points):
        term = Fraction(yi)
        for j, (xj, _) in enumerate(points):
            if i != j:
                term *= Fraction(x - xj, xi - xj)
        total += term
    return total


def _complex(text):
    """Parse ``3-4i`` / ``2+i`` / ``-5i`` / ``7`` into ``(a, b)``."""
    t = text.strip()
    if not t.endswith("i"):
        return int(t), 0
    m = re.fullmatch(r"(-?\d+)([+-])(\d*)i", t)
    if m:
        sign = 1 if m.group(2) == "+" else -1
        return int(m.group(1)), sign * (int(m.group(3)) if m.group(3) else 1)
    m = re.fullmatch(r"(-?)(\d*)i", t)
    return 0, (-1 if m.group(1) else 1) * (int(m.group(2)) if m.group(2) else 1)


def _half_up(value, places=3):
    """A Fraction rounded the way ``_format.num`` does (half away from zero)."""
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(value.numerator) / Decimal(value.denominator)
    text = f"{d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


class _Base(SimpleTestCase):
    name = None

    def samples(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS[self.name])
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            yield problem, solution.replace("$", "").strip()

    def close(self, stated, expected, problem):
        self.assertLessEqual(abs(float(stated) - expected), 0.0005 + 1e-9 * abs(expected),
                             msg=f"{problem!r} -> {stated!r}, expected {expected}")


class ChangeInTandemTests(_Base):
    name = "pc_change_in_tandem"

    def test_direction_and_concavity(self):
        for problem, solution in self.samples():
            _, ys = _table(problem)
            firsts = _diffs(ys)
            seconds = _diffs(firsts)
            self.assertTrue(all(d > 0 for d in firsts) or all(d < 0 for d in firsts))
            self.assertTrue(all(d > 0 for d in seconds) or all(d < 0 for d in seconds))
            expected = (f"{'increasing' if firsts[0] > 0 else 'decreasing'}, "
                        f"concave {'up' if seconds[0] > 0 else 'down'}")
            self.assertEqual(solution, expected, problem)


class SecondDifferencesTests(_Base):
    name = "pc_second_differences"

    def test_next_value_or_leading_coefficient(self):
        for problem, solution in self.samples():
            xs, ys = _table(problem)
            points = list(zip(xs, ys))
            # The table really is quadratic: the 4th point lies on the parabola
            # through the first three.
            self.assertEqual(_lagrange(points[:3], xs[3]), ys[3], problem)
            m = re.search(r"Find \$f\((-?\d+)\)\$", problem)
            if m:
                expected = _lagrange(points[:3], int(m.group(1)))
            else:
                h = xs[1] - xs[0]
                second = ys[2] - 2 * ys[1] + ys[0]
                expected = second / (2 * h * h)
            self.assertEqual(Fraction(solution), expected, problem)


class DegreeFromDifferencesTests(_Base):
    name = "pc_degree_from_differences"

    def test_degree(self):
        for problem, solution in self.samples():
            _, row = _table(problem)
            degree = 0
            while len(set(row)) > 1:
                row = _diffs(row)
                degree += 1
            self.assertNotEqual(row[0], 0)
            self.assertEqual(int(solution), degree, problem)


class ComplexConjugateZerosTests(_Base):
    name = "pc_complex_conjugate_zeros"

    def test_remaining_zero_or_min_degree(self):
        for problem, solution in self.samples():
            zeros = [_complex(z) for z in re.findall(r"\$x = ([^$]+)\$", problem)]
            nonreal = [z for z in zeros if z[1] != 0]
            reals = [z for z in zeros if z[1] == 0]
            if "remaining zero" in problem:
                degree = int(re.search(r"degree \$(\d+)\$", problem).group(1))
                self.assertEqual(len(nonreal), 1)
                self.assertEqual(len(zeros) + 1, degree)
                a, b = nonreal[0]
                self.assertEqual(_complex(solution), (a, -b), problem)
            else:
                pairs = {(a, abs(b)) for a, b in nonreal}
                self.assertEqual(int(solution), len(reals) + 2 * len(pairs), problem)


class EvenOddFunctionTests(_Base):
    name = "pc_even_odd_function"

    def test_symmetry(self):
        for problem, solution in self.samples():
            expr = re.search(r"f\(x\) = (.+?)\$ even", problem).group(1)
            m = re.fullmatch(r"\\frac\{(.+)\}\{(.+)\}", expr)
            if m:
                top, bot = _poly(m.group(1)), _poly(m.group(2))

                def f(x):
                    return _eval(top, x) / _eval(bot, x)
            else:
                p = _poly(expr)

                def f(x):
                    return _eval(p, x)
            pts = [Fraction(3, 2), Fraction(5, 2), Fraction(7, 3)]
            if all(f(-x) == f(x) for x in pts):
                expected = "even"
            elif all(f(-x) == -f(x) for x in pts):
                expected = "odd"
            else:
                expected = "neither"
            self.assertEqual(solution, expected, problem)


class FunctionTransformationTests(_Base):
    name = "pc_function_transformation"
    G = re.compile(r"g\(x\) = (?P<a>.*?)f\((?P<inner>.*)\)(?P<k>(?: [+-] \d+)?)\$")
    INNER = re.compile(r"(?P<b>[^x(]*)(?:\((?P<paren>[^)]*)\)|(?P<bare>x.*))")

    def test_point(self):
        for problem, solution in self.samples():
            x0, y0 = map(int, re.search(r"point \$\((-?\d+), (-?\d+)\)\$", problem).groups())
            g = self.G.search(problem)
            a = _coef(g.group("a"))
            k = int(g.group("k").replace(" ", "")) if g.group("k") else 0
            inner = self.INNER.fullmatch(g.group("inner"))
            b = _coef(inner.group("b"))
            shifted = inner.group("paren") or inner.group("bare")
            hm = re.fullmatch(r"x(?: ([+-]) (\d+))?", shifted)
            h = 0 if not hm.group(1) else (int(hm.group(2)) * (1 if hm.group(1) == "-" else -1))
            # Brute check: g(x) = a*f(b(x - h)) + k at the new x feeds f the value x0.
            sx, sy = re.fullmatch(r"\((\S+), (\S+)\)", solution).groups()
            x_new, y_new = Fraction(sx), Fraction(sy)
            self.assertEqual(b * (x_new - h), x0, problem)
            self.assertEqual(a * y0 + k, y_new, problem)


class IdentifyModelTests(_Base):
    name = "pc_identify_model"

    def test_model(self):
        for problem, solution in self.samples():
            _, ys = _table(problem)
            firsts = _diffs(ys)
            if len(set(firsts)) == 1:
                expected = "linear"
            elif len(set(_diffs(firsts))) == 1:
                expected = "quadratic"
            else:
                self.assertNotIn(0, ys)
                self.assertEqual(len({b / a for a, b in zip(ys, ys[1:])}), 1, problem)
                expected = "exponential"
            self.assertEqual(solution, expected, problem)


class QuadraticModelPredictTests(_Base):
    name = "pc_quadratic_model_predict"

    def test_prediction(self):
        for problem, solution in self.samples():
            xs, ys = _table(problem)
            target = int(re.search(r"predict \$\w\((\d+)\)\$", problem).group(1))
            self.assertEqual(Fraction(solution), _lagrange(list(zip(xs, ys)), target), problem)


class ExponentialFromTwoPointsTests(_Base):
    name = "pc_exponential_from_two_points"

    def test_parameters(self):
        for problem, solution in self.samples():
            (x1, y1), (x2, y2) = [tuple(map(int, p)) for p in
                                  re.findall(r"\$\((-?\d+), (-?\d+)\)\$", problem)]
            b = (y2 / y1) ** (1 / (x2 - x1))
            a = y1 / b ** x1
            if "Find $b$" in problem:
                expected = b
            elif "Find $a$" in problem:
                expected = a
            else:
                x3 = int(re.search(r"Find \$f\((-?\d+)\)\$", problem).group(1))
                expected = a * b ** x3
            self.assertAlmostEqual(float(Fraction(solution)), expected, places=6, msg=problem)


class RewriteExponentialTests(_Base):
    name = "pc_rewrite_exponential"

    def test_rewrite(self):
        for problem, solution in self.samples():
            value = float(Fraction(solution))
            m = re.search(r"\$(\d+) \\cdot (\d+)\^\{x ([+-]) (\d+)\}\$", problem)
            if m:
                c, b, n = int(m.group(1)), int(m.group(2)), int(m.group(4))
                n = n if m.group(3) == "+" else -n
                # c*b^(x+n) == value*b^x at a couple of x.
                for x in (0.5, 2.0):
                    self.assertAlmostEqual(c * b ** (x + n), value * b ** x, places=6, msg=problem)
                continue
            m = re.search(r"\$\d+ \\cdot (\d+)\^\{\\frac\{x\}\{(\d+)\}\}\$", problem)
            if m:
                big, root = int(m.group(1)), int(m.group(2))
                self.assertAlmostEqual(value, big ** (1 / root), places=6, msg=problem)
                continue
            m = re.search(r"Rewrite \$(\d+)\^\{(-?\d*)x\}\$", problem)
            b, k = int(m.group(1)), _coef(m.group(2))
            self.assertAlmostEqual(value, b ** float(k), places=6, msg=problem)


class ResidualTests(_Base):
    name = "pc_residual"

    def test_residual(self):
        for problem, solution in self.samples():
            x, y = re.search(r"point \$\((-?\d+), (-?[\d.]+)\)\$", problem).groups()
            x, y = int(x), Fraction(y)
            lin = re.search(r"\\hat\{y\} = (-?[\d.]*)x \+ (\d+)\$", problem)
            if lin:
                m = _coef(lin.group(1)) if lin.group(1) in ("", "-") else Fraction(lin.group(1))
                predicted = m * x + int(lin.group(2))
                self.assertEqual(Fraction(solution), y - predicted, problem)
            else:
                a, r = re.search(r"\\hat\{y\} = (\d+)\(([\d.]+)\)\^\{x\}", problem).groups()
                predicted = int(a) * Fraction(r) ** x
                self.assertEqual(solution, _half_up(y - predicted), problem)


class InverseExponentialTests(_Base):
    name = "pc_inverse_exponential"
    F = re.compile(r"f\(x\) = (?:(\d+) \\cdot )?(\d+)\^\{x\}(?: ([+-]) (\d+))?\$. "
                   r"Find \$f\^\{-1\}\((-?\d+)\)\$")

    def test_inverse(self):
        for problem, solution in self.samples():
            a, b, sign, k, v = self.F.search(problem).groups()
            a, b, v = int(a or 1), int(b), int(v)
            k = (int(k) if sign == "+" else -int(k)) if k else 0
            expected = math.log((v - k) / a, b)
            self.assertAlmostEqual(int(solution), expected, places=9, msg=problem)
            self.assertEqual(a * b ** int(solution) + k, v, problem)


class LogFunctionFeaturesTests(_Base):
    name = "pc_log_function_features"
    F = re.compile(r"f\(x\) = (?P<a>-?\d*)\\log_\{(?P<b>\d+)\}\(x(?: (?P<hs>[+-]) (?P<h>\d+))?\)"
                   r"(?: (?P<ks>[+-]) (?P<k>\d+))?\$")

    def test_features(self):
        for problem, solution in self.samples():
            m = self.F.search(problem)
            a = _coef(m.group("a"))
            b = int(m.group("b"))
            h = (int(m.group("h")) * (1 if m.group("hs") == "-" else -1)) if m.group("h") else 0
            k = (int(m.group("k")) * (1 if m.group("ks") == "+" else -1)) if m.group("k") else 0
            if "vertical asymptote" in problem:
                self.assertEqual(solution, f"x = {h}", problem)
            elif "domain" in problem:
                self.assertEqual(solution, f"x > {h}", problem)
            else:
                x = Fraction(solution)
                self.assertGreater(x, h)
                self.assertAlmostEqual(float(a) * math.log(float(x - h), b) + k, 0, places=9,
                                       msg=problem)


class SolveLogEquationTests(_Base):
    name = "pc_solve_log_equation"
    LOG = re.compile(r"\\log_\{(\d+)\}\(x(?: ([+-]) (\d+))?\)")

    def test_solution_checks(self):
        for problem, solution in self.samples():
            equation = re.search(r"Solve \$(.+)\$ for", problem).group(1)
            lhs, rhs = equation.rsplit(" = ", 1)
            logs = [(int(b), (int(c) if s == "+" else -int(c)) if c else 0)
                    for b, s, c in self.LOG.findall(lhs)]
            x = int(solution)

            def side(xv):
                vals = [math.log(xv + c, b) for b, c in logs]
                return vals[0] + vals[1] if " + \\log" in lhs else (
                    vals[0] - vals[1] if " - \\log" in lhs else vals[0])
            self.assertTrue(all(x + c > 0 for _, c in logs), problem)
            self.assertAlmostEqual(side(x), int(rhs), places=9, msg=problem)
            # Uniqueness: the valid solution set is a single integer, so check
            # no other integer in range also works (catches unrejected roots).
            for other in range(-150, 150):
                if other != x and all(other + c > 0 for _, c in logs):
                    self.assertNotAlmostEqual(side(other), int(rhs), places=9, msg=problem)


class ExpLogInequalityTests(_Base):
    name = "pc_exp_log_inequality"
    REL = {r">": ">", r"\ge": ">=", "<": "<", r"\le": "<="}

    @staticmethod
    def _holds(lhs, rel, rhs):
        return {">": lhs > rhs, ">=": lhs >= rhs, "<": lhs < rhs, "<=": lhs <= rhs}[rel]

    def _satisfies(self, solution, x):
        parts = solution.split()
        if len(parts) == 3:
            return self._holds(x, parts[1], int(parts[2]))
        lo, _, _, rel, hi = parts
        return x > int(lo) and self._holds(x, rel, int(hi))

    def test_solution_set(self):
        for problem, solution in self.samples():
            ineq = re.search(r"Solve \$(.+?)\$\.", problem).group(1)
            m = re.fullmatch(r"(.+) (>|<|\\ge|\\le) (-?\d+)", ineq)
            lhs, rel, rhs = m.group(1), self.REL[m.group(2)], int(m.group(3))
            em = re.fullmatch(r"(\d+)\^\{x(?: ([+-]) (\d+))?\}", lhs)
            rm = re.fullmatch(r"\\left\(\\frac\{1\}\{(\d+)\}\\right\)\^\{x\}", lhs)
            lm = re.fullmatch(r"\\log_\{(\d+)\}\(x(?: ([+-]) (\d+))?\)", lhs)
            if em:
                b = int(em.group(1))
                c = (int(em.group(3)) * (1 if em.group(2) == "-" else -1)) if em.group(3) else 0

                def value(x):
                    return Fraction(b) ** (x - c)
            elif rm:
                b = int(rm.group(1))

                def value(x):
                    return Fraction(1, b) ** x
            else:
                b = int(lm.group(1))
                c = (int(lm.group(3)) * (1 if lm.group(2) == "-" else -1)) if lm.group(3) else 0

                def value(x, b=b, c=c):
                    # Compare log_b(x - c) with rhs exactly: x - c vs b^rhs.
                    return None if x - c <= 0 else x - c
                rhs = b ** rhs
            # Test on a grid of halves around the boundary.
            for twice in range(-600, 600):
                x = Fraction(twice, 2)
                v = value(x)
                truth = v is not None and self._holds(v, rel, rhs)
                self.assertEqual(self._satisfies(solution, x), truth,
                                 f"{problem!r} -> {solution!r} at x={x}")


class LogModelContextTests(_Base):
    name = "pc_log_model_context"
    SCI = r"(?:([\d.]+) \\times )?10\^\{-(\d+)\}"

    def test_values(self):
        for problem, solution in self.samples():
            if "pH" in problem:
                m = re.search(r"\[\\text\{H\}\^\+\] = " + self.SCI + r"\$", problem)
                expected = -math.log10(float(m.group(1) or 1) * 10 ** -int(m.group(2)))
            elif "intensity $I = " in problem:
                m = re.search(r"\$I = " + self.SCI + r"\$", problem)
                intensity = float(m.group(1) or 1) * 10 ** -int(m.group(2))
                expected = 10 * math.log10(intensity / 1e-12)
            elif "decibels louder" in problem:
                d = int(re.search(r"\$(\d+)\$ decibels louder", problem).group(1))
                expected = 10 ** (d / 10)
            else:
                m1, m2 = map(float, re.findall(r"magnitude \$([\d.]+)\$", problem))
                expected = 10 ** (m1 - m2)
            self.close(solution, expected, problem)


class SemilogModelTests(_Base):
    name = "pc_semilog_model"

    def test_parameter(self):
        for problem, solution in self.samples():
            m = re.search(r"equation \$(\\ln y|\\log_\{10\} y) = (-?[\d.]+)x \+ ([\d.]+)\$",
                          problem)
            base = math.e if m.group(1) == r"\ln y" else 10
            slope, intercept = float(m.group(2)), float(m.group(3))
            expected = base ** intercept if "Find $a$" in problem else base ** slope
            self.close(solution, expected, problem)
