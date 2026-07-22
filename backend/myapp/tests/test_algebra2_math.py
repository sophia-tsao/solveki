"""Math-correctness tests for the Advanced Algebra 2 generators.

Each test parses the generated problem statement, independently recomputes the
expected answer, and asserts the generator's stated solution matches. Run over
many random samples so the check covers the generator's whole input space.

Importing ``algebra2`` directly runs its ``@register`` side effects (the module
is intentionally not wired into ``generators/__init__.py``).
"""
import math
import re

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
