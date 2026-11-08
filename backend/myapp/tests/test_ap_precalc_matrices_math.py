"""Math-correctness tests for the AP Precalculus Unit 4 generators.

Covers parametric functions, implicit curves, conics, vector-valued functions,
and matrices (``ap_precalc_matrices``). Each test parses the generated problem,
recomputes the answer independently, and asserts the stated solution matches,
over many random samples under a fixed seed.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import ap_precalc_matrices  # noqa: F401  (registers generators)
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000

_TERM = re.compile(r"([+-]?)(\d*)([a-z])(?:\^(\d+))?|([+-]?\d+)")


def _poly(text, var="t"):
    """Parse ``2t^2-3t+1`` into ``{exponent: coefficient}``."""
    poly = {}
    for m in _TERM.finditer(text.replace(" ", "")):
        if m.group(3):
            assert m.group(3) == var, text
            coeff = (-1 if m.group(1) == "-" else 1) * (int(m.group(2)) if m.group(2) else 1)
            exp = int(m.group(4)) if m.group(4) else 1
        else:
            coeff, exp = int(m.group(5)), 0
        poly[exp] = poly.get(exp, 0) + coeff
    return poly


def _at(poly, t):
    return sum(c * Fraction(t) ** e for e, c in poly.items())


def _general(text):
    """Parse ``Ax^2+Cy^2+Dx+Ey+F`` into a dict keyed by monomial."""
    out = {}
    for m in re.finditer(r"([+-]?)(\d*)(x\^2|y\^2|xy|x|y)|([+-]?\d+)", text):
        if m.group(3):
            coeff = (-1 if m.group(1) == "-" else 1) * (int(m.group(2)) if m.group(2) else 1)
            out[m.group(3)] = out.get(m.group(3), 0) + coeff
        else:
            out[""] = out.get("", 0) + int(m.group(4))
    return out


def _matrices(problem):
    """Every 2x2 ``bmatrix`` in the problem, as integer rows."""
    found = re.findall(r"\\begin\{bmatrix\} (-?\d+) & (-?\d+) \\\\ (-?\d+) & (-?\d+) "
                       r"\\end\{bmatrix\}", problem)
    return [[[int(a), int(b)], [int(c), int(d)]] for a, b, c, d in found]


def _pair(solution):
    m = re.fullmatch(r"\((-?[\d.]+), (-?[\d.]+)\)", solution)
    assert m, solution
    return float(m.group(1)), float(m.group(2))


def _mv(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1], m[1][0] * v[0] + m[1][1] * v[1])


_NAMED = {
    "counterclockwise rotation of $90^\\circ$": [[0, -1], [1, 0]],
    "rotation of $180^\\circ$": [[-1, 0], [0, -1]],
    "clockwise rotation of $90^\\circ$": [[0, 1], [-1, 0]],
    "reflection over the $x$-axis": [[1, 0], [0, -1]],
    "reflection over the $y$-axis": [[-1, 0], [0, 1]],
    "reflection over the line $y = x$": [[0, 1], [1, 0]],
}


def _named_matrix(desc):
    m = re.search(r"dilation centered at the origin with scale factor \$(\d+)\$", desc)
    if m:
        k = int(m.group(1))
        return [[k, 0], [0, k]]
    # Longest key first so "counterclockwise" isn't matched as "clockwise".
    for key in sorted(_NAMED, key=len, reverse=True):
        if key in desc:
            return _NAMED[key]
    raise AssertionError(desc)


class _Base(SimpleTestCase):
    name = None

    def samples(self):
        random.seed(0)
        gen = LOCAL_GENERATORS[self.name]
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            yield problem, solution


_XY = re.compile(r"x\(t\) = (?P<x>[^$]+)\$ and \$y\(t\) = (?P<y>[^$]+)\$")


class ParametricPositionTests(_Base):
    name = "pc_parametric_position"

    def test_answers(self):
        for problem, solution in self.samples():
            m = _XY.search(problem)
            xs, ys = _poly(m.group("x")), _poly(m.group("y"))
            pos = re.search(r"position of the particle at \$t = (\d+)\$", problem)
            if pos:
                t = int(pos.group(1))
                self.assertEqual(solution, f"({_at(xs, t)}, {_at(ys, t)})", problem)
            else:
                q = re.search(r"\$(\w)\$-coordinate equal to \$(-?\d+)\$", problem)
                poly = xs if q.group(1) == "x" else ys
                self.assertEqual(max(poly), 1, problem)  # linear: unique time
                t = int(solution)
                self.assertGreaterEqual(t, 0)
                self.assertEqual(_at(poly, t), int(q.group(2)), problem)


class ParametricRateTests(_Base):
    name = "pc_parametric_rate_of_change"

    def test_answers(self):
        for problem, solution in self.samples():
            m = _XY.search(problem)
            xs, ys = _poly(m.group("x")), _poly(m.group("y"))
            single = re.search(r"of \$(\w)\(t\)\$ with respect to \$t\$ on the interval "
                               r"\$\[(\d+), (\d+)\]\$", problem)
            if single:
                poly = xs if single.group(1) == "x" else ys
                t1, t2 = int(single.group(2)), int(single.group(3))
                expected = (_at(poly, t2) - _at(poly, t1)) / (t2 - t1)
            else:
                t1, t2 = map(int, re.search(r"from \$t = (\d+)\$ to \$t = (\d+)\$",
                                            problem).groups())
                expected = (_at(ys, t2) - _at(ys, t1)) / (_at(xs, t2) - _at(xs, t1))
            self.assertEqual(Fraction(solution), expected, problem)


class ParametricCircleLineTests(_Base):
    name = "pc_parametric_circle_line"

    @staticmethod
    def _trig(text, fn):
        m = re.fullmatch(rf"(?:(-?\d+) \+ )?(\d*)\\{fn} t", text)
        return int(m.group(1) or 0), int(m.group(2) or 1)

    def test_answers(self):
        for problem, solution in self.samples():
            if "circle" in problem:
                m = re.search(r"x\(t\) = ([^$]+)\$, \$y\(t\) = ([^$]+)\$", problem)
                h, r1 = self._trig(m.group(1), "cos")
                k, r2 = self._trig(m.group(2), "sin")
                self.assertEqual(r1, r2)
                expected = f"({h}, {k})" if "center" in problem else str(r1)
                self.assertEqual(solution, expected, problem)
            else:
                p, q = re.findall(r"\((-?\d+), (-?\d+)\)", problem)[:2]
                num, den = map(int, re.search(r"t = \\frac\{(\d+)\}\{(\d+)\}", problem).groups())
                t = Fraction(num, den)
                x = int(p[0]) + (int(q[0]) - int(p[0])) * t
                y = int(p[1]) + (int(q[1]) - int(p[1])) * t
                self.assertEqual(x.denominator, 1)
                self.assertEqual(solution, f"({x}, {y})", problem)
                # The stated parametrization really is the segment P -> Q.
                xt = _poly(re.search(r"x\(t\) = ([^$]+)\$", problem).group(1))
                self.assertEqual(_at(xt, 0), int(p[0]))
                self.assertEqual(_at(xt, 1), int(q[0]))


class ImplicitCurveTests(_Base):
    name = "pc_implicit_curve_points"

    def test_answers(self):
        for problem, solution in self.samples():
            eq = _general(re.search(r"implicitly by \$([^=]+)=", problem).group(1))
            c = int(re.search(r"=(-?\d+)\$", problem).group(1))
            x = int(re.search(r"point \$\((-?\d+), y\)\$", problem).group(1))
            # Brute-force every integer y; the generator promises integer roots.
            expected = [y for y in range(-50, 51)
                        if eq.get("x^2", 0) * x * x + eq.get("xy", 0) * x * y
                        + eq.get("y^2", 0) * y * y == c]
            values = [int(v) for v in solution.split(", ")]
            self.assertEqual(values, expected, problem)
            # ...and there are no non-integer roots: the quadratic in y has
            # at most two roots, so it's enough that we found all of them.
            disc = (eq.get("xy", 0) * x) ** 2 - 4 * (x * x * eq.get("x^2", 0) - c)
            self.assertEqual(math.isqrt(disc) ** 2, disc, problem)


class ClassifyConicTests(_Base):
    name = "pc_classify_conic"

    def test_answers(self):
        for problem, solution in self.samples():
            g = _general(re.search(r"conic section \$(.+)=0\$", problem).group(1))
            A, C, D, E, F = (g.get(k, 0) for k in ("x^2", "y^2", "x", "y", ""))
            if A * C == 0:
                expected = "parabola"
                self.assertNotEqual(A + C, 0)
                self.assertNotEqual(E if A else D, 0, problem)  # not degenerate
            elif A == C:
                expected = "circle"
                # Complete the square: r^2 = (D^2 + E^2)/(4A^2) - F/A > 0.
                self.assertGreater(Fraction(D * D + E * E, 4 * A * A) - Fraction(F, A), 0)
            elif A * C > 0:
                expected = "ellipse"
                rhs = Fraction(D * D, 4 * A) + Fraction(E * E, 4 * C) - F
                self.assertGreater(rhs / A, 0, problem)
            else:
                expected = "hyperbola"
                rhs = Fraction(D * D, 4 * A) + Fraction(E * E, 4 * C) - F
                self.assertNotEqual(rhs, 0, problem)
            self.assertEqual(solution, expected, problem)


class ParametrizeEllipseTests(_Base):
    name = "pc_parametrize_ellipse"
    ELLIPSE = re.compile(r"\\frac\{(?P<x>[^}]+)\}\{(?P<a2>\d+)\} \+ "
                         r"\\frac\{(?P<y>[^}]+)\}\{(?P<b2>\d+)\} = 1")

    @staticmethod
    def _center(text):
        m = re.fullmatch(r"\(\w([+-])(\d+)\)\^2|\w\^2", text)
        if m.group(1) is None:
            return 0
        return int(m.group(2)) * (1 if m.group(1) == "-" else -1)

    @staticmethod
    def _angle(tex):
        if tex == "0":
            return 0.0
        m = re.fullmatch(r"\\frac\{(\d*)\\pi\}\{(\d+)\}|(\d*)\\pi", tex)
        if m.group(2):
            return int(m.group(1) or 1) * math.pi / int(m.group(2))
        return int(m.group(3) or 1) * math.pi

    def test_answers(self):
        for problem, solution in self.samples():
            m = self.ELLIPSE.search(problem)
            h, k = self._center(m.group("x")), self._center(m.group("y"))
            a, b = math.isqrt(int(m.group("a2"))), math.isqrt(int(m.group("b2")))
            self.assertEqual(a * a, int(m.group("a2")))
            if "value of $p$" in problem:
                expected = a if r"p\cos t" in problem else b
                self.assertEqual(solution, str(expected), problem)
            else:
                t = self._angle(re.search(r"at \$t = ([^$]+)\$", problem).group(1))
                x, y = _pair(solution)
                self.assertAlmostEqual(x, h + a * math.cos(t), delta=0.0006, msg=problem)
                self.assertAlmostEqual(y, k + b * math.sin(t), delta=0.0006, msg=problem)


class VectorValuedTests(_Base):
    name = "pc_vector_valued_function"

    def test_answers(self):
        for problem, solution in self.samples():
            m = re.search(r"\\langle (.+?), (.+?) \\rangle\$", problem)
            xs, ys = _poly(m.group(1)), _poly(m.group(2))
            pos = re.search(r"position vector \$p\((\d+)\)\$", problem)
            if pos:
                t = int(pos.group(1))
                self.assertEqual(solution, f"({_at(xs, t)}, {_at(ys, t)})", problem)
                continue
            m2 = (re.search(r"p\((\d+)\) - p\((\d+)\)", problem)
                  or re.search(r"t = (\d+)\$ and \$t = (\d+)", problem))
            ta, tb = int(m2.group(1)), int(m2.group(2))
            dx, dy = _at(xs, ta) - _at(xs, tb), _at(ys, ta) - _at(ys, tb)
            if "displacement vector $p" in problem:
                self.assertEqual(solution, f"({dx}, {dy})", problem)
            else:
                self.assertAlmostEqual(float(solution), math.hypot(dx, dy), delta=0.0006)


class InverseMatrixEntryTests(_Base):
    name = "pc_inverse_matrix_entry"

    def test_answers(self):
        for problem, solution in self.samples():
            (a, b), (c, d) = _matrices(problem)[0]
            i, j = map(int, re.search(r"row (\d), column (\d)", problem).groups())
            det = a * d - b * c
            self.assertNotEqual(det, 0)
            inv = [[Fraction(d, det), Fraction(-b, det)], [Fraction(-c, det), Fraction(a, det)]]
            # Check A * A^-1 = I, then the requested entry.
            for r in range(2):
                for s in range(2):
                    self.assertEqual(sum([[a, b], [c, d]][r][k] * inv[k][s] for k in range(2)),
                                     int(r == s))
            self.assertEqual(Fraction(solution), inv[i - 1][j - 1], problem)


class MatrixTransformPointTests(_Base):
    name = "pc_matrix_transform_point"

    def test_answers(self):
        for problem, solution in self.samples():
            point = tuple(map(int, re.search(r"point \$\((-?\d+), (-?\d+)\)\$", problem).groups()))
            mats = _matrices(problem)
            m = mats[0] if mats else _named_matrix(problem.split(" is ", 1)[1].split(". Find")[0])
            self.assertEqual(_pair(solution), _mv(m, point), problem)

    def test_named_rotation_geometry(self):
        """The named matrices really rotate/reflect: check against trig."""
        x, y = 3, 1
        for key, deg in (("counterclockwise rotation of $90^\\circ$", 90),
                         ("rotation of $180^\\circ$", 180),
                         ("clockwise rotation of $90^\\circ$", -90)):
            th = math.radians(deg)
            expected = (x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th))
            got = _mv(_NAMED[key], (x, y))
            self.assertAlmostEqual(got[0], expected[0])
            self.assertAlmostEqual(got[1], expected[1])


class MatrixCompositionTests(_Base):
    name = "pc_matrix_composition"

    def test_answers(self):
        for problem, solution in self.samples():
            mats = _matrices(problem)
            if "area" in problem or "scale areas" in problem:
                (a, b), (c, d) = mats[0]
                det = abs(a * d - b * c)
                self.assertNotEqual(det, 0)
                area = re.search(r"with area \$(\d+)\$", problem)
                expected = det * int(area.group(1)) if area else det
                self.assertEqual(solution, str(expected), problem)
            elif "Find $P$" in problem:
                image = tuple(map(int, re.search(r"to \$\((-?\d+), (-?\d+)\)\$",
                                                 problem).groups()))
                p = _pair(solution)
                self.assertEqual(_mv(mats[0], p), image, problem)
            else:
                point = tuple(map(int, re.search(r"point \$\((-?\d+), (-?\d+)\)\$",
                                                 problem).groups()))
                if mats:
                    first, second = mats
                else:
                    m = re.search(r"transformed by (.+?), and the result is then transformed "
                                  r"by (.+?)\. Find", problem)
                    first, second = _named_matrix(m.group(1)), _named_matrix(m.group(2))
                self.assertEqual(_pair(solution), _mv(second, _mv(first, point)), problem)


class MarkovTransitionTests(_Base):
    name = "pc_markov_transition"
    PATTERN = re.compile(
        r"\$(?P<stay>\d+)\\%\$ of the \w+ at (?P<s1>.+?) stay there.*?"
        r"\$(?P<switch>\d+)\\%\$ of the \w+ at (?P<s2>.+?) move to.*?"
        r"has \$(?P<n1>\d+)\$ \w+ and .+? has \$(?P<n2>\d+)\$\. "
        r"How many \w+ will be at (?P<target>.+?) after (?P<k>\d) ")

    def test_answers(self):
        for problem, solution in self.samples():
            m = self.PATTERN.search(problem)
            self.assertIsNotNone(m, problem)
            stay, switch = Fraction(int(m["stay"]), 100), Fraction(int(m["switch"]), 100)
            a, b = Fraction(int(m["n1"])), Fraction(int(m["n2"]))
            for _ in range(int(m["k"])):
                # Simulate people moving rather than multiplying a matrix.
                a, b = a * stay + b * switch, a * (1 - stay) + b * (1 - switch)
            self.assertEqual(a + b, int(m["n1"]) + int(m["n2"]))  # nobody lost
            expected = a if m["target"] == m["s1"] else b
            self.assertEqual(expected.denominator, 1)
            self.assertEqual(solution, str(expected), problem)
