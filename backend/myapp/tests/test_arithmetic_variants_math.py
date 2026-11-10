"""Math-correctness tests for the arithmetic variants (arithmetic_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently (directly or by brute force), and checks the served solution,
over 2000 seeded samples.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators import arithmetic_variants  # noqa: F401 - attaches the variants
from myapp.generators._format import num

SAMPLES = 2000


def _ints(text):
    return [int(v) for v in re.findall(r"-?\d+", text)]


def _ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _is_prime(n):
    return n > 1 and all(n % d for d in range(2, math.isqrt(n) + 1))


def _clock(total_minutes):
    h, m = divmod(total_minutes % 720, 60)
    return f"{h or 12}:{m:02d}"


def _parse_clock(text):
    h, m = map(int, text.split(":"))
    return (h % 12) * 60 + m


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
        return [int(g) if g is not None and re.fullmatch(r"-?\d+", g) else g for g in m.groups()]

    def check(self, pattern, compute, positive=True):
        for problem, solution in self.samples():
            want = compute(*self.search(pattern, problem))
            self.assertEqual(solution, str(want), problem)
            if positive:
                self.assertGreaterEqual(int(solution), 0, problem)


# --- Arithmetic facts --------------------------------------------------------------------------

class AdditionMissingAddend(_Base):
    name, variant = "addition", "missing_addend"

    def test(self):
        self.check(r"\$(\d+) \+ \\square = (\d+)\$", lambda a, t: t - a)


class AdditionMakeATen(_Base):
    name, variant = "addition", "make_a_ten"

    def test(self):
        def compute(a, b, c):
            self.assertEqual(c % 10, 0)
            return a + b - c
        self.check(r"\$(\d+) \+ (\d+) = (\d+) \+ \\square\$", compute)


class AdditionStartUnknown(_Base):
    name, variant = "addition", "start_unknown"

    def test(self):
        self.check(r"Then \$(\d+)\$ more came\. Now there are \$(\d+)\$", lambda more, total: total - more)


class SubtractionConstantDifference(_Base):
    name, variant = "subtraction", "constant_difference"

    def test(self):
        self.check(r"\$(\d+) - (\d+) = (\d+) - \\square\$", lambda a, b, c: c - (a - b))


class SubtractionCompare(_Base):
    name, variant = "subtraction", "compare_story"

    def test(self):
        def compute(big, small):
            self.assertGreater(big, small)
            return big - small
        self.check(r"Ann has \$(\d+)\$ stickers and Ben has \$(\d+)\$", compute)


class MultiplicationSplit(_Base):
    name, variant = "multiplication", "distributive_split"

    def test(self):
        def compute(a, b, a2):
            self.assertEqual(a, a2)
            return b - 10  # a*b = a*10 + a*x  =>  x = b - 10
        self.check(r"\$(\d+) \\times (\d+) = (\d+) \\times 10 \+ \d+ \\times \\square\$", compute)


class MultiplicationDoubling(_Base):
    name, variant = "multiplication", "doubling"

    def test(self):
        def compute(a, b, p, a2, b2):
            self.assertEqual((a * b, a2, b2), (p, 2 * a, b))
            return a2 * b2
        self.check(r"If \$(\d+) \\times (\d+) = (\d+)\$, what is \$(\d+) \\times (\d+)\$", compute)


class DivisionInterpretRemainder(_Base):
    name, variant = "division", "interpret_remainder"

    def test(self):
        for problem, solution in self.samples():
            total, per = _ints(problem)[:2]
            self.assertNotEqual(total % per, 0, problem)
            if "vans are needed" in problem:
                want = -(-total // per)
            elif "completely filled" in problem:
                want = total // per
            else:
                self.assertIn("left over", problem)
                want = total % per
            self.assertEqual(solution, str(want), problem)


class DivisionFactFamily(_Base):
    name, variant = "division", "fact_family"

    def test(self):
        def compute(a, b, p, p2, q):
            self.assertEqual((a * b, p2, q), (p, p, a))
            return p // q
        self.check(r"\$(\d+) \\times (\d+) = (\d+)\$\. Fill in the box: \$(\d+) \\div \\square = (\d+)\$", compute)


class AbsoluteDifferenceNumberLine(_Base):
    name, variant = "absolute_difference", "number_line"

    def test(self):
        for problem, solution in self.samples():
            a, b = [int(v) for v in re.findall(r"\$(-?\d+)(?:\^\\circ)?\$", problem)]
            self.assertEqual(solution, str(abs(b - a)), problem)


class ExponentMissing(_Base):
    name, variant = "exponentiation", "missing_exponent"

    def test(self):
        def compute(b, v):
            e = next(e for e in range(1, 40) if b ** e >= v)
            self.assertEqual(b ** e, v)
            return e
        self.check(r"\$(\d+)\^\{\\square\} = (\d+)\$", compute)


class ExponentVsProduct(_Base):
    name, variant = "exponentiation", "power_vs_product"

    def test(self):
        self.check(r"\$(\d+)\^\{(\d+)\}\$ than \$\d+ \\times \d+\$", lambda b, e: b ** e - b * e)


class SquareSignOrder(_Base):
    name, variant = "square", "sign_and_order"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"Evaluate \$(\(-(\d+)\)|-(\d+))\^2\$", problem)
            self.assertIsNotNone(m, problem)
            want = int(m.group(2)) ** 2 if m.group(2) else -int(m.group(3)) ** 2
            self.assertEqual(solution, str(want), problem)


class SquareConsecutive(_Base):
    name, variant = "square", "consecutive_squares"

    def test(self):
        self.check(r"\$(\d+)\^2 = (\d+)\^2 \+ \\square\$", lambda a, b: a * a - b * b)


class SquareRootDontAdd(_Base):
    name, variant = "square_root", "roots_dont_add"

    def test(self):
        def compute(p, q, p2, q2):
            self.assertEqual((p, q), (p2, q2))
            roots = [math.isqrt(v) for v in (p, q, p + q)]
            self.assertEqual([r * r for r in roots], [p, q, p + q])
            return roots[0] + roots[1] - roots[2]
        self.check(r"\\sqrt\{(\d+)\} \+ \\sqrt\{(\d+)\} - \\sqrt\{(\d+) \+ (\d+)\}", compute)


class SquareRootSide(_Base):
    name, variant = "square_root", "side_of_square"

    def test(self):
        def compute(area):
            r = math.isqrt(area)
            self.assertEqual(r * r, area)
            return r
        self.check(r"area of \$(\d+)\$", compute)


class CubeRootEdge(_Base):
    name, variant = "cube_root", "cube_edge"

    def test(self):
        for problem, solution in self.samples():
            v = _ints(problem)[0]
            if "cube has a volume" not in problem:
                self.assertIn(r"\sqrt[3]", problem)
                v = _ints(problem.split(r"\sqrt[3]")[1])[0]
            r = round(abs(v) ** (1 / 3))
            self.assertEqual(r ** 3, abs(v), problem)
            self.assertEqual(solution, str(r if v > 0 else -r), problem)


class LcmBuses(_Base):
    name, variant = "lcm", "buses"

    def test(self):
        def compute(a, b):
            self.assertNotEqual(a, b)
            return next(t for t in range(1, a * b + 1) if t % a == 0 and t % b == 0)
        self.check(r"every \$(\d+)\$ minutes and bus B every \$(\d+)\$", compute)


class LcmSmallestOver(_Base):
    name, variant = "lcm", "smallest_over"

    def test(self):
        self.check(
            r"greater than \$(\d+)\$ that is divisible by both \$(\d+)\$ and \$(\d+)\$",
            lambda n, a, b: next(k for k in range(n + 1, n + a * b + 2) if k % a == 0 and k % b == 0),
        )


class GcdBouquets(_Base):
    name, variant = "greatest_common_divisor", "bouquets"

    def test(self):
        def compute(a, b):
            want = max(g for g in range(1, min(a, b) + 1) if a % g == 0 and b % g == 0)
            self.assertGreater(want, 1)
            return want
        self.check(r"has \$(\d+)\$ roses and \$(\d+)\$ tulips", compute)


class PrimeFactorsSquare(_Base):
    name, variant = "prime_factors", "perfect_square_multiplier"

    def test(self):
        self.check(r"multiply \$(\d+)\$ by", lambda n: next(k for k in range(1, n + 1) if math.isqrt(k * n) ** 2 == k * n))


class PrimeFactorsReverse(_Base):
    name, variant = "prime_factors", "from_factorization"

    def test(self):
        for problem, solution in self.samples():
            tex = re.search(r"factorization \$(.+)\$\?", problem).group(1)
            value = 1
            for part in tex.split(r" \cdot "):
                m = re.fullmatch(r"(\d+)(?:\^\{(\d+)\})?", part)
                self.assertIsNotNone(m, problem)
                p, e = int(m.group(1)), int(m.group(2) or 1)
                self.assertTrue(_is_prime(p), problem)
                value *= p ** e
            self.assertEqual(solution, str(value), problem)


class IsPrimeNext(_Base):
    name, variant = "is_prime", "next_prime"

    def test(self):
        self.check(r"greater than \$(\d+)\$", lambda n: next(p for p in range(n + 1, 2 * n + 2) if _is_prime(p)))


class IsCompositeCount(_Base):
    name, variant = "is_composite", "count_composites"

    def test(self):
        self.check(
            r"from \$(\d+)\$ to \$(\d+)\$",
            lambda lo, hi: sum(1 for n in range(lo, hi + 1) if n > 1 and not _is_prime(n)),
        )


class CompareFractionsBetween(_Base):
    name, variant = "compare_fractions", "fraction_between"

    def test(self):
        pattern = r"\\frac\{(\d+)\}\{(\d+)\} < \\frac\{n\}\{(\d+)\} < \\frac\{(\d+)\}\{(\d+)\}"
        for problem, solution in self.samples():
            a, b, d, c, e = self.search(pattern, problem)
            fits = [n for n in range(0, 10 * d) if Fraction(a, b) < Fraction(n, d) < Fraction(c, e)]
            self.assertEqual(len(fits), 1, problem)
            self.assertEqual(solution, str(fits[0]), problem)


class CompareFractionsGreater(_Base):
    name, variant = "compare_fractions", "greater_fraction"

    def test(self):
        def compute(a, b, c, d):
            big = max(Fraction(a, b), Fraction(c, d))
            self.assertNotEqual(Fraction(a, b), Fraction(c, d))
            return f"{big.numerator}/{big.denominator}"
        self.check(r"greater, \$(\d+)/(\d+)\$ or \$(\d+)/(\d+)\$", compute, positive=False)


class FactorialQuotient(_Base):
    name, variant = "factorial", "quotient"

    def test(self):
        self.check(r"\\frac\{(\d+)!\}\{(\d+)!\}", lambda n, m: math.factorial(n) // math.factorial(m))


class FactorialArrangements(_Base):
    name, variant = "factorial", "arrangements"

    def test(self):
        for problem, solution in self.samples():
            if "What is $n$" in problem:
                ways = _ints(problem.split("in $")[1])[0]
                want = next(n for n in range(1, 20) if math.factorial(n) == ways)
            else:
                want = math.factorial(_ints(problem)[0])
            self.assertEqual(solution, str(want), problem)


# --- Grades 1-5 --------------------------------------------------------------------------------

class PlaceValueRegrouping(_Base):
    name, variant = "arith_place_value", "unusual_regrouping"

    def test(self):
        self.check(
            r"\$(\d+)\$ thousands, \$(\d+)\$ hundreds, \$(\d+)\$ tens, and \$(\d+)\$ ones",
            lambda th, h, t, o: th * 1000 + h * 100 + t * 10 + o,
        )


class PlaceValueRatio(_Base):
    name, variant = "arith_place_value", "digit_value_ratio"

    def test(self):
        def compute(number, d):
            digits = str(number)
            pos = [i for i, ch in enumerate(digits) if ch == str(d)]
            self.assertEqual(len(pos), 2, number)
            first = d * 10 ** (len(digits) - 1 - pos[0])
            second = d * 10 ** (len(digits) - 1 - pos[1])
            return first // second
        self.check(r"In \$(\d+)\$, the first \$(\d)\$", compute)


class RoundingReverse(_Base):
    name, variant = "arith_rounding", "smallest_that_rounds"

    def test(self):
        places = {"ten": 10, "hundred": 100, "thousand": 1000}
        pattern = r"rounds to \$(\d+)\$ when rounded to the nearest (ten|hundred|thousand)\. What is the (smallest|largest)"
        for problem, solution in self.samples():
            target, place, which = self.search(pattern, problem)
            p = places[place]
            ok = [n for n in range(target - p, target + p) if (n + p // 2) // p * p == target]
            self.assertEqual(solution, str(min(ok) if which == "smallest" else max(ok)), problem)


class RoundingEstimate(_Base):
    name, variant = "arith_rounding", "estimate_sum"

    def test(self):
        self.check(r"Estimate \$(\d+) \+ (\d+)\$", lambda a, b: (a + 50) // 100 * 100 + (b + 50) // 100 * 100)


class _MissingNumerator:
    """Shared by the two fraction-addition topics."""
    variant = "missing_numerator"

    def test(self):
        pattern = r"\\frac\{(\d+)\}\{(\d+)\} \+ \\frac\{\\square\}\{(\d+)\} = \\frac\{(\d+)\}\{(\d+)\}"
        for problem, solution in self.samples():
            a, b, d, t, d2 = self.search(pattern, problem)
            self.assertEqual(d, d2)
            n = (Fraction(t, d) - Fraction(a, b)) * d
            self.assertEqual(n.denominator, 1, problem)
            self.assertGreater(n, 0, problem)
            self.assertEqual(solution, str(n), problem)


class AddFractionsMissingNumerator(_MissingNumerator, _Base):
    name = "arith_add_fractions"


class AddUnlikeFractionsMissingNumerator(_MissingNumerator, _Base):
    name = "arith_add_unlike_fractions"


class SubtractFractionsToMakeOne(_Base):
    name, variant = "arith_subtract_fractions", "to_make_one"

    def test(self):
        def compute(n, d):
            self.assertEqual(math.gcd(n, d), 1)
            f = 1 - Fraction(n, d)
            return f"{f.numerator}/{f.denominator}" if f.denominator > 1 else f"{f.numerator}"
        self.check(r"added to \$(\d+)/(\d+)\$", compute, positive=False)


class CompareDecimalsMisconception(_Base):
    name, variant = "arith_compare_decimals", "longer_is_not_bigger"

    def test(self):
        for problem, solution in self.samples():
            x, y = re.search(r"greater, \$(\d\.\d)\$ or \$(\d\.\d\d)\$", problem).groups()
            self.assertEqual(solution, max(x, y, key=Fraction), problem)


class AddDecimalsMissing(_Base):
    name, variant = "arith_add_decimals", "missing_addend"

    def test(self):
        for problem, solution in self.samples():
            a, t = re.search(r"\$([\d.]+) \+ \\square = ([\d.]+)\$", problem).groups()
            self.assertEqual(Fraction(solution), Fraction(t) - Fraction(a), problem)
            self.assertEqual(solution, num(Fraction(solution)), problem)


class SubtractDecimalsChange(_Base):
    name, variant = "arith_subtract_decimals", "change_from_twenty"

    def test(self):
        for problem, solution in self.samples():
            p1, p2 = re.findall(r"\$(\d+\.\d+)\$", problem)
            want = 20 - Fraction(p1) - Fraction(p2)
            self.assertGreater(want, 0, problem)
            self.assertEqual(Fraction(solution), want, problem)


class MultiplyDecimalsFromWhole(_Base):
    name, variant = "arith_multiply_decimals", "place_value_from_whole"

    def test(self):
        pattern = r"\$(\d+) \\times (\d+) = (\d+)\$, what is \$([\d.]+) \\times ([\d.]+)\$"
        for problem, solution in self.samples():
            a, b, p, x, y = re.search(pattern, problem).groups()
            self.assertEqual(int(a) * int(b), int(p), problem)
            self.assertEqual(Fraction(solution), Fraction(x) * Fraction(y), problem)  # exact, not rounded


class DivideDecimalsFromWhole(_Base):
    name, variant = "arith_divide_decimals", "place_value_from_whole"

    def test(self):
        for problem, solution in self.samples():
            x, y = re.search(r"what is \$([\d.]+) \\div ([\d.]+)\$", problem).groups()
            self.assertEqual(Fraction(solution), Fraction(x) / Fraction(y), problem)


class OrderLargestValue(_Base):
    name, variant = "arith_order_of_operations", "largest_value"

    def test(self):
        def compute(a, b, c):
            return max(eval(f"{a}{o1}{b}{o2}{c}") for o1, o2 in (("+", "*"), ("*", "+")))
        self.check(r"\$(\d+) \\,\\square\\, (\d+) \\,\\square\\, (\d+)\$", compute)


class OrderMissingNumber(_Base):
    name, variant = "arith_order_of_operations", "missing_number"

    def test(self):
        self.check(
            r"\$(\d+) \+ \\square \\times (\d+) = (\d+)\$",
            lambda a, b, t: next(k for k in range(0, t + 1) if a + k * b == t),
        )


class NthMultipleReverse(_Base):
    name, variant = "arith_nth_multiple", "which_multiple"

    def test(self):
        for problem, solution in self.samples():
            if "How many multiples" in problem:
                b, top = self.search(r"multiples of \$(\d+)\$ are there from \$1\$ to \$(\d+)\$", problem)
                want = sum(1 for k in range(1, top + 1) if k % b == 0)
            else:
                n, b = self.search(r"\$(\d+)\$ is which multiple of \$(\d+)\$", problem)
                want = n // b
                self.assertEqual(want * b, n)
            self.assertEqual(solution, str(want), problem)


class PowersOfTenReverse(_Base):
    name, variant = "arith_powers_of_ten", "missing_exponent"

    def test(self):
        self.check(
            r"\$(\d+) \\times 10\^\{\\square\} = (\d+)\$",
            lambda n, v: next(k for k in range(0, 10) if n * 10 ** k == v),
        )


class LengthPieces(_Base):
    name, variant = "arith_length_conversion", "pieces"

    def test(self):
        self.check(r"\$(\d+)\$ feet long\. How many \$(\d+)\$-inch", lambda ft, p: ft * 12 // p)


class MetricBatches(_Base):
    name, variant = "arith_metric_unit_conversion", "batches"

    def test(self):
        self.check(r"needs \$(\d+)\$ mL.* from \$(\d+)\$ L", lambda per, liters: liters * 1000 // per)


class MinutesReverse(_Base):
    name, variant = "arith_minutes_to_hours", "to_minutes"

    def test(self):
        self.check(r"\$(\d+)\$ hr \$(\d+)\$ min", lambda h, m: 60 * h + m)


class ElapsedStartUnknown(_Base):
    name, variant = "arith_elapsed_time", "start_unknown"

    def test(self):
        for problem, solution in self.samples():
            end, h, m = re.search(r"ended at (\d+:\d\d) and lasted (\d+) hr (\d+) min", problem).groups()
            self.assertEqual(solution, _clock(_parse_clock(end) - 60 * int(h) - int(m)), problem)


class ElapsedDuration(_Base):
    name, variant = "arith_elapsed_time", "duration"

    def test(self):
        def minutes(h, m, half):
            return (int(h) % 12 + (12 if half == "p.m." else 0)) * 60 + int(m)
        for problem, solution in self.samples():
            m = re.search(r"from (\d+):(\d\d) (a\.m\.|p\.m\.) to (\d+):(\d\d) (a\.m\.|p\.m\.)", problem)
            start, end = minutes(*m.groups()[:3]), minutes(*m.groups()[3:])
            self.assertGreater(end, start, problem)
            self.assertEqual(solution, str(end - start), problem)


class MoneyHowMuchMore(_Base):
    name, variant = "arith_money", "how_much_more"

    def test(self):
        for problem, solution in self.samples():
            have, need = re.findall(r"\$(\d+\.\d+)\$", problem)
            self.assertEqual(Fraction(solution), Fraction(need) - Fraction(have), problem)


class MoneyLeftAfterBuying(_Base):
    name, variant = "arith_money", "left_after_buying"

    def test(self):
        for problem, solution in self.samples():
            price = Fraction(re.search(r"cost \$(\d+\.\d+)\$", problem).group(1))
            have = int(re.search(r"With \$(\d+)\$ dollars", problem).group(1))
            bought = max(k for k in range(0, 1000) if k * price <= have)
            self.assertEqual(Fraction(solution), have - bought * price, problem)


class RectangleMissingSide(_Base):
    name, variant = "arith_area_of_rectangle", "missing_side"

    def test(self):
        def compute(area, length):
            self.assertEqual(area % length, 0)
            return area // length
        self.check(r"area of \$(\d+)\$ square units and a length of \$(\d+)\$", compute)


class RectangleLShape(_Base):
    name, variant = "arith_area_of_rectangle", "l_shape"

    def test(self):
        def compute(W, H, cw, ch):
            self.assertTrue(cw < W and ch < H)
            return W * H - cw * ch
        self.check(r"\$(\d+)\$ by \$(\d+)\$ rectangle has a \$(\d+)\$ by \$(\d+)\$", compute)


class CompareTensOnes(_Base):
    name, variant = "arith_compare_numbers", "tens_and_ones"

    def test(self):
        def compute(t1, o1, t2, o2):
            a, b = 10 * t1 + o1, 10 * t2 + o2
            self.assertNotEqual(a, b)
            return max(a, b)
        self.check(r"\$(\d+)\$ tens and \$(\d+)\$ ones, or \$(\d+)\$ tens and \$(\d+)\$ ones", compute)


class CompareMissingDigit(_Base):
    name, variant = "arith_compare_three_digit", "missing_digit"

    def test(self):
        self.check(
            r"\$(\d)\\square(\d) > (\d+)\$",
            lambda h, o, right: min(d for d in range(10) if 100 * h + 10 * d + o > right),
        )


class SequenceMissingFirst(_Base):
    name, variant = "arith_missing_number_sequence", "missing_first"

    def test(self):
        for problem, solution in self.samples():
            terms = _ints(problem.split("?, ")[1])
            diffs = {b - a for a, b in zip(terms, terms[1:])}
            self.assertEqual(len(diffs), 1, problem)
            self.assertEqual(solution, str(terms[0] - diffs.pop()), problem)


class EvenOddSumProduct(_Base):
    name, variant = "arith_even_or_odd", "sum_or_product"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"\$(\d+) (\+|\\times) (\d+)\$", problem)
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            value = a + b if op == "+" else a * b
            self.assertEqual(solution, "even" if value % 2 == 0 else "odd", problem)


class OrdinalFromBack(_Base):
    name, variant = "arith_ordinal_number", "from_the_back"

    def test(self):
        for problem, solution in self.samples():
            n = int(re.search(r"There are \$(\d+)\$ children", problem).group(1))
            k = int(re.search(r"Sam is (\d+)(?:st|nd|rd|th) from the front", problem).group(1))
            line = list(range(1, n + 1))  # positions from the front
            self.assertEqual(solution, _ordinal(line[::-1].index(k) + 1), problem)


class StoryChangeUnknown(_Base):
    name, variant = "arith_word_problem_within_20", "change_unknown"

    def test(self):
        def compute(start, now):
            self.assertLessEqual(now, 20)
            return now - start
        self.check(r"had \$(\d+)\$ shells.*now she has \$(\d+)\$", compute)


class Within1000Compensation(_Base):
    name, variant = "arith_add_subtract_within_1000", "compensation"

    def test(self):
        def compute(a, b, c):
            self.assertNotEqual(a, c)
            return a + b - c
        self.check(r"\$(\d+) \+ (\d+) = (\d+) \+ \\square\$", compute)


class TellTimePhrases(_Base):
    name, variant = "arith_tell_time_five_min", "quarter_and_before"

    def test(self):
        for problem, solution in self.samples():
            if m := re.search(r"'quarter to (\d+)'", problem):
                want = _clock(int(m.group(1)) * 60 - 15)
            elif m := re.search(r"'(\d+) minutes before (\d+) o'clock'", problem):
                want = _clock(int(m.group(2)) * 60 - int(m.group(1)))
            else:
                m = re.search(r"(\d+) minutes after (\d+:\d\d)\?", problem)
                want = _clock(_parse_clock(m.group(2)) + int(m.group(1)))
            self.assertEqual(solution, want, problem)


class FewestCoins(_Base):
    name, variant = "arith_count_money_value", "fewest_coins"

    def test(self):
        best = [0] + [math.inf] * 99
        for c in range(1, 100):
            best[c] = 1 + min(best[c - coin] for coin in (1, 5, 10, 25) if coin <= c)
        self.check(r"make \$(\d+)\$ cents", lambda cents: best[cents])


class ArrayRowsFromTotal(_Base):
    name, variant = "arith_array_repeated_addition", "rows_from_total"

    def test(self):
        def compute(total, rows):
            self.assertEqual(total % rows, 0)
            return total // rows
        self.check(r"\$(\d+)\$ chairs are set up in \$(\d+)\$ equal rows", compute)


class ArrayRepeatedAddition(_Base):
    name, variant = "arith_array_repeated_addition", "repeated_addition"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"\$([\d + ]+) = \\square \\times (\d+)\$", problem)
            addends = _ints(m.group(1))
            self.assertEqual(set(addends), {int(m.group(2))}, problem)
            self.assertEqual(solution, str(len(addends)), problem)


class EquivalentFractionOfSet(_Base):
    name, variant = "arith_equivalent_fraction", "fraction_of_set"

    def test(self):
        def compute(total, n, d):
            part = Fraction(n, d) * total
            self.assertEqual(part.denominator, 1)
            return part.numerator
        self.check(r"into \$(\d+)\$ equal slices\. How many slices make \$(\d+)/(\d+)\$", compute)


class MissingFactorEqualProducts(_Base):
    name, variant = "arith_missing_factor", "equal_products"

    def test(self):
        self.check(
            r"\$(\d+) \\times \\square = (\d+) \\times (\d+)\$",
            lambda a, b, c: next(k for k in range(1, b * c + 1) if a * k == b * c),
        )


class NumberLineWhichTick(_Base):
    name, variant = "arith_fraction_on_number_line", "which_tick"

    def test(self):
        self.check(
            r"into \$(\d+)\$ equal parts\. .* shows \$(\d+)/(\d+)\$",
            lambda parts, n, d: next(t for t in range(1, parts) if Fraction(t, parts) == Fraction(n, d)),
        )


class FractionWholeFromPart(_Base):
    name, variant = "arith_fraction_times_whole", "whole_from_part"

    def test(self):
        self.check(r"\$(\d+)/(\d+)\$ of a number is \$(\d+)\$", lambda n, d, part: Fraction(part * d, n))


class ImproperWholePart(_Base):
    name, variant = "arith_mixed_to_improper", "whole_part"

    def test(self):
        def compute(n, d):
            self.assertNotEqual(n % d, 0)
            return max(k for k in range(0, n + 1) if k * d < n)
        self.check(r"\$(\d+)/(\d+)\$ is between", compute)


class LongDivisionInterpret(_Base):
    name, variant = "arith_long_division_remainder", "interpret"

    def test(self):
        for problem, solution in self.samples():
            if m := re.search(r"divided by \$(\d+)\$ gives \$(\d+)\$ R \$(\d+)\$", problem):
                d, q, r = map(int, m.groups())
                self.assertLess(r, d)
                want = d * q + r
            else:
                total, per = _ints(problem)[:2]
                want = {True: -(-total // per)}.get("vans are needed" in problem)
                if want is None:
                    want = total // per if "completely filled" in problem else total % per
            self.assertEqual(solution, str(want), problem)


class AngleBisector(_Base):
    name, variant = "arith_angle_addition", "bisector"

    def test(self):
        for problem, solution in self.samples():
            if "angle ABD measures" in problem:
                want = 2 * self.search(r"ABD measures \$(\d+)\^\\circ\$", problem)[0]
            else:
                whole = self.search(r"ABC, which measures \$(\d+)\^\\circ\$", problem)[0]
                self.assertEqual(whole % 2, 0)
                want = whole // 2
            self.assertEqual(solution, str(want), problem)


class FactorPairsRectangles(_Base):
    name, variant = "arith_factor_pairs_count", "rectangles"

    def test(self):
        self.check(
            r"all \$(\d+)\$ square tiles",
            lambda n: len({tuple(sorted((a, n // a))) for a in range(1, n + 1) if n % a == 0}),
        )


class RoundDecimalReverse(_Base):
    name, variant = "arith_round_decimal", "smallest_that_rounds"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"rounds to \$([\d.]+)\$ \(nearest tenth\)\. What is the (smallest|largest)", problem)
            target = Fraction(m.group(1))
            ok = [Fraction(h, 100) for h in range(0, 1100) if num(Fraction(h, 100), 1) == num(target, 1)]
            want = min(ok) if m.group(2) == "smallest" else max(ok)
            self.assertEqual(Fraction(solution), want, problem)
