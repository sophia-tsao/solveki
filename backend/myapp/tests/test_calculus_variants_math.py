"""Math-correctness tests for the Calculus variants (calculus_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently (numerical calculus or brute force), and checks the served
solution, over 2000 seeded samples.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators import calculus_variants  # noqa: F401 - attaches the variants
from myapp.tests.test_prealgebra_variants_math import INT, frac, table_rows

SAMPLES = 2000
TOL = 0.0005 + 1e-9
NUM = r"(-?\d+(?:\.\d+)?)"
FRAC = r"(-?\d+(?:/\d+)?)"


def poly(text, var="x"):
    """A callable from a LaTeX polynomial such as '3x^{2} - x + 4' (or with t)."""
    expr = text.replace(" ", "").replace("{", "").replace("}", "")
    expr = re.sub(r"\\frac(\d+)(\d+)", r"(\1/\2)", expr)
    expr = expr.replace("^", "**")
    expr = re.sub(r"(\d)" + var, r"\1*" + var, expr)
    expr = re.sub(r"\)" + var, ")*" + var, expr)
    return lambda v: eval(expr, {var: v})  # noqa: S307 - test-only, generated input


def integrate(f, a, b, n=2000):
    """Simpson's rule (exact for cubics; ample for the smooth integrands here)."""
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(a + i * h)
    return s * h / 3


def deriv(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)


class _Base(SimpleTestCase):
    name = variant = None

    def samples(self, name=None, count=SAMPLES):
        random.seed(0)
        gen = LOCAL_GENERATORS[name or self.name]
        for _ in range(count):
            problem, solution, _steps = gen(variant=self.variant)
            yield problem, solution.replace("$", "").strip()

    def search(self, pattern, problem):
        m = re.search(pattern, problem)
        self.assertIsNotNone(m, problem)
        return m

    def close(self, solution, value, problem, tol=TOL):
        self.assertAlmostEqual(float(frac(solution)) if "/" in solution else float(solution), float(value), delta=tol, msg=problem)


class LimitHiddenParameter(_Base):
    name, variant = "calc_limit_rational", "hidden_parameter"

    def test(self):
        for problem, solution in self.samples():
            a = int(self.search(r"x \\to " + INT, problem)[1])
            sign, m = self.search(r"x\^2 \+ kx ([+-]) (\d+)\}", problem).groups()
            m = int(m) * (1 if sign == "+" else -1)
            ks = [k for k in range(-30, 31) if a * a + k * a + m == 0]
            self.assertEqual(len(ks), 1)
            k = ks[0]
            f = lambda x: (x * x + k * x + m) / (x - a)  # noqa: E731
            self.close(solution, (f(a + 1e-7) + f(a - 1e-7)) / 2, problem, 1e-4)


class LimitAtInfinity(_Base):
    name, variant = "calc_limit_rational", "at_infinity"

    def test(self):
        for problem, solution in self.samples():
            top, bottom = self.search(r"\\frac\{(.+?)\}\{(.+?)\}\$\. Express", problem).groups()
            f, g = poly(top), poly(bottom)
            x = 1e7
            self.close(solution, f(x) / g(x), problem, 1e-4)


class ConjugateAtInfinity(_Base):
    name, variant = "calc_limit_conjugate", "at_infinity"

    def test(self):
        for problem, solution in self.samples():
            inside = self.search(r"\\sqrt\{([^}]+)\}", problem)[1]
            f = poly(inside)
            x = 1e6
            self.close(solution, math.sqrt(f(x)) - x, problem, 1e-4)


class DerivativeHorizontalTangent(_Base):
    name, variant = "calc_derivative_polynomial", "horizontal_tangent"

    def test(self):
        for problem, solution in self.samples():
            f = poly(self.search(r"f\(x\) = ([^$]+)\$", problem)[1])
            m = re.search(r"\$f'\(x\) = " + INT + r"\$", problem)
            target = int(m[1]) if m else 0
            self.assertAlmostEqual(deriv(f, float(frac(solution))), target, delta=1e-4, msg=problem)


class PowerRuleSlope(_Base):
    name, variant = "power_rule_differentiation", "slope_at_point"

    def test(self):
        for problem, solution in self.samples():
            f = poly(self.search(r"f\(x\) = ([^$]+)\$", problem)[1])
            x0 = int(self.search(r"at \$x = " + INT, problem)[1])
            self.assertAlmostEqual(deriv(f, x0), int(solution), delta=1e-3, msg=problem)


def rule_table(problem):
    body = re.search(r"\\begin\{array\}\{[^}]*\}(.*?)\\end\{array\}", problem).group(1)
    rows = [r.split("&") for r in body.split(r"\\ \hline")]
    data = {r[0].strip(): [int(v) for v in r[1:]] for r in rows}
    xs = data["x"]
    get = lambda key: dict(zip(xs, data[key]))  # noqa: E731
    return get("f(x)"), get("f'(x)"), get("g(x)"), get("g'(x)")


class ProductFromTable(_Base):
    name, variant = "calc_product_rule", "from_table"

    def test(self):
        for problem, solution in self.samples():
            f, fp, g, gp = rule_table(problem)
            a = int(self.search(r"h'\((\d)\)", problem)[1])
            # Local linear models of f and g near a; differentiate their product numerically.
            F = lambda x: f[a] + fp[a] * (x - a)  # noqa: E731
            G = lambda x: g[a] + gp[a] * (x - a)  # noqa: E731
            self.assertAlmostEqual(deriv(lambda x: F(x) * G(x), a), int(solution), delta=1e-4)


class QuotientFromTable(_Base):
    name, variant = "calc_quotient_rule", "from_table"

    def test(self):
        for problem, solution in self.samples():
            f, fp, g, gp = rule_table(problem)
            a = int(self.search(r"h'\((\d)\)", problem)[1])
            if g[a] == 0:
                continue
            F = lambda x: f[a] + fp[a] * (x - a)  # noqa: E731
            G = lambda x: g[a] + gp[a] * (x - a)  # noqa: E731
            self.assertAlmostEqual(deriv(lambda x: F(x) / G(x), a), float(frac(solution)), delta=1e-4)


class ChainFromTable(_Base):
    name, variant = "calc_chain_rule", "from_table"

    def test(self):
        for problem, solution in self.samples():
            f, fp, g, gp = rule_table(problem)
            a = int(self.search(r"h'\((\d)\)", problem)[1])
            b = g[a]
            F = lambda u: f[b] + fp[b] * (u - b)  # noqa: E731
            G = lambda x: g[a] + gp[a] * (x - a)  # noqa: E731
            self.assertAlmostEqual(deriv(lambda x: F(G(x)), a), int(solution), delta=1e-4)


class ExpCriticalPoint(_Base):
    name, variant = "calc_derivative_exp_log_trig", "critical_point"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = self.search(r"\$f\(x\) = (\d*)e\^\{(\d*)x\} - (\d+)x\$", problem).groups()
            a, b, c = int(a or 1), int(b or 1), int(c)
            f = lambda x: a * math.exp(b * x) - c * x  # noqa: E731
            self.assertAlmostEqual(deriv(f, float(solution)), 0, delta=0.01 * c)


class HigherOrderPattern(_Base):
    name, variant = "calc_higher_order_derivative", "power_pattern"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"\$(\d+)\$th derivative of \$f\(x\) = (\d*)x\^\{(\d+)\}\$", problem)
            if m:
                n, c, p = int(m[1]), int(m[2] or 1), int(m[3])
                # Apply the power rule n times by repeated coefficient updates.
                coef, power = c, p
                for _ in range(n):
                    coef, power = coef * power, power - 1
                self.assertEqual(int(solution), coef, problem)
            else:
                s = poly(self.search(r"s\(t\) = ([^$]+)\$", problem)[1], "t")
                t = int(self.search(r"at \$t = " + INT, problem)[1])
                h = 1e-3
                acc = (s(t + h) - 2 * s(t) + s(t - h)) / (h * h)
                self.assertAlmostEqual(acc, int(solution), delta=1e-2)


class TangentLinearApproximation(_Base):
    name, variant = "calc_tangent_line", "linear_approximation"

    def test(self):
        for problem, solution in self.samples():
            f = poly(self.search(r"f\(x\) = ([^$]+)\$ at", problem)[1])
            a = int(self.search(r"at \$x = " + INT, problem)[1])
            x = float(self.search(r"approximate \$f\(" + NUM, problem)[1])
            self.close(solution, f(a) + deriv(f, a) * (x - a), problem, 1e-3)


class TangentThroughOrigin(_Base):
    name, variant = "calc_tangent_line", "through_origin"

    def test(self):
        for problem, solution in self.samples():
            c = int(self.search(r"x\^2 \+ (\d+)\$", problem)[1])
            a = int(solution)
            f = lambda x: x * x + c  # noqa: E731
            # Tangent at a evaluated at x = 0 should be 0.
            self.assertAlmostEqual(f(a) + deriv(f, a) * (0 - a), 0, delta=1e-4)


class ExtremaOptimization(_Base):
    name, variant = "calc_extrema", "optimization"

    def test(self):
        for problem, solution in self.samples(count=300):   # each sample runs a grid search
            m = re.search(r"corners of a \$(\d+)\$ cm square sheet", problem)
            if m:
                side = int(m[1])
                best = max((i / 1000 for i in range(1, side * 500)), key=lambda x: x * (side - 2 * x) ** 2)
                self.close(solution, best, problem, 0.002)
            else:
                L = int(self.search(r"has \$(\d+)\$ m of fence", problem)[1])
                best = max(x / 100 * (L - 2 * x / 100) for x in range(1, L * 50))
                self.close(solution, best, problem, 0.01)


class ExtremaAbsolute(_Base):
    name, variant = "calc_extrema", "absolute_on_interval"

    def test(self):
        for problem, solution in self.samples(count=500):   # each sample scans 4000 points
            f = poly(self.search(r"f\(x\) = ([^$]+)\$ on", problem)[1])
            lo, hi = map(int, self.search(r"on \$\[" + INT + ", " + INT + r"\]\$", problem).groups())
            vals = [f(lo + (hi - lo) * i / 4000) for i in range(4001)]
            want = max(vals) if "maximum" in problem else min(vals)
            self.assertAlmostEqual(int(solution), want, delta=1e-3)   # the grid may just miss the exact extremum


class ExtremaParameter(_Base):
    name, variant = "calc_extrema", "parameter_for_critical_point"

    def test(self):
        for problem, solution in self.samples():
            sign, a = self.search(r"x\^3 ([+-]) (\d+)x\^2 \+ kx\$", problem).groups()
            a = int(a) * (1 if sign == "+" else -1)
            c = int(self.search(r"critical point at \$x = " + INT, problem)[1])
            k = int(solution)
            self.assertAlmostEqual(deriv(lambda x: x ** 3 + a * x * x + k * x, c), 0, delta=1e-4)


class InflectionParameter(_Base):
    name, variant = "calc_inflection_point", "parameter"

    def test(self):
        for problem, solution in self.samples():
            c = int(self.search(r"inflection point at \$x = " + INT, problem)[1])
            k = int(solution)
            f = lambda x: x ** 3 + k * x * x  # noqa: E731
            h = 1e-3
            self.assertAlmostEqual((f(c + h) - 2 * f(c) + f(c - h)) / (h * h), 0, delta=1e-3)


class InflectionY(_Base):
    name, variant = "calc_inflection_point", "y_coordinate"

    def test(self):
        for problem, solution in self.samples(count=500):
            f = poly(self.search(r"f\(x\) = ([^$]+)\$", problem)[1])
            # Locate where the second difference changes sign.
            h = 1e-3
            xs = [i / 100 for i in range(-1000, 1001)]
            sec = [(f(x + h) - 2 * f(x) + f(x - h)) for x in xs]
            for i in range(len(xs) - 1):
                if sec[i] == 0 or sec[i] * sec[i + 1] < 0:
                    x0 = xs[i] if sec[i] == 0 else (xs[i] + xs[i + 1]) / 2
                    break
            self.assertAlmostEqual(f(x0), int(solution), delta=0.5)
            self.assertEqual(int(solution), round(f(round(x0))), problem)


class ConcavityDown(_Base):
    name, variant = "calc_concavity_interval", "concave_down"

    def test(self):
        for problem, solution in self.samples():
            f = poly(self.search(r"f\(x\) = ([^$]+)\$ concave", problem)[1])
            m = re.fullmatch(r"\((-inf|-?[\d/]+), (inf|-?[\d/]+)\)", solution)
            lo = -1e3 if m[1] == "-inf" else float(frac(m[1]))
            hi = 1e3 if m[2] == "inf" else float(frac(m[2]))
            h = 1e-2
            for x in (lo + 0.5, (lo + hi) / 2, hi - 0.5):
                self.assertLess(f(x + h) - 2 * f(x) + f(x - h), 0, problem)


class IntegralProperties(_Base):
    variant = "properties"

    def test(self):
        for name in ("calc_definite_integral_poly", "definite_integral"):
            for problem, solution in self.samples(name):
                a, c, P, a2, b, Q = map(int, self.search(r"\\int_\{" + INT + r"\}\^\{" + INT + r"\} f\(x\)\\,dx = " + INT
                                                         + r"\$ and \$\\int_\{" + INT + r"\}\^\{" + INT + r"\} f\(x\)\\,dx = " + INT, problem).groups())
                self.assertEqual(a, a2)
                m, sign, n = self.search(r"\\left\((-?\d*)f\(x\) ([+-]) (\d+)\\right\)", problem).groups()
                m = {"": 1, "-": -1}.get(m) if m in ("", "-") else int(m)
                n = int(n) * (1 if sign == "+" else -1)
                # A concrete f with those integrals: f = constant pieces on [a, b] and [b, c].
                fb = Fraction(Q, b - a)
                fc = Fraction(P - Q, c - b)
                self.assertEqual(int(solution), m * fc * (c - b) + n * (c - b), problem)


class IntegralUpperLimit(_Base):
    name, variant = "calc_definite_integral_poly", "upper_limit"

    def test(self):
        for problem, solution in self.samples():
            c, area = self.search(r"\\int_0\^k (\d*)x\\,dx = (.+?)\$", problem).groups()
            c = int(c or 1)
            self.assertAlmostEqual(integrate(lambda x: c * x, 0, int(solution)), float(frac(area.replace("\\frac{", "").replace("}{", "/").replace("}", ""))), places=6)


class IntegralFromGraph(_Base):
    name, variant = "calc_definite_integral_poly", "area_from_graph"

    def test(self):
        for problem, solution in self.samples():
            pts = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            def f(x):
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    if x0 <= x <= x1:
                        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                return 0
            value = sum(integrate(f, x0, x1, 200) for (x0, _), (x1, _) in zip(pts, pts[1:]))
            self.close(solution, value, problem, 1e-6)


class InitialValue(_Base):
    variant = "initial_value"

    def test(self):
        for name in ("calc_indefinite_integral_poly", "power_rule_integration"):
            for problem, solution in self.samples(name, 500):
                fp = poly(self.search(r"F'\(x\) = ([^$]+)\$", problem)[1])
                c = int(self.search(r"F\(0\) = " + INT, problem)[1])
                x0 = int(self.search(r"what is \$F\(" + INT, problem)[1])
                value = c + (integrate(fp, 0, x0) if x0 else 0)
                self.close(solution, value, problem, 1e-6)


class UsubNewLimits(_Base):
    name, variant = "calc_usub_integral", "new_limits"

    def test(self):
        for problem, solution in self.samples():
            p, q = map(int, self.search(r"\\int_\{" + INT + r"\}\^\{" + INT + r"\}", problem).groups())
            a, sign, b = self.search(r"u = " + INT + r"x ([+-]) (\d+)\$", problem).groups()
            u = lambda x: int(a) * x + int(b) * (1 if sign == "+" else -1)  # noqa: E731
            want = u(q) if "upper" in problem else u(p)
            self.assertEqual(int(solution), want, problem)


class AreaFindIntersections(_Base):
    name, variant = "calc_area_between_curves", "find_intersections"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"\$y = x\^2\$ and \$y = (\d+)x\$", problem)
            if m:
                k = int(m[1])
                f, g, a, b = (lambda x: k * x), (lambda x: x * x), 0, k
            else:
                c = int(self.search(r"\$y = (\d+) - x\^2\$", problem)[1])
                t = math.sqrt(c / 2)
                f, g, a, b = (lambda x: c - x * x), (lambda x: x * x), -t, t
            self.close(solution, integrate(lambda x: f(x) - g(x), a, b), problem, 1e-6)


class AverageWhereAttained(_Base):
    name, variant = "calc_average_value", "where_attained"

    def test(self):
        for problem, solution in self.samples():
            b = int(self.search(r"on \$\[0, (\d+)\]\$", problem)[1])
            avg = integrate(lambda x: x * x, 0, b) / b
            self.assertAlmostEqual(float(solution) ** 2, avg, delta=0.01 * b)


class AverageTemperature(_Base):
    name, variant = "calc_average_value", "temperature"

    def test(self):
        for problem, solution in self.samples():
            a, b, c, h = self.search(r"T\(t\) = (\d+) \+ (\d+)t - " + NUM + r"t\^2\$.*first \$(\d+)\$", problem).groups()
            T = lambda t: int(a) + int(b) * t - float(c) * t * t  # noqa: E731
            self.close(solution, integrate(T, 0, int(h)) / int(h), problem)


class RiemannFromTable(_Base):
    name, variant = "calc_riemann_sum", "from_table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, r)) for r in table_rows(problem))
            left = "left Riemann" in problem
            total = sum((xs[i + 1] - xs[i]) * (ys[i] if left else ys[i + 1]) for i in range(len(xs) - 1))
            self.assertEqual(int(solution), total, problem)


class RiemannOverUnder(_Base):
    name, variant = "calc_riemann_sum", "over_or_under"

    def test(self):
        for problem, solution in self.samples(count=200):   # only four cases exist
            inc = "is increasing" in problem
            left = "a left Riemann" in problem
            f = (lambda x: x * x) if inc else (lambda x: -x * x)
            exact = integrate(f, 1, 3)
            n = 4
            pts = [1 + 2 * i / n for i in range(n)] if left else [1 + 2 * (i + 1) / n for i in range(n)]
            est = sum(f(p) * 2 / n for p in pts)
            self.assertEqual(solution, "overestimate" if est > exact else "underestimate", problem)


class TrapezoidFromTable(_Base):
    name, variant = "calc_trapezoidal_rule", "from_table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, r)) for r in table_rows(problem))
            # Integrate the piecewise-linear interpolant exactly.
            total = sum(integrate(lambda x, i=i: ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i]), xs[i], xs[i + 1], 20)
                        for i in range(len(xs) - 1))
            self.close(solution, total, problem, 1e-6)


class VolumeSquareSections(_Base):
    name, variant = "calc_volume_revolution", "square_cross_sections"

    def test(self):
        for problem, solution in self.samples():
            m, k = self.search(r"under \$y = (\d*)x\$ from \$x = 0\$ to \$x = (\d+)\$", problem).groups()
            m, k = int(m or 1), int(k)
            self.close(solution, integrate(lambda x: (m * x) ** 2, 0, k), problem, 1e-6)


class VolumeShells(_Base):
    name, variant = "calc_volume_revolution", "shells_about_y"

    def test(self):
        for problem, solution in self.samples():
            a = int(self.search(r"\$y = (\d+)x - x\^2\$", problem)[1])
            # Washers about the y-axis: for each height y, the region spans x1(y)..x2(y).
            top = a * a / 4
            def washer(y):
                d = math.sqrt(max(0.0, a * a / 4 - y))
                x1, x2 = a / 2 - d, a / 2 + d
                return math.pi * (x2 * x2 - x1 * x1)
            vol = integrate(washer, 0, top)
            self.close(solution, vol / math.pi, problem, 1e-3)


class MotionTotalDistance(_Base):
    name, variant = "calc_particle_motion", "total_distance"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"v\(t\) = t\^2 - (\d+)t\$ for \$0 \\leq t \\leq (\d+)\$", problem).groups())
            v = lambda t: t * t - a * t  # noqa: E731
            # |v| has a kink where v changes sign (t = a): integrate the two smooth pieces.
            want = abs(integrate(v, 0, a)) + abs(integrate(v, a, b)) if "distance" in problem else integrate(v, 0, b)
            self.close(solution, want, problem, 1e-4)


class MotionSpeedingUp(_Base):
    name, variant = "calc_particle_motion", "speeding_up"

    def test(self):
        for problem, solution in self.samples():
            s = poly(self.search(r"s\(t\) = ([^$]+)\$", problem)[1], "t")
            t = int(self.search(r"at \$t = " + INT, problem)[1])
            speed = lambda u: abs(deriv(s, u))  # noqa: E731
            speeding = speed(t + 1e-3) > speed(t - 1e-3)
            self.assertEqual(solution, "yes" if speeding else "no", problem)


class RelatedRatesContexts(_Base):
    name, variant = "calc_related_rates", "new_contexts"

    def test(self):
        for problem, solution in self.samples():
            dt = 1e-6
            if "upside-down cone" in problem:
                rate = int(self.search(r"at \$(\d+)\$ cubic ft/min", problem)[1])
                m = re.search(r"depth is always \$(\d+)\$ times", problem)
                ratio = int(m[1]) if m else 1
                h = int(self.search(r"when it is \$(\d+)\$ ft deep", problem)[1])
                V = lambda d: math.pi / 3 * (d / ratio) ** 2 * d  # noqa: E731
                dhdt = rate / deriv(V, h)
                self.assertAlmostEqual(float(frac(solution)) / math.pi, dhdt, delta=1e-6)
            elif "street light" in problem:
                p, H, v = map(int, self.search(r"\$(\d+)\$ ft tall person walks away from a \$(\d+)\$ ft street light at \$(\d+)\$",
                                               problem).groups())
                shadow = lambda x: p * x / (H - p)  # noqa: E731
                self.assertAlmostEqual(float(frac(solution)), (shadow(10 + v * dt) - shadow(10)) / dt, delta=1e-4)
            else:
                rate, r = map(int, self.search(r"at \$(\d+)\$ cubic cm/s.*radius is \$(\d+)\$ cm", problem).groups())
                V = lambda rr: 4 / 3 * math.pi * rr ** 3  # noqa: E731
                self.assertAlmostEqual(float(frac(solution)) / math.pi, rate / deriv(V, r), delta=1e-6)


class MvtRolle(_Base):
    name, variant = "calc_mvt_find_c", "rolle"

    def test(self):
        for problem, solution in self.samples():
            k, a, b = self.search(r"f\(x\) = (-?\d*)\(x - \(?(-?\d+)\)?\)\(x - \(?(-?\d+)\)?\)\$", problem).groups()
            k = {"": 1, "-": -1}.get(k) if k in ("", "-") else int(k)
            f = lambda x: k * (x - int(a)) * (x - int(b))  # noqa: E731
            self.assertAlmostEqual(deriv(f, float(frac(solution))), 0, delta=1e-6)


class MvtGuaranteedRate(_Base):
    name, variant = "calc_mvt_find_c", "guaranteed_rate"

    def test(self):
        for problem, solution in self.samples():
            x1, y1, x2, y2 = map(int, self.search(r"f\((\d+)\) = " + INT + r"\$ and \$f\((\d+)\) = " + INT, problem).groups())
            self.assertEqual(frac(solution), Fraction(y2 - y1, x2 - x1), problem)


class OdeGrowthConstant(_Base):
    name, variant = "calc_separable_ode", "growth_constant"

    def test(self):
        for problem, solution in self.samples():
            y0, y1, t = self.search(r"starts at \$(\d+)\$ and is \$" + NUM + r"\$ after \$(\d+)\$ years", problem).groups()
            k = float(solution)
            # Integrate dP/dt = kP with small Euler-free exact steps (multiplicative).
            self.assertAlmostEqual(int(y0) * math.exp(k * int(t)), float(y1), delta=0.0006 * int(t) * float(y1))


class OdeCooling(_Base):
    name, variant = "calc_separable_ode", "cooling"

    def test(self):
        for problem, solution in self.samples():
            room, diff, k, target = self.search(r"T\(t\) = (\d+) \+ (\d+)e\^\{-" + NUM + r"t\}\$.*reach \$(\d+)\^", problem).groups()
            T = lambda t: int(room) + int(diff) * math.exp(-float(k) * t)  # noqa: E731
            self.assertAlmostEqual(T(float(solution)), int(target), delta=0.01)


class LhopitalParameter(_Base):
    name, variant = "calc_lhopital", "parameter"

    def test(self):
        for problem, solution in self.samples():
            c, L = self.search(r"\}\{(\d*)x\} = (.+?)\$\?", problem).groups()
            c = int(c or 1)
            Lv = float(frac(L.replace("\\frac{", "").replace("}{", "/").replace("}", "").replace("-\\", "-")))
            k = int(solution)
            x = 1e-6
            self.assertAlmostEqual(math.sin(k * x) / (c * x), Lv, delta=1e-5)


class LhopitalInfinity(_Base):
    name, variant = "calc_lhopital", "infinity_over_infinity"

    def test(self):
        for problem, solution in self.samples():
            a, b = self.search(r"\\frac\{(\d*)x \+ \\ln x\}\{(\d*)x\}", problem).groups()
            a, b = int(a or 1), int(b or 1)
            x = 1e12
            self.assertAlmostEqual(float(frac(solution)), (a * x + math.log(x)) / (b * x), delta=1e-6)


class LimitDefinitionRecognize(_Base):
    name, variant = "calc_limit_definition_derivative", "recognize_limit"

    def test(self):
        for problem, solution in self.samples():
            a, n = self.search(r"\(" + INT + r" \+ h\)\^\{(\d+)\}", problem).groups()
            a, n = int(a), int(n)
            h = 1e-7
            self.assertAlmostEqual(((a + h) ** n - a ** n) / h, int(solution), delta=1e-3 * max(1, abs(int(solution))))


class PartsTwice(_Base):
    name, variant = "calc_integration_by_parts", "twice"

    def test(self):
        for problem, solution in self.samples():
            b = int(self.search(r"\\int_0\^\{(\d+)\}", problem)[1])
            self.close(solution, integrate(lambda x: x * x * math.exp(x), 0, b), problem)


class TaylorDerivative(_Base):
    name, variant = "calc_taylor_coefficient", "derivative_from_coefficient"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"coefficient of \$x\^\{(\d+)\}\$", problem)[1])
            c = self.search(r"series of \$f\$ is \$(.+?)\$", problem)[1]
            c = frac(c.replace("\\frac{", "").replace("}{", "/").replace("}", "").replace("-\\", "-")) if "frac" in c else frac(c)
            self.assertEqual(frac(solution), c * math.factorial(n), problem)


class TaylorSubstitution(_Base):
    name, variant = "calc_taylor_coefficient", "substitution"

    def test(self):
        funcs = {"e": math.exp, "\\sin": math.sin, "\\cos": math.cos}
        for problem, solution in self.samples(count=400):
            n = int(self.search(r"coefficient of \$x\^\{(\d+)\}\$", problem)[1])
            m = re.search(r"series of \$e\^\{" + INT + r"x\}\$", problem)
            if m:
                k, f = int(m[1]), math.exp
            else:
                name, k = self.search(r"series of \$(\\sin|\\cos)\(" + INT + r"x\)\$", problem).groups()
                f, k = funcs[name], int(k)
            # n-th Taylor coefficient of f(kx) by a finite-difference n-th derivative at 0, scaled.
            h = 0.05
            nth = sum((-1) ** (n - j) * math.comb(n, j) * f(k * (j - n / 2) * h) for j in range(n + 1)) / h ** n
            self.assertAlmostEqual(float(frac(solution)), nth / math.factorial(n), delta=0.02 * max(1, abs(nth / math.factorial(n))))


class TaylorApproximate(_Base):
    name, variant = "calc_taylor_coefficient", "approximate"

    def test(self):
        for problem, solution in self.samples():
            h = float(self.search(r"approximate \$e\^\{" + NUM + r"\}\$", problem)[1])
            self.close(solution, 1 + h + h * h / 2, problem)
            # ...and it really is close to e^h (Taylor error about h^3/6, plus rounding).
            self.assertAlmostEqual(float(solution), math.exp(h), delta=abs(h) ** 3 / 6 * 1.2 + TOL)


class ImplicitFindPoint(_Base):
    name, variant = "calc_implicit_differentiation", "find_the_point"

    def test(self):
        for problem, solution in self.samples():
            r2, x = map(int, self.search(r"x\^2 \+ y\^2 = (\d+)\$ at the point where \$x = " + INT, problem).groups())
            y = lambda t: math.sqrt(r2 - t * t)  # noqa: E731
            self.assertAlmostEqual(deriv(y, x), float(frac(solution)), delta=1e-4)
