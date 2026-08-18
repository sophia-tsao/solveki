"""Solveki-local pre-algebra generators (Georgia grade 6-8 topics).

Every generator name starts with ``pre_`` and returns a ``(problem, solution)``
pair of LaTeX-wrapped strings. Answers are kept clean: integers, short decimals
(<=3 dp), or reduced ``\\frac{p}{q}`` fractions.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._format import frac_from, num
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
    return problem, f"${rate}$"


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
    return problem, f"${d}$"


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
    return problem, f"${x}$"


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
    return problem, f"${result}$"


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
    return problem, _frac_solution(result)


@register
def pre_absolute_value(min_val=-20, max_val=20):
    r"""Absolute Value Expression

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $|3 - 8|$ | $5$ |
    """
    if random.random() < 0.5:
        a = random.randint(max(0, min_val), max_val)
        b = random.randint(max(0, min_val), max_val)
        problem = f"Evaluate $|{a} - {b}|$"
        result = abs(a - b)
    else:
        a = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
        problem = f"Evaluate $|{a}| + |{b}|$"
        result = abs(a) + abs(b)
    return problem, f"${result}$"


@register
def pre_one_step_inequality():
    r"""One-Step Inequality

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the inequality: $x + 3 < 8$ | $x < 5$ |
    """
    op = random.choice(_OPS)
    if random.random() < 0.5:
        # Additive: x + a  op  b  ->  x op (b - a). No sign flip.
        a = random.choice([i for i in range(-10, 11) if i != 0])
        b = random.randint(-20, 20)
        c = b - a
        problem = f"Solve the inequality: $x {_signed(a)} {op} {b}$"
        solution = f"$x {_ASCII_OP[op]} {c}$"
    else:
        # Multiplicative: k*x op b  ->  x op' (b/k). Flip op when k < 0.
        k = random.choice([i for i in range(-10, 11) if abs(i) >= 2])
        c = random.randint(-15, 15)
        b = k * c
        out_op = _FLIP[op] if k < 0 else op
        problem = f"Solve the inequality: ${k}x {op} {b}$"
        solution = f"$x {_ASCII_OP[out_op]} {c}$"
    return problem, solution


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
    return problem, solution


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
            f"Answers should be formatted as such: 5.0*10^4."
        )
        solution = f"${mant}*10^{exp}$"
        return problem, solution


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
    if kind == "mult":
        problem = f"Simplify: ${a}^{{{m}}} \\times {a}^{{{n}}}$"
        r = m + n
    elif kind == "div":
        problem = f"Simplify: ${a}^{{{m}}} \\div {a}^{{{n}}}$"
        r = m - n
    else:
        problem = f"Simplify: $({a}^{{{m}}})^{{{n}}}$"
        r = m * n
    problem += " Answers should be formatted as such: 2^3."
    return problem, f"${a}^{r}$"


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
    return problem, f"${k}$"


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
    return problem, f"${result}$"


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
    return problem, _frac_solution(slope)


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
    return problem, f"${y}$"


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
    return problem, f"${num(mad)}$"


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
    return problem, f"${rng}$"


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
    return problem, f"${mode_val}$"


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
    return problem, f"${iqr}$"


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
        return problem, f"${num(root, 1)}$"


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
    return problem, f"${area}$"


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
    return problem, solution


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
    return problem, f"${result}$"


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
    return problem, f"${result}$"


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
    return problem, f"${ordered}$"


@register
def pre_coordinate_distance(coord_min=-10, coord_max=10):
    r"""Coordinate Distance

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the distance between the points $(2, 3)$ and $(2, 9)$. | $6$ |
    """
    if random.random() < 0.5:
        # Vertical segment: the points share an x-coordinate.
        x = random.randint(coord_min, coord_max)
        y1 = random.randint(coord_min, coord_max)
        y2 = random.randint(coord_min, coord_max)
        if y2 == y1:
            y2 = y1 + 1 if y1 < coord_max else y1 - 1
        p1, p2, dist = (x, y1), (x, y2), abs(y2 - y1)
    else:
        # Horizontal segment: the points share a y-coordinate.
        y = random.randint(coord_min, coord_max)
        x1 = random.randint(coord_min, coord_max)
        x2 = random.randint(coord_min, coord_max)
        if x2 == x1:
            x2 = x1 + 1 if x1 < coord_max else x1 - 1
        p1, p2, dist = (x1, y), (x2, y), abs(x2 - x1)
    problem = (
        f"Find the distance between the points "
        f"$({p1[0]}, {p1[1]})$ and $({p2[0]}, {p2[1]})$."
    )
    return problem, f"${dist}$"


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
    return problem, _frac_solution(x)


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
    return problem, _frac_solution(x)


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
    return problem, f"{frac_from(pct)}%"


def _dollars(cents):
    """Render an integer number of cents as a ``$D.CC`` dollar amount."""
    return f"${cents // 100}.{cents % 100:02d}"


@register
def pre_discount_tax_tip(min_price=10, max_price=200):
    r"""Discount, Tax, and Tip

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A jacket costs $48$ dollars. It is discounted by $25\%$. Find the sale price. Format your answer as a dollar amount like $X.XX. | $36.00 |
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
    problem += " Format your answer as a dollar amount like $X.XX."
    return problem, _dollars(final_cents)


@register
def pre_scale_length(min_k=2, max_k=9, min_len=2, max_len=15):
    r"""Scale Factor Length

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | On a map, $1$ cm represents $4$ km. A road measures $6$ cm on the map. Find the actual length in km. | $24$ |
    """
    k = random.randint(min_k, max_k)
    if random.random() < 0.5:
        # Forward: map length -> actual length.
        d = random.randint(min_len, max_len)
        actual = d * k
        problem = (
            f"On a map, $1$ cm represents ${k}$ km. A road measures ${d}$ cm "
            f"on the map. Find the actual length in km."
        )
        return problem, f"${actual}$"
    # Reverse: actual length -> map length (choose actual divisible by k).
    m = random.randint(min_len, max_len)
    actual = m * k
    problem = (
        f"On a map, $1$ cm represents ${k}$ km. A road is ${actual}$ km long. "
        f"Find its length on the map in cm."
    )
    return problem, f"${m}$"


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
    return problem, _frac_solution(prob)


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
    return problem, _frac_solution(x)


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
    return problem, _line_equation(m, b)


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
    return problem, _line_equation(m, b)


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
    return problem, answer


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
    return problem, answer
