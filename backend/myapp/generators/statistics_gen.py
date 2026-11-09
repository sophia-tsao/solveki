"""Solveki-local statistics / data-analysis generators.

These cover the computable gaps in Georgia's "Statistical Reasoning" course
and the data-analysis strands of Algebra. Every generator here is named with a
``stat_`` prefix, takes no required arguments, and returns a ``(problem,
solution)`` pair of LaTeX strings. Problem statements are written to be
regex-parseable (datasets are rendered as e.g. ``data set: 3, 7, 1, 9, 4``) so
the math-correctness tests can recover the inputs and recompute the answer.
"""
import math
import random
from fractions import Fraction
from math import gcd

from ._registry import register
from ._variants import with_variants
from ._format import num as _fmt  # noqa: F401 — typeable number formatter
from ._format import frac_from  # noqa: F401 — typeable fraction formatter
from ._steps import Steps, paren, tex_frac

_ROUNDED_LEAD = "Rounded to the nearest thousandth, the answer is"


def _median(values):
    """Median of a list, using the mean of the two middle values when even."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _is_exact(value):
    """Whether `value` needs no rounding to be shown to 3 decimal places."""
    return abs(float(value) - round(float(value), 3)) < 1e-12


def _lead(value):
    """The `Steps.answer` lead: mention rounding only when it happened."""
    return "The answer is" if _is_exact(value) else _ROUNDED_LEAD


def _eq(value):
    """`=` when `value` shows exactly to 3 decimals, else `\\approx`."""
    return "=" if _is_exact(value) else r"\approx"


def _ftex(value):
    """A Fraction as LaTeX: an integer, or a reduced ``\\frac``."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return tex_frac(value.numerator, value.denominator)


def _ordinal(k):
    if 10 <= k % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(k % 10, "th")
    return f"{k}{suffix}"


def _list_tex(values):
    return ", ".join(_fmt(v) for v in values)


def _median_tex(ordered):
    """LaTeX for the median of an ordered list: its middle value, or the mean
    of the two middle values."""
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return _fmt(ordered[mid])
    a, b = ordered[mid - 1], ordered[mid]
    return rf"\frac{{{a} + {b}}}{{2}} = {_fmt((a + b) / 2)}"


def _product_tex(p):
    """p(1 - p) for a two-decimal p: the value, or the product when it would
    need more than 3 decimal places (0.25 * 0.75 = 0.1875)."""
    pq = p * (1 - p)
    if _is_exact(pq):
        return _fmt(pq)
    return rf"{_fmt(p)} \cdot {_fmt(1 - p)}"


@register
@with_variants
def stat_five_number_summary(min_val=1, max_val=20):
    r"""Five-Number Summary

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given the data set: 3, 7, 1, 9, 4. Find the five-number summary. | $1, 3, 4, 7, 9$ |

    Q1 and Q3 are defined as the medians of the lower and upper halves, with
    the overall median excluded from both halves when the count is odd.
    """
    n = random.choice([5, 6, 7, 8])
    data = [random.randint(min_val, max_val) for _ in range(n)]
    ordered = sorted(data)

    mid = n // 2
    if n % 2 == 1:
        lower = ordered[:mid]
        upper = ordered[mid + 1:]
    else:
        lower = ordered[:mid]
        upper = ordered[mid:]

    minimum = ordered[0]
    maximum = ordered[-1]
    q1 = _median(lower)
    med = _median(ordered)
    q3 = _median(upper)

    problem = (
        f"Given the data set: {', '.join(str(v) for v in data)}. "
        "Find the five-number summary (minimum, Q1, median, Q3, maximum). "
        "Q1 and Q3 are the medians of the lower and upper halves, excluding "
        "the overall median when the number of values is odd. "
        "Give your answer as min, Q1, median, Q3, max."
    )
    solution = (
        f"${_fmt(minimum)}, {_fmt(q1)}, {_fmt(med)}, {_fmt(q3)}, {_fmt(maximum)}$"
    )

    s = Steps()
    s.step(f"Put the {n} values in order from least to greatest.", _list_tex(ordered))
    s.step(f"The minimum is ${_fmt(minimum)}$ and the maximum is ${_fmt(maximum)}$.")
    if n % 2 == 1:
        s.step(
            f"There are {n} values, so the median is the middle "
            f"({_ordinal(mid + 1)}) value: ${_fmt(med)}$."
        )
    else:
        s.step(
            f"There are {n} values, so the median is the mean of the "
            f"{_ordinal(mid)} and {_ordinal(mid + 1)} values.",
            rf"\text{{median}} = {_median_tex(ordered)}",
        )
    skip = " (leaving out the median)" if n % 2 == 1 else ""
    s.step(
        f"The lower half{skip} is ${_list_tex(lower)}$. Q1 is its median.",
        rf"Q_1 = {_median_tex(lower)}",
    )
    s.step(
        f"The upper half{skip} is ${_list_tex(upper)}$. Q3 is its median.",
        rf"Q_3 = {_median_tex(upper)}",
    )
    s.answer(solution, lead="As min, Q1, median, Q3, max, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def stat_z_score(min_val=0, max_val=100):
    r"""Z-Score

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A value of x = 15 comes from a distribution with mean = 10 and standard deviation = 2.5. Find its z-score. | $2$ |

    z = (x - mean) / standard deviation, rounded to 3 decimal places.
    """
    mean = random.randint(min_val, max_val)
    sd = random.choice([1, 2, 2.5, 4, 5, 8, 10])
    x = random.randint(min_val, max_val)

    z = (x - mean) / sd
    problem = (
        f"A value of x = {_fmt(x)} comes from a distribution with mean = "
        f"{_fmt(mean)} and standard deviation = {_fmt(sd)}. Find its z-score "
        "(rounded to 3 decimal places)."
    )
    solution = f"${_fmt(z)}$"

    s = Steps()
    s.formula(
        "A z-score counts how many standard deviations x is from the mean. The formula",
        r"z = \frac{x - \mu}{\sigma}",
    )
    s.substitute(rf"z = \frac{{{x} - {mean}}}{{{_fmt(sd)}}}")
    s.step(f"Subtract in the numerator, then divide by ${_fmt(sd)}$.",
           rf"z = \frac{{{x - mean}}}{{{_fmt(sd)}}} {_eq(z)} {_fmt(z)}")
    s.answer(solution, lead=_lead(z))
    return problem, solution, s.done()


def _integer_points(max_val=12):
    """Return 4-5 integer (x, y) points with non-zero x- and y-variance."""
    while True:
        count = random.choice([4, 5])
        xs = random.sample(range(0, max_val), count)  # distinct x -> Sxx > 0
        ys = [random.randint(0, max_val) for _ in range(count)]
        if len(set(ys)) > 1:  # non-constant y -> Syy > 0
            return list(zip(xs, ys))


def _points_str(points):
    return ", ".join(f"({x}, {y})" for x, y in points)


def _deviation_sums(points):
    """Exact means and deviation sums of integer points, as Fractions.

    With integer data and 4-5 points these are all multiples of 1/n, so they
    show exactly in at most two decimals.
    """
    n = len(points)
    mx = Fraction(sum(x for x, _ in points), n)
    my = Fraction(sum(y for _, y in points), n)
    sxx = sum((x - mx) ** 2 for x, _ in points)
    syy = sum((y - my) ** 2 for _, y in points)
    sxy = sum((x - mx) * (y - my) for x, y in points)
    return mx, my, sxx, syy, sxy


def _means_step(s, points):
    n = len(points)
    sx = sum(x for x, _ in points)
    sy = sum(y for _, y in points)
    s.step(
        f"Find the mean of the x-values and of the y-values ({n} points).",
        rf"\bar{{x}} = \frac{{{sx}}}{{{n}}} = {_fmt(sx / n)}, \quad "
        rf"\bar{{y}} = \frac{{{sy}}}{{{n}}} = {_fmt(sy / n)}",
    )


@register
@with_variants
def stat_correlation_coefficient(max_val=12):
    r"""Pearson Correlation Coefficient

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given the points: (1, 2), (3, 5), (4, 4), (6, 7). Find the correlation coefficient r. | $0.898$ |

    Pearson r = Sxy / sqrt(Sxx * Syy), rounded to 3 decimal places.
    """
    points = _integer_points(max_val)
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in points)
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    syy = sum((y - mean_y) ** 2 for _, y in points)

    r = sxy / math.sqrt(sxx * syy)
    problem = (
        f"Given the points: {_points_str(points)}. Find the Pearson "
        "correlation coefficient r (rounded to 3 decimal places)."
    )
    solution = f"${_fmt(r)}$"

    _, _, e_sxx, e_syy, e_sxy = _deviation_sums(points)
    s = Steps()
    _means_step(s, points)
    s.formula("The correlation coefficient",
              r"r = \frac{S_{xy}}{\sqrt{S_{xx} \cdot S_{yy}}}")
    s.step(
        r"Over all the points, add up $S_{xy} = \sum (x - \bar{x})(y - \bar{y})$, "
        r"$S_{xx} = \sum (x - \bar{x})^2$, and $S_{yy} = \sum (y - \bar{y})^2$.",
        rf"S_{{xy}} = {_fmt(e_sxy)}, \quad S_{{xx}} = {_fmt(e_sxx)}, \quad "
        rf"S_{{yy}} = {_fmt(e_syy)}",
    )
    s.substitute(
        rf"r = \frac{{{_fmt(e_sxy)}}}{{\sqrt{{{_fmt(e_sxx)} \cdot {_fmt(e_syy)}}}}}"
        rf" {_eq(r)} {_fmt(r)}",
        text="Substitute and evaluate.",
    )
    s.answer(solution, lead=_lead(r))
    return problem, solution, s.done()


@register
@with_variants
def stat_regression_line(max_val=12):
    r"""Least-Squares Regression Line

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given the points: (1, 2), (3, 5), (4, 4), (6, 7). Find the least-squares regression line. | $y = 0.836 x + 1.291$ |

    Slope m = Sxy / Sxx, intercept b = mean_y - m * mean_x, both rounded to 3dp.
    """
    points = _integer_points(max_val)
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in points)
    sxx = sum((x - mean_x) ** 2 for x, _ in points)

    m = sxy / sxx
    b = mean_y - m * mean_x

    sign = "-" if _fmt(b).startswith("-") else "+"
    problem = (
        f"Given the points: {_points_str(points)}. Find the least-squares "
        "regression line y = m x + b (m and b rounded to 3 decimal places)."
    )
    solution = f"$y = {_fmt(m)} x {sign} {_fmt(abs(b))}$"

    e_mx, e_my, e_sxx, _, e_sxy = _deviation_sums(points)
    e_m = e_sxy / e_sxx
    m_tex = _ftex(e_m)
    if e_m < 0:
        m_tex = rf"\left({m_tex}\right)"
    s = Steps()
    _means_step(s, points)
    s.step(
        "The least-squares slope and intercept are:",
        r"m = \frac{S_{xy}}{S_{xx}}, \quad b = \bar{y} - m\bar{x}",
    )
    s.step(
        r"Add up the deviation products $S_{xy} = \sum (x - \bar{x})(y - \bar{y})$ "
        r"and squares $S_{xx} = \sum (x - \bar{x})^2$.",
        rf"S_{{xy}} = {_fmt(e_sxy)}, \quad S_{{xx}} = {_fmt(e_sxx)}",
    )
    s.step(
        "Divide to get the slope.",
        rf"m = \frac{{{_fmt(e_sxy)}}}{{{_fmt(e_sxx)}}} = {_ftex(e_m)}"
        + ("" if e_m.denominator == 1 else rf" {_eq(m)} {_fmt(m)}"),
    )
    s.step(
        "Find the intercept, using the exact slope.",
        rf"b = {_fmt(e_my)} - {m_tex} \cdot {_fmt(e_mx)} {_eq(b)} {_fmt(b)}",
    )
    exact = _is_exact(m) and _is_exact(b)
    s.answer(solution, lead="The answer is" if exact else
             "With m and b rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def stat_margin_of_error(min_n=30, max_n=1500):
    r"""Margin of Error for a Proportion

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A poll has sample proportion p = 0.4, sample size n = 100, and critical value z = 1.96. Find the margin of error. | $0.096$ |

    Margin of error = z * sqrt(p(1 - p) / n), rounded to 3 decimal places.
    """
    p = random.choice([0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9])
    z = random.choice([1.645, 1.96, 2.576])
    n = random.randint(min_n, max_n)

    moe = z * math.sqrt(p * (1 - p) / n)
    problem = (
        f"A poll has sample proportion p = {_fmt(p)}, sample size n = {n}, and "
        f"critical value z = {_fmt(z)}. Find the margin of error "
        "z * sqrt(p(1 - p) / n) (rounded to 3 decimal places)."
    )
    solution = f"${_fmt(moe)}$"

    s = Steps()
    s.formula("The margin of error for a proportion",
              r"E = z\sqrt{\frac{p(1 - p)}{n}}")
    s.substitute(rf"E = {_fmt(z)}\sqrt{{\frac{{{_fmt(p)}(1 - {_fmt(p)})}}{{{n}}}}}")
    s.step(
        f"Simplify inside the square root: $1 - {_fmt(p)} = {_fmt(1 - p)}$"
        + (", then multiply." if _is_exact(p * (1 - p)) else "."),
        rf"E = {_fmt(z)}\sqrt{{\frac{{{_product_tex(p)}}}{{{n}}}}}",
    )
    s.step("Take the square root, then multiply by $z$.",
           rf"E {_eq(moe)} {_fmt(moe)}")
    s.answer(solution, lead=_lead(moe))
    return problem, solution, s.done()


@register
@with_variants
def stat_standard_error_mean(max_sd=50, max_n=400):
    r"""Standard Error of the Mean

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A sample has standard deviation s = 12 and size n = 36. Find the standard error of the mean. | $2$ |

    Standard error = s / sqrt(n), rounded to 3 decimal places.
    """
    sd = random.randint(1, max_sd)
    n = random.randint(2, max_n)

    se = sd / math.sqrt(n)
    problem = (
        f"A sample has standard deviation s = {sd} and size n = {n}. Find the "
        "standard error of the mean s / sqrt(n) (rounded to 3 decimal places)."
    )
    solution = f"${_fmt(se)}$"

    s = Steps()
    s.formula("The standard error of the mean", r"SE = \frac{s}{\sqrt{n}}")
    s.substitute(rf"SE = \frac{{{sd}}}{{\sqrt{{{n}}}}}")
    root = math.isqrt(n)
    if root * root == n:
        s.step(f"Since $\\sqrt{{{n}}} = {root}$, divide.",
               rf"SE = \frac{{{sd}}}{{{root}}} {_eq(se)} {_fmt(se)}")
    else:
        s.step(f"Evaluate: $\\sqrt{{{n}}} \\approx {_fmt(math.sqrt(n))}$, then divide "
               "(keep full calculator precision).",
               rf"SE \approx {_fmt(se)}")
    s.answer(solution, lead=_lead(se))
    return problem, solution, s.done()


@register
@with_variants
def stat_sample_proportion_ci(min_n=30, max_n=1500):
    r"""Confidence Interval for a Proportion

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A sample has proportion p = 0.4, size n = 100, and critical value z = 1.96. Find the confidence interval p +/- z*sqrt(p(1-p)/n). | $(0.304, 0.496)$ |

    Interval endpoints p +/- z * sqrt(p(1 - p) / n), each rounded to 3dp.
    """
    p = random.choice([0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9])
    z = random.choice([1.645, 1.96, 2.576])
    n = random.randint(min_n, max_n)

    moe = z * math.sqrt(p * (1 - p) / n)
    low = p - moe
    high = p + moe
    problem = (
        f"A sample has proportion p = {_fmt(p)}, size n = {n}, and critical "
        f"value z = {_fmt(z)}. Find the confidence interval "
        "p +/- z*sqrt(p(1-p)/n) (endpoints rounded to 3 decimal places). "
        "Give your answer as (low, high)."
    )
    solution = f"$({_fmt(low)}, {_fmt(high)})$"

    s = Steps()
    s.formula("A confidence interval for a proportion",
              r"p \pm E, \quad E = z\sqrt{\frac{p(1 - p)}{n}}")
    s.step(
        "Find the margin of error.",
        rf"E = {_fmt(z)}\sqrt{{\frac{{{_product_tex(p)}}}{{{n}}}}} \approx {_fmt(moe)}",
    )
    s.step(
        "Subtract and add the margin of error (keep its unrounded value).",
        rf"{_fmt(p)} - E \approx {_fmt(low)}, \quad {_fmt(p)} + E \approx {_fmt(high)}",
    )
    s.answer(solution, lead="As (low, high), rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def stat_relative_frequency(max_count=20):
    r"""Relative Frequency

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A survey recorded these category counts: 4, 7, 9, 5. Find the relative frequency of category 2. | $7/25$ |

    Relative frequency = category count / total count, as a reduced fraction.
    """
    k = random.choice([3, 4, 5])
    counts = [random.randint(1, max_count) for _ in range(k)]
    index = random.randint(0, k - 1)  # 0-based
    count = counts[index]
    total = sum(counts)

    divisor = gcd(count, total)
    numerator = count // divisor
    denominator = total // divisor

    problem = (
        f"A survey recorded these category counts: {', '.join(str(c) for c in counts)}. "
        f"Find the relative frequency of category {index + 1} "
        "(as a reduced fraction)."
    )
    solution = f"${numerator}/{denominator}$"

    s = Steps()
    s.step("Relative frequency is a category's count divided by the total count.",
           r"\text{relative frequency} = \frac{\text{category count}}{\text{total}}")
    s.step("Add all the counts to get the total.",
           f"{' + '.join(str(c) for c in counts)} = {total}")
    s.step(f"Category {index + 1} has a count of ${count}$, so its relative frequency is:",
           tex_frac(count, total))
    if divisor > 1:
        s.step(f"Divide the top and bottom by ${divisor}$ to reduce.",
               rf"\frac{{{count} \div {divisor}}}{{{total} \div {divisor}}} = "
               f"{tex_frac(numerator, denominator)}")
    s.answer(solution, lead="As a reduced fraction, the answer is")
    return problem, solution, s.done()


def _phi(z):
    """Standard-normal CDF via the error function: 0.5*(1 + erf(z/sqrt(2)))."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


@register
@with_variants
def stat_normal_probability():
    r"""Normal Distribution Probability

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A normally distributed variable X has mean = 50 and standard deviation = 10. Using the normal CDF, find P(X < 65). Round to the nearest thousandth. | $0.933$ |

    P uses the normal CDF Phi(z) = 0.5*(1 + erf(z/sqrt(2))); the answer is a
    decimal in [0, 1] rounded to 3 decimal places.
    """
    mean = random.randint(20, 80)
    sd = random.choice([2, 4, 5, 10])
    mults = [-2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2]
    kind = random.choice(["less", "greater", "between"])

    if kind == "between":
        a_m, b_m = sorted(random.sample(mults, 2))
        a = mean + sd * a_m
        b = mean + sd * b_m
        prob = _phi((b - mean) / sd) - _phi((a - mean) / sd)
        event = f"P({_fmt(a)} < X < {_fmt(b)})"
    elif kind == "less":
        b = mean + sd * random.choice(mults)
        prob = _phi((b - mean) / sd)
        event = f"P(X < {_fmt(b)})"
    else:
        b = mean + sd * random.choice(mults)
        prob = 1.0 - _phi((b - mean) / sd)
        event = f"P(X > {_fmt(b)})"

    problem = (
        f"A normally distributed variable X has mean = {_fmt(mean)} and "
        f"standard deviation = {_fmt(sd)}. Using the normal CDF, find "
        f"{event}. Round to the nearest thousandth."
    )
    solution = f"${_fmt(prob)}$"

    def z_tex(x):
        return rf"\frac{{{_fmt(x)} - {mean}}}{{{sd}}} = {_fmt((x - mean) / sd)}"

    z_b = _fmt((b - mean) / sd)
    s = Steps()
    s.step(f"Convert to the standard normal using $z = \\frac{{x - \\mu}}{{\\sigma}}$, "
           f"with $\\mu = {mean}$ and $\\sigma = {sd}$.")
    if kind == "between":
        z_a = _fmt((a - mean) / sd)
        s.step(f"Find the z-scores of ${_fmt(a)}$ and ${_fmt(b)}$.",
               rf"z_1 = {z_tex(a)}, \quad z_2 = {z_tex(b)}")
        s.step(
            "The probability between them is the area to the left of $z_2$ "
            "minus the area to the left of $z_1$.",
            rf"{event} = \Phi({z_b}) - \Phi({z_a})",
        )
        s.step("Evaluate both with a calculator's normal CDF and subtract, "
               "keeping full precision until the end.")
    else:
        s.step(f"Find the z-score of ${_fmt(b)}$.", f"z = {z_tex(b)}")
        phi_b = _phi((b - mean) / sd)
        if kind == "less":
            s.step("The probability is the area to the left of $z$.",
                   rf"{event} = \Phi({z_b}) \approx {_fmt(phi_b)}")
        else:
            s.step("The probability is the area to the right of $z$, which is "
                   "1 minus the area to the left.",
                   rf"{event} = 1 - \Phi({z_b}) \approx 1 - {_fmt(phi_b)}")
    s.answer(solution, lead=_lead(prob))
    return problem, solution, s.done()


@register
@with_variants
def stat_test_statistic():
    r"""Test Statistic for a Mean or Proportion

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A sample of size n = 36 has mean xbar = 52. The hypothesized mean is mu0 = 50 and the population standard deviation is sigma = 6. Find the z test statistic (round to the nearest thousandth). | $2$ |

    Mean: z = (xbar - mu0) / (sigma / sqrt(n)). Proportion: z = (phat - p0) /
    sqrt(p0(1 - p0) / n). Rounded to 3 decimal places.
    """
    kind = random.choice(["mean", "proportion"])
    s = Steps()
    if kind == "mean":
        n = random.choice([16, 25, 36, 49, 100])
        sigma = random.choice([3, 4, 5, 6, 8, 10])
        mu0 = random.randint(20, 80)
        xbar = mu0 + random.choice([-8, -5, -4, -3, -2, 2, 3, 4, 5, 8])
        z = (xbar - mu0) / (sigma / math.sqrt(n))
        problem = (
            f"A sample of size n = {n} has mean xbar = {_fmt(xbar)}. The "
            f"hypothesized mean is mu0 = {_fmt(mu0)} and the population "
            f"standard deviation is sigma = {_fmt(sigma)}. Find the z test "
            "statistic (round to the nearest thousandth)."
        )
        root = math.isqrt(n)
        diff = xbar - mu0
        s.formula("The z test statistic for a mean",
                  r"z = \frac{\bar{x} - \mu_0}{\sigma / \sqrt{n}}")
        s.substitute(rf"z = \frac{{{xbar} - {mu0}}}{{{sigma} / \sqrt{{{n}}}}}")
        se = Fraction(sigma, root)
        reduced = f" = {_ftex(se)}" if math.gcd(sigma, root) > 1 else ""
        s.step(
            f"Simplify the denominator: $\\sqrt{{{n}}} = {root}$, so "
            f"$\\sigma / \\sqrt{{n}} = \\frac{{{sigma}}}{{{root}}}{reduced}$.",
        )
        exact_z = _ftex(Fraction(diff * root, sigma))
        if se.denominator == 1:
            s.step(f"Divide the difference ${diff}$ by ${se}$.",
                   rf"z = \frac{{{diff}}}{{{se}}} = {exact_z}")
        else:
            s.step(f"Divide the difference ${diff}$ by ${_ftex(se)}$: multiply by "
                   "its reciprocal.",
                   rf"z = {diff} \cdot {_ftex(1 / se)}"
                   rf" = {exact_z}")
    else:
        n = random.choice([100, 150, 200, 400, 500])
        p0 = random.choice([0.25, 0.4, 0.5, 0.6, 0.75])
        phat = round(p0 + random.choice([-0.1, -0.08, -0.05, 0.05, 0.08, 0.1, 0.12]), 3)
        z = (phat - p0) / math.sqrt(p0 * (1 - p0) / n)
        problem = (
            f"A sample of size n = {n} has sample proportion phat = {_fmt(phat)}. "
            f"The hypothesized proportion is p0 = {_fmt(p0)}. Find the z test "
            "statistic (round to the nearest thousandth)."
        )
        s.formula("The z test statistic for a proportion",
                  r"z = \frac{\hat{p} - p_0}{\sqrt{\frac{p_0(1 - p_0)}{n}}}")
        s.substitute(rf"z = \frac{{{_fmt(phat)} - {_fmt(p0)}}}"
                     rf"{{\sqrt{{\frac{{{_fmt(p0)}(1 - {_fmt(p0)})}}{{{n}}}}}}}")
        s.step("Simplify the numerator and the product under the square root.",
               rf"z = \frac{{{_fmt(phat - p0)}}}{{\sqrt{{\frac{{{_product_tex(p0)}}}{{{n}}}}}}}")
    solution = f"${_fmt(z)}$"
    s.answer(solution, lead=_lead(z))
    return problem, solution, s.done()


@register
@with_variants
def stat_discrete_variance():
    r"""Expected Value and Variance

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A discrete random variable X takes the values 1, 2, 5 with probabilities 0.2, 0.5, 0.3 respectively. Find the variance Var(X) (round to the nearest thousandth if necessary). | $2.49$ |

    Var(X) = E[X^2] - (E[X])^2 = sum p_i x_i^2 - (sum p_i x_i)^2, rounded to 3
    decimal places when necessary.
    """
    denom = random.choice([10, 20])
    k = random.choice([3, 4])
    cuts = sorted(random.sample(range(1, denom), k - 1))
    counts = [b - a for a, b in zip([0] + cuts, cuts + [denom])]
    values = random.sample(range(0, 10), k)
    probs = [c / denom for c in counts]

    ev = sum(p * v for p, v in zip(probs, values))
    ev2 = sum(p * v * v for p, v in zip(probs, values))
    var = ev2 - ev * ev

    vals_str = ", ".join(str(v) for v in values)
    probs_str = ", ".join(_fmt(p) for p in probs)
    problem = (
        f"A discrete random variable X takes the values {vals_str} with "
        f"probabilities {probs_str} respectively. Find the variance Var(X) "
        "(round to the nearest thousandth if necessary)."
    )
    solution = f"${_fmt(var)}$"

    # Exact values: probabilities are multiples of 1/20, so E[X] and E[X^2]
    # show exactly in two decimals; only (E[X])^2 may need rounding.
    e_probs = [Fraction(c, denom) for c in counts]
    e_ev = sum(p * v for p, v in zip(e_probs, values))
    e_ev2 = sum(p * v * v for p, v in zip(e_probs, values))
    pairs = list(zip(values, e_probs))
    s = Steps()
    s.formula("The variance of a discrete random variable",
              r"\operatorname{Var}(X) = E[X^2] - (E[X])^2")
    s.step(
        "Find the expected value: multiply each value by its probability and add.",
        " + ".join(rf"{v}({_fmt(p)})" for v, p in pairs) + rf" = {_fmt(e_ev)}",
    )
    s.step(
        "Find $E[X^2]$: multiply each squared value by its probability and add.",
        " + ".join(rf"{v}^2({_fmt(p)})" for v, p in pairs) + rf" = {_fmt(e_ev2)}",
    )
    square = rf" = {_fmt(e_ev2)} - {_fmt(e_ev ** 2)}" if _is_exact(e_ev ** 2) else ""
    s.step(
        "Subtract the square of the expected value.",
        rf"\operatorname{{Var}}(X) = {_fmt(e_ev2)} - ({_fmt(e_ev)})^2{square}"
        rf" {_eq(e_ev2 - e_ev ** 2)} {_fmt(var)}",
    )
    s.answer(solution, lead=_lead(e_ev2 - e_ev ** 2))
    return problem, solution, s.done()


@register
@with_variants
def stat_percentile_rank():
    r"""Percentile Rank

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given the data set: 3, 7, 1, 9, 4. Find the percentile rank of the value 7. Use percentile rank = (number of values below it) / n * 100, and round to the nearest thousandth if necessary. | $60$ |

    Percentile rank = (number of values strictly below the target) / n * 100,
    rounded to 3 decimal places when necessary.
    """
    n = random.choice([6, 7, 8, 9, 10])
    data = [random.randint(1, 20) for _ in range(n)]
    value = random.choice(data)
    below = sum(1 for v in data if v < value)
    pr = below / n * 100

    problem = (
        f"Given the data set: {', '.join(str(v) for v in data)}. Find the "
        f"percentile rank of the value {value}. Use percentile rank = "
        "(number of values below it) / n * 100, and round to the nearest "
        "thousandth if necessary."
    )
    solution = f"${_fmt(pr)}$"

    s = Steps()
    s.step("Put the data in order from least to greatest.", _list_tex(sorted(data)))
    if below == 0:
        s.step(f"No values are strictly below ${value}$.")
    else:
        s.step(f"Count the values strictly below ${value}$: there "
               f"{'is' if below == 1 else 'are'} ${below}$.")
    s.formula("The percentile rank",
              r"\text{percentile rank} = \frac{\text{number below}}{n} \cdot 100")
    s.substitute(rf"\frac{{{below}}}{{{n}}} \cdot 100 {_eq(pr)} {_fmt(pr)}",
                 text=f"Substitute, with $n = {n}$ values in all.")
    s.answer(solution, lead=_lead(pr))
    return problem, solution, s.done()


@register
@with_variants
def stat_counting_probability():
    r"""Counting to Probability

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A box contains 10 marbles: 4 red and 6 green. You draw 3 marbles at random without replacement. Find the probability that exactly 2 are red. Express your answer as a reduced fraction a/b. | $3/10$ |

    Probability = C(r, m) * C(g, k - m) / C(n, k), given as a reduced fraction.
    """
    while True:
        r = random.randint(2, 6)
        g = random.randint(2, 6)
        n = r + g
        k = random.randint(2, min(4, n - 1))
        m = random.randint(max(0, k - g), min(k, r))
        ways = math.comb(r, m) * math.comb(g, k - m)
        total = math.comb(n, k)
        prob = Fraction(ways, total)
        if 0 < prob < 1:
            break

    problem = (
        f"A box contains {n} marbles: {r} red and {g} green. You draw {k} "
        "marbles at random without replacement. Find the probability that "
        f"exactly {m} are red. Express your answer as a reduced fraction a/b."
    )
    solution = f"${frac_from(prob)}$"

    s = Steps()
    s.step(
        f"Count the ways to choose exactly {m} red from {r} and {k - m} green from {g}.",
        rf"\binom{{{r}}}{{{m}}} \cdot \binom{{{g}}}{{{k - m}}} = "
        rf"{math.comb(r, m)} \cdot {math.comb(g, k - m)} = {ways}",
    )
    s.step(f"Count all the ways to choose {k} of the {n} marbles.",
           rf"\binom{{{n}}}{{{k}}} = {total}")
    reduced = f" = {_ftex(prob)}" if math.gcd(ways, total) > 1 else ""
    s.step("Divide the favorable ways by the total ways, and reduce.",
           rf"P = {tex_frac(ways, total)}{reduced}")
    s.answer(solution, lead="As a reduced fraction, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def stat_odds_probability():
    r"""Odds from Probability

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | The probability of an event is 3/7. Write the odds in favor of the event in the form a:b (lowest terms). | $3:4$ |

    Odds in favor = P : (1 - P). For P = a/b this is a : (b - a), reduced to
    lowest terms.
    """
    b = random.randint(3, 12)
    a = random.randint(1, b - 1)
    fr = Fraction(a, b)

    favor = fr.numerator
    against = fr.denominator - fr.numerator
    g = gcd(favor, against)

    problem = (
        f"The probability of an event is {fr.numerator}/{fr.denominator}. "
        "Write the odds in favor of the event in the form a:b (lowest terms)."
    )
    solution = f"${favor // g}:{against // g}$"

    s = Steps()
    s.step(
        "Odds in favor compare the chance the event happens to the chance it "
        "doesn't.",
        r"\text{odds in favor} = P : (1 - P)",
    )
    s.step(
        f"With $P = {tex_frac(fr.numerator, fr.denominator)}$, out of "
        f"${fr.denominator}$ equally likely outcomes, ${favor}$ "
        f"{'is' if favor == 1 else 'are'} favorable and "
        f"${fr.denominator} - {favor} = {against}$ "
        f"{'is' if against == 1 else 'are'} not.",
        f"{favor} : {against}",
    )
    if g > 1:
        s.step(f"Divide both parts by ${g}$.", f"{favor // g} : {against // g}")
    else:
        s.step(f"${favor}$ and ${against}$ have no common factor, so this is in lowest terms.")
    s.answer(solution, lead="In lowest terms, the answer is")
    return problem, solution, s.done()
