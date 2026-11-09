"""Extra question types for the statistics, probability and finance topics.

Variants for the generators in ``statistics_gen``, ``lib_seqstats_gen``,
``lib_finance_gen``, ``lib_fractions_gen`` and ``algebra2`` (z-scores). Each
attaches to its topic's dispatcher (see ``_variants.with_variants``); the
original question stays as the ``classic`` variant. See
docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction
from statistics import NormalDist

from ._format import frac_from, num
from ._steps import Steps, tex_frac
from . import algebra2, lib_finance_gen, lib_fractions_gen, lib_seqstats_gen, statistics_gen

_ROUND = "Round your answer to the nearest thousandth."
_ROUNDED = "Rounded to the nearest thousandth, the answer is"
_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."


def _tex(value):
    v = Fraction(value)
    return str(v.numerator) if v.denominator == 1 else tex_frac(v.numerator, v.denominator)


# --- Describing data ------------------------------------------------------------------

@lib_seqstats_gen.mean_median.variant("missing_score")
def _mean_missing_score():
    """What score on the last test brings the mean to a target?"""
    # Draw the target first, then the earlier scores around it, so a valid last score always
    # exists (drawing the scores first could leave no target in range, looping forever).
    while True:
        n = random.randint(3, 6)
        target = random.randint(70, 95)
        scores = [random.randint(60, 100) for _ in range(n - 1)]
        last = target * n - sum(scores)
        if 0 <= last <= 100:
            break
    problem = (
        f"A student's first {n - 1} test scores are {', '.join(map(str, scores))}. What score on test "
        f"{n} would make the mean of all {n} tests exactly {target}?"
    )
    solution = f"{last}"
    s = Steps()
    s.step(f"A mean of {target} over {n} tests needs a total of", f"{target} \\times {n} = {target * n}")
    s.step("Subtract the scores so far.", f"{target * n} - {sum(scores)} = {last}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.data_summary.variant("transform_sd")
def _sd_transform():
    """How adding a constant or multiplying changes the standard deviation."""
    sd = Fraction(random.randint(5, 60), 10)
    s = Steps()
    if random.random() < 0.5:
        c = random.randint(2, 30)
        problem = (f"A data set has a standard deviation of ${num(sd)}$. If ${c}$ is added to every "
                   "value, what is the new standard deviation?")
        answer = sd
        s.step(f"Adding ${c}$ shifts every value and the mean by the same amount, so the spread "
               "doesn't change.")
    else:
        c = random.randint(2, 5)
        problem = (f"A data set has a standard deviation of ${num(sd)}$. If every value is multiplied "
                   f"by ${c}$, what is the new standard deviation?")
        answer = sd * c
        s.step(f"Multiplying by ${c}$ stretches every distance from the mean by ${c}$.",
               rf"{c} \times {num(sd)} = {num(answer)}")
    solution = num(answer)
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_five_number_summary.variant("box_plot")
def _five_number_box_plot():
    """Read a box plot described in words: IQR or range."""
    mn, q1, med, q3, mx = sorted(random.sample(range(0, 101), 5))
    ask_iqr = random.random() < 0.5
    problem = (
        f"A box plot has whiskers from ${mn}$ to ${mx}$ and a box from ${q1}$ to ${q3}$ with the median "
        f"at ${med}$. What is the {'interquartile range' if ask_iqr else 'range'}?"
    )
    answer = q3 - q1 if ask_iqr else mx - mn
    solution = f"${answer}$"
    s = Steps()
    if ask_iqr:
        s.step("The box spans the first to the third quartile.", f"IQR = {q3} - {q1} = {answer}")
    else:
        s.step("The whiskers reach the minimum and maximum.", f"\\text{{range}} = {mx} - {mn} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_correlation_coefficient.variant("after_transformation")
def _correlation_after_transformation():
    """r is unchanged by shifting and positive scaling; a negative scale flips its sign."""
    r = Fraction(random.randint(-95, 95), 100)
    if r == 0:
        r = Fraction(1, 2)
    a = random.choice([2, 3, 5, -1, -2, -4])
    b = random.randint(-10, 10)
    which = random.choice(["x", "y"])
    new = r if a > 0 else -r
    sign = "+" if b >= 0 else "-"
    expr = f"{a}{which} {sign} {abs(b)}"
    problem = (
        f"The correlation between $x$ and $y$ is $r = {num(r)}$. Each {which}-value is replaced by "
        f"${expr}$. What is the new correlation?"
    )
    solution = f"${num(new)}$"
    s = Steps()
    s.step("Adding a constant doesn't change correlation, and neither does multiplying by a positive "
           "number.")
    if a < 0:
        s.step(f"Multiplying by a negative number (${a}$) reverses the direction, flipping the sign of $r$.")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_regression_line.variant("intercept_from_means")
def _regression_intercept_from_means():
    """The least-squares line passes through (x-bar, y-bar)."""
    slope = Fraction(random.randint(-40, 40), 10)
    xbar = Fraction(random.randint(10, 90), 10)
    ybar = Fraction(random.randint(-50, 300), 10)
    b = ybar - slope * xbar
    problem = (
        f"A least-squares regression line has slope ${num(slope)}$. The data have mean "
        f"$\\bar{{x}} = {num(xbar)}$ and $\\bar{{y}} = {num(ybar)}$. What is the line's y-intercept?"
    )
    solution = f"${num(b)}$"
    s = Steps()
    s.step(r"The least-squares line always passes through $(\bar{x}, \bar{y})$.",
           rf"{num(ybar)} = {num(slope)}({num(xbar)}) + b")
    s.step("Solve for $b$.", f"b = {num(b)}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_margin_of_error.variant("sample_size")
def _margin_sample_size():
    """Reverse: the smallest sample size giving a margin of error at most E."""
    p = Fraction(random.choice([30, 40, 50, 60, 70]), 100)
    z = random.choice([Fraction(1645, 1000), Fraction(196, 100), Fraction(2576, 1000)])
    e = Fraction(random.choice([2, 3, 4, 5]), 100)
    need = z * z * p * (1 - p) / (e * e)
    n = math.ceil(need)
    problem = (
        f"A poll expects a sample proportion near ${num(p)}$ and uses $z = {num(z)}$. What is the "
        f"smallest sample size $n$ that keeps the margin of error $z\\sqrt{{p(1-p)/n}}$ at most "
        f"${num(e)}$?"
    )
    solution = f"${n}$"
    s = Steps()
    s.step("Set the margin equal to the target and solve for $n$.",
           rf"n = \frac{{z^2 p(1-p)}}{{E^2}} = \frac{{{num(z)}^2({num(p)})({num(1 - p)})}}{{{num(e)}^2}} \approx {num(need)}")
    s.step("A sample size must be a whole number, and rounding down would make the margin too big, so "
           "round up.")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_standard_error_mean.variant("sample_size")
def _standard_error_sample_size():
    """Reverse: n from the standard deviation and the standard error."""
    n = random.choice([k * k for k in range(2, 21)])
    se = Fraction(random.randint(1, 20), 2)
    sd = se * math.isqrt(n)
    problem = (
        f"A sample has standard deviation $s = {num(sd)}$, and the standard error of the mean is "
        f"${num(se)}$. What is the sample size $n$?"
    )
    solution = f"${n}$"
    s = Steps()
    s.formula("The standard error", r"SE = \frac{s}{\sqrt{n}}")
    s.step("Solve for $n$.", rf"\sqrt{{n}} = \frac{{{num(sd)}}}{{{num(se)}}} = {math.isqrt(n)} \Rightarrow n = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_sample_proportion_ci.variant("from_interval")
def _proportion_from_interval():
    """Reverse: the sample proportion or margin from the interval's endpoints."""
    p = Fraction(random.randint(15, 85), 100)
    e = Fraction(random.randint(10, 90), 1000)
    low, high = p - e, p + e
    ask_p = random.random() < 0.5
    problem = (
        f"A confidence interval for a proportion is $({num(low)}, {num(high)})$. What is the "
        f"{'sample proportion' if ask_p else 'margin of error'}?"
    )
    answer = p if ask_p else e
    solution = f"${num(answer)}$"
    s = Steps()
    if ask_p:
        s.step("The interval is centered at the sample proportion: average the endpoints.",
               rf"\frac{{{num(low)} + {num(high)}}}{{2}} = {num(p)}")
    else:
        s.step("The margin of error is half the interval's width.",
               rf"\frac{{{num(high)} - {num(low)}}}{{2}} = {num(e)}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_relative_frequency.variant("count_from_frequency")
def _relative_frequency_count():
    """Reverse: a count from a relative frequency and the total."""
    # Totals whose every fraction count/total is a decimal of at most 3 places.
    total = random.choice([20, 25, 40, 50, 100, 125, 200, 250])
    count = random.randint(1, total - 1)
    rel = Fraction(count, total)
    problem = (
        f"In a survey of ${total}$ people, the relative frequency of the answer \"yes\" was "
        f"${num(rel)}$. How many people answered yes?"
    )
    solution = f"${count}$"
    s = Steps()
    s.step("Relative frequency is count divided by total, so multiply back.",
           rf"{num(rel)} \times {total} = {count}")
    s.answer(solution)
    return problem, solution, s.done()


_PERCENTILE_Z = {80: Fraction(842, 1000), 84: Fraction(994, 1000), 90: Fraction(1282, 1000),
                 95: Fraction(1645, 1000), 97: Fraction(1881, 1000), 99: Fraction(2326, 1000)}


@statistics_gen.stat_normal_probability.variant("value_at_percentile")
def _normal_value_at_percentile():
    """Inverse normal: the value at a percentile, given the matching z-score."""
    pct = random.choice(list(_PERCENTILE_Z))
    z = _PERCENTILE_Z[pct]
    upper = random.random() < 0.5
    mu, sigma = random.randint(20, 500), random.randint(2, 60)
    value = mu + (z if upper else -z) * sigma
    if upper:
        problem = (
            f"Scores are normally distributed with mean ${mu}$ and standard deviation ${sigma}$. The "
            f"{pct}th percentile of the standard normal distribution is $z = {num(z)}$. What score is "
            f"at the {pct}th percentile? {_ROUND}"
        )
    else:
        problem = (
            f"Scores are normally distributed with mean ${mu}$ and standard deviation ${sigma}$. The "
            f"{100 - pct}th percentile of the standard normal distribution is $z = {num(-z)}$. What score "
            f"is at the {100 - pct}th percentile? {_ROUND}"
        )
    solution = num(value)
    s = Steps()
    s.step("A value is the mean plus $z$ standard deviations.",
           rf"x = {mu} + ({num(z if upper else -z)})({sigma}) = {num(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_percentile_rank.variant("value_at_rank")
def _percentile_value_at_rank():
    """Reverse: which listed value has a given percentile rank."""
    n = random.choice([4, 5, 8, 10])
    data = sorted(random.sample(range(1, 100), n))
    i = random.randrange(n)
    rank = Fraction(100 * i, n)
    shuffled = data[:]
    random.shuffle(shuffled)
    problem = (
        f"Given the data set: {', '.join(map(str, shuffled))}. Which value has a percentile rank of "
        f"{num(rank)}? Use percentile rank = (number of values below it) / n * 100."
    )
    solution = f"{data[i]}"
    s = Steps()
    s.step(f"A percentile rank of {num(rank)} with n = {n} means this many values are below it:",
           rf"\frac{{{num(rank)}}}{{100}} \times {n} = {i}")
    s.step("Order the data and count up.", ", ".join(map(str, data)))
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_test_statistic.variant("reject_decision")
def _test_statistic_decision():
    """Compute z, then decide a two-sided test at the 0.05 level."""
    while True:
        sigma, n = random.randint(2, 20), random.choice([16, 25, 36, 49, 64, 81, 100])
        mu0 = random.randint(20, 200)
        xbar = mu0 + Fraction(random.randint(-40, 40), 10)
        z = (xbar - mu0) / (Fraction(sigma) / math.isqrt(n))
        if abs(abs(z) - Fraction(196, 100)) > Fraction(5, 100):
            break
    reject = abs(z) > Fraction(196, 100)
    problem = (
        f"A test of $H_0: \\mu = {mu0}$ against $H_a: \\mu \\neq {mu0}$ uses a sample of size $n = {n}$ "
        f"with mean ${num(xbar)}$; the population standard deviation is ${sigma}$. At the $0.05$ level "
        "(reject when $|z| > 1.96$), do you reject $H_0$? Answer yes or no."
    )
    answer = "yes" if reject else "no"
    s = Steps()
    s.formula("The test statistic", rf"z = \frac{{\bar x - \mu_0}}{{\sigma/\sqrt{{n}}}} = "
              rf"\frac{{{num(xbar)} - {mu0}}}{{{sigma}/{math.isqrt(n)}}} \approx {num(z)}")
    s.step(f"Compare $|z| \\approx {num(abs(z))}$ with $1.96$.")
    s.answer(answer)
    return problem, answer, s.done()


@statistics_gen.stat_discrete_variance.variant("linear_transform")
def _variance_linear_transform():
    """Var(aX + b) = a^2 Var(X)."""
    var = Fraction(random.randint(5, 90), 10)
    a, b = random.choice([2, 3, -2, -3, 4, 5]), random.randint(-10, 10)
    new = a * a * var
    problem = (
        f"A random variable $X$ has variance ${num(var)}$. What is the variance of "
        f"${a}X {'+' if b >= 0 else '-'} {abs(b)}$?"
    )
    solution = f"${num(new)}$"
    s = Steps()
    s.step("Adding a constant doesn't change variance; multiplying by $a$ multiplies it by $a^2$.",
           rf"\operatorname{{Var}}({a}X {'+' if b >= 0 else '-'} {abs(b)}) = ({a})^2({num(var)}) = {num(new)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Probability ------------------------------------------------------------------------

@statistics_gen.stat_counting_probability.variant("at_least_one")
def _counting_at_least_one():
    """P(at least one red) when drawing without replacement, via the complement."""
    red, green = random.randint(1, 8), random.randint(2, 10)
    draws = random.randint(2, min(4, green))
    none = Fraction(math.comb(green, draws), math.comb(red + green, draws))
    answer = 1 - none
    problem = (
        f"A box contains {red + green} marbles: {red} red and {green} green. You draw {draws} without "
        f"replacement. What is the probability that at least one is red? {_FRACTION_HINT}"
    )
    solution = f"${frac_from(answer)}$"
    s = Steps()
    s.step("At least one red is the complement of no red. Count the all-green draws.",
           rf"P(\text{{no red}}) = \frac{{\binom{{{green}}}{{{draws}}}}}{{\binom{{{red + green}}}{{{draws}}}}} = {_tex(none)}")
    s.step("Subtract from $1$.", rf"1 - {_tex(none)} = {_tex(answer)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_fractions_gen.dice_sum_probability.variant("count_outcomes")
def _dice_count_outcomes(sides=6):
    """How many outcomes of two dice give a sum."""
    target = random.randint(2, 2 * sides)
    pairs = [(a, b) for a in range(1, sides + 1) for b in range(1, sides + 1) if a + b == target]
    problem = (
        f"Two fair {sides}-sided dice are rolled. In how many of the {sides * sides} equally likely "
        f"outcomes is the sum {target}?"
    )
    solution = f"{len(pairs)}"
    s = Steps()
    s.step("List the ordered pairs (first die, second die).", r",\ ".join(f"({a}, {b})" for a, b in pairs))
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_odds_probability.variant("probability_from_odds")
def _probability_from_odds():
    """Reverse: odds in favor a:b mean probability a/(a + b)."""
    a, b = random.randint(1, 9), random.randint(1, 9)
    g = math.gcd(a, b)
    a, b = a // g, b // g
    against = random.random() < 0.5
    p = Fraction(b, a + b) if against else Fraction(a, a + b)
    problem = (
        f"The odds {'against' if against else 'in favor of'} an event are ${a}:{b}$. What is the "
        f"probability that the event happens? {_FRACTION_HINT}"
    )
    solution = f"${frac_from(p)}$"
    s = Steps()
    if against:
        s.step(f"Odds against of ${a}:{b}$ mean ${a}$ ways it fails for every ${b}$ ways it happens.")
    else:
        s.step(f"Odds in favor of ${a}:{b}$ mean ${a}$ ways it happens for every ${b}$ ways it fails.")
    s.step("Probability is the ways it happens over all the ways.", rf"\frac{{{p.numerator}}}{{{a + b}}} = {_tex(p)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.binomial_distribution.variant("at_least_one")
def _binomial_at_least_one():
    """P(at least one success) = 1 - (1 - p)^n."""
    n = random.randint(2, 12)
    p = Fraction(random.randint(5, 60), 100)
    value = 1 - (1 - p) ** n
    problem = (
        f"On each of ${n}$ independent trials the probability of success is ${num(p)}$. What is the "
        f"probability of at least one success? Give your answer as a decimal rounded to the nearest "
        "thousandth."
    )
    solution = num(value)
    s = Steps()
    s.step("At least one success is the complement of no successes.",
           rf"1 - (1 - {num(p)})^{{{n}}} = 1 - {num(1 - p)}^{{{n}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_finance_gen.conditional_probability.variant("bayes_test")
def _conditional_bayes_test():
    """Bayes' rule with rates: P(condition | positive test)."""
    prev = Fraction(random.choice([1, 2, 5, 10, 20]), 100)
    sens = Fraction(random.choice([80, 90, 95, 99]), 100)
    fpr = Fraction(random.choice([1, 2, 5, 10]), 100)
    pos = prev * sens + (1 - prev) * fpr
    value = prev * sens / pos
    problem = (
        f"{num(prev * 100)}% of a population has a condition. A test is positive for {num(sens * 100)}% of "
        f"people who have it and for {num(fpr * 100)}% of people who don't. If someone tests positive, "
        "what is the probability they have the condition? Give your answer as a decimal rounded to the "
        "nearest thousandth."
    )
    solution = num(value)
    s = Steps()
    s.step("Find the probability of testing positive, from both groups.",
           rf"P(+) = {num(prev)}({num(sens)}) + {num(1 - prev)}({num(fpr)}) = {num(pos)}")
    s.step("Divide the true positives by all positives.",
           rf"P(\text{{condition}} \mid +) = \frac{{{num(prev * sens)}}}{{{num(pos)}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


# --- Percents and money -----------------------------------------------------------------

@lib_finance_gen.percentage.variant("whole_from_part")
def _percentage_whole_from_part():
    """Reverse: p% of what number is v?"""
    pct = random.choice([5, 10, 12, 15, 20, 25, 30, 40, 45, 60, 75, 80])
    whole = random.randint(2, 400)
    part = Fraction(pct * whole, 100)
    problem = f"${pct}\\%$ of what number is ${num(part)}$?"
    solution = f"{whole}"
    s = Steps()
    s.step("Write the percent as a decimal and set up the equation.", rf"{num(Fraction(pct, 100))}x = {num(part)}")
    s.step(f"Divide by ${num(Fraction(pct, 100))}$.", f"x = {whole}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.percentage_difference.variant("prices")
def _percentage_difference_prices():
    """Percentage difference in context: two stores' prices."""
    a, b = random.sample(range(10, 200), 2)
    value = Fraction(abs(a - b) * 200, a + b)
    problem = (
        f"One store sells a lamp for ${a}$ dollars and another for ${b}$ dollars. What is the percentage "
        "difference between the prices (difference divided by their average, times 100)? Round to the "
        "nearest thousandth (just the number, with no % sign)."
    )
    solution = num(value)
    s = Steps()
    s.step("Divide the difference by the average of the two prices.",
           rf"\frac{{|{a} - {b}|}}{{({a} + {b})/2}} \times 100 \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.percentage_error.variant("observed_from_error")
def _percentage_error_observed():
    """Reverse: the observed value from the exact value and the percent error."""
    exact = random.choice(range(10, 501, 10))
    pct = random.choice([2, 4, 5, 10, 15, 20, 25])
    over = random.random() < 0.5
    observed = Fraction(exact * (100 + pct if over else 100 - pct), 100)
    problem = (
        f"A measurement has a ${pct}\\%$ error compared with the exact value ${exact}$, and the "
        f"measurement was {'too high' if over else 'too low'}. What was the measured value?"
    )
    solution = num(observed)
    s = Steps()
    s.step(f"A ${pct}\\%$ error is ${num(Fraction(pct * exact, 100))}$ away from ${exact}$.",
           rf"{num(Fraction(pct, 100))} \times {exact} = {num(Fraction(pct * exact, 100))}")
    s.step("Add it if too high, subtract if too low.", f"{exact} {'+' if over else '-'} {num(Fraction(pct * exact, 100))} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.simple_interest.variant("rate_from_interest")
def _simple_interest_rate():
    """Reverse: the annual rate from the interest earned."""
    P = random.choice(range(100, 5001, 100))
    r = random.randint(1, 12)
    t = random.randint(1, 10)
    interest = P * r * t // 100
    problem = (
        f"A principal of ${P}$ dollars earns ${interest}$ dollars of simple interest in ${t}$ years. "
        "What is the annual interest rate, as a percent (just the number, with no % sign)?"
    )
    solution = f"{r}"
    s = Steps()
    s.formula("Simple interest", "I = Prt")
    s.substitute(f"{interest} = {P} \\cdot r \\cdot {t}")
    s.step("Solve for $r$ and write it as a percent.",
           rf"r = \frac{{{interest}}}{{{P} \times {t}}} = {num(Fraction(r, 100))} = {r}\%")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.compound_interest.variant("years_to_reach")
def _compound_years_to_reach():
    """The first whole year the balance passes a target (annual compounding)."""
    P = random.choice(range(500, 5001, 500))
    r = random.choice([3, 4, 5, 6, 8, 10])
    mult = random.choice([Fraction(3, 2), Fraction(2), Fraction(5, 2)])
    target = P * mult
    t = 0
    balance = Fraction(P)
    while balance <= target:
        t += 1
        balance *= Fraction(100 + r, 100)
    problem = (
        f"${P}$ dollars is invested at ${r}\\%$ interest per year, compounded annually. After how many "
        f"whole years is the balance first more than ${num(target)}$ dollars?"
    )
    solution = f"{t}"
    before = P * Fraction(100 + r, 100) ** (t - 1)
    s = Steps()
    s.step(f"Each year the balance is multiplied by ${num(Fraction(100 + r, 100))}$.",
           rf"A(t) = {P}({num(Fraction(100 + r, 100))})^t")
    s.step(f"Check the years around the target.",
           rf"A({t - 1}) \approx {num(before)}, \quad A({t}) \approx {num(balance)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.profit_loss_percent.variant("selling_price")
def _profit_selling_price():
    """Reverse: the selling price from the cost and the profit (or loss) percent."""
    cost = random.randint(20, 900)
    pct = random.choice([5, 10, 15, 20, 25, 30, 40, 50])
    profit = random.random() < 0.5
    price = Fraction(cost * (100 + pct if profit else 100 - pct), 100)
    problem = (
        f"An item costs ${cost}$ dollars to make and is sold at a ${pct}\\%$ "
        f"{'profit' if profit else 'loss'}. What is the selling price, in dollars? Round to the "
        "nearest cent if needed."
    )
    solution = num(price, 2)
    s = Steps()
    s.step(f"A {pct}% {'profit adds' if profit else 'loss subtracts'} {pct}% of the cost.",
           rf"{cost} \times {num(Fraction(100 + pct if profit else 100 - pct, 100))} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


# --- z-scores (shared by both z-score topics) --------------------------------------------

def _z_compare():
    """Which of two results is more unusual: report the higher z-score."""
    m1, s1 = random.randint(50, 90), random.randint(4, 15)
    m2, s2 = random.randint(400, 700), random.randint(40, 120)
    x1 = m1 + random.randint(-2, 3) * s1 + random.randint(0, s1)
    x2 = m2 + random.randint(-2, 3) * s2 + random.randint(0, s2)
    z1, z2 = Fraction(x1 - m1, s1), Fraction(x2 - m2, s2)
    if z1 == z2:
        x1 += 1
        z1 = Fraction(x1 - m1, s1)
    best = max(z1, z2)
    problem = (
        f"Ana scored ${x1}$ on a test with mean ${m1}$ and standard deviation ${s1}$. Ben scored ${x2}$ "
        f"on a test with mean ${m2}$ and standard deviation ${s2}$. Who did better relative to their "
        f"test? Give that student's z-score. {_ROUND}"
    )
    solution = num(best)
    s = Steps()
    s.step("Compare the z-scores, not the raw scores.",
           rf"z_A = \frac{{{x1} - {m1}}}{{{s1}}} \approx {num(z1)}, \quad z_B = \frac{{{x2} - {m2}}}{{{s2}}} \approx {num(z2)}")
    s.answer(solution)
    return problem, solution, s.done()


for _gen in (statistics_gen.stat_z_score, algebra2.alg2_z_score):
    _gen.variant("compare_two_scores")(_z_compare)


def _z_value_from_score():
    """Reverse: the raw value at a given z-score (or the SD from x, mean and z)."""
    mu, sigma = random.randint(20, 500), random.randint(2, 50)
    z = Fraction(random.randint(-30, 30), 10)
    x = mu + z * sigma
    s = Steps()
    if random.random() < 0.5:
        problem = (f"A distribution has mean ${mu}$ and standard deviation ${sigma}$. What value has a z-score "
                   f"of ${num(z)}$?")
        answer = x
        s.step("A z-score counts standard deviations from the mean.", rf"x = {mu} + ({num(z)})({sigma}) = {num(x)}")
    else:
        while z == 0:
            z = Fraction(random.randint(1, 30), 10)
            x = mu + z * sigma
        problem = (f"A value of ${num(x)}$ has a z-score of ${num(z)}$ in a distribution with mean ${mu}$. What "
                   "is the standard deviation?")
        answer = Fraction(sigma)
        s.step("Solve $z = (x - \\mu)/\\sigma$ for $\\sigma$.", rf"\sigma = \frac{{{num(x)} - {mu}}}{{{num(z)}}} = {sigma}")
    solution = num(answer)
    s.answer(solution)
    return problem, solution, s.done()


for _gen in (statistics_gen.stat_z_score, algebra2.alg2_z_score):
    _gen.variant("reverse")(_z_value_from_score)


# =============================================================================
# Further variants (beyond each topic's first new question type)
# =============================================================================

@lib_seqstats_gen.mean_median.variant("median_from_table")
def _median_from_table():
    """The median read from a frequency table."""
    values = sorted(random.sample(range(1, 30), 5))
    counts = [random.randint(1, 6) for _ in values]
    data = [v for v, c in zip(values, counts) for _ in range(c)]
    n = len(data)
    median = Fraction(data[(n - 1) // 2] + data[n // 2], 2)
    from .prealgebra_variants import _table
    table = _table(r"\text{Value}", values, r"\text{Frequency}", counts)
    problem = f"The table shows a data set. ${table}$ What is its median?"
    solution = num(median)
    s = Steps()
    s.step(f"There are {' + '.join(map(str, counts))} = {n} values in order.")
    s.step("The median is the middle value (or the average of the two middle values).",
           f"{num(median)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.data_summary.variant("variance_only")
def _variance_only():
    """Just the population variance of a small data set."""
    data = [random.randint(1, 20) for _ in range(random.randint(4, 6))]
    mean = Fraction(sum(data), len(data))
    var = sum((v - mean) ** 2 for v in data) / len(data)
    problem = f"Find the population variance of the data set {', '.join(map(str, data))}. {_ROUND}"
    solution = num(var)
    s = Steps()
    s.step("Find the mean.", rf"\mu = \frac{{{sum(data)}}}{{{len(data)}}} = {num(mean)}")
    s.step("Average the squared distances from the mean.", rf"\sigma^2 \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_correlation_coefficient.variant("r_squared")
def _correlation_r_squared():
    """r^2 is the share of the variation in y explained by the line."""
    r = Fraction(random.randint(-99, 99), 100)
    pct = r * r * 100
    problem = (
        f"A linear model has correlation $r = {num(r)}$. What percent of the variation in $y$ does the model "
        "explain? Give just the number (no % sign), rounded to the nearest thousandth if needed."
    )
    solution = num(pct)
    s = Steps()
    s.step("The coefficient of determination is $r^2$.", rf"({num(r)})^2 = {num(r * r)} = {solution}\%")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_regression_line.variant("residual")
def _regression_residual():
    """The residual of a data point: actual minus predicted."""
    m = Fraction(random.randint(-40, 40), 10)
    b = Fraction(random.randint(-100, 300), 10)
    x = random.randint(0, 20)
    y = int(m * x + b) + random.randint(-15, 15)
    residual = y - (m * x + b)
    problem = (
        f"The regression line is $\\hat{{y}} = {num(m)}x {'+' if b >= 0 else '-'} {num(abs(b))}$. What is the "
        f"residual for the data point $({x}, {y})$?"
    )
    solution = num(residual)
    s = Steps()
    s.step("Predict $\\hat{y}$ at the data point's $x$.", rf"\hat{{y}} = {num(m)}({x}) {'+' if b >= 0 else '-'} {num(abs(b))} = {num(m * x + b)}")
    s.step("Residual = actual minus predicted.", f"{y} - {num(m * x + b)} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_margin_of_error.variant("scale_sample")
def _margin_scale_sample():
    """Multiplying n by k^2 divides the margin of error by k."""
    k = random.randint(2, 5)
    problem = (
        f"A survey's sample size is multiplied by ${k * k}$ (with the same sample proportion). By what number is "
        f"the margin of error multiplied? {_FRACTION_HINT}"
    )
    solution = frac_from(Fraction(1, k))
    s = Steps()
    s.step(r"The margin of error has $\sqrt{n}$ in the denominator.", rf"\frac{{1}}{{\sqrt{{{k * k}}}}} = \frac{{1}}{{{k}}}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_sample_proportion_ci.variant("from_counts")
def _proportion_from_counts():
    """A confidence interval when the data is given as a count."""
    n = random.choice([100, 200, 250, 400, 500, 800, 1000])
    x = random.randint(n // 10, 9 * n // 10)
    z = random.choice([Fraction(1645, 1000), Fraction(196, 100), Fraction(2576, 1000)])
    p = Fraction(x, n)
    e = float(z) * math.sqrt(float(p) * (1 - float(p)) / n)
    low, high = num(float(p) - e), num(float(p) + e)
    problem = (
        f"In a survey, ${x}$ of ${n}$ people said yes. Using $z = {num(z)}$, find the confidence interval "
        "p +/- z*sqrt(p(1-p)/n) (endpoints rounded to 3 decimal places). Give your answer as (low, high)."
    )
    solution = f"({low}, {high})"
    s = Steps()
    s.step("The sample proportion is the count over the sample size.", rf"\hat p = \frac{{{x}}}{{{n}}} = {num(p)}")
    s.step("Find the margin of error.", rf"{num(z)}\sqrt{{\frac{{{num(p)}({num(1 - p)})}}{{{n}}}}} \approx {num(e)}")
    s.step("Add and subtract it.", f"({low}, {high})")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_relative_frequency.variant("joint")
def _relative_frequency_joint():
    """A joint relative frequency from a two-way table."""
    c = {key: random.randint(1, 40) for key in ("AX", "AY", "BX", "BY")}
    total = sum(c.values())
    cell = random.choice(list(c))
    value = Fraction(c[cell], total)
    problem = (
        f"A two-way table of counts: A&X: {c['AX']}, A&Y: {c['AY']}, B&X: {c['BX']}, B&Y: {c['BY']}. What is the "
        f"joint relative frequency of {cell[0]} and {cell[1]}? Give a reduced fraction a/b."
    )
    solution = f"${frac_from(value)}$"
    s = Steps()
    s.step("A joint relative frequency is one cell over the grand total.", rf"\frac{{{c[cell]}}}{{{total}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_normal_probability.variant("expected_count")
def _normal_expected_count():
    """How many of N values to expect within a range, using the normal model."""
    mu, sigma = random.randint(20, 200), random.randint(2, 30)
    n = random.choice([100, 200, 500, 1000, 2000])
    a, b = sorted(random.sample(range(-25, 26), 2))
    lo, hi = mu + Fraction(a, 10) * sigma, mu + Fraction(b, 10) * sigma
    dist = NormalDist(mu, sigma)
    count = n * (dist.cdf(float(hi)) - dist.cdf(float(lo)))
    problem = (
        f"A variable is normally distributed with mean ${mu}$ and standard deviation ${sigma}$. Out of ${n}$ "
        f"values, about how many fall between ${num(lo)}$ and ${num(hi)}$? Round to the nearest whole number."
    )
    solution = f"{math.floor(count + 0.5)}"
    s = Steps()
    s.step("Find the probability with the normal CDF.",
           rf"P({num(lo)} < X < {num(hi)}) \approx {num(dist.cdf(float(hi)) - dist.cdf(float(lo)))}")
    s.step("Multiply by the number of values and round.", rf"{n} \times {num(count / n)} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_test_statistic.variant("mean_for_z")
def _test_statistic_mean_for_z():
    """Reverse: the sample mean that gives a stated z."""
    mu0, sigma = random.randint(20, 200), random.randint(2, 30)
    n = random.choice([16, 25, 36, 49, 64, 81, 100])
    z = Fraction(random.choice([-3, -2, -1, 1, 2, 3]) * random.randint(5, 10), 5)
    xbar = mu0 + z * Fraction(sigma, math.isqrt(n))
    problem = (
        f"For a test of $\\mu = {mu0}$ with $\\sigma = {sigma}$ and $n = {n}$, what sample mean gives a test "
        f"statistic of $z = {num(z)}$? {_ROUND}"
    )
    solution = num(xbar)
    s = Steps()
    s.step("Solve the z formula for the sample mean.", rf"\bar x = \mu + z\frac{{\sigma}}{{\sqrt{{n}}}} = {mu0} + ({num(z)})\frac{{{sigma}}}{{{math.isqrt(n)}}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_discrete_variance.variant("standard_deviation")
def _discrete_sd():
    """The standard deviation of a discrete random variable."""
    values = sorted(random.sample(range(0, 11), 3))
    probs = [Fraction(random.randint(1, 5), 10) for _ in range(2)]
    while sum(probs) >= 1:
        probs = [Fraction(random.randint(1, 4), 10) for _ in range(2)]
    probs.append(1 - sum(probs))
    mean = sum(v * p for v, p in zip(values, probs))
    var = sum(p * (v - mean) ** 2 for v, p in zip(values, probs))
    sd = math.sqrt(var)
    problem = (
        f"$X$ takes the values {', '.join(map(str, values))} with probabilities "
        f"{', '.join(num(p) for p in probs)}. What is the standard deviation of $X$? {_ROUND}"
    )
    solution = num(sd)
    s = Steps()
    s.step("Find the mean.", rf"E(X) = {num(mean)}")
    s.step("Find the variance, then take the square root.", rf"\operatorname{{Var}}(X) = {num(var)}, \quad \sigma \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_fractions_gen.dice_sum_probability.variant("difference")
def _dice_difference(sides=6):
    """P(the two dice differ by d)."""
    d = random.randint(0, sides - 1)
    count = sum(1 for a in range(1, sides + 1) for b in range(1, sides + 1) if abs(a - b) == d)
    value = Fraction(count, sides * sides)
    problem = (
        f"Two fair {sides}-sided dice are rolled. What is the probability that the two numbers differ by exactly "
        f"{d}? {_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    s.step(f"Count the ordered outcomes with a difference of {d}.", f"{count} \\text{{ of }} {sides * sides}")
    s.step("Simplify.", rf"\frac{{{count}}}{{{sides * sides}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@statistics_gen.stat_odds_probability.variant("odds_against")
def _odds_against():
    """Odds against from a probability."""
    d = random.randint(2, 12)
    n = random.randint(1, d - 1)
    p = Fraction(n, d)
    problem = f"The probability of an event is ${frac_from(p)}$. Write the odds against the event in the form a:b (lowest terms)."
    solution = f"{p.denominator - p.numerator}:{p.numerator}"
    s = Steps()
    s.step("Odds against compare the ways it fails to the ways it happens.",
           f"{p.denominator - p.numerator}:{p.numerator}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.binomial_distribution.variant("expected_count")
def _binomial_expected():
    """The expected number of successes, np, or n from it."""
    n = random.randint(5, 400)
    p = Fraction(random.randint(1, 19), 20)
    s = Steps()
    if random.random() < 0.5:
        problem = f"Over ${n}$ independent trials with success probability ${num(p)}$, what is the expected number of successes?"
        solution = num(n * p)
        s.step("The mean of a binomial distribution is $np$.", rf"{n} \times {num(p)} = {solution}")
    else:
        while (n * p).denominator != 1:
            n += 1
        problem = (f"A binomial experiment has success probability ${num(p)}$ and an expected ${num(n * p)}$ "
                   "successes. How many trials are there?")
        solution = f"{n}"
        s.step("Solve $np = \\mu$ for $n$.", rf"n = \frac{{{num(n * p)}}}{{{num(p)}}} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.conditional_probability.variant("two_way_table")
def _conditional_two_way():
    """P(B | A) from a two-way table of counts."""
    c = {key: random.randint(1, 40) for key in ("AX", "AY", "BX", "BY")}
    given = random.choice(["A", "B", "X", "Y"])
    target = random.choice(["X", "Y"] if given in "AB" else ["A", "B"])
    cell = (given + target) if given in "AB" else (target + given)
    total = sum(v for k, v in c.items() if given in k)
    value = c[cell] / total
    problem = (
        f"A two-way table of counts: A&X: {c['AX']}, A&Y: {c['AY']}, B&X: {c['BX']}, B&Y: {c['BY']}. Find "
        f"P({target} | {given}). Give your answer as a decimal rounded to the nearest thousandth."
    )
    solution = num(value)
    s = Steps()
    s.step(f"Restrict to {given}: there are ${total}$ of them.", rf"P({target} \mid {given}) = \frac{{{c[cell]}}}{{{total}}} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.percentage.variant("tip")
def _percentage_tip():
    """A tip as a percent of a bill."""
    bill = Fraction(random.randint(800, 15000), 100)
    pct = random.choice([15, 18, 20, 22, 25])
    tip = bill * pct / 100
    problem = (
        f"A restaurant bill is ${num(bill, 2)}$ dollars. How much is a ${pct}\\%$ tip, in dollars? Round to the "
        "nearest cent."
    )
    solution = num(tip, 2)
    s = Steps()
    s.step("Multiply the bill by the percent as a decimal.", rf"{num(bill, 2)} \times {num(Fraction(pct, 100))} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.simple_interest.variant("total_amount")
def _simple_interest_total():
    """The total balance (principal plus simple interest)."""
    P = random.choice(range(100, 5001, 50))
    r, t = random.randint(1, 12), random.randint(1, 10)
    total = P + Fraction(P * r * t, 100)
    problem = (
        f"${P}$ dollars earns ${r}\\%$ simple interest per year. What is the total balance after ${t}$ years, in "
        "dollars?"
    )
    solution = num(total)
    s = Steps()
    s.step("Find the interest.", rf"I = {P} \times {num(Fraction(r, 100))} \times {t} = {num(total - P)}")
    s.step("Add it to the principal.", f"{P} + {num(total - P)} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.compound_interest.variant("monthly")
def _compound_monthly():
    """Monthly compounding: A = P(1 + r/12)^(12t)."""
    P = random.choice(range(500, 10001, 500))
    r = random.choice([2, 3, 4, 5, 6])
    t = random.randint(1, 10)
    amount = P * (1 + r / 1200) ** (12 * t)
    problem = (
        f"${P}$ dollars is invested at ${r}\\%$ annual interest, compounded monthly. What is the balance after "
        f"${t}$ years, in dollars? Round to the nearest cent."
    )
    solution = num(amount, 2)
    s = Steps()
    s.formula("Monthly compounding", rf"A = P\left(1 + \frac{{r}}{{12}}\right)^{{12t}} = {P}\left(1 + \frac{{{num(Fraction(r, 100))}}}{{12}}\right)^{{{12 * t}}}")
    s.step("Evaluate.", rf"A \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_finance_gen.profit_loss_percent.variant("markup_then_discount")
def _profit_markup_discount():
    """Marked up, then discounted: the overall profit or loss percent."""
    up = random.choice([20, 25, 40, 50, 60, 100])
    down = random.choice([10, 20, 25, 30, 40, 50])
    factor = Fraction(100 + up, 100) * Fraction(100 - down, 100)
    change = (factor - 1) * 100
    problem = (
        f"A store marks an item up ${up}\\%$ above cost, then sells it at ${down}\\%$ off the marked price. What is "
        "the profit as a percent of cost? (A loss is negative.) Give just the number, rounded to the nearest "
        "thousandth if needed."
    )
    solution = num(change)
    s = Steps()
    s.step("Multiply the two changes as factors.", rf"{num(Fraction(100 + up, 100))} \times {num(Fraction(100 - down, 100))} = {num(factor)}")
    s.step("Subtract $1$ and convert to a percent.", rf"({num(factor)} - 1) \times 100 = {solution}")
    s.answer(solution)
    return problem, solution, s.done()
