"""Extra question types for the arithmetic topics (Grades 1-5 and arithmetic facts).

Variants for the generators in ``arithmetic``, ``lib_arith_gen``,
``lib_fractions_gen`` (GCD) and ``lib_solids_gen`` (cube roots). Each attaches to
its topic's dispatcher (see ``_variants.with_variants``); the original question
stays as the ``classic`` variant. Variants only use their own topic's skill. See
docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num
from ._steps import Steps, tex_frac
from . import arithmetic as ar, lib_arith_gen as la, lib_fractions_gen, lib_solids_gen

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."


def _tex(value):
    v = Fraction(value)
    return str(v.numerator) if v.denominator == 1 else tex_frac(v.numerator, v.denominator)


def _ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _money(cents):
    """A dollar amount with two decimals, e.g. 740 -> 7.40."""
    return f"{cents // 100}.{cents % 100:02d}"


def _hm(total_minutes):
    """Minutes after midnight as H:MM on a 12-hour clock."""
    h, m = divmod(total_minutes % (12 * 60), 60)
    return f"{h if h else 12}:{m:02d}"


# --- Arithmetic facts ----------------------------------------------------------------------------

@la.addition.variant("missing_addend")
def _addition_missing_addend():
    r"""$27 + \square = 42$."""
    a, total = random.randint(1, 60), random.randint(10, 99)
    if total <= a:
        total = a + random.randint(1, 30)
    problem = rf"What number goes in the box? ${a} + \square = {total}$"
    solution = f"{total - a}"
    s = Steps()
    s.step("Think: what do you add to the first number to reach the total? Subtract to find it.", f"{total} - {a} = {total - a}")
    s.answer(solution)
    return problem, solution, s.done()


@la.addition.variant("make_a_ten")
def _addition_compensation():
    r"""Compensation: $27 + 15 = 30 + \square$."""
    a = random.choice([x for x in range(11, 80) if x % 10])
    up = 10 - a % 10
    b = random.randint(up + 1, 19)
    problem = rf"Fill in the box: ${a} + {b} = {a + up} + \square$"
    solution = f"{b - up}"
    s = Steps()
    s.step(f"${a}$ became ${a + up}$, which is ${up}$ more, so the other number must be ${up}$ less.", f"{b} - {up} = {b - up}")
    s.answer(solution)
    return problem, solution, s.done()


@la.addition.variant("start_unknown")
def _addition_start_unknown():
    """A story where the starting amount is unknown."""
    start, more = random.randint(2, 40), random.randint(2, 40)
    thing = random.choice(["birds were in a tree", "cars were in a parking lot", "books were on a shelf"])
    problem = f"Some {thing}. Then ${more}$ more came. Now there are ${start + more}$. How many were there at first?"
    solution = f"{start}"
    s = Steps()
    s.step("The start plus the ones that came makes the total, so subtract.", f"{start + more} - {more} = {start}")
    s.answer(solution)
    return problem, solution, s.done()


@la.subtraction.variant("constant_difference")
def _subtraction_constant_difference():
    r"""$42 - 18 = 44 - \square$: shifting both numbers keeps the difference."""
    a = random.randint(20, 99)
    b = random.randint(2, a - 1)
    k = random.randint(1, 9)
    problem = rf"Fill in the box: ${a} - {b} = {a + k} - \square$"
    solution = f"{b + k}"
    s = Steps()
    s.step(f"Adding ${k}$ to both numbers keeps the difference the same.", f"{a} - {b} = {a + k} - {b + k}")
    s.answer(solution)
    return problem, solution, s.done()


@la.subtraction.variant("compare_story")
def _subtraction_compare():
    """How many more does one have than the other?"""
    big, small = sorted(random.sample(range(2, 99), 2), reverse=True)
    problem = f"Ann has ${big}$ stickers and Ben has ${small}$. How many more stickers does Ann have than Ben?"
    solution = f"{big - small}"
    s = Steps()
    s.step("\"How many more\" means find the difference.", f"{big} - {small} = {big - small}")
    s.answer(solution)
    return problem, solution, s.done()


@la.multiplication.variant("distributive_split")
def _multiplication_split():
    r"""$7 \times 14 = 7 \times 10 + 7 \times \square$."""
    a, b = random.randint(2, 9), random.randint(11, 19)
    problem = rf"Fill in the box: ${a} \times {b} = {a} \times 10 + {a} \times \square$"
    solution = f"{b - 10}"
    s = Steps()
    s.step(f"Split ${b}$ into $10 + {b - 10}$ and multiply each part.", rf"{a} \times {b} = {a} \times 10 + {a} \times {b - 10}")
    s.answer(solution)
    return problem, solution, s.done()


@la.multiplication.variant("doubling")
def _multiplication_doubling():
    r"""If $6 \times 8 = 48$, then $12 \times 8 = 96$."""
    a, b = random.randint(2, 9), random.randint(2, 12)
    problem = rf"If ${a} \times {b} = {a * b}$, what is ${2 * a} \times {b}$?"
    solution = f"{2 * a * b}"
    s = Steps()
    s.step(f"${2 * a}$ is double ${a}$, so the product doubles.", rf"2 \times {a * b} = {2 * a * b}")
    s.answer(solution)
    return problem, solution, s.done()


@la.division.variant("interpret_remainder")
def _division_interpret_remainder():
    """Whether to round up, round down, or keep the remainder depends on the story."""
    per = random.randint(3, 12)
    total = random.randint(per + 1, per * 12)
    while total % per == 0:
        total += 1
    q, r = divmod(total, per)
    kind = random.choice(["up", "down", "left"])
    if kind == "up":
        problem = f"${total}$ students are going on a trip, and each van holds ${per}$. How many vans are needed?"
        answer, why = q + 1, f"${q}$ vans leave ${r}$ students behind, so one more van is needed."
    elif kind == "down":
        problem = f"A baker has ${total}$ cookies and packs them in boxes of ${per}$. How many boxes can be completely filled?"
        answer, why = q, f"Only ${q}$ boxes can be filled; the ${r}$ left over don't fill another."
    else:
        problem = f"${total}$ marbles are shared equally among ${per}$ friends. How many marbles are left over?"
        answer, why = r, f"Each friend gets ${q}$, and ${r}$ are left over."
    solution = f"{answer}"
    s = Steps()
    s.step("Divide.", rf"{total} \div {per} = {q} \text{{ R }} {r}")
    s.step(why)
    s.answer(solution)
    return problem, solution, s.done()


@la.division.variant("fact_family")
def _division_fact_family():
    r"""Use a multiplication fact: $6 \times 7 = 42$, so $42 \div \square = 6$."""
    a, b = random.randint(2, 12), random.randint(2, 12)
    problem = rf"${a} \times {b} = {a * b}$. Fill in the box: ${a * b} \div \square = {a}$"
    solution = f"{b}"
    s = Steps()
    s.step("Multiplication and division are in the same fact family.", rf"{a * b} \div {b} = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@la.absolute_difference.variant("number_line")
def _absolute_number_line():
    """Distance between two numbers on a number line (or a temperature range)."""
    a, b = random.randint(-25, -1), random.randint(1, 25)
    if random.random() < 0.5:
        problem = f"Points are marked at ${a}$ and ${b}$ on a number line. How far apart are they?"
    else:
        problem = f"The low temperature was ${a}^\\circ$ and the high was ${b}^\\circ$. How many degrees warmer was the high?"
    solution = f"{b - a}"
    s = Steps()
    s.step("The distance between two numbers is their difference: here it crosses $0$.", f"{b} - ({a}) = {b - a}")
    s.answer(solution)
    return problem, solution, s.done()


@la.exponentiation.variant("missing_exponent")
def _exponent_missing():
    r"""$3^{\square} = 81$."""
    b = random.randint(2, 6)
    e = random.randint(2, 5 if b < 5 else 4)
    problem = rf"Fill in the box: ${b}^{{\square}} = {b ** e}$"
    solution = f"{e}"
    s = Steps()
    s.step(f"Multiply ${b}$ by itself until you reach ${b ** e}$.", r" \times ".join([str(b)] * e) + f" = {b ** e}")
    s.answer(solution)
    return problem, solution, s.done()


@la.exponentiation.variant("power_vs_product")
def _exponent_vs_product():
    r"""How much greater is $3^4$ than $3 \times 4$? (A power is not a product.)"""
    b, e = random.randint(2, 5), random.randint(3, 5)
    problem = rf"How much greater is ${b}^{{{e}}}$ than ${b} \times {e}$?"
    solution = f"{b ** e - b * e}"
    s = Steps()
    s.step(f"${b}^{{{e}}}$ means ${e}$ factors of ${b}$, not ${b} \\times {e}$.", f"{b}^{{{e}}} = {b ** e}, \\quad {b} \\times {e} = {b * e}")
    s.step("Subtract.", f"{b ** e} - {b * e} = {b ** e - b * e}")
    s.answer(solution)
    return problem, solution, s.done()


@la.square.variant("sign_and_order")
def _square_sign_order():
    r"""$-7^2 = -49$ but $(-7)^2 = 49$."""
    n = random.randint(2, 15)
    paren_ = random.random() < 0.5
    expr = f"(-{n})^2" if paren_ else f"-{n}^2"
    value = n * n if paren_ else -n * n
    problem = f"Evaluate ${expr}$."
    solution = f"{value}"
    s = Steps()
    if paren_:
        s.step("The parentheses make $-" + str(n) + "$ the base, and a negative times a negative is positive.", f"(-{n})(-{n}) = {n * n}")
    else:
        s.step("Without parentheses, the exponent applies only to $" + str(n) + "$; the minus sign comes after.", f"-({n} \\times {n}) = {-n * n}")
    s.answer(solution)
    return problem, solution, s.done()


@la.square.variant("consecutive_squares")
def _square_consecutive():
    r"""$17^2 = 16^2 + \square$ (consecutive squares differ by 2n + 1)."""
    n = random.randint(5, 30)
    problem = rf"Fill in the box: ${n + 1}^2 = {n}^2 + \square$"
    solution = f"{2 * n + 1}"
    s = Steps()
    s.step("Consecutive squares differ by the sum of the two numbers.", f"{n + 1}^2 - {n}^2 = {n + 1} + {n} = {2 * n + 1}")
    s.answer(solution)
    return problem, solution, s.done()


@la.square_root.variant("roots_dont_add")
def _square_root_dont_add():
    r"""$\sqrt{36} + \sqrt{64} - \sqrt{36 + 64}$: roots of a sum aren't sums of roots."""
    (p, q, r) = random.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17)])
    problem = rf"Evaluate $\sqrt{{{p * p}}} + \sqrt{{{q * q}}} - \sqrt{{{p * p} + {q * q}}}$."
    solution = f"{p + q - r}"
    s = Steps()
    s.step("Take each square root separately.", rf"{p} + {q} - \sqrt{{{p * p + q * q}}} = {p} + {q} - {r} = {p + q - r}")
    s.answer(solution)
    return problem, solution, s.done()


@la.square_root.variant("side_of_square")
def _square_root_side():
    """A square's side from its area."""
    n = random.randint(2, 25)
    problem = f"A square has an area of ${n * n}$ square units. How long is each side?"
    solution = f"{n}"
    s = Steps()
    s.step("The area is side times side, so the side is the square root.", rf"\sqrt{{{n * n}}} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.cube_root.variant("cube_edge")
def _cube_root_edge():
    """A cube's edge from its volume (or a negative cube root)."""
    n = random.randint(2, 15)
    if random.random() < 0.5:
        problem = f"A cube has a volume of ${n ** 3}$ cubic cm. How long is each edge, in cm?"
        solution = f"{n}"
        s = Steps()
        s.step("Volume is edge times edge times edge, so take the cube root.", rf"\sqrt[3]{{{n ** 3}}} = {n}")
    else:
        problem = rf"Evaluate $\sqrt[3]{{-{n ** 3}}}$."
        solution = f"{-n}"
        s = Steps()
        s.step("A negative number cubed is negative.", f"({-n})^3 = {-n ** 3}")
    s.answer(solution)
    return problem, solution, s.done()


@la.lcm.variant("buses")
def _lcm_buses():
    """When two repeating schedules line up again."""
    a, b = random.sample(range(4, 25), 2)
    problem = (
        f"Bus A leaves every ${a}$ minutes and bus B every ${b}$ minutes. They both leave at 9:00. In how many minutes do they "
        "next leave at the same time?"
    )
    solution = f"{math.lcm(a, b)}"
    s = Steps()
    s.step("They leave together again at the first common multiple of the two intervals.", f"\\text{{LCM}}({a}, {b}) = {math.lcm(a, b)}")
    s.answer(solution)
    return problem, solution, s.done()


@la.lcm.variant("smallest_over")
def _lcm_smallest_over():
    """The smallest number over N divisible by both a and b."""
    a, b = random.sample(range(2, 13), 2)
    l = math.lcm(a, b)
    N = random.randint(l, 10 * l)
    answer = (N // l + 1) * l
    problem = f"What is the smallest number greater than ${N}$ that is divisible by both ${a}$ and ${b}$?"
    solution = f"{answer}"
    s = Steps()
    s.step("Numbers divisible by both are the multiples of the LCM.", f"\\text{{LCM}}({a}, {b}) = {l}")
    s.step(f"Take the first multiple of ${l}$ past ${N}$.", f"{answer}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_fractions_gen.greatest_common_divisor.variant("bouquets")
def _gcd_bouquets():
    """The most identical groups with nothing left over."""
    g = random.randint(2, 12)
    a, b = g * random.randint(2, 9), g * random.randint(2, 9)
    while math.gcd(a, b) != g:
        b += g
    problem = (
        f"A florist has ${a}$ roses and ${b}$ tulips and makes identical bouquets using every flower. What is the greatest "
        "number of bouquets possible? Give your answer as a single integer."
    )
    solution = f"{g}"
    s = Steps()
    s.step("The number of bouquets must divide both counts; the most is the GCD.", f"\\gcd({a}, {b}) = {g}")
    s.answer(solution)
    return problem, solution, s.done()


@la.prime_factors.variant("perfect_square_multiplier")
def _prime_factors_square():
    """The smallest multiplier that makes n a perfect square."""
    base = random.randint(2, 12)
    extra = random.choice([2, 3, 5, 6, 7, 10])
    n = base * base * extra
    problem = f"What is the smallest whole number you can multiply ${n}$ by to get a perfect square?"
    factors = {}
    m = n
    p = 2
    while p * p <= m:
        while m % p == 0:
            factors[p] = factors.get(p, 0) + 1
            m //= p
        p += 1
    if m > 1:
        factors[m] = factors.get(m, 0) + 1
    need = math.prod(p for p, e in factors.items() if e % 2)
    solution = f"{need}"
    s = Steps()
    s.step("Write the prime factorization.", r" \cdot ".join(f"{p}^{{{e}}}" for p, e in sorted(factors.items())))
    s.step("A perfect square has every exponent even; multiply by each prime with an odd exponent.", f"{need}")
    s.answer(solution)
    return problem, solution, s.done()


@la.prime_factors.variant("from_factorization")
def _prime_factors_reverse():
    r"""Reverse: $n = 2^3 \cdot 3^2 \cdot 5$; find n."""
    primes = random.sample([2, 3, 5, 7, 11], random.randint(2, 3))
    exps = [random.randint(1, 3) for _ in primes]
    n = math.prod(p ** e for p, e in zip(primes, exps))
    tex = r" \cdot ".join(f"{p}^{{{e}}}" if e > 1 else str(p) for p, e in sorted(zip(primes, exps)))
    problem = f"What number has the prime factorization ${tex}$?"
    solution = f"{n}"
    s = Steps()
    s.step("Multiply it out.", f"{tex} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@la.is_prime.variant("next_prime")
def _is_prime_next():
    """The smallest prime greater than n."""
    n = random.randint(10, 200)
    p = n + 1
    while any(p % d == 0 for d in range(2, math.isqrt(p) + 1)):
        p += 1
    problem = f"What is the smallest prime number greater than ${n}$?"
    solution = f"{p}"
    s = Steps()
    s.step("Test the next numbers in order until one has no factor other than $1$ and itself.", f"{p}")
    s.answer(solution)
    return problem, solution, s.done()


@la.is_composite.variant("count_composites")
def _is_composite_count():
    """How many composite numbers lie in a range."""
    lo = random.randint(10, 80)
    hi = lo + random.randint(5, 15)
    comp = [n for n in range(lo, hi + 1) if any(n % d == 0 for d in range(2, math.isqrt(n) + 1))]
    problem = f"How many composite numbers are there from ${lo}$ to ${hi}$, including both?"
    solution = f"{len(comp)}"
    s = Steps()
    s.step("Cross out the primes; the rest are composite.", ", ".join(map(str, comp)))
    s.answer(solution)
    return problem, solution, s.done()


@la.compare_fractions.variant("fraction_between")
def _compare_fractions_between():
    """The one whole number n with p/q < n/d < r/s."""
    d = random.choice([6, 8, 10, 12])
    n = random.randint(1, d - 1)
    lo_f, hi_f = Fraction(n * 2 - 1, d * 2), Fraction(n * 2 + 1, d * 2)
    problem = (
        f"What whole number $n$ makes $\\frac{{{lo_f.numerator}}}{{{lo_f.denominator}}} < \\frac{{n}}{{{d}}} < "
        f"\\frac{{{hi_f.numerator}}}{{{hi_f.denominator}}}$ true?"
    )
    solution = f"{n}"
    s = Steps()
    s.step(f"Rewrite the bounds with denominator ${2 * d}$ and compare numerators.", rf"\frac{{{2 * n - 1}}}{{{2 * d}}} < \frac{{2n}}{{{2 * d}}} < \frac{{{2 * n + 1}}}{{{2 * d}}}")
    s.step("Only one even number fits.", f"2n = {2 * n} \\Rightarrow n = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@la.compare_fractions.variant("greater_fraction")
def _compare_fractions_greater():
    """Enter the greater of two fractions (benchmark reasoning)."""
    while True:
        a, b, c, d = random.randint(1, 9), random.randint(2, 12), random.randint(1, 9), random.randint(2, 12)
        f1, f2 = Fraction(a, b), Fraction(c, d)
        if a < b and c < d and f1 != f2 and math.gcd(a, b) == 1 and math.gcd(c, d) == 1:
            break
    problem = f"Which is greater, ${a}/{b}$ or ${c}/{d}$? Type the greater fraction."
    solution = frac_from(max(f1, f2))
    s = Steps()
    s.step("Compare with a common denominator (or cross-multiply).", f"{a} \\times {d} = {a * d}, \\quad {c} \\times {b} = {c * b}")
    s.answer(solution)
    return problem, solution, s.done()


@la.factorial.variant("quotient")
def _factorial_quotient():
    r"""$\frac{10!}{8!} = 10 \times 9$."""
    n = random.randint(5, 20)
    k = random.randint(1, 3)
    problem = rf"Evaluate $\frac{{{n}!}}{{{n - k}!}}$."
    solution = f"{math.factorial(n) // math.factorial(n - k)}"
    s = Steps()
    s.step(f"Everything up to ${n - k}$ cancels.", r" \times ".join(str(n - i) for i in range(k)) + f" = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@la.factorial.variant("arrangements")
def _factorial_arrangements():
    """Arrangements of n different books (n!) — or the reverse."""
    n = random.randint(3, 8)
    if random.random() < 0.5:
        problem = f"In how many different orders can ${n}$ different books be placed on a shelf?"
        solution = f"{math.factorial(n)}"
    else:
        problem = f"$n$ different books can be arranged on a shelf in ${math.factorial(n)}$ ways. What is $n$?"
        solution = f"{n}"
    s = Steps()
    s.step("The number of orders of $n$ things is $n!$.", f"{n}! = {math.factorial(n)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Grades 1-5 --------------------------------------------------------------------------------

@ar.arith_place_value.variant("unusual_regrouping")
def _place_value_regrouping():
    """Build a number from regrouped parts: 4 thousands + 17 hundreds + 3 ones."""
    th, hu, te, on = random.randint(1, 9), random.randint(10, 19), random.randint(2, 9), random.randint(2, 9)
    value = th * 1000 + hu * 100 + te * 10 + on
    problem = f"What number is ${th}$ thousands, ${hu}$ hundreds, ${te}$ tens, and ${on}$ ones?"
    solution = f"{value}"
    s = Steps()
    s.step("Find the value of each part and add.", f"{th * 1000} + {hu * 100} + {te * 10} + {on} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_place_value.variant("digit_value_ratio")
def _place_value_ratio():
    """In 7474, the first 7 is how many times the second?"""
    d = random.randint(1, 9)
    gap = random.choice([1, 2, 3])
    digits = [random.choice([x for x in range(1, 10) if x != d]) for _ in range(5)]
    i = random.randint(0, 4 - gap)
    digits[i] = digits[i + gap] = d
    number = int("".join(map(str, digits)))
    problem = f"In ${number}$, the first ${d}$ (from the left) is worth how many times the second ${d}$?"
    solution = f"{10 ** gap}"
    s = Steps()
    s.step(f"The two ${d}$s are ${gap}$ place{'s' if gap > 1 else ''} apart; each place is worth $10$ times the one to its right.",
           f"10^{gap} = {10 ** gap}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_rounding.variant("smallest_that_rounds")
def _rounding_reverse():
    """Reverse: the smallest or largest whole number that rounds to a value."""
    place, name = random.choice([(10, "ten"), (100, "hundred"), (1000, "thousand")])
    target = place * random.randint(2, 99)
    smallest = random.random() < 0.5
    answer = target - place // 2 if smallest else target + place // 2 - 1
    problem = f"A whole number rounds to ${target}$ when rounded to the nearest {name}. What is the {'smallest' if smallest else 'largest'} it could be?"
    solution = f"{answer}"
    s = Steps()
    s.step(f"Numbers within half of ${place}$ round to ${target}$, from ${target - place // 2}$ up to ${target + place // 2 - 1}$.")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_rounding.variant("estimate_sum")
def _rounding_estimate():
    """Estimate a sum by rounding each number first."""
    a, b = random.randint(100, 999), random.randint(100, 999)
    ra = (a + 50) // 100 * 100
    rb = (b + 50) // 100 * 100
    problem = f"Estimate ${a} + {b}$ by rounding each number to the nearest hundred first."
    solution = f"{ra + rb}"
    s = Steps()
    s.step("Round each number.", f"{a} \\to {ra}, \\quad {b} \\to {rb}")
    s.step("Add the rounded numbers.", f"{ra} + {rb} = {ra + rb}")
    s.answer(solution)
    return problem, solution, s.done()


def _fraction_missing_numerator():
    r"""$\frac{1}{2} + \frac{\square}{6} = \frac{5}{6}$."""
    d = random.choice([4, 6, 8, 10, 12])
    a_den = random.choice([x for x in (2, 3, 4, 6) if d % x == 0])
    a = Fraction(random.randint(1, a_den - 1), a_den)
    n = random.randint(1, d - 1)
    total = a + Fraction(n, d)
    problem = (
        rf"What number goes in the box? $\frac{{{a.numerator}}}{{{a.denominator}}} + \frac{{\square}}{{{d}}} = "
        rf"\frac{{{(total * d).numerator}}}{{{d}}}$"
    )
    solution = f"{n}"
    s = Steps()
    s.step(f"Rewrite with denominator ${d}$.", rf"\frac{{{a * d}}}{{{d}}} + \frac{{\square}}{{{d}}} = \frac{{{total * d}}}{{{d}}}")
    s.step("Subtract the numerators.", f"{total * d} - {a * d} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


ar.arith_add_fractions.variant("missing_numerator")(_fraction_missing_numerator)
ar.arith_add_unlike_fractions.variant("missing_numerator")(_fraction_missing_numerator)


@ar.arith_subtract_fractions.variant("to_make_one")
def _fraction_to_make_one():
    """What must be added to a fraction to make 1?"""
    d = random.randint(2, 12)
    n = random.choice([x for x in range(1, d) if math.gcd(x, d) == 1])
    problem = f"What fraction must be added to ${n}/{d}$ to make $1$? {_FRACTION_HINT}"
    solution = frac_from(Fraction(d - n, d))
    s = Steps()
    s.step(f"$1$ is ${d}/{d}$; subtract.", rf"\frac{{{d}}}{{{d}}} - \frac{{{n}}}{{{d}}} = {_tex(Fraction(d - n, d))}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_compare_decimals.variant("longer_is_not_bigger")
def _compare_decimals_misconception():
    """Which is greater, 0.5 or 0.45? More digits doesn't mean bigger."""
    a = random.randint(1, 9)
    b = random.choice([x for x in range(11, 100) if x % 10])
    x, y = Fraction(a, 10), Fraction(b, 100)
    problem = f"Which is greater, ${num(x)}$ or ${num(y)}$? Type the greater number."
    solution = num(max(x, y))
    s = Steps()
    s.step("Write both with the same number of decimal places.", f"{num(x)} = {a}0 \\text{{ hundredths}}, \\quad {num(y)} = {b} \\text{{ hundredths}}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_add_decimals.variant("missing_addend")
def _decimal_missing_addend():
    r"""$12.5 + \square = 15.75$."""
    a = Fraction(random.randint(10, 999), 10)
    b = Fraction(random.randint(10, 999), 100)
    problem = rf"What number goes in the box? ${num(a)} + \square = {num(a + b)}$"
    solution = num(b)
    s = Steps()
    s.step("Subtract to find the missing addend.", f"{num(a + b)} - {num(a)} = {num(b)}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_subtract_decimals.variant("change_from_twenty")
def _decimal_change():
    """Change from a $20 bill after two purchases."""
    p1, p2 = random.randint(100, 900), random.randint(100, 900)
    change = 2000 - p1 - p2
    problem = (
        f"You buy items costing ${_money(p1)}$ and ${_money(p2)}$ dollars and pay with a twenty-dollar bill. "
        "How much change do you get, in dollars?"
    )
    solution = num(Fraction(change, 100))
    s = Steps()
    s.step("Add the costs, then subtract from $20$.", f"20 - ({num(Fraction(p1, 100))} + {num(Fraction(p2, 100))}) = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_multiply_decimals.variant("place_value_from_whole")
def _decimal_multiply_from_whole():
    r"""Given $25 \times 32 = 800$, find $2.5 \times 0.32$."""
    a, b = random.randint(11, 99), random.randint(11, 99)
    pa, pb = random.choice([(1, 1), (1, 2), (2, 1)])  # at most 3 decimal places, so the product is exact
    x, y = Fraction(a, 10 ** pa), Fraction(b, 10 ** pb)
    problem = rf"Given that ${a} \times {b} = {a * b}$, what is ${num(x)} \times {num(y)}$?"
    solution = num(x * y)
    s = Steps()
    s.step(f"The factors have ${pa} + {pb} = {pa + pb}$ decimal places in all, so the product does too.", f"{a * b} \\to {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_divide_decimals.variant("place_value_from_whole")
def _decimal_divide_from_whole():
    r"""Given $105 \div 7 = 15$, find $10.5 \div 0.7$."""
    q, d = random.randint(2, 30), random.randint(2, 9)
    total = q * d
    problem = rf"Given that ${total} \div {d} = {q}$, what is ${num(Fraction(total, 10))} \div {num(Fraction(d, 10))}$?"
    solution = f"{q}"
    s = Steps()
    s.step("Both numbers were divided by $10$, so the quotient doesn't change.", rf"\frac{{{num(Fraction(total, 10))}}}{{{num(Fraction(d, 10))}}} = \frac{{{total}}}{{{d}}} = {q}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_order_of_operations.variant("largest_value")
def _order_largest_value():
    r"""Put + and × between 2, 3, 4 (once each) for the largest result."""
    a, b, c = random.sample(range(2, 10), 3)
    options = {f"{a} + {b} \\times {c}": a + b * c, f"{a} \\times {b} + {c}": a * b + c}
    best = max(options.values())
    problem = (
        f"Put one $+$ and one $\\times$ in the boxes: ${a} \\,\\square\\, {b} \\,\\square\\, {c}$. Using the order of operations, "
        "what is the largest result you can make?"
    )
    solution = f"{best}"
    s = Steps()
    s.step("Try both placements; multiplication happens first.", r",\quad ".join(f"{k} = {v}" for k, v in options.items()))
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_order_of_operations.variant("missing_number")
def _order_missing_number():
    r"""$3 + \square \times 2 = 11$."""
    a, b, k = random.randint(1, 20), random.randint(2, 9), random.randint(1, 12)
    problem = rf"What number goes in the box? ${a} + \square \times {b} = {a + k * b}$"
    solution = f"{k}"
    s = Steps()
    s.step("Multiplication comes first, so the product is the total minus the first number.", f"{a + k * b} - {a} = {k * b}")
    s.step(f"Divide by ${b}$.", f"{k * b} \\div {b} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_nth_multiple.variant("which_multiple")
def _nth_multiple_reverse():
    """Reverse: 84 is which multiple of 7? (or how many multiples up to 100)"""
    b = random.randint(2, 12)
    if random.random() < 0.5:
        n = random.randint(2, 15)
        problem = f"${b * n}$ is which multiple of ${b}$? (For example, 14 is the 2nd multiple of 7.) Type the number only."
        solution = f"{n}"
        s = Steps()
        s.step("Divide.", rf"{b * n} \div {b} = {n}")
    else:
        top = random.choice([50, 100, 200])
        problem = f"How many multiples of ${b}$ are there from $1$ to ${top}$?"
        solution = f"{top // b}"
        s = Steps()
        s.step(f"Divide ${top}$ by ${b}$ and drop the remainder.", rf"{top} \div {b} = {top // b} \text{{ R }} {top % b}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_powers_of_ten.variant("missing_exponent")
def _powers_of_ten_reverse():
    r"""$34 \times 10^{\square} = 34000$."""
    n, k = random.randint(2, 99), random.randint(1, 4)
    problem = rf"Fill in the box: ${n} \times 10^{{\square}} = {n * 10 ** k}$"
    solution = f"{k}"
    s = Steps()
    s.step("Each power of ten adds one zero; count the zeros added.", f"{n * 10 ** k} = {n} \\times {10 ** k}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_length_conversion.variant("pieces")
def _length_pieces():
    """How many pieces of a given length come from a longer ribbon (mixed units)."""
    feet = random.randint(2, 12)
    piece = random.choice([2, 3, 4, 6])
    problem = f"A ribbon is ${feet}$ feet long. How many ${piece}$-inch pieces can be cut from it?"
    solution = f"{feet * 12 // piece}"
    s = Steps()
    s.step("Convert to inches.", f"{feet} \\times 12 = {feet * 12}")
    s.step("Divide by the piece length.", rf"{feet * 12} \div {piece} = {feet * 12 // piece}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_metric_unit_conversion.variant("batches")
def _metric_batches():
    """Full batches from a container (L to mL)."""
    liters = random.randint(1, 5)
    per = random.choice([200, 250, 300, 400, 500, 750])
    problem = f"Each batch of a recipe needs ${per}$ mL of milk. How many full batches can be made from ${liters}$ L?"
    solution = f"{liters * 1000 // per}"
    s = Steps()
    s.step("Convert liters to milliliters.", f"{liters} \\times 1000 = {liters * 1000}")
    s.step("Divide and keep the whole number.", rf"{liters * 1000} \div {per} = {num(Fraction(liters * 1000, per))}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_minutes_to_hours.variant("to_minutes")
def _minutes_reverse():
    """Reverse: hours and minutes to minutes."""
    h, m = random.randint(1, 9), random.randint(0, 59)
    problem = f"How many minutes are in ${h}$ hr ${m}$ min?"
    solution = f"{60 * h + m}"
    s = Steps()
    s.step("Each hour is $60$ minutes.", f"{h} \\times 60 + {m} = {60 * h + m}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_elapsed_time.variant("start_unknown")
def _elapsed_start_unknown():
    """Reverse: the start time from the end time and the duration."""
    start = random.randint(8 * 60, 18 * 60)
    dur = random.randint(15, 180)
    problem = (
        f"A movie ended at {_hm(start + dur)} and lasted {dur // 60} hr {dur % 60} min. What time did it start? Format your answer as H:MM."
    )
    solution = _hm(start)
    s = Steps()
    s.step(f"Count back {dur // 60} hours and {dur % 60} minutes from {_hm(start + dur)}.", solution)
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_elapsed_time.variant("duration")
def _elapsed_duration():
    """How many minutes from one time to another (possibly across noon)."""
    start = random.randint(8 * 60, 15 * 60)
    dur = random.randint(20, 240)
    def label(t):
        h, m = divmod(t, 60)
        return f"{h % 12 or 12}:{m:02d} {'a.m.' if h < 12 else 'p.m.'}"
    problem = f"How many minutes are there from {label(start)} to {label(start + dur)}?"
    solution = f"{dur}"
    s = Steps()
    s.step("Count the whole hours, then the extra minutes.", f"{dur // 60} \\text{{ hr }} {dur % 60} \\text{{ min}} = {dur} \\text{{ min}}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_money.variant("how_much_more")
def _money_how_much_more():
    """How much more money is needed."""
    have, need = sorted(random.sample(range(100, 5000), 2))
    problem = f"You have ${_money(have)}$ dollars and need ${_money(need)}$. How much more do you need, in dollars?"
    solution = num(Fraction(need - have, 100))
    s = Steps()
    s.step("Subtract what you have from what you need.", f"{num(Fraction(need, 100))} - {num(Fraction(have, 100))} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_money.variant("left_after_buying")
def _money_left_after_buying():
    """Buy as many as you can; how much is left?"""
    while True:
        price = random.choice(range(75, 400, 25))
        have = random.randint(5, 20) * 100
        left = have % price
        if left:
            break
    problem = (
        f"Snacks cost ${_money(price)}$ dollars each. With ${have // 100}$ dollars, you buy as many as you can. "
        "How much money is left, in dollars?"
    )
    solution = num(Fraction(left, 100))
    s = Steps()
    s.step(
        f"${have // price}$ snacks cost ${_money(have // price * price)}$ dollars; one more would cost "
        f"${_money((have // price + 1) * price)}$, which is too much."
    )
    s.step("Subtract what you spent.", rf"{have // 100} - {_money(have // price * price)} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_area_of_rectangle.variant("missing_side")
def _rectangle_missing_side():
    """Reverse: the width from the area and the length."""
    l, w = random.randint(2, 20), random.randint(2, 20)
    problem = f"A rectangle has an area of ${l * w}$ square units and a length of ${l}$ units. What is its width?"
    solution = f"{w}"
    s = Steps()
    s.step("Area is length times width, so divide.", rf"{l * w} \div {l} = {w}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_area_of_rectangle.variant("l_shape")
def _rectangle_l_shape():
    """An L-shape split into two rectangles."""
    W, H = random.randint(5, 15), random.randint(5, 15)
    cw, ch = random.randint(1, W - 2), random.randint(1, H - 2)
    area = W * H - cw * ch
    problem = (
        f"A ${W}$ by ${H}$ rectangle has a ${cw}$ by ${ch}$ rectangle cut from one corner, leaving an L-shape. What is the area "
        "of the L-shape?"
    )
    solution = f"{area}"
    s = Steps()
    s.step("Subtract the cut-out from the whole rectangle.", rf"{W} \times {H} - {cw} \times {ch} = {area}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_compare_numbers.variant("tens_and_ones")
def _compare_tens_ones():
    """Compare numbers given as tens and ones (with regrouping)."""
    t1, o1 = random.randint(1, 4), random.randint(10, 19)
    t2, o2 = random.randint(1, 5), random.randint(0, 9)
    a, b = t1 * 10 + o1, t2 * 10 + o2
    if a == b:
        o2 += 1
        b += 1
    problem = (
        f"Which is greater: ${t1}$ tens and ${o1}$ ones, or ${t2}$ tens and ${o2}$ ones? Type the greater number as a numeral."
    )
    solution = f"{max(a, b)}"
    s = Steps()
    s.step("Write each as a number.", f"{t1 * 10} + {o1} = {a}, \\quad {t2 * 10} + {o2} = {b}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_compare_three_digit.variant("missing_digit")
def _compare_missing_digit():
    r"""The smallest digit that makes $4\square7 > 459$ true."""
    h = random.randint(1, 9)
    other_t = random.randint(0, 8)
    o1, o2 = random.randint(0, 9), random.randint(0, 9)
    right = h * 100 + other_t * 10 + o2
    digits = [d for d in range(10) if h * 100 + d * 10 + o1 > right]
    problem = f"What is the smallest digit that can go in the box to make ${h}\\square{o1} > {right}$ true?"
    solution = f"{min(digits)}"
    s = Steps()
    s.step("The hundreds match, so compare the tens (and then the ones).", f"{h}{min(digits)}{o1} > {right}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_missing_number_sequence.variant("missing_first")
def _sequence_missing_first():
    """Reverse: the missing first number of a skip-counting pattern."""
    d = random.choice([2, 3, 5, 10, -2, -5])
    first = random.randint(10, 60)
    terms = [first + i * d for i in range(5)]
    shown = "?, " + ", ".join(map(str, terms[1:]))
    problem = f"What is the missing first number? ${shown}$"
    solution = f"{first}"
    s = Steps()
    s.step("Find the rule: the amount added each time.", f"{terms[2]} - {terms[1]} = {d}")
    s.step("Go one step back from the second number.", f"{terms[1]} - ({d}) = {first}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_even_or_odd.variant("sum_or_product")
def _even_odd_sum_product():
    """Is a sum or product even or odd, without computing it?"""
    a, b = random.randint(10, 99), random.randint(10, 99)
    if random.random() < 0.5:
        problem = f"Without adding, is ${a} + {b}$ even or odd? Answer even or odd."
        answer = "even" if (a + b) % 2 == 0 else "odd"
        why = "Even + even and odd + odd are even; even + odd is odd."
    else:
        problem = f"Without multiplying, is ${a} \\times {b}$ even or odd? Answer even or odd."
        answer = "even" if (a * b) % 2 == 0 else "odd"
        why = "A product is odd only when both factors are odd."
    s = Steps()
    s.step(why, f"{a} \\text{{ is {'even' if a % 2 == 0 else 'odd'}}}, \\quad {b} \\text{{ is {'even' if b % 2 == 0 else 'odd'}}}")
    s.answer(answer)
    return problem, answer, s.done()


@ar.arith_ordinal_number.variant("from_the_back")
def _ordinal_from_back():
    """Position from the back of a line."""
    n = random.randint(5, 30)
    k = random.randint(1, n)
    problem = f"There are ${n}$ children in a line. Sam is {_ordinal(k)} from the front. What position is Sam from the back?"
    solution = _ordinal(n - k + 1)
    s = Steps()
    s.step("Count the children behind Sam, then add Sam.", f"{n} - {k} + 1 = {n - k + 1}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_word_problem_within_20.variant("change_unknown")
def _story_change_unknown():
    """A story where the change is unknown."""
    start = random.randint(1, 12)
    change = random.randint(1, 20 - start)
    problem = f"Mia had ${start}$ shells. She found some more, and now she has ${start + change}$. How many shells did she find?"
    solution = f"{change}"
    s = Steps()
    s.step("Find the difference between what she has now and what she had.", f"{start + change} - {start} = {change}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_add_subtract_within_1000.variant("compensation")
def _within_1000_compensation():
    r"""$472 + 318 = 470 + \square$."""
    a, b = random.choice([x for x in range(101, 700) if x % 10]), random.randint(101, 299)
    down = a % 10
    problem = rf"Fill in the box: ${a} + {b} = {a - down} + \square$"
    solution = f"{b + down}"
    s = Steps()
    s.step(f"${a}$ became ${a - down}$, which is ${down}$ less, so add ${down}$ to the other number.", f"{b} + {down} = {b + down}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_tell_time_five_min.variant("quarter_and_before")
def _tell_time_phrases():
    """'Quarter to 4', '20 minutes before 5', or a time after a given one."""
    h = random.randint(1, 12)
    kind = random.choice(["quarter_to", "before", "after"])
    s = Steps()
    if kind == "quarter_to":
        problem = f"Write 'quarter to {h}' as a time. Format as H:MM."
        t = h * 60 - 15
        s.step(f"Quarter to {h} is 15 minutes before {h}:00.")
    elif kind == "before":
        m = random.choice([5, 10, 20, 25])
        problem = f"Write '{m} minutes before {h} o'clock' as a time. Format as H:MM."
        t = h * 60 - m
        s.step(f"Count back {m} minutes from {h}:00.")
    else:
        base = h * 60 + random.choice(range(0, 60, 5))
        m = random.choice(range(5, 60, 5))
        problem = f"What time is it {m} minutes after {_hm(base)}? Format as H:MM."
        t = base + m
        s.step(f"Count forward {m} minutes from {_hm(base)}.")
    solution = _hm(t)
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_count_money_value.variant("fewest_coins")
def _money_fewest_coins():
    """The fewest coins (quarters, dimes, nickels, pennies) that make an amount."""
    cents = random.randint(6, 99)
    left, coins = cents, 0
    for c in (25, 10, 5, 1):
        coins += left // c
        left %= c
    problem = f"What is the fewest number of coins (quarters, dimes, nickels, pennies) that make ${cents}$ cents?"
    solution = f"{coins}"
    q, r = divmod(cents, 25)
    d, r = divmod(r, 10)
    n, p = divmod(r, 5)
    s = Steps()
    s.step("Use the largest coins first.", f"{q} \\text{{ quarters}}, {d} \\text{{ dimes}}, {n} \\text{{ nickels}}, {p} \\text{{ pennies}}")
    s.step("Count the coins.", f"{q} + {d} + {n} + {p} = {coins}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_array_repeated_addition.variant("rows_from_total")
def _array_rows_from_total():
    """Reverse: equal rows from the total."""
    rows, per = random.randint(2, 10), random.randint(2, 10)
    problem = f"${rows * per}$ chairs are set up in ${rows}$ equal rows. How many chairs are in each row?"
    solution = f"{per}"
    s = Steps()
    s.step("Equal rows: divide the total by the number of rows.", rf"{rows * per} \div {rows} = {per}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_array_repeated_addition.variant("repeated_addition")
def _array_repeated_addition():
    r"""$5 + 5 + 5 + 5 = \square \times 5$."""
    n, k = random.randint(2, 10), random.randint(2, 8)
    problem = "Fill in the box: $" + " + ".join([str(n)] * k) + rf" = \square \times {n}$"
    solution = f"{k}"
    s = Steps()
    s.step(f"Count how many ${n}$s are added.", f"{k} \\times {n}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_equivalent_fraction.variant("fraction_of_set")
def _equivalent_fraction_of_set():
    """3/4 of a 12-slice pizza is how many slices?"""
    d = random.choice([2, 3, 4, 5, 6, 8])
    n = random.choice([x for x in range(1, d) if math.gcd(x, d) == 1])
    total = d * random.randint(1, 4)
    problem = f"A pizza is cut into ${total}$ equal slices. How many slices make ${n}/{d}$ of the pizza?"
    solution = f"{total * n // d}"
    s = Steps()
    s.step(f"Split the slices into ${d}$ equal groups, then take ${n}$ of them.", rf"{total} \div {d} \times {n} = {total * n // d}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_missing_factor.variant("equal_products")
def _missing_factor_equal_products():
    r"""$6 \times \square = 3 \times 14$."""
    a, b = random.randint(2, 9), random.randint(2, 12)
    k = random.choice([2, 3])
    problem = rf"Fill in the box: ${a * k} \times \square = {a} \times {b * k}$"
    solution = f"{b}"
    s = Steps()
    s.step("Find the product on the right, then divide.", rf"{a} \times {b * k} = {a * b * k}, \quad {a * b * k} \div {a * k} = {b}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_fraction_on_number_line.variant("which_tick")
def _number_line_which_tick():
    """Reverse: which tick mark shows a fraction?"""
    parts = random.choice([4, 6, 8, 10, 12])
    d = random.choice([x for x in (2, 3, 4, 5, 6) if parts % x == 0])
    n = random.choice([x for x in range(1, d) if math.gcd(x, d) == 1])
    problem = (
        f"A number line from $0$ to $1$ is divided into ${parts}$ equal parts. Which tick mark to the right of $0$ shows "
        f"${n}/{d}$? (Type 3 for the 3rd tick.)"
    )
    solution = f"{n * parts // d}"
    s = Steps()
    s.step(f"Rewrite ${n}/{d}$ with denominator ${parts}$.", rf"\frac{{{n}}}{{{d}}} = \frac{{{n * parts // d}}}{{{parts}}}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_fraction_times_whole.variant("whole_from_part")
def _fraction_whole_from_part():
    """Reverse: 2/3 of a number is 12; find the number."""
    d = random.randint(2, 9)
    n = random.choice([x for x in range(1, d) if math.gcd(x, d) == 1])
    whole = d * random.randint(1, 10)
    part = whole * n // d
    problem = f"${n}/{d}$ of a number is ${part}$. What is the number?"
    solution = f"{whole}"
    s = Steps()
    s.step(f"${part}$ is ${n}$ of ${d}$ equal parts, so one part is ${part // n}$.", rf"{part} \div {n} = {part // n}")
    s.step(f"Multiply by ${d}$.", rf"{part // n} \times {d} = {whole}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_mixed_to_improper.variant("whole_part")
def _improper_whole_part():
    """Between which whole numbers an improper fraction lies."""
    d = random.randint(2, 9)
    n = random.randint(d + 1, d * 9)
    while n % d == 0:
        n += 1
    problem = f"${n}/{d}$ is between two whole numbers next to each other. What is the smaller one?"
    solution = f"{n // d}"
    s = Steps()
    s.step("Divide the numerator by the denominator.", rf"{n} \div {d} = {n // d} \text{{ R }} {n % d}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_long_division_remainder.variant("interpret")
def _long_division_interpret():
    """Interpreting the remainder in context, or rebuilding the dividend."""
    if random.random() < 0.5:
        return _division_interpret_remainder()
    d, q = random.randint(2, 12), random.randint(2, 30)
    r = random.randint(1, d - 1)
    problem = f"A number divided by ${d}$ gives ${q}$ R ${r}$. What is the number?"
    solution = f"{d * q + r}"
    s = Steps()
    s.step("Multiply back and add the remainder.", rf"{d} \times {q} + {r} = {d * q + r}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_angle_addition.variant("bisector")
def _angle_bisector():
    """A ray that bisects an angle splits it in half (or reverse)."""
    whole = random.choice(range(20, 181, 2))
    if random.random() < 0.5:
        problem = f"Ray BD bisects angle ABC, which measures ${whole}^\\circ$. What is the measure of angle ABD, in degrees?"
        solution = f"{whole // 2}"
        s = Steps()
        s.step("A bisector splits an angle into two equal angles.", rf"{whole} \div 2 = {whole // 2}")
    else:
        problem = f"Ray BD bisects angle ABC, and angle ABD measures ${whole // 2}^\\circ$. What is angle ABC, in degrees?"
        solution = f"{whole}"
        s = Steps()
        s.step("The two halves are equal.", rf"2 \times {whole // 2} = {whole}")
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_factor_pairs_count.variant("rectangles")
def _factor_pairs_rectangles():
    """How many rectangles can be built from n square tiles."""
    n = random.randint(6, 100)
    pairs = [(a, n // a) for a in range(1, math.isqrt(n) + 1) if n % a == 0]
    problem = f"How many different rectangles can be made using all ${n}$ square tiles? (A $2 \\times 3$ and a $3 \\times 2$ count as the same.)"
    solution = f"{len(pairs)}"
    s = Steps()
    s.step("Each rectangle is a factor pair.", r",\ ".join(f"{a} \\times {b}" for a, b in pairs))
    s.answer(solution)
    return problem, solution, s.done()


@ar.arith_round_decimal.variant("smallest_that_rounds")
def _round_decimal_reverse():
    """Reverse: the smallest 2-decimal number that rounds to a tenth."""
    target = Fraction(random.randint(11, 99), 10)
    smallest = random.random() < 0.5
    value = target - Fraction(5, 100) if smallest else target + Fraction(4, 100)
    problem = f"A number with two decimal places rounds to ${num(target)}$ (nearest tenth). What is the {'smallest' if smallest else 'largest'} it could be?"
    solution = num(value)
    s = Steps()
    s.step(f"Numbers from ${num(target - Fraction(5, 100))}$ to ${num(target + Fraction(4, 100))}$ round to ${num(target)}$.")
    s.answer(solution)
    return problem, solution, s.done()
