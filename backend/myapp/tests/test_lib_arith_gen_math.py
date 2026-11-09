"""Math-correctness tests for the ``lib_arith_gen`` local overrides.

Each test parses the numbers out of the problem statement, independently
recomputes the answer, and asserts the generator's solution matches — over
many seeded random samples. Solutions are compared as the exact strings the
student must type (grading is an exact match).
"""
import random
import re
from fractions import Fraction

from django.test import TestCase

from myapp.generators import lib_arith_gen  # noqa: F401
from myapp.generators import LOCAL_GENERATORS
from myapp.generators._variants import classic

SAMPLES = 2000


def _samples(name):
    random.seed(0)
    gen = classic(LOCAL_GENERATORS[name])
    for _ in range(SAMPLES):
        problem, solution = gen()[:2]
        yield problem, solution


def _is_prime(n):
    return n >= 2 and all(n % k for k in range(2, n))


class _Case(TestCase):
    def match(self, pattern, problem):
        m = re.search(pattern, problem)
        self.assertIsNotNone(m, f"parse fail: {problem!r}")
        return m.groups()


class AdditionTests(_Case):
    def test_sum(self):
        for problem, solution in _samples("addition"):
            a, b = map(int, self.match(r"What is \$(\d+) \+ (\d+)\$\?", problem))
            self.assertLessEqual(a + b, 99)
            self.assertEqual(solution, str(a + b), problem)


class SubtractionTests(_Case):
    def test_difference(self):
        for problem, solution in _samples("subtraction"):
            a, b = map(int, self.match(r"What is \$(\d+) - (\d+)\$\?", problem))
            self.assertGreaterEqual(a - b, 0, problem)
            self.assertEqual(solution, str(a - b), problem)


class MultiplicationTests(_Case):
    def test_product(self):
        for problem, solution in _samples("multiplication"):
            a, b = map(int, self.match(r"\$(\d+) \\times (\d+)\$", problem))
            self.assertEqual(solution, str(a * b), problem)


class DivisionTests(_Case):
    def test_quotient(self):
        for problem, solution in _samples("division"):
            n, d = map(int, self.match(r"\$(\d+) \\div (\d+)\$", problem))
            self.assertEqual(n % d, 0, f"doesn't divide evenly: {problem!r}")
            self.assertLessEqual(n, 100)
            self.assertEqual(solution, str(n // d), problem)


class AbsoluteDifferenceTests(_Case):
    def test_absolute_difference(self):
        for problem, solution in _samples("absolute_difference"):
            a, b = map(int, self.match(r"\\lvert (-?\d+) - \(?(-?\d+)\)? \\rvert", problem))
            self.assertEqual(solution, str(abs(a - b)), problem)


class ExponentiationTests(_Case):
    def test_power(self):
        for problem, solution in _samples("exponentiation"):
            base, exp = map(int, self.match(r"\$(\d+)\^\{(\d+)\}\$", problem))
            value = 1
            for _ in range(exp):
                value *= base
            self.assertLessEqual(value, 10000)
            self.assertEqual(solution, str(value), problem)


class SquareTests(_Case):
    def test_square(self):
        for problem, solution in _samples("square"):
            (a,) = map(int, self.match(r"\$(\d+)\^2\$", problem))
            self.assertEqual(solution, str(a * a), problem)


class SquareRootTests(_Case):
    def test_root(self):
        for problem, solution in _samples("square_root"):
            (n,) = map(int, self.match(r"\\sqrt\{(\d+)\}", problem))
            root = int(solution)
            self.assertGreaterEqual(root, 0)
            self.assertEqual(root * root, n, problem)


class LcmTests(_Case):
    def test_lcm(self):
        for problem, solution in _samples("lcm"):
            a, b = map(int, self.match(r"\$(\d+)\$ and \$(\d+)\$", problem))
            smallest = next(m for m in range(1, a * b + 1) if m % a == 0 and m % b == 0)
            self.assertEqual(solution, str(smallest), problem)


class PrimeFactorsTests(_Case):
    def test_factorization(self):
        for problem, solution in _samples("prime_factors"):
            (n,) = map(int, self.match(r"factorization of \$(\d+)\$", problem))
            self.assertRegex(solution, r"^\d+(,\d+)+$", "composite, so 2+ factors, no spaces")
            factors = [int(f) for f in solution.split(",")]
            self.assertEqual(factors, sorted(factors), problem)
            self.assertTrue(all(_is_prime(f) for f in factors), solution)
            product = 1
            for f in factors:
                product *= f
            self.assertEqual(product, n, problem)


class IsPrimeTests(_Case):
    def test_is_prime(self):
        seen = set()
        for problem, solution in _samples("is_prime"):
            (n,) = map(int, self.match(r"Is \$(\d+)\$ a prime number\?", problem))
            self.assertEqual(solution, "yes" if _is_prime(n) else "no", problem)
            seen.add(solution)
        self.assertEqual(seen, {"yes", "no"})


class IsCompositeTests(_Case):
    def test_is_composite(self):
        seen = set()
        for problem, solution in _samples("is_composite"):
            (n,) = map(int, self.match(r"Is \$(\d+)\$ a composite number\?", problem))
            self.assertEqual(solution, "no" if _is_prime(n) else "yes", problem)
            seen.add(solution)
        self.assertEqual(seen, {"yes", "no"})


class CompareFractionsTests(_Case):
    def test_symbol(self):
        seen = set()
        for problem, solution in _samples("compare_fractions"):
            pairs = re.findall(r"\\frac\{(\d+)\}\{(\d+)\}", problem)
            self.assertEqual(len(pairs), 2, f"parse fail: {problem!r}")
            left, right = (Fraction(int(n), int(d)) for n, d in pairs)
            expected = ">" if left > right else ("<" if left < right else "=")
            self.assertEqual(solution, expected, problem)
            seen.add(solution)
        self.assertEqual(seen, {">", "<", "="})


class FactorialTests(_Case):
    def test_factorial(self):
        for problem, solution in _samples("factorial"):
            (n,) = map(int, self.match(r"\$(\d+)!\$", problem))
            value = 1
            for k in range(2, n + 1):
                value *= k
            self.assertEqual(solution, str(value), problem)
