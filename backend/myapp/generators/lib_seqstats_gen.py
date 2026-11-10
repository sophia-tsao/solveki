"""Solveki-local overrides for broken ``mathgenerator`` sequence / integral /
statistics generators (assignment group G5).

Each generator here is named to *exactly* match a stock ``mathgenerator``
generator so ``_make_problem_for_topic`` (which resolves ``LOCAL_GENERATORS``
before the library) picks up our typeable version instead. The library
versions are unusable in the answer box (which does an exact/``parseFloat``
match) for a mix of reasons:

* ``mean_median`` has typos in its problem ("arithmatic", "mdian") and answers
  with a full English sentence rather than a typeable value.
* ``data_summary`` emits raw 16-digit floats and never says whether the
  statistics are the population or sample versions.
* ``arithmetic_progression_sum`` answers with a trailing ``.0`` (``78267.0``).
* ``geometric_progression`` returns a verbose multi-part sentence.
* ``definite_integral`` emits long truncated decimals like ``89.6667``.
* ``power_rule_integration`` returns untypeable ``\\frac{3}{8}x^{9}+...+C``.
* ``confidence_interval`` returns a tuple of 16-digit floats, sometimes with
  the endpoints reversed (high, low).
* ``quadratic_equation`` answers with brace set notation ``{-0.67, -9.83}`` and
  gives no instruction about format or ordering.

Our versions return plain integers, reduced ``a/b`` fractions, ordered pairs, or
comma-separated lists, and state the required format/order in the problem.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._variants import with_variants
from ._format import num as _num, frac_from as _frac_from
from ._steps import Steps, paren, tex_frac


def _median(values):
    """Median of a list; mean of the two middle values when the count is even."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _is_exact(value):
    """Whether `value` needs no rounding to be shown to 3 decimal places."""
    return abs(float(value) - round(float(value), 3)) < 1e-12


def _eq(value):
    """`=` when `value` shows exactly to 3 decimals, else `\\approx`."""
    return "=" if _is_exact(value) else r"\approx"


def _ftex(value):
    """A Fraction as LaTeX: an integer, or a reduced ``\\frac`` (sign in front)."""
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


def _x_term(coef, exp):
    """LaTeX for ``coef x^exp`` with a Fraction coefficient (1 is dropped)."""
    power = "x" if exp == 1 else f"x^{{{exp}}}"
    if coef == 1:
        return power
    return f"{_ftex(coef)}{power}"


@register
@with_variants
def mean_median(min_val=1, max_val=100):
    r"""Mean and Median of a Series

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given the series 9, 16, 18, 33, 58. Find the mean and median. | 26.8, 18 |

    Overrides the stock ``mean_median``, which misspells "arithmetic" and
    "median" and answers with a full sentence. We fix the typos and return two
    typeable numbers.
    """
    n = random.choice([5, 6, 7, 8, 9, 10])
    data = [random.randint(min_val, max_val) for _ in range(n)]
    mean = sum(data) / n
    median = _median(data)
    problem = (
        f"Given the series of numbers: {', '.join(str(v) for v in data)}. "
        "Find the arithmetic mean and the median of the series. "
        "Give your answer as mean, median, both rounded to the nearest "
        "thousandth."
    )
    solution = f"{_num(mean)}, {_num(median)}"

    total = sum(data)
    ordered = sorted(data)
    mid = n // 2
    s = Steps()
    s.step(f"To find the mean, first add the {n} values.",
           " + ".join(str(v) for v in data) + f" = {total}")
    s.step(f"Then divide the sum by the number of values, {n}.",
           rf"\text{{mean}} = \frac{{{total}}}{{{n}}} {_eq(mean)} {_num(mean)}")
    s.step("To find the median, put the values in order from least to greatest.",
           ", ".join(str(v) for v in ordered))
    if n % 2 == 1:
        s.step(f"There are {n} values, so the median is the middle "
               f"({_ordinal(mid + 1)}) value: ${_num(median)}$.")
    else:
        s.step(f"There are {n} values, so there are two middle values, the "
               f"{_ordinal(mid)} and {_ordinal(mid + 1)}. The median is their mean.",
               rf"\text{{median}} = \frac{{{ordered[mid - 1]} + {ordered[mid]}}}{{2}}"
               f" = {_num(median)}")
    s.answer(solution, lead="The mean and median are" if _is_exact(mean)
             else "Rounded to the nearest thousandth, the mean and median are")
    return problem, solution, s.done()


@register
@with_variants
def data_summary(min_val=1, max_val=50):
    r"""Mean, Standard Deviation and Variance of a Data Set

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the population mean, standard deviation and variance of ... | 25, 12.452, 155.067 |

    Overrides the stock ``data_summary``, which emits 16-digit floats and never
    states whether the statistics are the population or sample versions. We use
    the population versions (divide by N), state so explicitly, and round every
    number to three decimals.
    """
    n = random.choice([10, 12, 15])
    data = [random.randint(min_val, max_val) for _ in range(n)]
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    std_dev = math.sqrt(variance)
    problem = (
        f"For the data set: {', '.join(str(v) for v in data)}. "
        "Find the population mean, the population standard deviation, and the "
        "population variance (the standard deviation and variance divide by N, "
        "the number of values). Give your answer as mean, standard deviation, "
        "variance, each rounded to the nearest thousandth."
    )
    solution = f"{_num(mean)}, {_num(std_dev)}, {_num(variance)}"

    total = sum(data)
    exact_ss = sum((x - Fraction(total, n)) ** 2 for x in data)
    s = Steps()
    s.step(f"Add the {n} values: their sum is ${total}$. Divide by $N = {n}$ to get "
           "the mean.",
           rf"\mu = \frac{{{total}}}{{{n}}} {_eq(mean)} {_num(mean)}")
    s.formula("The population variance", r"\sigma^2 = \frac{\sum (x - \mu)^2}{N}")
    s.step(f"Subtract the mean from each value, square the result, and add all "
           f"{n} squares.",
           rf"\sum (x - \mu)^2 = {_ftex(exact_ss)}")
    # Keep the sum of squares exact (a fraction) here, so the variance and
    # standard deviation are rounded only once, at the end.
    s.step("Divide by $N$ to get the variance.",
           rf"\sigma^2 = {_ftex(exact_ss / n)} {_eq(variance)} {_num(variance)}")
    s.step("The standard deviation is the square root of the unrounded variance.",
           rf"\sigma = \sqrt{{{_ftex(exact_ss / n)}}} {_eq(std_dev)} {_num(std_dev)}")
    s.answer(solution, lead="As mean, standard deviation, variance, each rounded "
             "to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def arithmetic_progression_sum(min_a=-50, max_a=50, min_d=-12, max_d=12):
    r"""Sum of an Arithmetic Progression

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Sum of the first 12 terms with first term 45, common difference -66. | -3816 |

    Overrides the stock ``arithmetic_progression_sum``, whose answer carries a
    trailing ``.0``. The sum of an integer AP is always an integer; we return it
    as a plain integer.
    """
    a = random.randint(min_a, max_a)
    d = random.randint(min_d, max_d)
    n = random.randint(5, 60)
    # S_n = n/2 * (2a + (n - 1) d); always integral for integer a, d, n.
    total = n * (2 * a + (n - 1) * d) // 2
    problem = (
        f"Find the sum of the first {n} terms of an arithmetic progression "
        f"with first term {a} and common difference {d}. "
        "Give your answer as a single integer."
    )
    solution = _num(total)

    inner = 2 * a + (n - 1) * d
    s = Steps()
    s.formula("The sum of the first $n$ terms of an arithmetic progression",
              r"S_n = \frac{n}{2}\left(2a + (n - 1)d\right)")
    s.substitute(
        rf"S_{{{n}}} = \frac{{{n}}}{{2}}\left(2 \cdot {paren(a)} + {n - 1} \cdot {paren(d)}\right)",
        text=f"Substitute $n = {n}$, $a = {a}$, and $d = {d}$.",
    )
    s.step("Simplify inside the parentheses.",
           rf"{2 * a} + {paren((n - 1) * d)} = {inner}")
    s.step(f"Multiply by $\\frac{{{n}}}{{2}}$.",
           rf"S_{{{n}}} = \frac{{{n} \cdot {paren(inner)}}}{{2}} = "
           rf"\frac{{{n * inner}}}{{2}} = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def geometric_progression(min_a=1, max_a=9, min_r=2, max_r=5):
    r"""Nth Term of a Geometric Progression

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | GP with first term 3 and common ratio 2. Find the 5th term. | 48 |

    Overrides the stock ``geometric_progression``, which returns a verbose
    multi-part sentence. We ask for one thing -- the nth term, a * r^(n-1) --
    and answer with a single integer.
    """
    a = random.randint(min_a, max_a)
    r = random.randint(min_r, max_r)
    n = random.randint(3, 7)
    term = a * r ** (n - 1)
    problem = (
        f"A geometric progression has first term a = {a} and common ratio "
        f"r = {r}. Find the {_ordinal(n)} term (a * r^(n-1)). "
        "Give your answer as a single integer."
    )
    solution = _num(term)

    s = Steps()
    s.formula("The $n$th term of a geometric progression", r"a_n = a \cdot r^{n - 1}")
    s.substitute(rf"a_{{{n}}} = {a} \cdot {r}^{{{n} - 1}} = {a} \cdot {r}^{{{n - 1}}}",
                 text=f"Substitute $a = {a}$, $r = {r}$, and $n = {n}$.")
    s.step(f"Evaluate the power: ${r}^{{{n - 1}}} = {r ** (n - 1)}$. Then multiply.",
           rf"a_{{{n}}} = {a} \cdot {r ** (n - 1)} = {term}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def definite_integral(min_coef=1, max_coef=20):
    r"""Definite Integral of a Quadratic

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Integral of 17x^2 + 72x + 97 from x = 0 to x = 1. | 416/3 |

    Overrides the stock ``definite_integral``, which emits truncated decimals
    like ``89.6667``. The exact value is rational, so we return it as a reduced
    ``a/b`` fraction (or an integer).
    """
    p = random.randint(min_coef, max_coef)
    q = random.randint(min_coef, max_coef)
    s = random.randint(min_coef, max_coef)
    a = random.randint(-3, 2)
    b = random.randint(a + 1, 4)

    def antideriv(x):
        # Antiderivative of p x^2 + q x + s is p/3 x^3 + q/2 x^2 + s x.
        x = Fraction(x)
        return Fraction(p, 3) * x ** 3 + Fraction(q, 2) * x ** 2 + s * x

    value = antideriv(b) - antideriv(a)
    problem = (
        f"Evaluate the definite integral of {p}x^2 + {q}x + {s} "
        f"from x = {a} to x = {b}. "
        "Give your answer as a fraction in lowest terms in the form a/b, "
        "or an integer."
    )
    solution = _frac_from(value)

    f_tex = " + ".join(
        _x_term(coef, exp)
        for coef, exp in ((Fraction(p, 3), 3), (Fraction(q, 2), 2), (Fraction(s), 1))
    )
    upper, lower = antideriv(b), antideriv(a)
    lower_tex = _ftex(lower)
    if lower < 0:
        lower_tex = rf"\left({lower_tex}\right)"
    st = Steps()
    st.step(r"Find an antiderivative with the power rule "
            r"$\int x^n\,dx = \frac{x^{n+1}}{n+1}$.",
            rf"F(x) = {f_tex}")
    st.step("By the Fundamental Theorem of Calculus, the integral is $F$ at the "
            "upper limit minus $F$ at the lower limit.",
            rf"\int_{{{a}}}^{{{b}}} \left({p}x^2 + {q}x + {s}\right)dx = F({b}) - F({a})")
    st.step(f"Evaluate $F$ at $x = {b}$ and $x = {a}$.",
            rf"F({b}) = {_ftex(upper)}, \quad F({a}) = {_ftex(lower)}")
    st.step("Subtract.", rf"{_ftex(upper)} - {lower_tex} = {_ftex(value)}")
    st.answer(solution, lead="As an integer or a fraction in lowest terms, the answer is")
    return problem, solution, st.done()


@register
@with_variants
def power_rule_integration(max_terms=3, max_coef=9, max_exp=5):
    r"""Indefinite Integral of a Polynomial (Power Rule)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Antiderivative of 3x. | 3/2x^2 + C |

    Overrides the stock ``power_rule_integration``, which returns untypeable
    ``\frac{a}{b}x^{n}+...+C``. We integrate a short polynomial and write the
    antiderivative in typeable ASCII: descending powers, coefficients as
    integers or reduced ``a/b`` fractions, powers as ``x^n``, ending in ``+ C``.
    """
    count = random.randint(1, max_terms)
    exps = random.sample(range(1, max_exp + 1), count)
    # {exponent: coefficient} of the integrand.
    integrand = {e: random.randint(1, max_coef) for e in exps}

    def render_integrand_term(exp, coef):
        shown = "" if coef == 1 else coef  # "x", not "1x"
        return f"{shown}x" if exp == 1 else f"{shown}x^{exp}"

    integrand_str = " + ".join(
        render_integrand_term(e, integrand[e]) for e in sorted(integrand, reverse=True)
    )

    # Integrate: c x^e -> c/(e+1) x^(e+1). New exponents are all >= 2.
    antideriv = {e + 1: Fraction(c, e + 1) for e, c in integrand.items()}
    terms = [
        f"{'' if coef == 1 else _frac_from(coef)}x^{ne}"
        for ne, coef in sorted(antideriv.items(), reverse=True)
    ]
    solution = " + ".join(terms) + " + C"

    problem = (
        f"Find the indefinite integral (antiderivative) of {integrand_str}. "
        "Write the terms in descending powers of x, with coefficients as "
        "integers or reduced fractions a/b and powers written as x^n, ending "
        "with + C (for example, 1/2x^2 + 3x + C)."
    )

    def term_integral(exp, coef):
        power = "x" if exp == 1 else f"x^{{{exp}}}"
        result = rf"\int {'' if coef == 1 else coef}{power}\,dx = \frac{{{coef}}}{{{exp + 1}}}x^{{{exp + 1}}}"
        if math.gcd(coef, exp + 1) > 1:  # the coefficient reduces
            result += f" = {_x_term(Fraction(coef, exp + 1), exp + 1)}"
        return result

    s = Steps()
    s.formula("The power rule for integrals",
              r"\int c\,x^n\,dx = \frac{c}{n + 1}x^{n + 1} + C")
    s.step("Integrate each term: add 1 to the power, then divide by the new power.",
           r", \quad ".join(term_integral(e, integrand[e])
                            for e in sorted(integrand, reverse=True)))
    s.step("Add the results and the constant of integration $C$.",
           " + ".join(_x_term(coef, ne) for ne, coef in sorted(antideriv.items(), reverse=True))
           + " + C")
    s.answer(solution, lead="Written in the requested form, the answer is")
    return problem, solution, s.done()


# Confidence level -> two-sided normal critical value.
_Z_CRITICAL = {80: 1.282, 90: 1.645, 95: 1.96, 99: 2.576}


@register
@with_variants
def confidence_interval():
    r"""Confidence Interval for a Mean

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | mean 50, std 8, n = 25, z = 1.96. | (46.864, 53.136) |

    Overrides the stock ``confidence_interval``, which returns a tuple of
    16-digit floats sometimes in reversed (high, low) order. We compute
    mean +/- z * s/sqrt(n), return the endpoints low < high rounded to three
    decimals, and state the format.
    """
    mean = random.randint(20, 100)
    s = random.randint(2, 30)
    n = random.randint(5, 200)
    confidence = random.choice(sorted(_Z_CRITICAL))
    z = _Z_CRITICAL[confidence]

    margin = z * s / math.sqrt(n)
    low = mean - margin
    high = mean + margin
    problem = (
        f"A sample has mean {mean}, standard deviation {s}, and size n = {n}. "
        f"Using the critical value z = {_num(z)} (a {confidence}% confidence "
        "level), find the confidence interval mean +/- z * s / sqrt(n). "
        "Format your answer as (low, high) rounded to the nearest thousandth."
    )
    solution = f"({_num(low)}, {_num(high)})"

    steps = Steps()
    steps.formula("A confidence interval for a mean",
                  r"\bar{x} \pm E, \quad E = z \cdot \frac{s}{\sqrt{n}}")
    steps.step("Find the margin of error.",
               rf"E = {_num(z)} \cdot \frac{{{s}}}{{\sqrt{{{n}}}}} {_eq(margin)} {_num(margin)}")
    steps.step("Subtract and add the margin of error (keep its unrounded value).",
               rf"{mean} - E {_eq(low)} {_num(low)}, \quad {mean} + E {_eq(high)} {_num(high)}")
    steps.answer(solution, lead="As (low, high), rounded to the nearest thousandth, "
                 "the answer is")
    return problem, solution, steps.done()


@register
@with_variants
def quadratic_equation(max_num=6, max_den=3):
    r"""Zeros of a Quadratic Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve 2x^2 - x - 1 = 0. | -1/2, 1 |

    Overrides the stock ``quadratic_equation``, which answers with brace set
    notation and no instruction. We build the quadratic from two rational roots
    so the zeros are always rational, and return them as a comma-separated list,
    smaller first, each an integer or reduced ``a/b`` fraction.
    """
    def make_root():
        d = random.randint(1, max_den)
        num = random.choice([v for v in range(-max_num, max_num + 1) if v != 0])
        return Fraction(num, d)

    while True:
        r1 = make_root()
        r2 = make_root()
        # Clear denominators to integer coefficients: a x^2 + b x + c.
        a = r1.denominator * r2.denominator
        b = -(a * (r1 + r2))
        c = a * r1 * r2
        b = int(b)
        c = int(c)
        # Keep a clean, fully three-term equation (nonzero b and c) with two
        # distinct roots.
        if r1 != r2 and b != 0 and c != 0:
            break

    lo, hi = sorted((r1, r2))

    b_sign, b_abs = ("+", b) if b >= 0 else ("-", -b)
    c_sign, c_abs = ("+", c) if c >= 0 else ("-", -c)
    equation = f"{a}x^2 {b_sign} {b_abs}x {c_sign} {c_abs} = 0"
    problem = (
        f"Solve the quadratic equation {equation}. "
        "Give the two solutions as a comma-separated list, smaller first, "
        "each an integer or reduced fraction a/b (for example, -1/2, 1)."
    )
    solution = f"{_frac_from(lo)}, {_frac_from(hi)}"

    def linear(root):
        # The factor that is zero at `root`: (d x - n) for root = n/d.
        coef = "" if root.denominator == 1 else str(root.denominator)
        sign = "-" if root.numerator > 0 else "+"
        return f"{coef}x {sign} {abs(root.numerator)}"

    s = Steps()
    s.step("Factor the left side into two binomials (multiply them out to check).",
           f"({linear(lo)})({linear(hi)}) = 0")
    s.step("By the zero product property, one of the factors must be zero.",
           rf"{linear(lo)} = 0 \quad \text{{or}} \quad {linear(hi)} = 0")
    s.step("Solve each equation for $x$.",
           rf"x = {_ftex(lo)} \quad \text{{or}} \quad x = {_ftex(hi)}")
    s.answer(solution, lead="Listed smaller first, the answer is")
    return problem, solution, s.done()
