"""Solveki-local calculus generators.

Every generator here targets a computable gap in the Georgia "Calculus"
curriculum. Each takes no required arguments, returns a ``(problem, solution,
steps)`` triple (LaTeX strings plus a step-by-step explanation), and produces a
clean answer (integer, fraction, short float, or short polynomial string).
Names are prefixed ``calc_`` so they are easy to scope.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._variants import with_variants
from ._format import num as _num
from ._steps import Steps, paren, tex_frac
from .algebra import _format_polynomial

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."
_ROUNDED = "Rounded to the nearest thousandth, the answer is"


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


# --- LaTeX helpers for the step-by-step explanations ---

def _ftex(value):
    """An exact value (int or Fraction) in LaTeX: ``3`` or ``-\\frac{1}{2}``."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return tex_frac(fr.numerator, fr.denominator)


def _join(pieces):
    """Join signed LaTeX terms: ``["x^{2}", "-3x", "5"]`` -> ``x^{2} - 3x + 5``."""
    if not pieces:
        return "0"
    out = pieces[0]
    for piece in pieces[1:]:
        out += f" - {piece[1:]}" if piece.startswith("-") else f" + {piece}"
    return out


def _coef(coeff, body):
    """``coeff`` times ``body`` in LaTeX, dropping a unit coefficient."""
    if not body:
        return _ftex(coeff)
    if coeff == 1:
        return body
    if coeff == -1:
        return f"-{body}"
    return f"{_ftex(coeff)}{body}"


def _xpow(exp, var="x"):
    return "" if exp == 0 else var if exp == 1 else f"{var}^{{{exp}}}"


def _poly_tex(poly, var="x"):
    """A poly dict (int or Fraction coefficients) as LaTeX."""
    return _join([_coef(c, _xpow(e, var))
                  for e, c in sorted(poly.items(), reverse=True) if c != 0])


def _poly_sub(poly, value):
    """``poly`` with ``x`` replaced by ``(value)``: ``3(2)^{2} - (2) + 1``."""
    pieces = []
    for e, c in sorted(poly.items(), reverse=True):
        if c == 0:
            continue
        body = "" if e == 0 else f"({value})" + ("" if e == 1 else f"^{{{e}}}")
        pieces.append(_coef(c, body))
    return _join(pieces)


def _at(poly, x):
    """``poly`` evaluated at ``x``, showing the substitution: ``3(2) + 1 = 7``."""
    sub, val = _poly_sub(poly, _ftex(x)), _ftex(_poly_eval(poly, x))
    return val if sub == val else f"{sub} = {val}"


def _divide(n, d):
    """``\\frac{n}{d}``, followed by its reduced value when that differs."""
    if d < 0:
        n, d = -n, -d
    if d == 1:
        return str(n)
    fr = Fraction(n, d)
    shown = rf"\frac{{{n}}}{{{d}}}"
    if (fr.numerator, fr.denominator) == (n, d):
        return shown if n >= 0 else _ftex(fr)
    return f"{shown} = {_ftex(fr)}"


def _lin_factor(root):
    """The factor ``(x - root)`` in LaTeX (just ``x`` when the root is 0)."""
    return "x" if root == 0 else f"({_poly_tex({1: 1, 0: -root})})"


def _rel(value):
    """``=`` if ``value`` is exact at three decimals, else ``\\approx``."""
    return "=" if abs(value - round(value, 3)) < 1e-9 else r"\approx"


def _power_rule_terms(poly):
    """Each term's power-rule derivative, unsimplified: ``3 \\cdot 2x^{2}``."""
    return " + ".join(
        rf"{e} \cdot {paren(c)}{_xpow(e - 1)}"
        for e, c in sorted(poly.items(), reverse=True) if e >= 1 and c != 0
    )


_POWER_RULE = r"\frac{d}{dx}\left[x^n\right] = nx^{n-1}"


def _ftc_steps(s, poly, a, b):
    """Antiderivative, evaluation and subtraction for ``\\int_a^b poly``.

    Adds three steps and returns the exact value of the integral.
    """
    anti = {e + 1: Fraction(c, e + 1) for e, c in poly.items() if c != 0}
    fa, fb = _poly_eval(anti, a), _poly_eval(anti, b)
    s.step(
        r"Integrate term by term with the power rule "
        r"$\int x^n \, dx = \frac{x^{n+1}}{n+1}$.",
        rf"F(x) = {_poly_tex(anti)}",
    )
    s.step(
        "By the Fundamental Theorem of Calculus, evaluate $F$ at both bounds.",
        rf"F({b}) = {_ftex(fb)}, \quad F({a}) = {_ftex(fa)}",
    )
    s.step(
        "Subtract.",
        rf"\int_{{{a}}}^{{{b}}} {_poly_tex(poly)} \, dx = F({b}) - F({a}) "
        rf"= {_ftex(fb)} - {paren(_ftex(fa))} = {_ftex(fb - fa)}",
    )
    return fb - fa


# --------------------------------- limits ---------------------------------

@register
@with_variants
def calc_limit_rational(min_c=-4, max_c=4):
    r"""Limit of a Rational Function at a Point

    Either a removable discontinuity (shared linear factor cancels) or a
    direct substitution. Answer is an exact, reduced value.
    """
    c = random.randint(min_c, max_c)
    s = Steps()
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
        fx = _lin_factor(c)
        s.step(
            rf"Substituting $x = {c}$ makes both the numerator and the "
            rf"denominator $0$, so the limit has the form $\frac{{0}}{{0}}$. "
            rf"Factor both.",
            rf"\frac{{{_poly_tex(num)}}}{{{_poly_tex(den)}}} = "
            rf"\frac{{{fx}({_poly_tex(l1)})}}{{{fx}({_poly_tex(l2)})}}",
        )
        s.step(
            f"Cancel the common factor ${fx}$ (allowed because $x \\ne {c}$ "
            f"inside the limit).",
            rf"\lim_{{x \to {c}}} \frac{{{_poly_tex(l1)}}}{{{_poly_tex(l2)}}}",
        )
        s.step(
            f"Now substitute $x = {c}$.",
            rf"\frac{{{_poly_sub(l1, c)}}}{{{_poly_sub(l2, c)}}} = "
            rf"{_divide(_poly_eval(l1, c), _poly_eval(l2, c))}",
        )
    else:
        # Direct substitution: den(c) != 0.
        num = _rand_poly(random.randint(1, 2))
        while True:
            den = _rand_poly(random.randint(1, 2))
            if _poly_eval(den, c) != 0:
                break
        ans = Fraction(_poly_eval(num, c), _poly_eval(den, c))
        s.step(
            f"Substitute $x = {c}$ into the denominator. It isn't $0$, so the "
            f"limit can be found by direct substitution.",
            _at(den, c),
        )
        s.step(f"Substitute $x = {c}$ into the numerator.", _at(num, c))
        s.step(
            "Divide the numerator by the denominator.",
            rf"\lim_{{x \to {c}}} \frac{{{_poly_tex(num)}}}{{{_poly_tex(den)}}} = "
            rf"{_divide(_poly_eval(num, c), _poly_eval(den, c))}",
        )

    problem = (
        f"Evaluate $\\lim_{{x \\to {c}}} "
        f"\\frac{{{_poly_str(num)}}}{{{_poly_str(den)}}}$. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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
    s = Steps()
    s.step(
        rf"Substituting $x = {c}$ gives $\sqrt{{{c}}} - {b} = 0$ and "
        rf"${c} - {c} = 0$, so the limit has the form $\frac{{0}}{{0}}$.",
    )
    conj = rf"\sqrt{{x}}+{b}"
    if random.random() < 0.5:
        # (sqrt(x) - b)/(x - b^2) -> 1/(sqrt(x) + b) -> 1/(2b)
        num, den = f"\\sqrt{{x}}-{b}", f"x-{c}"
        ans = Fraction(1, 2 * b)
        s.step(
            f"Multiply the numerator and denominator by the conjugate ${conj}$. "
            f"The numerator becomes a difference of squares.",
            rf"\frac{{({num})({conj})}}{{({den})({conj})}} = "
            rf"\frac{{x-{c}}}{{(x-{c})({conj})}}",
        )
        s.step(
            f"Cancel the common factor $x-{c}$.",
            rf"\lim_{{x \to {c}}} \frac{{1}}{{{conj}}}",
        )
        s.step(
            f"Now substitute $x = {c}$.",
            rf"\frac{{1}}{{\sqrt{{{c}}}+{b}}} = \frac{{1}}{{{b}+{b}}} = {_ftex(ans)}",
        )
    else:
        # (x - b^2)/(sqrt(x) - b) -> sqrt(x) + b -> 2b
        num, den = f"x-{c}", f"\\sqrt{{x}}-{b}"
        ans = Fraction(2 * b)
        s.step(
            f"Multiply the numerator and denominator by the conjugate ${conj}$. "
            f"The denominator becomes a difference of squares.",
            rf"\frac{{({num})({conj})}}{{({den})({conj})}} = "
            rf"\frac{{(x-{c})({conj})}}{{x-{c}}}",
        )
        s.step(
            f"Cancel the common factor $x-{c}$.",
            rf"\lim_{{x \to {c}}} \left({conj}\right)",
        )
        s.step(
            f"Now substitute $x = {c}$.",
            rf"\sqrt{{{c}}}+{b} = {b}+{b} = {_ftex(ans)}",
        )
    problem = (
        f"Evaluate $\\lim_{{x \\to {c}}} \\frac{{{num}}}{{{den}}}$ by "
        f"multiplying by the conjugate. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    s.answer(solution)
    return problem, solution, s.done()


# ------------------------------ derivatives -------------------------------

@register
@with_variants
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

    s = Steps()
    s.formula("The power rule", _POWER_RULE)
    drop = " The constant term's derivative is $0$." if poly.get(0) else ""
    s.step(
        f"Apply it to each term: bring the exponent down and lower it by one.{drop}",
        rf"f'(x) = {_power_rule_terms(poly)}",
    )
    s.step("Multiply out the coefficients.", rf"f'(x) = {_poly_tex(deriv)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    d1, d2 = _poly_deriv(f1), _poly_deriv(f2)
    u, v = _poly_eval(f1, c), _poly_eval(f2, c)
    up, vp = _poly_eval(d1, c), _poly_eval(d2, c)
    s = Steps()
    s.formula("The product rule", r"(uv)' = u'v + uv'")
    s.step(
        f"Let $u = {_poly_tex(f1)}$ and $v = {_poly_tex(f2)}$. "
        f"Differentiate each with the power rule.",
        rf"u' = {_poly_tex(d1)}, \quad v' = {_poly_tex(d2)}",
    )
    s.step(
        f"Evaluate all four at $x = {c}$.",
        rf"u({c}) = {u}, \quad u'({c}) = {up}, \quad "
        rf"v({c}) = {v}, \quad v'({c}) = {vp}",
    )
    s.substitute(
        rf"f'({c}) = ({up})({v}) + ({u})({vp}) = {ans}",
        text="Substitute into the product rule.",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    u, v = _poly_eval(num, c), _poly_eval(den, c)
    up, vp = _poly_eval(numd, c), _poly_eval(dend, c)
    s = Steps()
    s.formula("The quotient rule", r"\left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^2}")
    s.step(
        f"Let $u = {_poly_tex(num)}$ and $v = {_poly_tex(den)}$, "
        f"so $u' = {up}$ and $v' = {vp}$.",
    )
    s.step(f"Evaluate $u$ and $v$ at $x = {c}$.", rf"u({c}) = {u}, \quad v({c}) = {v}")
    s.substitute(
        rf"f'({c}) = \frac{{({up})({v}) - ({u})({vp})}}{{({v})^2}} = {_divide(top, bottom)}",
        text="Substitute into the quotient rule and simplify.",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    pw = "" if n == 2 else f"^{{{n - 1}}}"
    g = _poly_eval(inner, c)
    s = Steps()
    s.formula("The chain rule", r"\frac{d}{dx}\left[g(x)^n\right] = n\,g(x)^{n-1} \cdot g'(x)")
    s.step(
        f"The inner function is $g(x) = {_poly_tex(inner)}$, so $g'(x) = {a}$.",
        rf"f'(x) = {n}({_poly_tex(inner)}){pw} \cdot {paren(a)}",
    )
    s.step(f"Evaluate the inner function at $x = {c}$.", f"g({c}) = {_at(inner, c)}")
    s.substitute(
        rf"f'({c}) = {n}({g}){pw} \cdot {paren(a)} = {ans}",
        text="Substitute and simplify.",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def calc_derivative_exp_log_trig():
    r"""Derivative of an Exponential, Logarithmic, or Trig Function

    One of $a e^{kx}$, $a \ln(x)$, $a \sin(kx)$, or $a \cos(kx)$, evaluated
    at a point and reported to 3 decimal places.
    """
    kind = random.choice(["exp", "ln", "sin", "cos"])
    a = random.choice([i for i in range(-6, 7) if i != 0])
    s = Steps()
    if kind == "ln":
        c = random.randint(1, 6)
        expr = f"{a} \\ln(x)"
        value = a / c
        s.formula("The derivative of the natural log", r"\frac{d}{dx}\ln(x) = \frac{1}{x}")
        s.step("Multiply by the constant.", rf"f'(x) = \frac{{{a}}}{{x}}")
        tail = "" if Fraction(a, c).denominator == 1 else f" {_rel(value)} {_num(value)}"
        s.substitute(
            rf"f'({c}) = {_divide(a, c)}{tail}",
            text=f"Substitute $x = {c}$.",
        )
    else:
        k = random.choice([i for i in range(-3, 4) if i != 0])
        c = random.randint(-3, 3)
        kx = _coef(k, "x")
        if kind == "exp":
            expr = f"{a} e^{{{k} x}}"
            value = a * k * math.exp(k * c)
            s.formula("By the chain rule, the derivative of $e^{u}$", r"\frac{d}{dx}e^{u} = e^{u} \cdot u'")
            s.step(
                f"Here $u = {kx}$, so $u' = {k}$.",
                rf"f'(x) = {a} \cdot {paren(k)} \cdot e^{{{kx}}} = {_coef(a * k, f'e^{{{kx}}}')}",
            )
            s.substitute(
                rf"f'({c}) = {_coef(a * k, f'e^{{{k * c}}}')} {_rel(value)} {_num(value)}",
                text=f"Substitute $x = {c}$.",
            )
        elif kind == "sin":
            expr = f"{a} \\sin({k} x)"
            value = a * k * math.cos(k * c)
            s.formula("By the chain rule, the derivative of $\\sin(u)$", r"\frac{d}{dx}\sin(u) = \cos(u) \cdot u'")
            s.step(
                f"Here $u = {kx}$, so $u' = {k}$.",
                rf"f'(x) = {a} \cdot {paren(k)} \cdot \cos({kx}) = {_coef(a * k, rf'\cos({kx})')}",
            )
            s.substitute(
                rf"f'({c}) = {_coef(a * k, rf'\cos({k * c})')} {_rel(value)} {_num(value)}",
                text=f"Substitute $x = {c}$ (in radians).",
            )
        else:  # cos
            expr = f"{a} \\cos({k} x)"
            value = -a * k * math.sin(k * c)
            s.formula("By the chain rule, the derivative of $\\cos(u)$", r"\frac{d}{dx}\cos(u) = -\sin(u) \cdot u'")
            s.step(
                f"Here $u = {kx}$, so $u' = {k}$.",
                rf"f'(x) = -{paren(a)} \cdot {paren(k)} \cdot \sin({kx}) = {_coef(-a * k, rf'\sin({kx})')}",
            )
            s.substitute(
                rf"f'({c}) = {_coef(-a * k, rf'\sin({k * c})')} {_rel(value)} {_num(value)}",
                text=f"Substitute $x = {c}$ (in radians).",
            )
    problem = (
        f"Find the derivative of $f(x) = {expr}$ at $x = {c}$. "
        f"Round your answer to the nearest thousandth."
    )
    solution = f"${_num(value)}$"
    s.answer(solution, lead="The answer is" if _rel(value) == "=" else _ROUNDED)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    lines = [
        rf"Differentiate once with the power rule ${_POWER_RULE}$.",
        "Differentiate again.",
        "Differentiate a third time.",
    ]
    cur = poly
    for i in range(order):
        cur = _poly_deriv(cur)
        s.step(lines[i], f"f{chr(39) * (i + 1)}(x) = {_poly_tex(cur)}")
    name = f"f{chr(39) * order}"
    if any(e > 0 and coeff for e, coeff in d.items()):
        s.step(f"Substitute $x = {c}$.", f"{name}({c}) = {_at(d, c)}")
    else:
        s.step(f"This derivative is a constant, so its value at $x = {c}$ is ${ans}$.")
    s.answer(solution)
    return problem, solution, s.done()


# ------------------------- applications of derivatives --------------------

@register
@with_variants
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

    y0 = _poly_eval(poly, c)
    s = Steps()
    s.step(f"Find the point of tangency by evaluating $f$ at $x = {c}$.", f"f({c}) = {_at(poly, c)}")
    s.step(
        "Differentiate with the power rule to get the slope function.",
        f"f'(x) = {_poly_tex(_poly_deriv(poly))}",
    )
    s.step(f"The slope is $f'({c})$.", f"m = f'({c}) = {_at(_poly_deriv(poly), c)}")
    slope_side = "0" if m == 0 else _coef(m, f"(x - {paren(c)})")
    s.step(
        f"Use point-slope form $y - y_1 = m(x - x_1)$ with the point $({c}, {y0})$.",
        f"y - {paren(y0)} = {slope_side}",
    )
    s.answer(solution, lead="Solve for $y$. The tangent line is")
    return problem, solution, s.done()


@register
@with_variants
def calc_extrema(min_root=-5, max_root=5):
    r"""Critical Points via the First Derivative

    Critical x-values of a quadratic or cubic, sorted, as ``x = a, b``.
    """
    s = Steps()
    if random.random() < 0.5:
        # Quadratic with an integer critical point.
        a = random.choice([i for i in range(-4, 5) if i != 0])
        r = random.randint(min_root, max_root)
        poly = {2: a, 1: -2 * a * r, 0: random.randint(-5, 5)}
        roots = [r]
        deriv = _poly_deriv(poly)
        s.step(
            "Critical points are where $f'(x) = 0$. Differentiate with the power rule.",
            f"f'(x) = {_poly_tex(deriv)}",
        )
        middle = "" if r == 0 else rf" \\ {_coef(2 * a, 'x')} &= {2 * a * r}"
        s.step(
            "Set the derivative equal to $0$ and solve.",
            rf"\begin{{aligned}} {_poly_tex(deriv)} &= 0{middle} \\ x &= {r} \end{{aligned}}",
        )
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
        deriv = _poly_deriv(poly)
        s.step(
            "Critical points are where $f'(x) = 0$. Differentiate with the power rule.",
            f"f'(x) = {_poly_tex(deriv)}",
        )
        monic = _poly_tex({2: 1, 1: -(r1 + r2), 0: r1 * r2})
        factors = "".join(sorted((_lin_factor(r1), _lin_factor(r2)), key=lambda f: f != "x"))
        s.step(
            f"Set it equal to $0$, factor out ${3 * a}$, and factor the quadratic.",
            rf"{_poly_tex(deriv)} = {3 * a}({monic}) = {3 * a}{factors} = 0",
        )
        s.step(
            "Set each factor equal to $0$.",
            rf"x = {r1} \quad \text{{or}} \quad x = {r2}",
        )
    xs = ", ".join(str(x) for x in sorted(roots))
    problem = (
        f"Find the critical points of $f(x) = {_poly_str(poly)}$. "
        f"Give the x-value(s) as integers or fractions a/b, comma-separated "
        f"and in increasing order."
    )
    solution = f"$x = {xs}$"
    s.answer(solution, lead="In increasing order, the critical points are")
    return problem, solution, s.done()


def _second_derivative_steps(s, poly):
    """Differentiate a cubic twice, then solve f''(x) = 0. Returns f''."""
    d1 = _poly_deriv(poly)
    d2 = _poly_deriv(d1)
    s.step(
        "Differentiate twice with the power rule.",
        rf"f'(x) = {_poly_tex(d1)}, \quad f''(x) = {_poly_tex(d2)}",
    )
    root = (f"x = 0" if not d2.get(0)
            else f"x = {_divide(-d2[0], d2[1])}")
    s.step(
        "Set the second derivative equal to $0$ and solve.",
        rf"{_poly_tex(d2)} = 0 \implies {root}",
    )
    return d2


@register
@with_variants
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

    s = Steps()
    s.step("An inflection point is where $f''(x) = 0$ and $f''$ changes sign.")
    _second_derivative_steps(s, poly)
    s.answer(
        solution,
        lead=f"Since $f''$ is linear with nonzero slope ${6 * a}$, it changes sign there. The answer is",
    )
    return problem, solution, s.done()


# -------------------------------- integrals -------------------------------

@register
@with_variants
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

    s = Steps()
    _ftc_steps(s, poly, a, b)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    raw = _join([
        _coef(coeff, "x") if e == 0
        else ("-" if coeff < 0 else "") + rf"\frac{{{abs(coeff)}}}{{{e + 1}}}{_xpow(e + 1)}"
        for e, coeff in sorted(poly.items(), reverse=True) if coeff != 0
    ])
    s = Steps()
    s.formula("The power rule for integrals", r"\int x^n \, dx = \frac{x^{n+1}}{n+1} + C")
    s.step(
        "Integrate term by term: raise each exponent by one and divide by the new exponent.",
        raw,
    )
    s.step(
        "Simplify each coefficient and add the constant of integration $C$.",
        f"{_poly_tex(anti)} + C",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    up, uq = a * p + b, a * q + b
    k = tex_frac(1, a) if a not in (1, -1) else ("" if a == 1 else "-")
    s = Steps()
    s.step(
        f"Let $u = {_poly_tex({1: a, 0: b})}$. Then $du = {_coef(a, 'dx')}$, so "
        f"$dx = {_coef(Fraction(1, a), 'du')}$.",
    )
    s.step(
        "Change the bounds to $u$-values.",
        rf"x = {p} \implies u = {up}, \quad x = {q} \implies u = {uq}",
    )
    s.step(
        "Rewrite the integral in terms of $u$ and integrate with the power rule.",
        rf"{k}\int_{{{up}}}^{{{uq}}} u^{{{n}}} \, du = "
        rf"{k}\left[\frac{{u^{{{n + 1}}}}}{{{n + 1}}}\right]_{{{up}}}^{{{uq}}}",
    )
    s.step(
        "Evaluate at the bounds and simplify.",
        rf"\frac{{({uq})^{{{n + 1}}} - ({up})^{{{n + 1}}}}}{{{a * (n + 1)}}} = "
        rf"\frac{{{upper} - {paren(lower)}}}{{{a * (n + 1)}}} = {_ftex(ans)}",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def calc_area_between_curves():
    r"""Area Between Two Curves

    Two polynomials that meet at the endpoints ``a`` and ``b`` (so one stays
    above the other on the interval). Exact area.
    """
    a = random.randint(-3, 2)
    b = random.randint(a + 1, 4)
    g = _rand_poly(random.randint(0, 2), lo=-3, hi=3)
    c = random.choice([-3, -2, -1])        # C < 0 -> f - g >= 0 on [a, b]
    diff = _poly_mul({0: c}, _poly_mul({1: 1, 0: -a}, {1: 1, 0: -b}))
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

    factors = "".join(sorted((_lin_factor(a), _lin_factor(b)), key=lambda t: t != "x"))
    s = Steps()
    s.formula(
        "The area between two curves, with $f$ on top",
        rf"A = \int_{{{a}}}^{{{b}}} \left(f(x) - g(x)\right) dx",
    )
    s.step(
        f"Subtract the functions. The factored form is $\\ge 0$ on $[{a}, {b}]$ "
        f"(the constant ${c}$ is negative and the two factors have opposite "
        f"signs between ${a}$ and ${b}$), so $f$ is on top.",
        rf"f(x) - g(x) = {_poly_tex(diff)} = {_coef(c, factors)}",
    )
    _ftc_steps(s, diff, a, b)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    s = Steps()
    s.formula(
        f"The average value of $f$ on $[{a}, {b}]$",
        rf"f_{{\text{{avg}}}} = \frac{{1}}{{{b} - {paren(a)}}} \int_{{{a}}}^{{{b}}} f(x) \, dx",
    )
    _ftc_steps(s, poly, a, b)
    s.step(
        f"Divide by the length of the interval, ${b - a}$.",
        rf"f_{{\text{{avg}}}} = \frac{{1}}{{{b - a}}} \cdot {paren(_ftex(integral))} = {_ftex(ans)}",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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

    xs = [a + i * dx for i in indices]
    s = Steps()
    s.step(
        "Find the width of each rectangle.",
        rf"\Delta x = \frac{{{b} - {paren(a)}}}{{{n}}} = {_ftex(dx)}",
    )
    s.step(
        f"A {side} sum uses the {side} endpoint of each subinterval.",
        "x = " + ", ".join(_ftex(x) for x in xs),
    )
    s.step(
        "Evaluate $f$ at each point and add.",
        _join([_ftex(_poly_eval(poly, x)) for x in xs]) + f" = {_ftex(total)}",
    )
    s.step(
        r"Multiply the sum by $\Delta x$.",
        rf"{_ftex(dx)} \cdot {paren(_ftex(total))} = {_ftex(ans)}",
    )
    s.answer(solution)
    return problem, solution, s.done()


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
@with_variants
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

    def combo(cx, x, cy, y):
        return _join([_coef(k, v) for k, v in ((cx, x), (cy, y)) if k])

    dydx = r"\frac{dy}{dx}"
    rules = r"the chain rule gives $\frac{d}{dx}y^2 = 2y\frac{dy}{dx}$"
    if B:
        rules += r", and the product rule gives $\frac{d}{dx}(xy) = y + x\frac{dy}{dx}$"
    terms = [_coef(2 * A, "x")]
    if B:
        terms.append(_coef(B, rf"\left(y + x{dydx}\right)"))
    terms.append(_coef(2 * C, f"y{dydx}"))
    top = 2 * A * x0 + B * y0
    s = Steps()
    s.step(
        f"Differentiate both sides with respect to $x$, treating $y$ as a "
        f"function of $x$: {rules}.",
        f"{_join(terms)} = 0",
    )
    s.step(
        r"Collect the $\frac{dy}{dx}$ terms on one side and solve.",
        rf"\left({combo(B, 'x', 2 * C, 'y')}\right){dydx} = -\left({combo(2 * A, 'x', B, 'y')}\right) "
        rf"\implies {dydx} = -\frac{{{combo(2 * A, 'x', B, 'y')}}}{{{combo(B, 'x', 2 * C, 'y')}}}",
    )
    s.substitute(
        rf"{dydx} = -\frac{{{combo(2 * A, f'({x0})', B, f'({y0})')}}}"
        rf"{{{combo(B, f'({x0})', 2 * C, f'({y0})')}}} = {_divide(-top, denom)}",
        text=f"Substitute the point $x = {x0}$, $y = {y0}$.",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def calc_particle_motion():
    r"""Particle Motion

    A particle has polynomial position $s(t)$. Find its velocity or
    acceleration at a time, or the time when the velocity is zero.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A particle moves along a line with position $s(t) = t^3-2t^2+t$. Find its velocity at $t = 2$. | $5$ |
    """
    ask = random.choice(["velocity", "acceleration", "rest"])
    st = Steps()
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
        v = _poly_tex(_poly_deriv(s), "t")
        st.step(
            "Velocity is the derivative of position. Differentiate with the power rule.",
            f"v(t) = s'(t) = {v}",
        )
        st.step(
            "Set the velocity equal to $0$ and solve for $t$.",
            rf"{v} = 0 \implies t = {_divide(-B, 2 * A)}",
        )
        solution = f"${_fmt_frac(root)}$"
        st.answer(solution)
        return problem, solution, st.done()
    s = _rand_poly(random.randint(2, 3))
    t = random.randint(-3, 4)
    body = _poly_str(s).replace("x", "t")
    v = _poly_deriv(s)
    st.step(
        "Velocity is the derivative of position. Differentiate with the power rule.",
        f"v(t) = s'(t) = {_poly_tex(v, 't')}",
    )
    if ask == "velocity":
        val = _poly_eval(_poly_deriv(s), t)
        st.step(f"Substitute $t = {t}$.", f"v({t}) = {_at(v, t)}")
    else:
        val = _poly_eval(_poly_deriv(_poly_deriv(s)), t)
        acc = _poly_deriv(v)
        st.step(
            "Acceleration is the derivative of velocity. Differentiate again.",
            f"a(t) = v'(t) = {_poly_tex(acc, 't')}",
        )
        if acc.get(1):
            st.step(f"Substitute $t = {t}$.", f"a({t}) = {_at(acc, t)}")
        else:
            st.step(f"The acceleration is constant, so at $t = {t}$:", f"a({t}) = {val}")
    problem = (
        f"A particle moves along a line with position $s(t) = {body}$. "
        f"Find its {ask} at $t = {t}$."
    )
    solution = f"${val}$"
    st.answer(solution)
    return problem, solution, st.done()


_KPI_HINT = "Your answer has the form k*pi; give the value of k as a fraction a/b or an integer."


@register
@with_variants
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
    s = Steps()
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
        s.formula(
            "The disk method formula",
            rf"V = \pi \int_{{{a}}}^{{{b}}} \left[f(x)\right]^2 dx",
        )
        s.step(
            "Square the radius $f(x)$.",
            rf"\left[f(x)\right]^2 = ({_poly_tex(f)})^2 = {_poly_tex(fsq)}",
        )
        _ftc_steps(s, fsq, a, b)
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
        s.formula(
            f"With outer radius $R(x) = {_poly_tex(R)}$ and inner radius "
            f"$r(x) = {p}$, the washer method formula",
            rf"V = \pi \int_{{{a}}}^{{{b}}} \left(R(x)^2 - r(x)^2\right) dx",
        )
        s.step(
            "Square both radii and subtract.",
            rf"R(x)^2 - r(x)^2 = ({_poly_tex(R)})^2 - {p}^2 = {_poly_tex(diff)}",
        )
        _ftc_steps(s, diff, a, b)
    solution = f"${_fmt_frac(k)}$"
    s.answer(solution, lead=rf"So $V = {_coef(k, r'\pi')}$, and $k$ is")
    return problem, solution, s.done()


@register
@with_variants
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
    lim = r"\lim_{x \to 0}"
    s = Steps()
    if kind == "cos":
        c = random.randint(1, 4)
        num = f"1-\\cos({_cx(a)})"
        den = f"x^2" if c == 1 else f"{c} x^2"
        ans = Fraction(a * a, 2 * c)
        first = rf"\frac{{{_coef(a, rf'\sin({_cx(a)})')}}}{{{_coef(2 * c, 'x')}}}"
        second = rf"\frac{{{_coef(a * a, rf'\cos({_cx(a)})')}}}{{{2 * c}}}"
        last = rf"\frac{{{_coef(a * a, r'\cos(0)')}}}{{{2 * c}}} = {_divide(a * a, 2 * c)}"
    else:
        b = random.choice([i for i in range(-5, 6) if i != 0])
        den = _cx(b)
        if kind == "sin":
            num = f"\\sin({_cx(a)})"
            top, at0 = rf"\cos({_cx(a)})", r"\cos(0)"
        elif kind == "tan":
            num = f"\\tan({_cx(a)})"
            top, at0 = rf"\sec^2({_cx(a)})", r"\sec^2(0)"
        else:  # exp
            num = f"e^{{{_cx(a)}}}-1"
            top, at0 = f"e^{{{_cx(a)}}}", "e^{0}"
        ans = Fraction(a, b)
        first = rf"\frac{{{_coef(a, top)}}}{{{b}}}"
        last = rf"\frac{{{_coef(a, at0)}}}{{{b}}} = {_divide(a, b)}"
    s.step(
        r"Substituting $x = 0$ gives $\frac{0}{0}$, so use L'Hopital's Rule: "
        r"$\lim \frac{f(x)}{g(x)} = \lim \frac{f'(x)}{g'(x)}$.",
    )
    s.step(
        "Differentiate the numerator and the denominator separately "
        "(the chain rule handles the inner multiple of $x$).",
        rf"{lim} \frac{{{num}}}{{{den}}} = {lim} {first}",
    )
    if kind == "cos":
        s.step(
            r"This is still $\frac{0}{0}$ at $x = 0$, so apply L'Hopital's Rule again.",
            rf"{lim} {first} = {lim} {second}",
        )
    s.step("Now substitute $x = 0$.", last)
    problem = (
        f"Use L'Hopital's Rule to evaluate "
        f"$\\lim_{{x \\to 0}} \\frac{{{num}}}{{{den}}}$. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(ans)}$"
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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
    solution = f"${ans}$"

    fp = _poly_eval(poly, p)
    in_h = {2: A, 1: 2 * A * p + B, 0: fp}      # f(p + h) as a poly in h
    lin = 2 * A * p + B
    s = Steps()
    s.formula(
        "The limit definition of the derivative",
        rf"f'({p}) = \lim_{{h \to 0}} \frac{{f({p}+h) - f({p})}}{{h}}",
    )
    s.step(
        f"Expand $f({p}+h)$.",
        rf"f({p}+h) = {_poly_sub(poly, f'{p}+h')} = {_poly_tex(in_h, 'h')}",
    )
    s.step(
        f"Subtract $f({p}) = {fp}$. The constant terms cancel.",
        rf"f({p}+h) - f({p}) = {_poly_tex({2: A, 1: lin}, 'h')}",
    )
    s.step(
        "Divide by $h$, then let $h \\to 0$.",
        rf"f'({p}) = \lim_{{h \to 0}} \left({_poly_tex({1: A, 0: lin}, 'h')}\right) = {ans}",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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
    solution = f"${_num(value)}$"

    def times(t):
        return "" if t == 1 else paren(t)

    def bracket(t):
        """The antiderivative evaluated at ``t``, unsimplified LaTeX."""
        if kind == "xex":
            return rf"({t - 1})e^{{{t}}}"
        if kind == "xsin":
            return rf"\left[\sin({t}) - {times(t)}\cos({t})\right]"
        if kind == "xcos":
            return rf"\left[\cos({t}) + {times(t)}\sin({t})\right]"
        return (rf"\left[{_coef(Fraction(t * t, 2), rf'\ln({t})')} - "
                rf"{_ftex(Fraction(t * t, 4))}\right]")

    parts = {
        "xex": (r"u = x, \quad dv = e^{x}\,dx \implies du = dx, \quad v = e^{x}",
                r"x e^{x} - \int e^{x}\,dx = x e^{x} - e^{x} = (x-1)e^{x}"),
        "xsin": (r"u = x, \quad dv = \sin(x)\,dx \implies du = dx, \quad v = -\cos(x)",
                 r"-x\cos(x) + \int \cos(x)\,dx = \sin(x) - x\cos(x)"),
        "xcos": (r"u = x, \quad dv = \cos(x)\,dx \implies du = dx, \quad v = \sin(x)",
                 r"x\sin(x) - \int \sin(x)\,dx = \cos(x) + x\sin(x)"),
        "xln": (r"u = \ln(x), \quad dv = x\,dx \implies du = \frac{1}{x}\,dx, \quad v = \frac{x^2}{2}",
                r"\frac{x^2}{2}\ln(x) - \int \frac{x}{2}\,dx = \frac{x^2}{2}\ln(x) - \frac{x^2}{4}"),
    }
    choice, anti = parts[kind]
    s = Steps()
    s.formula("Integration by parts", r"\int u \, dv = uv - \int v \, du")
    s.step(
        "Choose $u$ to be the factor that gets simpler when differentiated." if kind != "xln"
        else "Choose $u = \\ln(x)$, since its derivative is simpler and it is hard to integrate directly.",
        choice,
    )
    s.step("Apply the formula to find an antiderivative.", rf"\int {integrand} \, dx = {anti}")
    trig = " (in radians)" if kind in ("xsin", "xcos") else ""
    s.step(
        f"Evaluate from ${p}$ to ${q}${trig}.",
        f"{bracket(q)} - {bracket(p)} {_rel(value)} {_num(value)}",
    )
    s.answer(solution, lead="The answer is" if _rel(value) == "=" else _ROUNDED)
    return problem, solution, s.done()


# ---------------------- calculus (chunk 2 additions) ----------------------

_TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25),
            (20, 21, 29), (9, 40, 41), (6, 8, 10)]


@register
@with_variants
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
    s = Steps()
    if kind == "circle":
        r = random.randint(2, 8)
        dr = random.randint(1, 5)
        k = 2 * r * dr
        problem = (
            f"A circle's radius grows at ${dr}$ units per second. Find the "
            f"rate of change of its area $dA/dt$ when the radius is ${r}$. "
            f"{_KPI_HINT}"
        )
        solution = f"${_fmt_frac(k)}$"
        s.formula("The area of a circle", r"A = \pi r^2")
        s.step(
            "Differentiate both sides with respect to $t$ (chain rule).",
            r"\frac{dA}{dt} = 2\pi r \frac{dr}{dt}",
        )
        s.substitute(
            rf"\frac{{dA}}{{dt}} = 2\pi({r})({dr}) = {k}\pi",
            text=f"Substitute $r = {r}$ and $\\frac{{dr}}{{dt}} = {dr}$.",
        )
        s.answer(solution, lead=rf"So $\frac{{dA}}{{dt}} = {k}\pi$, and $k$ is")
        return problem, solution, s.done()
    if kind == "sphere":
        r = random.randint(2, 6)
        dr = random.randint(1, 4)
        k = 4 * r * r * dr
        problem = (
            f"A sphere's radius grows at ${dr}$ units per second. Find the "
            f"rate of change of its volume $dV/dt$ when the radius is ${r}$. "
            f"{_KPI_HINT}"
        )
        solution = f"${_fmt_frac(k)}$"
        s.formula("The volume of a sphere", r"V = \frac{4}{3}\pi r^3")
        s.step(
            "Differentiate both sides with respect to $t$ (chain rule).",
            r"\frac{dV}{dt} = 4\pi r^2 \frac{dr}{dt}",
        )
        s.substitute(
            rf"\frac{{dV}}{{dt}} = 4\pi({r})^2({dr}) = {k}\pi",
            text=f"Substitute $r = {r}$ and $\\frac{{dr}}{{dt}} = {dr}$.",
        )
        s.answer(solution, lead=rf"So $\frac{{dV}}{{dt}} = {k}\pi$, and $k$ is")
        return problem, solution, s.done()
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
    solution = f"${_fmt_frac(ans)}$"
    s.step(
        "Let $x$ be the base's distance from the wall and $y$ the top's "
        "height. By the Pythagorean theorem:",
        f"x^2 + y^2 = {c}^2",
    )
    s.step(
        f"Find the height when $x = {a}$.",
        rf"y = \sqrt{{{c}^2 - {a}^2}} = \sqrt{{{b * b}}} = {b}",
    )
    s.step(
        "Differentiate with respect to $t$ and solve for $\\frac{dy}{dt}$.",
        r"2x\frac{dx}{dt} + 2y\frac{dy}{dt} = 0 \implies \frac{dy}{dt} = -\frac{x}{y} \cdot \frac{dx}{dt}",
    )
    s.substitute(
        rf"\frac{{dy}}{{dt}} = -\frac{{{a}}}{{{b}}} \cdot {v} = {_divide(-a * v, b)}",
        text=f"Substitute $x = {a}$, $y = {b}$, and $\\frac{{dx}}{{dt}} = {v}$.",
    )
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
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
    solution = f"${_num(c)}$"

    fa, fb = _poly_eval(poly, a), _poly_eval(poly, b)
    slope = Fraction(fb - fa, b - a)
    deriv = _poly_deriv(poly)
    s = Steps()
    s.step(
        f"The Mean Value Theorem says some $c$ in $({a}, {b})$ satisfies:",
        rf"f'(c) = \frac{{f({b}) - f({a})}}{{{b} - {paren(a)}}}",
    )
    s.step(
        "Compute the average rate of change.",
        rf"\frac{{{fb} - {paren(fa)}}}{{{b} - {paren(a)}}} = {_divide(fb - fa, b - a)}",
    )
    s.step("Differentiate with the power rule.", f"f'(x) = {_poly_tex(deriv)}")
    if 2 in poly:
        mid = Fraction(a + b, 2)
        dec = "" if mid.denominator == 1 else f" = {_num(c)}"
        s.step(
            "Set $f'(c)$ equal to the average rate of change and solve for $c$.",
            rf"{_poly_tex(deriv, 'c')} = {_ftex(slope)} \implies c = "
            rf"{_divide(int(slope) - poly[1], 2 * poly[2])}{dec}",
        )
        s.answer(solution)
    else:
        csq = Fraction(fb - fa, 3 * (b - a))
        s.step(
            "Set $f'(c)$ equal to the average rate of change.",
            rf"3c^2 = {_ftex(slope)} \implies c^2 = {_ftex(csq)}",
        )
        s.step(
            f"Take the positive square root, since $c$ must lie in $({a}, {b})$.",
            rf"c = \sqrt{{{_ftex(csq)}}} {_rel(c)} {_num(c)}",
        )
        s.answer(solution, lead="The answer is" if _rel(c) == "=" else _ROUNDED)
    return problem, solution, s.done()


@register
@with_variants
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
    solution = f"${_num(approx)}$"

    # Redo the arithmetic exactly for display.
    width = Fraction(b - a, n)
    xs = [a + i * width for i in range(n + 1)]
    ys = [_poly_eval(poly, x) for x in xs]
    weights = [1 if i in (0, n) else 2 for i in range(n + 1)]
    exact_sum = sum(w * y for w, y in zip(weights, ys))
    exact = width / 2 * exact_sum
    values = [rf"f({_ftex(x)}) = {_ftex(y)}" for x, y in zip(xs, ys)]
    rows = [r", \quad ".join(values[i:i + 3]) for i in range(0, len(values), 3)]
    weighted = _join([
        (_ftex(y) if w == 1 else rf"2\left({_ftex(y)}\right)") for w, y in zip(weights, ys)
    ])
    rel = "=" if (exact * 1000).denominator == 1 else r"\approx"
    tail = "" if _ftex(exact) == _num(approx) else f" {rel} {_num(approx)}"
    s = Steps()
    s.formula(
        "The Trapezoidal Rule",
        r"T = \frac{\Delta x}{2}\left[f(x_0) + 2f(x_1) + \cdots + 2f(x_{n-1}) + f(x_n)\right]",
    )
    s.step(
        r"Find $\Delta x$ and the points $x_0, \ldots, x_n$.",
        rf"\Delta x = \frac{{{b} - {paren(a)}}}{{{n}}} = {_ftex(width)}, \quad "
        rf"x = " + ", ".join(_ftex(x) for x in xs),
    )
    s.step(
        "Evaluate $f$ at each point.",
        r"\begin{gathered} " + r" \\ ".join(rows) + r" \end{gathered}",
    )
    s.step(
        "Add the values, doubling every interior one.",
        f"{weighted} = {_ftex(exact_sum)}",
    )
    s.step(
        r"Multiply by $\frac{\Delta x}{2}$.",
        rf"T = {_ftex(width / 2)} \cdot {paren(_ftex(exact_sum))} = {_ftex(exact)}{tail}",
    )
    s.answer(solution, lead="The answer is" if rel == "=" else _ROUNDED)
    return problem, solution, s.done()


@register
@with_variants
def calc_separable_ode():
    r"""Separable Differential Equation

    Solve $dy/dx = f(x)g(y)$ with an initial condition, then evaluate the
    solution at a point. Both forms have strictly positive solutions, so the
    value is always defined and reported to the nearest thousandth.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the separable differential equation $dy/dx = 1 y$ with $y(0) = 2$, then find $y(1)$. Round to the nearest thousandth if necessary. | $5.437$ |
    """
    s = Steps()
    if random.random() < 0.5:
        k = random.choice([-2, -1, 1, 2])
        y0 = random.randint(1, 5)
        x0 = random.randint(0, 1)
        x1 = random.randint(-1, 2)
        y1 = y0 * math.exp(k * (x1 - x0))       # y = y0 e^{k (x - x0)}
        eq = f"dy/dx = {k} y"
        s.step(
            "Separate the variables: divide by $y$ and multiply by $dx$.",
            rf"\frac{{dy}}{{y}} = {_coef(k, r'\,dx')}",
        )
        s.step(
            "Integrate both sides. Since the initial value is positive, $y > 0$.",
            rf"\ln y = {_coef(k, 'x')} + C",
        )
        shift = _coef(k, "x") if x0 == 0 else _coef(k, f"(x - {x0})")
        power = _ftex(k * (x1 - x0))
    else:
        k = random.choice([-1, 1])
        y0 = random.randint(1, 5)
        x0 = random.randint(0, 1)
        x1 = random.randint(0, 2)
        y1 = y0 * math.exp(k * (x1 * x1 - x0 * x0) / 2)  # y = y0 e^{k(x^2-x0^2)/2}
        eq = f"dy/dx = {k} x y"
        half = Fraction(k, 2)
        s.step(
            "Separate the variables: divide by $y$ and multiply by $dx$.",
            rf"\frac{{dy}}{{y}} = {_coef(k, 'x')} \, dx",
        )
        s.step(
            "Integrate both sides. Since the initial value is positive, $y > 0$.",
            rf"\ln y = {_coef(half, 'x^{2}')} + C",
        )
        shift = _coef(half, "x^{2}") if x0 == 0 else _coef(half, "(x^{2} - 1)")
        power = _ftex(Fraction(k * (x1 * x1 - x0 * x0), 2))
    s.step(
        f"Exponentiate and use $y({x0}) = {y0}$ to find the constant.",
        rf"y = {_coef(y0, f'e^{{{shift}}}')}",
    )
    s.substitute(
        rf"y({x1}) = {_coef(y0, f'e^{{{power}}}')} {_rel(y1)} {_num(y1)}",
        text=f"Substitute $x = {x1}$.",
    )
    problem = (
        f"Solve the separable differential equation ${eq}$ with "
        f"$y({x0}) = {y0}$, then find $y({x1})$. "
        f"Round to the nearest thousandth if necessary."
    )
    solution = f"${_num(y1)}$"
    s.answer(solution, lead="The answer is" if _rel(y1) == "=" else _ROUNDED)
    return problem, solution, s.done()


@register
@with_variants
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
    solution = f"${interval}$"

    s = Steps()
    s.step("A function is concave up where $f''(x) > 0$.")
    d2 = _second_derivative_steps(s, poly)
    if A > 0:
        s.step(
            f"The slope of $f''$ is ${6 * A} > 0$, so $f''(x) > 0$ to the right of this point.",
            rf"{_poly_tex(d2)} > 0 \iff x > {_ftex(x_inf)}",
        )
    else:
        s.step(
            f"The slope of $f''$ is ${6 * A} < 0$, so $f''(x) > 0$ to the left of this "
            f"point (dividing by a negative flips the inequality).",
            rf"{_poly_tex(d2)} > 0 \iff x < {_ftex(x_inf)}",
        )
    s.answer(solution, lead="So $f$ is concave up on")
    return problem, solution, s.done()


@register
@with_variants
def calc_taylor_coefficient():
    r"""Taylor/Maclaurin Coefficient

    The exact coefficient of $x^k$ in the Maclaurin series of a standard
    function ($e^x$, $\sin x$, $\cos x$, $\ln(1+x)$, or $1/(1-x)$).

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the coefficient of $x^{3}$ in the Maclaurin series of $f(x) = e^x$. Express your answer as a fraction in the form a/b, or an integer. | $1/6$ |
    """
    kind = random.choice(["exp", "sin", "cos", "ln1p", "geometric"])
    s = Steps()
    if kind == "exp":
        k = random.randint(0, 5)
        coeff = Fraction(1, math.factorial(k))
        func = "e^x"
        s.formula(
            "The Maclaurin series of $e^x$",
            r"e^x = 1 + x + \frac{x^2}{2!} + \frac{x^3}{3!} + \cdots = \sum_{n=0}^{\infty} \frac{x^n}{n!}",
        )
        s.step(
            rf"The $x^{{{k}}}$ term is $\frac{{x^{{{k}}}}}{{{k}!}}$, so its coefficient is:",
            rf"\frac{{1}}{{{k}!}} = {_divide(1, math.factorial(k))}",
        )
    elif kind == "sin":
        k = random.randint(1, 7)
        coeff = (Fraction(0) if k % 2 == 0
                 else Fraction((-1) ** ((k - 1) // 2), math.factorial(k)))
        func = "\\sin(x)"
        s.formula(
            r"The Maclaurin series of $\sin(x)$",
            r"\sin(x) = x - \frac{x^3}{3!} + \frac{x^5}{5!} - \frac{x^7}{7!} + \cdots",
        )
        if k % 2 == 0:
            s.step(f"Only odd powers of $x$ appear, so there is no $x^{{{k}}}$ term.")
        else:
            sign = "+" if coeff > 0 else "-"
            s.step(
                rf"The $x^{{{k}}}$ term is $\frac{{x^{{{k}}}}}{{{k}!}}$ with a ${sign}$ "
                rf"sign (the signs alternate), so its coefficient is:",
                rf"{'-' if coeff < 0 else ''}\frac{{1}}{{{k}!}} = {_ftex(coeff)}",
            )
    elif kind == "cos":
        k = random.randint(0, 6)
        coeff = (Fraction(0) if k % 2 == 1
                 else Fraction((-1) ** (k // 2), math.factorial(k)))
        func = "\\cos(x)"
        s.formula(
            r"The Maclaurin series of $\cos(x)$",
            r"\cos(x) = 1 - \frac{x^2}{2!} + \frac{x^4}{4!} - \frac{x^6}{6!} + \cdots",
        )
        if k % 2 == 1:
            s.step(f"Only even powers of $x$ appear, so there is no $x^{{{k}}}$ term.")
        else:
            sign = "+" if coeff > 0 else "-"
            s.step(
                rf"The $x^{{{k}}}$ term is $\frac{{x^{{{k}}}}}{{{k}!}}$ with a ${sign}$ "
                rf"sign (the signs alternate), so its coefficient is:",
                rf"{'-' if coeff < 0 else ''}\frac{{1}}{{{k}!}} = {_ftex(coeff)}",
            )
    elif kind == "ln1p":
        k = random.randint(1, 5)
        coeff = Fraction((-1) ** (k + 1), k)
        func = "\\ln(1+x)"
        s.formula(
            r"The Maclaurin series of $\ln(1+x)$",
            r"\ln(1+x) = x - \frac{x^2}{2} + \frac{x^3}{3} - \frac{x^4}{4} + \cdots",
        )
        s.step(
            rf"The $x^{{{k}}}$ term is $\frac{{x^{{{k}}}}}{{{k}}}$ with sign "
            rf"$(-1)^{{{k}+1}}$, so its coefficient is:",
            rf"\frac{{(-1)^{{{k + 1}}}}}{{{k}}} = {_ftex(coeff)}",
        )
    else:  # 1/(1-x) = sum x^k
        k = random.randint(0, 5)
        coeff = Fraction(1)
        func = "\\frac{1}{1-x}"
        s.formula(
            r"The geometric series for $\frac{1}{1-x}$",
            r"\frac{1}{1-x} = 1 + x + x^2 + x^3 + \cdots = \sum_{n=0}^{\infty} x^n",
        )
        s.step(f"Every power of $x$ appears with coefficient $1$, including $x^{{{k}}}$.")
    problem = (
        f"Find the coefficient of $x^{{{k}}}$ in the Maclaurin series of "
        f"$f(x) = {func}$. {_FRACTION_HINT}"
    )
    solution = f"${_fmt_frac(coeff)}$"
    s.answer(solution)
    return problem, solution, s.done()
