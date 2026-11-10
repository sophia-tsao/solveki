"""Math-correctness tests for the AP Precalculus variants (ap_precalc_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently (numerically or by brute force), and checks the served solution,
over 2000 seeded samples.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators import ap_precalc_variants  # noqa: F401 - attaches the variants
from myapp.tests.test_prealgebra_variants_math import INT, frac, table_rows

SAMPLES = 2000
TOL = 0.0005 + 1e-9
NUM = r"(-?\d+(?:\.\d+)?)"
FRAC = r"(-?\d+(?:/\d+)?)"


class _Base(SimpleTestCase):
    name = variant = None

    def samples(self):
        random.seed(0)
        gen = LOCAL_GENERATORS[self.name]
        for _ in range(SAMPLES):
            problem, solution, _steps = gen(variant=self.variant)
            yield problem, solution.replace("$", "").strip()

    def search(self, pattern, problem):
        m = re.search(pattern, problem)
        self.assertIsNotNone(m, problem)
        return m

    def close(self, solution, value, problem):
        self.assertAlmostEqual(float(solution), float(value), delta=TOL, msg=problem)


class TandemFromRates(_Base):
    name, variant = "pc_change_in_tandem", "from_rates"

    def test(self):
        for problem, solution in self.samples():
            rates = [int(v) for v in re.findall(r"\$(-?\d+)\$ on", problem)]
            # Build f from the rates and check its second differences' sign.
            f = [0]
            for r in rates:
                f.append(f[-1] + r)
            second = [f[i + 2] - 2 * f[i + 1] + f[i] for i in range(len(f) - 2)]
            want = "concave up" if all(d > 0 for d in second) else ("concave down" if all(d < 0 for d in second) else None)
            self.assertEqual(solution, want, problem)


class SecondDifferencesMissing(_Base):
    name, variant = "pc_second_differences", "missing_entry"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = table_rows(problem)
            hole = ys.index("?")
            pts = [(int(x), int(y)) for x, y in zip(xs, ys) if y != "?"]
            # Fit a quadratic through three known points (Lagrange) and evaluate at the hole.
            (x0, y0), (x1, y1), (x2, y2) = pts[:3]
            x = int(xs[hole])
            L = lambda xa, xb, xc: Fraction((x - xb) * (x - xc), (xa - xb) * (xa - xc))  # noqa: E731
            value = y0 * L(x0, x1, x2) + y1 * L(x1, x0, x2) + y2 * L(x2, x0, x1)
            self.assertEqual(int(solution), value, problem)


class SecondDifferencesLeading(_Base):
    name, variant = "pc_second_differences", "leading_from_difference"

    def test(self):
        for problem, solution in self.samples():
            h, d = self.search(r"\$x\$-values \$(\d+)\$ apart, and its second differences are all \$" + NUM, problem).groups()
            a = frac(solution)
            f = lambda x: a * x * x + 3 * x - 7  # noqa: E731
            h = int(h)
            self.assertEqual(f(2 * h) - 2 * f(h) + f(0), Fraction(d), problem)


class DifferencesLeadingCoefficient(_Base):
    name, variant = "pc_degree_from_differences", "leading_coefficient"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"polynomial of degree \$(\d)\$", problem)[1])
            xs, ys = (list(map(int, row)) for row in table_rows(problem))
            # Solve for the coefficients by Gaussian elimination over fractions (Vandermonde).
            rows = [[Fraction(x) ** (n - j) for j in range(n + 1)] + [Fraction(y)] for x, y in zip(xs[:n + 1], ys[:n + 1])]
            for i in range(n + 1):
                piv = next(r for r in range(i, n + 1) if rows[r][i] != 0)
                rows[i], rows[piv] = rows[piv], rows[i]
                for r in range(n + 1):
                    if r != i and rows[r][i] != 0:
                        f = rows[r][i] / rows[i][i]
                        rows[r] = [a - f * b for a, b in zip(rows[r], rows[i])]
            lead = rows[0][-1] / rows[0][0]
            self.assertEqual(int(solution), lead, problem)


class ConjugateMaxReal(_Base):
    name, variant = "pc_complex_conjugate_zeros", "max_real_zeros"

    def test(self):
        for problem, solution in self.samples():
            degree, nonreal = map(int, self.search(r"degree \$(\d+)\$ with real coefficients has exactly \$(\d+)\$", problem).groups())
            self.assertEqual(nonreal % 2, 0)
            self.assertEqual(int(solution), degree - nonreal, problem)


class ConjugateMinimumDegree(_Base):
    name, variant = "pc_complex_conjugate_zeros", "minimum_degree"

    def test(self):
        for problem, solution in self.samples():
            zeros = re.findall(r"\$([^$]+)\$", problem.split("has zeros", 1)[1].split(". What")[0])
            real = [z for z in zeros if "i" not in z]
            nonreal = [z for z in zeros if "i" in z]
            self.assertEqual(int(solution), len(real) + 2 * len(nonreal), problem)


class EvenOddValue(_Base):
    name, variant = "pc_even_odd_function", "value_from_symmetry"

    def test(self):
        for problem, solution in self.samples():
            kind, a, v, neg = self.search(r"an (even|odd) function and \$f\((\d+)\) = " + INT + r"\$\. What is \$f\(" + INT,
                                          problem).groups()
            self.assertEqual(int(neg), -int(a))
            f = (lambda x: int(v) * (x / int(a)) ** 2) if kind == "even" else (lambda x: int(v) * (x / int(a)) ** 3)
            self.assertAlmostEqual(int(solution), f(int(neg)), places=9)


class EvenOddParameter(_Base):
    name, variant = "pc_even_odd_function", "parameter_for_even"

    def test(self):
        for problem, solution in self.samples():
            poly = self.search(r"\$f\(x\) = ([^$]+)\$", problem)[1].replace("k", f"({solution})")
            kind = self.search(r"an (even|odd) function", problem)[1]
            expr = re.sub(r"(\d)x", r"\1*x", poly.replace("^", "**").replace(")x", ")*x"))
            for x in (1.3, 2.7, -0.4):
                fx, fm = eval(expr, {"x": x}), eval(expr, {"x": -x})  # noqa: S307
                self.assertAlmostEqual(fm, fx if kind == "even" else -fx, places=6)


class TransformationPreimage(_Base):
    name, variant = "pc_function_transformation", "preimage"

    def test(self):
        for problem, solution in self.samples():
            gx, gy = self.search(r"point \$\(" + FRAC + ", " + INT + r"\)\$", problem).groups()
            m = self.search(r"g\(x\) = (-?\d*)f\((-?\d*)(?:\(x ([+-]) (\d+)\)|x)\) ([+-]) (\d+)\$", problem)
            a = {"": 1, "-": -1}.get(m[1]) if m[1] in ("", "-") else int(m[1])
            b = {"": 1, "-": -1}.get(m[2]) if m[2] in ("", "-") else int(m[2])
            h = (int(m[4]) * (1 if m[3] == "-" else -1)) if m[3] else 0
            k = int(m[6]) * (1 if m[5] == "+" else -1)
            fx, fy = (frac(v) for v in re.fullmatch(r"\((-?[\d/]+), (-?[\d/]+)\)", solution).groups())
            # g(gx) = a f(b(gx - h)) + k must equal gy, with f(fx) = fy and fx = b(gx - h).
            self.assertEqual(b * (frac(gx) - h), fx, problem)
            self.assertEqual(a * fy + k, int(gy), problem)


class TransformationNewMaximum(_Base):
    name, variant = "pc_function_transformation", "new_maximum"

    def test(self):
        for problem, solution in self.samples():
            M, m = map(int, self.search(r"maximum value of \$" + INT + r"\$ and a minimum value of \$" + INT, problem).groups())
            a, sign, k = self.search(r"g\(x\) = " + INT + r"f\(x\) ([+-]) (\d+)\$", problem).groups()
            k = int(k) * (1 if sign == "+" else -1)
            self.assertEqual(int(solution), max(int(a) * M + k, int(a) * m + k), problem)


class IdentifyModelConstant(_Base):
    name, variant = "pc_identify_model", "model_constant"

    def test(self):
        for problem, solution in self.samples():
            _, ys = table_rows(problem)
            ys = [Fraction(v) for v in ys]
            if "linear model" in problem:
                diffs = {ys[i + 1] - ys[i] for i in range(4)}
                self.assertEqual(diffs, {Fraction(int(solution))}, problem)
            else:
                ratios = {ys[i + 1] / ys[i] for i in range(4)}
                self.assertEqual(ratios, {frac(solution)}, problem)


class QuadraticTimeOfMax(_Base):
    name, variant = "pc_quadratic_model_predict", "time_of_maximum"

    def test(self):
        for problem, solution in self.samples():
            v, h0 = map(int, self.search(r"-16t\^2 \+ (\d+)t \+ (\d+)\$", problem).groups())
            ts = [i / 10000 for i in range(0, 100000)]
            h = lambda t: -16 * t * t + v * t + h0  # noqa: E731
            best = max(ts, key=h)
            want = best if "When does" in problem else h(best)
            self.assertAlmostEqual(float(solution), want, delta=0.001)


class ExponentialHalfLife(_Base):
    name, variant = "pc_exponential_from_two_points", "half_life"

    def test(self):
        for problem, solution in self.samples():
            a0, t, later = self.search(r"has \$(\d+)\$ grams, and \$(\d+)\$ hours later it has \$" + NUM, problem).groups()
            hl = float(solution)
            self.assertAlmostEqual(int(a0) * 0.5 ** (int(t) / hl), float(later), delta=0.0005 * int(a0))


class RewriteMonthlyFactor(_Base):
    name, variant = "pc_rewrite_exponential", "monthly_factor"

    def test(self):
        for problem, solution in self.samples():
            pct = int(self.search(r"grows by \$(\d+)\\%\$", problem)[1])
            self.assertAlmostEqual(float(solution) ** 12, 1 + pct / 100, delta=0.01)


class ResidualActual(_Base):
    name, variant = "pc_residual", "actual_from_residual"

    def test(self):
        for problem, solution in self.samples():
            m, sign, b, x, res = self.search(r"\\hat y = " + NUM + r"x ([+-]) " + NUM + r"\$\. The residual at \$x = (\d+)\$ is \$" + NUM,
                                             problem).groups()
            pred = Fraction(m) * int(x) + Fraction(b) * (1 if sign == "+" else -1)
            self.assertEqual(Fraction(solution) - pred, Fraction(res), problem)


class InverseExponentialTime(_Base):
    name, variant = "pc_inverse_exponential", "time_to_reach"

    def test(self):
        for problem, solution in self.samples():
            a, b, target = map(int, self.search(r"P\(t\) = (\d+) \\cdot (\d+)\^t\$\. After how many years does it reach \$(\d+)\$",
                                                problem).groups())
            self.assertEqual(a * b ** int(solution), target, problem)


class LogFeaturesParameter(_Base):
    name, variant = "pc_log_function_features", "parameter_from_point"

    def test(self):
        for problem, solution in self.samples():
            b = int(self.search(r"\\log_\{(\d+)\}", problem)[1])
            m = re.search(r"\(x ([+-]) (\d+)\)", problem)
            h = (int(m[2]) * (1 if m[1] == "-" else -1)) if m else 0
            x, y = map(int, self.search(r"through \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            self.assertAlmostEqual(int(solution) * math.log(x - h, b), y, places=9)


class SolveLogCount(_Base):
    name, variant = "pc_solve_log_equation", "count_valid"

    def test(self):
        seen = set()
        for problem, solution in self.samples():
            lhs, rhs = self.search(r"\\log\((x\^2[^)]*)\) = \\log\(([^)]+)\)", problem).groups()
            mb = re.fullmatch(r"x\^2(?: ([+-]) (\d+))?", lhs)
            b = (int(mb[2]) * (1 if mb[1] == "+" else -1)) if mb[1] else 0
            m = re.fullmatch(r"x(?: ([+-]) (\d+))?", rhs)
            a = (int(m[2]) * (1 if m[1] == "+" else -1)) if m[1] else 0
            # Real roots of x^2 - x + (b - a) = 0, exactly via the discriminant.
            disc = 1 - 4 * (b - a)
            roots = [] if disc < 0 else sorted({(1 + s * math.sqrt(disc)) / 2 for s in (1, -1)})
            valid = [x for x in roots if x * x + b > 0 and x + a > 0]
            self.assertEqual(int(solution), len(valid), problem)
            seen.add(len(valid))
        self.assertEqual(seen, {0, 1, 2})


class ExpInequalitySmallest(_Base):
    name, variant = "pc_exp_log_inequality", "smallest_integer"

    def test(self):
        for problem, solution in self.samples():
            b, N = map(int, self.search(r"\$(\d+)\^x > (\d+)\$", problem).groups())
            self.assertEqual(int(solution), min(x for x in range(0, 100) if b ** x > N), problem)


class LogMagnitudeRatio(_Base):
    name, variant = "pc_log_model_context", "magnitude_ratio"

    def test(self):
        for problem, solution in self.samples():
            m1, m2 = map(float, self.search(r"magnitude \$" + NUM + r"\$ earthquake than a magnitude \$" + NUM, problem).groups())
            self.assertAlmostEqual(int(solution), 10 ** m1 / 10 ** m2, delta=1e-6 * int(solution))


class SemilogPredict(_Base):
    name, variant = "pc_semilog_model", "predict"

    def test(self):
        for problem, solution in self.samples():
            m, b, x = self.search(r"\\log_\{10\} y = " + NUM + r"x \+ " + NUM + r"\$\. Predict \$y\$ when \$x = (\d+)\$", problem).groups()
            self.close(solution, 10 ** (float(m) * int(x) + float(b)), problem)


class PeriodicNegativeInput(_Base):
    name, variant = "pc_periodic_values", "negative_input"

    def test(self):
        for problem, solution in self.samples():
            p = int(self.search(r"period \$(\d+)\$", problem)[1])
            vals = {int(i): int(v) for i, v in re.findall(r"\$f\((\d+)\) = " + INT + r"\$", problem)}
            x = int(self.search(r"Find \$f\(" + INT, problem)[1])
            while x < 0:
                x += p
            self.assertEqual(int(solution), vals[x], problem)


class SinusoidalFirstTime(_Base):
    name, variant = "pc_sinusoidal_model", "first_time_at_height"

    def test(self):
        for problem, solution in self.samples():
            d, low, T, h = map(int, self.search(r"diameter \$(\d+)\$ ft has its lowest point \$(\d+)\$ ft.*every \$(\d+)\$ minutes.*reach \$(\d+)\$ ft",
                                                problem).groups())
            height = lambda t: low + d / 2 - d / 2 * math.cos(2 * math.pi * t / T)  # noqa: E731
            # Bisect for the first crossing on the way up (from the bottom at t = 0 to the top at T/2).
            lo, hi = 0.0, T / 2
            for _ in range(100):
                mid = (lo + hi) / 2
                if height(mid) < h:
                    lo = mid
                else:
                    hi = mid
            self.close(solution, lo, problem)


class SinusoidDilationFactor(_Base):
    name, variant = "pc_sinusoid_transformations", "dilation_factor"

    def test(self):
        for problem, solution in self.samples():
            old, new = self.search(r"period \$(\d+)\^\\circ\$\) is dilated horizontally so its period becomes \$" + NUM, problem).groups()
            self.assertEqual(frac(solution) * int(old), Fraction(new), problem)


class TangentCountAsymptotes(_Base):
    name, variant = "pc_tangent_features", "count_asymptotes"

    def test(self):
        for problem, solution in self.samples():
            b = int(self.search(r"\\tan\((\d*)x\)", problem)[1] or 1)
            # Asymptotes where cos(bx) = 0, i.e. bx = 90 + 180k.
            count = sum(1 for k in range(-10, 40) if 0 <= (90 + 180 * k) / b < 360)
            self.assertEqual(int(solution), count, problem)


class TrigInequalityLength(_Base):
    name, variant = "pc_trig_inequality", "solution_length"
    VALUES = {r"\frac{1}{2}": 0.5, r"-\frac{1}{2}": -0.5, r"\frac{\sqrt{2}}{2}": math.sqrt(2) / 2,
              r"\frac{\sqrt{3}}{2}": math.sqrt(3) / 2}

    def test(self):
        for problem, solution in self.samples():
            func, op, v = self.search(r"\$\\(sin|cos) x (>|<) (.+?)\$", problem).groups()
            f = math.sin if func == "sin" else math.cos
            target = self.VALUES[v]
            steps = 36000
            count = sum(1 for i in range(steps) if (f(math.radians(i / 100)) > target) == (op == ">"))
            self.assertAlmostEqual(int(solution), count / 100, delta=0.05)


class PolarMaxAngle(_Base):
    name, variant = "pc_polar_graph_features", "max_angle"

    def test(self):
        for problem, solution in self.samples():
            a, sign, b, func = self.search(r"\$r = (\d+) ([+-]) (\d+)\\(sin|cos)\\theta\$", problem).groups()
            f = math.sin if func == "sin" else math.cos
            r = lambda t: int(a) + (1 if sign == "+" else -1) * int(b) * f(math.radians(t))  # noqa: E731
            best = max(range(1, 361), key=lambda t: (round(r(t), 9), -t))
            self.assertEqual(int(solution), best, problem)


class PolarFasterInterval(_Base):
    name, variant = "pc_polar_rate_of_change", "faster_interval"

    def test(self):
        for problem, solution in self.samples():
            a, sign, b = self.search(r"\$r = (\d+) ([+-]) (\d+)\\sin\\theta\$", problem).groups()
            r = lambda t: int(a) + (1 if sign == "+" else -1) * int(b) * math.sin(t)  # noqa: E731
            r1 = (r(math.pi / 6) - r(0)) / (math.pi / 6)
            r2 = (r(math.pi / 2) - r(math.pi / 6)) / (math.pi / 3)
            self.assertNotAlmostEqual(abs(r1), abs(r2), places=6)
            self.close(solution, r1 if abs(r1) > abs(r2) else r2, problem)


class ParametricTimeAtPoint(_Base):
    name, variant = "pc_parametric_position", "time_at_point"

    def test(self):
        for problem, solution in self.samples():
            a, sb, b, c, sd, d = self.search(r"x\(t\) = " + INT + r"t ([+-]) (\d+)\$, \$y\(t\) = " + INT + r"t ([+-]) (\d+)\$", problem).groups()
            px, py = map(int, self.search(r"at \$\(" + INT + ", " + INT + r"\)\$\?", problem).groups())
            t = int(solution)
            self.assertEqual(int(a) * t + int(b) * (1 if sb == "+" else -1), px)
            self.assertEqual(int(c) * t + int(d) * (1 if sd == "+" else -1), py, problem)


class ParametricAverageSpeed(_Base):
    name, variant = "pc_parametric_rate_of_change", "average_speed"

    def test(self):
        for problem, solution in self.samples():
            a, c, t1, t2 = map(int, self.search(r"x\(t\) = " + INT + r"t\$, \$y\(t\) = " + INT + r"t\$\. .*from \$t = (\d+)\$ to \$t = (\d+)\$",
                                                problem).groups())
            dist = math.dist((a * t1, c * t1), (a * t2, c * t2))
            self.close(solution, dist / (t2 - t1), problem)


class ParametricRadius(_Base):
    name, variant = "pc_parametric_circle_line", "radius_from_period"

    def test(self):
        for problem, solution in self.samples():
            r, k = map(int, self.search(r"x\(t\) = (\d+)\\cos\((\d+)t\)", problem).groups())
            # Sweep t over [0, 2pi], unwrap the point's angle, and count full turns.
            total, prev = 0.0, 0.0
            for i in range(1, 20001):
                t = 2 * math.pi * i / 20000
                ang = math.atan2(r * math.sin(k * t), r * math.cos(k * t))
                step = (ang - prev + math.pi) % (2 * math.pi) - math.pi
                total += step
                prev = ang
            self.assertEqual(int(solution), round(total / (2 * math.pi)), problem)


class ImplicitCountPoints(_Base):
    name, variant = "pc_implicit_curve_points", "count_points"

    def test(self):
        for problem, solution in self.samples():
            hs, h, ks, k, r2 = self.search(r"\(x ([+-]) (\d+)\)\^2 \+ \(y ([+-]) (\d+)\)\^2 = (\d+)\$", problem).groups()
            h = int(h) * (1 if hs == "-" else -1)
            k = int(k) * (1 if ks == "-" else -1)
            x = int(self.search(r"have \$x = " + INT, problem)[1])
            rhs = int(r2) - (x - h) ** 2
            ys = set()
            if rhs >= 0:
                ys = {k + math.sqrt(rhs), k - math.sqrt(rhs)}
            self.assertEqual(int(solution), len(ys), problem)


class EllipseSemiAxis(_Base):
    name, variant = "pc_parametrize_ellipse", "semi_axis"

    def test(self):
        for problem, solution in self.samples():
            h, p, k, q = map(int, self.search(r"x\(t\) = " + INT + r" \+ (\d+)\\cos t\$, \$y\(t\) = " + INT + r" \+ (\d+)\\sin t", problem).groups())
            ask_a = "What is $A$" in problem
            t = 0.7
            x, y = h + p * math.cos(t), k + q * math.sin(t)
            A, B = (int(solution), q * q) if ask_a else (p * p, int(solution))
            self.assertAlmostEqual((x - h) ** 2 / A + (y - k) ** 2 / B, 1, places=9)


class ClassifyParameterCircle(_Base):
    name, variant = "pc_classify_conic", "parameter_for_circle"

    def test(self):
        for problem, solution in self.samples():
            c = int(self.search(r"kx\^2 \+ (\d+)y\^2", problem)[1])
            self.assertEqual(int(solution), c, problem)


class VectorValuedTime(_Base):
    name, variant = "pc_vector_valued_function", "time_for_component"

    def test(self):
        for problem, solution in self.samples():
            a, sign, b, target = self.search(r"\\langle " + INT + r"t ([+-]) (\d+), t\^2 \\rangle\$.*coordinate \$" + INT, problem).groups()
            self.assertEqual(int(a) * int(solution) + int(b) * (1 if sign == "+" else -1), int(target), problem)


def matrices(problem):
    out = []
    for body in re.findall(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", problem):
        out.append([[v.strip() for v in row.split("&")] for row in body.split(r"\\")])
    return out


class InverseSingular(_Base):
    name, variant = "pc_inverse_matrix_entry", "singular_parameter"

    def test(self):
        for problem, solution in self.samples():
            (a, b), (c, k) = matrices(problem)[0]
            self.assertEqual(k, "k")
            self.assertEqual(int(a) * int(solution) - int(b) * int(c), 0, problem)


class InverseDeterminant(_Base):
    name, variant = "pc_inverse_matrix_entry", "inverse_determinant"

    def test(self):
        for problem, solution in self.samples():
            (a, b), (c, d) = [[int(v) for v in row] for row in matrices(problem)[0]]
            det = a * d - b * c
            inv = [[Fraction(d, det), Fraction(-b, det)], [Fraction(-c, det), Fraction(a, det)]]
            self.assertEqual(frac(solution), inv[0][0] * inv[1][1] - inv[0][1] * inv[1][0], problem)


class MatrixPreimage(_Base):
    name, variant = "pc_matrix_transform_point", "preimage"

    def test(self):
        for problem, solution in self.samples():
            (a, b), (c, d) = [[int(v) for v in row] for row in matrices(problem)[0]]
            ix, iy = map(int, self.search(r"sends a point to \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            x, y = map(int, re.fullmatch(r"\((-?\d+), (-?\d+)\)", solution).groups())
            self.assertEqual((a * x + b * y, c * x + d * y), (ix, iy), problem)


class MatrixEntryFromMapping(_Base):
    name, variant = "pc_matrix_transform_point", "entry_from_mapping"

    def test(self):
        for problem, solution in self.samples():
            (k, b), (c, d) = matrices(problem)[0]
            (x, y), (ix, iy) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            self.assertEqual(k, "k")
            self.assertEqual(int(solution) * x + int(b) * y, ix, problem)


class MatrixOrderMatters(_Base):
    name, variant = "pc_matrix_composition", "order_matters"

    def test(self):
        for problem, solution in self.samples():
            A, B = ([[int(v) for v in row] for row in m] for m in matrices(problem))
            v = tuple(map(int, self.search(r"\$v = \(" + INT + ", " + INT + r"\)\$", problem).groups()))
            mm = lambda P, Q: [[sum(P[i][k] * Q[k][j] for k in range(2)) for j in range(2)] for i in range(2)]  # noqa: E731
            AB, BA = mm(A, B), mm(B, A)
            self.assertEqual(int(solution), (AB[0][0] - BA[0][0]) * v[0] + (AB[0][1] - BA[0][1]) * v[1], problem)


class MarkovSteadyState(_Base):
    name, variant = "pc_markov_transition", "steady_state"

    def test(self):
        for problem, solution in self.samples():
            p, q, total = map(int, self.search(r"\$(\d+)\\%\$ of customers at Store A switch to Store B, and \$(\d+)\\%\$.*With \$(\d+)\$",
                                               problem).groups())
            a, b = float(total), 0.0
            for _ in range(5000):
                a, b = a * (1 - p / 100) + b * q / 100, a * p / 100 + b * (1 - q / 100)
            self.assertAlmostEqual(int(solution), a, delta=1e-6)


class MarkovPreviousWeek(_Base):
    name, variant = "pc_markov_transition", "previous_week"

    def test(self):
        for problem, solution in self.samples():
            sa, sb, total, a1 = map(int, self.search(r"\$(\d+)\\%\$ of customers at Store A stay.*\$(\d+)\\%\$ at B stay.*There are \$(\d+)\$ "
                                                     r"customers in all, and this week Store A has \$(\d+)\$", problem).groups())
            a0 = int(solution)
            self.assertEqual(Fraction(sa, 100) * a0 + Fraction(100 - sb, 100) * (total - a0), a1, problem)
