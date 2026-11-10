"""Math-correctness tests for the Precalculus variants (precalculus_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently (numerically or by brute force), and checks the served solution,
over 2000 seeded samples.
"""
import cmath
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators import precalculus_variants  # noqa: F401 - attaches the variants
from myapp.tests.test_prealgebra_variants_math import INT, frac

SAMPLES = 2000
TOL = 0.0005 + 1e-9
NUM = r"(-?\d+(?:\.\d+)?)"
FRAC = r"(-?\d+(?:/\d+)?)"


def linear_roots(text):
    out = []
    for sign, mag in re.findall(r"\(x ([+-]) (\d+)\)", text):
        out.append(int(mag) if sign == "-" else -int(mag))
    return out


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

    def close(self, solution, value, problem):
        self.assertAlmostEqual(float(solution), float(value), delta=TOL, msg=problem)


class SinesAmbiguousCase(_Base):
    name, variant = "pc_law_of_sines", "ambiguous_case"

    def test(self):
        seen = set()
        for problem, solution in self.samples():
            A, a, b = map(int, self.search(r"angle \$A = (\d+)\^\\circ\$, side \$a = (\d+)\$.*side \$b = (\d+)\$",
                                           problem).groups())
            # Solve sin B = b sin A / a and count valid B values.
            sb = b * math.sin(math.radians(A)) / a
            count = 0
            if sb <= 1:
                for B in {math.degrees(math.asin(sb)), 180 - math.degrees(math.asin(sb))}:
                    if A + B < 180 - 1e-9 and B > 1e-9:
                        count += 1
            self.assertEqual(int(solution), count, problem)
            seen.add(count)
        self.assertEqual(seen, {0, 1, 2})


class CosinesAngleFromSides(_Base):
    name, variant = "pc_law_of_cosines_side", "angle_from_sides"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = map(int, self.search(r"\$a = (\d+)\$, \$b = (\d+)\$, and \$c = (\d+)\$", problem).groups())
            # Place the triangle: C at the origin, B on the x-axis; find A by intersecting circles.
            x = (b * b + a * a - c * c) / (2 * a)
            y = math.sqrt(max(0, b * b - x * x))
            self.close(solution, math.degrees(math.atan2(y, x)), problem)


class ObliqueSideFromArea(_Base):
    name, variant = "pc_oblique_triangle_area", "side_from_area"

    def test(self):
        for problem, solution in self.samples():
            a, C, area = self.search(r"sides \$a = (\d+)\$ and \$b\$ with included angle \$C = (\d+)\^\\circ\$\. Its area is "
                                     r"\$" + NUM + r"\$", problem).groups()
            b = int(solution)
            self.assertAlmostEqual(0.5 * int(a) * b * math.sin(math.radians(int(C))), float(area), places=9)


class InverseRangeRestriction(_Base):
    name, variant = "pc_inverse_trig", "range_restriction"

    def test(self):
        f = {"sin": (math.sin, math.asin), "cos": (math.cos, math.acos), "tan": (math.tan, math.atan)}
        for problem, solution in self.samples():
            kind, t = self.search(r"\\arc(sin|cos|tan)\(\\\w+ (\d+)\^\\circ\)", problem).groups()
            fwd, inv = f[kind]
            self.assertAlmostEqual(math.degrees(inv(fwd(math.radians(int(t))))), int(solution), places=6)


class DoubleAngleRecognize(_Base):
    name, variant = "pc_double_angle", "recognize_identity"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"2\\sin " + NUM + r"\^\\circ \\cos", problem)
            if m:
                t = math.radians(float(m[1]))
                value = 2 * math.sin(t) * math.cos(t)
            else:
                t = math.radians(float(self.search(r"\\cos\^2 " + NUM, problem)[1]))
                value = math.cos(t) ** 2 - math.sin(t) ** 2
            self.assertAlmostEqual(float(frac(solution)), value, places=9, msg=problem)


class SumDifferenceRecognize(_Base):
    name, variant = "pc_sum_difference_values", "recognize_identity"

    def test(self):
        for problem, solution in self.samples():
            expr = self.search(r"Evaluate \$([^$]+)\$", problem)[1]
            py = re.sub(r"\\(sin|cos) (\d+)\^\\circ", lambda m: f"math.{m[1]}(math.radians({m[2]}))", expr)
            py = py.replace(" ", "").replace(")math", ")*math")
            value = eval(py, {"math": math})  # noqa: S307 - test-only, generated input
            self.assertAlmostEqual(float(frac(solution)), value, places=9, msg=problem)


class HalfAngleExact(_Base):
    name, variant = "pc_half_angle_values", "exact_from_triple"

    def test(self):
        for problem, solution in self.samples():
            c = float(frac(self.search(r"\\cos\\theta = " + FRAC + r"\$", problem)[1]))
            theta = math.acos(c)
            func = self.search(r"Find \$\\(sin|cos)\\frac", problem)[1]
            value = math.sin(theta / 2) if func == "sin" else math.cos(theta / 2)
            self.assertAlmostEqual(float(frac(solution)), value, places=9, msg=problem)


class TrigCountSolutions(_Base):
    name, variant = "pc_solve_trig_equation", "count_solutions"
    VALUES = {"1": 1, "-1": -1, r"\sqrt{3}": math.sqrt(3), "0": 0, r"\frac{1}{2}": 0.5, r"-\frac{1}{2}": -0.5,
              r"\frac{\sqrt{2}}{2}": math.sqrt(2) / 2}

    def test(self):
        for problem, solution in self.samples():
            func, k, v = self.search(r"\$\\(sin|cos|tan)\((\d*)x\) = (.+?)\$ have", problem).groups()
            k = int(k or 1)
            target = self.VALUES[v]
            f = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[func]
            # List every solution u = kx in [0, 360k) from the inverse function, then count distinct x.
            if func == "sin":
                base = [math.asin(target), math.pi - math.asin(target)]
                period = 2 * math.pi
            elif func == "cos":
                base = [math.acos(target), -math.acos(target)]
                period = 2 * math.pi
            else:
                base = [math.atan(target)]
                period = math.pi
            xs = set()
            for u0 in base:
                for n in range(-2 * k - 2, 2 * k + 3):
                    x = (u0 + n * period) / k
                    if -1e-9 <= x < 2 * math.pi - 1e-9:
                        xs.add(round(x, 9))
            count = len(xs)
            self.assertEqual(int(solution), count, problem)


class PolarNegativeRadius(_Base):
    name, variant = "pc_polar_to_rectangular", "negative_radius"

    def test(self):
        for problem, solution in self.samples():
            r, t = map(int, self.search(r"\(r, \\theta\) = \(" + INT + r", (\d+)\^\\circ\)", problem).groups())
            z = cmath.rect(r, math.radians(t))
            x, y = map(float, re.fullmatch(r"\((-?[\d.]+), (-?[\d.]+)\)", solution).groups())
            self.assertAlmostEqual(x, z.real, delta=TOL)
            self.assertAlmostEqual(y, z.imag, delta=TOL)


class RectangularAngleByQuadrant(_Base):
    name, variant = "pc_rectangular_to_polar", "angle_by_quadrant"

    def test(self):
        for problem, solution in self.samples():
            x, y = map(int, self.search(r"point \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            self.close(solution, math.degrees(cmath.phase(complex(x, y))) % 360, problem)


class PolarCircleRadius(_Base):
    name, variant = "pc_polar_rectangular_equation", "circle_radius"

    def test(self):
        for problem, solution in self.samples():
            a, func = self.search(r"\$r = " + INT + r"\\(sin|cos)\\theta\$", problem).groups()
            a = int(a)
            # Sample the curve and measure its diameter (greatest distance between points).
            pts = [(a * (math.sin if func == "sin" else math.cos)(t) * math.cos(t),
                    a * (math.sin if func == "sin" else math.cos)(t) * math.sin(t))
                   for t in [i * math.pi / 360 for i in range(720)]]
            diam = max(math.dist(pts[0], p) for p in pts)
            diam = max(diam, max(math.dist(pts[180], p) for p in pts))
            self.assertAlmostEqual(float(solution) * 2, diam, delta=0.01)


class GeometricNumberOfTerms(_Base):
    name, variant = "pc_finite_geometric_sum", "number_of_terms"

    def test(self):
        for problem, solution in self.samples():
            a, r, total = map(int, self.search(r"first term \$" + INT + r"\$ and common ratio \$" + INT
                                               + r"\$\. How many terms add up to \$" + INT, problem).groups())
            ns = [n for n in range(1, 30) if sum(a * r ** i for i in range(n)) == total]
            self.assertEqual(ns[:1], [int(solution)], problem)


class SigmaUpperLimit(_Base):
    name, variant = "pc_sigma_arithmetic_sum", "upper_limit"

    def test(self):
        for problem, solution in self.samples():
            A, sign, B, total = self.search(r"\((\d+)k ([+-]) (\d+)\) = " + INT, problem).groups()
            B = int(B) * (1 if sign == "+" else -1)
            ns = [n for n in range(1, 60) if sum(int(A) * k + B for k in range(1, n + 1)) == int(total)]
            self.assertIn(int(solution), ns, problem)


class RecursiveLongRun(_Base):
    name, variant = "pc_recursive_sequence_term", "long_run"

    def test(self):
        for problem, solution in self.samples():
            a1 = int(self.search(r"\$a_1 = " + INT, problem)[1])
            m = self.search(r"a_n = (-?\\frac\{\d+\}\{\d+\}|-?\d+)a_\{n-1\} ([+-]) (\d+)\$", problem)
            r = frac(m[1])
            d = int(m[3]) * (1 if m[2] == "+" else -1)
            x = float(a1)
            for _ in range(2000):
                x = float(r) * x + d
            self.assertAlmostEqual(float(frac(solution)), x, places=6, msg=problem)


class SequenceLimitProduct(_Base):
    name, variant = "pc_sequence_limit", "product_form"

    def test(self):
        for problem, solution in self.samples():
            expr = self.search(r"\\frac\{(.+)\}\{(.+)\}\$\. Express", problem)
            top = expr[1].replace("n", "*n").replace("(*n", "(n").replace("-*n", "-n").replace(")(", ")*(")
            bottom = expr[2].replace("n^2", "*n**2").replace("n", "*n").replace("**n", "*n")
            bottom = re.sub(r"^\*", "", bottom).replace("-*", "-").replace("(*", "(").replace("**2", "^2").replace("^2", "**2")
            n = 1e7
            value = eval(top, {"n": n}) / eval(bottom, {"n": n})  # noqa: S307
            self.assertAlmostEqual(float(frac(solution)), value, delta=1e-4, msg=problem)


class VectorBoat(_Base):
    name, variant = "pc_vector_add", "boat_in_current"

    def test(self):
        for problem, solution in self.samples():
            b, c = map(int, self.search(r"at \$(\d+)\$ km/h relative to the water, while the current flows at \$(\d+)\$",
                                        problem).groups())
            self.close(solution, abs(complex(b, c)), problem)


class ProjectionComponent(_Base):
    name, variant = "pc_orthogonal_projection", "projection_component"

    def test(self):
        for problem, solution in self.samples():
            a = tuple(map(int, self.search(r"\\vec a = \\langle " + INT + ", " + INT, problem).groups()))
            b = tuple(map(int, self.search(r"\\vec b = \\langle " + INT + ", " + INT, problem).groups()))
            which = 0 if "first component" in problem else 1
            # Projection = the point on the line through b closest to a.
            t = (a[0] * b[0] + a[1] * b[1]) / (b[0] ** 2 + b[1] ** 2)
            self.assertAlmostEqual(float(frac(solution)), t * b[which], places=9, msg=problem)


class ParametricSlope(_Base):
    name, variant = "pc_parametric_to_rectangular", "slope_only"

    def test(self):
        for problem, solution in self.samples():
            a, sb, b, c, sd, d = self.search(r"\$x = " + INT + r"t ([+-]) (\d+)\$ and \$y = " + INT + r"t ([+-]) (\d+)\$",
                                             problem).groups()
            x = lambda t: int(a) * t + int(b) * (1 if sb == "+" else -1)  # noqa: E731
            y = lambda t: int(c) * t + int(d) * (1 if sd == "+" else -1)  # noqa: E731
            self.assertEqual(frac(solution), Fraction(y(1) - y(0), x(1) - x(0)), problem)


def quadrant_of(x, y):
    return {(True, True): "I", (False, True): "II", (False, False): "III", (True, False): "IV"}[(x > 0, y > 0)]


class UnitCircleOther(_Base):
    def test(self):
        for name, variant, ask in (("pc_unit_circle_cos", "from_sine_and_quadrant", "cos"),
                                   ("pc_unit_circle_sin", "from_cosine_and_quadrant", "sin"),
                                   ("pc_unit_circle_tan", "from_sine_and_quadrant", "tan")):
            self.variant = variant
            for problem, solution in self.samples(name):
                quad, gname, given = self.search(r"quadrant (I|II|III|IV) has \$\\(sin|cos)\\theta = " + FRAC, problem).groups()
                g = float(frac(given))
                other = math.sqrt(1 - g * g)
                angles = [math.atan2(g, other), math.atan2(g, -other)] if gname == "sin" else \
                    [math.atan2(other, g), math.atan2(-other, g)]
                theta = [t for t in angles if quadrant_of(math.cos(t), math.sin(t)) == quad][0]
                value = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[ask](theta)
                self.assertAlmostEqual(float(frac(solution)), value, places=9, msg=problem)


class UnitCirclePointFromOne(_Base):
    name, variant = "pc_unit_circle_point", "from_one_coordinate"

    def test(self):
        for problem, solution in self.samples():
            quad, axis, v = self.search(r"quadrant (I|II|III|IV) has (x|y)-coordinate \$" + FRAC, problem).groups()
            x, y = map(float, re.fullmatch(r"\((-?[\d.]+), (-?[\d.]+)\)", solution).groups())
            self.assertAlmostEqual(x * x + y * y, 1, delta=0.002)
            self.assertEqual(quadrant_of(x, y), quad, problem)
            self.assertAlmostEqual(x if axis == "x" else y, float(frac(v)), delta=TOL)


class ReciprocalFromSecant(_Base):
    name, variant = "pc_reciprocal_trig_values", "from_secant"

    def test(self):
        for problem, solution in self.samples():
            quad, sec = self.search(r"quadrant (I|II|III|IV) has \$\\sec\\theta = " + FRAC, problem).groups()
            c = 1 / float(frac(sec))
            s = math.sqrt(1 - c * c) * (1 if quad in ("I", "II") else -1)
            self.assertAlmostEqual(float(frac(solution)), s, places=9, msg=problem)


class TrigSumToProduct(_Base):
    name, variant = "pc_simplify_trig_identity", "sum_to_product"

    def test(self):
        for problem, solution in self.samples():
            sign, s_val = self.search(r"\$\\sin x ([+-]) \\cos x = " + FRAC + r"\$", problem).groups()
            target = float(frac(s_val))
            f = (lambda x: math.sin(x) + math.cos(x)) if sign == "+" else (lambda x: math.sin(x) - math.cos(x))
            # Find an x with f(x) = target by bisection on [-pi/4, 3pi/4] (f is monotone there for '-').
            lo, hi = (-math.pi / 4, 3 * math.pi / 4) if sign == "-" else (math.pi / 4, 5 * math.pi / 4)
            for _ in range(200):
                mid = (lo + hi) / 2
                if (f(mid) - target) * (f(lo) - target) <= 0:
                    hi = mid
                else:
                    lo = mid
            x = (lo + hi) / 2
            self.assertAlmostEqual(float(frac(solution)), math.sin(x) * math.cos(x), places=6, msg=problem)


class VaCoefficient(_Base):
    name, variant = "pc_rational_vertical_asymptotes", "coefficient_for_asymptote"

    def test(self):
        for problem, solution in self.samples():
            c_sign, c_mag = self.search(r"x\^2 \+ bx ([+-]) (\d+)\}", problem).groups()
            r = int(self.search(r"asymptote at \$x = " + INT, problem)[1])
            c = int(c_mag) * (1 if c_sign == "+" else -1)
            b = int(solution)
            self.assertEqual(r * r + b * r + c, 0, problem)
            num_roots = linear_roots(self.search(r"\\frac\{([^}]+)\}", problem)[1])
            self.assertNotIn(r, num_roots)


class ZerosCount(_Base):
    name, variant = "pc_rational_zeros", "count_after_cancelling"

    def test(self):
        for problem, solution in self.samples():
            top, bottom = self.search(r"\\frac\{(.*?)\}\{(.*?)\}\$", problem).groups()
            tr = re.findall(r"\(x ([+-]) (\d+)\)|(?<![(\w])x(?![\w])", top)
            roots_t = [(int(m[1]) if m[0] == "-" else -int(m[1])) if m[0] else 0 for m in tr]
            br = re.findall(r"\(x ([+-]) (\d+)\)|(?<![(\w])x(?![\w])", bottom)
            roots_b = [(int(m[1]) if m[0] == "-" else -int(m[1])) if m[0] else 0 for m in br]
            zeros = [r for r in roots_t if r not in roots_b]
            self.assertEqual(int(solution), len(set(zeros)), problem)


class HolesCoefficient(_Base):
    name, variant = "pc_rational_holes", "coefficient_for_hole"

    def test(self):
        for problem, solution in self.samples():
            sign, m = self.search(r"x\^2 \+ kx ([+-]) (\d+)\}", problem).groups()
            m = int(m) * (1 if sign == "+" else -1)
            r = linear_roots(self.search(r"\}\{([^}]+)\}\$", problem)[1])[0]
            k = int(solution)
            self.assertEqual(r * r + k * r + m, 0, problem)


class HaCoefficient(_Base):
    name, variant = "pc_rational_horizontal_asymptote", "coefficient_for_asymptote"

    def test(self):
        for problem, solution in self.samples():
            lead = self.search(r"\{(-?\d*)x\^2 - 4\}", problem)[1]
            c = {"": 1, "-": -1}.get(lead) if lead in ("", "-") else int(lead)
            h = frac(self.search(r"asymptote \$y = ([^$]+)\$", problem)[1])
            x = 1e8
            self.assertAlmostEqual((int(solution) * x * x + 1) / (c * x * x - 4), float(h), places=6, msg=problem)


class SlantIntercept(_Base):
    name, variant = "pc_rational_slant_asymptote", "asymptote_intercept"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{(-?\d*)x\^2 ([+-]) (\d+)x ([+-]) (\d+)\}\{\(x ([+-]) (\d+)\)\}", problem)
            a = {"": 1, "-": -1}.get(m[1]) if m[1] in ("", "-") else int(m[1])
            b = int(m[3]) * (1 if m[2] == "+" else -1)
            c = int(m[5]) * (1 if m[4] == "+" else -1)
            p = int(m[7]) if m[6] == "-" else -int(m[7])
            f = lambda x: (a * x * x + b * x + c) / (x - p)  # noqa: E731
            # For large x, f(x) - a x approaches the asymptote's intercept.
            x = 1e7
            self.assertAlmostEqual(f(x) - a * x, int(solution), delta=1e-4, msg=problem)


class YInterceptCoefficient(_Base):
    name, variant = "pc_rational_y_intercept", "coefficient_from_intercept"

    def test(self):
        for problem, solution in self.samples():
            top, bottom = self.search(r"\\frac\{a([^}]+)\}\{([^}]+)\}", problem).groups()
            y0 = frac(self.search(r"y-intercept \$([^$]+)\$", problem)[1])
            a = int(solution)
            value = Fraction(a) * math.prod(Fraction(-r) for r in linear_roots(top)) / math.prod(
                Fraction(-r) for r in linear_roots(bottom))
            self.assertEqual(value, y0, problem)


class RationalInequalityCount(_Base):
    name, variant = "pc_rational_inequality", "count_integers"

    def test(self):
        for problem, solution in self.samples():
            top, bottom, op = self.search(r"\\frac\{([^}]+)\}\{([^}]+)\} (<|\\leq) 0", problem).groups()
            z = (linear_roots(top) or [0])[0]
            p = (linear_roots(bottom) or [0])[0]
            ok = [x for x in range(-100, 101) if x != p and (Fraction(x - z, x - p) < 0 or (op == "\\leq" and x == z))]
            self.assertEqual(int(solution), len(ok), problem)


class SinusoidFromMaxMin(_Base):
    name, variant = "pc_sinusoid_features", "from_max_min"

    def test(self):
        for problem, solution in self.samples():
            hi, lo = map(int, self.search(r"maximum value of \$" + INT + r"\$ and a minimum value of \$" + INT, problem).groups())
            # y = A sin(x) + D with A, D from max/min: check the extremes of the curve.
            if "amplitude" in problem:
                A = int(solution)
                D = hi - A
                self.assertEqual(D - A, lo, problem)
            else:
                D = int(re.fullmatch(r"y = (-?\d+)", solution)[1])
                self.assertEqual(hi - D, D - lo, problem)


class BinomialConstantTerm(_Base):
    name, variant = "pc_binomial_term", "constant_term"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\left\(x \+ \\frac\{(\d+)\}\{x\}\\right\)\^\{(\d+)\}", problem)
            c, n = int(m[1]), int(m[2])
            # Multiply out (x + c/x)^n as a Laurent polynomial {power: coefficient}.
            poly = {0: 1}
            for _ in range(n):
                new = {}
                for pw, co in poly.items():
                    new[pw + 1] = new.get(pw + 1, 0) + co
                    new[pw - 1] = new.get(pw - 1, 0) + co * c
                poly = new
            self.assertEqual(int(solution), poly.get(0, 0), problem)


class DeMoivreFirstReal(_Base):
    name, variant = "pc_de_moivre", "first_real_power"

    def test(self):
        for problem, solution in self.samples():
            r, t = map(int, self.search(r"z = (\d+)\(\\cos (\d+)\^\\circ", problem).groups())
            z = cmath.rect(r, math.radians(t))
            n = next(k for k in range(1, 400) if abs((z ** k).imag) < 1e-6 * abs(z ** k))
            self.assertEqual(int(solution), n, problem)


class PartialFractionSum(_Base):
    name, variant = "pc_partial_fractions", "sum_of_numerators"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{(-?\d+)x ([+-]) (\d+)\}\{([^}]+)\}", problem)
            num_coef, const = int(m[1]), int(m[3]) * (1 if m[2] == "+" else -1)
            p, q = linear_roots(m[4])
            A = Fraction(num_coef * p + const, p - q)
            B = Fraction(num_coef * q + const, q - p)
            self.assertEqual(int(solution), A + B, problem)


# --- Further variants ---------------------------------------------------------------

class SinesFindAngle(_Base):
    name, variant = "pc_law_of_sines", "find_angle"

    def test(self):
        for problem, solution in self.samples():
            A, a, b = map(int, self.search(r"angle \$A = (\d+)\^\\circ\$, side \$a = (\d+)\$, and side \$b = (\d+)\$", problem).groups())
            B = math.radians(float(solution))
            self.assertAlmostEqual(a / math.sin(math.radians(A)), b / math.sin(B), delta=0.01 * a)
            self.assertLess(float(solution), 90)


class SinesRiverWidth(_Base):
    name, variant = "pc_law_of_sines", "river_width"

    def test(self):
        for problem, solution in self.samples():
            base, A, B = map(int, self.search(r"stand \$(\d+)\$ m apart.*angle \$TAB = (\d+)\^\\circ\$ and angle \$TBA = (\d+)",
                                              problem).groups())
            # Coordinates: A at the origin, B at (base, 0); intersect the two sight lines.
            ta, tb = math.tan(math.radians(A)), math.tan(math.radians(B))
            x = base * tb / (ta + tb)
            y = x * ta
            self.close(solution, math.hypot(x, y), problem)


class CosinesShips(_Base):
    name, variant = "pc_law_of_cosines_side", "ships"

    def test(self):
        for problem, solution in self.samples():
            v1, v2, ang, t = map(int, self.search(r"at \$(\d+)\$ km/h and the other at \$(\d+)\$ km/h, with \$(\d+)\^\\circ\$.*after "
                                                  r"\$(\d+)\$ hours", problem).groups())
            p1 = cmath.rect(v1 * t, 0)
            p2 = cmath.rect(v2 * t, math.radians(ang))
            self.close(solution, abs(p1 - p2), problem)


class CosinesIsObtuse(_Base):
    name, variant = "pc_law_of_cosines_side", "is_obtuse"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = map(int, self.search(r"sides \$(\d+)\$, \$(\d+)\$, and \$(\d+)\$", problem).groups())
            C = math.degrees(math.acos((a * a + b * b - c * c) / (2 * a * b)))
            self.assertEqual(solution, "yes" if C > 90 + 1e-9 else "no", problem)


class ObliqueHeron(_Base):
    name, variant = "pc_oblique_triangle_area", "heron"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = map(int, self.search(r"sides \$(\d+)\$, \$(\d+)\$, and \$(\d+)\$", problem).groups())
            C = math.acos((a * a + b * b - c * c) / (2 * a * b))
            self.close(solution, 0.5 * a * b * math.sin(C), problem)


class ObliqueAngleFromArea(_Base):
    name, variant = "pc_oblique_triangle_area", "angle_from_area"

    def test(self):
        for problem, solution in self.samples():
            a, b, area = self.search(r"sides \$(\d+)\$ and \$(\d+)\$ with.*area is \$" + NUM, problem).groups()
            self.assertAlmostEqual(0.5 * int(a) * int(b) * math.sin(math.radians(float(solution))), float(area), delta=0.01)


class InverseComposition(_Base):
    name, variant = "pc_inverse_trig", "composition"

    def test(self):
        f = {"sin": math.sin, "cos": math.cos, "tan": math.tan}
        inv = {"sin": math.asin, "cos": math.acos, "tan": math.atan}
        for problem, solution in self.samples():
            outer, inner, p, q = self.search(r"\\(sin|cos|tan)\\left\(\\arc(sin|cos|tan)\\frac\{(\d+)\}\{(\d+)\}", problem).groups()
            self.assertAlmostEqual(float(frac(solution)), f[outer](inv[inner](int(p) / int(q))), places=9)


class DoubleAngleQuadrant(_Base):
    name, variant = "pc_double_angle", "quadrant_sign"

    def test(self):
        for problem, solution in self.samples():
            s_val, quad = self.search(r"\$\\sin x = " + FRAC + r"\$ and \$x\$ is in quadrant (III|II|IV)\.", problem).groups()
            sv = float(frac(s_val))
            base = math.asin(sv)
            x = {"II": math.pi - base, "III": math.pi - base, "IV": base}[quad]
            self.assertEqual(quadrant_of(math.cos(x), math.sin(x)), quad)
            self.assertAlmostEqual(float(frac(solution)), math.sin(2 * x), places=9)


class DoubleAngleSquare(_Base):
    name, variant = "pc_double_angle", "square_from_double"

    def test(self):
        for problem, solution in self.samples():
            c, which = self.search(r"\$\\cos 2x = " + FRAC + r"\$, what is \$\\(sin|cos)\^2 x\$", problem).groups()
            x = math.acos(float(frac(c))) / 2
            value = math.sin(x) ** 2 if which == "sin" else math.cos(x) ** 2
            self.assertAlmostEqual(float(frac(solution)), value, places=9)


TRIG_VALUES = {r"\frac{1}{2}": 0.5, r"-\frac{1}{2}": -0.5, "1": 1, "-1": -1, r"\frac{\sqrt{2}}{2}": math.sqrt(2) / 2,
               r"-\frac{\sqrt{2}}{2}": -math.sqrt(2) / 2}


def solutions_in_circle(func, value, k=1):
    """Degrees x in [0, 360) with func(k x) = value, found on a 0.001-degree scan of sign changes and touches."""
    f = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[func]
    out = []
    for i in range(360 * 8):
        x0, x1 = i / 8, (i + 1) / 8
        y0 = f(math.radians(k * x0)) - value
        y1 = f(math.radians(k * x1)) - value
        if abs(y0) < 1e-12:
            out.append(x0)
        elif y0 * y1 < 0 and abs(y1 - y0) < 1:   # skip tangent's jump at an asymptote
            lo, hi = x0, x1
            for _ in range(60):
                mid = (lo + hi) / 2
                if (f(math.radians(k * mid)) - value) * y0 > 0:
                    lo = mid
                else:
                    hi = mid
            out.append((lo + hi) / 2)
    return out


class TrigSumOfSolutions(_Base):
    name, variant = "pc_solve_trig_equation", "sum_of_solutions"

    def test(self):
        for problem, solution in self.samples():
            func, v = self.search(r"\$\\(sin|cos|tan) x = (.+?)\$ for", problem).groups()
            sols = sorted({round(x, 6) for x in solutions_in_circle(func, TRIG_VALUES[v])})
            self.assertAlmostEqual(int(solution), sum(sols), delta=0.01, msg=problem)


class TrigSmallestMultipleAngle(_Base):
    name, variant = "pc_solve_trig_equation", "smallest_multiple_angle"

    def test(self):
        for problem, solution in self.samples():
            func, k, v = self.search(r"\$\\(sin|cos|tan)\((\d+)x\) = (.+?)\$", problem).groups()
            sols = [x for x in {round(x, 6) for x in solutions_in_circle(func, TRIG_VALUES[v], int(k))} if x > 1e-9]
            self.close(solution, min(sols), problem)


class PolarEquivalentNegative(_Base):
    name, variant = "pc_polar_to_rectangular", "equivalent_with_negative_r"

    def test(self):
        for problem, solution in self.samples():
            r, t = map(int, self.search(r"point \$\((\d+), (\d+)\^\\circ\)\$", problem).groups())
            a = cmath.rect(r, math.radians(t))
            b = cmath.rect(-r, math.radians(int(solution)))
            self.assertAlmostEqual(abs(a - b), 0, places=9)
            self.assertTrue(0 <= int(solution) < 360)


class GeometricSalary(_Base):
    name, variant = "pc_finite_geometric_sum", "salary_raises"

    def test(self):
        for problem, solution in self.samples():
            start, pct, n = map(int, self.search(r"pays \$(\d+)\$ dollars.*a \$(\d+)\\%\$ raise.*over \$(\d+)\$ years", problem).groups())
            pay, total = float(start), 0.0
            for _ in range(n):
                total += pay
                pay *= 1 + pct / 100
            self.assertAlmostEqual(float(solution), total, delta=0.005 + 1e-6 * total)


class RecursiveFirstTerm(_Base):
    name, variant = "pc_recursive_sequence_term", "first_term"

    def test(self):
        for problem, solution in self.samples():
            r, sign, d, a4 = self.search(r"a_n = " + INT + r"a_\{n-1\} ([+-]) (\d+)\$, and \$a_4 = " + INT, problem).groups()
            r, d = int(r), int(d) * (1 if sign == "+" else -1)
            a = int(solution)
            for _ in range(3):
                a = r * a + d
            self.assertEqual(a, int(a4), problem)


class SequenceAverageCost(_Base):
    name, variant = "pc_sequence_limit", "average_cost"

    def test(self):
        for problem, solution in self.samples():
            fixed, per = self.search(r"C\(n\) = (\d+) \+ " + NUM + r"n\$", problem).groups()
            n = 10 ** 9
            self.assertAlmostEqual(float(solution), (int(fixed) + float(per) * n) / n, places=4)


class VectorMissing(_Base):
    name, variant = "pc_vector_add", "missing_vector"

    def test(self):
        for problem, solution in self.samples():
            u = tuple(map(int, self.search(r"\\vec u = \\langle " + INT + ", " + INT, problem).groups()))
            w = tuple(map(int, self.search(r"\\vec v = \\langle " + INT + ", " + INT, problem).groups()))
            v = tuple(map(int, re.fullmatch(r"\((-?\d+), (-?\d+)\)", solution).groups()))
            self.assertEqual((u[0] + v[0], u[1] + v[1]), w, problem)


class VectorLinearCombination(_Base):
    name, variant = "pc_vector_add", "linear_combination"

    def test(self):
        for problem, solution in self.samples():
            vecs = [tuple(map(int, v)) for v in re.findall(r"\\langle (-?\d+), (-?\d+) \\rangle", problem)]
            u, v, w = vecs
            fits = [a for a in range(-20, 21) for b in range(-20, 21)
                    if (a * u[0] + b * v[0], a * u[1] + b * v[1]) == w]
            self.assertEqual(fits, [int(solution)], problem)


class UnitCircleCoterminal(_Base):
    name, variant = "pc_unit_circle_sin", "coterminal"

    def test(self):
        for problem, solution in self.samples():
            angle = int(self.search(r"\\sin\(" + INT + r"\^\\circ\)", problem)[1])
            self.close(solution, math.sin(math.radians(angle)), problem)


class UnitCircleAngleFromValue(_Base):
    name, variant = "pc_unit_circle_cos", "angle_from_value"

    def test(self):
        for problem, solution in self.samples():
            sign = self.search(r"\\sin\\theta (<|>) 0", problem)[1]
            theta = float(frac(solution)) * math.pi
            cos_tex = self.search(r"\\cos\\theta = (.+?)\$", problem)[1]
            want = {r"\frac{\sqrt{3}}{2}": math.sqrt(3) / 2, r"\frac{\sqrt{2}}{2}": math.sqrt(2) / 2, r"\frac{1}{2}": 0.5,
                    r"-\frac{1}{2}": -0.5, r"-\frac{\sqrt{2}}{2}": -math.sqrt(2) / 2,
                    r"-\frac{\sqrt{3}}{2}": -math.sqrt(3) / 2}[cos_tex]
            self.assertTrue(0 <= theta < 2 * math.pi)
            self.assertAlmostEqual(math.cos(theta), want, places=9)
            self.assertEqual(math.sin(theta) < 0, sign == "<", problem)


class SinusoidPeriodFromTable(_Base):
    name, variant = "pc_sinusoid_features", "period_from_table"

    def test(self):
        for problem, solution in self.samples():
            body = re.search(r"\\begin\{array\}\{[^}]*\}(.*?)\\end\{array\}", problem).group(1)
            top, bottom = body.split(r"\\ \hline")
            xs = [int(v) for v in top.split("&")[1:]]
            ys = [int(v) for v in bottom.split("&")[1:]]
            # Fit y = D + A sin(2 pi x / P) through the data for P = the answer.
            P = int(solution)
            D, A = ys[0], ys[1] - ys[0]
            for x, y in zip(xs, ys):
                self.assertAlmostEqual(D + A * math.sin(2 * math.pi * x / P), y, places=9)


class SinusoidMaxValue(_Base):
    name, variant = "pc_sinusoid_features", "maximum_value"

    def test(self):
        for problem, solution in self.samples():
            kind, A, func, B, sign, D = self.search(r"(maximum|minimum) value of \$y = " + INT + r"\\(sin|cos)\((\d+)x\) ([+-]) (\d+)\$",
                                                    problem).groups()
            f = math.sin if func == "sin" else math.cos
            ys = [int(A) * f(int(B) * t / 100) + int(D) * (1 if sign == "+" else -1) for t in range(0, 1000)]
            want = max(ys) if kind == "maximum" else min(ys)
            self.assertAlmostEqual(int(solution), want, delta=0.01)


class BinomialCoefficientSum(_Base):
    name, variant = "pc_binomial_term", "coefficient_sum"

    def test(self):
        for problem, solution in self.samples():
            a, sign, b, n = self.search(r"\$\((\d*)x ([+-]) (\d+)\)\^\{(\d+)\}\$", problem).groups()
            a, b, n = int(a or 1), int(b) * (1 if sign == "+" else -1), int(n)
            coeffs = [math.comb(n, k) * a ** k * b ** (n - k) for k in range(n + 1)]
            self.assertEqual(int(solution), sum(coeffs), problem)


class BinomialUnknownConstant(_Base):
    name, variant = "pc_binomial_term", "unknown_constant"

    def test(self):
        for problem, solution in self.samples():
            n, coef = map(int, self.search(r"\(1 \+ kx\)\^\{(\d+)\}\$ is \$(\d+)\$", problem).groups())
            k = int(solution)
            self.assertGreater(k, 0)
            self.assertEqual(math.comb(n, 2) * k * k, coef, problem)


class DeMoivreArgument(_Base):
    name, variant = "pc_de_moivre", "argument_of_power"

    def test(self):
        for problem, solution in self.samples():
            r, t, n = map(int, self.search(r"z = (\d+)\(\\cos (\d+)\^\\circ.*argument of \$z\^\{(\d+)\}\$", problem).groups())
            arg = math.degrees(cmath.phase(cmath.rect(r, math.radians(t)) ** n)) % 360
            self.assertAlmostEqual(min(abs(arg - int(solution)), 360 - abs(arg - int(solution))), 0, delta=1e-6)


class DeMoivreRootModulus(_Base):
    name, variant = "pc_de_moivre", "root_modulus"

    def test(self):
        words = {"square": 2, "cube": 3, "fourth": 4, "fifth": 5}
        for problem, solution in self.samples():
            word, r, t = self.search(r"each (square|cube|fourth|fifth) root of \$(\d+)\(\\cos (\d+)", problem).groups()
            z = cmath.rect(int(r), math.radians(int(t)))
            root = z ** (1 / words[word])
            self.close(solution, abs(root), problem)


class PartialThreeFactors(_Base):
    name, variant = "pc_partial_fractions", "three_factors"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{([^}]+)\}\{([^}]+)\} = .*over \$\(x ([+-]) (\d+)\)\$", problem)
            from myapp.tests.test_algebra2_variants_math import coeffs_of, evaluate
            num_ = coeffs_of(m[1])
            roots = linear_roots(m[2])
            target = int(m[4]) if m[3] == "-" else -int(m[4])
            others = [r for r in roots if r != target]
            cover = Fraction(evaluate(num_, target), math.prod(target - r for r in others))
            self.assertEqual(int(solution), cover, problem)


class PolarCircleCenter(_Base):
    name, variant = "pc_polar_rectangular_equation", "circle_center"

    def test(self):
        for problem, solution in self.samples():
            a, func = self.search(r"\$r = " + INT + r"\\(sin|cos)\\theta\$", problem).groups()
            a = int(a)
            g = math.sin if func == "sin" else math.cos
            pts = [(a * g(t) * math.cos(t), a * g(t) * math.sin(t)) for t in [i * math.pi / 180 for i in range(180)]]
            cx = (max(p[0] for p in pts) + min(p[0] for p in pts)) / 2
            cy = (max(p[1] for p in pts) + min(p[1] for p in pts)) / 2
            x, y = map(float, re.fullmatch(r"\((-?[\d.]+), (-?[\d.]+)\)", solution).groups())
            self.assertAlmostEqual(x, cx, delta=0.01)
            self.assertAlmostEqual(y, cy, delta=0.01)


class ProjectionZero(_Base):
    name, variant = "pc_orthogonal_projection", "zero_projection"

    def test(self):
        for problem, solution in self.samples():
            a1 = int(self.search(r"of \$\\langle " + INT + r", k \\rangle\$", problem)[1])
            b1, b2 = map(int, self.search(r"onto \$\\langle " + INT + ", " + INT + r" \\rangle\$", problem).groups())
            k = int(solution)
            self.assertEqual(a1 * b1 + k * b2, 0, problem)
