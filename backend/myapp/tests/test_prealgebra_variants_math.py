"""Math-correctness tests for the pre-algebra variants (prealgebra_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently (brute force where uniqueness matters), and checks the served
solution, over 2000 seeded samples.
"""
import math
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS

SAMPLES = 2000
INT = r"(-?\d+)"
NUM = r"(-?\d+(?:\.\d+)?)"


def frac(text):
    """A typed or LaTeX value as a Fraction: '3/4', '-2', '0.25', '-\\frac{3}{4}'."""
    text = text.replace("$", "").strip()
    m = re.fullmatch(r"(-?)\\frac\{(\d+)\}\{(\d+)\}", text)
    if m:
        value = Fraction(int(m.group(2)), int(m.group(3)))
        return -value if m.group(1) else value
    return Fraction(text)


def ints(text):
    return [int(v) for v in re.findall(r"-?\d+", text)]


def table_rows(problem):
    """The two rows of the first LaTeX array table, as lists of strings."""
    body = re.search(r"\\begin\{array\}\{[^}]*\}(.*?)\\end\{array\}", problem).group(1)
    top, bottom = body.split(r"\\ \hline")
    return [cell.strip() for cell in top.split("&")][1:], [cell.strip() for cell in bottom.split("&")][1:]


class _Base(SimpleTestCase):
    name = variant = None

    def samples(self):
        import random
        random.seed(0)
        gen = LOCAL_GENERATORS[self.name]
        for _ in range(SAMPLES):
            problem, solution, _steps = gen(variant=self.variant)
            yield problem, solution.replace("$", "").strip()

    def search(self, pattern, problem):
        m = re.search(pattern, problem)
        self.assertIsNotNone(m, problem)
        return m


class UnitRateBetterBuy(_Base):
    name, variant = "pre_unit_rate", "better_buy"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"sells \$(\d+)\$ ounces of cereal for \$([\d.]+)\$ dollars.*"
                            r"sells \$(\d+)\$ ounces for \$([\d.]+)\$ dollars", problem)
            s1, p1, s2, p2 = int(m[1]), Fraction(m[2]), int(m[3]), Fraction(m[4])
            best = min(p1 / s1, p2 / s2)
            self.assertEqual(best.denominator in (1, 2, 4, 5, 10, 20, 25, 50, 100), True)
            self.assertEqual(Fraction(solution), best, problem)


class RatioPartOfWhole(_Base):
    name, variant = "pre_equivalent_ratio", "part_of_whole"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"is \$(\d+):(\d+)\$\. There are \$(\d+)\$", problem)
            a, b, total = int(m[1]), int(m[2]), int(m[3])
            self.assertEqual(total % (a + b), 0)
            self.assertEqual(int(solution), total // (a + b) * b, problem)


class ProportionBinomial(_Base):
    name, variant = "pre_solve_proportion", "binomial_numerator"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{x ([+-]) (\d+)\}\{(\d+)\} = \\frac\{(\d+)\}\{(\d+)\}", problem)
            c = int(m[2]) * (1 if m[1] == "+" else -1)
            a, b, d = int(m[3]), int(m[4]), int(m[5])
            x = frac(solution)
            self.assertEqual((x + c) / a, Fraction(b, d), problem)


class ScaleFindTheScale(_Base):
    name, variant = "pre_scale_length", "find_the_scale"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d+)\$ cm represents \$(\d+)\$ km", problem)
            self.assertEqual(Fraction(solution), Fraction(int(m[2]), int(m[1])), problem)


class IntegersSumAndProduct(_Base):
    name, variant = "pre_integer_operations", "sum_and_product"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"sum of \$" + INT + r"\$ and a product of \$" + INT, problem)
            total, product = int(m[1]), int(m[2])
            pairs = {
                (min(x, total - x), max(x, total - x))
                for x in range(-50, 51) if x * (total - x) == product
            }
            self.assertEqual(len(pairs), 1, problem)
            self.assertEqual(int(solution), pairs.pop()[1], problem)


class RationalsSignedChange(_Base):
    name, variant = "pre_rational_operations", "signed_change"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"at \$([^$]+)\$ meters.*The diver (descends|rises) \$([^$]+)\$ meters",
                            problem)
            start, change = frac(m[1]), frac(m[3])
            end = start - change if m[2] == "descends" else start + change
            self.assertEqual(frac(solution), end, problem)


class AbsoluteNumberLine(_Base):
    name, variant = "pre_absolute_value", "number_line_distance"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"at \$" + INT + r"\$ and point \$B\$ is at \$" + INT, problem)
            self.assertEqual(int(solution), abs(int(m[1]) - int(m[2])), problem)


class OneStepIntegerExtreme(_Base):
    name, variant = "pre_one_step_inequality", "integer_extreme"

    def test(self):
        ops = {"<": lambda l, r: l < r, "\\leq": lambda l, r: l <= r,
               ">": lambda l, r: l > r, "\\geq": lambda l, r: l >= r}
        for problem, solution in self.samples():
            m = self.search(r"the (greatest|smallest) integer that satisfies \$(\d+)x (<|>|\\leq|\\geq) "
                            + INT, problem)
            k, op, c = int(m[2]), m[3], int(m[4])
            sols = [x for x in range(-100, 101) if ops[op](k * x, c)]
            expected = max(sols) if m[1] == "greatest" else min(sols)
            self.assertEqual(int(solution), expected, problem)


class MultiStepBudget(_Base):
    name, variant = "pre_multi_step_inequality", "budget"

    def test(self):
        for problem, solution in self.samples():
            budget, fee, price = ints(problem)[:3]
            best = max(t for t in range(0, 200) if fee + price * t <= budget)
            self.assertEqual(int(solution), best, problem)


class SciHowManyTimes(_Base):
    name, variant = "pre_scientific_notation_ops", "how_many_times"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"is \$(\d+) \\times 10\^\{" + INT + r"\}\$ than \$(\d+) \\times 10\^\{"
                            + INT, problem)
            a, e1, b, e2 = int(m[1]), int(m[2]), int(m[3]), int(m[4])
            expected = Fraction(a * 10 ** (e1 + 20), b * 10 ** (e2 + 20))
            self.assertEqual(expected.denominator, 1)
            self.assertEqual(int(solution), expected, problem)


class ExponentsCommonBase(_Base):
    name, variant = "pre_integer_exponent_rules", "common_base"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d+)\^\{(\d+)\} \\cdot (\d+)\^\{(\d+)\} = (\d+)\^", problem)
            v1, m1, v2, n2, base = (int(g) for g in m.groups())
            self.assertEqual(base ** int(solution), v1 ** m1 * v2 ** n2, problem)


class ProportionalityTable(_Base):
    name, variant = "pre_constant_of_proportionality", "table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = table_rows(problem)
            ks = {Fraction(int(y), int(x)) for x, y in zip(xs, ys)}
            self.assertEqual(len(ks), 1, problem)
            self.assertEqual(frac(solution), ks.pop(), problem)


class EvaluateFunctionTable(_Base):
    name, variant = "pre_evaluate_function", "table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = table_rows(problem)
            f = dict(zip(map(int, xs), map(int, ys)))
            m = re.search(r"What is \$f\(" + INT + r"\) \+ f\(" + INT + r"\)\$", problem)
            if m:
                expected = f[int(m[1])] + f[int(m[2])]
            else:
                v = int(self.search(r"is \$f\(x\) = " + INT, problem)[1])
                matches = [x for x, y in f.items() if y == v]
                self.assertEqual(len(matches), 1, problem)
                expected = matches[0]
            self.assertEqual(int(solution), expected, problem)


class SlopeMissingCoordinate(_Base):
    name, variant = "pre_slope_from_two_points", "missing_coordinate"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"slope \$" + INT + r"\$ passes through \$\(" + INT + r", k\)\$ and \$\("
                            + INT + ", " + INT, problem)
            slope, x1, x2, y2 = (int(g) for g in m.groups())
            k = int(solution)
            self.assertEqual(Fraction(y2 - k, x2 - x1), slope, problem)


class LinearInputFromOutput(_Base):
    name, variant = "pre_linear_function_value", "input_from_output"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$m = " + INT + r"\$ and y-intercept \$b = " + INT + r"\$.*\$y = " + INT,
                            problem)
            slope, b, y = (int(g) for g in m.groups())
            self.assertEqual(slope * frac(solution) + b, y, problem)


class SlopeInterceptCoefficient(_Base):
    name, variant = "pre_slope_intercept_form", "coefficient_from_slope"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$Ax ([+-]) (\d*)y = " + INT + r"\$ has slope \$" + INT, problem)
            B = int(m[2] or 1) * (1 if m[1] == "+" else -1)
            slope = int(m[4])
            self.assertEqual(Fraction(-int(solution), B), slope, problem)


class LineParallelPerpendicular(_Base):
    name, variant = "pre_line_from_slope_point", "parallel_or_perpendicular"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"(parallel|perpendicular) to \$y = (-?\d*)x", problem)
            m0 = Fraction(int(m[2]) if m[2] not in ("", "-") else (-1 if m[2] == "-" else 1))
            x0, y0 = map(int, self.search(r"point \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            want = m0 if m[1] == "parallel" else -1 / m0
            sm = re.fullmatch(r"y = (-?[\d/]*)x(?: ([+-]) ([\d/]+))?", solution)
            self.assertIsNotNone(sm, solution)
            slope = Fraction({"": "1", "-": "-1"}.get(sm[1], sm[1]))
            b = Fraction(sm[3]) * (1 if sm[2] == "+" else -1) if sm[2] else Fraction(0)
            self.assertEqual(slope, want, problem)
            self.assertEqual(slope * x0 + b, y0, problem)


class CompareInitialValue(_Base):
    name, variant = "pre_compare_functions", "initial_value"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, row)) for row in table_rows(problem))
            slope = Fraction(ys[1] - ys[0], xs[1] - xs[0])
            b_a = ys[0] - slope * xs[0]
            b_b = int(self.search(r"crosses the y-axis at \$" + INT, problem)[1])
            self.assertNotEqual(b_a, b_b)
            self.assertEqual(solution, "A" if b_a > b_b else "B", problem)


def parse_xy(text):
    """(a, b, c) of a LaTeX line ``ax + by = c`` such as ``-3x + 4y = 7`` or ``x - y = 2``."""
    m = re.fullmatch(r"(-?\d*)x ([+-]) (\d*)y = (-?\d+)", text.strip())
    a = {"": 1, "-": -1}[m[1]] if m[1] in ("", "-") else int(m[1])
    b = int(m[3] or 1) * (1 if m[2] == "+" else -1)
    return a, b, int(m[4])


class SystemNoSolutionParameter(_Base):
    name, variant = "pre_system_solution_count", "no_solution_parameter"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"system \$([^$]+)\$ and \$kx ([+-]) (\d*)y = " + INT, problem)
            a1, b1, c1 = parse_xy(m[1])
            b2 = int(m[3] or 1) * (1 if m[2] == "+" else -1)
            c2 = int(m[4])
            # The only k making the lines parallel (determinant 0)...
            ks = [k for k in range(-100, 101) if a1 * b2 - b1 * k == 0]
            self.assertEqual(ks, [int(solution)], problem)
            # ...and they are distinct lines, so there is no solution.
            self.assertNotEqual(Fraction(b2, b1) * c1, c2, problem)


class MadTransform(_Base):
    name, variant = "pre_mean_absolute_deviation", "transform"

    def test(self):
        for problem, solution in self.samples():
            data = ints(self.search(r"data set \$([^$]+)\$", problem)[1])
            mean = Fraction(sum(data), len(data))
            mad = sum(abs(v - mean) for v in data) / len(data)
            self.assertEqual(Fraction(self.search(r"of \$([\d.]+)\$", problem)[1]), mad)
            m = re.search(r"every value is multiplied by \$(\d+)\$", problem)
            expected = mad * int(m[1]) if m else mad
            self.assertEqual(Fraction(solution), expected, problem)


class RangeMissingMaximum(_Base):
    name, variant = "pre_range", "missing_maximum"

    def test(self):
        for problem, solution in self.samples():
            data = ints(self.search(r"data set \$([^$]+)\$", problem)[1])
            r = int(self.search(r"range of \$(\d+)\$", problem)[1])
            x = int(solution)
            self.assertGreater(x, max(data))
            self.assertEqual(max(data + [x]) - min(data + [x]), r, problem)


class ModeFrequencyTable(_Base):
    name, variant = "pre_mode", "frequency_table"

    def test(self):
        for problem, solution in self.samples():
            values, counts = (list(map(int, row)) for row in table_rows(problem))
            top = max(counts)
            self.assertEqual(counts.count(top), 1, problem)
            self.assertEqual(int(solution), values[counts.index(top)], problem)


class IqrBoxPlot(_Base):
    name, variant = "pre_interquartile_range", "box_plot"

    def test(self):
        for problem, solution in self.samples():
            q1, q3 = map(int, self.search(r"box runs from \$(\d+)\$ to \$(\d+)\$", problem).groups())
            self.assertEqual(int(solution), q3 - q1, problem)


class IqrOutlierFence(_Base):
    name, variant = "pre_interquartile_range", "outlier_fence"

    def test(self):
        for problem, solution in self.samples():
            q1, q3 = map(int, self.search(r"\$Q_1 = (\d+)\$ and \$Q_3 = (\d+)\$", problem).groups())
            fence = q3 + Fraction(3, 2) * (q3 - q1)
            expected = min(v for v in range(0, 500) if v > fence)
            self.assertEqual(int(solution), expected, problem)


class IrrationalIntegersBetween(_Base):
    name, variant = "pre_approximate_irrational", "integers_between"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"\\sqrt\{(\d+)\}\$ and \$\\sqrt\{(\d+)\}", problem).groups())
            count = sum(1 for n in range(0, 20) if a < n * n < b)
            self.assertEqual(int(solution), count, problem)


class TrapezoidHeight(_Base):
    name, variant = "pre_area_of_trapezoid", "height_from_area"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"bases of \$(\d+)\$ and \$(\d+)\$ units and an area of \$([\d.]+)\$", problem)
            b1, b2, area = int(m[1]), int(m[2]), Fraction(m[3])
            self.assertEqual(Fraction(b1 + b2, 2) * int(solution), area, problem)


class FdpPercentOfGroup(_Base):
    name, variant = "pre_convert_fdp", "percent_of_group"

    def test(self):
        for problem, solution in self.samples():
            total, part = map(int, self.search(r"Of the \$(\d+)\$ .*?, \$(\d+)\$", problem).groups())
            self.assertTrue(solution.endswith("%"))
            self.assertEqual(Fraction(solution[:-1]), Fraction(100 * part, total), problem)


class ExpressionScaled(_Base):
    name, variant = "pre_evaluate_expression", "scaled_expression"

    @staticmethod
    def _linear(text):
        """(coefficient, constant) of a LaTeX linear expression like '-6x - 3'."""
        m = re.fullmatch(r"(-?\d*)x(?: ([+-]) (\d+))?", text.strip())
        coef = {"": 1, "-": -1}.get(m[1]) if m[1] in ("", "-") else int(m[1])
        const = int(m[3]) * (1 if m[2] == "+" else -1) if m[2] else 0
        return coef, const

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"If \$([^=]+) = " + INT + r"\$, what is the value of \$([^$]+)\$", problem)
            a, b = self._linear(m[1])
            c = int(m[2])
            ka, kb = self._linear(m[3])
            x = Fraction(c - b, a)
            self.assertEqual(Fraction(solution), ka * x + kb, problem)


class DistributiveFactorOut(_Base):
    name, variant = "pre_distributive_property", "factor_out"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(-?\d*)x ([+-]) (\d+) = \\square\((\d*)x ([+-]) (\d+)\)", problem)
            left = (int(m[1] or 1), int(m[3]) * (1 if m[2] == "+" else -1))
            inner = (int(m[4] or 1), int(m[6]) * (1 if m[5] == "+" else -1))
            g = int(solution)
            self.assertEqual((g * inner[0], g * inner[1]), left, problem)


class OrderBetween(_Base):
    name, variant = "pre_order_rational", "between"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"numbers \$([^$]+)\$, which one is greater than \$([^$]+)\$ and less "
                            r"than \$([^$]+)\$", problem)
            values = [Fraction(v.strip()) for v in m[1].split(",")]
            low, high = Fraction(m[2]), Fraction(m[3])
            between = [v for v in values if low < v < high]
            self.assertEqual(len(between), 1, problem)
            self.assertIn(solution, [v.strip() for v in m[1].split(",")])
            self.assertEqual(Fraction(solution), between[0], problem)


class CoordinatePointFromDistance(_Base):
    name, variant = "pre_coordinate_distance", "point_from_distance"
    MOVES = {"above": (0, 1), "below": (0, -1), "to the right of": (1, 0), "to the left of": (-1, 0)}

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d+)\$ units (above|below|to the right of|to the left of) \$\("
                            + INT + ", " + INT, problem)
            d, (dx, dy) = int(m[1]), self.MOVES[m[2]]
            x, y = int(m[3]), int(m[4])
            self.assertEqual(solution, f"({x + d * dx}, {y + d * dy})", problem)


class TwoStepThinkOfANumber(_Base):
    name, variant = "pre_two_step_equation", "think_of_a_number"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"multiply it by \$(\d+)\$, and then (add|subtract) \$(\d+)\$\. The result is \$"
                            + INT, problem)
            a, b = int(m[1]), int(m[3]) * (1 if m[2] == "add" else -1)
            self.assertEqual(a * int(solution) + b, int(m[4]), problem)


class MultiStepInfinitelyMany(_Base):
    name, variant = "pre_multi_step_equation", "infinitely_many"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$" + INT + r"\(x ([+-]) (\d+)\) = (-?\d*)x \+ k\$", problem)
            a = int(m[1])
            b = int(m[3]) * (1 if m[2] == "+" else -1)
            self.assertEqual(int(m[4] if m[4] not in ("", "-") else {"": 1, "-": -1}[m[4]]), a)
            # Identical sides for every x: check a few x values.
            k = int(solution)
            for x in (-3, 0, 5):
                self.assertEqual(a * (x + b), a * x + k, problem)


class BothSidesBreakEven(_Base):
    name, variant = "pre_variables_both_sides", "break_even"

    def test(self):
        for problem, solution in self.samples():
            f1, r1, f2, r2 = ints(problem)[:4]
            months = int(solution)
            self.assertEqual(f1 + r1 * months, f2 + r2 * months, problem)


class PercentOriginalFromNew(_Base):
    name, variant = "pre_percent_change", "original_from_new"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"After a \$(\d+)\\%\$ (increase|decrease), a price is \$(\d+)\$", problem)
            pct, new = int(m[1]), int(m[3])
            factor = Fraction(100 + pct if m[2] == "increase" else 100 - pct, 100)
            self.assertEqual(Fraction(solution) * factor, new, problem)


class DiscountOriginalPrice(_Base):
    name, variant = "pre_discount_tax_tip", "original_price"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"After a \$(\d+)\\%\$ discount, a \w+ costs \$([\d.]+)\$ dollars", problem)
            pct, sale = int(m[1]), Fraction(m[2])
            self.assertRegex(solution, r"^\d+\.\d\d$")
            self.assertEqual(Fraction(solution) * Fraction(100 - pct, 100), sale, problem)


class ProbabilityAtLeastOne(_Base):
    name, variant = "pre_compound_probability", "at_least_one"

    def test(self):
        for problem, solution in self.samples():
            t1, r1, t2, r2 = ints(problem)[:4]
            outcomes = [(a < r1) or (b < r2) for a in range(t1) for b in range(t2)]
            self.assertEqual(frac(solution), Fraction(sum(outcomes), len(outcomes)), problem)


# --- Further variants ---------------------------------------------------------

def signed(sign, magnitude):
    return int(magnitude) * (1 if sign == "+" else -1)


def coef(text):
    """A LaTeX coefficient as an int: '' -> 1, '-' -> -1."""
    return {"": 1, "-": -1}[text] if text in ("", "-") else int(text)


class UnitRateGraph(_Base):
    name, variant = "pre_unit_rate", "graph"

    def test(self):
        for problem, solution in self.samples():
            x, y = map(int, self.search(r"and \$\((\d+), (\d+)\)\$", problem).groups())
            self.assertEqual(Fraction(solution), Fraction(y, x), problem)


class UnitRateComplexFraction(_Base):
    name, variant = "pre_unit_rate", "complex_fraction"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"crawls \$([^$]+)\$ meter in \$([^$]+)\$ hour", problem)
            self.assertEqual(frac(solution), frac(m[1]) / frac(m[2]), problem)


class UnitRateDistanceFromRate(_Base):
    name, variant = "pre_unit_rate", "distance_from_rate"

    def test(self):
        for problem, solution in self.samples():
            rate = int(self.search(r"steady \$(\d+)\$ miles", problem)[1])
            hours = Fraction(self.search(r"in \$([\d.]+)\$ hours", problem)[1])
            self.assertEqual(Fraction(solution), rate * hours, problem)


class UnitRateTable(_Base):
    name, variant = "pre_unit_rate", "table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, row)) for row in table_rows(problem))
            rates = {Fraction(y, x) for x, y in zip(xs, ys)}
            self.assertEqual(rates, {Fraction(solution)}, problem)


class RatioAndDifference(_Base):
    name, variant = "pre_equivalent_ratio", "ratio_and_difference"

    def test(self):
        for problem, solution in self.samples():
            a, b, diff = map(int, self.search(r"\$(\d+):(\d+)\$, and the larger number is \$(\d+)\$",
                                              problem).groups())
            larger = int(solution)
            smaller = larger - diff
            self.assertEqual(Fraction(smaller, larger), Fraction(a, b), problem)


class RatioTable(_Base):
    name, variant = "pre_equivalent_ratio", "ratio_table"

    def test(self):
        for problem, solution in self.samples():
            tops, bottoms = table_rows(problem)
            hole = bottoms.index("?")
            ratios = {Fraction(int(b), int(t)) for t, b in zip(tops, bottoms) if b != "?"}
            self.assertEqual(len(ratios), 1)
            self.assertEqual(Fraction(int(solution), int(tops[hole])), ratios.pop(), problem)


class ProportionUnknownDenominator(_Base):
    name, variant = "pre_solve_proportion", "unknown_denominator"

    def test(self):
        for problem, solution in self.samples():
            a, b, d = map(int, self.search(r"\\frac\{(\d+)\}\{x\} = \\frac\{(\d+)\}\{(\d+)\}", problem).groups())
            self.assertEqual(Fraction(a) / frac(solution), Fraction(b, d), problem)


class ScaleModel(_Base):
    name, variant = "pre_scale_length", "model_scale"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"scale of \$1:(\d+)\$", problem)[1])
            m = re.search(r"The model is \$(\d+)\$ cm long", problem)
            if m:
                self.assertEqual(int(solution), int(m[1]) * n, problem)
            else:
                real = int(self.search(r"The real car is \$(\d+)\$ cm", problem)[1])
                self.assertEqual(int(solution) * n, real, problem)


class IntegersMissingAddend(_Base):
    name, variant = "pre_integer_operations", "missing_addend"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$\(?(-?\d+)\)? \+ \\square = " + INT, problem)
            self.assertEqual(int(m[1]) + int(solution), int(m[2]), problem)


class IntegersNumberLineMoves(_Base):
    name, variant = "pre_integer_operations", "number_line_moves"

    def test(self):
        for problem, solution in self.samples():
            pos = int(self.search(r"Start at \$" + INT, problem)[1])
            for d, way in re.findall(r"\$(\d+)\$ units (right|left)", problem):
                pos += int(d) if way == "right" else -int(d)
            self.assertEqual(int(solution), pos, problem)


class IntegersTemperatureChange(_Base):
    name, variant = "pre_integer_operations", "temperature_change"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"was \$" + INT + r"\^\\circ\$F\. By noon it was \$" + INT, problem)
            if m:
                self.assertEqual(int(solution), int(m[2]) - int(m[1]), problem)
            else:
                m = self.search(r"was \$" + INT + r"\^\\circ\$F\. By midnight it had fallen \$(\d+)\$",
                                problem)
                self.assertEqual(int(solution), int(m[1]) - int(m[2]), problem)


class AbsoluteNegativeFromAbsolute(_Base):
    name, variant = "pre_absolute_value", "negative_from_absolute"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"\$\|x\| = (\d+)\$", problem)[1])
            self.assertEqual([x for x in range(-50, 51) if abs(x) == n and x < 0], [int(solution)])


class AbsoluteOrderOfOperations(_Base):
    name, variant = "pre_absolute_value", "order_of_operations"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"\$\|" + INT + r"\| - \|" + INT + r"\|\$", problem)
            if m:
                expected = abs(int(m[1])) - abs(int(m[2]))
            else:
                m = self.search(r"\$\|" + INT + " - " + INT + r"\|\$", problem)
                expected = abs(int(m[1]) - int(m[2]))
            self.assertEqual(int(solution), expected, problem)


class InequalityFromNumberLine(_Base):
    name, variant = "pre_one_step_inequality", "from_number_line"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"(closed|open) circle at \$" + INT + r"\$ with the line shaded to the (left|right)",
                            problem)
            op = {("closed", "left"): "<=", ("open", "left"): "<",
                  ("closed", "right"): ">=", ("open", "right"): ">"}[(m[1], m[3])]
            self.assertEqual(solution, f"x {op} {m[2]}", problem)


class MultiStepCountPositive(_Base):
    name, variant = "pre_multi_step_inequality", "count_positive_integers"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d+)x ([+-]) (\d+) (<|\\leq) " + INT, problem)
            a, b, op, c = int(m[1]), signed(m[2], m[3]), m[4], int(m[5])
            count = sum(1 for x in range(1, 500) if (a * x + b < c if op == "<" else a * x + b <= c))
            self.assertEqual(int(solution), count, problem)


class SciNormalize(_Base):
    name, variant = "pre_scientific_notation_ops", "normalize"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"Write \$([\d.]+) \\times 10\^\{" + INT + r"\}\$", problem)
            value = Fraction(m[1]) * Fraction(10) ** int(m[2])
            sm = re.fullmatch(r"(\d\.\d+)\*10\^(-?\d+)", solution)
            self.assertIsNotNone(sm, solution)
            self.assertTrue(1 <= Fraction(sm[1]) < 10)
            self.assertEqual(Fraction(sm[1]) * Fraction(10) ** int(sm[2]), value, problem)


class ExponentsMissingInner(_Base):
    name, variant = "pre_integer_exponent_rules", "missing_inner_exponent"

    def test(self):
        for problem, solution in self.samples():
            m, n, t = map(int, self.search(r"\^\{(\d+)\} \\cdot a\^\{(\d+)\} = a\^\{(\d+)\}", problem).groups())
            self.assertEqual(int(solution) * m + n, t, problem)


class ExponentsEvaluateWithNegative(_Base):
    name, variant = "pre_integer_exponent_rules", "evaluate_with_negative"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"\$(\d+)\^\{" + INT + r"\} \\cdot \d+\^\{" + INT + r"\}\$", problem)
            if m:
                expected = Fraction(int(m[1])) ** (int(m[2]) + int(m[3]))
            else:
                m = self.search(r"\\frac\{(\d+)\^\{" + INT + r"\}\}\{\d+\^\{" + INT + r"\}\}", problem)
                expected = Fraction(int(m[1])) ** (int(m[2]) - int(m[3]))
            self.assertEqual(frac(solution), expected, problem)


class ProportionalityGraph(_Base):
    name, variant = "pre_constant_of_proportionality", "graph"

    def test(self):
        for problem, solution in self.samples():
            x, y = map(int, self.search(r"and \$\((\d+), (\d+)\)\$", problem).groups())
            self.assertEqual(frac(solution), Fraction(y, x), problem)


class ProportionalityReverse(_Base):
    name, variant = "pre_constant_of_proportionality", "reverse"

    def test(self):
        for problem, solution in self.samples():
            k, y = map(int, self.search(r"\$y = (\d+)x\$\. What is \$x\$ when \$y = (\d+)\$", problem).groups())
            self.assertEqual(k * int(solution), y, problem)


class EvaluateFunctionReverse(_Base):
    name, variant = "pre_evaluate_function", "input_from_output"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$f\(x\) = (-?\d*)x ([+-]) (\d+)\$, for what value of \$x\$ is \$f\(x\) = "
                            + INT, problem)
            self.assertEqual(coef(m[1]) * int(solution) + signed(m[2], m[3]), int(m[4]), problem)


class EvaluateFunctionContext(_Base):
    name, variant = "pre_evaluate_function", "context"

    def test(self):
        for problem, solution in self.samples():
            rate, fee, n = map(int, self.search(r"\$C\(h\) = (\d+)h \+ (\d+)\$.*a \$(\d+)\$-hour",
                                                problem).groups())
            self.assertEqual(int(solution), rate * n + fee, problem)


class SlopeTable(_Base):
    name, variant = "pre_slope_from_two_points", "table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, row)) for row in table_rows(problem))
            slopes = {Fraction(ys[i + 1] - ys[i], xs[i + 1] - xs[i]) for i in range(len(xs) - 1)}
            self.assertEqual(slopes, {frac(solution)}, problem)


class SlopeRiseOverRun(_Base):
    name, variant = "pre_slope_from_two_points", "rise_over_run"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"(rises|falls) \$(\d+)\$ units for every \$(\d+)\$", problem)
            rise = int(m[2]) * (1 if m[1] == "rises" else -1)
            self.assertEqual(frac(solution), Fraction(rise, int(m[3])), problem)


class LinearTablePredict(_Base):
    name, variant = "pre_linear_function_value", "table_predict"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, row)) for row in table_rows(problem))
            slope = Fraction(ys[1] - ys[0], xs[1] - xs[0])
            b = ys[0] - slope * xs[0]
            target = int(self.search(r"when \$x = (\d+)\$", problem)[1])
            self.assertEqual(int(solution), slope * target + b, problem)


class LinearTaxiFare(_Base):
    name, variant = "pre_linear_function_value", "taxi_fare"

    def test(self):
        for problem, solution in self.samples():
            base, rate, miles = self.search(r"charges \$([\d.]+)\$ dollars plus \$([\d.]+)\$ dollars per "
                                            r"mile\. What does a \$(\d+)\$", problem).groups()
            self.assertEqual(Fraction(solution), Fraction(base) + Fraction(rate) * int(miles), problem)


def parse_line(solution):
    """(m, b) of a typed ``y = mx + b`` solution."""
    sm = re.fullmatch(r"y = (-?[\d/]*)x(?: ([+-]) ([\d/]+))?", solution)
    assert sm, solution
    slope = Fraction({"": "1", "-": "-1"}.get(sm[1], sm[1]))
    b = Fraction(sm[3]) * (1 if sm[2] == "+" else -1) if sm[2] else Fraction(0)
    return slope, b


class LineFromTable(_Base):
    name, variant = "pre_line_from_slope_point", "table"

    def test(self):
        for problem, solution in self.samples():
            xs, ys = (list(map(int, row)) for row in table_rows(problem))
            slope, b = parse_line(solution)
            for x, y in zip(xs, ys):
                self.assertEqual(slope * x + b, y, problem)


class LineFromContext(_Base):
    name, variant = "pre_line_from_slope_point", "context"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"holds \$(\d+)\$ liters of water and (is filled|drains) at \$(\d+)\$", problem)
            rate = int(m[3]) * (1 if m[2] == "is filled" else -1)
            self.assertEqual(parse_line(solution), (rate, int(m[1])), problem)


class SlopeInterceptInterceptOnly(_Base):
    name, variant = "pre_slope_intercept_form", "intercept_only"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"the (x|y)-intercept of the line \$([^$]+)\$", problem)
            A, B, C = parse_xy(m[2])
            expected = Fraction(C, A) if m[1] == "x" else Fraction(C, B)
            self.assertEqual(frac(solution), expected, problem)


class SystemCountFromDescriptions(_Base):
    name, variant = "pre_system_solution_count", "from_descriptions"

    def test(self):
        for problem, solution in self.samples():
            m1, b1, m2, b2 = map(int, self.search(r"slope \$" + INT + r"\$ and y-intercept \$" + INT
                                                  + r"\$\. Line 2 has slope \$" + INT
                                                  + r"\$ and y-intercept \$" + INT, problem).groups())
            expected = "one" if m1 != m2 else ("infinite" if b1 == b2 else "none")
            self.assertEqual(solution, expected, problem)


class SystemInfinitelyManyParameter(_Base):
    name, variant = "pre_system_solution_count", "infinitely_many_parameter"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"system \$([^$]+)\$ and \$(-?\d*)x ([+-]) (\d*)y = k\$", problem)
            a1, b1, c1 = parse_xy(m[1])
            a2, b2 = coef(m[2]), signed(m[3], m[4] or 1)
            k = int(solution)
            # Same line: (a2, b2, k) is a multiple of (a1, b1, c1).
            self.assertEqual(a1 * b2, a2 * b1)
            self.assertEqual(Fraction(a2, a1) * c1, k, problem)


class MadCompareClasses(_Base):
    name, variant = "pre_mean_absolute_deviation", "compare_classes"

    def test(self):
        for problem, solution in self.samples():
            a = ints(self.search(r"Class A's quiz scores are \$([^$]+)\$", problem)[1])
            b = ints(self.search(r"Class B's are \$([^$]+)\$", problem)[1])

            def mad(d):
                mean = Fraction(sum(d), len(d))
                return sum(abs(v - mean) for v in d) / len(d)
            self.assertNotEqual(mad(a), mad(b))
            self.assertEqual(Fraction(solution), max(mad(a), mad(b)), problem)


class RangeAfterTransformation(_Base):
    name, variant = "pre_range", "after_transformation"

    def test(self):
        for problem, solution in self.samples():
            data = ints(self.search(r"data set \$([^$]+)\$", problem)[1])
            add = re.search(r"If \$(\d+)\$ is added", problem)
            new = [v + int(add[1]) for v in data] if add else \
                [v * int(self.search(r"multiplied by \$(\d+)\$", problem)[1]) for v in data]
            self.assertEqual(int(solution), max(new) - min(new), problem)


class RangeFrequencyTable(_Base):
    name, variant = "pre_range", "frequency_table"

    def test(self):
        for problem, solution in self.samples():
            values, counts = (list(map(int, row)) for row in table_rows(problem))
            data = [v for v, c in zip(values, counts) for _ in range(c)]
            self.assertEqual(int(solution), max(data) - min(data), problem)


class IrrationalBetweenIntegers(_Base):
    name, variant = "pre_approximate_irrational", "between_integers"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"\\sqrt\{(\d+)\}", problem)[1])
            lo = int(solution)
            self.assertTrue(lo * lo < n < (lo + 1) ** 2, problem)


class IrrationalLargestBelow(_Base):
    name, variant = "pre_approximate_irrational", "largest_below"

    def test(self):
        for problem, solution in self.samples():
            bound = Fraction(self.search(r"\\sqrt\{n\} < ([\d.]+)\$", problem)[1])
            ok = [n for n in range(0, 200) if n < bound * bound]
            self.assertEqual(int(solution), max(ok), problem)


class TrapezoidFromVertices(_Base):
    name, variant = "pre_area_of_trapezoid", "from_vertices"

    def test(self):
        for problem, solution in self.samples():
            pts = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            self.assertEqual(len(pts), 4)
            shoelace = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])))
            self.assertEqual(Fraction(solution), Fraction(shoelace, 2), problem)


class CoordinateReflectionDistance(_Base):
    name, variant = "pre_coordinate_distance", "reflection_distance"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"point \$\(" + INT + ", " + INT + r"\)\$ is reflected over the (x|y)-axis", problem)
            x, y = int(m[1]), int(m[2])
            image = (x, -y) if m[3] == "x" else (-x, y)
            self.assertEqual(int(solution), math.dist((x, y), image), problem)


class FdpRepeatingDecimal(_Base):
    name, variant = "pre_convert_fdp", "repeating_decimal"

    def test(self):
        for problem, solution in self.samples():
            block = self.search(r"0\.\\overline\{(\d+)\}", problem)[1]
            value = Fraction(int(block), 10 ** len(block) - 1)
            self.assertEqual(frac(solution), value, problem)
            self.assertEqual(solution, f"{value.numerator}/{value.denominator}")


class FdpPercentBeyond(_Base):
    name, variant = "pre_convert_fdp", "percent_beyond"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"the decimal \$([\d.]+)\$ to a percent", problem)
            if m:
                self.assertEqual(Fraction(solution.rstrip("%")), Fraction(m[1]) * 100, problem)
            else:
                pct = Fraction(self.search(r"Convert \$([\d.]+)\\%\$", problem)[1])
                self.assertEqual(Fraction(solution), pct / 100, problem)


class ExpressionTwoVariables(_Base):
    name, variant = "pre_evaluate_expression", "two_variables"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"Evaluate \$(-?\d*)x ([+-]) (\d*)y(?: ([+-]) (\d+))?\$ when \$x = " + INT
                            + r"\$ and \$y = " + INT, problem)
            a, b = coef(m[1]), signed(m[2], m[3] or 1)
            c = signed(m[4], m[5]) if m[4] else 0
            x, y = int(m[6]), int(m[7])
            self.assertEqual(int(solution), a * x + b * y + c, problem)


class DistributiveMissingInner(_Base):
    name, variant = "pre_distributive_property", "missing_inner"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$(\d+)\((\d*)x \+ \\square\) = (\d*)x ([+-]) (\d+)\$", problem)
            a, b, ab, const = int(m[1]), coef(m[2]), coef(m[3]), signed(m[4], m[5])
            self.assertEqual(a * b, ab)
            self.assertEqual(a * int(solution), const, problem)


class DistributiveMentalMath(_Base):
    name, variant = "pre_distributive_property", "mental_math"

    def test(self):
        for problem, solution in self.samples():
            a, n = map(int, self.search(r"find \$(\d+) \\times (\d+)\$", problem).groups())
            self.assertEqual(int(solution), a * n, problem)


class OrderExtreme(_Base):
    name, variant = "pre_order_rational", "extreme"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"is the (least|greatest|closest to 0): \$([^$]+)\$", problem)
            shown = [v.strip() for v in m[2].split(",")]
            values = [Fraction(v) for v in shown]
            if m[1] == "least":
                want = min(values)
            elif m[1] == "greatest":
                want = max(values)
            else:
                best = min(abs(v) for v in values)
                closest = [v for v in values if abs(v) == best]
                self.assertEqual(len(closest), 1, problem)
                want = closest[0]
            self.assertIn(solution, shown)
            self.assertEqual(Fraction(solution), want, problem)


class TwoStepFractionCoefficient(_Base):
    name, variant = "pre_two_step_equation", "fraction_coefficient"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\\frac\{x\}\{(\d+)\} ([+-]) (\d+) = " + INT, problem)
            a, b, c = int(m[1]), signed(m[2], m[3]), int(m[4])
            self.assertEqual(Fraction(int(solution), a) + b, c, problem)


class MultiStepConsecutive(_Base):
    name, variant = "pre_multi_step_equation", "consecutive_integers"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"The sum of (\d) (consecutive(?: even| odd)?) integers is \$" + INT, problem)
            count, kind, total = int(m[1]), m[2], int(m[3])
            gap = 1 if kind == "consecutive" else 2
            starts = [n for n in range(-200, 200)
                      if sum(n + gap * i for i in range(count)) == total
                      and (kind != "consecutive even" or n % 2 == 0)
                      and (kind != "consecutive odd" or n % 2 == 1)]
            self.assertEqual(len(starts), 1, problem)
            self.assertEqual(int(solution), starts[0] + gap * (count - 1), problem)


class BothSidesNoSolution(_Base):
    name, variant = "pre_variables_both_sides", "no_solution_parameter"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$ax ([+-]) (\d+) = (-?\d*)x ([+-]) (\d+)\$", problem)
            b, c, d = signed(m[1], m[2]), coef(m[3]), signed(m[4], m[5])
            no_solution = [a for a in range(-20, 21)
                           if not any(a * x + b == c * x + d for x in range(-500, 501))
                           and a == c]
            self.assertEqual(no_solution, [int(solution)], problem)


class BothSidesExpressionValue(_Base):
    name, variant = "pre_variables_both_sides", "expression_value"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"If \$(-?\d*)x ([+-]) (\d+) = (-?\d*)x ([+-]) (\d+)\$, what is the value of "
                            r"\$x ([+-]) (\d+)\$", problem)
            a, b, c, d = coef(m[1]), signed(m[2], m[3]), coef(m[4]), signed(m[5], m[6])
            k = signed(m[7], m[8])
            x = Fraction(d - b, a - c)
            self.assertEqual(int(solution), x + k, problem)


def cents_half_up(value):
    return math.floor(value * 100 + Fraction(1, 2))


class DiscountThenTax(_Base):
    name, variant = "pre_discount_tax_tip", "discount_then_tax"

    def test(self):
        for problem, solution in self.samples():
            price, off, tax = map(int, self.search(r"\$(\d+)\$-dollar item is on sale for \$(\d+)\\%\$ off, "
                                                   r"and then a \$(\d+)\\%\$", problem).groups())
            final = Fraction(price) * Fraction(100 - off, 100) * Fraction(100 + tax, 100)
            self.assertEqual(round(Fraction(solution) * 100), cents_half_up(final), problem)


class DiscountBetterCoupon(_Base):
    name, variant = "pre_discount_tax_tip", "better_coupon"

    def test(self):
        for problem, solution in self.samples():
            price, pct, off = map(int, self.search(r"costs \$(\d+)\$ dollars\. Coupon A takes \$(\d+)\\%\$ off; "
                                                   r"coupon B takes \$(\d+)\$", problem).groups())
            a, b = Fraction(price * (100 - pct), 100), Fraction(price - off)
            self.assertNotEqual(a, b)
            self.assertEqual(Fraction(solution), min(a, b), problem)


class DiscountSuccessive(_Base):
    name, variant = "pre_discount_tax_tip", "successive_discounts"

    def test(self):
        for problem, solution in self.samples():
            price, p1, p2 = map(int, self.search(r"\$(\d+)\$-dollar coat is marked \$(\d+)\\%\$ off\. At the "
                                                 r"register, another \$(\d+)\\%\$", problem).groups())
            final = Fraction(price * (100 - p1) * (100 - p2), 10000)
            self.assertEqual(round(Fraction(solution) * 100), cents_half_up(final), problem)


class ProbabilityWithoutReplacement(_Base):
    name, variant = "pre_compound_probability", "without_replacement"

    def test(self):
        for problem, solution in self.samples():
            total, red = map(int, self.search(r"has \$(\d+)\$ marbles, \$(\d+)\$ of them red", problem).groups())
            draws = [(i, j) for i in range(total) for j in range(total) if i != j]
            both = sum(1 for i, j in draws if i < red and j < red)
            self.assertEqual(frac(solution), Fraction(both, len(draws)), problem)


class ProbabilityMissing(_Base):
    name, variant = "pre_compound_probability", "missing_probability"

    def test(self):
        for problem, solution in self.samples():
            pa = frac(self.search(r"\$P\(A\) = ([\d/]+)\$", problem)[1])
            both = frac(self.search(r"B\) = ([\d/]+)\$", problem)[1])
            self.assertEqual(pa * frac(solution), both, problem)


class ProbabilitySampleSpace(_Base):
    name, variant = "pre_compound_probability", "sample_space"
    SIZES = {"a coin is flipped": 2, "a number cube is rolled": 6,
             "a spinner with 4 equal sections is spun": 4,
             "a letter is picked from A, B, and C": 3,
             "a card is drawn from cards numbered 1 to 5": 5}

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"First (.+?), then (.+?)\. How many", problem)
            self.assertEqual(int(solution), self.SIZES[m[1]] * self.SIZES[m[2]], problem)
