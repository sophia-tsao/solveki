"""Solveki-local arithmetic generators (Georgia grade 1-5 topics).

Each generator takes no required arguments and returns a ``(problem,
solution, steps)`` tuple: two strings, with math wrapped in LaTeX ``$...$``,
and a step-by-step explanation built with ``_steps.Steps``. Answers are kept
clean: integers, short terminating decimals, or reduced fraction strings like
``"3/4"``. These are elementary topics, so the steps use short, concrete
sentences.
"""
import random
from decimal import Decimal, ROUND_HALF_UP
from math import gcd, lcm

from ._registry import register
from ._format import frac
from ._steps import Steps, paren, tex_frac
from ._variants import with_variants


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


# ---------------------------------------------------------------------------
# Step-building helpers
# ---------------------------------------------------------------------------

_PLACES = ["ones", "tens", "hundreds", "thousands", "ten thousands"]
_PLACE_ONE = ["one", "ten", "hundred", "thousand", "ten thousand"]


def _answer_text(s, value, lead="The answer is"):
    """End on an answer like ``4:45`` or ``7 R 5`` set upright, not as math.

    In math mode a colon gets relation spacing and letters turn italic, so
    the value is wrapped in ``\\text``; it still reads verbatim.
    """
    s.answer(rf"$\text{{{value}}}$", lead=lead)


def _column(top, bottom, op, result=None):
    """A right-aligned column sum like ``472 / + 318 / ---- / 790``."""
    rows = rf"{top} \\ {op}\ {bottom} \\ \hline"
    if result is not None:
        rows += f" {result}"
    return rf"\begin{{array}}{{r}} {rows} \end{{array}}"


def _decimal_places(text):
    return len(text.split(".")[1]) if "." in text else 0


def _column_add_steps(s, a, b):
    """Column addition of whole numbers, one step per place, with carrying."""
    s.step("Line up the numbers by place value: ones under ones, tens under "
           "tens, hundreds under hundreds.", _column(a, b, "+"))
    da = [int(ch) for ch in reversed(str(a))]
    db = [int(ch) for ch in reversed(str(b))]
    cols = max(len(da), len(db))
    carry = 0
    for i in range(cols):
        name = _PLACES[i]
        terms = [d[i] for d in (da, db) if i < len(d)]
        if len(terms) == 1 and not carry:
            s.step(f"Bring down the ${terms[0]}$ in the {name} place.")
            continue
        total = sum(terms) + carry
        expr = " + ".join(str(t) for t in terms + [1] * carry)
        text = f"Add the {name}: ${expr} = {total}$"
        if carry:
            text += " (counting the 1 you carried)"
        if total >= 10 and i < cols - 1:
            text += f". Write ${total % 10}$ and carry the 1 to the {_PLACES[i + 1]}."
        else:
            text += f". Write ${total}$."
        s.step(text)
        carry = total // 10


def _column_subtract_steps(s, a, b):
    """Column subtraction of whole numbers, one step per place, with borrowing."""
    s.step("Line up the numbers by place value: ones under ones, tens under "
           "tens, hundreds under hundreds.", _column(a, b, "-"))
    da = [int(ch) for ch in reversed(str(a))]
    db = [int(ch) for ch in reversed(str(b))]
    borrow = 0
    for i, x in enumerate(da):
        name = _PLACES[i]
        has_y = i < len(db)
        y = db[i] if has_y else 0
        top = x - borrow
        lent = f"The {name} digit lent 1, so it is now ${top}$. " if borrow and top >= 0 else ""
        if top < 0:
            s.step(
                f"The {name} digit is $0$ and still has to lend 1, so borrow 1 "
                f"from the {_PLACES[i + 1]}: it becomes $10 - 1 = 9$, and "
                f"${9} - {y} = {9 - y}$."
            )
            borrow = 1
        elif top < y:
            s.step(
                f"{lent}Subtract the {name}: ${top}$ is less than ${y}$, so "
                f"borrow 1 from the {_PLACES[i + 1]}: ${top + 10} - {y} = {top + 10 - y}$."
            )
            borrow = 1
        elif not has_y and top == 0 and i == len(da) - 1:
            s.step(f"{lent}Nothing is left in the {name} place, so the answer "
                   f"has no {name} digit.")
            borrow = 0
        elif not has_y:
            s.step(f"{lent}Bring down the ${top}$ in the {name} place.")
            borrow = 0
        else:
            s.step(f"{lent}Subtract the {name}: ${top} - {y} = {top - y}$.")
            borrow = 0


def _decimal_column_steps(s, x, y, op, result, solution_value):
    """Add or subtract decimals in a column with the decimal points lined up.

    ``x`` and ``y`` are the decimal strings as shown in the problem;
    ``result`` the exact Decimal; ``solution_value`` the answer as served.
    """
    places = max(_decimal_places(x), _decimal_places(y))
    xp, yp = f"{Decimal(x):.{places}f}", f"{Decimal(y):.{places}f}"
    rp = f"{result:.{places}f}"
    if xp != x or yp != y:
        s.step(
            "Line up the decimal points. Write a zero at the end so both "
            f"numbers have {places} decimal places.",
            _column(xp, yp, op),
        )
    else:
        s.step("Line up the decimal points, one number under the other.",
               _column(xp, yp, op))
    if op == "+":
        how = "Add each column from right to left, carrying when a column adds up to 10 or more."
    else:
        how = "Subtract each column from right to left, borrowing when the top digit is too small."
    s.step(f"{how} Bring the decimal point straight down.", _column(xp, yp, op, rp))
    if rp != solution_value:
        s.step(f"Zeros at the end of a decimal don't change its value: ${rp} = {solution_value}$.")


def _fraction_steps(s, a, b, c, d, op):
    """Add or subtract ``a/b op c/d`` over a common denominator, then simplify.

    Returns the lead for the final answer step.
    """
    verb = "Add" if op == "+" else "Subtract"
    if b == d:
        den, na, nc = b, a, c
        combine = (f"The denominators are the same, so {verb.lower()} the "
                   "numerators and keep the denominator.")
    else:
        den = lcm(b, d)
        ka, kc = den // b, den // d
        na, nc = a * ka, c * kc
        s.step(f"The denominators are different. Find a common denominator: the "
               f"least common multiple of ${b}$ and ${d}$ is ${den}$.")
        parts = [
            rf"\frac{{{n}}}{{{dd}}} = \frac{{{n} \times {k}}}{{{dd} \times {k}}}"
            rf" = \frac{{{n * k}}}{{{den}}}"
            for n, dd, k in ((a, b, ka), (c, d, kc))
            if k > 1
        ]
        s.step(f"Rewrite each fraction with denominator ${den}$: multiply the top "
               "and bottom by the same number.", r",\qquad ".join(parts))
        combine = f"{verb} the numerators and keep the denominator."
    total = na + nc if op == "+" else na - nc
    s.step(combine, rf"{tex_frac(na, den)} {op} {tex_frac(nc, den)} = {tex_frac(total, den)}")
    if total == 0:
        return "The two fractions are equal, so the answer is"
    g = gcd(total, den)
    if g == den:
        s.step(f"The numerator is a multiple of the denominator, so this is a "
               f"whole number: ${total} \\div {den} = {total // den}$.")
        return "The answer is"
    if g > 1:
        s.step(f"Simplify: divide the numerator and denominator by ${g}$.",
               rf"{tex_frac(total, den)} = \frac{{{total} \div {g}}}{{{den} \div {g}}}"
               rf" = {tex_frac(total // g, den // g)}")
        return "In simplest form, the answer is"
    return "This is already in simplest form, so the answer is"


def _compare_symbol_step(s, a, b, symbol):
    """Explain which symbol to write once ``a`` and ``b`` have been compared."""
    if symbol == ">":
        s.step(f"${a}$ is greater than ${b}$. The symbol $>$ means \"is greater "
               "than\": its open side faces the bigger number.")
    elif symbol == "<":
        s.step(f"${a}$ is less than ${b}$. The symbol $<$ means \"is less "
               "than\": its open side faces the bigger number.")
    else:
        s.step("The two numbers are the same, so they are equal. Use $=$.")


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


@register
@with_variants
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

    pos = length - 1 - idx
    names = ", ".join(_PLACES[:length])
    s = Steps()
    s.step(f"Name the places in ${number}$, starting from the right: {names}. "
           f"The digit ${digit}$ is in the {_PLACES[pos]} place.")
    if pos == 0:
        s.step(f"A digit in the ones place is worth just itself, so it is worth ${digit}$.")
    else:
        unit = _PLACE_ONE[pos] if digit == 1 else _PLACES[pos]
        s.step(f"So the digit means ${digit}$ {unit}. Each {_PLACE_ONE[pos]} is ${place}$.",
               rf"{digit} \times {place} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    low = n // p * p
    high = low + p
    right = {10: "ones", 100: "tens", 1000: "hundreds"}[p]
    digit = n // (p // 10) % 10
    s = Steps()
    s.step(f"Find the two nearest {place_name}s: ${n}$ is between ${low}$ and ${high}$.")
    s.step(f"Look at the {right} digit, just to the right of the {place_name}s "
           f"place. In ${n}$ it is ${digit}$.")
    if digit >= 5:
        s.step(f"${digit}$ is 5 or more, so round up to ${high}$.")
    else:
        s.step(f"${digit}$ is less than 5, so round down to ${low}$.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    lead = _fraction_steps(s, a, b, c, d, "+")
    s.answer(solution, lead=lead)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    lead = _fraction_steps(s, a, b, c, d, "-")
    s.answer(solution, lead=lead)
    return problem, solution, s.done()


@register
@with_variants
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

    (wx, fx), (wy, fy) = x.split("."), y.split(".")
    s = Steps()
    if int(wx) != int(wy):
        big, small = max(int(wx), int(wy)), min(int(wx), int(wy))
        s.step(f"Compare the whole-number parts first: ${wx}$ and ${wy}$.")
        s.step(f"${big}$ is greater than ${small}$, so ${larger}$ is greater. "
               "The digits after the decimal point don't matter here.")
    else:
        s.step(f"The whole-number parts are both ${wx}$, so compare the digits "
               "after the decimal point.")
        fx, fy = fx.ljust(2, "0"), fy.ljust(2, "0")
        if len(x) != len(y):
            s.step("Write a zero at the end of the shorter decimal so both have "
                   "two decimal places. This doesn't change its value.",
                   rf"{wx}.{fx} \quad\text{{and}}\quad {wy}.{fy}")
        if fx[0] != fy[0]:
            s.step(f"Compare the tenths digits: ${fx[0]}$ and ${fy[0]}$. "
                   f"Since ${max(fx[0], fy[0])} > {min(fx[0], fy[0])}$, ${larger}$ is greater.")
        else:
            s.step(f"The tenths digits are both ${fx[0]}$. Compare the hundredths "
                   f"digits: ${fx[1]}$ and ${fy[1]}$. Since "
                   f"${max(fx[1], fy[1])} > {min(fx[1], fy[1])}$, ${larger}$ is greater.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    _decimal_column_steps(s, x, y, "+", res, _fmt(res))
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    _decimal_column_steps(s, x, y, "-", res, _fmt(res))
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    xi, yi = int(x.replace(".", "")), int(y.replace(".", ""))
    product = f"{res:.2f}"
    s = Steps()
    s.step("Multiply as if there were no decimal points.",
           rf"{xi} \times {yi} = {xi * yi}")
    s.step(f"${x}$ and ${y}$ each have 1 decimal place, so the product has "
           f"$1 + 1 = 2$ decimal places. Move the decimal point 2 places left "
           f"from the end of ${xi * yi}$.",
           rf"{x} \times {y} = {product}")
    if product != _fmt(res):
        s.step(f"Zeros at the end of a decimal don't change its value: ${product} = {_fmt(res)}$.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step("Use the order of operations: parentheses first, then multiplication "
           "and division, then addition and subtraction from left to right.")
    kind = templates.index(expr)
    if kind == 0:
        s.step(f"Parentheses first: ${a} + {b} = {a + b}$.", rf"{a + b} \times {c}")
        s.step(f"Multiply: ${a + b} \\times {c} = {value}$.")
    elif kind == 1:
        s.step(f"Parentheses first: ${b} - {c} = {b - c}$.", rf"{a} \times {paren(b - c)}")
        sign = " A positive times a negative is negative." if b - c < 0 else ""
        s.step(f"Multiply: ${a} \\times {paren(b - c)} = {value}$.{sign}")
    elif kind == 2:
        s.step(f"There are no parentheses, so multiply first: ${b} \\times {c} = {b * c}$.",
               f"{a} + {b * c} - {d}")
        s.step(f"Add and subtract from left to right: ${a} + {b * c} = {a + b * c}$, "
               f"then ${a + b * c} - {d} = {value}$.")
    elif kind == 3:
        s.step(f"Work out both parentheses: ${a} - {b} = {a - b}$ and ${c} + {d} = {c + d}$.",
               rf"{paren(a - b)} \times {c + d}")
        sign = " A negative times a positive is negative." if a - b < 0 else ""
        s.step(f"Multiply: ${paren(a - b)} \\times {c + d} = {value}$.{sign}")
    else:
        s.step(f"There are no parentheses, so multiply first: ${a} \\times {b} = {a * b}$.",
               f"{a * b} + {c}")
        s.step(f"Add: ${a * b} + {c} = {value}$.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    first = ", ".join(str(base * i) for i in range(1, 4))
    s = Steps()
    s.step(f"The multiples of ${base}$ are what you get when you skip count by "
           f"${base}$: ${first}, \\ldots$ The 1st multiple is ${base} \\times 1$, "
           f"the 2nd is ${base} \\times 2$, and so on.")
    s.step(f"So the {_ordinal(n)} multiple is ${base} \\times {n}$.",
           rf"{base} \times {n} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def arith_powers_of_ten(max_k=3):
    r"""Powers of Ten

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $34 \times 10^{2}$ | $3400$ |
    """
    k = random.randint(1, max_k)
    p = 10 ** k
    multiply = random.random() < 0.5
    if multiply:
        n = random.randint(1, 999)
        res = Decimal(n) * Decimal(p)
        problem = f"Calculate ${n} \\times 10^{{{k}}}$"
    else:
        n = random.randint(1, 9999)
        res = Decimal(n) / Decimal(p)
        problem = f"Calculate ${n} \\div 10^{{{k}}}$"
    solution = f"${_fmt(res)}$"

    places = "place" if k == 1 else "places"
    s = Steps()
    if k == 1:
        s.step("$10^{1}$ is just $10$: a 1 followed by 1 zero.")
    else:
        tens = r" \times ".join(["10"] * k)
        s.step(f"$10^{{{k}}}$ means {k} tens multiplied together: ${tens} = {p}$, "
               f"a 1 followed by {k} zeros.")
    if multiply:
        s.step(f"Multiplying by ${p}$ moves the decimal point {k} {places} to the "
               f"right. For a whole number, that means writing {k} "
               f"{'zero' if k == 1 else 'zeros'} at the end.",
               rf"{n} \times {p} = {_fmt(res)}")
    else:
        s.step(f"Dividing by ${p}$ moves the decimal point {k} {places} to the "
               "left. Start with the decimal point at the end of the number, and "
               "write zeros in front if you run out of digits.",
               rf"{n} \div {p} = {_fmt(res)}")
    s.answer(solution)
    return problem, solution, s.done()


# Conversion factors, each unit expressed in the system's smallest unit.
_LENGTH_SYSTEMS = {
    "metric": {"km": 100000, "m": 100, "cm": 1},
    "customary": {"yd": 36, "ft": 12, "in": 1},
}


@register
@with_variants
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

    s = Steps()
    if f_from >= f_to:
        ratio = f_from // f_to
        s.step(f"Know the conversion: 1 {from_unit} = ${ratio}$ {to_unit}.")
        s.step(f"You are changing to a smaller unit, so you need more of them. "
               f"Multiply by ${ratio}$.", rf"{value} \times {ratio} = {result}")
    else:
        ratio = f_to // f_from
        s.step(f"Know the conversion: 1 {to_unit} = ${ratio}$ {from_unit}.")
        s.step(f"You are changing to a larger unit, so you need fewer of them. "
               f"Divide by ${ratio}$.", rf"{value} \div {ratio} = {result}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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
    solution = f"{h} hr {m} min"

    s = Steps()
    s.step("There are $60$ minutes in 1 hour.")
    s.step(f"Find how many groups of 60 fit in ${total}$. "
           f"${h} \\times 60 = {h * 60}$, and one more hour would be "
           f"${(h + 1) * 60}$, which is too many. So there "
           f"{'is $1$ whole hour' if h == 1 else f'are ${h}$ whole hours'}.")
    s.step("Subtract to find the minutes left over.", f"{total} - {h * 60} = {m}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    if m:
        s.step(f"The movie starts at {start}, which is ${m}$ minutes past ${h}$. "
               f"Add the ${dur}$ minutes to those ${m}$ minutes.", f"{m} + {dur} = {m + dur}")
    else:
        s.step(f"The movie starts at {start}, exactly ${h}$ o'clock, so there are "
               f"no extra minutes yet. Add the ${dur}$ minutes.", f"0 + {dur} = {dur}")
    if m + dur >= 60:
        s.step(f"${m + dur}$ minutes is more than an hour. 60 minutes make 1 hour, "
               f"so ${m + dur}$ minutes is 1 hour and ${em}$ minutes. "
               f"The hour goes from ${h}$ to ${eh}$.")
    else:
        s.step(f"${m + dur}$ is less than 60, so the hour stays ${h}$.")
    if em < 10:
        s.step(f"Write the minutes with two digits: ${em}$ is written as $0{em}$.")
    _answer_text(s, f"{eh}:{em:02d}", lead="The movie ends at")
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    _decimal_column_steps(s, str(a), str(b), op, res, str(res))
    s.answer(solution, lead="In dollars, the answer is")
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.formula("The area of a rectangle", r"\text{Area} = \text{length} \times \text{width}")
    s.substitute(rf"\text{{Area}} = {length} \times {width}",
                 text="Put in the length and width from the problem.")
    s.step("Multiply.", rf"\text{{Area}} = {area}")
    s.answer(solution, lead="The area in square units is")
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step(f"Compare ${a}$ and ${b}$. When you count up, the number you say "
           "later is the bigger one.")
    _compare_symbol_step(s, a, b, symbol)
    s.answer(symbol, lead=f"So ${a} \\,{symbol}\\, {b}$, and the answer is")
    return problem, symbol, s.done()


@register
@with_variants
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

    # Two shown neighbours that reveal the rule.
    j = 0 if idx >= 2 else idx + 1
    s = Steps()
    s.step(f"Find the rule. Look at two numbers next to each other: "
           f"${seq[j]}$ and ${seq[j + 1]}$. Each number is ${diff}$ more than "
           "the one before.", f"{seq[j]} + {diff} = {seq[j + 1]}")
    s.step(f"The missing number comes right after ${seq[idx - 1]}$, so add ${diff}$.",
           f"{seq[idx - 1]} + {diff} = {missing}")
    s.step(f"Check: the next number is ${missing} + {diff} = {seq[idx + 1]}$. It matches.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def arith_even_or_odd(max_n=100):
    r"""Even or Odd

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Is $13$ even or odd? Answer 'even' or 'odd'. | odd |
    """
    n = random.randint(1, max_n)
    answer = "even" if n % 2 == 0 else "odd"
    problem = f"Is ${n}$ even or odd? Answer 'even' or 'odd'."

    s = Steps()
    s.step("Even numbers end in 0, 2, 4, 6, or 8. Odd numbers end in 1, 3, 5, 7, or 9.")
    s.step(f"Look at the last digit of ${n}$: it is ${n % 10}$, so ${n}$ is {answer}.")
    s.answer(answer)
    return problem, answer, s.done()


@register
@with_variants
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
    answer = _ordinal(n)

    s = Steps()
    s.step("An ordinal number tells position: 1st, 2nd, 3rd, 4th, and so on. "
           "Write the number, then add an ending.")
    last_two, last = n % 100, n % 10
    if 11 <= last_two <= 13:
        s.step(f"${n}$ ends in ${last_two}$. Numbers ending in 11, 12, or 13 "
               "always take the ending \"th\".")
    elif last in (1, 2, 3):
        ending = {1: "st", 2: "nd", 3: "rd"}[last]
        s.step(f"${n}$ ends in ${last}$. Numbers ending in {last} take the ending \"{ending}\".")
    else:
        s.step(f"${n}$ ends in ${last}$, so it takes the ending \"th\".")
    _answer_text(s, answer)
    return problem, answer, s.done()


@register
@with_variants
def arith_word_problem_within_20():
    r"""Add and Subtract Word Problem within 20

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | There are 6 red apples and 7 green apples in a basket. How many apples are there in all? | $13$ |
    """
    s = Steps()
    if random.random() < 0.5:
        # Addition; keep the total within 20.
        a = random.randint(1, 10)
        b = random.randint(1, 20 - a)
        answer = a + b
        problem = (
            f"There are {a} red apples and {b} green apples in a basket. "
            f"How many apples are there in all?"
        )
        s.step("\"In all\" means put the red and green apples together. So add.",
               f"{a} + {b}")
        s.step(f"Start at ${a}$ and count on ${b}$ more.", f"{a} + {b} = {answer}")
    else:
        # Subtraction; keep both operands and the result positive.
        a = random.randint(2, 20)
        b = random.randint(1, a - 1)
        answer = a - b
        problem = (
            f"There are {a} ducks in a pond. {b} ducks swim away. "
            f"How many ducks are left?"
        )
        s.step("Some ducks swim away, so there are fewer left. Take them away: subtract.",
               f"{a} - {b}")
        s.step(f"Start at ${a}$ and count back ${b}$.", f"{a} - {b} = {answer}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def arith_add_subtract_within_1000():
    r"""Add and Subtract within 1000

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Calculate $472 + 318$ | $790$ |
    """
    s = Steps()
    if random.random() < 0.5:
        a = random.randint(0, 1000)
        b = random.randint(0, 1000 - a)
        answer = a + b
        problem = f"Calculate ${a} + {b}$"
        _column_add_steps(s, a, b)
    else:
        a = random.randint(0, 1000)
        b = random.randint(0, a)
        answer = a - b
        problem = f"Calculate ${a} - {b}$"
        _column_subtract_steps(s, a, b)
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step(f"\"{h} o'clock\" gives the hour: ${h}$. \"{m} minutes past\" gives "
           f"the minutes: ${m}$.")
    if m < 10:
        s.step(f"Write the hour, then a colon, then the minutes with two digits. "
               f"${m}$ is written as $0{m}$.")
    else:
        s.step("Write the hour, then a colon, then the minutes.")
    _answer_text(s, f"{h}:{m:02d}")
    return problem, solution, s.done()


@register
@with_variants
def arith_count_money_value():
    r"""Count Money Value

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | You have 2 quarters, 3 dimes, 1 nickel, and 4 pennies. What is the total value? Give your answer in dollars and cents, for example 0.89. | $0.89$ |
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
        f"Give your answer in dollars and cents, for example 1.23."
    )
    solution = f"${dollars}.{rem:02d}$"

    s = Steps()
    s.step("A quarter is worth 25 cents, a dime 10 cents, a nickel 5 cents, "
           "and a penny 1 cent.")
    s.step("Find the value of each kind of coin.",
           rf"{q} \times 25 = {q * 25},\quad {d} \times 10 = {d * 10},\quad "
           rf"{n} \times 5 = {n * 5},\quad {p} \times 1 = {p}")
    s.step("Add them up to get the total in cents.",
           rf"{q * 25} + {d * 10} + {n * 5} + {p} = {cents}")
    if dollars:
        s.step(f"100 cents make 1 dollar, so ${cents}$ cents is ${dollars}$ dollar "
               f"and ${rem}$ cents. Write the dollars, a decimal point, then the "
               "cents with two digits.", rf"{dollars}.{rem:02d} \text{{ dollars}}")
    else:
        s.step(f"${cents}$ cents is less than 1 dollar, so write $0$ dollars, a "
               "decimal point, then the cents with two digits.",
               rf"{dollars}.{rem:02d} \text{{ dollars}}")
    s.answer(solution, lead="In dollars and cents, the answer is")
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step(f"Each row has ${cols}$ dots. Add ${cols}$ once for each of the "
           f"${rows}$ rows.", " + ".join([str(cols)] * rows) + f" = {total}")
    s.step(f"Adding ${cols}$ a total of ${rows}$ times is the same as multiplying.",
           rf"{rows} \times {cols} = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    for place, x, y in zip(("hundreds", "tens", "ones"), str(a), str(b)):
        if x == y:
            then = "too" if place == "ones" else "so look at the next place"
            s.step(f"Compare the {place} digits: ${x}$ and ${y}$. They are the "
                   f"same, {then}.")
        else:
            s.step(f"Compare the {place} digits: ${x}$ and ${y}$. "
                   f"${max(x, y)}$ is bigger.")
            break
    if symbol == "=":
        s.step("Every digit matches, so the numbers are equal. Use $=$.")
    else:
        _compare_symbol_step(s, a, b, symbol)
    s.answer(symbol, lead=f"So ${a} \\,{symbol}\\, {b}$, and the answer is")
    return problem, symbol, s.done()


@register
@with_variants
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

    s = Steps()
    s.step(f"Look at the denominators. What times ${b}$ makes ${d}$?",
           rf"{b} \times {k} = {d}")
    s.step(f"To keep the fractions equal, multiply the numerator by the same "
           f"number, ${k}$.",
           rf"\frac{{{a}}}{{{b}}} = \frac{{{a} \times {k}}}{{{b} \times {k}}} = \frac{{{answer}}}{{{d}}}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step(f"Think: ${a}$ times what number makes ${c}$? Division undoes "
           f"multiplication, so divide ${c}$ by ${a}$.")
    s.step("Divide.", rf"{c} \div {a} = {factor}")
    s.step(f"Check: ${a} \\times {factor} = {c}$. It works.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step(f"The space from 0 to 1 is split into ${b}$ equal parts, so each "
           f"part is ${tex_frac(1, b)}$.")
    s.step(f"The {_ordinal(a)} tick mark is ${a}$ {'part' if a == 1 else 'parts'} to the right of 0, so it "
           f"shows ${tex_frac(a, b)}$.")
    g = gcd(a, b)
    if g > 1:
        s.step(f"Simplify: divide the numerator and denominator by ${g}$.",
               rf"{tex_frac(a, b)} = {tex_frac(a // g, b // g)}")
        s.answer(solution, lead="In simplest form, the answer is")
    else:
        s.answer(solution)
    return problem, solution, s.done()


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

    s = Steps()
    s.step(f"Step 1: find how many apples came in the crates. There are "
           f"${crates}$ crates with ${per}$ apples each, so multiply.",
           rf"{crates} \times {per} = {crates * per}")
    s.step(f"Step 2: add those to the ${start}$ apples the store already had.",
           f"{start} + {crates * per} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    top = k * a
    g = gcd(top, b)
    s = Steps()
    s.step("To multiply a whole number by a fraction, multiply the whole number "
           "by the numerator and keep the denominator.",
           rf"{k} \times {tex_frac(a, b)} = \frac{{{k} \times {a}}}{{{b}}} = {tex_frac(top, b)}")
    lead = "The answer is"
    if g == b:
        s.step(f"The numerator is a multiple of the denominator, so this is a "
               f"whole number: ${top} \\div {b} = {top // b}$.")
    elif g > 1:
        s.step(f"Simplify: divide the numerator and denominator by ${g}$.",
               rf"{tex_frac(top, b)} = {tex_frac(top // g, b // g)}")
        lead = "In simplest form, the answer is"
    else:
        lead = "This is already in simplest form, so the answer is"
    s.answer(solution, lead=lead)
    return problem, solution, s.done()


@register
@with_variants
def arith_mixed_to_improper(max_den=9):
    r"""Mixed and Improper Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert the mixed number 2 1/3 to an improper fraction. Format as p/q. | $7/3$ |
    """
    c = random.randint(2, max_den)
    a = random.randint(1, 9)
    # Keep the fraction part in lowest terms (no 2 2/4): then p/c is reduced
    # too, so the expected answer is the simplest form a student would give.
    b = random.choice([k for k in range(1, c) if gcd(k, c) == 1])
    p = a * c + b
    problem = (
        f"Convert the mixed number {a} {b}/{c} to an improper fraction. "
        f"Format as p/q."
    )
    solution = f"${p}/{c}$"

    s = Steps()
    s.step(f"Each whole is ${c}$ parts of size ${tex_frac(1, c)}$. Multiply the "
           "whole number by the denominator to count the parts in the wholes.",
           rf"{a} \times {c} = {a * c}")
    s.step(f"Add the ${b}$ extra {'part' if b == 1 else 'parts'} from the numerator.",
           f"{a * c} + {b} = {p}")
    s.step(f"Put that over the same denominator, ${c}$.",
           rf"{a}\,{tex_frac(b, c)} = {tex_frac(p, c)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step(f"Find the biggest multiple of ${b}$ that is not more than ${a}$. "
           f"${b} \\times {q} = {b * q}$, and ${b} \\times {q + 1} = {b * (q + 1)}$ "
           f"is too big. So the quotient is ${q}$.")
    s.step("Subtract to find what is left over. That is the remainder.",
           f"{a} - {b * q} = {r}")
    if r == 0:
        s.step(f"The remainder is $0$, so ${b}$ divides ${a}$ evenly.")
    else:
        s.step(f"Check: the remainder ${r}$ is less than ${b}$, so we are done.")
    _answer_text(s, f"{q} R {r}")
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.step("The two smaller angles fit together to make the whole angle, so "
           "their measures add up.", r"\angle ABD + \angle DBC = \angle ABC")
    s.substitute(rf"{known}^\circ + \angle DBC = {total}^\circ")
    s.step(f"Subtract ${known}^\\circ$ from both sides.",
           rf"\angle DBC = {total}^\circ - {known}^\circ = {missing}^\circ")
    s.answer(solution, lead="In degrees, the answer is")
    return problem, solution, s.done()


@register
@with_variants
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

    found = [(k, n // k) for k in range(1, n + 1) if k * k <= n and n % k == 0]
    s = Steps()
    s.step(f"A factor pair is two whole numbers that multiply to make ${n}$. "
           "Try $1, 2, 3, \\ldots$ in order and keep the ones that divide evenly.",
           r",\quad ".join(rf"{x} \times {y}" for x, y in found))
    last = found[-1][0]
    if last * last == n:
        s.step(f"Stop at ${last} \\times {last}$: after that the pairs just repeat "
               f"in the other order. ${last} \\times {last}$ counts as one pair.")
    else:
        s.step(f"Stop after ${found[-1][0]} \\times {found[-1][1]}$: the next factor "
               "would be bigger than its partner, so the pairs would just repeat "
               "in the other order.")
    s.step(f"Count the pairs: there {'is' if pairs == 1 else 'are'} ${pairs}$.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    lead = _fraction_steps(s, a, b, c, d, op)
    s.answer(solution, lead=lead)
    return problem, solution, s.done()


@register
@with_variants
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

    digits = f"{frac_part:03d}"
    if place_name == "tenth":
        right, digit = "hundredths", digits[1]
    else:
        right, digit = "thousandths", digits[2]
    s = Steps()
    s.step(f"Look at the {right} digit, just to the right of the {place_name}s "
           f"place. In ${x}$ it is ${digit}$.")
    if int(digit) >= 5:
        s.step(f"${digit}$ is 5 or more, so round up: the {place_name}s digit goes "
               "up by 1 and the digits after it are dropped.",
               rf"{x} \approx {rounded}")
    else:
        s.step(f"${digit}$ is less than 5, so round down: keep the {place_name}s "
               "digit and drop the digits after it.", rf"{x} \approx {rounded}")
    if str(rounded) != _fmt(rounded):
        s.step(f"Zeros at the end of a decimal don't change its value: "
               f"${rounded} = {_fmt(rounded)}$.")
    s.answer(solution)
    return problem, solution, s.done()


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
@with_variants
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

    s = Steps()
    if mult > 1:
        factor = int(mult)
        zeros = len(str(factor)) - 1
        s.step(f"Know the conversion: 1 {from_unit} = ${factor}$ {to_unit}.")
        s.step(f"You are changing to a smaller unit, so you need more of them. "
               f"Multiply by ${factor}$: move the decimal point {zeros} places right.",
               rf"{value} \times {factor} = {_fmt(result)}")
    else:
        factor = int(1 / mult)
        zeros = len(str(factor)) - 1
        s.step(f"Know the conversion: 1 {to_unit} = ${factor}$ {from_unit}.")
        s.step(f"You are changing to a larger unit, so you need fewer of them. "
               f"Divide by ${factor}$: move the decimal point {zeros} places left.",
               rf"{value} \div {factor} = {_fmt(result)}")
    s.answer(solution, lead=f"In {to_unit}, the answer is")
    return problem, solution, s.done()


@register
@with_variants
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

    unit = "tenths" if dp == 1 else "hundredths"
    scaled_a = int(a.scaleb(dp))
    scaled_q = int(q.scaleb(dp))
    s = Steps()
    s.step(f"Think of ${_fmt(a)}$ as a number of {unit}: ${_fmt(a)}$ is ${scaled_a}$ {unit}.")
    s.step(f"Divide the whole numbers: ${scaled_a} \\div {b} = {scaled_q}$. "
           f"So the quotient is ${scaled_q}$ {unit}.")
    s.step(f"Write ${scaled_q}$ {unit} as a decimal: ${_fmt(q)}$.")
    s.step(f"Check: ${_fmt(q)} \\times {b} = {_fmt(a)}$.")
    s.answer(solution)
    return problem, solution, s.done()
