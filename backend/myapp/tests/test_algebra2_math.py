"""Math-correctness tests for the Advanced Algebra 2 generators.

Each test parses the generated problem statement, independently recomputes the
expected answer, and asserts the generator's stated solution matches. Run over
many random samples so the check covers the generator's whole input space.

Importing ``algebra2`` directly runs its ``@register`` side effects (the module
is intentionally not wired into ``generators/__init__.py``).
"""
import math
import random
import re
from fractions import Fraction

from django.test import TestCase

from myapp.generators import algebra2  # noqa: F401 - registers alg2_* generators
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000


# A polynomial term parser shared by several tests: optional sign, optional
# magnitude, and x / x^n / constant. Returns highest-first is not guaranteed;
# we key by exponent instead.
_TERM = re.compile(r"([+-]?)(\d*)x\^(\d+)|([+-]?)(\d*)x(?!\^)|([+-]?\d+)(?!x)")


def parse_poly(poly):
    """Parse a polynomial string into ``{exponent: coefficient}``."""
    coeffs = {}
    for m in _TERM.finditer(poly):
        if m.group(3) is not None:  # x^n
            sign = -1 if m.group(1) == "-" else 1
            mag = int(m.group(2)) if m.group(2) else 1
            coeffs[int(m.group(3))] = coeffs.get(int(m.group(3)), 0) + sign * mag
        elif m.group(0).endswith("x"):  # linear
            sign = -1 if m.group(4) == "-" else 1
            mag = int(m.group(5)) if m.group(5) else 1
            coeffs[1] = coeffs.get(1, 0) + sign * mag
        elif m.group(6):  # constant
            coeffs[0] = coeffs.get(0, 0) + int(m.group(6))
    return coeffs


def eval_poly(coeffs, x):
    return sum(c * (x ** e) for e, c in coeffs.items())


class EvaluatePolynomialTests(TestCase):
    PROBLEM = re.compile(r"p\(x\)=(?P<poly>.+?)\$ at \$x=(?P<x>-?\d+)")
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_evaluates_correctly(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_evaluate_polynomial"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            coeffs = parse_poly(m.group("poly"))
            x = int(m.group("x"))
            expected = eval_poly(coeffs, x)
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class PolynomialDivisionTests(TestCase):
    PROBLEM = re.compile(
        r"p\(x\)=(?P<poly>.+?)\$ by \$\(x(?P<sign>[+-])(?P<r>\d+)\)"
    )
    SOLUTION = re.compile(
        r"quotient \$(?P<q>.+?)\$, remainder \$(?P<rem>-?\d+)\$"
    )

    def test_division_reconstructs_dividend(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_polynomial_division"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            pm = self.PROBLEM.search(problem)
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(pm, f"could not parse problem: {problem!r}")
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            # divisor (x - r): "x-2" -> r=2, "x+3" -> r=-3
            r = int(pm.group("r")) if pm.group("sign") == "-" else -int(pm.group("r"))
            dividend = parse_poly(pm.group("poly"))
            quotient = parse_poly(sm.group("q"))
            remainder = int(sm.group("rem"))

            # p(x) should equal q(x)*(x - r) + remainder, verified at points.
            for x in range(-4, 5):
                lhs = eval_poly(dividend, x)
                rhs = eval_poly(quotient, x) * (x - r) + remainder
                self.assertEqual(lhs, rhs, f"{problem!r} -> {solution!r} at x={x}")


class RemainderTheoremTests(TestCase):
    PROBLEM = re.compile(
        r"p\(x\)=(?P<poly>.+?)\$ is divided by \$\(x(?P<sign>[+-])(?P<r>\d+)\)"
    )
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_remainder_equals_p_of_r(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_remainder_theorem"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            r = int(m.group("r")) if m.group("sign") == "-" else -int(m.group("r"))
            coeffs = parse_poly(m.group("poly"))
            expected = eval_poly(coeffs, r)
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class BuildPolynomialTests(TestCase):
    PROBLEM = re.compile(r"roots (?P<roots>.+?)$")
    SOLUTION = re.compile(r"\$(?P<poly>.+?)\$")
    NUM = re.compile(r"-?\d+")

    def test_roots_are_zeros_and_monic(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_build_polynomial_from_roots"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            rm = self.PROBLEM.search(problem)
            self.assertIsNotNone(rm, f"could not parse: {problem!r}")
            roots = [int(n) for n in self.NUM.findall(rm.group("roots"))]
            self.assertIn(len(roots), (2, 3))
            coeffs = parse_poly(self.SOLUTION.search(solution).group("poly"))

            # Each stated root must be a zero of the polynomial.
            for root in roots:
                self.assertEqual(
                    eval_poly(coeffs, root), 0,
                    f"root {root} not a zero: {problem!r} -> {solution!r}",
                )
            # Monic: leading coefficient is 1.
            top = max(coeffs)
            self.assertEqual(top, len(roots), f"wrong degree: {solution!r}")
            self.assertEqual(coeffs[top], 1, f"not monic: {solution!r}")


class AddComplexTests(TestCase):
    OPERANDS = re.compile(
        r"\((?P<a>-?\d+)(?P<b>[+-](?:\d+)?)i\)(?P<op>[+-])"
        r"\((?P<c>-?\d+)(?P<d>[+-](?:\d+)?)i\)"
    )
    SOLUTION = re.compile(r"\$(?P<p>-?\d+)(?P<q>[+-](?:\d+)?)i\$")

    @staticmethod
    def _imag(token):
        # token like "+3", "-", "+" (bare sign => magnitude 1)
        sign = -1 if token[0] == "-" else 1
        mag = int(token[1:]) if len(token) > 1 else 1
        return sign * mag

    def test_addition_and_subtraction(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_add_complex"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.OPERANDS.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = int(m.group("a"))
            b = self._imag(m.group("b"))
            c = int(m.group("c"))
            d = self._imag(m.group("d"))
            if m.group("op") == "+":
                ep, eq = a + c, b + d
            else:
                ep, eq = a - c, b - d

            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            sp = int(sm.group("p"))
            sq = self._imag(sm.group("q"))
            self.assertEqual((sp, sq), (ep, eq), f"{problem!r} -> {solution!r}")


class RationalExponentTests(TestCase):
    PROBLEM = re.compile(r"Evaluate \$(?P<base>\d+)\^\{(?P<p>\d+)/(?P<q>\d+)\}\$")
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_value_matches(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_rational_exponent"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            base = int(m.group("base"))
            p = int(m.group("p"))
            q = int(m.group("q"))
            expected = base ** (p / q)
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=6,
                                   msg=f"{problem!r} -> {solution!r}")


class SolveRadicalTests(TestCase):
    PROBLEM = re.compile(
        r"\\sqrt\{(?P<a>-?\d+)x(?P<b>[+-]\d+)\}=(?P<c>\d+)"
    )
    SOLUTION = re.compile(r"x=(?P<x>-?\d+)")

    def test_solution_satisfies_equation(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_solve_radical_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b, c = int(m.group("a")), int(m.group("b")), int(m.group("c"))
            x = int(self.SOLUTION.search(solution).group("x"))
            inside = a * x + b
            self.assertGreaterEqual(inside, 0, f"negative radicand: {problem!r}")
            self.assertAlmostEqual(math.sqrt(inside), c, places=6,
                                   msg=f"{problem!r} -> {solution!r}")


class SolveExponentialTests(TestCase):
    PROBLEM = re.compile(r"\$(?P<base>\d+)\^x=(?P<value>\d+)\$")
    SOLUTION = re.compile(r"x=(?P<x>-?\d+)")

    def test_base_to_x_equals_value(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_solve_exponential_log"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            base, value = int(m.group("base")), int(m.group("value"))
            x = int(self.SOLUTION.search(solution).group("x"))
            self.assertEqual(base ** x, value, f"{problem!r} -> {solution!r}")


class EvaluateLogTests(TestCase):
    PROBLEM = re.compile(r"\\log_\{(?P<base>\d+)\}\((?P<n>\d+)\)")
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_log_value(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_evaluate_log"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            base, n = int(m.group("base")), int(m.group("n"))
            exponent = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(base ** exponent, n, f"{problem!r} -> {solution!r}")


class InverseLinearTests(TestCase):
    PROBLEM = re.compile(
        r"f\(x\)=(?P<m>-?\d+)x(?P<b>[+-]\d+)\$, find \$f\^\{-1\}\((?P<a>-?\d+)\)"
    )
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_inverse_at_point(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_inverse_linear_function"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            mm, b, a = int(m.group("m")), int(m.group("b")), int(m.group("a"))
            t = int(self.SOLUTION.search(solution).group("v"))
            # f(t) should equal a  =>  m*t + b == a
            self.assertEqual(mm * t + b, a, f"{problem!r} -> {solution!r}")


class ZScoreTests(TestCase):
    PROBLEM = re.compile(
        r"value of \$(?P<x>-?\d+)\$.*mean \$(?P<mean>-?\d+)\$ and "
        r"standard deviation \$(?P<sd>-?\d+)\$"
    )
    SOLUTION = re.compile(r"\$(?P<z>-?[\d.]+)\$")

    def test_z_score(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_z_score"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            x, mean, sd = int(m.group("x")), int(m.group("mean")), int(m.group("sd"))
            expected = (x - mean) / sd
            stated = float(self.SOLUTION.search(solution).group("z"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class EmpiricalRuleTests(TestCase):
    PROBLEM = re.compile(r"within \$(?P<k>\d+)\$")

    def test_percent_matches_k(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_empirical_rule"]
        expected = {1: "68%", 2: "95%", 3: "99.7%"}
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            k = int(m.group("k"))
            self.assertEqual(solution, expected[k], f"{problem!r} -> {solution!r}")


class SolveSystemMatrixTests(TestCase):
    EQ = re.compile(r"(?P<a>-?\d+)x(?P<b>[+-]\d+)y=(?P<c>-?\d+)")
    SOLUTION = re.compile(r"x=(?P<x>-?\d+), y=(?P<y>-?\d+)")

    def test_solution_satisfies_both_equations(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_solve_system_matrix"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            eqs = self.EQ.findall(problem)
            self.assertEqual(len(eqs), 2, f"could not parse: {problem!r}")
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            x, y = int(sm.group("x")), int(sm.group("y"))
            for a, b, c in eqs:
                self.assertEqual(
                    int(a) * x + int(b) * y, int(c),
                    f"{problem!r} -> {solution!r}",
                )


class LogProductRuleTests(TestCase):
    PROBLEM = re.compile(r"\\log_b\(x\)=(?P<p>-?\d+)\$ and \$\\log_b\(y\)=(?P<q>-?\d+)")
    SOLUTION = re.compile(r"\$(?P<ans>-?\d+)\$")

    def test_sum(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_log_product_rule"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            p, q = int(m.group("p")), int(m.group("q"))
            self.assertEqual(int(self.SOLUTION.search(solution).group("ans")), p + q,
                             f"{problem!r} -> {solution!r}")


class LogQuotientRuleTests(TestCase):
    PROBLEM = re.compile(r"\\log_b\(x\)=(?P<p>-?\d+)\$ and \$\\log_b\(y\)=(?P<q>-?\d+)")
    SOLUTION = re.compile(r"\$(?P<ans>-?\d+)\$")

    def test_difference(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_log_quotient_rule"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            p, q = int(m.group("p")), int(m.group("q"))
            self.assertEqual(int(self.SOLUTION.search(solution).group("ans")), p - q,
                             f"{problem!r} -> {solution!r}")


class LogPowerRuleTests(TestCase):
    PROBLEM = re.compile(r"\\log_b\(x\)=(?P<p>-?\d+)\$, find \$\\log_b\(x\^\{(?P<k>\d+)\}\)")
    SOLUTION = re.compile(r"\$(?P<ans>-?\d+)\$")

    def test_product(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_log_power_rule"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            p, k = int(m.group("p")), int(m.group("k"))
            self.assertEqual(int(self.SOLUTION.search(solution).group("ans")), k * p,
                             f"{problem!r} -> {solution!r}")


class LogChangeOfBaseTests(TestCase):
    PROBLEM = re.compile(r"\\log_\{(?P<base>\d+)\}\((?P<n>\d+)\)")
    SOLUTION = re.compile(r"\$(?P<ans>-?[\d.]+)\$")

    def test_change_of_base(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_log_change_of_base"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            base, n = int(m.group("base")), int(m.group("n"))
            expected = math.log(n) / math.log(base)
            stated = float(self.SOLUTION.search(solution).group("ans"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")
            # Genuinely irrational: not an exact integer power of the base.
            self.assertGreater(abs(expected - round(expected)), 1e-6,
                               f"{problem!r} should not be an exact power")


class RationalizeDenominatorTests(TestCase):
    TWO_RAD = re.compile(r"\\sqrt\{(?P<a>\d+)\}-\\sqrt\{(?P<b>\d+)\}")
    RAD_INT = re.compile(r"\\sqrt\{(?P<a>\d+)\}-(?P<d>\d+)")
    INT_RAD = re.compile(r"(?P<d>\d+)-\\sqrt\{(?P<a>\d+)\}")
    DENOM = re.compile(r"\\frac\{1\}\{(?P<denom>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")
    SOLUTION = re.compile(r"\$(?P<ans>-?\d+)\$")

    def test_conjugate_denominator(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_rationalize_denominator"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            d = self.DENOM.search(problem)
            self.assertIsNotNone(d, f"could not parse: {problem!r}")
            denom = d.group("denom")
            ans = int(self.SOLUTION.search(solution).group("ans"))
            m2 = self.TWO_RAD.fullmatch(denom)
            mr = self.RAD_INT.fullmatch(denom)
            mi = self.INT_RAD.fullmatch(denom)
            if m2:
                expected = int(m2.group("a")) - int(m2.group("b"))
            elif mr:
                expected = int(mr.group("a")) - int(mr.group("d")) ** 2
            elif mi:
                expected = int(mi.group("d")) ** 2 - int(mi.group("a"))
            else:
                self.fail(f"unrecognized denominator: {denom!r}")
            self.assertEqual(ans, expected, f"{problem!r} -> {solution!r}")


class RadicalEquationConjugateTests(TestCase):
    PROBLEM = re.compile(
        r"\\sqrt\{x\+(?P<a>\d+)\} (?P<op>[+-]) \\sqrt\{x\+(?P<b>\d+)\} = (?P<c>\d+)"
    )
    SOLUTION = re.compile(r"x=(?P<x>-?\d+)")

    def test_solution_satisfies_equation(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_radical_equation_conjugate"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, b, c = int(m.group("a")), int(m.group("b")), int(m.group("c"))
            op = m.group("op")
            x = int(self.SOLUTION.search(solution).group("x"))
            lhs = math.sqrt(x + a) + (1 if op == "+" else -1) * math.sqrt(x + b)
            self.assertAlmostEqual(lhs, c, places=6, msg=f"{problem!r} -> {solution!r}")


class FunctionCompositionTests(TestCase):
    PROBLEM = re.compile(
        r"f\(x\)=(?P<f>.+?)\$ and \$g\(x\)=(?P<g>.+?)\$, "
        r"find \$\(f \\circ g\)\((?P<x>-?\d+)\)"
    )
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_composition_value(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_function_composition"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            cf = parse_poly(m.group("f"))
            cg = parse_poly(m.group("g"))
            x0 = int(m.group("x"))
            inner = eval_poly(cg, x0)
            expected = eval_poly(cf, inner)
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class SolveRationalEquationTests(TestCase):
    PROBLEM = re.compile(
        r"\\frac\{(?P<a>-?\d+)\}\{x(?P<ps>[+-])(?P<p>\d+)\} = "
        r"\\frac\{(?P<c>-?\d+)\}\{x(?P<qs>[+-])(?P<q>\d+)\}"
    )
    SOLUTION = re.compile(r"x=(?P<x>-?\d+(?:/\d+)?)")

    def test_root_is_genuine(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_solve_rational_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a, c = int(m.group("a")), int(m.group("c"))
            p = int(m.group("p")) if m.group("ps") == "+" else -int(m.group("p"))
            q = int(m.group("q")) if m.group("qs") == "+" else -int(m.group("q"))
            # a/(x+p) = c/(x+q) => x = (c*p - a*q)/(a - c)
            self.assertNotEqual(a, c, f"degenerate equation: {problem!r}")
            expected = Fraction(c * p - a * q, a - c)
            stated = Fraction(self.SOLUTION.search(solution).group("x"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")
            # Not extraneous: denominators nonzero at the root.
            self.assertNotEqual(stated + p, 0, f"extraneous root: {problem!r}")
            self.assertNotEqual(stated + q, 0, f"extraneous root: {problem!r}")


class RationalExpressionOpsTests(TestCase):
    PROBLEM = re.compile(
        r"\\frac\{(?P<n1>x[+-]\d+)\}\{(?P<d1>x[+-]\d+)\} "
        r"(?P<op>\\cdot|\\div) "
        r"\\frac\{(?P<n2>x[+-]\d+)\}\{(?P<d2>x[+-]\d+)\}"
    )
    SOLUTION = re.compile(r"\((?P<an>x[+-]\d+)\)/\((?P<ad>x[+-]\d+)\)")

    @staticmethod
    def _const(token):
        return int(token[1:])  # "x+2" -> 2, "x-3" -> -3

    def test_simplification_matches_numerically(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_rational_expression_ops"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            n1 = self._const(m.group("n1"))
            d1 = self._const(m.group("d1"))
            n2 = self._const(m.group("n2"))
            d2 = self._const(m.group("d2"))
            op = m.group("op")
            an = self._const(sm.group("an"))
            ad = self._const(sm.group("ad"))
            for t in (7, 8, 9, 10, 11):
                e1 = (t + n1) / (t + d1)
                e2 = (t + n2) / (t + d2)
                orig = e1 * e2 if op == "\\cdot" else e1 / e2
                ans = (t + an) / (t + ad)
                self.assertAlmostEqual(
                    orig, ans, places=6, msg=f"{problem!r} -> {solution!r} at t={t}"
                )


def _imag_coeff(token):
    """Signed imaginary magnitude from a token like '+3', '-', '-1/5', '+'."""
    sign = -1 if token[0] == "-" else 1
    body = token[1:]
    return sign * (Fraction(body) if body else Fraction(1))


class ComplexDivisionTests(TestCase):
    PROBLEM = re.compile(
        r"\((?P<a>-?\d+)(?P<b>[+-]\d*)i\)/\((?P<c>-?\d+)(?P<d>[+-]\d*)i\)"
    )
    SOLUTION = re.compile(
        r"\$(?P<re>-?\d+(?:/\d+)?)(?P<im>[+-]\d*(?:/\d+)?)i\$"
    )

    def test_division_value(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_complex_division"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = int(m.group("a"))
            b = int(_imag_coeff(m.group("b")))
            c = int(m.group("c"))
            d = int(_imag_coeff(m.group("d")))
            denom = c * c + d * d
            exp_re = Fraction(a * c + b * d, denom)
            exp_im = Fraction(b * c - a * d, denom)
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            got_re = Fraction(sm.group("re"))
            got_im = _imag_coeff(sm.group("im"))
            self.assertEqual(
                (got_re, got_im), (exp_re, exp_im), f"{problem!r} -> {solution!r}"
            )


class ComplexModulusTests(TestCase):
    PROBLEM = re.compile(r"\|(?P<a>-?\d+)(?P<b>[+-]\d*)i\|")
    SOLUTION = re.compile(r"\$(?P<v>-?[\d.]+)\$")

    def test_modulus_value(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_complex_modulus"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            a = int(m.group("a"))
            b = int(_imag_coeff(m.group("b")))
            expected = math.sqrt(a * a + b * b)
            stated = float(self.SOLUTION.search(solution).group("v"))
            self.assertAlmostEqual(stated, expected, places=3,
                                   msg=f"{problem!r} -> {solution!r}")


class InverseNonlinearTests(TestCase):
    PROBLEM = re.compile(
        r"f\(x\)=\((?P<inner>x[+-]\d+)\)\^3(?P<k>[+-]\d+)"
    )
    SOLUTION = re.compile(
        r"\((?P<sinner>x[+-]\d+)\)\^\(1/3\)(?P<souter>[+-]\d+)"
    )

    @staticmethod
    def _cbrt(v):
        return math.copysign(abs(v) ** (1.0 / 3.0), v)

    def test_inverse_composes_to_identity(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_inverse_nonlinear"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            # f(x) = (x - h)^3 + k; inner text "x + (-h)" so const = -h.
            h = -int(m.group("inner")[1:])
            k = int(m.group("k"))
            inner_c = int(sm.group("sinner")[1:])
            outer_c = int(sm.group("souter"))
            for t in (-5, -2, 0, 1, 3, 6):
                inv = self._cbrt(t + inner_c) + outer_c
                f_of_inv = (inv - h) ** 3 + k
                self.assertAlmostEqual(
                    f_of_inv, t, places=4, msg=f"{problem!r} -> {solution!r} at t={t}"
                )


def _divisors(n):
    n = abs(n)
    return [d for d in range(1, n + 1) if n % d == 0]


class RationalRootListTests(TestCase):
    PROBLEM = re.compile(r"p\(x\)=(?P<poly>.+?)\$ given")

    def test_candidate_list(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_rational_root_list"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            coeffs = parse_poly(m.group("poly"))
            lead = coeffs[max(coeffs)]
            const = coeffs[0]
            positives = sorted({Fraction(p, q) for p in _divisors(const)
                                for q in _divisors(lead)})
            expected = positives + [-c for c in positives]
            stated = [Fraction(tok) for tok in solution.split(", ")]
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class SolveSystemThreeTests(TestCase):
    EQ = re.compile(
        r"(?P<a>-?\d+)x(?P<b>[+-]\d+)y(?P<c>[+-]\d+)z=(?P<d>-?\d+)"
    )
    SOLUTION = re.compile(r"\((?P<x>-?\d+), (?P<y>-?\d+), (?P<z>-?\d+)\)")

    def test_solution_satisfies_all_equations(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_solve_system_three"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            eqs = self.EQ.findall(problem)
            self.assertEqual(len(eqs), 3, f"could not parse: {problem!r}")
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            x, y, z = int(sm.group("x")), int(sm.group("y")), int(sm.group("z"))
            for a, b, c, d in eqs:
                self.assertEqual(
                    int(a) * x + int(b) * y + int(c) * z, int(d),
                    f"{problem!r} -> {solution!r}",
                )


class MatrixOperationTests(TestCase):
    MAT = r"\[\[(-?\d+), (-?\d+)\], \[(-?\d+), (-?\d+)\]\]"
    PROBLEM = re.compile(
        r"A=" + MAT + r"\$ and \$B=" + MAT
    )
    RC = re.compile(r"row (?P<i>\d), column (?P<j>\d)")
    SOLUTION = re.compile(r"\$(?P<v>-?\d+)\$")

    def test_entry_matches(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_matrix_operation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            nums = [int(g) for g in m.groups()]
            A = [[nums[0], nums[1]], [nums[2], nums[3]]]
            B = [[nums[4], nums[5]], [nums[6], nums[7]]]
            rc = self.RC.search(problem)
            i, j = int(rc.group("i")), int(rc.group("j"))
            if "A+B" in problem:
                expected = A[i - 1][j - 1] + B[i - 1][j - 1]
            else:
                expected = sum(A[i - 1][k] * B[k][j - 1] for k in range(2))
            stated = int(self.SOLUTION.search(solution).group("v"))
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class SolvePolynomialFactoringTests(TestCase):
    PROBLEM = re.compile(r"p\(x\)=(?P<poly>.+?)=0")

    def test_roots_are_complete_and_sorted(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_solve_polynomial_factoring"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            coeffs = parse_poly(m.group("poly"))
            expected = sorted(x for x in range(-30, 31)
                              if eval_poly(coeffs, x) == 0)
            stated = [int(tok) for tok in solution.split(", ")]
            self.assertEqual(stated, sorted(stated), f"not sorted: {solution!r}")
            self.assertEqual(stated, expected, f"{problem!r} -> {solution!r}")


class ConicEquationTests(TestCase):
    A_VAL = re.compile(r"a=(?P<a>\d+)")
    B_VAL = re.compile(r"b=(?P<b>\d+)")
    SOLUTION = re.compile(
        r"x\^2/(?P<A>\d+)(?P<sign>[+-])y\^2/(?P<B>\d+)=1"
    )

    def test_standard_form(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_conic_equation"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            a = int(self.A_VAL.search(problem).group("a"))
            b = int(self.B_VAL.search(problem).group("b"))
            sm = self.SOLUTION.search(solution)
            self.assertIsNotNone(sm, f"could not parse solution: {solution!r}")
            self.assertEqual(int(sm.group("A")), a * a, f"{problem!r}")
            self.assertEqual(int(sm.group("B")), b * b, f"{problem!r}")
            if "ellipse" in problem:
                self.assertEqual(sm.group("sign"), "+", f"{problem!r}")
            else:
                self.assertEqual(sm.group("sign"), "-", f"{problem!r}")


class PolynomialEndBehaviorTests(TestCase):
    PROBLEM = re.compile(r"p\(x\)=(?P<poly>.+?)\$")

    def test_end_behavior(self):
        random.seed(0)
        gen = LOCAL_GENERATORS["alg2_polynomial_end_behavior"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            coeffs = parse_poly(m.group("poly"))
            degree = max(coeffs)
            lead = coeffs[degree]
            right = "inf" if lead > 0 else "-inf"
            if degree % 2 == 0:
                left = right
            else:
                left = "-inf" if lead > 0 else "inf"
            self.assertEqual(solution, f"{left}, {right}",
                             f"{problem!r} -> {solution!r}")
