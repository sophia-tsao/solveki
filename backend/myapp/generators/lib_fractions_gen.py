"""Solveki-local overrides for broken ``mathgenerator`` fraction/factor generators.

Each generator here is named to *exactly* match a stock ``mathgenerator``
generator so ``_make_problem_for_topic`` (which resolves ``LOCAL_GENERATORS``
before the library) picks up our typeable version instead. The library
versions are unusable in the answer box (which does an exact/``parseFloat``
match) for a mix of reasons:

* ``common_factors`` / ``factors`` return Python list literals like
  ``[1, 2, 4]`` — untypeable bracket notation.
* ``fraction_multiplication`` / ``divide_fractions`` return ``\\frac{a}{b}``
  (often unreduced) — untypeable LaTeX.
* ``greatest_common_divisor`` uses eight- and nine-digit operands that are
  impossible to compute by hand.
* ``dice_sum_probability`` returns an unreduced ``\\frac{3}{36}`` and even
  allows a single die (where a "sum" is meaningless).

Our versions return plain integers, reduced ``a/b`` fractions, or ascending
comma-separated lists, and state the required format/order in the problem.
"""
import random
from fractions import Fraction
from math import gcd

from ._registry import register
from ._variants import with_variants
from ._steps import Steps, tex_frac


def _factors_of(n):
    """Return the sorted list of positive divisors of ``n`` (n >= 1)."""
    divisors = set()
    i = 1
    while i * i <= n:
        if n % i == 0:
            divisors.add(i)
            divisors.add(n // i)
        i += 1
    return sorted(divisors)


def _ascending_list(values):
    """Render ints as an ascending, bracket-free ``'1, 2, 4'`` list."""
    return ", ".join(str(v) for v in sorted(values))


def _frac_str(numerator, denominator):
    """Reduce and render typeably: integer when whole, else ``'p/q'``."""
    fr = Fraction(numerator, denominator)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _factor_pairs(n):
    """Factor pairs ``(a, b)`` with ``a * b == n`` and ``a <= b``, smallest first."""
    return [(d, n // d) for d in _factors_of(n) if d * d <= n]


def _prime_factorization(n):
    """``{prime: exponent}`` for ``n >= 2``."""
    powers, p = {}, 2
    while p * p <= n:
        while n % p == 0:
            powers[p] = powers.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        powers[n] = powers.get(n, 0) + 1
    return powers


def _tex_powers(powers):
    r"""``{2: 3, 3: 1}`` as ``2^{3} \times 3``."""
    return r" \times ".join(
        str(p) if e == 1 else f"{p}^{{{e}}}" for p, e in sorted(powers.items())
    )


def _simplify_step(s, numerator, denominator):
    """Add the step that puts ``numerator/denominator`` in lowest terms."""
    g = gcd(numerator, denominator)
    fraction = tex_frac(numerator, denominator)
    if denominator == 1:
        s.step("A fraction with a denominator of $1$ is a whole number.",
               f"{fraction} = {numerator}")
    elif g == denominator:
        s.step(f"The top divides evenly by the bottom: "
               rf"${numerator} \div {denominator} = {numerator // denominator}$.",
               f"{fraction} = {numerator // denominator}")
    elif g > 1:
        s.step(f"Simplify. Divide the top and bottom by ${g}$, the greatest "
               "number that divides both.",
               rf"\frac{{{numerator} \div {g}}}{{{denominator} \div {g}}} = "
               f"{tex_frac(numerator // g, denominator // g)}")
    else:
        s.step(f"${numerator}$ and ${denominator}$ have no common factor other "
               "than $1$, so the fraction is already in lowest terms.")


@register
@with_variants
def common_factors(min_val=2, max_val=100):
    r"""Common Factors of Two Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | List all common factors of 12 and 18... | 1, 2, 3, 6 |

    Overrides the stock ``common_factors``, which answers with a Python list
    literal like ``[1, 2]``. We return an ascending, comma-separated list with
    no brackets.
    """
    a = random.randint(min_val, max_val)
    b = random.randint(min_val, max_val)
    common = sorted(set(_factors_of(a)) & set(_factors_of(b)))
    problem = (
        f"Find all common factors of {a} and {b}. "
        "List all common factors in ascending order, comma-separated "
        "(e.g. 1, 2, 4)."
    )
    solution = _ascending_list(common)

    s = Steps()
    s.step(f"List the factors of ${a}$ (the numbers that divide it evenly).",
           f"{a}: " + ", ".join(map(str, _factors_of(a))))
    s.step(f"List the factors of ${b}$.", f"{b}: " + ", ".join(map(str, _factors_of(b))))
    if common == [1]:
        s.step("The only number in both lists is $1$.")
    else:
        s.step("The common factors are the numbers that appear in both lists.")
    s.answer(solution, lead="In ascending order, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def factors(min_val=2, max_val=100):
    r"""Factors of a Number

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | List all factors of 12... | 1, 2, 3, 4, 6, 12 |

    Overrides the stock ``factors``, which answers with a Python list literal.
    We return an ascending, comma-separated list with no brackets.
    """
    n = random.randint(min_val, max_val)
    problem = (
        f"Find all factors of {n}. "
        "List all factors in ascending order, comma-separated "
        "(e.g. 1, 2, 3, 6)."
    )
    solution = _ascending_list(_factors_of(n))

    pairs = _factor_pairs(n)
    s = Steps()
    s.step(f"Find pairs of numbers that multiply to make ${n}$. Try $1$, $2$, "
           "$3$, and so on. Stop when the pairs start to repeat.",
           r", \quad ".join(rf"{x} \times {y}" for x, y in pairs))
    if len(pairs) == 1:
        s.step(rf"Only $1 \times {n}$ works, so ${n}$ is a prime number.")
    else:
        s.step("Write every number from the pairs, from smallest to largest.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def fraction_multiplication(max_val=10):
    r"""Multiplication of Two Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $\frac{3}{10} \cdot \frac{2}{5} =$ | 3/25 |

    Overrides the stock ``fraction_multiplication``, which answers with an
    often-unreduced ``\frac{a}{b}``. We return the reduced product in the
    typeable form ``a/b`` (or an integer).
    """
    a = random.randint(1, max_val)
    b = random.randint(1, max_val)
    c = random.randint(1, max_val)
    d = random.randint(1, max_val)
    problem = (
        f"Calculate $\\frac{{{a}}}{{{b}}} \\cdot \\frac{{{c}}}{{{d}}}$. "
        "Give your answer as a fraction in lowest terms in the form a/b, "
        "or an integer."
    )
    solution = _frac_str(a * c, b * d)

    s = Steps()
    s.step("To multiply fractions, multiply the tops (numerators) and multiply "
           "the bottoms (denominators).",
           rf"\frac{{{a}}}{{{b}}} \times \frac{{{c}}}{{{d}}} = "
           rf"\frac{{{a} \times {c}}}{{{b} \times {d}}} = {tex_frac(a * c, b * d)}")
    _simplify_step(s, a * c, b * d)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def divide_fractions(max_val=10):
    r"""Division of Two Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $\frac{3}{10} \div \frac{2}{5} =$ | 3/4 |

    Overrides the stock ``divide_fractions``, which answers with an
    often-unreduced ``\frac{a}{b}``. We return the reduced quotient in the
    typeable form ``a/b`` (or an integer).
    """
    a = random.randint(1, max_val)
    b = random.randint(1, max_val)
    # Numerator of the divisor must be non-zero so division is defined.
    c = random.randint(1, max_val)
    d = random.randint(1, max_val)
    problem = (
        f"Calculate $\\frac{{{a}}}{{{b}}} \\div \\frac{{{c}}}{{{d}}}$. "
        "Give your answer as a fraction in lowest terms in the form a/b, "
        "or an integer."
    )
    # (a/b) / (c/d) = a*d / (b*c)
    solution = _frac_str(a * d, b * c)

    s = Steps()
    s.step("To divide by a fraction, multiply by its reciprocal. Flip the "
           "second fraction upside down.",
           rf"\frac{{{a}}}{{{b}}} \div \frac{{{c}}}{{{d}}} = "
           rf"\frac{{{a}}}{{{b}}} \times \frac{{{d}}}{{{c}}}")
    s.step("Multiply the tops and multiply the bottoms.",
           rf"\frac{{{a} \times {d}}}{{{b} \times {c}}} = {tex_frac(a * d, b * c)}")
    _simplify_step(s, a * d, b * c)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def greatest_common_divisor(min_val=2, max_val=100, count_choices=(2, 3)):
    r"""Greatest Common Divisor (HCF) of Several Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the greatest common divisor (GCD) of 24, 36. | 12 |

    Overrides the stock ``greatest_common_divisor``, which uses eight- and
    nine-digit operands that can't be worked by hand. We pick a few small,
    review-friendly integers. The answer is a single integer.
    """
    count = random.choice(count_choices)
    numbers = [random.randint(min_val, max_val) for _ in range(count)]
    result = 0
    for value in numbers:
        result = gcd(result, value)
    number_list = ", ".join(str(v) for v in numbers)
    problem = (
        f"Find the greatest common divisor (GCD) of {number_list}. "
        "Give your answer as a single integer."
    )
    solution = str(result)

    factorizations = [_prime_factorization(v) if v > 1 else {} for v in numbers]
    shared = {
        p: min(f.get(p, 0) for f in factorizations)
        for p in factorizations[0]
        if all(p in f for f in factorizations)
    }
    s = Steps()
    s.step("Write each number as a product of primes.",
           r"\begin{aligned} "
           + r" \\ ".join(f"{v} &= {_tex_powers(f)}" for v, f in zip(numbers, factorizations))
           + r" \end{aligned}")
    if shared:
        product = _tex_powers(shared)
        s.step("Take each prime that appears in every number, using the "
               "smallest power of it that appears.",
               rf"\text{{GCD}} = {product}"
               + ("" if product == str(result) else f" = {result}"))
    else:
        s.step("No prime appears in every number, so the only common factor is $1$.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def dice_sum_probability(sides=6):
    r"""Probability of a Given Sum on Two Dice

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | If 2 fair 6-sided dice are rolled, the probability of a sum of 9 is... | 1/9 |

    Overrides the stock ``dice_sum_probability``, which returns an unreduced
    ``\frac{3}{36}`` and even permits a single die. We fix the roll at two dice
    and return the probability as a reduced ``a/b`` fraction.
    """
    target = random.randint(2, 2 * sides)
    # Count ordered outcomes of two dice summing to `target`.
    favorable = sum(
        1
        for x in range(1, sides + 1)
        for y in range(1, sides + 1)
        if x + y == target
    )
    total = sides * sides
    problem = (
        f"If 2 fair {sides}-sided dice are rolled at the same time, "
        f"what is the probability of getting a sum of {target}? "
        "Give your answer as a fraction in lowest terms in the form a/b."
    )
    solution = _frac_str(favorable, total)

    rolls = [(x, target - x) for x in range(1, sides + 1) if 1 <= target - x <= sides]
    s = Steps()
    s.step(rf"Each die has ${sides}$ faces, so there are ${sides} \times {sides} = "
           f"{total}$ equally likely outcomes.")
    s.step(f"List the rolls (first die, second die) that add to ${target}$.",
           r", \; ".join(f"({x}, {y})" for x, y in rolls))
    s.step(f"Probability is favorable outcomes divided by total outcomes: "
           f"${favorable}$ out of ${total}$.",
           f"P = {tex_frac(favorable, total)}")
    _simplify_step(s, favorable, total)
    s.answer(solution)
    return problem, solution, s.done()
