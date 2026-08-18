"""Solveki-local arithmetic generators (Georgia grade 1-5 topics).

Each generator takes no required arguments and returns a ``(problem,
solution)`` tuple of two strings, with math wrapped in LaTeX ``$...$``. Answers
are kept clean: integers, short terminating decimals, or reduced fraction
strings like ``"3/4"``.
"""
import random
from decimal import Decimal, ROUND_HALF_UP
from math import gcd

from ._registry import register
from ._format import frac


def _reduce(num, den):
    """Return a reduced fraction string, or a plain integer string.

    ``num`` is assumed non-negative and ``den`` positive.
    """
    if num == 0:
        return "0"
    g = gcd(num, den)
    num //= g
    den //= g
    if den == 1:
        return str(num)
    return f"{num}/{den}"


def _fmt(value):
    """Format a Decimal/int as a plain decimal string with no trailing zeros."""
    d = Decimal(value).normalize()
    # Avoid exponent notation (e.g. '1E+2') that .normalize() can produce.
    return format(d, "f")


def _rand_decimal(max_int=99, dp_choices=(1, 2)):
    """Return a random non-negative decimal *string* with 1 or 2 dp."""
    dp = random.choice(dp_choices)
    whole = random.randint(0, max_int)
    frac = random.randint(0, 10 ** dp - 1)
    return f"{whole}.{frac:0{dp}d}"


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@register
def arith_place_value(min_length=3, max_length=5):
    r"""Place Value

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is the value of the digit 7 in the number 4738? | $700$ |
    """
    length = random.randint(min_length, max_length)
    # Distinct nonzero digits guarantee the chosen digit occurs exactly once
    # and the number has no leading zero.
    digits = random.sample(range(1, 10), length)
    number = int("".join(str(d) for d in digits))
    idx = random.randrange(length)
    digit = digits[idx]
    place = 10 ** (length - 1 - idx)
    value = digit * place
    problem = f"What is the value of the digit {digit} in the number {number}?"
    solution = f"${value}$"
    return problem, solution


@register
def arith_rounding(max_n=100000):
    r"""Rounding

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Round 4738 to the nearest hundred. | $4700$ |
    """
    place_name, p = random.choice(
        [("ten", 10), ("hundred", 100), ("thousand", 1000)]
    )
    n = random.randint(p, max_n)
    rounded = ((n + p // 2) // p) * p  # round half up
    problem = f"Round {n} to the nearest {place_name}."
    solution = f"${rounded}$"
    return problem, solution


@register
def arith_add_fractions(max_den=12):
    r"""Add Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $\frac{1}{2} + \frac{1}{3}$ | $5/6$ |
    """
    b = random.randint(2, max_den)
    d = random.randint(2, max_den)
    a = random.randint(1, b - 1)
    c = random.randint(1, d - 1)
    num = a * d + c * b
    den = b * d
    problem = (
        f"Simplify $\\frac{{{a}}}{{{b}}} + \\frac{{{c}}}{{{d}}}$. "
        f"Express your answer as a fraction in the form a/b, or an integer."
    )
    solution = f"${_reduce(num, den)}$"
    return problem, solution


@register
def arith_subtract_fractions(max_den=12):
    r"""Subtract Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $\frac{3}{4} - \frac{1}{2}$ | $1/4$ |
    """
    b = random.randint(2, max_den)
    d = random.randint(2, max_den)
    a = random.randint(1, b - 1)
    c = random.randint(1, d - 1)
    # Order so the result is non-negative.
    if a * d < c * b:
        a, b, c, d = c, d, a, b
    num = a * d - c * b
    den = b * d
    problem = (
        f"Simplify $\\frac{{{a}}}{{{b}}} - \\frac{{{c}}}{{{d}}}$. "
        f"Express your answer as a fraction in the form a/b, or an integer."
    )
    solution = f"${_reduce(num, den)}$"
    return problem, solution


@register
def arith_compare_decimals(max_int=99):
    r"""Compare Decimals

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Which is greater: $3.4$ or $3.45$? | $3.45$ |
    """
    x = _rand_decimal(max_int=max_int)
    y = _rand_decimal(max_int=max_int)
    while Decimal(x) == Decimal(y):
        y = _rand_decimal()
    larger = x if Decimal(x) > Decimal(y) else y
    problem = f"Which is greater: ${x}$ or ${y}$?"
    solution = f"${larger}$"
    return problem, solution


@register
def arith_add_decimals(max_int=99):
    r"""Add Decimals

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $12.5 + 3.25$ | $15.75$ |
    """
    x = _rand_decimal(max_int=max_int)
    y = _rand_decimal(max_int=max_int)
    res = Decimal(x) + Decimal(y)
    problem = f"Calculate ${x} + {y}$"
    solution = f"${_fmt(res)}$"
    return problem, solution


@register
def arith_subtract_decimals(max_int=99):
    r"""Subtract Decimals

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $12.5 - 3.25$ | $9.25$ |
    """
    x = _rand_decimal(max_int=max_int)
    y = _rand_decimal(max_int=max_int)
    if Decimal(x) < Decimal(y):
        x, y = y, x
    res = Decimal(x) - Decimal(y)
    problem = f"Calculate ${x} - {y}$"
    solution = f"${_fmt(res)}$"
    return problem, solution


@register
def arith_multiply_decimals(max_int=12):
    r"""Multiply Decimals

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $2.5 \times 3.2$ | $8$ |
    """
    x = _rand_decimal(max_int=max_int, dp_choices=(1,))
    y = _rand_decimal(max_int=max_int, dp_choices=(1,))
    res = Decimal(x) * Decimal(y)
    problem = f"Calculate ${x} \\times {y}$"
    solution = f"${_fmt(res)}$"
    return problem, solution


@register
def arith_order_of_operations(max_val=12):
    r"""Order of Operations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $(3 + 4) \times 2 - 5$ | $9$ |
    """
    a = random.randint(1, max_val)
    b = random.randint(1, max_val)
    c = random.randint(1, max_val)
    d = random.randint(1, max_val)
    templates = [
        f"({a} + {b}) \\times {c}",
        f"{a} \\times ({b} - {c})",
        f"{a} + {b} \\times {c} - {d}",
        f"({a} - {b}) \\times ({c} + {d})",
        f"{a} \\times {b} + {c}",
    ]
    expr = random.choice(templates)
    value = eval(expr.replace("\\times", "*"), {"__builtins__": {}}, {})
    problem = f"Evaluate ${expr}$"
    solution = f"${value}$"
    return problem, solution


@register
def arith_nth_multiple(max_n=20, max_base=12):
    r"""Nth Multiple

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is the 4th multiple of 7? | $28$ |
    """
    n = random.randint(2, max_n)
    base = random.randint(2, max_base)
    value = n * base
    problem = f"What is the {_ordinal(n)} multiple of {base}?"
    solution = f"${value}$"
    return problem, solution


@register
def arith_powers_of_ten(max_k=3):
    r"""Powers of Ten

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $34 \times 10^{2}$ | $3400$ |
    """
    k = random.randint(1, max_k)
    p = 10 ** k
    if random.random() < 0.5:
        n = random.randint(1, 999)
        res = Decimal(n) * Decimal(p)
        problem = f"Calculate ${n} \\times 10^{{{k}}}$"
    else:
        n = random.randint(1, 9999)
        res = Decimal(n) / Decimal(p)
        problem = f"Calculate ${n} \\div 10^{{{k}}}$"
    solution = f"${_fmt(res)}$"
    return problem, solution


# Conversion factors, each unit expressed in the system's smallest unit.
_LENGTH_SYSTEMS = {
    "metric": {"km": 100000, "m": 100, "cm": 1},
    "customary": {"yd": 36, "ft": 12, "in": 1},
}


@register
def arith_length_conversion(max_value=20):
    r"""Length Conversion

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert 5 km to m. | $5000$ |
    """
    units = random.choice(list(_LENGTH_SYSTEMS.values()))
    from_unit, to_unit = random.sample(list(units), 2)
    f_from = units[from_unit]
    f_to = units[to_unit]
    if f_from >= f_to:
        value = random.randint(1, max_value)
    else:
        # Smaller -> larger unit: pick a value that divides cleanly.
        step = f_to // f_from
        value = random.randint(1, max_value) * step
    result = value * f_from // f_to
    problem = f"Convert {value} {from_unit} to {to_unit}."
    solution = f"${result}$"
    return problem, solution


@register
def arith_minutes_to_hours():
    r"""Convert Minutes to Hours and Minutes

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert 135 minutes to hours and minutes. | $2 hr 15 min$ |

    Overrides the stock ``mathgenerator`` ``minutes_to_hours`` generator, which
    states no answer format. The total is at least one hour so the answer always
    has an hours part; the requested ``H hr M min`` form is stated explicitly.
    """
    total = random.randint(61, 599)
    h, m = divmod(total, 60)
    problem = (
        f"Convert {total} minutes to hours and minutes. "
        f"Format your answer as 'H hr M min' (for example, 2 hr 15 min)."
    )
    return problem, f"{h} hr {m} min"


@register
def arith_elapsed_time():
    r"""Elapsed Time

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A movie starts at 4:15 and lasts 30 minutes. ... | $4:45$ |

    Grade-2 friendly: the start hour is small (1-9), minutes fall on a 5-minute
    mark, and the duration is a small multiple of 5, so the arithmetic stays
    simple and the arrival never wraps past 12.
    """
    h = random.randint(1, 9)
    m = random.choice(range(0, 60, 5))
    dur = random.choice(range(5, 60, 5))
    total = h * 60 + m + dur
    eh, em = divmod(total, 60)
    start = f"{h}:{m:02d}"
    problem = (
        f"A movie starts at {start} and lasts {dur} minutes. "
        f"What time does it end? Format your answer as H:MM."
    )
    solution = f"${eh}:{em:02d}$"
    return problem, solution


@register
def arith_money(max_cents=5000):
    r"""Money

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the result in dollars: $9.25 + 3.50$ | $12.75$ |
    """
    op = random.choice(["+", "-"])
    a = (Decimal(random.randint(1, max_cents)) / 100).quantize(Decimal("0.01"))
    b = (Decimal(random.randint(1, max_cents)) / 100).quantize(Decimal("0.01"))
    if op == "-" and a < b:
        a, b = b, a
    res = (a + b if op == "+" else a - b).quantize(Decimal("0.01"))
    problem = f"Find the result in dollars: ${a} {op} {b}$"
    solution = f"${res}$"
    return problem, solution


@register
def arith_area_of_rectangle(max_side=50):
    r"""Area of a Rectangle

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A rectangle has length 7 units and width 4 units. ... | $28$ |
    """
    length = random.randint(1, max_side)
    width = random.randint(1, max_side)
    area = length * width
    problem = (
        f"A rectangle has length {length} units and width {width} units. "
        f"What is its area in square units?"
    )
    solution = f"${area}$"
    return problem, solution


@register
def arith_compare_numbers(max_n=20):
    r"""Compare Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Fill in the blank with >, <, or =: $7 \,\square\, 4$. | > |
    """
    a = random.randint(0, max_n)
    # Make an equals result reasonably common, otherwise pick an independent b.
    if random.random() < 0.3:
        b = a
    else:
        b = random.randint(0, max_n)
    symbol = ">" if a > b else "<" if a < b else "="
    problem = f"Fill in the blank with >, <, or =: ${a} \\,\\square\\, {b}$."
    return problem, symbol


@register
def arith_missing_number_sequence(length=5):
    r"""Missing Number in a Sequence

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the missing number in the sequence: 2, 4, ?, 8, 10. | $6$ |
    """
    start = random.randint(0, 10)
    diff = random.randint(1, 5)
    seq = [start + i * diff for i in range(length)]
    # Blank an interior term so both neighbours are shown.
    idx = random.randint(1, length - 2)
    missing = seq[idx]
    shown = [("?" if i == idx else str(v)) for i, v in enumerate(seq)]
    problem = (
        f"Find the missing number in the sequence: {', '.join(shown)}."
    )
    solution = f"${missing}$"
    return problem, solution


@register
def arith_even_or_odd(max_n=100):
    r"""Even or Odd

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Is $13$ even or odd? Answer 'even' or 'odd'. | odd |
    """
    n = random.randint(1, max_n)
    answer = "even" if n % 2 == 0 else "odd"
    problem = f"Is ${n}$ even or odd? Answer 'even' or 'odd'."
    return problem, answer


@register
def arith_ordinal_number(max_n=100):
    r"""Ordinal Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Write the ordinal number for $5$ (for example, 3 -> 3rd). | 5th |
    """
    n = random.randint(1, max_n)
    problem = (
        f"Write the ordinal number for ${n}$ (for example, 3 -> 3rd)."
    )
    return problem, _ordinal(n)


@register
def arith_word_problem_within_20():
    r"""Add and Subtract Word Problem within 20

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | There are 6 red apples and 7 green apples in a basket. How many apples are there in all? | $13$ |
    """
    if random.random() < 0.5:
        # Addition; keep the total within 20.
        a = random.randint(1, 10)
        b = random.randint(1, 20 - a)
        answer = a + b
        problem = (
            f"There are {a} red apples and {b} green apples in a basket. "
            f"How many apples are there in all?"
        )
    else:
        # Subtraction; keep both operands and the result positive.
        a = random.randint(2, 20)
        b = random.randint(1, a - 1)
        answer = a - b
        problem = (
            f"There are {a} ducks in a pond. {b} ducks swim away. "
            f"How many ducks are left?"
        )
    solution = f"${answer}$"
    return problem, solution


@register
def arith_add_subtract_within_1000():
    r"""Add and Subtract within 1000

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $472 + 318$ | $790$ |
    """
    if random.random() < 0.5:
        a = random.randint(0, 1000)
        b = random.randint(0, 1000 - a)
        answer = a + b
        problem = f"Calculate ${a} + {b}$"
    else:
        a = random.randint(0, 1000)
        b = random.randint(0, a)
        answer = a - b
        problem = f"Calculate ${a} - {b}$"
    solution = f"${answer}$"
    return problem, solution


@register
def arith_tell_time_five_min():
    r"""Tell Time to the Nearest 5 Minutes

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Write '25 minutes past 3 o'clock' as a time. Format as H:MM. | $3:25$ |
    """
    h = random.randint(1, 12)
    m = random.choice(range(5, 60, 5))
    problem = (
        f"Write '{m} minutes past {h} o'clock' as a time. Format as H:MM."
    )
    solution = f"${h}:{m:02d}$"
    return problem, solution


@register
def arith_count_money_value():
    r"""Count Money Value

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | You have 2 quarters, 3 dimes, 1 nickel, and 4 pennies. What is the total value? Format your answer as a dollar amount like $X.XX. | $0.89 |
    """
    while True:
        q = random.randint(0, 4)
        d = random.randint(0, 4)
        n = random.randint(0, 4)
        p = random.randint(0, 9)
        cents = q * 25 + d * 10 + n * 5 + p
        if cents > 0:
            break
    dollars, rem = divmod(cents, 100)
    problem = (
        f"You have {q} quarters, {d} dimes, {n} nickels, and {p} pennies. "
        f"What is the total value? "
        f"Format your answer as a dollar amount like $X.XX."
    )
    solution = f"${dollars}.{rem:02d}"
    return problem, solution


@register
def arith_array_repeated_addition(max_side=10):
    r"""Arrays and Repeated Addition

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | An array has 4 rows with 6 dots in each row. How many dots are there in total? | $24$ |
    """
    rows = random.randint(2, max_side)
    cols = random.randint(2, max_side)
    total = rows * cols
    problem = (
        f"An array has {rows} rows with {cols} dots in each row. "
        f"How many dots are there in total?"
    )
    solution = f"${total}$"
    return problem, solution


@register
def arith_compare_three_digit():
    r"""Compare 3-Digit Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Fill in the blank with >, <, or =: $472 \,\square\, 419$. | > |
    """
    a = random.randint(100, 999)
    if random.random() < 0.3:
        b = a
    else:
        b = random.randint(100, 999)
    symbol = ">" if a > b else "<" if a < b else "="
    problem = f"Fill in the blank with >, <, or =: ${a} \\,\\square\\, {b}$."
    return problem, symbol


@register
def arith_equivalent_fraction():
    r"""Equivalent Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the missing number: $\frac{2}{3} = \frac{\square}{12}$. Express your answer as an integer. | $8$ |
    """
    b = random.randint(2, 9)
    a = random.randint(1, b - 1)
    k = random.randint(2, 6)
    d = b * k
    answer = a * k
    problem = (
        f"Find the missing number: "
        f"$\\frac{{{a}}}{{{b}}} = \\frac{{\\square}}{{{d}}}$. "
        f"Express your answer as an integer."
    )
    solution = f"${answer}$"
    return problem, solution


@register
def arith_missing_factor(max_factor=12):
    r"""Missing Factor

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the missing factor: $6 \times \square = 42$. Express your answer as an integer. | $7$ |
    """
    a = random.randint(2, max_factor)
    factor = random.randint(2, max_factor)
    c = a * factor
    problem = (
        f"Find the missing factor: ${a} \\times \\square = {c}$. "
        f"Express your answer as an integer."
    )
    solution = f"${factor}$"
    return problem, solution


@register
def arith_fraction_on_number_line(max_parts=10):
    r"""Fraction on a Number Line

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A number line from 0 to 1 is divided into 4 equal parts. What fraction does the 3rd tick mark to the right of 0 represent? Give your answer as a reduced fraction a/b or an integer. | $3/4$ |
    """
    b = random.randint(2, max_parts)
    a = random.randint(1, b - 1)
    problem = (
        f"A number line from 0 to 1 is divided into {b} equal parts. "
        f"What fraction does the {_ordinal(a)} tick mark to the right of 0 "
        f"represent? Give your answer as a reduced fraction a/b or an integer."
    )
    solution = f"${frac(a, b)}$"
    return problem, solution


@register
def arith_two_step_word_problem():
    r"""Two-Step Word Problem

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A store had 12 apples. It received 5 crates with 8 apples in each crate. How many apples does the store have now? | $52$ |
    """
    start = random.randint(5, 30)
    crates = random.randint(2, 9)
    per = random.randint(2, 12)
    answer = start + crates * per
    problem = (
        f"A store had {start} apples. It received {crates} crates with "
        f"{per} apples in each crate. How many apples does the store have now?"
    )
    solution = f"${answer}$"
    return problem, solution


@register
def arith_fraction_times_whole(max_den=9):
    r"""Multiply a Fraction by a Whole Number

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $4 \times \frac{2}{3}$. Express your answer as a fraction in the form a/b, or an integer. | $8/3$ |
    """
    k = random.randint(2, 10)
    b = random.randint(2, max_den)
    a = random.randint(1, b - 1)
    problem = (
        f"Calculate ${k} \\times \\frac{{{a}}}{{{b}}}$. "
        f"Express your answer as a fraction in the form a/b, or an integer."
    )
    solution = f"${frac(k * a, b)}$"
    return problem, solution


@register
def arith_mixed_to_improper(max_den=9):
    r"""Mixed and Improper Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert the mixed number 2 1/3 to an improper fraction. Format as p/q. | $7/3$ |
    """
    c = random.randint(2, max_den)
    a = random.randint(1, 9)
    b = random.randint(1, c - 1)
    p = a * c + b
    problem = (
        f"Convert the mixed number {a} {b}/{c} to an improper fraction. "
        f"Format as p/q."
    )
    solution = f"${p}/{c}$"
    return problem, solution


@register
def arith_long_division_remainder():
    r"""Long Division with Remainder

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $47 \div 6$. Give the quotient and remainder in the form 'q R r'. | $7 R 5$ |
    """
    b = random.randint(2, 12)
    a = random.randint(b + 1, 200)
    q, r = divmod(a, b)
    problem = (
        f"${a} \\div {b}$. "
        f"Give the quotient and remainder in the form 'q R r'."
    )
    solution = f"${q} R {r}$"
    return problem, solution


@register
def arith_angle_addition():
    r"""Angle Addition

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Angle ABD and angle DBC are adjacent angles that together form angle ABC. If angle ABC = 90 degrees and angle ABD = 35 degrees, what is the measure of angle DBC in degrees? | $55$ |
    """
    total = random.choice([90, 120, 150, 180])
    known = random.randint(1, total - 1)
    missing = total - known
    problem = (
        f"Angle ABD and angle DBC are adjacent angles that together form "
        f"angle ABC. If angle ABC = {total} degrees and angle ABD = {known} "
        f"degrees, what is the measure of angle DBC in degrees?"
    )
    solution = f"${missing}$"
    return problem, solution


@register
def arith_factor_pairs_count(max_n=60):
    r"""Factor Pairs Count

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | How many factor pairs does $12$ have? | $3$ |
    """
    n = random.randint(2, max_n)
    divisors = sum(1 for k in range(1, n + 1) if n % k == 0)
    pairs = (divisors + 1) // 2
    problem = f"How many factor pairs does ${n}$ have?"
    solution = f"${pairs}$"
    return problem, solution


@register
def arith_add_unlike_fractions(max_den=12):
    r"""Add and Subtract Unlike Denominators

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $\frac{1}{2} + \frac{1}{3}$. Express your answer as a fraction in the form a/b, or an integer. | $5/6$ |
    """
    b = random.randint(2, max_den)
    d = random.randint(2, max_den)
    while d == b:
        d = random.randint(2, max_den)
    a = random.randint(1, b - 1)
    c = random.randint(1, d - 1)
    op = random.choice(["+", "-"])
    if op == "-" and a * d < c * b:
        # Keep the difference non-negative by swapping the two fractions.
        a, b, c, d = c, d, a, b
    num = a * d + c * b if op == "+" else a * d - c * b
    den = b * d
    problem = (
        f"Simplify $\\frac{{{a}}}{{{b}}} {op} \\frac{{{c}}}{{{d}}}$. "
        f"Express your answer as a fraction in the form a/b, or an integer."
    )
    solution = f"${_reduce(num, den)}$"
    return problem, solution


@register
def arith_round_decimal():
    r"""Round Decimals

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Round $3.472$ to the nearest hundredth. | $3.47$ |
    """
    whole = random.randint(0, 99)
    frac_part = random.randint(0, 999)
    x = Decimal(f"{whole}.{frac_part:03d}")
    place_name, quant = random.choice(
        [("tenth", Decimal("0.1")), ("hundredth", Decimal("0.01"))]
    )
    rounded = x.quantize(quant, rounding=ROUND_HALF_UP)
    problem = f"Round ${x}$ to the nearest {place_name}."
    solution = f"${_fmt(rounded)}$"
    return problem, solution


# Metric conversions, keyed by system. Each entry is (from, to, multiplier)
# where ``1 from = multiplier to``; multipliers are powers of ten so every
# result terminates within three decimal places for the sampled value range.
_METRIC_CONVERSIONS = [
    ("kg", "g", Decimal("1000")),
    ("g", "kg", Decimal("0.001")),
    ("L", "mL", Decimal("1000")),
    ("mL", "L", Decimal("0.001")),
    ("km", "m", Decimal("1000")),
    ("m", "km", Decimal("0.001")),
    ("m", "cm", Decimal("100")),
    ("cm", "m", Decimal("0.01")),
]


@register
def arith_metric_unit_conversion():
    r"""Metric Unit Conversion

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert 2500 g to kg. Give your answer in kg. | $2.5$ |
    """
    from_unit, to_unit, mult = random.choice(_METRIC_CONVERSIONS)
    value = random.randint(1, 999)
    result = Decimal(value) * mult
    problem = (
        f"Convert {value} {from_unit} to {to_unit}. "
        f"Give your answer in {to_unit}."
    )
    solution = f"${_fmt(result)}$"
    return problem, solution


@register
def arith_divide_decimals():
    r"""Divide Decimals

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $10.5 \div 7$. Give your answer as a decimal. | $1.5$ |
    """
    b = random.randint(2, 9)
    dp = random.choice([1, 2])
    whole = random.randint(1, 12)
    frac_part = random.randint(1, 10 ** dp - 1)
    q = Decimal(f"{whole}.{frac_part:0{dp}d}")
    a = q * b
    problem = (
        f"Calculate ${_fmt(a)} \\div {b}$. Give your answer as a decimal."
    )
    solution = f"${_fmt(q)}$"
    return problem, solution
