"""Solveki-local calculus generators.

Every generator here targets a computable gap in the Georgia "Calculus"
curriculum. Each takes no required arguments, returns a ``(problem, solution)``
pair of LaTeX strings, and produces a clean answer (integer, fraction, short
float, or short polynomial string). Names are prefixed ``calc_`` so they are
easy to scope.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._format import num as _num
from .algebra import _format_polynomial

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."


# --- small polynomial helpers (poly represented as {exponent: coefficient}) ---

def _poly_eval(poly, x):
    """Evaluate ``poly`` at ``x`` (works for ints and Fractions)."""
    return sum(coeff * (x ** exp) for exp, coeff in poly.items())


def _poly_deriv(poly):
    """Return the derivative of ``poly`` as a new dict."""
    return {exp - 1: coeff * exp for exp, coeff in poly.items() if exp >= 1}


def _poly_mul(p, q):
    """Multiply two polynomials."""
    out = {}
    for e1, c1 in p.items():
        for e2, c2 in q.items():
            out[e1 + e2] = out.get(e1 + e2, 0) + c1 * c2
    return out


def _poly_add(p, q):
    """Add two polynomials."""
    out = dict(p)
    for exp, coeff in q.items():
        out[exp] = out.get(exp, 0) + coeff
    return out


def _poly_str(poly):
    """Render a poly dict via the shared algebra formatter."""
    terms = sorted(poly.items(), key=lambda kv: -kv[0])
    return _format_polynomial([(coeff, exp) for exp, coeff in terms])


def _fmt_frac(value):
    """Render a Fraction (or int) as ``"a/b"`` or ``"a"`` when whole."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _rand_poly(degree, lo=-5, hi=5):
    """A random poly of exactly ``degree`` (leading coeff nonzero)."""
    poly = {}
    for exp in range(degree + 1):
        poly[exp] = random.randint(lo, hi)
    lead = random.choice([c for c in range(lo, hi + 1) if c != 0])
    poly[degree] = lead
    return poly


# --------------------------------- limits ---------------------------------

@register
def calc_limit_rational(min_c=-4, max_c=4):
    r"""Limit of a Rational Function at a Point

    Either a removable discontinuity (shared linear factor cancels) or a
    direct substitution. Answer is an exact, reduced value.
    """
    c = random.randint(min_c, max_c)
    if random.random() < 0.5:
        # Removable: num = (x - c)*L1, den = (x - c)*L2 with L2(c) != 0.
        l1 = {1: random.choice([i for i in range(-4, 5) if i != 0]),
              0: random.randint(-5, 5)}
        while True:
            l2 = {1: random.choice([i for i in range(-4, 5) if i != 0]),
                  0: random.randint(-5, 5)}
            if _poly_eval(l2, c) != 0:
                break
        factor = {1: 1, 0: -c}
        num = _poly_mul(factor, l1)
        den = _poly_mul(factor, l2)
        ans = Fraction(_poly_eval(l1, c), _poly_eval(l2, c))
    else:
        # Direct substitution: den(c) != 0.
        num = _rand_poly(random.randint(1, 2))
        while True:
            den = _rand_poly(random.randint(1, 2))
            if _poly_eval(den, c) != 0:
                break
        ans = Fraction(_poly_eval(num, c), _poly_eval(den, c))

    problem = (
        f"Evaluate $\\lim_{{x \\to {c}}} "
        f"\\frac{{{_poly_str(num)}}}{{{_poly_str(den)}}}$. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    return problem, solution


@register
def calc_limit_conjugate(min_b=1, max_b=6):
    r"""Limit Using the Conjugate

    A $0/0$ indeterminate limit with a square root, resolved by multiplying by
    the conjugate. Built around $\sqrt{x} = b$ at $x = b^2$, so cancelling the
    common ``(x - b^2)`` factor leaves ``1/(sqrt(x) + b)`` (or its reciprocal),
    giving a clean value at the point.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\lim_{x \to 9} \frac{\sqrt{x}-3}{x-9}$ | $1/6$ |
    """
    b = random.randint(min_b, max_b)
    c = b * b
    if random.random() < 0.5:
        # (sqrt(x) - b)/(x - b^2) -> 1/(sqrt(x) + b) -> 1/(2b)
        num, den = f"\\sqrt{{x}}-{b}", f"x-{c}"
        ans = Fraction(1, 2 * b)
    else:
        # (x - b^2)/(sqrt(x) - b) -> sqrt(x) + b -> 2b
        num, den = f"x-{c}", f"\\sqrt{{x}}-{b}"
        ans = Fraction(2 * b)
    problem = (
        f"Evaluate $\\lim_{{x \\to {c}}} \\frac{{{num}}}{{{den}}}$ by "
        f"multiplying by the conjugate. {_FRACTION_HINT}"
    )
    return problem, f"${_fmt_frac(ans)}$"


# ------------------------------ derivatives -------------------------------

@register
def calc_derivative_polynomial(min_degree=2, max_degree=4):
    r"""Derivative of a Polynomial

    Solution is the derivative polynomial as a string.
    """
    poly = _rand_poly(random.randint(min_degree, max_degree))
    deriv = _poly_deriv(poly)
    problem = (
        f"Find the derivative of $f(x) = {_poly_str(poly)}$. "
        f"Write your answer as a polynomial, e.g. 3x^2-2x+1."
    )
    solution = f"${_poly_str(deriv)}$"
    return problem, solution


@register
def calc_product_rule(min_c=-4, max_c=4):
    r"""Product Rule at a Point

    Derivative of a product of two linear/quadratic factors, evaluated at a
    point for an exact numeric answer.
    """
    def factor():
        deg = random.randint(1, 2)
        return _rand_poly(deg, lo=-4, hi=4)

    f1, f2 = factor(), factor()
    c = random.randint(min_c, max_c)
    product = _poly_mul(f1, f2)
    ans = _poly_eval(_poly_deriv(product), c)
    problem = (
        f"Find the derivative of $f(x) = ({_poly_str(f1)})({_poly_str(f2)})$ "
        f"at $x = {c}$"
    )
    solution = f"${ans}$"
    return problem, solution


@register
def calc_quotient_rule(min_c=-4, max_c=4):
    r"""Quotient Rule at a Point

    Derivative of a (linear)/(linear) rational at a point, exact reduced
    fraction.
    """
    num = {1: random.choice([i for i in range(-5, 6) if i != 0]),
           0: random.randint(-5, 5)}
    c = random.randint(min_c, max_c)
    while True:
        den = {1: random.choice([i for i in range(-5, 6) if i != 0]),
               0: random.randint(-5, 5)}
        if _poly_eval(den, c) != 0:
            break
    # (num' den - num den') / den^2
    numd, dend = _poly_deriv(num), _poly_deriv(den)
    top = (_poly_eval(numd, c) * _poly_eval(den, c)
           - _poly_eval(num, c) * _poly_eval(dend, c))
    bottom = _poly_eval(den, c) ** 2
    ans = Fraction(top, bottom)
    problem = (
        f"Find the derivative of $f(x) = "
        f"\\frac{{{_poly_str(num)}}}{{{_poly_str(den)}}}$ at $x = {c}$. "
        f"{_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    return problem, solution


@register
def calc_chain_rule(min_c=-3, max_c=3, max_power=4):
    r"""Chain Rule at a Point

    Derivative of $(ax+b)^n$ evaluated at a point, exact numeric.
    """
    a = random.choice([i for i in range(-3, 4) if i != 0])
    b = random.randint(-4, 4)
    n = random.randint(2, max_power)
    c = random.randint(min_c, max_c)
    inner = {1: a, 0: b}
    ans = n * a * (_poly_eval(inner, c) ** (n - 1))
    problem = (
        f"Find the derivative of $f(x) = ({_poly_str(inner)})^{{{n}}}$ "
        f"at $x = {c}$"
    )
    solution = f"${ans}$"
    return problem, solution


@register
def calc_derivative_exp_log_trig():
    r"""Derivative of an Exponential, Logarithmic, or Trig Function

    One of $a e^{kx}$, $a \ln(x)$, $a \sin(kx)$, or $a \cos(kx)$, evaluated
    at a point and reported to 3 decimal places.
    """
    kind = random.choice(["exp", "ln", "sin", "cos"])
    a = random.choice([i for i in range(-6, 7) if i != 0])
    if kind == "ln":
        c = random.randint(1, 6)
        expr = f"{a} \\ln(x)"
        value = a / c
    else:
        k = random.choice([i for i in range(-3, 4) if i != 0])
        c = random.randint(-3, 3)
        if kind == "exp":
            expr = f"{a} e^{{{k} x}}"
            value = a * k * math.exp(k * c)
        elif kind == "sin":
            expr = f"{a} \\sin({k} x)"
            value = a * k * math.cos(k * c)
        else:  # cos
            expr = f"{a} \\cos({k} x)"
            value = -a * k * math.sin(k * c)
    problem = (
        f"Find the derivative of $f(x) = {expr}$ at $x = {c}$. "
        f"Round your answer to the nearest thousandth."
    )
    solution = f"${_num(value)}$"
    return problem, solution


@register
def calc_higher_order_derivative(min_c=-3, max_c=3):
    r"""Higher-Order Derivative at a Point

    The n-th derivative of a polynomial evaluated at a point, exact numeric.
    """
    order = random.randint(2, 3)
    degree = random.randint(order, order + 2)
    poly = _rand_poly(degree)
    d = poly
    for _ in range(order):
        d = _poly_deriv(d)
    c = random.randint(min_c, max_c)
    ans = _poly_eval(d, c) if d else 0
    ordinal = {2: "2nd", 3: "3rd"}[order]
    problem = (
        f"Find the {ordinal} derivative of $f(x) = {_poly_str(poly)}$ "
        f"at $x = {c}$"
    )
    solution = f"${ans}$"
    return problem, solution


# ------------------------- applications of derivatives --------------------

@register
def calc_tangent_line(min_c=-3, max_c=3):
    r"""Tangent Line to a Polynomial at a Point

    Solution is the line ``y = m x + b``.
    """
    poly = _rand_poly(random.randint(2, 3))
    c = random.randint(min_c, max_c)
    m = _poly_eval(_poly_deriv(poly), c)
    b = _poly_eval(poly, c) - m * c
    rhs = _poly_str({1: m, 0: b})
    problem = (
        f"Find the tangent line to $f(x) = {_poly_str(poly)}$ at $x = {c}$. "
        f"Write your answer in the form y = mx+b."
    )
    solution = f"$y = {rhs}$"
    return problem, solution


@register
def calc_extrema(min_root=-5, max_root=5):
    r"""Critical Points via the First Derivative

    Critical x-values of a quadratic or cubic, sorted, as ``x = a, b``.
    """
    if random.random() < 0.5:
        # Quadratic with an integer critical point.
        a = random.choice([i for i in range(-4, 5) if i != 0])
        r = random.randint(min_root, max_root)
        poly = {2: a, 1: -2 * a * r, 0: random.randint(-5, 5)}
        roots = [r]
    else:
        # Cubic with two distinct integer critical points.
        while True:
            r1 = random.randint(min_root, max_root)
            r2 = random.randint(min_root, max_root)
            if r1 != r2 and (r1 + r2) % 2 == 0:
                break
        r1, r2 = sorted((r1, r2))
        a = random.choice([i for i in range(-3, 4) if i != 0])
        b = -3 * a * (r1 + r2) // 2
        c = 3 * a * r1 * r2
        poly = {3: a, 2: b, 1: c, 0: random.randint(-5, 5)}
        roots = [r1, r2]
    xs = ", ".join(str(x) for x in sorted(roots))
    problem = (
        f"Find the critical points of $f(x) = {_poly_str(poly)}$. "
        f"Give the x-value(s) as integers or fractions a/b, comma-separated "
        f"and in increasing order."
    )
    solution = f"$x = {xs}$"
    return problem, solution


@register
def calc_inflection_point(max_coeff=6):
    r"""Inflection Point of a Cubic via the Second Derivative

    Reports the exact reduced x-value of the inflection point.
    """
    a = random.choice([i for i in range(-4, 5) if i != 0])
    b = random.randint(-max_coeff, max_coeff)
    c = random.randint(-max_coeff, max_coeff)
    d = random.randint(-max_coeff, max_coeff)
    poly = {3: a, 2: b, 1: c, 0: d}
    # f'' = 6a x + 2b -> x = -b / (3a)
    ans = Fraction(-b, 3 * a)
    problem = (
        f"Find the inflection point of $f(x) = {_poly_str(poly)}$. "
        f"Give the x-value as an integer or fraction a/b. {_FRACTION_HINT}"
    )
    solution = f"$x = {_fmt_frac(ans)}$"
    return problem, solution


# -------------------------------- integrals -------------------------------

@register
def calc_definite_integral_poly():
    r"""Definite Integral of a Polynomial

    Exact value over ``[a, b]``.
    """
    poly = _rand_poly(random.randint(1, 3))
    a = random.randint(-4, 3)
    b = random.randint(a + 1, 5)
    total = sum(
        Fraction(coeff * (b ** (exp + 1) - a ** (exp + 1)), exp + 1)
        for exp, coeff in poly.items()
    )
    problem = (
        f"Evaluate $\\int_{{{a}}}^{{{b}}} {_poly_str(poly)} \\, dx$. "
        f"{_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(total)}$"
    return problem, solution


@register
def calc_indefinite_integral_poly():
    r"""Indefinite Integral of a Polynomial

    Antiderivative (with ``+ C``) has clean integer coefficients by
    construction.
    """
    degree = random.randint(1, 3)
    poly = {}
    anti = {}
    for exp in range(degree + 1):
        m = random.randint(-4, 4)
        if exp == degree and m == 0:
            m = random.choice([-2, -1, 1, 2])
        poly[exp] = m * (exp + 1)      # integrates to m*x^(exp+1)
        anti[exp + 1] = m
    problem = (
        f"Find the indefinite integral $\\int {_poly_str(poly)} \\, dx$. "
        f"Write your answer as a polynomial plus C, e.g. x^2+3x + C."
    )
    solution = f"${_poly_str(anti)} + C$"
    return problem, solution


@register
def calc_usub_integral():
    r"""Definite Integral by u-Substitution

    $\int_p^q (ax+b)^n \, dx$, exact value.
    """
    a = random.choice([i for i in range(-3, 4) if i != 0])
    b = random.randint(-4, 4)
    n = random.randint(2, 4)
    p = random.randint(-3, 2)
    q = random.randint(p + 1, 4)
    upper = (a * q + b) ** (n + 1)
    lower = (a * p + b) ** (n + 1)
    ans = Fraction(upper - lower, a * (n + 1))
    inner = _poly_str({1: a, 0: b})
    problem = (
        f"Evaluate $\\int_{{{p}}}^{{{q}}} ({inner})^{{{n}}} \\, dx$. "
        f"{_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    return problem, solution


@register
def calc_area_between_curves():
    r"""Area Between Two Curves

    Two polynomials that meet at the endpoints ``a`` and ``b`` (so one stays
    above the other on the interval). Exact area.
    """
    a = random.randint(-3, 2)
    b = random.randint(a + 1, 4)
    g = _rand_poly(random.randint(0, 2), lo=-3, hi=3)
    c = random.choice([-3, -2, -1])        # C < 0 -> f - g >= 0 on [a, b]
    diff = _poly_mul({1: c}, _poly_mul({1: 1, 0: -a}, {1: 1, 0: -b}))
    f = _poly_add(g, diff)
    # area = integral of (f - g) = integral of diff over [a, b]
    area = sum(
        Fraction(coeff * (b ** (exp + 1) - a ** (exp + 1)), exp + 1)
        for exp, coeff in diff.items()
    )
    problem = (
        f"Find the area between $f(x) = {_poly_str(f)}$ and "
        f"$g(x) = {_poly_str(g)}$ over $[{a}, {b}]$. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(abs(area))}$"
    return problem, solution


@register
def calc_average_value():
    r"""Average Value of a Function

    $\frac{1}{b-a}\int_a^b f(x)\,dx$ for a polynomial. Exact.
    """
    poly = _rand_poly(random.randint(1, 3))
    a = random.randint(-4, 3)
    b = random.randint(a + 1, 5)
    integral = sum(
        Fraction(coeff * (b ** (exp + 1) - a ** (exp + 1)), exp + 1)
        for exp, coeff in poly.items()
    )
    ans = integral / (b - a)
    problem = (
        f"Find the average value of $f(x) = {_poly_str(poly)}$ on $[{a}, {b}]$. "
        f"{_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    return problem, solution


@register
def calc_riemann_sum():
    r"""Left or Right Riemann Sum

    A polynomial on ``[a, b]`` with ``n`` rectangles. Exact value.
    """
    side = random.choice(["left", "right"])
    poly = _rand_poly(random.randint(1, 2), lo=-3, hi=3)
    a = random.randint(-3, 2)
    b = random.randint(a + 1, 4)
    n = random.randint(2, 6)
    dx = Fraction(b - a, n)
    indices = range(n) if side == "left" else range(1, n + 1)
    total = sum(_poly_eval(poly, a + i * dx) for i in indices)
    ans = dx * total
    problem = (
        f"Find the {side} Riemann sum of $f(x) = {_poly_str(poly)}$ on "
        f"$[{a}, {b}]$ using ${n}$ rectangles. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    return problem, solution


# ------------------------- more calculus (chunk) --------------------------

def _implicit_lhs(A, B, C):
    """Render ``A x^2 + B xy + C y^2`` with clean signs (omit zero terms)."""
    parts = []
    for coeff, var in [(A, "x^2"), (B, "xy"), (C, "y^2")]:
        if coeff == 0:
            continue
        mag = abs(coeff)
        body = ("" if mag == 1 else str(mag)) + var
        parts.append(("-" if coeff < 0 else "+", body))
    out = ""
    for i, (sign, body) in enumerate(parts):
        if i == 0:
            out += ("-" if sign == "-" else "") + body
        else:
            out += f" {sign} {body}"
    return out


def _cx(coef):
    """Render ``coef * x`` as ``x``/``-x``/``3 x`` for use inside functions."""
    if coef == 1:
        return "x"
    if coef == -1:
        return "-x"
    return f"{coef} x"


@register
def calc_implicit_differentiation():
    r"""Implicit Differentiation

    Differentiate a conic relation $A x^2 + B xy + C y^2 = D$ implicitly and
    evaluate $dy/dx$ at an integer point on the curve.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given the implicit relation $x^2 + y^2 = 25$, find $dy/dx$ at the point $(3, 4)$. | $-3/4$ |
    """
    for _ in range(200):
        A = random.choice([i for i in range(-4, 5) if i != 0])
        C = random.choice([i for i in range(-4, 5) if i != 0])
        B = random.randint(-3, 3)
        x0 = random.choice([i for i in range(-4, 5) if i != 0])
        y0 = random.choice([i for i in range(-4, 5) if i != 0])
        denom = B * x0 + 2 * C * y0
        if denom != 0:
            break
    else:
        A, B, C, x0, y0, denom = 1, 0, 1, 3, 4, 8
    D = A * x0 * x0 + B * x0 * y0 + C * y0 * y0
    lhs = _implicit_lhs(A, B, C)
    ans = Fraction(-(2 * A * x0 + B * y0), denom)
    problem = (
        f"Given the implicit relation ${lhs} = {D}$, find $dy/dx$ at the "
        f"point $({x0}, {y0})$. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    return problem, solution


@register
def calc_particle_motion():
    r"""Particle Motion

    A particle has polynomial position $s(t)$. Find its velocity or
    acceleration at a time, or the time when the velocity is zero.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A particle moves along a line with position $s(t) = t^3-2t^2+t$. Find its velocity at $t = 2$. | $5$ |
    """
    ask = random.choice(["velocity", "acceleration", "rest"])
    if ask == "rest":
        A = random.choice([i for i in range(-4, 5) if i != 0])
        B = random.choice([i for i in range(-6, 7) if i != 0])
        Cc = random.randint(-6, 6)
        s = {2: A, 1: B, 0: Cc}
        root = Fraction(-B, 2 * A)
        body = _poly_str(s).replace("x", "t")
        problem = (
            f"A particle moves along a line with position $s(t) = {body}$. "
            f"Find the time $t$ at which its velocity is zero. {_FRACTION_HINT}"
        )
        return problem, f"${_fmt_frac(root)}$"
    s = _rand_poly(random.randint(2, 3))
    t = random.randint(-3, 4)
    body = _poly_str(s).replace("x", "t")
    if ask == "velocity":
        val = _poly_eval(_poly_deriv(s), t)
    else:
        val = _poly_eval(_poly_deriv(_poly_deriv(s)), t)
    problem = (
        f"A particle moves along a line with position $s(t) = {body}$. "
        f"Find its {ask} at $t = {t}$."
    )
    return problem, f"${val}$"


_KPI_HINT = "Your answer has the form k*pi; give the value of k as a fraction a/b or an integer."


@register
def calc_volume_revolution():
    r"""Volume of a Solid of Revolution

    Revolve a region under (disk) or between (washer) polynomial curves about
    the x-axis. The volume is $k\pi$; the student reports $k$ exactly.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | The region under $y = x$ from $x = 0$ to $x = 3$ is revolved about the x-axis. Find the volume. Your answer has the form k*pi; give k. | $9$ |
    """
    a = random.randint(0, 3)
    b = random.randint(a + 1, 5)
    if random.random() < 0.5:
        # Disk: f(x) = m x + c, positive on [a, b] (a >= 0).
        m = random.randint(0, 3)
        c = random.randint(1, 4)
        f = {1: m, 0: c}
        fsq = _poly_mul(f, f)
        k = sum(
            Fraction(coeff * (b ** (e + 1) - a ** (e + 1)), e + 1)
            for e, coeff in fsq.items()
        )
        problem = (
            f"The region under $y = {_poly_str(f)}$ from $x = {a}$ to "
            f"$x = {b}$ is revolved about the x-axis. Find the volume. "
            f"{_KPI_HINT}"
        )
    else:
        # Washer: outer R = m x + (p + q) strictly above inner r = p.
        p = random.randint(1, 3)
        mm = random.randint(1, 3)
        q = random.randint(1, 3)
        R = {1: mm, 0: p + q}
        r = {0: p}
        diff = _poly_add(_poly_mul(R, R), {e: -coeff for e, coeff in _poly_mul(r, r).items()})
        k = sum(
            Fraction(coeff * (b ** (e + 1) - a ** (e + 1)), e + 1)
            for e, coeff in diff.items()
        )
        problem = (
            f"The region between $y = {_poly_str(R)}$ and $y = {_poly_str(r)}$ "
            f"from $x = {a}$ to $x = {b}$ is revolved about the x-axis. Find "
            f"the volume. {_KPI_HINT}"
        )
    return problem, f"${_fmt_frac(k)}$"


@register
def calc_lhopital():
    r"""L'Hopital's Rule

    A $0/0$ indeterminate limit at $x = 0$ resolved by one application of
    L'Hopital's Rule, with an exact rational value.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Use L'Hopital's Rule to evaluate $\lim_{x \to 0} \frac{\sin(3 x)}{2 x}$. | $3/2$ |
    """
    kind = random.choice(["sin", "exp", "cos", "tan"])
    a = random.choice([i for i in range(-5, 6) if i != 0])
    if kind == "cos":
        c = random.randint(1, 4)
        num = f"1-\\cos({_cx(a)})"
        den = f"x^2" if c == 1 else f"{c} x^2"
        ans = Fraction(a * a, 2 * c)
    else:
        b = random.choice([i for i in range(-5, 6) if i != 0])
        den = _cx(b)
        if kind == "sin":
            num = f"\\sin({_cx(a)})"
        elif kind == "tan":
            num = f"\\tan({_cx(a)})"
        else:  # exp
            num = f"e^{{{_cx(a)}}}-1"
        ans = Fraction(a, b)
    problem = (
        f"Use L'Hopital's Rule to evaluate "
        f"$\\lim_{{x \\to 0}} \\frac{{{num}}}{{{den}}}$. {_FRACTION_HINT}"
    )
    return problem, f"${_fmt_frac(ans)}$"


@register
def calc_limit_definition_derivative():
    r"""Derivative Using the Limit Definition

    Apply the limit definition $f'(x)=\lim_{h\to0}(f(x+h)-f(x))/h$ to a
    quadratic and evaluate the derivative at a point (an integer value).

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Using the limit definition of the derivative, find $f'(2)$ for $f(x) = 3x^2-x+1$. | $11$ |
    """
    A = random.choice([i for i in range(-5, 6) if i != 0])
    B = random.randint(-6, 6)
    C = random.randint(-6, 6)
    poly = {2: A, 1: B, 0: C}
    p = random.randint(-4, 4)
    ans = _poly_eval(_poly_deriv(poly), p)
    problem = (
        f"Using the limit definition of the derivative, find $f'({p})$ for "
        f"$f(x) = {_poly_str(poly)}$."
    )
    return problem, f"${ans}$"


@register
def calc_integration_by_parts():
    r"""Integration by Parts

    A definite integral evaluated with one round of integration by parts:
    $x e^x$, $x\sin x$, $x\cos x$, or $x\ln x$ over clean integer bounds.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\int_{0}^{1} x e^{x} \, dx$. Round to the nearest thousandth if necessary. | $1$ |
    """
    kind = random.choice(["xex", "xsin", "xcos", "xln"])
    if kind == "xln":
        p = random.randint(1, 3)
        q = random.randint(p + 1, 5)
        integrand = "x \\ln(x)"

        def F(t):
            return t * t / 2 * math.log(t) - t * t / 4
    else:
        p = random.randint(-2, 3)
        q = random.randint(p + 1, 4)
        if kind == "xex":
            integrand = "x e^{x}"

            def F(t):
                return (t - 1) * math.exp(t)
        elif kind == "xsin":
            integrand = "x \\sin(x)"

            def F(t):
                return math.sin(t) - t * math.cos(t)
        else:  # xcos
            integrand = "x \\cos(x)"

            def F(t):
                return math.cos(t) + t * math.sin(t)
    value = F(q) - F(p)
    problem = (
        f"Evaluate $\\int_{{{p}}}^{{{q}}} {integrand} \\, dx$. "
        f"Round to the nearest thousandth if necessary."
    )
    return problem, f"${_num(value)}$"


# ---------------------- calculus (chunk 2 additions) ----------------------

_TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25),
            (20, 21, 29), (9, 40, 41), (6, 8, 10)]


@register
def calc_related_rates():
    r"""Related Rates

    An expanding circle, expanding sphere, or a sliding ladder. The requested
    rate is exact: circle/sphere rates come out as $k\pi$ (report $k$), while
    the ladder gives a clean rational rate.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A 5 ft ladder leans against a wall. Its base slides away from the wall at 2 ft/s. Find $dy/dt$ (the rate of change of the top's height) when the base is 3 ft from the wall. | $-3/2$ |
    """
    kind = random.choice(["circle", "sphere", "ladder"])
    if kind == "circle":
        r = random.randint(2, 8)
        dr = random.randint(1, 5)
        k = 2 * r * dr
        problem = (
            f"A circle's radius grows at ${dr}$ units per second. Find the "
            f"rate of change of its area $dA/dt$ when the radius is ${r}$. "
            f"{_KPI_HINT}"
        )
        return problem, f"${_fmt_frac(k)}$"
    if kind == "sphere":
        r = random.randint(2, 6)
        dr = random.randint(1, 4)
        k = 4 * r * r * dr
        problem = (
            f"A sphere's radius grows at ${dr}$ units per second. Find the "
            f"rate of change of its volume $dV/dt$ when the radius is ${r}$. "
            f"{_KPI_HINT}"
        )
        return problem, f"${_fmt_frac(k)}$"
    # ladder: base = horizontal leg x, height = vertical leg y, x^2+y^2=c^2
    a, b, c = random.choice(_TRIPLES)
    if random.random() < 0.5:
        a, b = b, a
    v = random.randint(1, 4)
    ans = Fraction(-a * v, b)      # dy/dt = -(x/y) dx/dt
    problem = (
        f"A ${c}$ ft ladder leans against a wall. Its base slides away from "
        f"the wall at ${v}$ ft/s. Find $dy/dt$ (the rate of change of the "
        f"top's height) when the base is ${a}$ ft from the wall. "
        f"{_FRACTION_HINT}"
    )
    return problem, f"${_fmt_frac(ans)}$"


@register
def calc_mvt_find_c():
    r"""Mean Value Theorem

    Given $f$ on $[a, b]$, find the value $c$ in $(a, b)$ guaranteed by the
    Mean Value Theorem, where $f'(c)$ equals the average rate of change. A
    quadratic gives $c$ at the midpoint; $f(x)=x^3$ gives an irrational $c$.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Let $f(x) = x^2$ on the interval $[0, 4]$. Find the value $c$ in $(0, 4)$ guaranteed by the Mean Value Theorem. Round to the nearest thousandth if the value is irrational. | $2$ |
    """
    if random.random() < 0.5:
        A = random.choice([i for i in range(-4, 5) if i != 0])
        B = random.randint(-6, 6)
        Cc = random.randint(-6, 6)
        a = random.randint(-4, 2)
        b = random.randint(a + 1, 5)
        poly = {2: A, 1: B, 0: Cc}
        c = (a + b) / 2                      # 2A c + B = A(a+b)+B
    else:
        a = random.randint(0, 3)
        b = random.randint(a + 1, 5)
        poly = {3: 1}
        c = math.sqrt((a * a + a * b + b * b) / 3)   # 3c^2 = a^2+ab+b^2
    body = _poly_str(poly)
    problem = (
        f"Let $f(x) = {body}$ on the interval $[{a}, {b}]$. Find the value "
        f"$c$ in $({a}, {b})$ guaranteed by the Mean Value Theorem. "
        f"Round to the nearest thousandth if the value is irrational."
    )
    return problem, f"${_num(c)}$"


@register
def calc_trapezoidal_rule():
    r"""Trapezoidal Rule

    Approximate the definite integral of a polynomial over $[a, b]$ using $n$
    trapezoids, reporting the estimate to the nearest thousandth.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Use the Trapezoidal Rule with $n = 2$ subintervals to approximate $\int_{0}^{2} x^2 \, dx$. Round to the nearest thousandth. | $3$ |
    """
    poly = _rand_poly(random.randint(1, 3), lo=-3, hi=3)
    a = random.randint(-3, 2)
    b = random.randint(a + 1, 5)
    n = random.randint(2, 6)
    dx = (b - a) / n
    total = 0.0
    for i in range(n + 1):
        x = a + i * dx
        weight = 1 if (i == 0 or i == n) else 2
        total += weight * _poly_eval(poly, x)
    approx = dx / 2 * total
    problem = (
        f"Use the Trapezoidal Rule with $n = {n}$ subintervals to approximate "
        f"$\\int_{{{a}}}^{{{b}}} {_poly_str(poly)} \\, dx$. "
        f"Round to the nearest thousandth."
    )
    return problem, f"${_num(approx)}$"


@register
def calc_separable_ode():
    r"""Separable Differential Equation

    Solve $dy/dx = f(x)g(y)$ with an initial condition, then evaluate the
    solution at a point. Both forms have strictly positive solutions, so the
    value is always defined and reported to the nearest thousandth.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the separable differential equation $dy/dx = 1 y$ with $y(0) = 2$, then find $y(1)$. Round to the nearest thousandth if necessary. | $5.437$ |
    """
    if random.random() < 0.5:
        k = random.choice([-2, -1, 1, 2])
        y0 = random.randint(1, 5)
        x0 = random.randint(0, 1)
        x1 = random.randint(-1, 2)
        y1 = y0 * math.exp(k * (x1 - x0))       # y = y0 e^{k (x - x0)}
        eq = f"dy/dx = {k} y"
    else:
        k = random.choice([-1, 1])
        y0 = random.randint(1, 5)
        x0 = random.randint(0, 1)
        x1 = random.randint(0, 2)
        y1 = y0 * math.exp(k * (x1 * x1 - x0 * x0) / 2)  # y = y0 e^{k(x^2-x0^2)/2}
        eq = f"dy/dx = {k} x y"
    problem = (
        f"Solve the separable differential equation ${eq}$ with "
        f"$y({x0}) = {y0}$, then find $y({x1})$. "
        f"Round to the nearest thousandth if necessary."
    )
    return problem, f"${_num(y1)}$"


@register
def calc_concavity_interval():
    r"""Concavity Interval

    For a cubic, $f'' = 6Ax + 2B$ changes sign at $x = -B/(3A)$. The function is
    concave up on the half-line where $f'' > 0$.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | On what interval is $f(x) = x^3-3x^2+2$ concave up? Answer as an interval like (a, inf) or (-inf, a). | $(1, inf)$ |
    """
    A = random.choice([i for i in range(-4, 5) if i != 0])
    B = random.randint(-6, 6)
    Cc = random.randint(-6, 6)
    D = random.randint(-6, 6)
    poly = {3: A, 2: B, 1: Cc, 0: D}
    x_inf = Fraction(-B, 3 * A)
    if A > 0:
        interval = f"({_fmt_frac(x_inf)}, inf)"
    else:
        interval = f"(-inf, {_fmt_frac(x_inf)})"
    problem = (
        f"On what interval is $f(x) = {_poly_str(poly)}$ concave up? "
        f"Answer as an interval like (a, inf) or (-inf, a)."
    )
    return problem, f"${interval}$"


@register
def calc_taylor_coefficient():
    r"""Taylor/Maclaurin Coefficient

    The exact coefficient of $x^k$ in the Maclaurin series of a standard
    function ($e^x$, $\sin x$, $\cos x$, $\ln(1+x)$, or $1/(1-x)$).

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the coefficient of $x^{3}$ in the Maclaurin series of $f(x) = e^x$. Express your answer as a fraction in the form a/b, or an integer. | $1/6$ |
    """
    kind = random.choice(["exp", "sin", "cos", "ln1p", "geometric"])
    if kind == "exp":
        k = random.randint(0, 5)
        coeff = Fraction(1, math.factorial(k))
        func = "e^x"
    elif kind == "sin":
        k = random.randint(1, 7)
        coeff = (Fraction(0) if k % 2 == 0
                 else Fraction((-1) ** ((k - 1) // 2), math.factorial(k)))
        func = "\\sin(x)"
    elif kind == "cos":
        k = random.randint(0, 6)
        coeff = (Fraction(0) if k % 2 == 1
                 else Fraction((-1) ** (k // 2), math.factorial(k)))
        func = "\\cos(x)"
    elif kind == "ln1p":
        k = random.randint(1, 5)
        coeff = Fraction((-1) ** (k + 1), k)
        func = "\\ln(1+x)"
    else:  # 1/(1-x) = sum x^k
        k = random.randint(0, 5)
        coeff = Fraction(1)
        func = "\\frac{1}{1-x}"
    problem = (
        f"Find the coefficient of $x^{{{k}}}$ in the Maclaurin series of "
        f"$f(x) = {func}$. {_FRACTION_HINT}"
    )
    return problem, f"${_fmt_frac(coeff)}$"
