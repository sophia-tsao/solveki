"""Solveki-local pre-algebra generators (Georgia grade 6-8 topics).

Every generator name starts with ``pre_`` and returns a ``(problem, solution,
steps)`` triple of LaTeX-wrapped strings plus a step-by-step explanation.
Answers are kept clean: integers, short decimals (<=3 dp), or reduced
``p/q`` fractions.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._format import frac_from, num
from ._steps import Steps, paren, tex_frac
from .algebra import _format_polynomial

# Inequality relation tokens and their reversal. The problem statement renders
# LaTeX (``\leq``/``\geq``); solutions use typeable ASCII (``<=``/``>=``).
_FLIP = {"<": ">", ">": "<", "\\leq": "\\geq", "\\geq": "\\leq"}
_OPS = list(_FLIP)
# Map a LaTeX relation token to the typeable ASCII the student would type.
_ASCII_OP = {"<": "<", ">": ">", "\\leq": "<=", "\\geq": ">="}

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."


def _signed(mag_value):
    """Return a ``' + n'`` / ``' - n'`` display fragment for a signed int."""
    if mag_value >= 0:
        return f"+ {mag_value}"
    return f"- {abs(mag_value)}"


def _frac_solution(fr):
    """Render a ``Fraction`` typeably as ``$p$`` (integer) or ``$p/q$``."""
    return f"${frac_from(fr)}$"


# --- Step helpers -----------------------------------------------------------

def _tex(value):
    """A ``Fraction``/int as LaTeX: an integer, or ``\\frac`` with sign in front."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return tex_frac(fr.numerator, fr.denominator)


def _term(coeff, var="x"):
    """``coeff`` times ``var`` as LaTeX, dropping a unit coefficient: ``-x``."""
    if coeff == 1:
        return var
    if coeff == -1:
        return f"-{var}"
    return f"{_tex(coeff)}{var}"


def _tex_line(m, b):
    """``y = mx + b`` in LaTeX for ``Fraction`` slope/intercept."""
    line = f"y = {_term(m)}"
    if b > 0:
        line += f" + {_tex(b)}"
    elif b < 0:
        line += f" - {_tex(-b)}"
    return line


def _join_signed(values):
    """Join ints as a sum: ``[18, -12, 5]`` -> ``18 - 12 + 5``."""
    text = str(values[0])
    for v in values[1:]:
        text += f" {_signed(v)}"
    return text


def _move_constant(b, var=""):
    """How to clear a ``+ b`` (or ``+ b*var``) term: "Subtract $3$ from both sides"."""
    if b > 0:
        return f"Subtract ${_term(b, var) if var else b}$ from both sides"
    return f"Add ${_term(-b, var) if var else -b}$ to both sides"


def _simplify(s, n, d):
    """Add a step reducing the fraction ``n/d`` if it isn't in simplest form."""
    fr = Fraction(n, d)
    if d == 1:
        s.step("Any number divided by $1$ is itself.", rf"\frac{{{n}}}{{1}} = {n}")
        return
    if (fr.numerator, fr.denominator) == (n, d):
        return
    if n == 0:
        s.step("A fraction with numerator $0$ is equal to $0$.",
               rf"\frac{{{n}}}{{{d}}} = 0")
        return
    g = math.gcd(n, d) * (-1 if d < 0 else 1)
    s.step(
        f"Simplify by dividing the numerator and denominator by ${g}$.",
        rf"\frac{{{n}}}{{{d}}} = {_tex(fr)}",
    )


def _money(cents):
    """An integer number of cents as ``D.CC`` (no dollar sign)."""
    return f"{cents // 100}.{cents % 100:02d}"


def _sign_rule_steps(s, a, b, op):
    """Steps evaluating ``(a) op (b)`` for signed integers with the sign rules."""
    if op == "-":
        s.step(
            "Subtracting a number is the same as adding its opposite.",
            f"({a}) - ({b}) = ({a}) + ({-b})",
        )
        b, op = -b, "+"
    if op == "+":
        result = a + b
        if a == 0 or b == 0:
            s.step("Adding $0$ does not change a number.", f"({a}) + ({b}) = {result}")
            return result
        if (a > 0) == (b > 0):
            s.step(
                "Both numbers have the same sign, so add their absolute values.",
                f"{abs(a)} + {abs(b)} = {abs(result)}",
            )
            last = f"Both numbers are {'positive' if a > 0 else 'negative'}, so the answer is too."
        else:
            big, small = max(abs(a), abs(b)), min(abs(a), abs(b))
            s.step(
                "The signs are different, so subtract the smaller absolute value "
                "from the larger one.",
                f"{big} - {small} = {abs(result)}",
            )
            if result == 0:
                last = "The two numbers are opposites, so they cancel out."
            else:
                lead = a if abs(a) > abs(b) else b
                last = (f"${lead}$ has the larger absolute value, so the answer is "
                        f"{'positive' if lead > 0 else 'negative'}.")
        s.step(last, f"({a}) + ({b}) = {result}")
        return result
    word, sym = ("multiplying", r"\times") if op == "\\times" else ("dividing", r"\div")
    result = a * b if op == "\\times" else a // b
    if a == 0:
        what = "Zero times any number" if op == "\\times" else "Zero divided by any nonzero number"
        s.step(f"{what} is $0$.", f"({a}) {sym} ({b}) = 0")
        return result
    if b == 0:
        s.step("Any number times $0$ is $0$.", f"({a}) {sym} ({b}) = 0")
        return result
    verb = "Multiply" if word == "multiplying" else "Divide"
    s.step(f"{verb} the absolute values first.", f"{abs(a)} {sym} {abs(b)} = {abs(result)}")
    same = (a > 0) == (b > 0)
    s.step(
        f"When {word}, the same signs give a positive answer and different "
        f"signs give a negative answer. The signs here are "
        f"{'the same, so the answer is positive' if same else 'different, so the answer is negative'}.",
        f"({a}) {sym} ({b}) = {result}",
    )
    return result


# --- Generators -------------------------------------------------------------

@register
def pre_unit_rate(min_rate=2, max_rate=30, min_time=2, max_time=12):
    r"""Unit Rate

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A vehicle travels $120$ miles in $3$ hours. Find the unit rate in miles per hour. | $40$ |
    """
    rate = random.randint(min_rate, max_rate)
    t = random.randint(min_time, max_time)
    d = rate * t
    problem = (
        f"A vehicle travels ${d}$ miles in ${t}$ hours. "
        f"Find the unit rate in miles per hour."
    )
    solution = f"${rate}$"

    s = Steps()
    s.step(
        "A unit rate is the amount for $1$ unit. To find miles per $1$ hour, "
        "divide the miles by the hours.",
        rf"\text{{rate}} = \frac{{{d} \text{{ miles}}}}{{{t} \text{{ hours}}}}",
    )
    s.step("Divide.", rf"{d} \div {t} = {rate}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_equivalent_ratio(min_term=1, max_term=9, min_factor=2, max_factor=9):
    r"""Equivalent Ratio

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Fill in the blank to make the ratios equivalent: $2:5 = 6:\square$ | $15$ |
    """
    a = random.randint(min_term, max_term)
    b = random.randint(min_term, max_term)
    f = random.randint(min_factor, max_factor)
    c = a * f
    d = b * f
    problem = (
        f"Fill in the blank to make the ratios equivalent: "
        f"${a}:{b} = {c}:\\square$"
    )
    solution = f"${d}$"

    s = Steps()
    s.step("To make an equivalent ratio, multiply both terms by the same number.")
    s.step(
        f"The first term goes from ${a}$ to ${c}$, so the multiplier is "
        f"${c} \\div {a} = {f}$.",
    )
    s.step("Multiply the second term by the same number.", rf"{b} \times {f} = {d}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_solve_proportion(min_term=1, max_term=12, min_factor=1, max_factor=9):
    r"""Solve a Proportion

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve for $x$: $\frac{2}{3} = \frac{x}{9}$ | $6$ |
    """
    a = random.randint(min_term, max_term)
    b = random.randint(min_term, max_term)
    k = random.randint(min_factor, max_factor)
    d = b * k
    x = a * k
    problem = f"Solve for $x$: $\\frac{{{a}}}{{{b}}} = \\frac{{x}}{{{d}}}$"
    solution = f"${x}$"

    s = Steps()
    s.step(
        "In equal fractions, the numerator and denominator are multiplied by "
        "the same number."
    )
    s.step(
        f"The denominator goes from ${b}$ to ${d}$, so the multiplier is "
        f"${d} \\div {b} = {k}$.",
    )
    s.step("Multiply the numerator by the same number.", rf"x = {a} \times {k} = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_integer_operations(min_val=-20, max_val=20, max_quotient=12):
    r"""Signed Integer Operations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $(-6) \times (4)$ | $-24$ |
    """
    op = random.choice(["+", "-", "\\times", "\\div"])
    if op == "\\div":
        b = random.choice([i for i in range(-12, 13) if i != 0])
        quotient = random.randint(-max_quotient, max_quotient)
        a = b * quotient
        result = quotient
    else:
        a = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
        if op == "+":
            result = a + b
        elif op == "-":
            result = a - b
        else:
            result = a * b
    problem = f"Evaluate $({a}) {op} ({b})$"
    solution = f"${result}$"

    s = Steps()
    _sign_rule_steps(s, a, b, op)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_rational_operations(min_num=-9, max_num=9, min_den=2, max_den=9):
    r"""Signed Fraction Operations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\frac{1}{2} + \frac{-1}{3}$ | $1/6$ |
    """
    op = random.choice(["+", "-", "\\times", "\\div"])
    a = random.choice([i for i in range(min_num, max_num + 1) if i != 0])
    b = random.randint(min_den, max_den)
    c = random.choice([i for i in range(min_num, max_num + 1) if i != 0])
    d = random.randint(min_den, max_den)
    f1 = Fraction(a, b)
    f2 = Fraction(c, d)
    if op == "+":
        result = f1 + f2
    elif op == "-":
        result = f1 - f2
    elif op == "\\times":
        result = f1 * f2
    else:
        result = f1 / f2
    problem = (
        f"Evaluate $\\frac{{{a}}}{{{b}}} {op} \\frac{{{c}}}{{{d}}}$. {_FRACTION_HINT}"
    )
    solution = _frac_solution(result)

    s = Steps()
    lhs = rf"\frac{{{a}}}{{{b}}}"
    rhs = rf"\frac{{{c}}}{{{d}}}"
    if op in ("+", "-"):
        lcd = b * d // math.gcd(b, d)
        n1, n2 = a * (lcd // b), c * (lcd // d)
        if b == d:
            s.step(f"Both fractions already have the denominator ${b}$.")
        else:
            s.step(
                f"Rewrite both fractions with the common denominator ${lcd}$.",
                rf"\frac{{{n1}}}{{{lcd}}} {op} \frac{{{n2}}}{{{lcd}}}",
            )
        total = n1 + n2 if op == "+" else n1 - n2
        verb = "Add" if op == "+" else "Subtract"
        s.step(
            f"{verb} the numerators and keep the denominator.",
            rf"\frac{{{n1} {op} {paren(n2)}}}{{{lcd}}} = \frac{{{total}}}{{{lcd}}}",
        )
        _simplify(s, total, lcd)
    else:
        if op == "\\div":
            s.step(
                "Dividing by a fraction is the same as multiplying by its reciprocal.",
                rf"{lhs} \div {rhs} = {lhs} \times \frac{{{d}}}{{{c}}}",
            )
            top, bottom = (a, d), (b, c)
        else:
            top, bottom = (a, c), (b, d)
        n, den = top[0] * top[1], bottom[0] * bottom[1]
        s.step(
            "Multiply the numerators together and the denominators together.",
            rf"\frac{{{top[0]} \cdot {paren(top[1])}}}{{{bottom[0]} \cdot {paren(bottom[1])}}}"
            rf" = \frac{{{n}}}{{{den}}}",
        )
        _simplify(s, n, den)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_absolute_value(min_val=-20, max_val=20):
    r"""Absolute Value Expression

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $|3 - 8|$ | $5$ |
    """
    s = Steps()
    if random.random() < 0.5:
        a = random.randint(max(0, min_val), max_val)
        b = random.randint(max(0, min_val), max_val)
        problem = f"Evaluate $|{a} - {b}|$"
        result = abs(a - b)
        s.step("First, subtract inside the absolute value bars.", f"|{a} - {b}| = |{a - b}|")
        s.step(
            "Absolute value is the distance from $0$, so it is never negative.",
            f"|{a - b}| = {result}",
        )
    else:
        a = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
        problem = f"Evaluate $|{a}| + |{b}|$"
        result = abs(a) + abs(b)
        s.step(
            "Absolute value is the distance from $0$, so it is never negative. "
            "Find each absolute value.",
            rf"|{a}| = {abs(a)}, \quad |{b}| = {abs(b)}",
        )
        s.step("Add.", f"{abs(a)} + {abs(b)} = {result}")
    solution = f"${result}$"
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_one_step_inequality():
    r"""One-Step Inequality

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the inequality: $x + 3 < 8$ | $x < 5$ |
    """
    op = random.choice(_OPS)
    s = Steps()
    if random.random() < 0.5:
        # Additive: x + a  op  b  ->  x op (b - a). No sign flip.
        a = random.choice([i for i in range(-10, 11) if i != 0])
        b = random.randint(-20, 20)
        c = b - a
        problem = f"Solve the inequality: $x {_signed(a)} {op} {b}$"
        solution = f"$x {_ASCII_OP[op]} {c}$"
        s.step(
            f"{_move_constant(a)} to get $x$ by itself. Adding or "
            "subtracting does not change the direction of the inequality.",
            f"x {op} {b} {_signed(-a)}",
        )
        s.step("Simplify.", f"x {op} {c}")
    else:
        # Multiplicative: k*x op b  ->  x op' (b/k). Flip op when k < 0.
        k = random.choice([i for i in range(-10, 11) if abs(i) >= 2])
        c = random.randint(-15, 15)
        b = k * c
        out_op = _FLIP[op] if k < 0 else op
        problem = f"Solve the inequality: ${k}x {op} {b}$"
        solution = f"$x {_ASCII_OP[out_op]} {c}$"
        text = f"Divide both sides by ${k}$."
        if k < 0:
            text += (" Dividing by a negative number reverses the direction "
                     "of the inequality sign.")
        s.step(text, rf"\frac{{{k}x}}{{{k}}} {out_op} \frac{{{b}}}{{{k}}}")
        s.step("Simplify.", f"x {out_op} {c}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_multi_step_inequality():
    r"""Multi-Step Inequality

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the inequality: $3x + 4 \leq 19$ | $x \leq 5$ |
    """
    op = random.choice(_OPS)
    a = random.choice([i for i in range(-10, 11) if abs(i) >= 2])
    b = random.randint(-20, 20)
    r = random.randint(-15, 15)
    c = a * r + b
    out_op = _FLIP[op] if a < 0 else op
    problem = f"Solve the inequality: ${a}x {_signed(b)} {op} {c}$"
    solution = f"$x {_ASCII_OP[out_op]} {r}$"

    s = Steps()
    if b == 0:
        s.step("Adding $0$ changes nothing, so drop it.", f"{a}x {op} {c}")
    else:
        s.step(
            f"{_move_constant(b)}. This does not change the "
            "direction of the inequality.",
            f"{a}x {op} {c - b}",
        )
    text = f"Divide both sides by ${a}$."
    if a < 0:
        text += (" Dividing by a negative number reverses the direction of "
                 "the inequality sign.")
    s.step(text, rf"x {out_op} \frac{{{c - b}}}{{{a}}}")
    s.step("Simplify.", f"x {out_op} {r}")
    s.answer(solution)
    return problem, solution, s.done()


def _normalize_sci(fr):
    """Return ``(mantissa, exponent)`` for a positive ``Fraction`` value.

    Mantissa lands in ``[1, 10)`` and is rounded to 3 dp.
    """
    ten = Fraction(10)
    x = fr
    exp = 0
    while x >= ten:
        x /= ten
        exp += 1
    while x < 1:
        x *= ten
        exp -= 1
    return round(float(x), 3), exp


def _sci_steps(op, m1t, m2t, e1, e2, mant, exp):
    """Steps for ``m1 x 10^e1 op m2 x 10^e2`` landing on ``mant x 10^exp``."""
    m1, m2 = f"{m1t / 10:.1f}", f"{m2t / 10:.1f}"
    s = Steps()
    if op in ("+", "-"):
        verb = "add" if op == "+" else "subtract"
        raw = (m1t + m2t if op == "+" else m1t - m2t) / 10
        s.step(
            f"Both numbers have the same power of ten, so {verb} the decimal "
            f"parts and keep $10^{{{e1}}}$.",
            rf"({m1} {op} {m2}) \times 10^{{{e1}}} = {raw:.1f} \times 10^{{{e1}}}",
        )
        if raw >= 10:
            s.step(
                "In scientific notation the first number must be at least $1$ "
                "and less than $10$. Move the decimal point one place left and "
                "add $1$ to the exponent.",
                rf"{mant} \times 10^{{{exp}}}",
            )
        elif raw < 1:
            s.step(
                "In scientific notation the first number must be at least $1$ "
                "and less than $10$. Move the decimal point one place right and "
                "subtract $1$ from the exponent.",
                rf"{mant} \times 10^{{{exp}}}",
            )
        return s
    s.step(
        "To divide, divide the decimal parts and subtract the exponents.",
        rf"\frac{{{m1}}}{{{m2}}} \times 10^{{{e1} - {paren(e2)}}}"
        rf" = \frac{{{m1}}}{{{m2}}} \times 10^{{{e1 - e2}}}",
    )
    exact = Fraction(m1t, m2t)
    if exact < 1:
        exact *= 10
        s.step(
            f"Since ${m1}$ is less than ${m2}$, the quotient is less than $1$. "
            "Multiply the decimal part by $10$ and subtract $1$ from the exponent "
            "so the first number is between $1$ and $10$.",
            rf"\frac{{{m1t}}}{{{m2}}} \times 10^{{{exp}}}",
        )
        quotient = rf"{m1t} \div {m2}"
    else:
        quotient = rf"{m1} \div {m2}"
    rel = "=" if Fraction(str(mant)) == exact else r"\approx"
    s.step("Divide.", rf"{quotient} {rel} {mant}, \text{{ so }} {mant} \times 10^{{{exp}}}")
    return s


@register
def pre_scientific_notation_ops():
    r"""Scientific Notation Operations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $3.0 \times 10^{4} + 2.0 \times 10^{4}$ | $5.0 \times 10^{4}$ |
    """
    ten = Fraction(10)
    while True:
        op = random.choice(["+", "-", "\\div"])
        if op in ("+", "-"):
            e = random.randint(-3, 6)
            e1 = e2 = e
            m1t = random.randint(10, 99)
            m2t = random.randint(10, 99)
            if op == "-":
                if m1t <= m2t:
                    continue
        else:
            e1 = random.randint(-3, 6)
            e2 = random.randint(-3, 6)
            m1t = random.randint(10, 99)
            m2t = random.randint(10, 99)
        f1 = Fraction(m1t, 10) * (ten ** e1)
        f2 = Fraction(m2t, 10) * (ten ** e2)
        if op == "+":
            value = f1 + f2
        elif op == "-":
            value = f1 - f2
        else:
            value = f1 / f2
        if value <= 0:
            continue
        mant, exp = _normalize_sci(value)
        if mant < 1.0 or mant >= 10.0:
            continue
        m1 = m1t / 10
        m2 = m2t / 10
        problem = (
            f"Evaluate ${m1:.1f} \\times 10^{{{e1}}} {op} "
            f"{m2:.1f} \\times 10^{{{e2}}}$. "
            f"Answers should be formatted as such: 5.0*10^4. "
            f"Round the decimal part to the nearest thousandth if necessary."
        )
        solution = f"${mant}*10^{exp}$"
        s = _sci_steps(op, m1t, m2t, e1, e2, mant, exp)
        rounded = Fraction(str(mant)) != _normalize_exact(value)
        lead = ("Rounded to three decimal places, the answer is" if rounded
                else "In the requested format, the answer is")
        s.answer(solution, lead=lead)
        return problem, solution, s.done()


def _normalize_exact(fr):
    """The exact mantissa in ``[1, 10)`` of a positive ``Fraction``."""
    while fr >= 10:
        fr /= 10
    while fr < 1:
        fr *= 10
    return fr


@register
def pre_integer_exponent_rules(min_base=2, max_base=9, min_exp=-4, max_exp=4):
    r"""Integer Exponent Rules

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify: $2^{3} \times 2^{-1}$ | $2^2$ |
    """
    a = random.randint(min_base, max_base)
    m = random.randint(min_exp, max_exp)
    n = random.randint(min_exp, max_exp)
    kind = random.choice(["mult", "div", "power"])
    s = Steps()
    if kind == "mult":
        problem = f"Simplify: ${a}^{{{m}}} \\times {a}^{{{n}}}$"
        r = m + n
        s.step(
            "Product rule: when you multiply powers with the same base, add "
            "the exponents.",
            r"a^m \times a^n = a^{m + n}",
        )
        s.step("Add the exponents.",
               rf"{a}^{{{m}}} \times {a}^{{{n}}} = {a}^{{{m} + {paren(n)}}} = {a}^{{{r}}}")
    elif kind == "div":
        problem = f"Simplify: ${a}^{{{m}}} \\div {a}^{{{n}}}$"
        r = m - n
        s.step(
            "Quotient rule: when you divide powers with the same base, subtract "
            "the exponents.",
            r"a^m \div a^n = a^{m - n}",
        )
        s.step("Subtract the exponents.",
               rf"{a}^{{{m}}} \div {a}^{{{n}}} = {a}^{{{m} - {paren(n)}}} = {a}^{{{r}}}")
    else:
        problem = f"Simplify: $({a}^{{{m}}})^{{{n}}}$"
        r = m * n
        s.step(
            "Power rule: when you raise a power to a power, multiply the exponents.",
            r"(a^m)^n = a^{m \cdot n}",
        )
        s.step("Multiply the exponents.",
               rf"({a}^{{{m}}})^{{{n}}} = {a}^{{{m} \cdot {paren(n)}}} = {a}^{{{r}}}")
    problem += " Answers should be formatted as such: 2^3."
    solution = f"${a}^{r}$"
    s.answer(solution, lead="In the requested format, the answer is")
    return problem, solution, s.done()


@register
def pre_constant_of_proportionality(max_k=12, min_x=2, max_x=12):
    r"""Constant of Proportionality

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | The variable $y$ varies directly with $x$. When $x = 4$, $y = 12$. Find the constant of proportionality $k$. | $3$ |
    """
    k = random.choice([i for i in range(-max_k, max_k + 1) if i != 0])
    x = random.randint(min_x, max_x)
    y = k * x
    problem = (
        f"The variable $y$ varies directly with $x$. "
        f"When $x = {x}$, $y = {y}$. "
        f"Find the constant of proportionality $k$."
    )
    solution = f"${k}$"

    s = Steps()
    s.step("Direct variation means $y = kx$, so $k = \\frac{y}{x}$.")
    s.substitute(rf"k = \frac{{{y}}}{{{x}}}")
    s.step("Divide.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


def _plug_in(terms, v):
    """Render ``terms`` with ``x`` replaced by ``(v)``: ``2(3)^{2} - 4(3) + 5``."""
    text = ""
    for coeff, exp in terms:
        if coeff == 0:
            continue
        mag = abs(coeff)
        if exp == 0:
            body = str(mag)
        else:
            power = f"({v})" if exp == 1 else f"({v})^{{{exp}}}"
            body = power if mag == 1 else f"{mag}{power}"
        if not text:
            text = body if coeff > 0 else f"-{body}"
        else:
            text += f" {'+' if coeff > 0 else '-'} {body}"
    return text


@register
def pre_evaluate_function(min_coeff=-9, max_coeff=9, min_x=-6, max_x=6):
    r"""Evaluate a Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $f(x)=2x+3$, evaluate $f(4)$. | $11$ |
    """
    v = random.randint(min_x, max_x)
    nonzero = [i for i in range(min_coeff, max_coeff + 1) if i != 0]
    if random.random() < 0.5:
        a = random.choice(nonzero)
        b = random.randint(min_coeff, max_coeff)
        terms = [(a, 1), (b, 0)]
    else:
        a = random.choice(nonzero)
        b = random.randint(min_coeff, max_coeff)
        c = random.randint(min_coeff, max_coeff)
        terms = [(a, 2), (b, 1), (c, 0)]
    poly = _format_polynomial(terms)
    result = sum(coeff * (v ** exp) for coeff, exp in terms)
    problem = f"Given $f(x)={poly}$, evaluate $f({v})$."
    solution = f"${result}$"

    s = Steps()
    s.step(f"Replace every $x$ with ${v}$.", f"f({v}) = {_plug_in(terms, v)}")
    values = [coeff * v ** exp for coeff, exp in terms if coeff != 0]
    if len(values) > 1:
        squared = any(exp == 2 for coeff, exp in terms if coeff != 0)
        text = ("Follow the order of operations: square first, then multiply."
                if squared else "Multiply.")
        s.step(text, f"f({v}) = {_join_signed(values)}")
        s.step("Add and subtract from left to right.", f"f({v}) = {result}")
    else:
        s.step("Evaluate.", f"f({v}) = {result}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_slope_from_two_points(coord_min=-10, coord_max=10):
    r"""Slope from Two Points

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the slope of the line through the points $(1, 2)$ and $(3, 8)$. | $3$ |
    """
    x1 = random.randint(coord_min, coord_max)
    x2 = random.randint(coord_min, coord_max)
    while x2 == x1:
        x2 = random.randint(coord_min, coord_max)
    y1 = random.randint(coord_min, coord_max)
    y2 = random.randint(coord_min, coord_max)
    slope = Fraction(y2 - y1, x2 - x1)
    problem = (
        f"Find the slope of the line through the points "
        f"$({x1}, {y1})$ and $({x2}, {y2})$. {_FRACTION_HINT}"
    )
    solution = _frac_solution(slope)

    s = Steps()
    s.formula("The slope formula", r"m = \frac{y_2 - y_1}{x_2 - x_1}")
    s.substitute(rf"m = \frac{{{y2} - {paren(y1)}}}{{{x2} - {paren(x1)}}}")
    s.step("Subtract.", rf"m = \frac{{{y2 - y1}}}{{{x2 - x1}}}")
    _simplify(s, y2 - y1, x2 - x1)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_linear_function_value(min_val=-10, max_val=10):
    r"""Linear Function Value

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A line has slope $m = 2$ and y-intercept $b = 3$. Find $y$ when $x = 4$. | $11$ |
    """
    m = random.choice([i for i in range(min_val, max_val + 1) if i != 0])
    b = random.randint(min_val, max_val)
    x = random.randint(min_val, max_val)
    y = m * x + b
    problem = (
        f"A line has slope $m = {m}$ and y-intercept $b = {b}$. "
        f"Find $y$ when $x = {x}$."
    )
    solution = f"${y}$"

    s = Steps()
    s.formula("Slope-intercept form", "y = mx + b")
    s.substitute(f"y = {m}({x}) {_signed(b)}")
    s.step("Multiply.", f"y = {m * x} {_signed(b)}")
    s.step("Add or subtract.", f"y = {y}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_mean_absolute_deviation(min_val=1, max_val=20):
    r"""Mean Absolute Deviation

    Convention: mean = sum/n (chosen so it is an integer); MAD is the mean of
    the absolute deviations from that mean.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the mean absolute deviation of the data set: $2, 4, 6, 8$. | $2$ |
    """
    n = random.choice([4, 5])
    while True:
        data = [random.randint(min_val, max_val) for _ in range(n)]
        if sum(data) % n == 0:
            break
    mean = sum(data) / n
    mad = sum(abs(v - mean) for v in data) / n
    data_str = ", ".join(str(v) for v in data)
    problem = (
        f"Find the mean absolute deviation of the data set: ${data_str}$. "
        f"Round your answer to the nearest thousandth."
    )
    solution = f"${num(mad)}$"

    mu = sum(data) // n
    devs = [abs(v - mu) for v in data]
    s = Steps()
    s.step(
        "First find the mean: add the values and divide by how many there are.",
        rf"\text{{mean}} = \frac{{{' + '.join(map(str, data))}}}{{{n}}}"
        rf" = \frac{{{sum(data)}}}{{{n}}} = {mu}",
    )
    s.step(
        f"Find how far each value is from the mean ${mu}$. Distances are never negative.",
        r",\quad ".join(f"|{v} - {mu}| = {dv}" for v, dv in zip(data, devs)),
    )
    s.step(
        "The mean absolute deviation is the mean of these distances.",
        rf"\text{{MAD}} = \frac{{{' + '.join(map(str, devs))}}}{{{n}}}"
        rf" = \frac{{{sum(devs)}}}{{{n}}} = {num(mad)}",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_range(min_val=1, max_val=50, min_n=4, max_n=7):
    r"""Range of a Data Set

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the range of the data set: $3, 8, 5, 12, 7$. | $9$ |

    The range is the difference between the largest and smallest values.
    """
    n = random.randint(min_n, max_n)
    data = [random.randint(min_val, max_val) for _ in range(n)]
    rng = max(data) - min(data)
    data_str = ", ".join(str(v) for v in data)
    problem = f"Find the range of the data set: ${data_str}$."
    solution = f"${rng}$"

    s = Steps()
    s.formula("The range", r"\text{range} = \text{largest} - \text{smallest}")
    s.step(f"The largest value is ${max(data)}$ and the smallest value is ${min(data)}$.")
    s.step("Subtract.", f"{max(data)} - {min(data)} = {rng}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_mode(min_val=1, max_val=20, min_others=3, max_others=5):
    r"""Mode of a Data Set

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the mode of the data set: $4, 7, 4, 9, 2, 4$. | $4$ |

    The mode is the value that appears most often. Each data set is built to
    have exactly one mode: the mode value repeats while every other value
    appears once, so the answer is a single number.
    """
    n_others = random.randint(min_others, max_others)
    values = random.sample(range(min_val, max_val + 1), n_others + 1)
    mode_val = values[0]
    mode_count = random.randint(2, 3)
    data = [mode_val] * mode_count + values[1:]
    random.shuffle(data)
    data_str = ", ".join(str(v) for v in data)
    problem = f"Find the mode of the data set: ${data_str}$."
    solution = f"${mode_val}$"

    s = Steps()
    s.step("The mode is the value that appears most often.")
    s.step(
        "Put the values in order so repeated values sit next to each other.",
        ", ".join(str(v) for v in sorted(data)),
    )
    s.step(
        f"The value ${mode_val}$ appears ${mode_count}$ times. Every other value "
        "appears only once."
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_interquartile_range(min_val=1, max_val=30):
    r"""Interquartile Range

    Convention: sort the 7 values; Q1 is the median of the lower 3 (index 1),
    Q3 is the median of the upper 3 (index 5); IQR = Q3 - Q1.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the interquartile range (IQR) of the data set: $3, 5, 7, 8, 10, 12, 15$. | $7$ |
    """
    data = [random.randint(min_val, max_val) for _ in range(7)]
    s = sorted(data)
    iqr = s[5] - s[1]
    data_str = ", ".join(str(v) for v in data)
    problem = (
        f"Find the interquartile range (IQR) of the data set: ${data_str}$."
    )
    solution = f"${iqr}$"

    st = Steps()
    st.step("Put the values in order from least to greatest.", ", ".join(map(str, s)))
    st.step(
        f"The median is the middle (4th) value, ${s[3]}$. It splits the data into "
        f"a lower half ${', '.join(map(str, s[:3]))}$ and an upper half "
        f"${', '.join(map(str, s[4:]))}$."
    )
    st.step(
        f"$Q_1$ is the median of the lower half, and $Q_3$ is the median of the "
        f"upper half.",
        rf"Q_1 = {s[1]}, \quad Q_3 = {s[5]}",
    )
    st.step("The interquartile range is $Q_3 - Q_1$.", rf"\text{{IQR}} = {s[5]} - {s[1]} = {iqr}")
    st.answer(solution)
    return problem, solution, st.done()


@register
def pre_approximate_irrational(min_n=2, max_n=120):
    r"""Approximate an Irrational Square Root

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Approximate $\sqrt{50}$ to the nearest tenth. | $7.1$ |
    """
    while True:
        n = random.randint(min_n, max_n)
        root = math.sqrt(n)
        if root == int(root):
            continue  # skip perfect squares
        scaled = root * 10
        # Reject values that sit ambiguously on a rounding boundary.
        if abs(scaled - (math.floor(scaled) + 0.5)) < 1e-6:
            continue
        problem = f"Approximate $\\sqrt{{{n}}}$ to the nearest tenth."
        solution = f"${num(root, 1)}$"

        lo = math.isqrt(n)
        thousandths = math.floor(root * 1000)
        truncated = f"{thousandths // 1000}.{thousandths % 1000:03d}"
        hundredths = thousandths // 10 % 10
        s = Steps()
        s.step(
            f"${n}$ is between the perfect squares ${lo * lo}$ and "
            f"${(lo + 1) ** 2}$, so $\\sqrt{{{n}}}$ is between ${lo}$ and ${lo + 1}$.",
            rf"\sqrt{{{lo * lo}}} < \sqrt{{{n}}} < \sqrt{{{(lo + 1) ** 2}}}",
        )
        s.step("Find more decimal places (with a calculator).",
               rf"\sqrt{{{n}}} = {truncated}\ldots")
        direction = "round up" if hundredths >= 5 else "round down"
        s.step(
            f"To round to the nearest tenth, look at the hundredths digit. It is "
            f"${hundredths}$, so {direction}."
        )
        s.answer(solution, lead="Rounded to the nearest tenth, the answer is")
        return problem, solution, s.done()


@register
def pre_area_of_trapezoid(min_base=2, max_base=20, min_height=2, max_height=14):
    r"""Area of a Trapezoid

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A trapezoid has parallel bases of length $6$ and $10$ and height $4$. Find its area. | $32$ |

    Area $= \frac{1}{2}(b_1 + b_2)h$. The bases and height are chosen so the
    area is a whole number.
    """
    while True:
        b1 = random.randint(min_base, max_base)
        b2 = random.randint(min_base, max_base)
        h = random.randint(min_height, max_height)
        if (b1 + b2) * h % 2 == 0:
            break
    area = (b1 + b2) * h // 2
    problem = (
        f"A trapezoid has parallel bases of length ${b1}$ and ${b2}$ and "
        f"height ${h}$. Find its area."
    )
    solution = f"${area}$"

    s = Steps()
    s.formula("The area of a trapezoid", r"A = \frac{1}{2}(b_1 + b_2)h")
    s.substitute(rf"A = \frac{{1}}{{2}}({b1} + {b2})({h})")
    s.step("Add the bases.", rf"A = \frac{{1}}{{2}}({b1 + b2})({h})")
    s.step("Multiply, then take half.",
           rf"A = \frac{{{(b1 + b2) * h}}}{{2}} = {area}")
    s.answer(solution)
    return problem, solution, s.done()


_PLACE_NAMES = {1: "tenths", 2: "hundredths", 3: "thousandths"}


def _fraction_from_parts(s, numerator, denominator):
    """Steps writing ``numerator/denominator`` (numerator may be a decimal) reduced."""
    if "." in numerator:
        places = len(numerator.split(".")[1])
        scale = 10 ** places
        whole = int(numerator.replace(".", ""))
        s.step(
            f"Multiply the numerator and denominator by ${scale}$ to clear the decimal.",
            rf"\frac{{{numerator}}}{{{denominator}}} = \frac{{{whole}}}{{{denominator * scale}}}",
        )
        _simplify(s, whole, denominator * scale)
    else:
        _simplify(s, int(numerator), denominator)


@register
def pre_convert_fdp():
    r"""Convert Between Fractions, Decimals, and Percents

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert the fraction $1/4$ to a percent. Express your answer as a percent (e.g. 25%). | 25% |
    """
    denoms = [2, 4, 5, 8, 10, 20, 25, 50]
    forms = ["fraction", "decimal", "percent"]
    fr = Fraction(1, 4)
    source, target = "fraction", "percent"
    for _ in range(100):
        q = random.choice(denoms)
        p = random.randint(1, 2 * q)
        cand = Fraction(p, q)
        s, t = random.sample(forms, 2)
        # A fraction shown/asked for must be a genuine fraction, not an integer.
        if s == "fraction" and cand.denominator == 1:
            continue
        if t == "fraction" and cand.denominator == 1:
            continue
        fr, source, target = cand, s, t
        break
    if source == "fraction":
        src = f"the fraction ${frac_from(fr)}$"
    elif source == "decimal":
        src = f"the decimal ${num(fr)}$"
    else:
        src = f"the percent ${num(fr * 100)}\\%$"
    if target == "decimal":
        problem = f"Convert {src} to a decimal. Express your answer as a decimal."
        solution = f"${num(fr)}$"
    elif target == "percent":
        problem = (
            f"Convert {src} to a percent. "
            f"Express your answer as a percent (e.g. 25%)."
        )
        solution = f"{num(fr * 100)}%"
    else:
        problem = (
            f"Convert {src} to a reduced fraction. "
            f"Express your answer as a reduced fraction a/b, or an integer."
        )
        solution = f"${frac_from(fr)}$"

    dec, pct = num(fr), num(fr * 100)
    frac_tex = tex_frac(fr.numerator, fr.denominator)
    st = Steps()
    if source == "fraction":
        st.step("A fraction bar means divide, so divide the numerator by the denominator.",
                rf"{frac_tex} = {fr.numerator} \div {fr.denominator} = {dec}")
    elif source == "percent" and target == "decimal":
        st.step("Percent means per hundred, so divide by $100$.",
                rf"{pct}\% = {pct} \div 100 = {dec}")
    if target == "percent":
        st.step("To change a decimal to a percent, multiply by $100$ "
                "(move the decimal point two places right).",
                rf"{dec} \times 100 = {pct}\%")
    elif target == "fraction" and source == "decimal":
        places = len(dec.split(".")[1])
        scale = 10 ** places
        st.step(f"The last digit is in the {_PLACE_NAMES[places]} place, so write "
                f"the decimal over ${scale}$.",
                rf"{dec} = \frac{{{int(dec.replace('.', ''))}}}{{{scale}}}")
        _simplify(st, int(dec.replace(".", "")), scale)
    elif target == "fraction":
        st.step("Percent means per hundred, so write the percent over $100$.",
                rf"{pct}\% = \frac{{{pct}}}{{100}}")
        _fraction_from_parts(st, pct, 100)
    if target == "fraction":
        st.answer(solution, lead="In simplest form, the answer is")
    else:
        st.answer(solution)
    return problem, solution, st.done()


@register
def pre_evaluate_expression(min_coeff=2, max_coeff=9, min_const=-9,
                            max_const=9, min_x=-6, max_x=6):
    r"""Evaluate an Algebraic Expression

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $3x + 2$ when $x = 4$. | $14$ |
    """
    a = random.randint(min_coeff, max_coeff)
    b = random.choice([i for i in range(min_const, max_const + 1) if i != 0])
    x = random.randint(min_x, max_x)
    poly = _format_polynomial([(a, 1), (b, 0)])
    result = a * x + b
    problem = f"Evaluate ${poly}$ when $x = {x}$."
    solution = f"${result}$"

    s = Steps()
    s.step(f"Replace $x$ with ${x}$.", f"{a}({x}) {_signed(b)}")
    s.step("Multiply first.", f"{a * x} {_signed(b)}")
    s.step("Then add or subtract.", f"{a * x} {_signed(b)} = {result}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_distributive_property(min_a=2, max_a=9, min_b=1, max_b=9,
                              min_c=-9, max_c=9):
    r"""Distributive Property

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Expand $3(2x + 5)$. | $6x+15$ |
    """
    a = random.randint(min_a, max_a)
    b = random.choice([i for i in range(min_b, max_b + 1) if i != 0])
    c = random.choice([i for i in range(min_c, max_c + 1) if i != 0])
    inner = _format_polynomial([(b, 1), (c, 0)])
    result = _format_polynomial([(a * b, 1), (a * c, 0)])
    problem = f"Expand ${a}({inner})$."
    solution = f"${result}$"

    s = Steps()
    s.step(
        f"The distributive property says to multiply ${a}$ by each term inside "
        "the parentheses.",
        rf"{a} \cdot {_term(b)} + {a} \cdot {paren(c)}",
    )
    s.step("Multiply each term.", f"{_term(a * b)} {_signed(a * c)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_order_rational():
    r"""Order Rational Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Order from least to greatest: $-1/2, 0.75, -2, 1/4$. Separate with commas. | $-2, -1/2, 1/4, 0.75$ |
    """
    denoms = [2, 4, 5, 8, 10]
    n = random.choice([4, 5])
    values = []
    seen = set()
    for _ in range(200):
        if len(values) >= n:
            break
        d = random.choice([1] + denoms)
        v = Fraction(random.randint(-20, 20), d)
        if v in seen:
            continue
        seen.add(v)
        values.append(v)
    # Deterministic top-up (bounded): distinct large integers if sampling was
    # unlucky and produced too few distinct values.
    extra = 100
    while len(values) < n:
        v = Fraction(extra)
        extra += 1
        if v not in seen:
            seen.add(v)
            values.append(v)

    def _disp(value):
        if value.denominator == 1:
            return str(value.numerator)
        if random.random() < 0.5:
            return num(value)          # terminating decimal (<=3 dp)
        return frac_from(value)         # typeable a/b

    pairs = [(v, _disp(v)) for v in values]
    shuffled = pairs[:]
    random.shuffle(shuffled)
    problem_list = ", ".join(text for _, text in shuffled)
    ordered = ", ".join(text for _, text in sorted(pairs, key=lambda t: t[0]))
    problem = (
        f"Order from least to greatest: ${problem_list}$. Separate with commas."
    )
    solution = f"${ordered}$"

    s = Steps()
    fractions = [v for v, text in shuffled if "/" in text]
    if fractions:
        s.step(
            "Write each fraction as a decimal so all the numbers are easy to compare.",
            r",\quad ".join(f"{_tex(v)} = {num(v)}" for v in fractions),
        )
    s.step(
        "Negative numbers are less than positive numbers, and among negative "
        "numbers the one farthest from $0$ is the least. Order the values.",
        " < ".join(num(v) for v in sorted(values)),
    )
    s.answer(solution, lead="Written as in the problem, the order is")
    return problem, solution, s.done()


@register
def pre_coordinate_distance(coord_min=-10, coord_max=10):
    r"""Coordinate Distance

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the distance between the points $(2, 3)$ and $(2, 9)$. | $6$ |
    """
    s = Steps()
    if random.random() < 0.5:
        # Vertical segment: the points share an x-coordinate.
        x = random.randint(coord_min, coord_max)
        y1 = random.randint(coord_min, coord_max)
        y2 = random.randint(coord_min, coord_max)
        if y2 == y1:
            y2 = y1 + 1 if y1 < coord_max else y1 - 1
        p1, p2, dist = (x, y1), (x, y2), abs(y2 - y1)
        s.step(
            f"Both points have $x$-coordinate ${x}$, so they lie on a vertical "
            "line. The distance is the difference of the $y$-coordinates."
        )
        s.step("Subtract and take the absolute value, since distance is never negative.",
               f"|{y2} - {paren(y1)}| = |{y2 - y1}| = {dist}")
    else:
        # Horizontal segment: the points share a y-coordinate.
        y = random.randint(coord_min, coord_max)
        x1 = random.randint(coord_min, coord_max)
        x2 = random.randint(coord_min, coord_max)
        if x2 == x1:
            x2 = x1 + 1 if x1 < coord_max else x1 - 1
        p1, p2, dist = (x1, y), (x2, y), abs(x2 - x1)
        s.step(
            f"Both points have $y$-coordinate ${y}$, so they lie on a horizontal "
            "line. The distance is the difference of the $x$-coordinates."
        )
        s.step("Subtract and take the absolute value, since distance is never negative.",
               f"|{x2} - {paren(x1)}| = |{x2 - x1}| = {dist}")
    problem = (
        f"Find the distance between the points "
        f"$({p1[0]}, {p1[1]})$ and $({p2[0]}, {p2[1]})$."
    )
    solution = f"${dist}$"
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_two_step_equation(min_a=2, max_a=9, min_val=-12, max_val=12):
    r"""Two-Step Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $3x + 4 = 19$ for $x$. Express your answer as a fraction in the form a/b, or an integer. | $5$ |
    """
    a = random.choice([i for i in range(-max_a, max_a + 1) if abs(i) >= min_a])
    b = random.choice([i for i in range(min_val, max_val + 1) if i != 0])
    c = random.randint(min_val, max_val)
    x = Fraction(c - b, a)
    problem = f"Solve ${a}x {_signed(b)} = {c}$ for $x$. {_FRACTION_HINT}"
    solution = _frac_solution(x)

    s = Steps()
    s.step(f"{_move_constant(b)}.", f"{a}x = {c - b}")
    s.step(f"Divide both sides by ${a}$.", rf"x = \frac{{{c - b}}}{{{a}}}")
    _simplify(s, c - b, a)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_multi_step_equation(min_a=2, max_a=9, min_val=-10, max_val=10):
    r"""Multi-Step Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $3(x + 4) = 27$ for $x$. Express your answer as a fraction in the form a/b, or an integer. | $5$ |
    """
    a = random.choice([i for i in range(-max_a, max_a + 1) if abs(i) >= min_a])
    b = random.choice([i for i in range(min_val, max_val + 1) if i != 0])
    c = random.randint(-40, 40)
    x = Fraction(c, a) - b
    problem = f"Solve ${a}(x {_signed(b)}) = {c}$ for $x$. {_FRACTION_HINT}"
    solution = _frac_solution(x)

    q = Fraction(c, a)
    s = Steps()
    divided = rf"\frac{{{c}}}{{{a}}}"
    if _tex(q) != divided:
        divided += f" = {_tex(q)}"
    s.step(f"Divide both sides by ${a}$.", f"x {_signed(b)} = {divided}")
    if q.denominator == 1:
        s.step(f"{_move_constant(b)}.", f"x = {q} {_signed(-b)} = {x}")
    else:
        den = q.denominator
        s.step(
            f"{_move_constant(b)}. Write ${abs(b)}$ as "
            f"${tex_frac(abs(b) * den, den)}$ to combine it with the fraction.",
            rf"x = \frac{{{q.numerator} {_signed(-b * den)}}}{{{den}}} = {_tex(x)}",
        )
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_percent_change():
    r"""Percent Increase or Decrease

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A quantity changes from $80$ to $100$. Find the percent change. Express your answer as a signed percent (e.g. 25% or -25%). | 25% |
    """
    bases = [10, 20, 25, 40, 50, 80, 100, 125, 200, 250]
    pcts = [5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100]
    a_val, b_val = 80, 100
    for _ in range(200):
        base = random.choice(bases)
        pct_mag = random.choice(pcts)
        sign = random.choice([1, -1])
        delta = Fraction(base * pct_mag, 100) * sign
        end = base + delta
        if end.denominator == 1 and end > 0 and end != base:
            a_val, b_val = base, int(end)
            break
    pct = Fraction(b_val - a_val, a_val) * 100
    problem = (
        f"A quantity changes from ${a_val}$ to ${b_val}$. "
        f"Find the percent change. "
        f"Express your answer as a signed percent (e.g. 25% or -25%)."
    )
    solution = f"{frac_from(pct)}%"

    change = b_val - a_val
    s = Steps()
    s.formula(
        "The percent change",
        r"\text{percent change} = \frac{\text{new} - \text{original}}{\text{original}}"
        r" \times 100\%",
    )
    s.substitute(rf"\frac{{{b_val} - {a_val}}}{{{a_val}}} \times 100\%"
                 rf" = \frac{{{change}}}{{{a_val}}} \times 100\%")
    s.step("Divide, then multiply by $100$.",
           rf"{num(Fraction(change, a_val))} \times 100\% = {_tex(pct)}\%")
    kind = "an increase" if change > 0 else "a decrease, so the percent is negative"
    s.step(f"The quantity went from ${a_val}$ to ${b_val}$, which is {kind}.")
    s.answer(solution)
    return problem, solution, s.done()


def _dollars(cents):
    """Render an integer number of cents as a ``$D.CC`` dollar amount."""
    return f"${cents // 100}.{cents % 100:02d}"


@register
def pre_discount_tax_tip(min_price=10, max_price=200):
    r"""Discount, Tax, and Tip

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A jacket costs $48$ dollars. It is discounted by $25\%$. Find the sale price. Give your answer in dollars and cents, for example 36.00. | $36.00 |
    """
    price = random.randint(min_price, max_price)
    pct = random.choice([5, 10, 15, 20, 25, 30, 40, 50])
    kind = random.choice(["discount", "tax", "tip"])
    if kind == "discount":
        item = random.choice(["jacket", "book", "lamp", "backpack", "chair"])
        final_cents = price * (100 - pct)
        clause = f"It is discounted by ${pct}\\%$"
        result_name = "sale price"
        problem = (
            f"A {item} costs ${price}$ dollars. {clause}. "
            f"Find the {result_name}."
        )
    elif kind == "tax":
        final_cents = price * (100 + pct)
        problem = (
            f"A meal costs ${price}$ dollars. A ${pct}\\%$ sales tax is applied. "
            f"Find the total cost."
        )
    else:
        final_cents = price * (100 + pct)
        problem = (
            f"A restaurant bill is ${price}$ dollars. A ${pct}\\%$ tip is added. "
            f"Find the total amount."
        )
    problem += " Give your answer in dollars and cents, for example 12.34."
    solution = _dollars(final_cents)

    # ``price`` dollars times ``pct`` percent is ``price * pct`` cents.
    extra, total = _money(price * pct), _money(final_cents)
    s = Steps()
    s.step(
        rf"Find the {kind}: ${pct}\%$ of ${price}$ dollars. Write the percent as a "
        f"decimal and multiply.",
        rf"{num(Fraction(pct, 100))} \times {price} = {extra}",
    )
    if kind == "discount":
        s.step(f"A discount is taken off, so subtract ${extra}$ dollars from the price.",
               f"{price}.00 - {extra} = {total}")
    else:
        s.step(f"The {kind} is added on, so add ${extra}$ dollars to the original amount.",
               f"{price}.00 + {extra} = {total}")
    # The solution's literal dollar sign would read as a math delimiter here.
    s.answer(f"${total}$ dollars")
    return problem, solution, s.done()


@register
def pre_scale_length(min_k=2, max_k=9, min_len=2, max_len=15):
    r"""Scale Factor Length

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | On a map, $1$ cm represents $4$ km. A road measures $6$ cm on the map. Find the actual length in km. | $24$ |
    """
    k = random.randint(min_k, max_k)
    s = Steps()
    s.step(f"The scale says each $1$ cm on the map stands for ${k}$ km in real life.")
    if random.random() < 0.5:
        # Forward: map length -> actual length.
        d = random.randint(min_len, max_len)
        actual = d * k
        problem = (
            f"On a map, $1$ cm represents ${k}$ km. A road measures ${d}$ cm "
            f"on the map. Find the actual length in km."
        )
        solution = f"${actual}$"
        s.step(f"The road has ${d}$ of those centimeters, so multiply.",
               rf"{d} \times {k} = {actual}")
        s.answer(solution)
        return problem, solution, s.done()
    # Reverse: actual length -> map length (choose actual divisible by k).
    m = random.randint(min_len, max_len)
    actual = m * k
    problem = (
        f"On a map, $1$ cm represents ${k}$ km. A road is ${actual}$ km long. "
        f"Find its length on the map in cm."
    )
    solution = f"${m}$"
    s.step(f"To find how many centimeters make ${actual}$ km, divide by ${k}$.",
           rf"{actual} \div {k} = {m}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_compound_probability(min_total=2, max_total=10):
    r"""Probability of Compound Events

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Bag A has $4$ marbles, $1$ red. Bag B has $3$ marbles, $2$ blue. One marble is drawn from each bag. Find the probability that the A marble is red and the B marble is blue. Express your answer as a fraction in the form a/b, or an integer. | $1/6$ |
    """
    a = random.randint(min_total, max_total)
    b = random.randint(min_total, max_total)
    red = random.randint(1, a)
    blue = random.randint(1, b)
    prob = Fraction(red, a) * Fraction(blue, b)
    problem = (
        f"Bag A has ${a}$ marbles, ${red}$ red. Bag B has ${b}$ marbles, "
        f"${blue}$ blue. One marble is drawn from each bag. Find the "
        f"probability that the A marble is red and the B marble is blue. "
        f"{_FRACTION_HINT}"
    )
    solution = _frac_solution(prob)

    s = Steps()
    s.step(
        "Find each probability: the number of favorable marbles over the total.",
        rf"P(\text{{red}}) = \frac{{{red}}}{{{a}}}, \quad P(\text{{blue}}) = \frac{{{blue}}}{{{b}}}",
    )
    s.step(
        "The draws are from different bags, so they are independent. Multiply "
        "the probabilities.",
        rf"\frac{{{red}}}{{{a}}} \cdot \frac{{{blue}}}{{{b}}} = \frac{{{red * blue}}}{{{a * b}}}",
    )
    _simplify(s, red * blue, a * b)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_variables_both_sides(min_coeff=-9, max_coeff=9):
    r"""Variables on Both Sides

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $5x + 2 = 3x + 8$ for $x$. Express your answer as a fraction in the form a/b, or an integer. | $3$ |
    """
    nonzero = [i for i in range(min_coeff, max_coeff + 1) if i != 0]
    a = random.choice(nonzero)
    c = random.choice(nonzero)
    while c == a:
        c = random.choice(nonzero)
    b = random.choice(nonzero)
    d = random.choice(nonzero)
    x = Fraction(d - b, a - c)
    problem = (
        f"Solve ${a}x {_signed(b)} = {c}x {_signed(d)}$ for $x$. "
        f"{_FRACTION_HINT}"
    )
    solution = _frac_solution(x)

    k = a - c
    s = Steps()
    s.step(f"{_move_constant(c, 'x')} to get the $x$-terms on the left.",
           f"{_term(k)} {_signed(b)} = {d}")
    s.step(f"{_move_constant(b)}.", f"{_term(k)} = {d - b}")
    if k != 1:
        s.step(f"Divide both sides by ${k}$.", rf"x = \frac{{{d - b}}}{{{k}}}")
        _simplify(s, d - b, k)
    s.answer(solution)
    return problem, solution, s.done()


def _line_equation(m, b):
    """Render ``y = mx + b`` typeably for ``Fraction`` slope/intercept."""
    if m == 1:
        slope = "x"
    elif m == -1:
        slope = "-x"
    else:
        slope = f"{frac_from(m)}x"
    if b == 0:
        return f"$y = {slope}$"
    if b > 0:
        return f"$y = {slope} + {frac_from(b)}$"
    return f"$y = {slope} - {frac_from(-b)}$"


@register
def pre_slope_intercept_form(min_coeff=-9, max_coeff=9):
    r"""Slope-Intercept Form from Standard Form

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Rewrite $2x + 4y = 8$ in slope-intercept form. Give the equation in the form y = mx + b. | $y = -1/2x + 2$ |
    """
    nonzero = [i for i in range(min_coeff, max_coeff + 1) if i != 0]
    A = random.choice(nonzero)
    B = random.choice(nonzero)
    C = random.randint(min_coeff, max_coeff)
    m = Fraction(-A, B)
    b = Fraction(C, B)
    problem = (
        f"Rewrite ${A}x {_signed(B)}y = {C}$ in slope-intercept form. "
        f"Give the equation in the form y = mx + b."
    )
    solution = _line_equation(m, b)

    s = Steps()
    s.step(f"Get the $y$-term by itself: {_move_constant(A, 'x').lower()}.",
           f"{_term(B, 'y')} = {_format_polynomial([(-A, 1), (C, 0)])}")
    if B != 1:
        raw = rf"y = \frac{{{-A}}}{{{B}}}x"
        if C != 0:
            raw += rf" + \frac{{{C}}}{{{B}}}"
        s.step(f"Divide every term by ${B}$.", raw)
    s.step("Simplify to the form $y = mx + b$.", _tex_line(m, b))
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_line_from_slope_point(min_val=-8, max_val=8):
    r"""Line from Slope and a Point

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A line has slope $2$ and passes through the point $(3, 4)$. Give the equation in the form y = mx + b. | $y = 2x - 2$ |
    """
    p = random.choice([i for i in range(min_val, max_val + 1) if i != 0])
    q = random.choice([1, 1, 1, 2, 3, 4])
    m = Fraction(p, q)
    x0 = random.randint(min_val, max_val)
    y0 = random.randint(min_val, max_val)
    b = Fraction(y0) - m * x0
    problem = (
        f"A line has slope ${frac_from(m)}$ and passes through the point "
        f"$({x0}, {y0})$. Give the equation in the form y = mx + b."
    )
    solution = _line_equation(m, b)

    mx = m * x0
    s = Steps()
    s.step(
        f"Start from $y = mx + b$. Substitute the slope $m = {_tex(m)}$ and the "
        f"point $x = {x0}$, $y = {y0}$.",
        f"{y0} = {_tex(m)}({x0}) + b",
    )
    s.step("Multiply.", f"{y0} = {_tex(mx)} + b")
    s.step(f"Subtract ${_tex(mx)}$ from both sides to find $b$.",
           f"b = {y0} - {paren(_tex(mx))} = {_tex(b)}")
    s.step("Write the equation with $m$ and $b$.", _tex_line(m, b))
    s.answer(solution)
    return problem, solution, s.done()


@register
def pre_compare_functions(min_val=-9, max_val=9):
    r"""Compare Two Functions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Function A is given by $y = 2x + 1$. Function B passes through the points $(0, 0)$ and $(1, 5)$. Which has the greater rate of change? Answer A or B. | B |
    """
    mA = random.choice([i for i in range(min_val, max_val + 1) if i != 0])
    bA = random.randint(min_val, max_val)
    slope_a = Fraction(mA)
    slope_b = slope_a
    x1 = y1 = x2 = y2 = 0
    for _ in range(100):
        x1 = random.randint(min_val, max_val)
        x2 = random.randint(min_val, max_val)
        if x2 == x1:
            continue
        y1 = random.randint(min_val, max_val)
        y2 = random.randint(min_val, max_val)
        slope_b = Fraction(y2 - y1, x2 - x1)
        if slope_b != slope_a:
            break
    else:
        # Deterministic fallback guaranteeing distinct slopes.
        x1, y1, x2, y2 = 0, 0, 1, mA + 1
        slope_b = Fraction(mA + 1)
    answer = "A" if slope_a > slope_b else "B"
    problem = (
        f"Function A is given by {_line_equation(mA, bA)}. "
        f"Function B passes through the points $({x1}, {y1})$ and "
        f"$({x2}, {y2})$. Which has the greater rate of change? Answer A or B."
    )

    s = Steps()
    s.step(
        f"The rate of change of a line is its slope. Function A is in the form "
        f"$y = mx + b$, so its slope is ${mA}$."
    )
    raw = rf"\frac{{{y2} - {paren(y1)}}}{{{x2} - {paren(x1)}}} = \frac{{{y2 - y1}}}{{{x2 - x1}}}"
    if _tex(slope_b) != rf"\frac{{{y2 - y1}}}{{{x2 - x1}}}":
        raw += f" = {_tex(slope_b)}"
    s.step("Find the slope of function B with $m = \\frac{y_2 - y_1}{x_2 - x_1}$.",
           f"m = {raw}")
    big, small = (slope_a, slope_b) if answer == "A" else (slope_b, slope_a)
    s.step("Compare the slopes.", f"{_tex(big)} > {_tex(small)}")
    s.answer(answer, lead="The function with the greater rate of change is")
    return problem, answer, s.done()


def _classify_system(a1, b1, c1, a2, b2, c2):
    """Return 'one', 'none', or 'infinite' for the given 2x2 linear system."""
    det = a1 * b2 - a2 * b1
    if det != 0:
        return "one"
    # Coefficient rows are parallel; coincident (infinite) iff all augmented
    # 2x2 minors vanish, otherwise the lines are parallel and distinct (none).
    if a1 * c2 - a2 * c1 == 0 and b1 * c2 - b2 * c1 == 0:
        return "infinite"
    return "none"


@register
def pre_system_solution_count(min_coeff=2, max_coeff=6):
    r"""Number of Solutions of a Linear System

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Determine the number of solutions of the system: $2x + 3y = 6$ and $4x + 6y = 7$. Answer 'one', 'none', or 'infinite'. | none |
    """
    nonzero = [i for i in range(-max_coeff, max_coeff + 1) if abs(i) >= 1]
    a1 = random.choice([i for i in nonzero if abs(i) >= min_coeff])
    b1 = random.choice([i for i in nonzero if abs(i) >= min_coeff])
    c1 = random.randint(-9, 9)
    kind = random.choice(["one", "none", "infinite"])
    if kind == "one":
        a2, b2, c2 = a1, b1, random.randint(-9, 9)
        for _ in range(100):
            a2 = random.choice([i for i in nonzero if abs(i) >= min_coeff])
            b2 = random.choice([i for i in nonzero if abs(i) >= min_coeff])
            if a1 * b2 - a2 * b1 != 0:
                break
        else:
            a2, b2 = b1, a1  # deterministic fallback with nonzero det
    else:
        k = random.choice([i for i in range(-4, 5) if abs(i) >= 1])
        a2, b2 = k * a1, k * b1
        if kind == "infinite":
            c2 = k * c1
        else:
            c2 = k * c1 + random.choice([i for i in range(-5, 6) if i != 0])
    answer = _classify_system(a1, b1, c1, a2, b2, c2)
    problem = (
        f"Determine the number of solutions of the system: "
        f"${a1}x {_signed(b1)}y = {c1}$ and ${a2}x {_signed(b2)}y = {c2}$. "
        f"Answer 'one', 'none', or 'infinite'."
    )

    s = Steps()
    s.step(
        "Write each equation in slope-intercept form $y = mx + b$ by solving for $y$.",
        rf"{_tex_line(Fraction(-a1, b1), Fraction(c1, b1))}, \quad "
        rf"{_tex_line(Fraction(-a2, b2), Fraction(c2, b2))}",
    )
    if answer == "one":
        s.step("The slopes are different, so the lines cross at exactly one point.")
    elif answer == "infinite":
        s.step("The slopes and $y$-intercepts are the same, so both equations "
               "describe the same line. Every point on it is a solution.")
    else:
        s.step("The slopes are the same but the $y$-intercepts are different, so "
               "the lines are parallel and never meet.")
    s.answer(answer)
    return problem, answer, s.done()
