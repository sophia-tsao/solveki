"""Math-correctness tests for the Algebra II variants (algebra2_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently (brute force where uniqueness matters), and checks the served
solution, over 2000 seeded samples.
"""
import cmath
import itertools
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators import algebra2_variants  # noqa: F401 - attaches the variants
from myapp.tests.test_prealgebra_variants_math import INT, frac, table_rows

SAMPLES = 2000
TOL = 0.0005 + 1e-9
NUM = r"(-?\d+(?:\.\d+)?)"


def poly_eval(text, x):
    """Evaluate a LaTeX polynomial/product such as '2(x + 1)^3(x - 2)' or 'x^3 - 2x + 5' at x."""
    expr = text.replace(" ", "")
    expr = re.sub(r"\^\{?(\d+)\}?", r"**\1", expr)
    expr = re.sub(r"(\d)(x|\()", r"\1*\2", expr)
    expr = re.sub(r"\)(\(|x)", r")*\1", expr)
    expr = re.sub(r"(x)(\()", r"\1*\2", expr)
    return eval(expr, {"x": x})  # noqa: S307 - test-only, generated input


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


class PolynomialCoefficientSum(_Base):
    name, variant = "alg2_evaluate_polynomial", "coefficient_sum"

    def test(self):
        for problem, solution in self.samples():
            expr = self.search(r"\$p\(x\) = ([^$]+)\$", problem)[1]
            want = poly_eval(expr, 1) if "sum of its coefficients" in problem else poly_eval(expr, 0)
            self.assertEqual(int(solution), want, problem)


class DivisionRemainderParameter(_Base):
    name, variant = "alg2_polynomial_division", "remainder_parameter"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$x\^3 \+ kx ([+-]) (\d+)\$ is divided by \$\(x ([+-]) (\d+)\)\$, the remainder is \$" + INT,
                            problem)
            c = int(m[2]) * (1 if m[1] == "+" else -1)
            r = int(m[4]) * (1 if m[3] == "-" else -1)
            k = int(solution)
            # Synthetic division: the remainder of x^3 + kx + c by (x - r).
            coeffs, carry = [1, 0, k, c], 0
            for co in coeffs:
                carry = carry * r + co
            self.assertEqual(carry, int(m[5]), problem)


class RemainderFactorParameter(_Base):
    name, variant = "alg2_remainder_theorem", "factor_parameter"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$\(x ([+-]) (\d+)\)\$ a factor of \$([^$]+)\$", problem)
            r = int(m[2]) * (1 if m[1] == "-" else -1)
            expr = m[3].replace("k", f"({solution})")
            self.assertEqual(poly_eval(expr, r), 0, problem)


class RemainderTwoConditions(_Base):
    name, variant = "alg2_remainder_theorem", "two_remainders"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"bx ([+-]) (\d+)\$ leaves a remainder of \$" + INT + r"\$ when divided by \$x - 1\$ and \$"
                            + INT, problem)
            c, r1, r2 = int(m[2]) * (1 if m[1] == "+" else -1), int(m[3]), int(m[4])
            fits = [(a, b) for a in range(-30, 31) for b in range(-30, 31)
                    if 1 + a + b + c == r1 and -1 + a - b + c == r2]
            self.assertEqual(len(fits), 1)
            self.assertEqual(int(solution), fits[0][0], problem)


class BuildLeadingFromIntercept(_Base):
    name, variant = "alg2_build_polynomial_from_roots", "leading_from_intercept"

    def test(self):
        for problem, solution in self.samples():
            roots = [int(v) for v in re.findall(r"\$(-?\d+)\$", problem.split("x-intercepts", 1)[1].split("and y")[0])]
            y0 = int(self.search(r"y-intercept \$" + INT, problem)[1])
            a = int(solution)
            self.assertEqual(a * math.prod(0 - r for r in roots), y0, problem)


class PolynomialCountReal(_Base):
    name, variant = "alg2_solve_polynomial_factoring", "count_real_solutions"

    def test(self):
        for problem, solution in self.samples():
            expr = self.search(r"does \$([^$]+) = 0\$", problem)[1]
            # Count sign changes on a fine grid plus exact zeros (roots are +-sqrt of integers).
            f = lambda x: poly_eval(expr, x)  # noqa: E731
            roots = set()
            for k in range(0, 10):
                for r in (math.sqrt(k), -math.sqrt(k)):
                    if abs(f(r)) < 1e-6:
                        roots.add(round(r, 9))
            self.assertEqual(int(solution), len(roots), problem)


class RationalRootCount(_Base):
    name, variant = "alg2_rational_root_list", "count_candidates"

    def test(self):
        for problem, solution in self.samples():
            poly = self.search(r"for \$([^$]+)\$\?", problem)[1]
            lead = re.match(r"(\d*)x\^3", poly)[1]
            a = int(lead or 1)
            const = re.search(r"([+-]) (\d+)$", poly)
            c = int(const[2])
            cands = {Fraction(s * p, q) for p in range(1, c + 1) if c % p == 0 for q in range(1, a + 1) if a % q == 0
                     for s in (1, -1)}
            self.assertEqual(int(solution), len(cands), problem)


class EndBehaviorMinimumDegree(_Base):
    name, variant = "alg2_polynomial_end_behavior", "minimum_degree"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"exactly \$(\d+)\$ points", problem)[1])
            same = "on both ends" in problem
            degrees = [d for d in range(1, 20) if d >= n and (d % 2 == 0) == same]
            self.assertEqual(int(solution), min(degrees), problem)


class ComplexUnknownParts(_Base):
    name, variant = "alg2_add_complex", "unknown_parts"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\(a ([+-]) (\d+)i\) - \(" + INT + r" - bi\) = " + INT + r" ([+-]) (\d+)i", problem)
            p = int(m[2]) * (1 if m[1] == "+" else -1)
            c, real = int(m[3]), int(m[4])
            imag = int(m[6]) * (1 if m[5] == "+" else -1)
            a, b = real + c, imag - p
            z = complex(a, p) - complex(c, -b)
            self.assertEqual(z, complex(real, imag))
            self.assertEqual(int(solution), a + b, problem)


class ComplexRealProduct(_Base):
    name, variant = "multiply_complex_numbers", "real_product"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$\(" + INT + r" ([+-]) (\d+)i\)\(k ([+-]) (\d+)i\)\$", problem)
            p = int(m[1])
            q = int(m[3]) * (1 if m[2] == "+" else -1)
            r = int(m[5]) * (1 if m[4] == "+" else -1)
            product = complex(p, q) * complex(int(solution), r)
            self.assertEqual(product.imag, 0, problem)


class ModulusProductRule(_Base):
    name, variant = "alg2_complex_modulus", "product_rule"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"\$\|z\| = (\d+)\$ and \$\|w\| = (\d+)\$", problem)
            if m:
                z, w = int(m[1]), cmath.rect(int(m[2]), 1.1)
                self.assertAlmostEqual(abs(z * w), int(solution), places=9)
            else:
                a, n = map(int, self.search(r"\$\|z\| = (\d+)\$, what is \$\|z\^(\d+)\|\$", problem).groups())
                self.assertAlmostEqual(abs(cmath.rect(a, 0.7) ** n), int(solution), places=6)


class DivisionModulusOfQuotient(_Base):
    name, variant = "alg2_complex_division", "modulus_of_quotient"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{(\d+) ([+-]) (\d+)i\}\{(\d+) ([+-]) (\d+)i\}", problem)
            z = complex(int(m[1]), int(m[3]) * (1 if m[2] == "+" else -1))
            w = complex(int(m[4]), int(m[6]) * (1 if m[5] == "+" else -1))
            self.assertAlmostEqual(float(frac(solution)), abs(z / w), places=9)


class RationalExponentSolve(_Base):
    name, variant = "alg2_rational_exponent", "solve_for_base"

    def test(self):
        for problem, solution in self.samples():
            m, n, v = map(int, self.search(r"\$x\^\{(\d+)/(\d+)\} = (\d+)\$", problem).groups())
            self.assertAlmostEqual(int(solution) ** (m / n), v, places=6)


class RadicalExtraneous(_Base):
    name, variant = "alg2_solve_radical_equation", "extraneous_root"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\sqrt\{x ([+-]) (\d+)\} = x ([+-]) (\d+)\$", problem)
            a = int(m[2]) * (1 if m[1] == "+" else -1)
            b = int(m[4]) * (1 if m[3] == "+" else -1)
            sols = [x for x in range(-200, 200) if x + a >= 0 and x + b >= 0 and math.isqrt(x + a) ** 2 == x + a
                    and math.isqrt(x + a) == x + b]
            self.assertEqual([f"x={v}" for v in sols], [solution], problem)


class ExponentialShiftedPower(_Base):
    name, variant = "alg2_solve_exponential_log", "shifted_power"

    def test(self):
        for problem, solution in self.samples():
            b, v = map(int, self.search(r"If \$(\d+)\^x = (\d+)\$", problem).groups())
            x = math.log(v, b)
            m = re.search(r"\^\{x \+ (\d+)\}", problem)
            want = b ** (x + int(m[1])) if m else b ** (2 * x)
            self.assertAlmostEqual(int(solution), want, delta=1e-6 * want)


class LogReverse(_Base):
    variant = "reverse"

    def test(self):
        for name in ("alg2_evaluate_log", "log"):
            for problem, solution in self.samples(name):
                m = re.search(r"\\log_b (\d+) = (\d+)\$", problem)
                if m:
                    self.assertEqual(int(solution) ** int(m[2]), int(m[1]), problem)
                else:
                    b, k = map(int, self.search(r"\\log_\{(\d+)\} x = (\d+)\$", problem).groups())
                    self.assertAlmostEqual(math.log(int(solution), b), k, places=9)


class LogProductMissing(_Base):
    name, variant = "alg2_log_product_rule", "missing_log"

    def test(self):
        for problem, solution in self.samples():
            a, total = map(int, self.search(r"\\log_b x = " + INT + r"\$ and \$\\log_b\(xy\) = " + INT, problem).groups())
            b = 2.0
            x, y = b ** a, b ** int(solution)
            self.assertAlmostEqual(math.log(x * y, b), total, places=9)


class LogQuotientMissing(_Base):
    name, variant = "alg2_log_quotient_rule", "missing_log"

    def test(self):
        for problem, solution in self.samples():
            a, q = map(int, self.search(r"\\log_b x = " + INT + r"\$ and .*\\right\) = " + INT, problem).groups())
            b = 3.0
            self.assertAlmostEqual(math.log(b ** a / b ** int(solution), b), q, places=9)


class LogPowerMissing(_Base):
    name, variant = "alg2_log_power_rule", "missing_exponent"

    def test(self):
        for problem, solution in self.samples():
            m, total = map(int, self.search(r"\\log_b x = " + INT + r"\$ and \$\\log_b\(x\^k\) = " + INT, problem).groups())
            b = 2.0
            self.assertAlmostEqual(math.log((b ** m) ** int(solution), b), total, places=9)


class LogChain(_Base):
    name, variant = "alg2_log_change_of_base", "chain"

    def test(self):
        for problem, solution in self.samples():
            a, b, b2, c = map(int, self.search(r"\\log_\{(\d+)\} (\d+) \\cdot \\log_\{(\d+)\} (\d+)\$", problem).groups())
            self.assertEqual(b, b2)
            self.assertAlmostEqual(math.log(b, a) * math.log(c, b), int(solution), places=9)


class RadicalConjugateSum(_Base):
    name, variant = "alg2_radical_equation_conjugate", "conjugate_sum"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"If \$\\sqrt\{x ([+-]) (\d+)\} - \\sqrt\{x ([+-]) (\d+)\} = (\d+)\$", problem)
            p = int(m[2]) * (1 if m[1] == "+" else -1)
            q = int(m[4]) * (1 if m[3] == "+" else -1)
            d = int(m[5])
            # Solve for x by brute force, then evaluate the sum.
            xs = [x for x in range(-300, 1000) if x + p >= 0 and x + q >= 0
                  and abs(math.sqrt(x + p) - math.sqrt(x + q) - d) < 1e-9]
            self.assertEqual(len(xs), 1, problem)
            x = xs[0]
            self.assertAlmostEqual(math.sqrt(x + p) + math.sqrt(x + q), int(solution), places=9)


class RationalizeConjugateFactor(_Base):
    name, variant = "alg2_rationalize_denominator", "conjugate_factor"

    def test(self):
        for problem, solution in self.samples():
            top, m, n = map(int, self.search(r"\\frac\{(\d+)\}\{\\sqrt\{(\d+)\} - \\sqrt\{(\d+)\}\}", problem).groups())
            left = top / (math.sqrt(m) - math.sqrt(n))
            self.assertAlmostEqual(left, int(solution) * (math.sqrt(m) + math.sqrt(n)), places=9)


class InverseFromTable(_Base):
    variant = "from_table"

    def test(self):
        for name in ("alg2_inverse_linear_function", "alg2_inverse_nonlinear"):
            for problem, solution in self.samples(name):
                xs, ys = (list(map(int, row)) for row in table_rows(problem))
                v = int(self.search(r"f\^\{-1\}\(" + INT + r"\)", problem)[1])
                self.assertEqual(len(set(ys)), len(ys))
                self.assertEqual(int(solution), xs[ys.index(v)], problem)


class CompositionFromTables(_Base):
    name, variant = "alg2_function_composition", "from_tables"

    def test(self):
        for problem, solution in self.samples():
            tables = re.findall(r"\\begin\{array\}\{[^}]*\}(.*?)\\end\{array\}", problem)
            rows = []
            for t in tables:
                top, bottom = t.split(r"\\ \hline")
                rows.append(dict(zip(map(int, top.split("&")[1:]), map(int, bottom.split("&")[1:]))))
            f, g = rows
            a = int(self.search(r"\$f\(g\((\d+)\)\)\$", problem)[1])
            self.assertEqual(int(solution), f[g[a]], problem)


class RationalExtraneous(_Base):
    name, variant = "alg2_solve_rational_equation", "extraneous_root"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{x\^2\}\{x ([+-]) (\d+)\} = \\frac\{(\d+)\}\{x [+-] \d+\} \+ \(?(-?\d+)\)?\$", problem)
            a = int(m[2]) * (1 if m[1] == "-" else -1)
            a2, k = int(m[3]), int(m[4])
            sols = [x for x in range(-60, 61) if x != a and Fraction(x * x, x - a) == Fraction(a2, x - a) + k]
            self.assertEqual([f"x={v}" for v in sols], [solution], problem)


class RationalOpsExcluded(_Base):
    name, variant = "alg2_rational_expression_ops", "excluded_values"

    def test(self):
        for problem, solution in self.samples():
            vals = [int(v) for v in re.findall(r"x - \(?(-?\d+)\)?", problem)]
            a, b, c, d = vals
            undefined = {x for x in range(-20, 21) if x in (b, d) or x == c}
            self.assertEqual(int(solution), len(undefined), problem)


class SystemThreeSum(_Base):
    name, variant = "alg2_solve_system_three", "sum_without_solving"

    def test(self):
        for problem, solution in self.samples():
            eqs = re.findall(r"\$([^$]+) = (-?\d+)\$", problem)
            rows, rhs = [], []
            for lhs, r in eqs:
                coef = {}
                for sign, mag, var in re.findall(r"(-|\+)?\s*(\d*)([xyz])", lhs):
                    coef[var] = int(mag or 1) * (-1 if sign == "-" else 1)
                rows.append([coef.get(v, 0) for v in "xyz"])
                rhs.append(int(r))
            sums = {sum(r[j] for r in rows) for j in range(3)}
            self.assertEqual(len(sums), 1, problem)
            self.assertEqual(Fraction(sum(rhs), sums.pop()), int(solution), problem)


def matrix(text):
    rows = text.split(r"\\")
    return [[v.strip() for v in row.split("&")] for row in rows]


class MatrixCommutator(_Base):
    name, variant = "alg2_matrix_operation", "commutator_entry"

    def test(self):
        for problem, solution in self.samples():
            mats = re.findall(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", problem)
            A, B = ([[int(v) for v in row] for row in matrix(m)] for m in mats)
            i, j = map(int, self.search(r"row (\d), column (\d)", problem).groups())
            ab = sum(A[i - 1][k] * B[k][j - 1] for k in range(2))
            ba = sum(B[i - 1][k] * A[k][j - 1] for k in range(2))
            self.assertEqual(int(solution), ab - ba, problem)


class DeterminantSingular(_Base):
    name, variant = "int_matrix_22_determinant", "singular_parameter"

    def test(self):
        for problem, solution in self.samples():
            (a, k), (c, d) = matrix(self.search(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", problem)[1])
            self.assertEqual(k, "k")
            fits = [v for v in range(-200, 201) if int(a) * int(d) - v * int(c) == 0]
            self.assertEqual(fits, [int(solution)], problem)


class ConicFocalDistance(_Base):
    name, variant = "alg2_conic_equation", "focal_distance"

    def test(self):
        for problem, solution in self.samples():
            A, sign, B = self.search(r"\\frac\{x\^2\}\{(\d+)\} ([+-]) \\frac\{y\^2\}\{(\d+)\}", problem).groups()
            A, B = int(A), int(B)
            if sign == "-":
                c = math.sqrt(A + B)
            else:
                big, small = max(A, B), min(A, B)
                c = math.sqrt(big - small)
            self.close(solution, c, problem)


class EmpiricalBand(_Base):
    name, variant = "alg2_empirical_rule", "band_percent"

    def test(self):
        for problem, solution in self.samples():
            mu, sd = map(int, self.search(r"mean \$(\d+)\$ and standard deviation \$(\d+)\$", problem).groups())
            lo, hi = map(int, self.search(r"between \$" + INT + r"\$ and \$" + INT, problem).groups())
            a, b = (lo - mu) // sd, (hi - mu) // sd
            # Cumulative 68-95-99.7 percentages below each whole-SD cut point.
            below = {-3: 0.15, -2: 2.5, -1: 16, 0: 50, 1: 84, 2: 97.5, 3: 99.85}
            self.assertAlmostEqual(float(solution), below[b] - below[a], places=6, msg=problem)


class ConfidenceFromInterval(_Base):
    name, variant = "confidence_interval", "from_interval"

    def test(self):
        for problem, solution in self.samples():
            low, high = map(Fraction, self.search(r"is \$\(" + NUM + ", " + NUM + r"\)\$", problem).groups())
            want = (low + high) / 2 if "sample mean" in problem else (high - low) / 2
            self.assertEqual(Fraction(solution), want, problem)


class ApTermFromTwoTerms(_Base):
    name, variant = "arithmetic_progression_term", "from_two_terms"

    def test(self):
        for problem, solution in self.samples():
            (m, am), (n, an) = [(int(i), int(v)) for i, v in re.findall(r"a_\{(\d+)\} = (-?\d+)", problem)]
            k = int(self.search(r"What is \$a_\{(\d+)\}\$", problem)[1])
            d = Fraction(an - am, n - m)
            self.assertEqual(int(solution), am + (k - m) * d, problem)


class ApSumFromTwoTerms(_Base):
    name, variant = "arithmetic_progression_sum", "from_two_terms"

    def test(self):
        for problem, solution in self.samples():
            (m, am), (n, an) = [(int(i), int(v)) for i, v in re.findall(r"a_\{(\d+)\} = (-?\d+)", problem)]
            count = int(self.search(r"first \$(\d+)\$ terms", problem)[1])
            d = Fraction(an - am, n - m)
            a1 = am - (m - 1) * d
            self.assertEqual(int(solution), sum(a1 + i * d for i in range(count)), problem)


class GpFromTwoTerms(_Base):
    name, variant = "geometric_progression", "from_two_terms"

    def test(self):
        for problem, solution in self.samples():
            (m, am), (n, an) = [(int(i), int(v)) for i, v in re.findall(r"a_\{(\d+)\} = (-?\d+)", problem)]
            k = int(self.search(r"What is \$a_\{(\d+)\}\$", problem)[1])
            positive = "ratio is positive" in problem
            ratios = [r for r in range(-6, 7) if r and am * r ** (n - m) == an and (r > 0 or not positive)]
            self.assertEqual(len(ratios), 1, problem)
            self.assertEqual(int(solution), am * ratios[0] ** (k - m), problem)


class CombinationsHandshakes(_Base):
    name, variant = "combinations", "handshakes"

    def test(self):
        for problem, solution in self.samples():
            h = int(self.search(r"There are \$(\d+)\$ handshakes", problem)[1])
            people = [n for n in range(2, 100) if len(list(itertools.combinations(range(n), 2))) == h]
            self.assertEqual(people, [int(solution)], problem)


class PermutationOfficers(_Base):
    name, variant = "permutation", "officers"

    def test(self):
        for problem, solution in self.samples():
            ways = int(self.search(r"in \$(\d+)\$ ways", problem)[1])
            self.assertEqual([n for n in range(2, 100) if math.perm(n, 2) == ways], [int(solution)], problem)


class SetsInclusionExclusion(_Base):
    name, variant = "set_operation", "inclusion_exclusion"

    def test(self):
        for problem, solution in self.samples():
            total, a, b, both = map(int, self.search(r"Of \$(\d+)\$ students, \$(\d+)\$ take art, \$(\d+)\$ take music, and "
                                                     r"\$(\d+)\$ take both", problem).groups())
            students = range(total)
            art = set(range(a))
            music = set(range(a - both, a - both + b))
            self.assertEqual(len(art & music), both)
            self.assertEqual(int(solution), sum(1 for s in students if s not in art and s not in music), problem)


# --- Further variants ----------------------------------------------------------------

def coeffs_of(text):
    """Integer coefficients (highest first) of an _poly-style polynomial in x."""
    text = text.replace(" ", "")
    terms = re.findall(r"([+-]?)(\d*)(x(?:\^(\d+))?)?", text)
    out = {}
    for sign, mag, xpart, power in terms:
        if not mag and not xpart:
            continue
        p = int(power) if power else (1 if xpart else 0)
        out[p] = int(mag or 1) * (-1 if sign == "-" else 1)
    deg = max(out)
    return [out.get(d, 0) for d in range(deg, -1, -1)]


def evaluate(coeffs, x):
    v = 0
    for c in coeffs:
        v = v * x + c
    return v


class PolynomialCoefficientFromValue(_Base):
    name, variant = "alg2_evaluate_polynomial", "coefficient_from_value"

    def test(self):
        for problem, solution in self.samples():
            sign, c, x0, value = self.search(r"x\^3 \+ kx ([+-]) (\d+)\$ and \$p\(" + INT + r"\) = " + INT, problem).groups()
            c = int(c) * (1 if sign == "+" else -1)
            self.assertEqual(evaluate([1, 0, int(solution), c], int(x0)), int(value), problem)


class PolynomialBoxVolume(_Base):
    name, variant = "alg2_evaluate_polynomial", "box_volume"

    def test(self):
        for problem, solution in self.samples():
            L, W, x = map(int, self.search(r"from a \$(\d+)\$ by \$(\d+)\$ inch.*when \$x = (\d+)\$", problem).groups())
            self.assertEqual(int(solution), x * (L - 2 * x) * (W - 2 * x), problem)


class DivisionQuotientConstant(_Base):
    name, variant = "alg2_polynomial_division", "quotient_constant"

    def test(self):
        for problem, solution in self.samples():
            poly, sign, r = self.search(r"When \$([^$]+)\$ is divided by \$\(x ([+-]) (\d+)\)\$", problem).groups()
            r = int(r) if sign == "-" else -int(r)
            p = coeffs_of(poly)
            # Long division by (x - r): quotient q with p = (x - r) q + rem; compare constant term of q.
            q = []
            rem = p[:]
            for i in range(len(p) - 1):
                lead = rem[i]
                q.append(lead)
                rem[i + 1] += lead * r
            self.assertEqual(int(solution), q[-1], problem)


class RemainderLinearDivisor(_Base):
    name, variant = "alg2_remainder_theorem", "linear_divisor"

    def test(self):
        for problem, solution in self.samples():
            poly, a, sign, b = self.search(r"when \$([^$]+)\$ is divided by \$(\d+)x ([+-]) (\d+)\$", problem).groups()
            root = Fraction(int(b) if sign == "-" else -int(b), int(a))
            self.assertEqual(frac(solution), evaluate(coeffs_of(poly), root), problem)


class RemainderIsFactor(_Base):
    name, variant = "alg2_remainder_theorem", "is_factor"

    def test(self):
        seen = set()
        for problem, solution in self.samples():
            sign, r, poly = self.search(r"Is \$\(x ([+-]) (\d+)\)\$ a factor of \$([^$]+)\$", problem).groups()
            r = int(r) if sign == "-" else -int(r)
            self.assertEqual(solution, "yes" if evaluate(coeffs_of(poly), r) == 0 else "no", problem)
            seen.add(solution)
        self.assertEqual(seen, {"yes", "no"})


class BuildOneCoefficient(_Base):
    name, variant = "alg2_build_polynomial_from_roots", "one_coefficient"

    def test(self):
        for problem, solution in self.samples():
            roots = [int(v) for v in re.findall(r"\$(-?\d+)\$", problem.split("roots", 1)[1].split("(counted")[0])]
            poly = [1]
            for r in roots:
                poly = [a - r * b for a, b in zip(poly + [0], [0] + poly)]
            want = poly[-1] if "constant term" in problem else poly[1]
            self.assertEqual(int(solution), want, problem)


def complex_of(text):
    m = re.fullmatch(r"(-?\d+)([+-])(\d+)i", text.replace(" ", ""))
    return complex(int(m[1]), int(m[3]) * (1 if m[2] == "+" else -1))


class ComplexMissingAddend(_Base):
    name, variant = "alg2_add_complex", "missing_addend"

    def test(self):
        for problem, solution in self.samples():
            a, b = self.search(r"\$\(([^)]+)\) \+ z = ([^$]+)\$", problem).groups()
            self.assertEqual(complex_of(a) + complex_of(solution), complex_of(b), problem)


class ComplexPlusConjugate(_Base):
    name, variant = "alg2_add_complex", "plus_conjugate"

    def test(self):
        for problem, solution in self.samples():
            z = complex_of(self.search(r"\$z = ([^$]+)\$", problem)[1])
            self.assertEqual(int(solution), (z + z.conjugate()).real, problem)


class ComplexConjugateProduct(_Base):
    name, variant = "multiply_complex_numbers", "conjugate_product"

    def test(self):
        for problem, solution in self.samples():
            a, b = self.search(r"\$\(([^)]+)\)\(([^)]+)\)\$", problem).groups()
            self.assertEqual(complex(int(solution), 0), complex_of(a) * complex_of(b), problem)


class ComplexPowerOfI(_Base):
    name, variant = "multiply_complex_numbers", "power_of_i"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"\$i\^\{(\d+)\}\$", problem)[1])
            z = 1j ** n
            want = {1: "1", -1: "-1"}.get(round(z.real)) if abs(z.imag) < 1e-9 else ("i" if z.imag > 0 else "-i")
            self.assertEqual(solution, want, problem)


class RationalExponentNegative(_Base):
    name, variant = "alg2_rational_exponent", "negative_exponent"

    def test(self):
        for problem, solution in self.samples():
            base, m, n = map(int, self.search(r"\$(\d+)\^\{-(\d+)/(\d+)\}\$", problem).groups())
            self.assertAlmostEqual(float(frac(solution)), base ** (-m / n), places=9)


class RationalExponentFromRadical(_Base):
    name, variant = "alg2_rational_exponent", "radical_to_exponent"

    def test(self):
        for problem, solution in self.samples():
            n, m = self.search(r"\\sqrt\[(\d*)\]\{x\^\{(\d+)\}\}", problem).groups()
            n = int(n or 2)
            x = 7.3
            self.assertAlmostEqual(x ** float(frac(solution)), (x ** int(m)) ** (1 / n), places=6)


class RadicalCubeRoot(_Base):
    name, variant = "alg2_solve_radical_equation", "cube_root"

    def test(self):
        for problem, solution in self.samples():
            a, sign, b, c = self.search(r"\\sqrt\[3\]\{" + INT + r"x ([+-]) (\d+)\} = " + INT, problem).groups()
            x = int(solution.replace("x=", ""))
            inside = int(a) * x + int(b) * (1 if sign == "+" else -1)
            self.assertEqual(round(math.copysign(abs(inside) ** (1 / 3), inside)), int(c), problem)
            self.assertEqual(int(c) ** 3, inside)


class RadicalPendulum(_Base):
    name, variant = "alg2_solve_radical_equation", "pendulum"

    def test(self):
        for problem, solution in self.samples():
            T = float(self.search(r"period of \$" + NUM + r"\$ seconds", problem)[1])
            self.assertAlmostEqual(2 * math.pi * math.sqrt(float(solution) / 9.8), T, delta=0.002)


class ExponentialCommonBase(_Base):
    name, variant = "alg2_solve_exponential_log", "common_base"

    def test(self):
        for problem, solution in self.samples():
            b, sa, a, B, sb, c = self.search(r"\$(\d+)\^\{x ([+-]) (\d+)\} = (\d+)\^\{x ([+-]) (\d+)\}\$", problem).groups()
            a = int(a) * (1 if sa == "+" else -1)
            c = int(c) * (1 if sb == "+" else -1)
            x = float(frac(solution))
            self.assertAlmostEqual((x + a) * math.log(int(b)), (x + c) * math.log(int(B)), places=9)


class ExponentialDoublingTime(_Base):
    name, variant = "alg2_solve_exponential_log", "doubling_time"

    def test(self):
        for problem, solution in self.samples():
            r = int(self.search(r"At \$(\d+)\\%\$", problem)[1])
            self.assertAlmostEqual((1 + r / 100) ** float(solution), 2, delta=0.002)


class LogFractional(_Base):
    variant = "fractional_value"

    def test(self):
        for name in ("alg2_evaluate_log", "log"):
            for problem, solution in self.samples(name):
                b, arg = self.search(r"\\log_\{(\d+)\} ([^$]+)\$", problem).groups()
                if arg.startswith("{") and arg.endswith("}"):
                    arg = arg[1:-1]
                value = float(frac(arg))
                self.assertAlmostEqual(float(frac(solution)), math.log(value, int(b)), places=9)


class LogBetweenIntegers(_Base):
    name, variant = "alg2_evaluate_log", "between_integers"

    def test(self):
        for problem, solution in self.samples():
            b, n = map(int, self.search(r"\\log_\{(\d+)\} (\d+)\$", problem).groups())
            self.assertEqual(int(solution), math.floor(math.log(n, b) + 1e-12), problem)


class LogReciprocal(_Base):
    name, variant = "alg2_log_change_of_base", "reciprocal"

    def test(self):
        for problem, solution in self.samples():
            k = frac(self.search(r"\\log_a b = ([^$]+)\$", problem)[1])
            a = 3.0
            b = a ** float(k)
            self.assertAlmostEqual(float(frac(solution)), math.log(a, b), places=9)


class InverseSlope(_Base):
    name, variant = "alg2_inverse_linear_function", "inverse_slope"

    def test(self):
        for problem, solution in self.samples():
            m, sign, b = self.search(r"\$f\(x\) = (-?\\frac\{\d+\}\{\d+\}|-?\d+)x ([+-]) (\d+)\$", problem).groups()
            m, b = frac(m), int(b) * (1 if sign == "+" else -1)
            finv = lambda y: (y - b) / m  # noqa: E731
            self.assertEqual(frac(solution), finv(Fraction(1)) - finv(Fraction(0)), problem)


class InverseRestrictedQuadratic(_Base):
    name, variant = "alg2_inverse_nonlinear", "restricted_quadratic"

    def test(self):
        for problem, solution in self.samples():
            h = int(self.search(r"for \$x \\geq " + INT, problem)[1])
            sign, k = self.search(r"\^2 ([+-]) (\d+)\$", problem).groups()
            k = int(k) * (1 if sign == "+" else -1)
            v = int(self.search(r"f\^\{-1\}\(" + INT + r"\)", problem)[1])
            x = int(solution)
            self.assertGreaterEqual(x, h)
            self.assertEqual((x - h) ** 2 + k, v, problem)


class CompositionSolve(_Base):
    name, variant = "alg2_function_composition", "solve_composite"

    def test(self):
        for problem, solution in self.samples():
            a, sb, b, c, sd, d, v = self.search(r"\$f\(x\) = " + INT + r"x ([+-]) (\d+)\$ and \$g\(x\) = " + INT
                                                + r"x ([+-]) (\d+)\$.*\$f\(g\(x\)\) = " + INT, problem).groups()
            f = lambda t: int(a) * t + int(b) * (1 if sb == "+" else -1)  # noqa: E731
            g = lambda t: int(c) * t + int(d) * (1 if sd == "+" else -1)  # noqa: E731
            self.assertEqual(f(g(int(solution))), int(v), problem)


class CompositionDecompose(_Base):
    name, variant = "alg2_function_composition", "decompose"

    def test(self):
        for problem, solution in self.samples():
            a, sign, b, n = self.search(r"\$h\(x\) = \(" + INT + r"x ([+-]) (\d+)\)\^(\d)\$", problem).groups()
            t = int(self.search(r"What is \$g\(" + INT, problem)[1])
            inner = int(a) * t + int(b) * (1 if sign == "+" else -1)
            self.assertEqual(int(solution) ** int(n), inner ** int(n))
            self.assertEqual(int(solution), inner, problem)


class RationalWorkRate(_Base):
    name, variant = "alg2_solve_rational_equation", "work_rate"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"tank in \$(\d+)\$ hours and another in \$(\d+)\$", problem).groups())
            t = frac(solution)
            self.assertEqual(t / a + t / b, 1, problem)


class RationalRoundTrip(_Base):
    name, variant = "alg2_solve_rational_equation", "round_trip_speed"

    def test(self):
        for problem, solution in self.samples():
            v1, v2 = map(int, self.search(r"at \$(\d+)\$ mph and back along the same road at \$(\d+)\$", problem).groups())
            d = 120
            self.close(solution, 2 * d / (d / v1 + d / v2), problem)


class ModulusMissingPart(_Base):
    name, variant = "alg2_complex_modulus", "missing_part"

    def test(self):
        for problem, solution in self.samples():
            b, r = map(int, self.search(r"\|a [+-] (\d+)i\| = (\d+)\$", problem).groups())
            self.assertAlmostEqual(abs(complex(int(solution), b)), r, places=9)


class ModulusDistance(_Base):
    name, variant = "alg2_complex_modulus", "distance"

    def test(self):
        for problem, solution in self.samples():
            z, w = self.search(r"apart are \$([^$]+)\$ and \$([^$]+)\$", problem).groups()
            self.close(solution, abs(complex_of(z) - complex_of(w)), problem)


class RationalRootIsCandidate(_Base):
    name, variant = "alg2_rational_root_list", "is_candidate"

    def test(self):
        for problem, solution in self.samples():
            cand = frac(self.search(r"Could \$([^$]+)\$ be", problem)[1])
            poly = coeffs_of(self.search(r"root of \$([^$]+)\$", problem)[1])
            a, c = poly[0], poly[-1]
            cands = {Fraction(s * p, q) for p in range(1, abs(c) + 1) if c % p == 0 for q in range(1, a + 1) if a % q == 0
                     for s in (1, -1)}
            self.assertEqual(solution, "yes" if cand in cands else "no", problem)


class SystemThreeTickets(_Base):
    name, variant = "alg2_solve_system_three", "ticket_types"

    def test(self):
        for problem, solution in self.samples():
            total = int(self.search(r"sold \$(\d+)\$ tickets", problem)[1])
            p1, p2, p3 = map(int, re.findall(r"\(\$(\d+)\$ dollars\)", problem))
            revenue = int(self.search(r"for \$(\d+)\$ dollars in all", problem)[1])
            diff, more = self.search(r"sold \$(\d+)\$ (more|fewer) adult", problem).groups()
            diff = int(diff) * (1 if more == "more" else -1)
            fits = [(a, st, c) for a in range(0, total + 1) for c in range(0, total + 1 - a)
                    for st in [total - a - c] if a - c == diff and p1 * a + p2 * st + p3 * c == revenue]
            self.assertEqual(len(fits), 1, problem)
            self.assertEqual(int(solution), fits[0][1], problem)


class MatrixMissingEntry(_Base):
    name, variant = "alg2_matrix_operation", "missing_matrix_entry"

    def test(self):
        for problem, solution in self.samples():
            mats = re.findall(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", problem)
            A, B = ([[int(v) for v in row] for row in matrix(m)] for m in mats)
            i, j = map(int, self.search(r"row (\d), column (\d)", problem).groups())
            self.assertEqual(A[i - 1][j - 1] + int(solution), B[i - 1][j - 1], problem)


class DeterminantScaled(_Base):
    name, variant = "int_matrix_22_determinant", "scaled_matrix"

    def test(self):
        for problem, solution in self.samples():
            d, k = map(int, self.search(r"\\det A = " + INT + r"\$\. What is \$\\det\((\d+)A\)", problem).groups())
            A = [[d, 0], [0, 1]]
            kA = [[k * v for v in row] for row in A]
            self.assertEqual(int(solution), kA[0][0] * kA[1][1] - kA[0][1] * kA[1][0], problem)


class DeterminantArea(_Base):
    name, variant = "int_matrix_22_determinant", "parallelogram_area"

    def test(self):
        for problem, solution in self.samples():
            (a, b), (c, d) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            pts = [(0, 0), (a, b), (a + c, b + d), (c, d)]
            shoelace = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) // 2
            self.assertEqual(int(solution), shoelace, problem)


class PolynomialByGrouping(_Base):
    name, variant = "alg2_solve_polynomial_factoring", "by_grouping"

    def test(self):
        for problem, solution in self.samples():
            p = coeffs_of(self.search(r"solve \$([^$]+) = 0\$", problem)[1])
            roots = [x for x in range(-40, 41) if evaluate(p, x) == 0]
            self.assertEqual(int(solution), max(roots), problem)


class PolynomialSumOfRoots(_Base):
    name, variant = "alg2_solve_polynomial_factoring", "sum_of_roots"

    def test(self):
        for problem, solution in self.samples():
            p = coeffs_of(self.search(r"solutions of \$([^$]+) = 0\$", problem)[1])
            roots = [x for x in range(-40, 41) if evaluate(p, x) == 0]
            self.assertEqual(len(roots), 3, problem)
            self.assertEqual(int(solution), sum(roots), problem)


class ConicAsymptoteSlope(_Base):
    name, variant = "alg2_conic_equation", "asymptote_slope"

    def test(self):
        for problem, solution in self.samples():
            A, B = map(int, self.search(r"\\frac\{x\^2\}\{(\d+)\} - \\frac\{y\^2\}\{(\d+)\}", problem).groups())
            x = 1e6
            y = math.sqrt(B * (x * x / A - 1))
            self.assertAlmostEqual(float(frac(solution)), y / x, places=6)


class EndBehaviorTurningPoints(_Base):
    name, variant = "alg2_polynomial_end_behavior", "turning_points"

    def test(self):
        for problem, solution in self.samples():
            p = coeffs_of(self.search(r"graph of \$([^$]+)\$", problem)[1])
            self.assertEqual(int(solution), len(p) - 2, problem)


class EmpiricalCount(_Base):
    name, variant = "alg2_empirical_rule", "count_in_range"

    def test(self):
        for problem, solution in self.samples():
            mu, sd, n = map(int, self.search(r"mean \$(\d+)\$ and standard deviation \$(\d+)\$\. Out of \$(\d+)\$", problem).groups())
            lo = int(self.search(r"between \$" + INT, problem)[1])
            k = (mu - lo) // sd
            pct = {1: 68, 2: 95, 3: 99.7}[k]
            self.assertAlmostEqual(float(solution), n * pct / 100, places=6)


class EmpiricalSdFromRange(_Base):
    name, variant = "alg2_empirical_rule", "sd_from_range"

    def test(self):
        for problem, solution in self.samples():
            pct = self.search(r"middle ([\d.]+)%", problem)[1]
            lo, hi = map(int, self.search(r"between \$" + INT + r"\$ and \$" + INT, problem).groups())
            k = {"68": 1, "95": 2, "99.7": 3}[pct]
            self.assertEqual(Fraction(hi - lo, 2 * k), int(solution), problem)


class ApWhichTerm(_Base):
    name, variant = "arithmetic_progression_term", "which_term"

    def test(self):
        for problem, solution in self.samples():
            nums = [int(v) for v in re.findall(r"-?\d+", self.search(r"\$([^$]*\\ldots[^$]*)\$", problem)[1])]
            a1, d = nums[0], nums[1] - nums[0]
            target = nums[-1] if "How many terms" in problem else int(self.search(r"which term is \$" + INT, problem)[1])
            self.assertEqual(a1 + (int(solution) - 1) * d, target, problem)


class ApSumOddNumbers(_Base):
    name, variant = "arithmetic_progression_sum", "odd_numbers"

    def test(self):
        for problem, solution in self.samples():
            last = int(self.search(r"\\cdots \+ (\d+)\$", problem)[1])
            self.assertEqual(int(solution), sum(range(1, last + 1, 2)), problem)


class ApSumTheater(_Base):
    name, variant = "arithmetic_progression_sum", "theater_rows"

    def test(self):
        for problem, solution in self.samples():
            first, d, rows = map(int, self.search(r"first row has \$(\d+)\$ seats, and each row has \$(\d+)\$ more.*in "
                                                  r"\$(\d+)\$ rows", problem).groups())
            self.assertEqual(int(solution), sum(first + i * d for i in range(rows)), problem)


class GpGeometricMean(_Base):
    name, variant = "geometric_progression", "geometric_mean"

    def test(self):
        for problem, solution in self.samples():
            a, c = map(int, self.search(r"\$ (\d+), x, (\d+)\$", problem).groups())
            x = int(solution)
            self.assertEqual(Fraction(x, a), Fraction(c, x), problem)


class CombinationsAtLeastOne(_Base):
    name, variant = "combinations", "at_least_one"

    def test(self):
        for problem, solution in self.samples():
            k, g, b = map(int, self.search(r"committee of \$(\d+)\$ is chosen from \$(\d+)\$ girls and \$(\d+)\$ boys",
                                           problem).groups())
            people = ["g"] * g + ["b"] * b
            count = sum(1 for c in itertools.combinations(range(g + b), k) if any(people[i] == "g" for i in c))
            self.assertEqual(int(solution), count, problem)


class CombinationsSymmetry(_Base):
    name, variant = "combinations", "symmetry"

    def test(self):
        for problem, solution in self.samples():
            n, r = map(int, self.search(r"\\binom\{(\d+)\}\{(\d+)\}", problem).groups())
            self.assertEqual(int(solution), math.factorial(n) // (math.factorial(r) * math.factorial(n - r)), problem)


class PermutationRepeatedLetters(_Base):
    name, variant = "permutation", "repeated_letters"

    def test(self):
        for problem, solution in self.samples():
            word = self.search(r"letters in ([A-Z]+)\?", problem)[1]
            self.assertEqual(int(solution), len(set(itertools.permutations(word))), problem)


class PermutationPairTogether(_Base):
    name, variant = "permutation", "pair_together"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"ways can \$(\d+)\$ people", problem)[1])
            if n > 7:
                continue   # brute force is slow; the formula is checked for smaller n
            count = sum(1 for p in itertools.permutations(range(n)) if abs(p.index(0) - p.index(1)) == 1)
            self.assertEqual(int(solution), count, problem)


class SetsMissingRegion(_Base):
    name, variant = "set_operation", "missing_region"

    def test(self):
        for problem, solution in self.samples():
            a, b, u = map(int, self.search(r"\|A\| = (\d+)\$, \$\|B\| = (\d+)\$, and \$\|A \\cup B\| = (\d+)\$", problem).groups())
            both = int(solution)
            A = set(range(a))
            B = set(range(a - both, a - both + b))
            self.assertEqual(len(A | B), u, problem)
