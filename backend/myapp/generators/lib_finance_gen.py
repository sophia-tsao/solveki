"""Solveki-local overrides for ``mathgenerator`` percentage/finance generators.

Group G4. Each generator's ``__name__`` deliberately matches a stock
``mathgenerator`` generator so ``_make_problem_for_topic`` (which resolves
``LOCAL_GENERATORS`` before the library) uses ours instead. The stock versions
are unusable here for the usual reasons: they round non-integer answers to two
decimals without ever telling the student what precision to type, and several
staple a stray ``%`` / ``\\%`` sign onto the answer (``36.92\\%``) or return a
percentage where the student can't tell whether a percent sign is expected --
both break the exact / ``parseFloat`` match of the answer box.

Our versions round every non-integer answer to three decimals, STATE that in
the problem, and return a bare typeable number: no ``%`` sign, no LaTeX. Where
the stock problem is ambiguous about what quantity is wanted (compound interest,
conditional probability, binomial distribution) we pin down and state a single
clear definition.

Every generator is zero-required-arg, returns a ``(problem, solution)`` pair,
and produces a typeable solution via :func:`num` (a plain integer or a decimal
to at most three places).
"""
import math
import random

from ._registry import register
from ._format import num
from ._steps import Steps


def _is_exact(value):
    """Whether `value` needs no rounding to be shown to 3 decimal places."""
    return abs(value - round(value, 3)) < 1e-12


def _eq(value):
    """`=` when `value` shows exactly to 3 decimals, else `\\approx`."""
    return "=" if _is_exact(value) else r"\approx"


def _lead(value):
    """The `Steps.answer` lead: mention rounding only when it happened."""
    if _is_exact(value):
        return "The answer is"
    return "Rounded to the nearest thousandth, the answer is"


_ROUND_HINT = "Round your answer to the nearest thousandth."
# For quantities that are conceptually a percentage: keep the % sign out of the
# answer so the exact/parseFloat match stays clean.
_PERCENT_HINT = (
    "Give your answer as a percentage rounded to the nearest thousandth "
    "(just the number, with no % sign)."
)
_PROB_HINT = "Give your answer as a decimal rounded to the nearest thousandth."


@register
def percentage():
    r"""Percentage of a Number

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is $18\%$ of $73$? | 13.14 |

    Overrides the stock generator, which rounds to 2dp and states no format.
    Answer is ``p/100 * n``, often non-integer.
    """
    p = random.randint(1, 99)
    n = random.randint(1, 99)
    value = p / 100 * n
    problem = f"What is ${p}\\%$ of ${n}$? {_ROUND_HINT}"
    solution = num(value)

    rate = num(p / 100)
    s = Steps()
    s.step("Write the percent as a decimal by dividing by $100$.",
           rf"{p}\% = \frac{{{p}}}{{100}} = {rate}")
    s.step(f"Multiply the decimal by ${n}$.", rf"{rate} \times {n} = {solution}")
    s.answer(solution, lead=_lead(value))
    return problem, solution, s.done()


@register
def percentage_difference():
    r"""Percentage Difference Between Two Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is the percentage difference between $34$ and $145$? | 124.022 |

    Overrides the stock generator, which rounds to 2dp and appends a bare ``%``
    to the answer. Percentage difference is ``|a - b| / ((a + b) / 2) * 100``.
    Both numbers are positive so the denominator is never zero.
    """
    a = random.randint(1, 200)
    b = random.randint(1, 200)
    value = abs(a - b) / ((a + b) / 2) * 100
    problem = (
        f"What is the percentage difference between ${a}$ and ${b}$? "
        f"{_PERCENT_HINT}"
    )
    solution = num(value)

    diff = abs(a - b)
    average = num((a + b) / 2)
    s = Steps()
    s.formula("Percentage difference compares the gap between two numbers to "
              "their average. The formula",
              r"\text{percentage difference} = \frac{|a - b|}{(a + b) / 2} \times 100")
    s.step("Find the difference between the numbers and their average.",
           rf"|{a} - {b}| = {diff}, \quad \frac{{{a} + {b}}}{{2}} = {average}")
    s.step("Divide the difference by the average, then multiply by $100$.",
           rf"\frac{{{diff}}}{{{average}}} \times 100 {_eq(value)} {solution}")
    s.answer(solution, lead=_lead(value))
    return problem, solution, s.done()


@register
def percentage_error():
    r"""Percentage Error

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the percentage error when the observed value is $66$ and the exact value is $45$. | 46.667 |

    Overrides the stock generator, which rounds to 2dp and appends ``\\%`` to
    the answer. Percentage error is ``|observed - exact| / |exact| * 100``. The
    exact value is kept non-zero so the denominator is defined.
    """
    observed = random.randint(1, 200)
    exact = random.randint(1, 200)
    value = abs(observed - exact) / abs(exact) * 100
    problem = (
        f"Find the percentage error when the observed value is ${observed}$ "
        f"and the exact value is ${exact}$. {_PERCENT_HINT}"
    )
    solution = num(value)

    error = abs(observed - exact)
    s = Steps()
    s.formula("Percentage error compares how far off a measurement is to the "
              "exact value. The formula",
              r"\text{percentage error} = \frac{|\text{observed} - \text{exact}|}"
              r"{|\text{exact}|} \times 100")
    s.step("Find how far the observed value is from the exact value.",
           rf"|{observed} - {exact}| = {error}")
    s.step(f"Divide by the exact value, ${exact}$, then multiply by $100$.",
           rf"\frac{{{error}}}{{{exact}}} \times 100 {_eq(value)} {solution}")
    s.answer(solution, lead=_lead(value))
    return problem, solution, s.done()


@register
def simple_interest():
    r"""Simple Interest

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the simple interest on a principal of $3201$ dollars at a rate of $10\%$ per year for $2$ years. | 640.2 |

    Overrides the stock generator, which rounds to 2dp and states no format.
    Simple interest is ``P * R * T / 100``.
    """
    p = random.randint(100, 10000)
    r = random.randint(1, 15)
    t = random.randint(1, 20)
    value = p * r * t / 100
    problem = (
        f"Find the simple interest on a principal of ${p}$ dollars at a rate "
        f"of ${r}\\%$ per year for ${t}$ years. {_ROUND_HINT}"
    )
    solution = num(value)

    rate = num(r / 100)
    s = Steps()
    s.formula("Simple interest is principal times rate times time. The formula",
              r"I = P \times r \times t")
    s.step(f"Write the rate as a decimal: ${r}\\% = {rate}$.")
    s.substitute(rf"I = {p} \times {rate} \times {t} = {solution}",
                 text=f"Substitute $P = {p}$, $r = {rate}$, and $t = {t}$, then multiply.")
    s.answer(solution, lead="The simple interest, in dollars, is")
    return problem, solution, s.done()


@register
def compound_interest():
    r"""Compound Interest (Total Amount)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the total amount when a principal of $3201$ dollars is invested at a rate of $10\%$ per year, compounded annually, for $2$ years. | 3873.21 |

    Overrides the stock generator, which rounds to 2dp and states no format.
    Matching the stock definition, we return the TOTAL amount (principal plus
    interest) after annual compounding: ``P * (1 + R/100)^T``. The problem
    states explicitly that the total amount is wanted.
    """
    p = random.randint(100, 10000)
    r = random.randint(1, 15)
    t = random.randint(1, 20)
    value = p * (1 + r / 100) ** t
    problem = (
        f"Find the total amount when a principal of ${p}$ dollars is invested "
        f"at a rate of ${r}\\%$ per year, compounded annually, for ${t}$ "
        f"years. {_ROUND_HINT}"
    )
    solution = num(value)

    rate = num(r / 100)
    s = Steps()
    s.formula("The total amount with annual compounding", r"A = P(1 + r)^t")
    s.step(f"Write the rate as a decimal: ${r}\\% = {rate}$.")
    s.substitute(rf"A = {p}(1 + {rate})^{{{t}}} = {p}({num(1 + r / 100)})^{{{t}}}",
                 text=f"Substitute $P = {p}$, $r = {rate}$, and $t = {t}$.")
    s.step("Evaluate the power, then multiply by the principal. Keep full "
           "precision until the end.",
           rf"A {_eq(value)} {solution}")
    if _is_exact(value):
        lead = "The total amount in dollars is"
    else:
        lead = "Rounded to the nearest thousandth, the total amount in dollars is"
    s.answer(solution, lead=lead)
    return problem, solution, s.done()


@register
def profit_loss_percent():
    r"""Profit or Loss Percent

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | An item has a cost price of $138$ and a sell price of $583$. Find the profit or loss as a percentage of the cost price. | 322.464 |

    Overrides the stock generator, which rounds to 2dp and gives no format. The
    profit-or-loss percent is ``|sell - cost| / cost * 100``, measured against
    the cost price (a single non-negative number either way).
    """
    cost = random.randint(1, 1000)
    sell = random.randint(1, 1000)
    value = abs(sell - cost) / cost * 100
    kind = "profit" if sell >= cost else "loss"
    problem = (
        f"An item has a cost price of ${cost}$ and a sell price of ${sell}$. "
        f"This is a {kind}. Find the {kind} as a percentage of the cost "
        f"price. {_PERCENT_HINT}"
    )
    solution = num(value)

    amount = abs(sell - cost)
    s = Steps()
    if kind == "profit":
        s.step("The item sold for at least what it cost, so subtract the cost "
               "price from the sell price to find the profit.",
               rf"\text{{profit}} = {sell} - {cost} = {amount}")
    else:
        s.step("The item sold for less than it cost, so subtract the sell price "
               "from the cost price to find the loss.",
               rf"\text{{loss}} = {cost} - {sell} = {amount}")
    s.formula(f"The {kind} percent",
              rf"\text{{{kind} percent}} = \frac{{\text{{{kind}}}}}{{\text{{cost price}}}} \times 100")
    s.substitute(rf"\frac{{{amount}}}{{{cost}}} \times 100 {_eq(value)} {solution}",
                 text="Substitute and simplify.")
    s.answer(solution, lead=_lead(value))
    return problem, solution, s.done()


@register
def conditional_probability():
    r"""Conditional Probability P(A | B)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | In a survey, $40$ people said they exercise, and of those, $14$ also said they eat healthily. If one of the people who exercise is chosen at random, what is the probability they also eat healthily? | 0.35 |

    Overrides the stock generator, whose Bayes-theorem problem returns a
    percentage with a trailing ``%`` and rounds to 2dp. We pose a clean
    frequency-based conditional probability ``P(A | B) = count(A and B) /
    count(B)`` and return it as a decimal probability in [0, 1].
    """
    b_count = random.randint(2, 50)
    ab_count = random.randint(0, b_count)
    value = ab_count / b_count
    problem = (
        f"In a survey, ${b_count}$ people said they exercise, and of those, "
        f"${ab_count}$ also said they eat healthily. If one of the people who "
        f"exercise is chosen at random, what is the probability they also eat "
        f"healthily? {_PROB_HINT}"
    )
    solution = num(value)

    s = Steps()
    s.step(f"The person is chosen only from the ${b_count}$ who exercise, so those "
           "people are the whole sample space.")
    s.formula("The conditional probability",
              r"P(\text{healthy} \mid \text{exercise}) = "
              r"\frac{\text{number who exercise and eat healthily}}{\text{number who exercise}}")
    s.substitute(rf"P = \frac{{{ab_count}}}{{{b_count}}} {_eq(value)} {solution}",
                 text="Substitute the counts and divide.")
    s.answer(solution, lead=_lead(value))
    return problem, solution, s.done()


@register
def binomial_distribution():
    r"""Binomial Distribution P(X = k)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | On each of $10$ independent trials the probability of success is $0.35$. What is the probability of exactly $4$ successes? | 0.238 |

    Overrides the stock generator, which returns a cumulative percentage
    (``P(X <= k) * 100``) rounded to 2dp with no stated format. We pin down the
    single clearest definition -- the probability of EXACTLY ``k`` successes --
    ``C(n, k) * p^k * (1 - p)^(n - k)`` -- and return it as a decimal in [0, 1].
    The success probability is a clean two-decimal value.
    """
    n = random.randint(1, 15)
    k = random.randint(0, n)
    p = random.randint(5, 95) / 100
    value = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
    problem = (
        f"On each of ${n}$ independent trials the probability of success is "
        f"${num(p)}$. What is the probability of exactly ${k}$ successes? "
        f"{_PROB_HINT}"
    )
    solution = num(value)

    q = num(1 - p)
    s = Steps()
    s.formula("The binomial probability of exactly $k$ successes",
              r"P(X = k) = \binom{n}{k} p^k (1 - p)^{n - k}")
    s.substitute(rf"P(X = {k}) = \binom{{{n}}}{{{k}}} ({num(p)})^{{{k}}} ({q})^{{{n - k}}}",
                 text=f"Substitute $n = {n}$, $k = {k}$, and $p = {num(p)}$, "
                      f"so $1 - p = {q}$.")
    s.step(f"Count the arrangements: $\\binom{{{n}}}{{{k}}} = {math.comb(n, k)}$.",
           rf"P(X = {k}) = {math.comb(n, k)} \cdot ({num(p)})^{{{k}}} ({q})^{{{n - k}}}")
    s.step("Evaluate the powers and multiply, keeping full precision until the end.",
           rf"P(X = {k}) {_eq(value)} {solution}")
    s.answer(solution, lead=_lead(value))
    return problem, solution, s.done()
