"""Math-correctness tests for the ``lib_algebra_extra_gen`` local overrides.

Each test parses the problem statement, independently recomputes the expected
result, and asserts the generator's solution matches — over many random
samples. The polynomial tests (``expanding``, ``power_rule_differentiation``)
also guard typeability: no LaTeX braces, and the answer is in strictly
descending power order.
"""
import random
import re
from fractions import Fraction

from django.test import TestCase

from myapp.generators import lib_algebra_extra_gen  # noqa: F401
from myapp.generators import LOCAL_GENERATORS
from myapp.generators._variants import classic

SAMPLES = 1000

# One term of a typeable polynomial answer: optional sign, optional coeff,
# 'x', optional '^power'. Constants have no 'x'.
_TERM = re.compile(r"(?P<coeff>-?\d*)x(?:\^(?P<power>\d+))?|(?P<const>-?\d+)")


def _parse_solution(text):
    """Parse a typeable polynomial string into a {power: coeff} dict."""
    terms = {}
    # Normalise ' - '/' + ' joins into signed tokens, then split on whitespace.
    normalized = text.replace(" + ", " +").replace(" - ", " -")
    for token in normalized.split():
        token = token.lstrip("+")  # a leading '+' isn't part of the number
        m = _TERM.fullmatch(token)
        assert m, f"unparseable term {token!r} in {text!r}"
        if m.group("const") is not None:
            terms[0] = terms.get(0, 0) + int(m.group("const"))
            continue
        c = m.group("coeff")
        coeff = 1 if c in ("", "+") else (-1 if c == "-" else int(c))
        power = int(m.group("power")) if m.group("power") else 1
        terms[power] = terms.get(power, 0) + coeff
    return terms


def _assert_typeable_descending(test, solution):
    test.assertNotIn("{", solution)
    test.assertNotIn("}", solution)
    test.assertNotIn("\\", solution)
    powers = [int(p) if p else 1 for p in re.findall(r"x(?:\^(\d+))?", solution)]
    test.assertEqual(powers, sorted(powers, reverse=True),
                     f"terms not in descending order: {solution!r}")


class ExpandingTests(TestCase):
    FACTOR = re.compile(r"\((-?\d*)x([+-]\d+)?\)")

    def test_product_matches(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["expanding"])
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            factors = self.FACTOR.findall(problem)
            self.assertEqual(len(factors), 2, f"parse fail: {problem!r}")

            def coeffs(lead, const):
                lead = 1 if lead == "" else (-1 if lead == "-" else int(lead))
                const = int(const) if const else 0
                return lead, const

            a, b = coeffs(*factors[0])
            c, d = coeffs(*factors[1])
            expected = {2: a * c, 1: a * d + b * c, 0: b * d}
            expected = {p: v for p, v in expected.items() if v != 0}

            got = _parse_solution(solution)
            got = {p: v for p, v in got.items() if v != 0}
            self.assertEqual(got, expected, f"{problem!r} -> {solution!r}")
            _assert_typeable_descending(self, solution)


class PowerRuleDifferentiationTests(TestCase):
    def test_derivative_matches(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["power_rule_differentiation"])
        term_re = re.compile(r"(\d+)x\^\{(\d+)\}")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            shown = problem.split("$")[1]
            src = {}
            for c, p in term_re.findall(shown):
                src[int(p)] = src.get(int(p), 0) + int(c)

            expected = {}
            for p, c in src.items():
                expected[p - 1] = expected.get(p - 1, 0) + c * p
            expected = {p: v for p, v in expected.items() if v != 0}

            got = _parse_solution(solution)
            got = {p: v for p, v in got.items() if v != 0}
            self.assertEqual(got, expected, f"{problem!r} -> {solution!r}")
            _assert_typeable_descending(self, solution)


# ---------------------------------------------------------------------------
# Overrides of stock generators used by seeded topics.
# ---------------------------------------------------------------------------

OVERRIDE_SAMPLES = 2000


def _override_samples(name):
    random.seed(0)
    gen = classic(LOCAL_GENERATORS[name])
    for _ in range(OVERRIDE_SAMPLES):
        yield gen()[:2]


def _coeff(text):
    """A written coefficient: '' -> 1, '-' -> -1, '3' -> 3."""
    return {"": 1, "-": -1}.get(text, None) or int(text)


def _signed(sign, digits):
    return int(digits) * (-1 if sign == "-" else 1)


class _Parse(TestCase):
    def match(self, pattern, problem):
        m = re.search(pattern, problem)
        self.assertIsNotNone(m, f"parse fail: {problem!r}")
        return m.groups()


class BasicAlgebraTests(_Parse):
    def test_solution_solves_equation(self):
        for problem, solution in _override_samples("basic_algebra"):
            a, sign, b, c = self.match(r"\$(-?\d*)x ([+-]) (\d+) = (-?\d+)\$", problem)
            a, b, c = _coeff(a), _signed(sign, b), int(c)
            self.assertRegex(solution, r"^-?\d+(/\d+)?$")
            x = Fraction(solution)
            self.assertEqual(a * x + b, c, f"{problem!r} -> {solution!r}")
            self.assertEqual(str(x), solution, "fraction not in lowest terms")


class LinearEquationsTests(_Parse):
    EQ = r"(-?\d*)x ([+-]) (\d*)y = (-?\d+)"

    def test_solution_solves_both_equations(self):
        for problem, solution in _override_samples("linear_equations"):
            eqs = re.findall(self.EQ, problem)
            self.assertEqual(len(eqs), 2, f"parse fail: {problem!r}")
            (sx, sy) = self.match(r"^\((-?\d+), (-?\d+)\)$", solution)
            x, y = int(sx), int(sy)
            rows = []
            for a, sign, b, c in eqs:
                a, b, c = _coeff(a), _coeff(b) * (-1 if sign == "-" else 1), int(c)
                self.assertEqual(a * x + b * y, c, f"{problem!r} -> {solution!r}")
                rows.append((a, b))
            (a1, b1), (a2, b2) = rows
            self.assertNotEqual(a1 * b2 - a2 * b1, 0, f"not a unique solution: {problem!r}")


def _line(rhs):
    """Parse the right side of ``y = ...`` into (slope, intercept)."""
    m = re.fullmatch(r"(?:(-?\d*)x)?\s*(?:([+-]) (\d+))?|(-?\d+)", rhs)
    assert m, rhs
    if m.group(4) is not None:
        return 0, int(m.group(4))
    slope = _coeff(m.group(1)) if m.group(1) is not None else 0
    intercept = _signed(m.group(2), m.group(3)) if m.group(3) else 0
    return slope, intercept


class IntersectionOfTwoLinesTests(_Parse):
    def test_point_is_on_both_lines(self):
        for problem, solution in _override_samples("intersection_of_two_lines"):
            rhs = re.findall(r"\$y = ([^$]+)\$", problem)
            self.assertEqual(len(rhs), 2, f"parse fail: {problem!r}")
            (m1, b1), (m2, b2) = (_line(r) for r in rhs)
            self.assertNotEqual(m1, m2, "lines must have one intersection")
            x = Fraction(b2 - b1, m1 - m2)
            sx, sy = self.match(r"^\((-?\d+(?:/\d+)?), (-?\d+(?:/\d+)?)\)$", solution)
            self.assertEqual((Fraction(sx), Fraction(sy)), (x, m1 * x + b1), problem)
            self.assertEqual((str(Fraction(sx)), str(Fraction(sy))), (sx, sy), "not reduced")


class SurdsComparisonTests(_Parse):
    def test_symbol(self):
        seen = set()
        for problem, solution in _override_samples("surds_comparison"):
            roots = re.findall(r"\\sqrt(?:\[(\d)\])?\{(\d+)\}", problem)
            self.assertEqual(len(roots), 2, f"parse fail: {problem!r}")
            left, right = (int(n) ** (1 / int(idx or 2)) for idx, n in roots)
            if abs(left - right) < 1e-9:
                expected = "="
            else:
                expected = ">" if left > right else "<"
            self.assertEqual(solution, expected, problem)
            seen.add(solution)
        self.assertTrue({">", "<"} <= seen)


class LogTests(_Parse):
    def test_exponent(self):
        for problem, solution in _override_samples("log"):
            base, value = map(int, self.match(r"\\log_\{(\d+)\}\((\d+)\)", problem))
            k, power = 0, 1
            while power < value:
                power *= base
                k += 1
            self.assertEqual(power, value, f"not a power of the base: {problem!r}")
            self.assertEqual(solution, str(k), problem)


def _to_complex(text):
    """'3-2i' / '-i' / '4+i' -> Python complex."""
    return complex(re.sub(r"(?<!\d)i", "1i", text).replace("i", "j"))


class MultiplyComplexNumbersTests(_Parse):
    def test_product(self):
        for problem, solution in _override_samples("multiply_complex_numbers"):
            z1, z2 = self.match(r"\$\(([^)]+)\)\(([^)]+)\)\$", problem)
            self.assertRegex(solution, r"^-?\d+[+-]\d+i$", "a+bi with both parts, no spaces")
            self.assertEqual(_to_complex(solution), _to_complex(z1) * _to_complex(z2), problem)


class IntMatrix22DeterminantTests(_Parse):
    def test_determinant(self):
        for problem, solution in _override_samples("int_matrix_22_determinant"):
            a, b, c, d = map(int, self.match(
                r"\\begin\{bmatrix\} (-?\d+) & (-?\d+) \\\\ (-?\d+) & (-?\d+) \\end", problem))
            self.assertEqual(solution, str(a * d - b * c), problem)


class VectorDotTests(_Parse):
    def test_dot_product(self):
        for problem, solution in _override_samples("vector_dot"):
            vecs = re.findall(r"\\langle ([^\\]+) \\rangle", problem)
            self.assertEqual(len(vecs), 2, f"parse fail: {problem!r}")
            u, v = ([int(x) for x in vec.split(", ")] for vec in vecs)
            self.assertEqual(len(u), 3)
            self.assertEqual(solution, str(sum(p * q for p, q in zip(u, v))), problem)


class ArithmeticProgressionTermTests(_Parse):
    def test_nth_term(self):
        for problem, solution in _override_samples("arithmetic_progression_term"):
            n, t1, t2, t3 = map(int, self.match(
                r"the (\d+)(?:st|nd|rd|th) term .*\$(-?\d+), (-?\d+), (-?\d+), \\dots\$", problem))
            d = t2 - t1
            self.assertEqual(t3 - t2, d, f"not arithmetic: {problem!r}")
            term = t1
            for _ in range(n - 1):
                term += d
            self.assertEqual(solution, str(term), problem)


def _fact(n):
    out = 1
    for k in range(2, n + 1):
        out *= k
    return out


class CombinationsTests(_Parse):
    def test_count(self):
        for problem, solution in _override_samples("combinations"):
            r, n = map(int, self.match(r"choose \$(\d+)\$ objects from \$(\d+)\$", problem))
            self.assertEqual(solution, str(_fact(n) // (_fact(r) * _fact(n - r))), problem)


class PermutationTests(_Parse):
    def test_count(self):
        for problem, solution in _override_samples("permutation"):
            r, n = map(int, self.match(r"arrange \$(\d+)\$ objects chosen from \$(\d+)\$", problem))
            self.assertEqual(solution, str(_fact(n) // _fact(n - r)), problem)
