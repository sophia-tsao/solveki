"""Math-correctness tests for the AP Precalculus Unit 3 generators (ap_precalc_trig).

Each test parses the generated problem text, recomputes the answer
independently (numerically with ``math``, or by brute force over a grid), and
asserts the served solution matches, over many random samples under a fixed
seed. No database is needed.
"""
import math
import random
import re

from django.test import SimpleTestCase

from myapp.generators import ap_precalc_trig  # noqa: F401  (registers generators)
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000


def _angle_value(s):
    """Parse ``0``, ``\\pi``, ``3\\pi``, ``\\frac{5\\pi}{6}`` into radians."""
    s = s.strip()
    if s == "0":
        return 0.0
    m = re.fullmatch(r"\\frac\{(\d*)\\pi\}\{(\d+)\}", s)
    if m:
        return (int(m.group(1)) if m.group(1) else 1) * math.pi / int(m.group(2))
    m = re.fullmatch(r"(\d*)\\pi", s)
    assert m, f"bad angle {s!r}"
    return (int(m.group(1)) if m.group(1) else 1) * math.pi


def _surd_value(s):
    """Parse ``-\\frac{\\sqrt{3}}{2}``, ``\\sqrt{3}``, ``1`` etc. into a float."""
    s = s.strip()
    sign = 1
    if s.startswith("-"):
        sign, s = -1, s[1:]
    m = re.fullmatch(r"\\frac\{(.+)\}\{(\d+)\}", s)
    if m:
        return sign * _surd_value(m.group(1)) / int(m.group(2))
    m = re.fullmatch(r"(\d*)\\sqrt\{(\d+)\}", s)
    if m:
        return sign * (int(m.group(1)) if m.group(1) else 1) * math.sqrt(int(m.group(2)))
    return sign * int(s)


def _coeff(token):
    """``""`` -> 1, ``"-"`` -> -1, ``"-3"`` -> -3."""
    if token in ("", "+"):
        return 1
    if token == "-":
        return -1
    return int(token)


def _value(solution):
    return float(solution.replace("$", ""))


class _Base(SimpleTestCase):
    name = None

    def samples(self):
        random.seed(0)
        gen = LOCAL_GENERATORS[self.name]
        for _ in range(SAMPLES):
            yield gen()[:2]

    def assertRounded(self, solution, true, problem):
        self.assertLessEqual(abs(_value(solution) - true), 0.0005 + 1e-9,
                             f"{problem!r} -> {solution!r} (true {true})")


class PeriodicValuesTests(_Base):
    name = "pc_periodic_values"

    def test_values_and_periods(self):
        for problem, solution in self.samples():
            if "What is the period" in problem:
                data = [int(v) for v in re.search(r"are \$([-\d, ]+)\$", problem).group(1).split(", ")]
                period = next(q for q in range(1, len(data) + 1)
                              if all(data[i] == data[i + q] for i in range(len(data) - q)))
                self.assertEqual(solution, f"${period}$", problem)
            else:
                p = int(re.search(r"period \$(\d+)\$", problem).group(1))
                table = {int(x): int(v) for x, v in
                         re.findall(r"\$f\((-?\d+)\) = (-?\d+)\$", problem)}
                n = int(re.search(r"Find \$f\((-?\d+)\)\$", problem).group(1))
                self.assertEqual(len(table), p, problem)
                x = next(x for x in table if (x - n) % p == 0)
                self.assertEqual(solution, f"${table[x]}$", problem)


class SinusoidalModelTests(_Base):
    name = "pc_sinusoidal_model"

    def test_model_answers(self):
        for problem, solution in self.samples():
            if m := re.search(r"diameter of \$(\d+)\$ feet, and its lowest point is "
                              r"\$(\d+)\$ feet.*?every \$(\d+)\$ minutes", problem):
                diam, low, T = map(int, m.groups())
                high = low + diam

                def f(t):
                    # Height of a rider who starts at the bottom of the wheel.
                    return low + diam / 2 * (1 - math.cos(2 * math.pi * t / T))
            elif m := re.search(r"high tide of \$(\d+)\$ feet and a low tide of "
                                r"\$(\d+)\$ feet, with \$(\d+)\$ hours", problem):
                high, low, T = map(int, m.groups())

                def f(t):
                    return (high + low) / 2 + (high - low) / 2 * math.cos(2 * math.pi * t / T)
            else:
                m = re.search(r"low of \$(\d+)\^\\circ\$F and a high of \$(\d+)\^\\circ\$F", problem)
                low, high = map(int, m.groups())
                T = 24

                def f(t):
                    return (high + low) / 2 - (high - low) / 2 * math.cos(2 * math.pi * t / T)
            # The model must hit the stated extremes over one cycle.
            values = [f(T * k / 400) for k in range(401)]
            self.assertAlmostEqual(max(values), high, places=6)
            self.assertAlmostEqual(min(values), low, places=6)

            if "amplitude" in problem:
                self.assertRounded(solution, (high - low) / 2, problem)
            elif "midline" in problem:
                self.assertEqual(solution, f"$y = {(high + low) // 2}$", problem)
            elif "what is $B$" in problem:
                self.assertRounded(solution, 2 * math.pi / T, problem)
            else:
                t = float(re.search(r"Find \$[hT]\(([\d.]+)\)\$", problem).group(1))
                self.assertRounded(solution, f(t), problem)


class SinusoidTransformationTests(_Base):
    name = "pc_sinusoid_transformations"

    def test_transformed_function(self):
        for problem, solution in self.samples():
            fn = math.sin if "f(x) = \\sin x" in problem else math.cos
            a = int(re.search(r"vertical dilation by a factor of \$(\d+)\$", problem).group(1))
            if "reflection over" in problem:
                a = -a
            b = int(re.search(r"horizontal dilation by a factor of \$\\frac\{1\}\{(\d+)\}\$",
                              problem).group(1))
            h = 0.0
            if m := re.search(r"horizontal translation of \$(.+?)\$ units (right|left)", problem):
                h = _angle_value(m.group(1)) * (1 if m.group(2) == "right" else -1)
            m = re.search(r"vertical translation of \$(\d+)\$ units (up|down)", problem)
            d = int(m.group(1)) * (1 if m.group(2) == "up" else -1)

            def g(x):
                # Dilate horizontally (x -> b x), then translate by h.
                return a * fn(b * (x - h)) + d

            grid = [g(2 * math.pi * k / 3000) for k in range(3000)]
            if "maximum value" in problem:
                self.assertRounded(solution, max(grid), problem)
            elif "minimum value" in problem:
                self.assertRounded(solution, min(grid), problem)
            elif "period" in problem:
                # Smallest positive shift p with g(x + p) = g(x).
                self.assertRounded(solution, 2 * math.pi / b, problem)
                p = 2 * math.pi / b
                self.assertAlmostEqual(g(0.3 + p), g(0.3), places=9)
            else:
                x = _angle_value(re.search(r"Evaluate \$g\\left\((.+?)\\right\)\$",
                                           problem).group(1))
                self.assertRounded(solution, g(x), problem)


class TangentFeaturesTests(_Base):
    name = "pc_tangent_features"
    EQ = re.compile(r"y = (?P<a>-?\d*)\\tan\\left\((?P<inside>.+?)\\right\)(?P<d> [+-] \d+)?\$")
    INSIDE = re.compile(r"(?:(?P<b>\d+)\()?(?:(?P<b0>\d+)?x)(?: (?P<op>[+-]) (?P<c>\d+)\^\\circ)?\)?")

    def test_tangent_features(self):
        for problem, solution in self.samples():
            if "in radians" in problem:
                m = re.search(r"y = (-?\d*)\\tan\((\d+)x\)", problem)
                self.assertRounded(solution, math.pi / int(m.group(2)), problem)
                continue
            m = self.EQ.search(problem)
            self.assertIsNotNone(m, problem)
            a = _coeff(m.group("a"))
            d = int(m.group("d").replace(" ", "")) if m.group("d") else 0
            im = self.INSIDE.fullmatch(m.group("inside"))
            self.assertIsNotNone(im, problem)
            b = int(im.group("b") or im.group("b0") or 1)
            c = int(im.group("c") or 0) * (1 if im.group("op") == "-" else -1)

            def y(x):
                return a * math.tan(math.radians(b * (x - c))) + d

            if "period in degrees" in problem:
                p = int(solution.strip("$"))
                self.assertAlmostEqual(y(7.3 + p), y(7.3), places=6)
                for q in range(1, p):  # no smaller whole-degree period
                    self.assertNotAlmostEqual(y(7.3 + q), y(7.3), places=6)
            elif "smallest positive" in problem:
                first = next(x for x in range(1, 1000)
                             if (b * (x - c) - 90) % 180 == 0)
                self.assertEqual(solution, f"${first}$", problem)
            elif "increasing or decreasing" in problem:
                x0 = c + 1 / b  # just right of a zero of the inside, inside a branch
                rising = y(x0 + 1e-4) > y(x0)
                self.assertEqual(solution, "increasing" if rising else "decreasing", problem)
            else:
                x = int(re.search(r"when \$x = (-?\d+)\^\\circ\$", problem).group(1))
                self.assertRounded(solution, y(x), problem)


class TrigInequalityTests(_Base):
    name = "pc_trig_inequality"
    PROB = re.compile(r"Solve \$\\(?P<fn>sin|cos|tan) x (?P<rel>>|<|\\geq|\\leq) (?P<c>.+?)\$ "
                      r"for \$(?P<lo>-?\d+)\^\\circ (?P<lr><|\\leq) x (?P<hr><|\\leq) (?P<hi>-?\d+)\^\\circ\$")
    SOL = re.compile(r"(-?\d+) (<=?) x (<=?) (-?\d+)")
    OPS = {">": lambda u, v: u > v + 1e-9, "<": lambda u, v: u < v - 1e-9,
           r"\geq": lambda u, v: u >= v - 1e-9, r"\leq": lambda u, v: u <= v + 1e-9}
    ASCII = {"<": lambda u, v: u < v, "<=": lambda u, v: u <= v}

    def test_interval_matches_brute_force(self):
        for problem, solution in self.samples():
            m = self.PROB.search(problem)
            self.assertIsNotNone(m, problem)
            fn = getattr(math, m.group("fn"))
            c = _surd_value(m.group("c"))
            lo, hi = int(m.group("lo")), int(m.group("hi"))
            sm = self.SOL.fullmatch(solution)
            self.assertIsNotNone(sm, solution)
            a, r1, r2, b = int(sm.group(1)), sm.group(2), sm.group(3), int(sm.group(4))
            # Every half-degree in the domain: in the stated interval iff it solves it.
            for k in range(2 * lo, 2 * hi + 1):
                x = k / 2
                in_domain = (x > lo or (m.group("lr") == r"\leq" and x == lo)) and \
                            (x < hi or (m.group("hr") == r"\leq" and x == hi))
                if not in_domain:
                    continue
                if m.group("fn") == "tan" and abs(x) == 90:
                    continue
                solves = self.OPS[m.group("rel")](fn(math.radians(x)), c)
                claimed = self.ASCII[r1](a, x) and self.ASCII[r2](x, b)
                self.assertEqual(solves, claimed, f"{problem!r} -> {solution!r} at x={x}")


class ReciprocalTrigTests(_Base):
    name = "pc_reciprocal_trig_values"

    def test_values(self):
        for problem, solution in self.samples():
            m = re.search(r"Evaluate \$\\(sec|csc|cot)\\left\((.+?)\\right\)\$", problem)
            fn, theta = m.group(1), _angle_value(m.group(2))
            top, bottom = {"sec": (1, math.cos(theta)), "csc": (1, math.sin(theta)),
                           "cot": (math.cos(theta), math.sin(theta))}[fn]
            if abs(bottom) < 1e-9:
                self.assertEqual(solution, "undefined", problem)
            else:
                self.assertRounded(solution, top / bottom, problem)


_ROSE = re.compile(r"r = (?P<a>-?\d*)\\(?P<fn>sin|cos)\((?P<n>\d+)\\theta\)")
_LIMACON = re.compile(r"r = (?:(?P<a>\d+) (?P<op>[+-]) )?(?P<b>-?\d*)\\(?P<fn>sin|cos)\\theta")


def _polar_function(problem):
    """The polar curve in the problem as a function of theta."""
    if m := _ROSE.search(problem):
        a, n, fn = _coeff(m.group("a")), int(m.group("n")), getattr(math, m.group("fn"))
        return (lambda t: a * fn(n * t)), ("rose", a, n)
    m = _LIMACON.search(problem)
    assert m, problem
    fn = getattr(math, m.group("fn"))
    if m.group("a"):
        a = int(m.group("a"))
        b = _coeff(m.group("b")) * (1 if m.group("op") == "+" else -1)
    else:
        a, b = 0, _coeff(m.group("b"))
    return (lambda t: a + b * fn(t)), ("limacon", a, b)


class PolarGraphFeaturesTests(_Base):
    name = "pc_polar_graph_features"
    GRID = [2 * math.pi * k / 20000 for k in range(20000)]

    def test_features(self):
        for problem, solution in self.samples():
            r, kind = _polar_function(problem)
            if "How many petals" in problem:
                # Count distinct petal tips: points where |r| is maximal.
                _, a, n = kind
                tips = {(round(r(t) * math.cos(t), 6) + 0.0, round(r(t) * math.sin(t), 6) + 0.0)
                        for t in (math.pi * k / (2 * n) for k in range(4 * n))
                        if abs(abs(r(t)) - abs(a)) < 1e-9}
                self.assertEqual(solution, f"${len(tips)}$", problem)
            elif "How long is each petal" in problem or "greatest distance" in problem:
                self.assertRounded(solution, max(abs(r(t)) for t in self.GRID), problem)
            elif "least distance" in problem:
                nearest = min(abs(r(t)) for t in self.GRID)
                self.assertLessEqual(abs(_value(solution) - nearest), 1e-3, problem)
            else:
                theta = _angle_value(re.search(r"\\theta = (.+?)\$", problem).group(1))
                self.assertRounded(solution, r(theta), problem)


class PolarRateOfChangeTests(_Base):
    name = "pc_polar_rate_of_change"

    def test_rates(self):
        for problem, solution in self.samples():
            r, _ = _polar_function(problem)
            if "average rate of change" in problem:
                m = re.search(r"interval \$([^$]+?) \\leq \\theta \\leq ([^$]+?)\$", problem)
                t1, t2 = _angle_value(m.group(1)), _angle_value(m.group(2))
                self.assertLess(t1, t2)
                self.assertRounded(solution, (r(t2) - r(t1)) / (t2 - t1), problem)
            else:
                m = re.search(r"interval \$([^$]+?) < \\theta < ([^$]+?)\$", problem)
                t1, t2 = _angle_value(m.group(1)), _angle_value(m.group(2))
                dist = [abs(r(t1 + (t2 - t1) * k / 200)) for k in range(1, 200)]
                diffs = [y - x for x, y in zip(dist, dist[1:])]
                if solution == "increasing":
                    self.assertTrue(all(dd > 0 for dd in diffs), problem)
                else:
                    self.assertEqual(solution, "decreasing", problem)
                    self.assertTrue(all(dd < 0 for dd in diffs), problem)
