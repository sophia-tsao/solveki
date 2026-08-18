"""Math-correctness tests for the newer Precalculus generators.

Covers the unit-circle family, the quadratic-form (u-substitution) trig
equation, and the rational-function topics (asymptotes, holes, zeros,
intercepts, inequalities). Each test parses the generated problem, recomputes
the answer independently, and asserts the stated solution matches, over many
random samples under a fixed seed.
"""
import math
import random
import re
from fractions import Fraction

from django.test import TestCase

from myapp.generators import precalculus  # noqa: F401  (registers generators)
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000


def _parse_factored(s):
    """Parse '2(x-3)(x+1)', '-x', '(x-4)x' etc. into (lead, [roots])."""
    lead = 1
    rest = s
    m = re.match(r"^(-?\d+)", rest)
    if m:
        lead = int(m.group(1))
        rest = rest[m.end():]
    elif rest.startswith("-"):
        lead = -1
        rest = rest[1:]
    roots = [-int(c) for c in re.findall(r"\(x([+-]\d+)\)", rest)]
    rest2 = re.sub(r"\(x[+-]\d+\)", "", rest)
    roots += [0] * rest2.count("x")
    return lead, roots


_POLY_TERM = re.compile(r"([+-]?)(\d*)x\^(\d+)|([+-]?)(\d*)x(?!\^)|([+-]?\d+)(?!x)")


def _poly_from_str(s):
    """Parse a rendered polynomial into ``{exponent: coefficient}``."""
    poly = {}
    for m in _POLY_TERM.finditer(s):
        if m.group(3) is not None:
            sign = -1 if m.group(1) == "-" else 1
            mag = int(m.group(2)) if m.group(2) else 1
            poly[int(m.group(3))] = poly.get(int(m.group(3)), 0) + sign * mag
        elif m.group(0).endswith("x"):
            sign = -1 if m.group(4) == "-" else 1
            mag = int(m.group(5)) if m.group(5) else 1
            poly[1] = poly.get(1, 0) + sign * mag
        elif m.group(6):
            poly[0] = poly.get(0, 0) + int(m.group(6))
    return poly


def _angle_value(s):
    """Parse an ``_angle_latex`` token back into radians."""
    if s == "0":
        return 0.0
    mfrac = re.fullmatch(r"\\frac\{(\d*)\\pi\}\{(\d+)\}", s)
    if mfrac:
        num = int(mfrac.group(1)) if mfrac.group(1) else 1
        return num * math.pi / int(mfrac.group(2))
    mtop = re.fullmatch(r"(\d*)\\pi", s)
    num = int(mtop.group(1)) if mtop.group(1) else 1
    return num * math.pi


_FRAC = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")


class UnitCirclePointTests(TestCase):
    ANG = re.compile(r"\\theta = (?P<ang>[^$]+)\$")
    SOL = re.compile(r"\((?P<x>-?[\d.]+), (?P<y>-?[\d.]+)\)")

    def test_point_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_unit_circle_point"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.ANG.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            theta = _angle_value(m.group("ang").strip())
            s = self.SOL.search(solution)
            self.assertAlmostEqual(float(s.group("x")), math.cos(theta), places=3,
                                   msg=f"{problem!r} -> {solution!r}")
            self.assertAlmostEqual(float(s.group("y")), math.sin(theta), places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class UnitCircleTrigTests(TestCase):
    ANG = re.compile(r"\\(?P<fn>sin|cos|tan)\\left\((?P<ang>.+?)\\right\)")
    SOL = re.compile(r"\$(?P<v>-?[\d.]+)\$")

    def _check(self, name, fn):
        random.seed(0)
        gen = LOCAL_GENERATORS[name]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.ANG.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            theta = _angle_value(m.group("ang"))
            stated = float(self.SOL.search(solution).group("v"))
            self.assertAlmostEqual(stated, fn(theta), places=3,
                                   msg=f"{problem!r} -> {solution!r}")

    def test_sin(self):
        self._check("pc_unit_circle_sin", math.sin)

    def test_cos(self):
        self._check("pc_unit_circle_cos", math.cos)

    def test_tan(self):
        self._check("pc_unit_circle_tan", math.tan)


class TrigQuadraticTests(TestCase):
    EQ = re.compile(r"Solve \$(?P<eq>.+?) = 0\$")
    SOL = re.compile(r"\$(?P<sols>[-\d,\s]*)\$")

    @staticmethod
    def _coeff(token):
        if token in ("", "+"):
            return 1
        if token == "-":
            return -1
        return int(token)

    def test_solutions_solve_the_quadratic(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_trig_quadratic"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            eq = self.EQ.search(problem).group("eq")
            func = "sin" if "\\sin" in eq else "cos"
            fn = math.sin if func == "sin" else math.cos
            a = self._coeff(re.search(rf"(-?\d*)\\{func}\^2\(x\)", eq).group(1))
            mb = re.search(rf"([+-]\d*)\\{func}\(x\)", eq)
            b = self._coeff(mb.group(1)) if mb else 0
            mc = re.search(r"([+-]\d+)$", eq)
            c = int(mc.group(1)) if mc else 0
            raw = self.SOL.search(solution).group("sols").strip()
            stated = set(int(t) for t in raw.split(",")) if raw else set()
            self.assertTrue(stated, f"no solutions: {problem!r} -> {solution!r}")
            # Independently solve the quadratic in u, then find the integer
            # degrees whose sin/cos hits a root (the same criterion the
            # generator uses). Comparing degree-sets is robust near double
            # roots, where evaluating the quadratic gives tiny nonzero values.
            disc = b * b - 4 * a * c
            self.assertGreaterEqual(disc, 0, f"complex roots: {problem!r}")
            sq = math.sqrt(disc)
            roots = [(-b + sq) / (2 * a), (-b - sq) / (2 * a)]
            expected = set()
            for d in range(360):
                u = fn(math.radians(d))
                if any(abs(u - r) < 1e-6 for r in roots):
                    expected.add(d)
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class RationalVerticalAsymptoteTests(TestCase):
    def test_va(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_rational_vertical_asymptotes"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = _FRAC.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            _, num_roots = _parse_factored(m.group(1))
            _, den_roots = _parse_factored(m.group(2))
            expected = sorted(set(den_roots) - set(num_roots))
            exp = ", ".join(str(v) for v in expected) if expected else "none"
            self.assertEqual(solution.strip(), exp, f"{problem!r} -> {solution!r}")


class RationalZerosTests(TestCase):
    def test_zeros(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_rational_zeros"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = _FRAC.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            _, num_roots = _parse_factored(m.group(1))
            _, den_roots = _parse_factored(m.group(2))
            expected = sorted(set(num_roots) - set(den_roots))
            exp = ", ".join(str(v) for v in expected) if expected else "none"
            self.assertEqual(solution.strip(), exp, f"{problem!r} -> {solution!r}")


class RationalHolesTests(TestCase):
    SOL = re.compile(r"\((?P<x>-?\d+), (?P<y>-?\d+(?:/-?\d+)?)\)")

    def test_hole(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_rational_holes"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = _FRAC.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            ln, num_roots = _parse_factored(m.group(1))
            ld, den_roots = _parse_factored(m.group(2))
            shared = set(num_roots) & set(den_roots)
            self.assertEqual(len(shared), 1, f"expected one shared root: {problem!r}")
            h = next(iter(shared))
            nr, dr = list(num_roots), list(den_roots)
            nr.remove(h)
            dr.remove(h)
            num_val = Fraction(ln)
            for r in nr:
                num_val *= (h - r)
            den_val = Fraction(ld)
            for r in dr:
                den_val *= (h - r)
            y = num_val / den_val
            s = self.SOL.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            self.assertEqual(int(s.group("x")), h, f"{problem!r} -> {solution!r}")
            self.assertEqual(Fraction(s.group("y")), y, f"{problem!r} -> {solution!r}")


class RationalHorizontalAsymptoteTests(TestCase):
    def test_ha(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_rational_horizontal_asymptote"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = _FRAC.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            ln, num_roots = _parse_factored(m.group(1))
            ld, den_roots = _parse_factored(m.group(2))
            nd, dd = len(num_roots), len(den_roots)
            if nd < dd:
                exp = "0"
            elif nd == dd:
                fr = Fraction(ln, ld)
                exp = (str(fr.numerator) if fr.denominator == 1
                       else f"{fr.numerator}/{fr.denominator}")
            else:
                exp = "none"
            self.assertEqual(solution.strip(), exp, f"{problem!r} -> {solution!r}")


class RationalSlantAsymptoteTests(TestCase):
    SOL = re.compile(r"y = (?P<slope>-?\d*)x(?P<int> [+-] \d+)?")

    def test_slant(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_rational_slant_asymptote"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = _FRAC.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            poly = _poly_from_str(m.group(1))
            _, den_roots = _parse_factored(m.group(2))
            self.assertEqual(len(den_roots), 1, f"denominator not linear: {problem!r}")
            q = den_roots[0]
            s = self.SOL.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            slope_raw = s.group("slope")
            slope = -1 if slope_raw == "-" else (1 if slope_raw == "" else int(slope_raw))
            b = int(s.group("int").replace(" ", "")) if s.group("int") else 0

            def nval(x):
                return sum(c * x ** e for e, c in poly.items())

            r = nval(q)  # remainder of the division
            for x in (-3, 0, 2, 5):
                self.assertEqual(nval(x), (slope * x + b) * (x - q) + r,
                                 f"x={x}: {problem!r} -> {solution!r}")


class RationalYInterceptTests(TestCase):
    def test_y_intercept(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_rational_y_intercept"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = _FRAC.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            ln, num_roots = _parse_factored(m.group(1))
            ld, den_roots = _parse_factored(m.group(2))
            num0 = ln
            for r in num_roots:
                num0 *= (0 - r)
            den0 = ld
            for r in den_roots:
                den0 *= (0 - r)
            y = Fraction(num0, den0)
            exp = (str(y.numerator) if y.denominator == 1
                   else f"{y.numerator}/{y.denominator}")
            self.assertEqual(solution.strip(), exp, f"{problem!r} -> {solution!r}")


class RationalInequalityTests(TestCase):
    PAT = re.compile(
        r"\\frac\{(?P<num>[^{}]+)\}\{(?P<den>[^{}]+)\} (?P<rel>>|<|\\ge|\\le) 0"
    )

    @staticmethod
    def _intervals(sol):
        out = []
        for piece in sol.split(" U "):
            piece = piece.strip()
            lb = piece[0] == "["
            rb = piece[-1] == "]"
            a, b = piece[1:-1].split(", ")
            lo = float("-inf") if a == "-inf" else float(a)
            hi = float("inf") if b == "inf" else float(b)
            out.append((lo, lb, hi, rb))
        return out

    @staticmethod
    def _member(intervals, x):
        for lo, li, hi, ri in intervals:
            if lo < x < hi:
                return True
            if x == lo and li:
                return True
            if x == hi and ri:
                return True
        return False

    def test_solution_set(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_rational_inequality"]
        holds = {">": lambda g: g > 0, "<": lambda g: g < 0,
                 "\\ge": lambda g: g >= 0, "\\le": lambda g: g <= 0}
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PAT.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            z = _parse_factored(m.group("num"))[1][0]
            p = _parse_factored(m.group("den"))[1][0]
            test = holds[m.group("rel")]
            intervals = self._intervals(solution.strip())
            for t in range(-24, 25):
                x = t / 2
                if x == p:
                    self.assertFalse(
                        self._member(intervals, x),
                        f"asymptote included: {problem!r} -> {solution!r}")
                    continue
                g = (x - z) / (x - p)
                self.assertEqual(
                    self._member(intervals, x), test(g),
                    f"x={x}: {problem!r} -> {solution!r}")


class SinusoidFeaturesTests(TestCase):
    EQ = re.compile(
        r"y = (?P<amp>-?\d*)\\(?P<fn>sin|cos)\((?P<b>\d*)x "
        r"(?P<csign>[+-]) (?P<c>\d+)\)(?P<tail> [+-] \d+)?"
    )

    def test_features(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_sinusoid_features"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.EQ.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            amp = m.group("amp")
            A_abs = 1 if amp in ("", "-") else abs(int(amp))
            B = int(m.group("b")) if m.group("b") else 1
            c_mag = int(m.group("c"))
            C = c_mag if m.group("csign") == "-" else -c_mag
            tail = m.group("tail")
            D = int(tail.replace(" ", "")) if tail else 0

            if "amplitude" in problem:
                self.assertEqual(solution, f"${A_abs}$",
                                 f"{problem!r} -> {solution!r}")
            elif "period" in problem:
                stated = float(re.search(r"\$(-?[\d.]+)\$", solution).group(1))
                self.assertAlmostEqual(stated, 2 * math.pi / B, places=3,
                                       msg=f"{problem!r} -> {solution!r}")
            elif "midline" in problem:
                self.assertEqual(solution, f"$y = {D}$",
                                 f"{problem!r} -> {solution!r}")
            else:  # phase shift
                stated = re.search(r"\$(-?\d+(?:/-?\d+)?)\$", solution).group(1)
                self.assertEqual(Fraction(stated), Fraction(C, B),
                                 f"{problem!r} -> {solution!r}")


class SumDifferenceValuesTests(TestCase):
    P = re.compile(
        r"\\(?P<fn>sin|cos|tan)\((?P<a>\d+)\^\\circ (?P<op>[+-]) "
        r"(?P<b>\d+)\^\\circ\)"
    )
    SOL = re.compile(r"\$(?P<v>-?[\d.]+)\$")

    def test_values(self):
        random.seed(0)
        fns = {"sin": math.sin, "cos": math.cos, "tan": math.tan}
        gen = LOCAL_GENERATORS["pc_sum_difference_values"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b = int(m.group("a")), int(m.group("b"))
            angle = a + b if m.group("op") == "+" else a - b
            expected = fns[m.group("fn")](math.radians(angle))
            stated = float(self.SOL.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class HalfAngleValuesTests(TestCase):
    P = re.compile(
        r"\\(?P<fn>sin|cos|tan)\\left\(\\frac\{(?P<full>\d+)\^\\circ\}\{2\}"
        r"\\right\)"
    )
    SOL = re.compile(r"\$(?P<v>-?[\d.]+)\$")

    def test_values(self):
        random.seed(0)
        fns = {"sin": math.sin, "cos": math.cos, "tan": math.tan}
        gen = LOCAL_GENERATORS["pc_half_angle_values"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            half = int(m.group("full")) / 2
            expected = fns[m.group("fn")](math.radians(half))
            stated = float(self.SOL.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class BinomialTermTests(TestCase):
    BASE = re.compile(
        r"\((?P<a>-?\d*)x (?P<bsign>[+-]) (?P<b>\d+)\)\^\{(?P<n>\d+)\}"
    )
    KTERM = re.compile(r"coefficient of the \$x(?:\^\{(?P<k>\d+)\})?\$")

    def test_coefficient(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_binomial_term"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            mb = self.BASE.search(problem)
            mk = self.KTERM.search(problem)
            self.assertIsNotNone(mb, f"could not parse base: {problem!r}")
            self.assertIsNotNone(mk, f"could not parse term: {problem!r}")
            a_raw = mb.group("a")
            a = 1 if a_raw == "" else (-1 if a_raw == "-" else int(a_raw))
            b_mag = int(mb.group("b"))
            b = b_mag if mb.group("bsign") == "+" else -b_mag
            n = int(mb.group("n"))
            k = int(mk.group("k")) if mk.group("k") else 1
            expected = math.comb(n, k) * a ** k * b ** (n - k)
            self.assertEqual(int(solution.strip("$")), expected,
                             f"{problem!r} -> {solution!r}")


class DeMoivreTests(TestCase):
    P = re.compile(
        r"\\left\((?P<r>\d+)\(\\cos (?P<theta>\d+)\^\\circ \+ i\\sin "
        r"\d+\^\\circ\)\\right\)\^\{(?P<n>\d+)\}"
    )
    SOL = re.compile(r"\$(?P<a>-?[\d.]+)(?P<b>[+-][\d.]+)i\$")

    def test_rectangular(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_de_moivre"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.P.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            r = int(m.group("r"))
            theta = int(m.group("theta"))
            n = int(m.group("n"))
            mag = r ** n
            ang = math.radians(n * theta)
            ex_x = mag * math.cos(ang)
            ex_y = mag * math.sin(ang)
            s = self.SOL.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            self.assertAlmostEqual(float(s.group("a")), ex_x, places=3,
                                   msg=f"{problem!r} -> {solution!r}")
            self.assertAlmostEqual(float(s.group("b")), ex_y, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


def _trig_to_py(expr):
    """Turn a LaTeX/typeable trig expression into a Python-evaluable string."""
    e = expr
    while "\\frac" in e:
        e = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", e)
    e = e.replace("\\", "")
    e = re.sub(r"(sin|cos|tan|sec|csc|cot)\^2\(x\)", r"(\1(x))**2", e)
    e = re.sub(r"\)(?=[a-z(])", ")*", e)
    return e


def _trig_val(expr, x):
    ns = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sec": lambda t: 1 / math.cos(t),
        "csc": lambda t: 1 / math.sin(t),
        "cot": lambda t: math.cos(t) / math.sin(t),
        "x": x,
    }
    return eval(_trig_to_py(expr), {"__builtins__": {}}, ns)


class SimplifyTrigIdentityTests(TestCase):
    LHS = re.compile(r"Simplify the expression \$(?P<lhs>.+?)\$ using")

    def test_identity(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_simplify_trig_identity"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.LHS.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            lhs = m.group("lhs")
            ans = solution.strip("$")
            for x in (0.3, 0.7, 1.0, 2.0, 2.5, 3.0):
                self.assertAlmostEqual(
                    _trig_val(lhs, x), _trig_val(ans, x), places=6,
                    msg=f"x={x}: {problem!r} -> {solution!r}")


class RecursiveSequenceTermTests(TestCase):
    A1 = re.compile(r"a_1 = (-?\d+)")
    REC = re.compile(r"a_n = (-?\d*)a_\{n-1\} ([+-]) (\d+)")
    N = re.compile(r"Find \$a_\{(\d+)\}\$")

    def test_term(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_recursive_sequence_term"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            ma1 = self.A1.search(problem)
            mrec = self.REC.search(problem)
            mn = self.N.search(problem)
            self.assertIsNotNone(ma1, f"could not parse: {problem!r}")
            self.assertIsNotNone(mrec, f"could not parse: {problem!r}")
            self.assertIsNotNone(mn, f"could not parse: {problem!r}")
            a1 = int(ma1.group(1))
            raw = mrec.group(1)
            r = 1 if raw == "" else (-1 if raw == "-" else int(raw))
            d = int(mrec.group(3))
            if mrec.group(2) == "-":
                d = -d
            n = int(mn.group(1))
            value = a1
            for _ in range(n - 1):
                value = value * r + d
            self.assertEqual(int(solution.strip("$")), value,
                             f"{problem!r} -> {solution!r}")


class PartialFractionsTests(TestCase):
    TARGET = re.compile(r"over the factor \$(?P<factor>[^$]+)\$")

    def test_numerator(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_partial_fractions"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = _FRAC.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            poly = _poly_from_str(m.group(1))
            _, den_roots = _parse_factored(m.group(2))
            self.assertEqual(len(den_roots), 2, f"expected two roots: {problem!r}")
            mt = self.TARGET.search(problem)
            self.assertIsNotNone(mt, f"could not parse target: {problem!r}")
            _, troots = _parse_factored(mt.group("factor"))
            target = troots[0]
            others = list(den_roots)
            others.remove(target)
            # cover-up: A = numerator(target) / prod(target - other_roots)
            num_val = Fraction(poly.get(1, 0)) * target + Fraction(poly.get(0, 0))
            denom = Fraction(1)
            for o in others:
                denom *= (target - o)
            expected = num_val / denom
            self.assertEqual(Fraction(solution.strip()), expected,
                             f"{problem!r} -> {solution!r}")


def _eval_side(side, x, y):
    """Evaluate one side of a rectangular equation at ``(x, y)``."""
    e = side.replace("^", "**")
    e = re.sub(r"(\d)(?=[xy])", r"\1*", e)
    return eval(e, {"__builtins__": {}}, {"x": x, "y": y})


class PolarRectangularEquationTests(TestCase):
    POLAR = re.compile(r"polar equation \$(?P<polar>.+?)\$ to")
    THETAS = (0.3, 0.6, 1.0, 1.4, 2.0, 2.5)

    def _points(self, polar):
        """Yield (x, y) points on the polar curve for the sample thetas."""
        pts = []
        for th in self.THETAS:
            m = re.fullmatch(r"r = (\d+)", polar)
            if m:
                r = int(m.group(1))
            elif re.fullmatch(r"r\\cos\\theta = \d+", polar):
                c = int(re.search(r"= (\d+)", polar).group(1))
                r = c / math.cos(th)
            elif re.fullmatch(r"r\\sin\\theta = \d+", polar):
                c = int(re.search(r"= (\d+)", polar).group(1))
                r = c / math.sin(th)
            elif re.fullmatch(r"r = \d+\\cos\\theta", polar):
                a = int(re.search(r"r = (\d+)", polar).group(1))
                r = a * math.cos(th)
            elif re.fullmatch(r"r = \d+\\sin\\theta", polar):
                a = int(re.search(r"r = (\d+)", polar).group(1))
                r = a * math.sin(th)
            else:
                raise AssertionError(f"unknown polar form: {polar!r}")
            pts.append((r * math.cos(th), r * math.sin(th)))
        return pts

    def test_conversion(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_polar_rectangular_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.POLAR.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            polar = m.group("polar")
            lhs, rhs = solution.strip("$").split(" = ")
            for x, y in self._points(polar):
                self.assertAlmostEqual(
                    _eval_side(lhs, x, y), _eval_side(rhs, x, y), places=6,
                    msg=f"{problem!r} -> {solution!r} at ({x}, {y})")


class OrthogonalProjectionTests(TestCase):
    PROBLEM = re.compile(
        r"\\vec\{a\} = \\langle (?P<ax>-?\d+), (?P<ay>-?\d+) \\rangle\$ onto "
        r"\$\\vec\{b\} = \\langle (?P<bx>-?\d+), (?P<by>-?\d+) \\rangle"
    )

    def test_orthogonal_projection(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["pc_orthogonal_projection"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            ax, ay, bx, by = (int(m.group(g)) for g in ("ax", "ay", "bx", "by"))
            norm_sq = bx * bx + by * by
            norm = math.isqrt(norm_sq)
            self.assertEqual(
                norm * norm, norm_sq, f"b norm not integer: {problem!r}"
            )
            expected = Fraction(ax * bx + ay * by, norm)
            body = solution.strip("$")
            if "/" in body:
                p, q = body.split("/")
                stated = Fraction(int(p), int(q))
            else:
                stated = Fraction(int(body))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")
