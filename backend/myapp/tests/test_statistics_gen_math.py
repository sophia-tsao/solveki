"""Math-correctness tests for the ``stat_`` statistics generators.

Each test parses the generated problem statement, independently recomputes the
expected answer using the *same* statistical conventions the generator states,
and asserts the generator's solution matches. Every generator is exercised over
many random samples so the check covers its whole input space.
"""
import math
import re

from django.test import TestCase

# Importing the module runs its @register side effects, populating
# LOCAL_GENERATORS with the stat_* generators.
from myapp.generators import statistics_gen  # noqa: F401
from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000

NUM = r"-?\d+(?:\.\d+)?"


def _median(values):
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


class FiveNumberSummaryTests(TestCase):
    DATA = re.compile(r"data set: (?P<data>[\d, ]+?)\.")
    SOLUTION = re.compile(
        rf"\((?P<mn>{NUM}), (?P<q1>{NUM}), (?P<med>{NUM}), "
        rf"(?P<q3>{NUM}), (?P<mx>{NUM})\)"
    )

    def test_summary_matches_convention(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_five_number_summary"]
        sol_re = re.compile(
            rf"\$(?P<mn>{NUM}), (?P<q1>{NUM}), (?P<med>{NUM}), "
            rf"(?P<q3>{NUM}), (?P<mx>{NUM})\$"
        )
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.DATA.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            data = [int(v) for v in m.group("data").split(", ")]
            ordered = sorted(data)
            n = len(ordered)
            mid = n // 2
            if n % 2 == 1:
                lower, upper = ordered[:mid], ordered[mid + 1:]
            else:
                lower, upper = ordered[:mid], ordered[mid:]

            expected = (
                ordered[0], _median(lower), _median(ordered),
                _median(upper), ordered[-1],
            )
            s = sol_re.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            stated = (
                float(s.group("mn")), float(s.group("q1")),
                float(s.group("med")), float(s.group("q3")),
                float(s.group("mx")),
            )
            for got, exp in zip(stated, expected):
                self.assertAlmostEqual(
                    got, exp, places=3,
                    msg=f"summary wrong for {problem!r} -> {solution!r}",
                )


class ZScoreTests(TestCase):
    PROBLEM = re.compile(
        rf"x = (?P<x>{NUM}) .*mean = (?P<mean>{NUM}) and standard deviation "
        rf"= (?P<sd>{NUM})"
    )
    SOLUTION = re.compile(rf"\$(?P<z>{NUM})\$")

    def test_z_score(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_z_score"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            x, mean, sd = (
                float(m.group("x")), float(m.group("mean")), float(m.group("sd"))
            )
            expected = round((x - mean) / sd, 3)
            stated = float(self.SOLUTION.search(solution).group("z"))
            self.assertAlmostEqual(
                stated, expected, places=3,
                msg=f"z-score wrong for {problem!r} -> {solution!r}",
            )


POINT = re.compile(r"\((-?\d+), (-?\d+)\)")


def _parse_points(problem):
    marker = problem.index("points:")
    return [(int(a), int(b)) for a, b in POINT.findall(problem[marker:])]


class CorrelationCoefficientTests(TestCase):
    SOLUTION = re.compile(rf"\$(?P<r>{NUM})\$")

    def test_correlation(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_correlation_coefficient"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            points = _parse_points(problem)
            self.assertGreaterEqual(len(points), 4, f"parse: {problem!r}")
            n = len(points)
            mx = sum(x for x, _ in points) / n
            my = sum(y for _, y in points) / n
            sxy = sum((x - mx) * (y - my) for x, y in points)
            sxx = sum((x - mx) ** 2 for x, _ in points)
            syy = sum((y - my) ** 2 for _, y in points)
            expected = round(sxy / math.sqrt(sxx * syy), 3)
            stated = float(self.SOLUTION.search(solution).group("r"))
            self.assertAlmostEqual(
                stated, expected, places=3,
                msg=f"r wrong for {problem!r} -> {solution!r}",
            )


class RegressionLineTests(TestCase):
    SOLUTION = re.compile(
        rf"y = (?P<m>{NUM}) x (?P<sign>[+-]) (?P<b>{NUM})"
    )

    def test_regression(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_regression_line"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            points = _parse_points(problem)
            n = len(points)
            mx = sum(x for x, _ in points) / n
            my = sum(y for _, y in points) / n
            sxy = sum((x - mx) * (y - my) for x, y in points)
            sxx = sum((x - mx) ** 2 for x, _ in points)
            exp_m = round(sxy / sxx, 3)
            exp_b = round(my - (sxy / sxx) * mx, 3)
            s = self.SOLUTION.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            stated_m = float(s.group("m"))
            stated_b = float(s.group("b"))
            if s.group("sign") == "-":
                stated_b = -stated_b
            self.assertAlmostEqual(
                stated_m, exp_m, places=3,
                msg=f"slope wrong for {problem!r} -> {solution!r}",
            )
            self.assertAlmostEqual(
                stated_b, exp_b, places=3,
                msg=f"intercept wrong for {problem!r} -> {solution!r}",
            )


class MarginOfErrorTests(TestCase):
    PROBLEM = re.compile(
        rf"p = (?P<p>{NUM}), sample size n = (?P<n>\d+), and critical "
        rf"value z = (?P<z>{NUM})"
    )
    SOLUTION = re.compile(rf"\$(?P<moe>{NUM})\$")

    def test_margin_of_error(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_margin_of_error"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            p, n, z = float(m.group("p")), int(m.group("n")), float(m.group("z"))
            expected = round(z * math.sqrt(p * (1 - p) / n), 3)
            stated = float(self.SOLUTION.search(solution).group("moe"))
            self.assertAlmostEqual(
                stated, expected, places=3,
                msg=f"MOE wrong for {problem!r} -> {solution!r}",
            )


class StandardErrorMeanTests(TestCase):
    PROBLEM = re.compile(
        rf"standard deviation s = (?P<s>{NUM}) and size n = (?P<n>\d+)"
    )
    SOLUTION = re.compile(rf"\$(?P<se>{NUM})\$")

    def test_standard_error(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_standard_error_mean"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            s, n = float(m.group("s")), int(m.group("n"))
            expected = round(s / math.sqrt(n), 3)
            stated = float(self.SOLUTION.search(solution).group("se"))
            self.assertAlmostEqual(
                stated, expected, places=3,
                msg=f"SE wrong for {problem!r} -> {solution!r}",
            )


class SampleProportionCITests(TestCase):
    PROBLEM = re.compile(
        rf"proportion p = (?P<p>{NUM}), size n = (?P<n>\d+), and critical "
        rf"value z = (?P<z>{NUM})"
    )
    SOLUTION = re.compile(rf"\((?P<low>{NUM}), (?P<high>{NUM})\)")

    def test_confidence_interval(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_sample_proportion_ci"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            m = self.PROBLEM.search(problem)
            self.assertIsNotNone(m, f"could not parse: {problem!r}")
            p, n, z = float(m.group("p")), int(m.group("n")), float(m.group("z"))
            moe = z * math.sqrt(p * (1 - p) / n)
            s = self.SOLUTION.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            self.assertAlmostEqual(
                float(s.group("low")), round(p - moe, 3), places=3,
                msg=f"CI low wrong for {problem!r} -> {solution!r}",
            )
            self.assertAlmostEqual(
                float(s.group("high")), round(p + moe, 3), places=3,
                msg=f"CI high wrong for {problem!r} -> {solution!r}",
            )


class RelativeFrequencyTests(TestCase):
    COUNTS = re.compile(r"category counts: (?P<counts>[\d, ]+?)\.")
    CATEGORY = re.compile(r"relative frequency of category (?P<idx>\d+)")
    SOLUTION = re.compile(r"\$(?P<num>\d+)/(?P<den>\d+)\$")

    def test_relative_frequency(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS["stat_relative_frequency"]
        for _ in range(SAMPLES):
            problem, solution = gen()
            cm = self.COUNTS.search(problem)
            im = self.CATEGORY.search(problem)
            self.assertIsNotNone(cm, f"could not parse: {problem!r}")
            self.assertIsNotNone(im, f"could not parse: {problem!r}")
            counts = [int(c) for c in cm.group("counts").split(", ")]
            idx = int(im.group("idx")) - 1
            expected = counts[idx] / sum(counts)
            s = self.SOLUTION.search(solution)
            self.assertIsNotNone(s, f"could not parse solution: {solution!r}")
            num, den = int(s.group("num")), int(s.group("den"))
            self.assertEqual(
                math.gcd(num, den), 1,
                f"fraction not reduced: {solution!r}",
            )
            self.assertAlmostEqual(
                num / den, expected, places=3,
                msg=f"rel freq wrong for {problem!r} -> {solution!r}",
            )
