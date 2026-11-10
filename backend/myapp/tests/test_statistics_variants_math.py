"""Math-correctness tests for the statistics, probability and finance variants.

Each test forces one variant of a generator (see statistics_variants.py),
parses the problem text, recomputes the answer independently, and checks the
served solution, over 2000 seeded samples.
"""
import itertools
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators import statistics_variants  # noqa: F401 - attaches the variants
from myapp.tests.test_prealgebra_variants_math import INT, frac

SAMPLES = 2000
TOL = 0.0005 + 1e-9  # half-up rounding can land exactly 0.0005 away
NUM = r"(-?\d+(?:\.\d+)?)"


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


class MeanMissingScore(_Base):
    name, variant = "mean_median", "missing_score"

    def test(self):
        for problem, solution in self.samples():
            scores = [int(v) for v in self.search(r"scores are ([\d, ]+)\. What", problem)[1].split(", ")]
            n, target = map(int, self.search(r"all (\d+) tests exactly (\d+)\?", problem).groups())
            self.assertEqual(Fraction(sum(scores) + int(solution), n), target, problem)
            self.assertTrue(0 <= int(solution) <= 100)


class SdTransform(_Base):
    name, variant = "data_summary", "transform_sd"

    def test(self):
        for problem, solution in self.samples():
            sd = Fraction(self.search(r"deviation of \$([\d.]+)\$", problem)[1])
            data = [-1, 1]  # a two-point data set with SD 1, scaled to sd
            base = [v * sd for v in data]
            m = re.search(r"If \$(\d+)\$ is added", problem)
            new = [v + int(m[1]) for v in base] if m else \
                [v * int(self.search(r"multiplied by \$(\d+)\$", problem)[1]) for v in base]
            mean = sum(new) / len(new)
            pop_sd = math.sqrt(sum((v - mean) ** 2 for v in new) / len(new))
            self.close(solution, pop_sd, problem)


class FiveNumberBoxPlot(_Base):
    name, variant = "stat_five_number_summary", "box_plot"

    def test(self):
        for problem, solution in self.samples():
            mn, mx, q1, q3 = map(int, self.search(r"whiskers from \$(\d+)\$ to \$(\d+)\$ and a box from "
                                                  r"\$(\d+)\$ to \$(\d+)\$", problem).groups())
            want = q3 - q1 if "interquartile range" in problem else mx - mn
            self.assertEqual(int(solution), want, problem)


class CorrelationAfterTransformation(_Base):
    name, variant = "stat_correlation_coefficient", "after_transformation"

    def test(self):
        for problem, solution in self.samples():
            r = Fraction(self.search(r"\$r = " + NUM + r"\$", problem)[1])
            a = int(self.search(r"replaced by \$" + INT + r"[xy]", problem)[1])
            # Build data with correlation exactly r, transform, and recompute.
            xs = [Fraction(v) for v in (-1, 1, -1, 1)]
            noise = [Fraction(v) for v in (1, -1, -1, 1)]
            k = (1 - r * r) ** 0.5
            ys = [float(r) * float(x) + k * float(e) for x, e in zip(xs, noise)]
            xs = [float(x) for x in xs]
            if "Each x-value" in problem:
                xs = [a * x for x in xs]
            else:
                ys = [a * y for y in ys]
            mx, my = sum(xs) / 4, sum(ys) / 4
            cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            corr = cov / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
            self.close(solution, corr, problem)


class RegressionInterceptFromMeans(_Base):
    name, variant = "stat_regression_line", "intercept_from_means"

    def test(self):
        for problem, solution in self.samples():
            slope = Fraction(self.search(r"slope \$" + NUM + r"\$", problem)[1])
            xbar = Fraction(self.search(r"\\bar\{x\} = " + NUM, problem)[1])
            ybar = Fraction(self.search(r"\\bar\{y\} = " + NUM, problem)[1])
            self.assertEqual(slope * xbar + Fraction(solution), ybar, problem)


class MarginSampleSize(_Base):
    name, variant = "stat_margin_of_error", "sample_size"

    def test(self):
        for problem, solution in self.samples():
            p = Fraction(self.search(r"proportion near \$([\d.]+)\$", problem)[1])
            z = Fraction(self.search(r"\$z = ([\d.]+)\$", problem)[1])
            e = Fraction(self.search(r"at most \$([\d.]+)\$", problem)[1])
            ok = lambda n: z * z * p * (1 - p) / n <= e * e  # noqa: E731  (E^2 compare, exact)
            n = int(solution)
            self.assertTrue(ok(n), problem)
            self.assertFalse(ok(n - 1), problem)


class StandardErrorSampleSize(_Base):
    name, variant = "stat_standard_error_mean", "sample_size"

    def test(self):
        for problem, solution in self.samples():
            sd = Fraction(self.search(r"\$s = ([\d.]+)\$", problem)[1])
            se = Fraction(self.search(r"mean is \$([\d.]+)\$", problem)[1])
            self.assertEqual(sd * sd / (se * se), int(solution), problem)


class ProportionFromInterval(_Base):
    name, variant = "stat_sample_proportion_ci", "from_interval"

    def test(self):
        for problem, solution in self.samples():
            low, high = map(Fraction, self.search(r"is \$\(([\d.]+), ([\d.]+)\)\$", problem).groups())
            want = (low + high) / 2 if "sample proportion" in problem else (high - low) / 2
            self.assertEqual(Fraction(solution), want, problem)


class RelativeFrequencyCount(_Base):
    name, variant = "stat_relative_frequency", "count_from_frequency"

    def test(self):
        for problem, solution in self.samples():
            total = int(self.search(r"survey of \$(\d+)\$", problem)[1])
            rel = Fraction(self.search(r"was \$([\d.]+)\$", problem)[1])
            self.assertEqual(Fraction(int(solution), total), rel, problem)


class NormalValueAtPercentile(_Base):
    name, variant = "stat_normal_probability", "value_at_percentile"

    def test(self):
        from statistics import NormalDist
        for problem, solution in self.samples():
            mu, sigma = map(int, self.search(r"mean \$(\d+)\$ and standard deviation \$(\d+)\$", problem).groups())
            pct = int(self.search(r"The (\d+)th percentile", problem)[1])
            z = Fraction(self.search(r"\$z = " + NUM + r"\$", problem)[1])
            # The stated z really is that percentile (to its 3 decimals)...
            self.assertAlmostEqual(float(z), NormalDist().inv_cdf(pct / 100), delta=0.0006)
            # ...and the answer uses it.
            self.close(solution, mu + z * sigma, problem)


class PercentileValueAtRank(_Base):
    name, variant = "stat_percentile_rank", "value_at_rank"

    def test(self):
        for problem, solution in self.samples():
            data = [int(v) for v in self.search(r"data set: ([\d, ]+)\.", problem)[1].split(", ")]
            rank = Fraction(self.search(r"rank of ([\d.]+)\?", problem)[1])
            fits = [v for v in data if Fraction(100 * sum(1 for w in data if w < v), len(data)) == rank]
            self.assertEqual(fits, [int(solution)], problem)


class TestStatisticDecision(_Base):
    name, variant = "stat_test_statistic", "reject_decision"

    def test(self):
        for problem, solution in self.samples():
            mu0 = int(self.search(r"H_0: \\mu = (\d+)", problem)[1])
            n = int(self.search(r"\$n = (\d+)\$", problem)[1])
            xbar = Fraction(self.search(r"with mean \$" + NUM + r"\$", problem)[1])
            sigma = int(self.search(r"deviation is \$(\d+)\$", problem)[1])
            z = (xbar - mu0) / (sigma / math.sqrt(n))
            self.assertEqual(solution, "yes" if abs(z) > 1.96 else "no", problem)


class VarianceLinearTransform(_Base):
    name, variant = "stat_discrete_variance", "linear_transform"

    def test(self):
        for problem, solution in self.samples():
            var = Fraction(self.search(r"variance \$([\d.]+)\$", problem)[1])
            a = int(self.search(r"variance of \$" + INT + "X", problem)[1])
            self.assertEqual(Fraction(solution), a * a * var, problem)


class CountingAtLeastOne(_Base):
    name, variant = "stat_counting_probability", "at_least_one"

    def test(self):
        for problem, solution in self.samples():
            red, green, k = map(int, self.search(r"(\d+) red and (\d+) green\. You draw (\d+)", problem).groups())
            balls = ["r"] * red + ["g"] * green
            combos = list(itertools.combinations(range(len(balls)), k))
            hits = sum(1 for c in combos if any(balls[i] == "r" for i in c))
            self.assertEqual(frac(solution), Fraction(hits, len(combos)), problem)


class DiceCountOutcomes(_Base):
    name, variant = "dice_sum_probability", "count_outcomes"

    def test(self):
        for problem, solution in self.samples():
            sides, target = map(int, self.search(r"fair (\d+)-sided dice.*the sum (\d+)\?", problem).groups())
            count = sum(1 for a in range(1, sides + 1) for b in range(1, sides + 1) if a + b == target)
            self.assertEqual(int(solution), count, problem)


class ProbabilityFromOdds(_Base):
    name, variant = "stat_odds_probability", "probability_from_odds"

    def test(self):
        for problem, solution in self.samples():
            kind, a, b = self.search(r"odds (against|in favor of) an event are \$(\d+):(\d+)\$", problem).groups()
            a, b = int(a), int(b)
            p = Fraction(a, a + b) if kind == "in favor of" else Fraction(b, a + b)
            self.assertEqual(frac(solution), p, problem)


class BinomialAtLeastOne(_Base):
    name, variant = "binomial_distribution", "at_least_one"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"each of \$(\d+)\$", problem)[1])
            p = float(self.search(r"success is \$([\d.]+)\$", problem)[1])
            total = sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(1, n + 1))
            self.close(solution, total, problem)


class ConditionalBayesTest(_Base):
    name, variant = "conditional_probability", "bayes_test"

    def test(self):
        for problem, solution in self.samples():
            prev, sens, fpr = (Fraction(v) / 100 for v in re.findall(r"([\d.]+)%", problem)[:3])
            # Count a population of 1,000,000 people exactly.
            pop = 10 ** 6
            sick = pop * prev
            true_pos, false_pos = sick * sens, (pop - sick) * fpr
            self.close(solution, true_pos / (true_pos + false_pos), problem)


class PercentageWholeFromPart(_Base):
    name, variant = "percentage", "whole_from_part"

    def test(self):
        for problem, solution in self.samples():
            pct, part = self.search(r"\$(\d+)\\%\$ of what number is \$([\d.]+)\$", problem).groups()
            self.assertEqual(Fraction(int(pct), 100) * int(solution), Fraction(part), problem)


class PercentageDifferencePrices(_Base):
    name, variant = "percentage_difference", "prices"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"for \$(\d+)\$ dollars and another for \$(\d+)\$", problem).groups())
            self.close(solution, abs(a - b) / ((a + b) / 2) * 100, problem)


class PercentageErrorObserved(_Base):
    name, variant = "percentage_error", "observed_from_error"

    def test(self):
        for problem, solution in self.samples():
            pct, exact = map(int, self.search(r"\$(\d+)\\%\$ error compared with the exact value \$(\d+)\$",
                                              problem).groups())
            observed = Fraction(solution)
            self.assertEqual(abs(observed - exact) / exact * 100, pct, problem)
            self.assertEqual(observed > exact, "too high" in problem)


class SimpleInterestRate(_Base):
    name, variant = "simple_interest", "rate_from_interest"

    def test(self):
        for problem, solution in self.samples():
            P, I, t = map(int, self.search(r"principal of \$(\d+)\$ dollars earns \$(\d+)\$ dollars of simple "
                                           r"interest in \$(\d+)\$", problem).groups())
            self.assertEqual(P * Fraction(int(solution), 100) * t, I, problem)


class CompoundYearsToReach(_Base):
    name, variant = "compound_interest", "years_to_reach"

    def test(self):
        for problem, solution in self.samples():
            P, r = map(int, self.search(r"\$(\d+)\$ dollars is invested at \$(\d+)\\%\$", problem).groups())
            target = Fraction(self.search(r"more than \$([\d.]+)\$", problem)[1])
            t = int(solution)
            bal = lambda y: P * Fraction(100 + r, 100) ** y  # noqa: E731
            self.assertGreater(bal(t), target, problem)
            self.assertLessEqual(bal(t - 1), target, problem)


class ProfitSellingPrice(_Base):
    name, variant = "profit_loss_percent", "selling_price"

    def test(self):
        for problem, solution in self.samples():
            cost, pct, kind = self.search(r"costs \$(\d+)\$ dollars to make and is sold at a \$(\d+)\\%\$ "
                                          r"(profit|loss)", problem).groups()
            price = int(cost) * Fraction(100 + int(pct) if kind == "profit" else 100 - int(pct), 100)
            cents = math.floor(price * 100 + Fraction(1, 2))
            self.assertEqual(round(Fraction(solution) * 100), cents, problem)


class ZCompareTwoScores(_Base):
    variant = "compare_two_scores"

    def test(self):
        for name in ("stat_z_score", "alg2_z_score"):
            for problem, solution in self.samples(name):
                x1, m1, s1, x2, m2, s2 = map(int, self.search(
                    r"scored \$(-?\d+)\$ on a test with mean \$(\d+)\$ and standard deviation \$(\d+)\$\. Ben "
                    r"scored \$(-?\d+)\$ on a test with mean \$(\d+)\$ and standard deviation \$(\d+)\$",
                    problem).groups())
                z1, z2 = (x1 - m1) / s1, (x2 - m2) / s2
                self.assertNotAlmostEqual(z1, z2, places=9)
                self.close(solution, max(z1, z2), problem)


class ZReverse(_Base):
    variant = "reverse"

    def test(self):
        for name in ("stat_z_score", "alg2_z_score"):
            for problem, solution in self.samples(name):
                m = re.search(r"mean \$(\d+)\$ and standard deviation \$(\d+)\$\. What value has a z-score of \$"
                              + NUM, problem)
                if m:
                    mu, sigma, z = int(m[1]), int(m[2]), Fraction(m[3])
                    self.assertEqual((Fraction(solution) - mu) / sigma, z, problem)
                else:
                    x, z, mu = self.search(r"value of \$" + NUM + r"\$ has a z-score of \$" + NUM
                                           + r"\$ in a distribution with mean \$(\d+)\$", problem).groups()
                    self.assertEqual((Fraction(x) - int(mu)) / Fraction(solution), Fraction(z), problem)


def table_cols(problem):
    body = re.search(r"\\begin\{array\}\{[^}]*\}(.*?)\\end\{array\}", problem).group(1)
    top, bottom = body.split(r"\\ \hline")
    return [int(c) for c in top.split("&")[1:]], [int(c) for c in bottom.split("&")[1:]]


class MedianFromTable(_Base):
    name, variant = "mean_median", "median_from_table"

    def test(self):
        import statistics
        for problem, solution in self.samples():
            values, counts = table_cols(problem)
            data = [v for v, c in zip(values, counts) for _ in range(c)]
            self.assertEqual(Fraction(solution), Fraction(statistics.median(data)).limit_denominator(), problem)


class VarianceOnly(_Base):
    name, variant = "data_summary", "variance_only"

    def test(self):
        import statistics
        for problem, solution in self.samples():
            data = [int(v) for v in self.search(r"data set ([\d, ]+)\.", problem)[1].split(", ")]
            self.close(solution, statistics.pvariance(data), problem)


class CorrelationRSquared(_Base):
    name, variant = "stat_correlation_coefficient", "r_squared"

    def test(self):
        for problem, solution in self.samples():
            r = Fraction(self.search(r"\$r = " + NUM + r"\$", problem)[1])
            self.assertEqual(Fraction(solution), r * r * 100, problem)


class RegressionResidual(_Base):
    name, variant = "stat_regression_line", "residual"

    def test(self):
        for problem, solution in self.samples():
            m, sign, b = self.search(r"\\hat\{y\} = " + NUM + r"x ([+-]) ([\d.]+)\$", problem).groups()
            b = Fraction(b) * (1 if sign == "+" else -1)
            x, y = map(int, self.search(r"point \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            self.assertEqual(Fraction(solution), y - (Fraction(m) * x + b), problem)


class MarginScaleSample(_Base):
    name, variant = "stat_margin_of_error", "scale_sample"

    def test(self):
        for problem, solution in self.samples():
            k2 = int(self.search(r"multiplied by \$(\d+)\$", problem)[1])
            e = lambda n: 1.96 * math.sqrt(0.25 / n)  # noqa: E731
            self.assertAlmostEqual(float(frac(solution)), e(100 * k2) / e(100), places=9)


class ProportionFromCounts(_Base):
    name, variant = "stat_sample_proportion_ci", "from_counts"

    def test(self):
        for problem, solution in self.samples():
            x, n = map(int, self.search(r"\$(\d+)\$ of \$(\d+)\$ people", problem).groups())
            z = float(self.search(r"\$z = ([\d.]+)\$", problem)[1])
            p = x / n
            e = z * math.sqrt(p * (1 - p) / n)
            low, high = map(float, re.fullmatch(r"\((-?[\d.]+), (-?[\d.]+)\)", solution).groups())
            self.assertAlmostEqual(low, p - e, delta=TOL)
            self.assertAlmostEqual(high, p + e, delta=TOL)


class RelativeFrequencyJoint(_Base):
    name, variant = "stat_relative_frequency", "joint"

    def test(self):
        for problem, solution in self.samples():
            c = {k: int(v) for k, v in re.findall(r"([AB])&([XY]): (\d+)", problem) and
                 [(a + b, v) for a, b, v in re.findall(r"([AB])&([XY]): (\d+)", problem)]}
            cell = "".join(self.search(r"frequency of ([AB]) and ([XY])", problem).groups())
            self.assertEqual(frac(solution), Fraction(c[cell], sum(c.values())), problem)


class NormalExpectedCount(_Base):
    name, variant = "stat_normal_probability", "expected_count"

    def test(self):
        for problem, solution in self.samples():
            mu, sigma, n = map(int, self.search(r"mean \$(\d+)\$ and standard deviation \$(\d+)\$\. Out of \$(\d+)\$",
                                                problem).groups())
            lo, hi = map(float, self.search(r"between \$" + NUM + r"\$ and \$" + NUM + r"\$", problem).groups())
            p = 0.5 * (math.erf((hi - mu) / (sigma * math.sqrt(2))) - math.erf((lo - mu) / (sigma * math.sqrt(2))))
            self.assertLessEqual(abs(int(solution) - n * p), 0.5 + 1e-9, problem)


class TestStatisticMeanForZ(_Base):
    name, variant = "stat_test_statistic", "mean_for_z"

    def test(self):
        for problem, solution in self.samples():
            mu0, sigma, n = map(int, self.search(r"\\mu = (\d+)\$ with \$\\sigma = (\d+)\$ and \$n = (\d+)\$", problem).groups())
            z = float(self.search(r"\$z = " + NUM + r"\$", problem)[1])
            self.close(solution, mu0 + z * sigma / math.sqrt(n), problem)


class DiscreteSd(_Base):
    name, variant = "stat_discrete_variance", "standard_deviation"

    def test(self):
        for problem, solution in self.samples():
            values = [int(v) for v in self.search(r"takes the values ([\d, ]+) with", problem)[1].split(", ")]
            probs = [Fraction(v) for v in self.search(r"probabilities ([\d., ]+)\.", problem)[1].split(", ")]
            self.assertEqual(sum(probs), 1)
            ex = sum(v * p for v, p in zip(values, probs))
            ex2 = sum(v * v * p for v, p in zip(values, probs))
            self.close(solution, math.sqrt(ex2 - ex * ex), problem)


class DiceDifference(_Base):
    name, variant = "dice_sum_probability", "difference"

    def test(self):
        for problem, solution in self.samples():
            sides, d = map(int, self.search(r"fair (\d+)-sided dice.*differ by exactly (\d+)\?", problem).groups())
            hits = sum(1 for a in range(1, sides + 1) for b in range(1, sides + 1) if abs(a - b) == d)
            self.assertEqual(frac(solution), Fraction(hits, sides * sides), problem)


class OddsAgainst(_Base):
    name, variant = "stat_odds_probability", "odds_against"

    def test(self):
        for problem, solution in self.samples():
            p = frac(self.search(r"event is \$([\d/]+)\$", problem)[1])
            a, b = map(int, solution.split(":"))
            self.assertEqual(math.gcd(a, b), 1)
            self.assertEqual(Fraction(b, a + b), p, problem)


class BinomialExpected(_Base):
    name, variant = "binomial_distribution", "expected_count"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"Over \$(\d+)\$ independent trials with success probability \$([\d.]+)\$", problem)
            if m:
                self.assertEqual(Fraction(solution), int(m[1]) * Fraction(m[2]), problem)
            else:
                p, mu = self.search(r"probability \$([\d.]+)\$ and an expected \$([\d.]+)\$", problem).groups()
                self.assertEqual(int(solution) * Fraction(p), Fraction(mu), problem)


class ConditionalTwoWay(_Base):
    name, variant = "conditional_probability", "two_way_table"

    def test(self):
        for problem, solution in self.samples():
            c = {a + b: int(v) for a, b, v in re.findall(r"([AB])&([XY]): (\d+)", problem)}
            target, given = self.search(r"P\(([ABXY]) \| ([ABXY])\)", problem).groups()
            both = sum(v for k, v in c.items() if target in k and given in k)
            total = sum(v for k, v in c.items() if given in k)
            self.close(solution, both / total, problem)


class PercentageTip(_Base):
    name, variant = "percentage", "tip"

    def test(self):
        for problem, solution in self.samples():
            bill, pct = self.search(r"bill is \$([\d.]+)\$ dollars\. How much is a \$(\d+)\\%\$", problem).groups()
            tip = Fraction(bill) * int(pct) / 100
            self.assertEqual(round(Fraction(solution) * 100), math.floor(tip * 100 + Fraction(1, 2)), problem)


class SimpleInterestTotal(_Base):
    name, variant = "simple_interest", "total_amount"

    def test(self):
        for problem, solution in self.samples():
            P, r, t = map(int, self.search(r"\$(\d+)\$ dollars earns \$(\d+)\\%\$ simple interest per year\. What is "
                                           r"the total balance after \$(\d+)\$", problem).groups())
            balance = Fraction(P)
            for _ in range(t):
                balance += Fraction(P * r, 100)
            self.assertEqual(Fraction(solution), balance, problem)


class CompoundMonthly(_Base):
    name, variant = "compound_interest", "monthly"

    def test(self):
        for problem, solution in self.samples():
            P, r, t = map(int, self.search(r"\$(\d+)\$ dollars is invested at \$(\d+)\\%\$.*after \$(\d+)\$ years",
                                           problem).groups())
            balance = P
            for _ in range(12 * t):
                balance *= 1 + r / 1200
            self.assertAlmostEqual(float(solution), balance, delta=0.005 + 1e-9, msg=problem)


class ProfitMarkupDiscount(_Base):
    name, variant = "profit_loss_percent", "markup_then_discount"

    def test(self):
        for problem, solution in self.samples():
            up, down = map(int, self.search(r"up \$(\d+)\\%\$ above cost, then sells it at \$(\d+)\\%\$", problem).groups())
            cost = Fraction(100)
            price = cost * (100 + up) / 100 * (100 - down) / 100
            self.assertEqual(Fraction(solution), (price - cost) / cost * 100, problem)
