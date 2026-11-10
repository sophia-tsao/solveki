"""Solveki-local generators for Georgia "Precalculus".

Every generator here takes no required arguments, is decorated with
``@register``, and returns ``(problem, solution, steps)``: LaTeX strings plus a
step-by-step explanation built with ``_steps.Steps``.
Answers are kept clean: integers, values rounded to at most three decimal
places, or reduced ``"a/b"`` fractions. Never seed ``random`` inside a
generator.
"""
import random
from fractions import Fraction
from math import (acos, asin, atan, atan2, comb, cos, degrees, gcd, hypot, pi,
                  radians, sin, sqrt, tan)

from ._registry import register
from ._variants import with_variants
from ._format import num as _num, frac_from as _frac_from
from ._steps import Steps, paren, tex_frac

_ROUND_HINT = "Round your answer to the nearest thousandth."


# Primitive Pythagorean triples (leg, leg, hypotenuse), used where an exact
# rational trig value is required.
_PYTHAG_TRIPLES = [
    (3, 4, 5),
    (5, 12, 13),
    (8, 15, 17),
    (7, 24, 25),
    (20, 21, 29),
    (9, 40, 41),
    (12, 35, 37),
]

# Special exact values as (LaTeX, numeric) pairs, grouped by the trig context.
_R2 = sqrt(2) / 2
_R3 = sqrt(3) / 2
_SIN_COS_VALUES = [
    (r"0", 0.0),
    (r"\frac{1}{2}", 0.5),
    (r"\frac{\sqrt{2}}{2}", _R2),
    (r"\frac{\sqrt{3}}{2}", _R3),
    (r"1", 1.0),
    (r"-\frac{1}{2}", -0.5),
    (r"-\frac{\sqrt{2}}{2}", -_R2),
    (r"-\frac{\sqrt{3}}{2}", -_R3),
    (r"-1", -1.0),
]
_TAN_VALUES = [
    (r"0", 0.0),
    (r"\frac{\sqrt{3}}{3}", sqrt(3) / 3),
    (r"1", 1.0),
    (r"\sqrt{3}", sqrt(3)),
    (r"-\frac{\sqrt{3}}{3}", -sqrt(3) / 3),
    (r"-1", -1.0),
    (r"-\sqrt{3}", -sqrt(3)),
]


def _format_poly(terms, var):
    """Render ``(coefficient, exponent)`` pairs as a polynomial string.

    ``terms`` is ordered from the highest exponent down. Zero-coefficient
    terms are dropped and unit coefficients omit the leading ``1``.
    """
    pieces = []
    for coeff, exp in terms:
        if coeff == 0:
            continue
        sign = "-" if coeff < 0 else "+"
        magnitude = abs(coeff)
        if exp == 0:
            body = str(magnitude)
        else:
            token = var if exp == 1 else f"{var}^{exp}"
            body = token if magnitude == 1 else f"{magnitude}{token}"
        pieces.append((sign, body))

    if not pieces:
        return "0"

    first_sign, first_body = pieces[0]
    result = first_body if first_sign == "+" else f"-{first_body}"
    for sign, body in pieces[1:]:
        result += f"{sign}{body}"
    return result


# ------------------- step-by-step helpers (exact values) -------------------
#
# Exact special-angle values are sums of rational multiples of square roots,
# stored as ``{radicand: Fraction}`` ("surds"), e.g. (sqrt(6) + sqrt(2))/4 is
# ``{2: 1/4, 6: 1/4}``. They let the steps show exact arithmetic before the
# rounded answer.

def _square_free(n):
    """Split ``n`` as ``out**2 * inside`` with ``inside`` square-free."""
    out, k = 1, 2
    while k * k <= n:
        while n % (k * k) == 0:
            n //= k * k
            out *= k
        k += 1
    return out, n


def _surd(pairs):
    """Build a surd from ``(coefficient, radicand)`` pairs, simplified."""
    terms = {}
    for coeff, rad in pairs:
        if rad == 0:
            continue
        out, rad = _square_free(rad)
        terms[rad] = terms.get(rad, 0) + Fraction(coeff) * out
    return {r: c for r, c in terms.items() if c != 0}


def _s_add(x, y):
    return _surd([(c, r) for r, c in x.items()] + [(c, r) for r, c in y.items()])


def _s_scale(x, k):
    return _surd([(c * k, r) for r, c in x.items()])


def _s_mul(x, y):
    return _surd([(c1 * c2, r1 * r2)
                  for r1, c1 in x.items() for r2, c2 in y.items()])


def _s_div(x, y):
    """``x / y`` for a one-term ``y`` or ``y = p + q*sqrt(m)`` (conjugate)."""
    if len(y) == 1:
        (r, c), = y.items()
        return _s_scale(_s_mul(x, {r: Fraction(1)}), 1 / (c * r))
    conj = {r: (c if r == 1 else -c) for r, c in y.items()}
    return _s_scale(_s_mul(x, conj), 1 / _s_mul(y, conj)[1])


def _s_float(x):
    return sum(float(c) * sqrt(r) for r, c in x.items())


def _s_rational(x):
    return set(x) <= {1}


def _s_tex(x):
    r"""LaTeX for a surd over a common denominator: ``\frac{\sqrt{6}+\sqrt{2}}{4}``."""
    if not x:
        return "0"
    den = 1
    for c in x.values():
        den = den * c.denominator // gcd(den, c.denominator)
    items = sorted(x.items(), key=lambda item: (item[1] < 0, item[0]))
    negate = den != 1 and all(c < 0 for _, c in items)
    top = ""
    for i, (r, c) in enumerate(items):
        k = int(c * den) * (-1 if negate else 1)
        mag = abs(k)
        body = str(mag) if r == 1 else ("" if mag == 1 else str(mag)) + rf"\sqrt{{{r}}}"
        if i == 0:
            top += ("-" if k < 0 else "") + body
        else:
            top += (" - " if k < 0 else " + ") + body
    if den == 1:
        return top
    return ("-" if negate else "") + rf"\frac{{{top}}}{{{den}}}"


def _wrap(tex):
    r"""Parenthesise LaTeX that starts with a minus sign (for products)."""
    return rf"\left({tex}\right)" if tex.startswith("-") else tex


def _approx(x):
    r"""A surd and its decimal: ``\frac{1}{2} = 0.5``, ``\frac{\sqrt{3}}{2} \approx 0.866``."""
    tex, decimal = _s_tex(x), _num(_s_float(x))
    if tex == decimal:
        return tex
    return f"{tex} {'=' if _s_rational(x) else chr(92) + 'approx'} {decimal}"


def _quotient_steps(s, lhs, top, bottom, text):
    """Steps dividing surd ``top`` by ``bottom``; returns the exact quotient.

    First clears any fractions inside the numerator and denominator, then
    divides, rationalizing the denominator (by its conjugate if needed).
    """
    lcd = 1
    for c in list(top.values()) + list(bottom.values()):
        lcd = lcd * c.denominator // gcd(lcd, c.denominator)
    line = rf"{lhs} = \frac{{{_s_tex(top)}}}{{{_s_tex(bottom)}}}"
    if lcd != 1:
        top, bottom = _s_scale(top, lcd), _s_scale(bottom, lcd)
        if bottom != {1: 1}:
            line += rf" = \frac{{{_s_tex(top)}}}{{{_s_tex(bottom)}}}"
            text += f" Multiply the top and bottom by ${lcd}$ to clear the fractions."
    final = _s_div(top, bottom)
    if _s_rational(bottom):
        s.step(f"{text} Then divide.", f"{line} = {_approx(final)}")
        return final
    s.step(text, line)
    if len(bottom) > 1:
        conj = {r: (c if r == 1 else -c) for r, c in bottom.items()}
        how = (f"Multiply the top and bottom by the conjugate ${_s_tex(conj)}$, "
               f"then simplify.")
    else:
        how = "Rationalize the denominator, then simplify."
    s.step(how, rf"{lhs} = {_approx(final)}")
    return final


def _tex_fraction(value):
    """A ``Fraction`` as LaTeX: an integer or a signed ``\\frac``."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return tex_frac(fr.numerator, fr.denominator)


def _divide(n, d):
    r"""``n / d`` worked to lowest terms: ``\frac{-6}{4} = -\frac{3}{2}``.

    Already-reduced fractions with a positive denominator are shown once.
    """
    value = _tex_fraction(Fraction(n, d))
    if d > 1 and gcd(n, d) == 1:
        return value
    return rf"\frac{{{n}}}{{{d}}} = {value}"


# sin of each first-quadrant special angle.
_SIN_REF = {
    0: {}, 30: {1: Fraction(1, 2)}, 45: {2: Fraction(1, 2)},
    60: {3: Fraction(1, 2)}, 90: {1: Fraction(1)},
}
_QUADRANT_NAMES = {1: "I", 2: "II", 3: "III", 4: "IV"}
# The quadrants where each function is positive.
_POSITIVE_IN = {"sin": (1, 2), "cos": (1, 4), "tan": (1, 3)}
_FN_NAMES = {"sin": "sine", "cos": "cosine", "tan": "tangent"}


def _ref_angle(deg):
    d = deg % 180
    return d if d <= 90 else 180 - d


def _quadrant(deg):
    """Quadrant 1-4 of an angle in degrees, or None on an axis."""
    d = deg % 360
    return None if d % 90 == 0 else d // 90 + 1


def _exact_trig(fn, deg):
    """Exact sin/cos/tan of a multiple of 30 or 45 degrees, as a surd."""
    d = deg % 360
    ref = _ref_angle(d)
    s = _s_scale(_SIN_REF[ref], 1 if d <= 180 else -1)
    c = _s_scale(_SIN_REF[90 - ref], 1 if (d <= 90 or d >= 270) else -1)
    if fn == "sin":
        return s
    if fn == "cos":
        return c
    return _s_div(s, c)


def _reference_step(s, fn, deg):
    """Add the step locating ``deg`` and giving the sign of ``fn`` there."""
    quadrant = _quadrant(deg)
    d = deg % 360
    if quadrant is None:
        point = f"({_s_tex(_exact_trig('cos', d))}, {_s_tex(_exact_trig('sin', d))})"
        s.step(f"${d}^\\circ$ lies on an axis, at the point ${point}$ of the "
               f"unit circle ($x$ is the cosine, $y$ is the sine).")
        return
    sign = "positive" if quadrant in _POSITIVE_IN[fn] else "negative"
    s.step(f"${deg}^\\circ$ is in Quadrant {_QUADRANT_NAMES[quadrant]} with "
           f"reference angle ${_ref_angle(d)}^\\circ$, and {_FN_NAMES[fn]} is "
           f"{sign} in Quadrant {_QUADRANT_NAMES[quadrant]}.")


def _exact_trig_line(fn, deg, arg_tex):
    r"""``\sin(arg) = -\sin 30^\circ = -\frac{1}{2}``, via the reference angle."""
    value = _exact_trig(fn, deg)
    lhs = rf"\{fn}\left({arg_tex}\right)"
    if _quadrant(deg) is None:
        if fn == "tan":
            y, x = _exact_trig("sin", deg), _exact_trig("cos", deg)
            return rf"{lhs} = \frac{{y}}{{x}} = \frac{{{_s_tex(y)}}}{{{_s_tex(x)}}} = {_approx(value)}"
        return rf"{lhs} = {_approx(value)}"
    sign = "" if _quadrant(deg) in _POSITIVE_IN[fn] else "-"
    return rf"{lhs} = {sign}\{fn} {_ref_angle(deg)}^\circ = {_approx(value)}"


def _coef(k, var):
    """``k`` times ``var`` with unit coefficients dropped: ``x``, ``-x``, ``3x``."""
    if k == 1:
        return var
    if k == -1:
        return f"-{var}"
    return f"{k}{var}"


def _minus(var, value):
    """``var - value`` with the sign folded: ``x - 3``, ``x + 2``, ``x``."""
    if value == 0:
        return var
    return f"{var} - {value}" if value > 0 else f"{var} + {-value}"


def _signed(value):
    """`` + 3`` / `` - 3`` / ``""`` for appending a constant term."""
    if value == 0:
        return ""
    return f" + {value}" if value > 0 else f" - {-value}"


@register
@with_variants
def pc_law_of_sines(min_angle=25, max_angle=80, min_side=3, max_side=25):
    r"""Law of Sines (ASA)

    Given two angles and a side, find another side via
    ``b = a * sin(B) / sin(A)``.
    """
    angle_a = random.randint(min_angle, max_angle)
    angle_b = random.randint(min_angle, max_angle)
    side_a = random.randint(min_side, max_side)
    ans = side_a * sin(radians(angle_b)) / sin(radians(angle_a))
    problem = (
        f"In triangle $ABC$, angle $A = {angle_a}^\\circ$, angle "
        f"$B = {angle_b}^\\circ$, and side $a = {side_a}$ (opposite $A$). "
        f"Find side $b$ (opposite $B$), rounded to the nearest thousandth."
    )
    solution = f"${_num(ans)}$"
    s = Steps()
    s.formula("The Law of Sines", r"\frac{a}{\sin A} = \frac{b}{\sin B}")
    s.step(r"Multiply both sides by $\sin B$ to solve for $b$.",
           r"b = \frac{a \sin B}{\sin A}")
    s.substitute(rf"b = \frac{{{side_a} \sin {angle_b}^\circ}}{{\sin {angle_a}^\circ}}")
    s.step("Evaluate with a calculator in degree mode, rounding only at the end.",
           rf"b = \frac{{{side_a} \sin {angle_b}^\circ}}{{\sin {angle_a}^\circ}}"
           rf" \approx {_num(ans)}")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def pc_law_of_cosines_side(min_side=3, max_side=20, min_angle=20, max_angle=160):
    r"""Law of Cosines (SAS)

    Given two sides and the included angle, find the third side via
    ``c^2 = a^2 + b^2 - 2ab*cos(C)``.
    """
    side_a = random.randint(min_side, max_side)
    side_b = random.randint(min_side, max_side)
    angle_c = random.randint(min_angle, max_angle)
    c_sq = side_a ** 2 + side_b ** 2 - 2 * side_a * side_b * cos(radians(angle_c))
    ans = sqrt(c_sq)
    problem = (
        f"In triangle $ABC$, side $a = {side_a}$, side $b = {side_b}$, and the "
        f"included angle $C = {angle_c}^\\circ$. Find side $c$, rounded to the "
        f"nearest thousandth."
    )
    solution = f"${_num(ans)}$"
    s = Steps()
    s.formula("The Law of Cosines", r"c^2 = a^2 + b^2 - 2ab\cos C")
    s.substitute(rf"c^2 = {side_a}^2 + {side_b}^2 - 2({side_a})({side_b})\cos {angle_c}^\circ")
    s.step("Simplify, then evaluate the cosine in degree mode.",
           rf"c^2 = {side_a ** 2 + side_b ** 2} - {2 * side_a * side_b}\cos {angle_c}^\circ"
           rf" \approx {_num(c_sq)}")
    s.step("Take the square root of both sides, using the unrounded value of $c^2$.",
           rf"c = \sqrt{{{side_a ** 2 + side_b ** 2} - {2 * side_a * side_b}\cos {angle_c}^\circ}}"
           rf" \approx {_num(ans)}")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def pc_oblique_triangle_area(min_side=3, max_side=20, min_angle=20, max_angle=160):
    r"""Oblique Triangle Area (SAS)

    Area of a triangle from two sides and the included angle:
    ``0.5 * a * b * sin(C)``.
    """
    side_a = random.randint(min_side, max_side)
    side_b = random.randint(min_side, max_side)
    angle_c = random.randint(min_angle, max_angle)
    ans = 0.5 * side_a * side_b * sin(radians(angle_c))
    problem = (
        f"A triangle has sides $a = {side_a}$ and $b = {side_b}$ with included "
        f"angle $C = {angle_c}^\\circ$. Find its area, rounded to the nearest "
        f"thousandth."
    )
    solution = f"${_num(ans)}$"
    s = Steps()
    s.formula("The area of a triangle from two sides and the included angle",
              r"\text{Area} = \frac{1}{2}ab\sin C")
    s.substitute(rf"\text{{Area}} = \frac{{1}}{{2}}({side_a})({side_b})\sin {angle_c}^\circ")
    s.step("Multiply, then evaluate the sine in degree mode.",
           rf"\text{{Area}} = {_num(0.5 * side_a * side_b)}\sin {angle_c}^\circ"
           rf" \approx {_num(ans)}")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def pc_inverse_trig():
    r"""Inverse Trigonometric Values

    Evaluate arcsin/arccos/arctan at a special value; answer in degrees.
    """
    func = random.choice(["sin", "cos", "tan"])
    if func == "tan":
        latex, value = random.choice(_TAN_VALUES)
        deg = round(degrees(atan2(value, 1.0)))
    else:
        latex, value = random.choice(_SIN_COS_VALUES)
        deg = round(degrees(asin(value) if func == "sin" else acos(value)))
    problem = f"Evaluate $\\arc{func}\\left({latex}\\right)$ in degrees."
    solution = f"${deg}$"

    ranges = {"sin": r"-90^\circ \le \theta \le 90^\circ",
              "cos": r"0^\circ \le \theta \le 180^\circ",
              "tan": r"-90^\circ < \theta < 90^\circ"}
    s = Steps()
    s.step(f"$\\arc{func}\\left({latex}\\right)$ is the angle $\\theta$ in the "
           f"range ${ranges[func]}$ with $\\{func}\\theta = {latex}$.")
    if value >= 0:
        s.step(f"From the special angles, $\\{func} {deg}^\\circ = {latex}$, and "
               f"${deg}^\\circ$ is in the range.",
               rf"\{func} {deg}^\circ = {latex}")
    else:
        ref = abs(deg) if func != "cos" else 180 - deg
        positive = latex.lstrip("-")
        s.step(f"Ignore the sign first: $\\{func} {ref}^\\circ = {positive}$, so "
               f"the reference angle is ${ref}^\\circ$.")
        if func == "cos":
            s.step("In this range cosine is negative only for angles past "
                   "$90^\\circ$, so subtract the reference angle from $180^\\circ$.",
                   rf"\theta = 180^\circ - {ref}^\circ = {deg}^\circ")
        else:
            s.step(f"In this range {_FN_NAMES[func]} is negative only for negative "
                   f"angles, so take the negative of the reference angle.",
                   rf"\theta = -{ref}^\circ")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_double_angle():
    r"""Double-Angle Values

    Given ``sin x`` or ``cos x`` (from a Pythagorean triple, x acute), compute
    ``sin(2x)`` or ``cos(2x)`` as a reduced fraction.
    """
    a, b, c = random.choice(_PYTHAG_TRIPLES)
    # Randomly decide which leg plays the "opposite" role for sin.
    if random.random() < 0.5:
        a, b = b, a
    given = random.choice(["sin", "cos"])
    if given == "sin":
        given_num = a  # sin x = a/c  ->  cos x = b/c
    else:
        given_num = b  # cos x = b/c  ->  sin x = a/c
    sin_num, cos_num = a, b  # over c
    target = random.choice(["sin", "cos"])
    if target == "sin":
        frac = Fraction(2 * sin_num * cos_num, c * c)
    else:
        frac = Fraction(cos_num * cos_num - sin_num * sin_num, c * c)
    problem = (
        f"Given that $\\{given} x = \\frac{{{given_num}}}{{{c}}}$ and $x$ is "
        f"acute, find $\\{target}(2x)$. Express your answer as a reduced "
        f"fraction a/b."
    )
    solution = f"${frac.numerator}/{frac.denominator}$"

    other = "cos" if given == "sin" else "sin"
    other_num = cos_num if given == "sin" else sin_num
    s = Steps()
    s.step(f"Since $x$ is acute, both $\\sin x$ and $\\cos x$ are positive. Use "
           f"$\\sin^2 x + \\cos^2 x = 1$ to find $\\{other} x$.",
           rf"\{other} x = \sqrt{{1 - \left({tex_frac(given_num, c)}\right)^2}}"
           rf" = \sqrt{{{tex_frac(c * c - given_num ** 2, c * c)}}}"
           rf" = {tex_frac(other_num, c)}")
    if target == "sin":
        s.formula("The double-angle identity for sine", r"\sin(2x) = 2\sin x\cos x")
        raw = rf"2 \cdot {tex_frac(sin_num, c)} \cdot {tex_frac(cos_num, c)}"
        raw_num = 2 * sin_num * cos_num
    else:
        s.formula("The double-angle identity for cosine",
                  r"\cos(2x) = \cos^2 x - \sin^2 x")
        raw = (rf"\left({tex_frac(cos_num, c)}\right)^2 - "
               rf"\left({tex_frac(sin_num, c)}\right)^2")
        raw_num = cos_num * cos_num - sin_num * sin_num
    result = rf"{raw} = {tex_frac(raw_num, c * c)}"
    if (frac.numerator, frac.denominator) != (raw_num, c * c):
        result += f" = {_tex_fraction(frac)}"
    s.substitute(rf"\{target}(2x) = {result}",
                 text=f"Substitute $\\sin x = {tex_frac(sin_num, c)}$ and "
                      f"$\\cos x = {tex_frac(cos_num, c)}$.")
    s.answer(solution)
    return problem, solution, s.done()


def _solve_trig(func_numeric, value, is_tan):
    """Integer-degree solutions of ``f(x) = value`` on ``[0, 360)``."""
    sols = []
    for d in range(360):
        if is_tan and d in (90, 270):
            continue
        if abs(func_numeric(radians(d)) - value) < 1e-6:
            sols.append(d)
    return sols


@register
@with_variants
def pc_solve_trig_equation():
    r"""Solve a Trigonometric Equation

    Solve ``sin/cos/tan(x) = value`` on ``[0, 360)`` degrees.
    """
    func = random.choice(["sin", "cos", "tan"])
    if func == "tan":
        latex, value = random.choice(_TAN_VALUES)
        sols = _solve_trig(tan, value, True)
    else:
        latex, value = random.choice(_SIN_COS_VALUES)
        fn = sin if func == "sin" else cos
        sols = _solve_trig(fn, value, False)
    problem = (
        f"Solve $\\{func}(x) = {latex}$ for $x$ in $[0, 360)$ degrees. "
        f"List all solutions in degrees, comma-separated and in increasing "
        f"order."
    )
    solution = "$" + ", ".join(str(d) for d in sorted(sols)) + "$"
    s = Steps()
    _trig_equation_steps(s, func, latex, value, sols)
    s.answer(solution)
    return problem, solution, s.done()


def _trig_equation_steps(s, func, latex, value, sols):
    """Steps solving ``func(x) = value`` on ``[0, 360)`` via the reference angle."""
    listed = ", ".join(f"{d}^\\circ" for d in sorted(sols))
    if value == 0 or (func != "tan" and abs(value) == 1):
        if func == "tan":
            where = "where the $y$-coordinate is $0$ (since $\\tan x = \\frac{y}{x}$)"
        else:
            coord = "y" if func == "sin" else "x"
            where = f"where the ${coord}$-coordinate is ${latex}$"
        s.step(f"${latex}$ is a quadrantal value: on the unit circle this happens "
               f"only on an axis, {where}.", rf"x = {listed}")
        return
    ref = round(degrees({"sin": asin, "cos": acos, "tan": atan}[func](abs(value))))
    s.step(f"First find the reference angle: $\\{func} {ref}^\\circ = "
           f"{latex.lstrip('-')}$, so it is ${ref}^\\circ$.")
    quadrants = _POSITIVE_IN[func] if value > 0 else tuple(
        q for q in (1, 2, 3, 4) if q not in _POSITIVE_IN[func])
    sign = "positive" if value > 0 else "negative"
    names = " and ".join(_QUADRANT_NAMES[q] for q in quadrants)
    forms = {1: f"{ref}^\\circ", 2: f"180^\\circ - {ref}^\\circ = {180 - ref}^\\circ",
             3: f"180^\\circ + {ref}^\\circ = {180 + ref}^\\circ",
             4: f"360^\\circ - {ref}^\\circ = {360 - ref}^\\circ"}
    s.step(f"{_FN_NAMES[func].capitalize()} is {sign} in Quadrants {names}. Place "
           f"the reference angle in each.",
           r",\quad ".join(f"x = {forms[q]}" for q in quadrants))


def _clean(value):
    """Round to 3 dp and normalise ``-0.0`` to ``0.0``."""
    return round(value, 3) + 0.0


def _pt(value):
    """Typeable coordinate component: 3dp, trailing ``.0`` dropped."""
    return _num(value)


@register
@with_variants
def pc_polar_to_rectangular(max_r=10):
    r"""Polar to Rectangular

    Convert ``(r, theta_deg)`` to rectangular ``(x, y)``.
    """
    r = random.randint(1, max_r)
    theta = random.choice([0, 30, 45, 60, 90, 120, 135, 150, 180,
                            210, 225, 240, 270, 300, 315, 330])
    x = r * cos(radians(theta))
    y = r * sin(radians(theta))
    problem = (
        f"Convert the polar coordinates $(r, \\theta) = ({r}, {theta}^\\circ)$ "
        f"to rectangular coordinates, rounded to the nearest thousandth. "
        f"Format your answer as (x, y)."
    )
    solution = f"({_pt(x)}, {_pt(y)})"

    s = Steps()
    s.step("Convert polar to rectangular coordinates with these formulas.",
           r"x = r\cos\theta, \quad y = r\sin\theta")
    if _quadrant(theta) is None:
        s.step(f"${theta}^\\circ$ lies on an axis, so its cosine and sine are "
               f"$0$ or $\\pm 1$.")
    else:
        s.step(f"${theta}^\\circ$ is in Quadrant {_QUADRANT_NAMES[_quadrant(theta)]} "
               f"with reference angle ${_ref_angle(theta)}^\\circ$, which fixes the "
               f"signs of its cosine and sine.")
    for name, fn in (("x", "cos"), ("y", "sin")):
        exact = _exact_trig(fn, theta)
        s.step(f"Find ${name}$.",
               rf"{name} = {r}\{fn} {theta}^\circ = {r} \cdot {_wrap(_s_tex(exact))}"
               rf" = {_approx(_s_scale(exact, r))}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_rectangular_to_polar(max_coord=10):
    r"""Rectangular to Polar

    Convert ``(x, y)`` to polar ``(r, theta_deg)`` with ``0 <= theta < 360``.
    """
    while True:
        x = random.randint(-max_coord, max_coord)
        y = random.randint(-max_coord, max_coord)
        if x != 0 or y != 0:
            break
    r = hypot(x, y)
    theta = degrees(atan2(y, x))
    if theta < 0:
        theta += 360
    problem = (
        f"Convert the rectangular coordinates $(x, y) = ({x}, {y})$ to polar "
        f"coordinates $(r, \\theta)$ with $\\theta$ in degrees, "
        f"$0 \\le \\theta < 360$, rounded to the nearest thousandth. "
        f"Format your answer as (r, theta)."
    )
    solution = f"({_pt(r)}, {_pt(theta)})"

    s = Steps()
    r_sq = x * x + y * y
    r_value = f"= {int(r)}" if int(r) ** 2 == r_sq else rf"\approx {_num(r)}"
    s.formula("The distance from the origin", r"r = \sqrt{x^2 + y^2}")
    s.substitute(rf"r = \sqrt{{{paren(x)}^2 + {paren(y)}^2}} = \sqrt{{{r_sq}}} {r_value}")
    if x == 0 or y == 0:
        axis = {(1, 0): ("positive $x$", 0), (0, 1): ("positive $y$", 90),
                (-1, 0): ("negative $x$", 180), (0, -1): ("negative $y$", 270)}
        where, angle = axis[((x > 0) - (x < 0), (y > 0) - (y < 0))]
        s.step(f"The point lies on the {where}-axis, so $\\theta = {angle}^\\circ$.")
    else:
        alpha = degrees(atan2(abs(y), abs(x)))
        ratio = _tex_fraction(Fraction(abs(y), abs(x)))
        a_rel = "=" if abs(alpha - round(alpha)) < 1e-9 else r"\approx"
        s.step("Find the reference angle $\\alpha$ from $\\tan\\alpha = "
               "\\left|\\frac{y}{x}\\right|$.",
               rf"\alpha = \tan^{{-1}}\left({ratio}\right) {a_rel} {_num(alpha)}^\circ")
        quadrant = int(_quadrant(theta))
        forms = {1: r"\theta = \alpha", 2: r"\theta = 180^\circ - \alpha",
                 3: r"\theta = 180^\circ + \alpha", 4: r"\theta = 360^\circ - \alpha"}
        s.step(f"The point $({x}, {y})$ is in Quadrant {_QUADRANT_NAMES[quadrant]}.",
               rf"{forms[quadrant]} {a_rel} {_num(theta)}^\circ")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_finite_geometric_sum(max_a=6, max_n=8):
    r"""Finite Geometric Series Sum

    Sum of the first ``n`` terms with first term ``a`` and ratio ``r``.
    """
    a = random.choice([i for i in range(-max_a, max_a + 1) if i != 0])
    r = random.choice([-3, -2, 2, 3])
    n = random.randint(2, max_n)
    total = sum(a * r ** k for k in range(n))
    problem = (
        f"Find the sum of the first ${n}$ terms of the geometric series with "
        f"first term $a = {a}$ and common ratio $r = {r}$."
    )
    solution = f"${total}$"
    s = Steps()
    s.formula("The sum of the first $n$ terms of a geometric series",
              r"S_n = \frac{a(1 - r^n)}{1 - r}")
    s.substitute(rf"S_{{{n}}} = \frac{{{a}\left(1 - {paren(r)}^{{{n}}}\right)}}"
                 rf"{{1 - {paren(r)}}}")
    s.step(f"Evaluate the power: ${paren(r)}^{{{n}}} = {r ** n}$.",
           rf"S_{{{n}}} = \frac{{{a}\left(1 - {paren(r ** n)}\right)}}{{{1 - r}}}"
           rf" = \frac{{{a}({1 - r ** n})}}{{{1 - r}}}")
    s.step("Multiply and divide.",
           rf"S_{{{n}}} = \frac{{{a * (1 - r ** n)}}}{{{1 - r}}} = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_sigma_arithmetic_sum(max_coeff=5, max_const=10, max_n=20):
    r"""Sigma-Notation Arithmetic Sum

    Evaluate ``sum_{k=1}^{n} (A*k + B)``.
    """
    coeff = random.randint(1, max_coeff)
    const = random.randint(-max_const, max_const)
    n = random.randint(3, max_n)
    total = sum(coeff * k + const for k in range(1, n + 1))
    term = f"{coeff}k"
    if const > 0:
        term += f" + {const}"
    elif const < 0:
        term += f" - {abs(const)}"
    problem = f"Evaluate $\\sum_{{k=1}}^{{{n}}} ({term})$."
    solution = f"${total}$"

    sigma = rf"\sum_{{k=1}}^{{{n}}}"
    tri = n * (n + 1) // 2
    k_sum = rf"{'' if coeff == 1 else coeff}{sigma} k"
    s = Steps()
    if const == 0:
        s.step("Pull the constant factor out of the sum." if coeff != 1
               else f"This is the sum of the first ${n}$ positive integers.",
               rf"{sigma} {term} = {k_sum}")
    else:
        s.step("Split the sum into two sums" + (" and pull the constant factor out."
                                                 if coeff != 1 else "."),
               rf"{sigma} ({term}) = {k_sum} + {sigma} {paren(const)}")
    s.step("Use $\\sum_{k=1}^{n} k = \\frac{n(n+1)}{2}$"
           + ("." if const == 0 else ", and adding a constant $c$ for $n$ terms gives $cn$."),
           rf"{sigma} k = \frac{{{n}({n + 1})}}{{2}} = {tri}")
    if const == 0:
        if coeff != 1:
            s.step("Multiply.", rf"{coeff}({tri}) = {total}")
    else:
        s.step("Substitute and simplify.",
               rf"{coeff}({tri}) + {paren(const)}({n}) = {coeff * tri}"
               rf"{_signed(const * n)} = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_sequence_limit():
    r"""Limit of a Rational Sequence

    ``lim_{n->inf} (numerator)/(denominator)`` of equal-degree polynomials,
    equal to the ratio of leading coefficients (reduced).
    """
    degree = random.randint(1, 3)

    def _poly():
        terms = []
        lead = random.choice([i for i in range(-9, 10) if i != 0])
        terms.append((lead, degree))
        for exp in range(degree - 1, -1, -1):
            terms.append((random.randint(-9, 9), exp))
        return terms, lead

    num_terms, num_lead = _poly()
    den_terms, den_lead = _poly()
    frac = Fraction(num_lead, den_lead)
    numerator = _format_poly(num_terms, "n")
    denominator = _format_poly(den_terms, "n")
    problem = (
        f"Find $\\lim_{{n \\to \\infty}} \\frac{{{numerator}}}{{{denominator}}}$. "
        f"Express your answer as an integer or reduced fraction a/b."
    )
    if frac.denominator == 1:
        solution = f"${frac.numerator}$"
    else:
        solution = f"${frac.numerator}/{frac.denominator}$"

    power = "n" if degree == 1 else f"n^{degree}"
    s = Steps()
    s.step(f"The numerator and denominator both have degree ${degree}$. Divide "
           f"every term by ${power}$, the highest power of $n$.")
    s.step(f"As $n \\to \\infty$, every term with $n$ left in its denominator goes "
           f"to $0$, leaving only the leading coefficients.",
           rf"\lim_{{n \to \infty}} \frac{{{numerator}}}{{{denominator}}} = "
           rf"\frac{{{num_lead}}}{{{den_lead}}}")
    if (num_lead, den_lead) != (frac.numerator, frac.denominator):
        s.step("Simplify.", rf"\frac{{{num_lead}}}{{{den_lead}}} = {_tex_fraction(frac)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_vector_add(max_component=9):
    r"""Vector Operations (2D)

    Add, subtract, or scale two 2D vectors.
    """
    ux, uy = (random.randint(-max_component, max_component),
              random.randint(-max_component, max_component))
    vx, vy = (random.randint(-max_component, max_component),
              random.randint(-max_component, max_component))
    op = random.choice(["add", "sub", "scalar"])
    if op == "add":
        target = r"\vec{u} + \vec{v}"
        rx, ry = ux + vx, uy + vy
    elif op == "sub":
        target = r"\vec{u} - \vec{v}"
        rx, ry = ux - vx, uy - vy
    else:
        scalar = random.choice([i for i in range(-5, 6) if i not in (0, 1)])
        target = rf"{scalar}\vec{{u}}"
        rx, ry = scalar * ux, scalar * uy
    problem = (
        f"Let $\\vec{{u}} = \\langle {ux}, {uy} \\rangle$ and "
        f"$\\vec{{v}} = \\langle {vx}, {vy} \\rangle$. Compute ${target}$. "
        f"Give the resulting vector as (x, y)."
    )
    solution = f"({rx}, {ry})"

    s = Steps()
    if op == "scalar":
        s.step("Multiply each component of $\\vec{u}$ by the scalar.",
               rf"{scalar}\langle {ux}, {uy} \rangle = \langle {scalar}({ux}), "
               rf"{scalar}({uy}) \rangle = \langle {rx}, {ry} \rangle")
    else:
        verb, sym = ("Add", "+") if op == "add" else ("Subtract", "-")
        s.step(f"{verb} the vectors component by component.",
               rf"\langle {ux} {sym} {paren(vx)}, {uy} {sym} {paren(vy)} \rangle"
               rf" = \langle {rx}, {ry} \rangle")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_parametric_to_rectangular(max_bd=6):
    r"""Eliminate the Parameter

    Given ``x = a*t + b`` and ``y = c*t + d`` (a divides c), eliminate ``t`` to
    write ``y`` as a linear function of ``x``.
    """
    a = random.choice([i for i in range(-3, 4) if i != 0])
    quotient = random.choice([i for i in range(-4, 5) if i != 0])  # c / a
    c = a * quotient
    b = random.randint(-max_bd, max_bd)
    d = random.randint(-max_bd, max_bd)
    slope = c // a  # == quotient, integer
    intercept = d - slope * b

    if slope == 1:
        slope_str = "x"
    elif slope == -1:
        slope_str = "-x"
    else:
        slope_str = f"{slope}x"
    if intercept > 0:
        rhs = f"{slope_str} + {intercept}"
    elif intercept < 0:
        rhs = f"{slope_str} - {abs(intercept)}"
    else:
        rhs = slope_str

    b_str = f"+ {b}" if b >= 0 else f"- {abs(b)}"
    d_str = f"+ {d}" if d >= 0 else f"- {abs(d)}"
    problem = (
        f"Eliminate the parameter for $x = {a}t {b_str}$ and "
        f"$y = {c}t {d_str}$ to express $y$ as a linear function of $x$. "
        f"Write your answer in the form y = mx+b."
    )
    solution = f"$y = {rhs}$"

    x_minus_b = _minus("x", b)
    product = f"{_coef(slope, '')}({x_minus_b})" if b else _coef(slope, "x")
    s = Steps()
    if a == 1:
        s.step(f"Solve $x = {a}t {b_str}$ for $t$.", rf"t = {x_minus_b}")
        s.step(f"Substitute into $y = {c}t {d_str}$.", rf"y = {product} {d_str}")
    else:
        s.step(f"Solve $x = {a}t {b_str}$ for $t$: isolate the $t$ term, then "
               f"divide by ${a}$.",
               rf"t = \frac{{{x_minus_b}}}{{{a}}}")
        s.step(f"Substitute into $y = {c}t {d_str}$; since "
               f"$\\frac{{{c}}}{{{a}}} = {slope}$, the fraction simplifies.",
               rf"y = {c} \cdot \frac{{{x_minus_b}}}{{{a}}} {d_str} = {product} {d_str}")
    if b:
        s.step("Distribute and combine the constants.",
               rf"y = {_line_rhs(slope, -slope * b)} {d_str} = {rhs}")
    elif d == 0:
        s.step("Drop the $+ 0$.", f"y = {rhs}")
    s.answer(solution)
    return problem, solution, s.done()


# --------------------------- unit circle ---------------------------

def _angle_latex(num, den):
    r"""Render ``(num/den) * pi`` as LaTeX: ``0``, ``\pi``, ``3\pi``,
    ``\frac{\pi}{6}``, ``\frac{5\pi}{6}``."""
    if num == 0:
        return "0"
    top = r"\pi" if num == 1 else rf"{num}\pi"
    if den == 1:
        return top
    return rf"\frac{{{top}}}{{{den}}}"


# The 16 standard unit-circle angles in [0, 2*pi), as reduced (num, den) of pi.
_UNIT_ANGLES = [
    (0, 1), (1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4), (5, 6),
    (1, 1), (7, 6), (5, 4), (4, 3), (3, 2), (5, 3), (7, 4), (11, 6),
]
# Tangent is undefined at pi/2 and 3*pi/2.
_TAN_ANGLES = [pair for pair in _UNIT_ANGLES if pair not in ((1, 2), (3, 2))]


def _unit_circle_steps(fn, num, den, solution):
    """Steps evaluating ``fn`` at ``num/den * pi`` via degrees and the reference angle."""
    angle = _angle_latex(num, den)
    deg = num * 180 // den
    s = Steps()
    if num == 0:
        s.step("The angle $0$ points along the positive $x$-axis, at the point "
               "$(1, 0)$ of the unit circle.")
    else:
        s.step("Convert to degrees by multiplying by $\\frac{180^\\circ}{\\pi}$.",
               rf"{angle} \cdot \frac{{180^\circ}}{{\pi}} = {deg}^\circ")
        _reference_step(s, fn, deg)
    s.step("Use the special-angle value.", _exact_trig_line(fn, deg, angle))
    exact = _s_rational(_exact_trig(fn, deg))
    s.answer(solution, lead="The answer is" if exact
             else "Rounded to the nearest thousandth, the answer is")
    return s.done()


@register
@with_variants
def pc_unit_circle_point():
    r"""Coordinates on the Unit Circle

    Give the point ``(cos theta, sin theta)`` at a standard angle. Irrational
    coordinates are rounded to the nearest thousandth.
    """
    num, den = random.choice(_UNIT_ANGLES)
    theta = num * pi / den
    x, y = cos(theta), sin(theta)
    problem = (
        f"Give the coordinates $(x, y)$ of the point on the unit circle at "
        f"angle $\\theta = {_angle_latex(num, den)}$. Round each coordinate to "
        f"the nearest thousandth if it is irrational. Format your answer as "
        f"(x, y)."
    )
    solution = f"({_num(x)}, {_num(y)})"

    deg = num * 180 // den
    cos_v, sin_v = _exact_trig("cos", deg), _exact_trig("sin", deg)
    s = Steps()
    s.step("The point on the unit circle at angle $\\theta$ is "
           "$(\\cos\\theta, \\sin\\theta)$.")
    if num:
        s.step("Convert to degrees by multiplying by $\\frac{180^\\circ}{\\pi}$.",
               rf"{_angle_latex(num, den)} \cdot \frac{{180^\circ}}{{\pi}} = {deg}^\circ")
    if _quadrant(deg) is None:
        s.step(f"${deg}^\\circ$ lies on an axis of the unit circle.",
               rf"(\cos {deg}^\circ, \sin {deg}^\circ) = ({_s_tex(cos_v)}, {_s_tex(sin_v)})")
    else:
        q = _quadrant(deg)
        xs = "+" if q in (1, 4) else "-"
        ys = "+" if q in (1, 2) else "-"
        s.step(f"${deg}^\\circ$ is in Quadrant {_QUADRANT_NAMES[q]}, where $x$ is "
               f"${xs}$ and $y$ is ${ys}$, with reference angle ${_ref_angle(deg)}^\\circ$.",
               rf"(\cos {deg}^\circ, \sin {deg}^\circ) = ({_s_tex(cos_v)}, {_s_tex(sin_v)})")
        s.step("Round each irrational coordinate to the nearest thousandth.",
               rf"\approx ({_num(_s_float(cos_v))}, {_num(_s_float(sin_v))})")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_unit_circle_sin():
    r"""Sine on the Unit Circle

    Evaluate ``sin(theta)`` at a standard angle; irrational values are rounded.
    """
    num, den = random.choice(_UNIT_ANGLES)
    value = sin(num * pi / den)
    problem = (
        f"Evaluate $\\sin\\left({_angle_latex(num, den)}\\right)$. Round your "
        f"answer to the nearest thousandth if it is irrational."
    )
    solution = f"${_num(value)}$"
    return problem, solution, _unit_circle_steps("sin", num, den, solution)


@register
@with_variants
def pc_unit_circle_cos():
    r"""Cosine on the Unit Circle

    Evaluate ``cos(theta)`` at a standard angle; irrational values are rounded.
    """
    num, den = random.choice(_UNIT_ANGLES)
    value = cos(num * pi / den)
    problem = (
        f"Evaluate $\\cos\\left({_angle_latex(num, den)}\\right)$. Round your "
        f"answer to the nearest thousandth if it is irrational."
    )
    solution = f"${_num(value)}$"
    return problem, solution, _unit_circle_steps("cos", num, den, solution)


@register
@with_variants
def pc_unit_circle_tan():
    r"""Tangent on the Unit Circle

    Evaluate ``tan(theta)`` at a standard angle where it is defined (pi/2 and
    3*pi/2 are excluded); irrational values are rounded.
    """
    num, den = random.choice(_TAN_ANGLES)
    value = tan(num * pi / den)
    problem = (
        f"Evaluate $\\tan\\left({_angle_latex(num, den)}\\right)$. Round your "
        f"answer to the nearest thousandth if it is irrational."
    )
    solution = f"${_num(value)}$"
    return problem, solution, _unit_circle_steps("tan", num, den, solution)


# ----------------- quadratic-form trigonometric equation -----------------

# Rational unit-circle values usable as roots of a quadratic in u = sin/cos x.
# Each gives integer-degree solutions of f(x) = value on [0, 360).
_QUADRATIC_ROOTS = [Fraction(-1), Fraction(-1, 2), Fraction(0),
                    Fraction(1, 2), Fraction(1)]


def _degree_solutions(func, value):
    """Integer degrees in ``[0, 360)`` where ``sin``/``cos`` equals ``value``."""
    fn = sin if func == "sin" else cos
    return [d for d in range(360) if abs(fn(radians(d)) - value) < 1e-6]


def _format_quadratic_trig(a, b, c, func):
    r"""Render ``a f^2 + b f + c`` where ``f`` is ``\sin(x)`` or ``\cos(x)``."""
    f = rf"\{func}(x)"
    fsq = rf"\{func}^2(x)"
    if a == 1:
        s = fsq
    elif a == -1:
        s = "-" + fsq
    else:
        s = f"{a}{fsq}"
    if b != 0:
        sign = "+" if b > 0 else "-"
        mag = "" if abs(b) == 1 else str(abs(b))
        s += f"{sign}{mag}{f}"
    if c != 0:
        sign = "+" if c > 0 else "-"
        s += f"{sign}{abs(c)}"
    return s


@register
def pc_trig_quadratic():
    r"""Quadratic-Form Trigonometric Equation (u-substitution)

    Solve ``a*f(x)^2 + b*f(x) + c = 0`` (f = sin or cos) on ``[0, 360)`` degrees
    via the substitution ``u = f(x)``, which turns it into a quadratic in ``u``.
    Roots are drawn from the rational unit-circle values, so every solution is
    an integer number of degrees.
    """
    func = random.choice(["sin", "cos"])
    while True:
        r1 = random.choice(_QUADRATIC_ROOTS)
        r2 = random.choice(_QUADRATIC_ROOTS)
        if not (r1 == 0 and r2 == 0):  # avoid the degenerate u^2 = 0
            break
    # (u - r1)(u - r2) = u^2 - (r1+r2) u + r1 r2, cleared to integer coeffs.
    b_frac = -(r1 + r2)
    c_frac = r1 * r2
    denom = 1
    for fr in (b_frac, c_frac):
        denom = denom * fr.denominator // gcd(denom, fr.denominator)
    a = denom
    b = int(b_frac * denom)
    c = int(c_frac * denom)
    g = gcd(gcd(abs(a), abs(b)), abs(c)) or 1
    a, b, c = a // g, b // g, c // g

    sols = set()
    for r in {r1, r2}:
        sols.update(_degree_solutions(func, float(r)))
    equation = _format_quadratic_trig(a, b, c, func)
    problem = (
        f"Solve ${equation} = 0$ for $x$ in $[0, 360)$ degrees by letting "
        f"$u = \\{func}(x)$ (the equation is quadratic in $u$). List all "
        f"solutions in degrees, comma-separated and in increasing order."
    )
    solution = "$" + ", ".join(str(d) for d in sorted(sols)) + "$"

    roots = sorted({r1, r2})
    factors = [_u_factor(r) for r in roots]
    if len(roots) == 1:
        factored = f"{factors[0]}^2"
    else:
        factored = "".join(sorted(factors, key=lambda f: f != "u"))
    scale = Fraction(a, roots[0].denominator * roots[-1].denominator)
    if scale != 1:
        factored = f"{_tex_fraction(scale)}{factored}"
    s = Steps()
    s.substitute(rf"{_format_poly([(a, 2), (b, 1), (c, 0)], 'u')} = 0",
                 text=f"Let $u = \\{func}(x)$, so the equation becomes a quadratic in $u$.")
    s.step("Factor the quadratic.", f"{factored} = 0")
    s.step("Set each factor equal to $0$." if len(roots) > 1 else "Solve for $u$.",
           r" \quad\text{or}\quad ".join(f"u = {_tex_fraction(r)}" for r in roots))
    lines = []
    for r in roots:
        degs = ", ".join(f"{d}^\\circ" for d in _degree_solutions(func, float(r)))
        lines.append(rf"\{func}(x) = {_tex_fraction(r)} &\Rightarrow x = {degs}")
    s.step(f"Replace $u$ with $\\{func}(x)$ and solve each equation on "
           f"$[0^\\circ, 360^\\circ)$ using the unit circle.",
           r"\begin{aligned}" + r" \\ ".join(lines) + r"\end{aligned}")
    s.answer(solution)
    return problem, solution, s.done()


def _u_factor(root):
    """The integer-coefficient factor ``(qu - p)`` vanishing at ``root = p/q``."""
    if root == 0:
        return "u"
    return f"({_coef(root.denominator, 'u')}{_signed(-root.numerator)})"


# --------------------------- rational functions ---------------------------

def _linear_factor(root):
    """Render ``(x - root)``: 2 -> ``(x-2)``, -3 -> ``(x+3)``, 0 -> ``x``."""
    if root == 0:
        return "x"
    return f"(x-{root})" if root > 0 else f"(x+{-root})"


def _factored(roots, lead=1):
    """Render ``lead * prod (x - root_i)`` in factored form."""
    body = "".join(_linear_factor(r) for r in roots)
    if not body:
        return str(lead)
    if lead == 1:
        return body
    if lead == -1:
        return "-" + body
    return f"{lead}{body}"


def _distinct_ints(k, lo=-4, hi=4, exclude=()):
    """Pick ``k`` distinct integers in ``[lo, hi]`` avoiding ``exclude``."""
    pool = [n for n in range(lo, hi + 1) if n not in exclude]
    return random.sample(pool, k)


def _line_rhs(m, b):
    """Render ``mx + b`` (m != 0) as ``x``, ``-x``, ``2x - 3`` etc."""
    if m == 1:
        s = "x"
    elif m == -1:
        s = "-x"
    else:
        s = f"{m}x"
    if b > 0:
        s += f" + {b}"
    elif b < 0:
        s += f" - {abs(b)}"
    return s


def _rational_with_optional_hole():
    """Numerator/denominator integer roots, with a ~40% chance of one shared
    root (a hole). Used by the vertical-asymptote and zeros generators. When a
    hole is introduced the denominator keeps a genuine second root, so the
    function never degenerates to a fully-cancelling ``(x-a)/(x-a)``."""
    if random.random() < 0.4:
        shared, den_other = _distinct_ints(2)
        den_roots = [shared, den_other]
        if random.random() < 0.5:
            num_roots = [shared]  # reduces to 1/(x - den_other): no zeros
        else:
            num_other = random.choice(
                [n for n in range(-4, 5) if n not in (shared, den_other)])
            num_roots = [shared, num_other]
    else:
        den_roots = _distinct_ints(random.randint(1, 2))
        num_roots = _distinct_ints(random.randint(1, 2), exclude=den_roots)
    return num_roots, den_roots


@register
@with_variants
def pc_rational_vertical_asymptotes():
    r"""Vertical Asymptotes of a Rational Function

    Vertical asymptotes occur at denominator zeros that are *not* cancelled by
    the numerator (those are holes). Presented in factored form with small
    integer roots.
    """
    num_roots, den_roots = _rational_with_optional_hole()
    va = sorted(set(den_roots) - set(num_roots))
    func = f"\\frac{{{_factored(num_roots)}}}{{{_factored(den_roots)}}}"
    problem = (
        f"Find the vertical asymptote(s) of $f(x) = {func}$. List the x-values "
        f"comma-separated in increasing order, or answer none."
    )
    solution = ", ".join(str(v) for v in va) if va else "none"

    s = Steps()
    s.step("A vertical asymptote occurs where the denominator is $0$, unless that "
           "factor cancels with the numerator (then it is a hole).")
    s.step(f"Set each factor of the denominator ${_factored(den_roots)}$ equal to $0$.",
           _or_list(sorted(den_roots)))
    _cancel_steps(s, num_roots, den_roots)
    if va:
        s.step("The remaining denominator zeros are the vertical asymptotes.",
               _or_list(va))
    s.answer(solution)
    return problem, solution, s.done()


def _or_list(values):
    r"""``x = -1 \quad\text{or}\quad x = 3``."""
    return r" \quad\text{or}\quad ".join(f"x = {v}" for v in values)


def _cancel_steps(s, num_roots, den_roots):
    """Add a step for each factor shared by numerator and denominator."""
    for r in sorted(set(num_roots) & set(den_roots)):
        s.step(f"The factor ${_linear_factor(r)}$ is in both the numerator and the "
               f"denominator, so it cancels: $x = {r}$ is a hole, not an asymptote "
               f"or a zero.")


@register
@with_variants
def pc_rational_zeros():
    r"""Zeros of a Rational Function

    The real zeros are numerator zeros that are not also denominator zeros (a
    shared root is a hole, not a zero).
    """
    num_roots, den_roots = _rational_with_optional_hole()
    zeros = sorted(set(num_roots) - set(den_roots))
    func = f"\\frac{{{_factored(num_roots)}}}{{{_factored(den_roots)}}}"
    problem = (
        f"Find the real zero(s) of $f(x) = {func}$. List the x-values "
        f"comma-separated in increasing order, or answer none."
    )
    solution = ", ".join(str(z) for z in zeros) if zeros else "none"

    s = Steps()
    s.step("A rational function is $0$ where its numerator is $0$, as long as the "
           "denominator is not also $0$ there.")
    s.step(f"Set each factor of the numerator ${_factored(num_roots)}$ equal to $0$.",
           _or_list(sorted(num_roots)))
    _cancel_steps(s, num_roots, den_roots)
    if zeros:
        s.step("The remaining numerator zeros are the zeros of $f$.", _or_list(zeros))
    else:
        s.step("No numerator zeros remain, so $f$ has no real zeros.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_rational_holes():
    r"""Holes of a Rational Function

    A shared linear factor cancels, leaving a hole. Its coordinates are the
    shared root and the reduced function's value there (a small fraction).
    """
    shared = random.choice(range(-4, 5))
    den_other = random.choice([n for n in range(-4, 5) if n != shared])
    if random.random() < 0.6:
        num_other = random.choice(
            [n for n in range(-4, 5) if n not in (shared, den_other)])
        num_roots = [shared, num_other]
        num_others = [num_other]
    else:
        num_roots = [shared]
        num_others = []
    den_roots = [shared, den_other]
    y = Fraction(1)
    for r in num_others:
        y *= (shared - r)
    y /= (shared - den_other)
    func = f"\\frac{{{_factored(num_roots)}}}{{{_factored(den_roots)}}}"
    problem = (
        f"The graph of $f(x) = {func}$ has a hole. Find its coordinates. "
        f"Format your answer as (x, y); give y as an integer or fraction a/b."
    )
    solution = f"({shared}, {_frac_from(y)})"

    reduced = rf"\frac{{{_factored(num_others)}}}{{{_linear_factor(den_other)}}}"
    top = 1
    for r in num_others:
        top *= shared - r
    plugged_top = "".join(_at(shared, r) for r in num_others) or "1"
    s = Steps()
    s.step(f"The factor ${_linear_factor(shared)}$ appears in both the numerator and "
           f"the denominator. Cancel it.",
           rf"f(x) = {reduced}, \quad x \ne {shared}")
    s.step(f"The hole is at $x = {shared}$, where the cancelled factor is $0$.")
    bottom = shared - den_other
    value = rf"y = \frac{{{plugged_top}}}{{{_at(shared, den_other)}}} = {_divide(top, bottom)}"
    s.step(f"Find the $y$-coordinate by substituting $x = {shared}$ into the "
           f"simplified function.", value)
    s.answer(solution)
    return problem, solution, s.done()


def _at(x_value, root):
    """The factor ``(x - root)`` evaluated at ``x = x_value``, unsimplified."""
    if root == 0:
        return f"({x_value})"
    return f"({x_value} - {root})" if root > 0 else f"({x_value} + {-root})"


@register
@with_variants
def pc_rational_horizontal_asymptote():
    r"""Horizontal Asymptote of a Rational Function

    Compares degrees: lower numerator degree -> ``y = 0``; equal -> ratio of
    leading coefficients; higher numerator degree -> none. Numerator and
    denominator roots are disjoint so the degrees are genuine.
    """
    case = random.choice(["zero", "equal", "none"])
    if case == "zero":
        num_deg, den_deg = 1, 2
    elif case == "equal":
        num_deg = den_deg = random.randint(1, 2)
    else:
        num_deg, den_deg = 2, 1
    num_roots = _distinct_ints(num_deg)
    den_roots = _distinct_ints(den_deg, exclude=num_roots)
    lead_num = random.choice([1, 2, 3, -1, -2, -3])
    lead_den = random.choice([1, 2, 3])
    func = (f"\\frac{{{_factored(num_roots, lead_num)}}}"
            f"{{{_factored(den_roots, lead_den)}}}")
    if case == "zero":
        solution = "0"
    elif case == "equal":
        solution = _frac_from(Fraction(lead_num, lead_den))
    else:
        solution = "none"
    problem = (
        f"Find the horizontal asymptote of $f(x) = {func}$. If it is $y = c$, "
        f"give c as an integer or fraction a/b; if there is none, answer none."
    )

    def lead_term(lead, deg):
        return _coef(lead, "x" if deg == 1 else f"x^{deg}")

    s = Steps()
    s.step(f"Compare degrees. Multiplied out, the numerator's leading term is "
           f"${lead_term(lead_num, num_deg)}$ (degree ${num_deg}$) and the "
           f"denominator's is ${lead_term(lead_den, den_deg)}$ (degree ${den_deg}$).")
    if case == "zero":
        s.step("The numerator has the smaller degree, so $f(x) \\to 0$ as "
               "$x \\to \\pm\\infty$.", "y = 0")
    elif case == "equal":
        s.step("The degrees are equal, so the asymptote is the ratio of the "
               "leading coefficients.", f"y = {_divide(lead_num, lead_den)}")
    else:
        s.step("The numerator has the larger degree, so $f(x)$ grows without "
               "bound as $x \\to \\pm\\infty$ and there is no horizontal asymptote.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_rational_slant_asymptote():
    r"""Slant (Oblique) Asymptote of a Rational Function

    Numerator degree is one more than the (linear) denominator, so polynomial
    division gives a line ``y = mx + b`` plus a proper remainder. Built as
    ``num = (mx + b)(x - q) + r`` with a nonzero remainder ``r`` (so it is a
    genuine slant, not exact division).
    """
    m = random.choice([1, 2, -1, -2])
    b = random.randint(-4, 4)
    q = random.choice([n for n in range(-4, 5) if n != 0])
    r = random.choice([n for n in range(-5, 6) if n != 0])
    a2, a1, a0 = m, b - m * q, r - b * q
    num_poly = _format_poly([(a2, 2), (a1, 1), (a0, 0)], "x")
    den_poly = _linear_factor(q)
    func = f"\\frac{{{num_poly}}}{{{den_poly}}}"
    problem = (
        f"Find the slant (oblique) asymptote of $f(x) = {func}$. "
        f"Write your answer in the form y = mx+b."
    )
    solution = f"y = {_line_rhs(m, b)}"

    remainder = (rf" + \frac{{{r}}}{{{den_poly}}}" if r > 0
                 else rf" - \frac{{{-r}}}{{{den_poly}}}")
    s = Steps()
    s.step("The numerator's degree is one more than the denominator's, so divide: "
           "the quotient is the slant asymptote.")
    s.step(f"Divide by ${den_poly}$ with synthetic division, using ${q}$ and the "
           f"coefficients ${a2}, {a1}, {a0}$. Bring down ${a2}$, then multiply by "
           f"${q}$ and add to the next coefficient each time.",
           rf"{a2}({q}) + {paren(a1)} = {b}, \quad {b}({q}) + {paren(a0)} = {r}")
    s.step(f"So the quotient is ${_line_rhs(m, b)}$ with remainder ${r}$.",
           rf"\frac{{{num_poly}}}{{{den_poly}}} = {_line_rhs(m, b)}{remainder}")
    s.step("As $x \\to \\pm\\infty$ the remainder fraction goes to $0$, so the graph "
           "approaches the line given by the quotient.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def pc_rational_y_intercept():
    r"""Y-Intercept of a Rational Function

    Evaluates ``f(0) = num(0)/den(0)``. Zero is excluded as a denominator root
    (so ``f(0)`` is defined) and roots/leading coefficients are small, so the
    y-value is a small integer or fraction.
    """
    num_roots = _distinct_ints(random.randint(1, 2))
    den_roots = _distinct_ints(random.randint(1, 2), exclude=[0] + num_roots)
    lead_num = random.choice([1, 2, -1, -2])
    lead_den = random.choice([1, 2])
    num0 = lead_num
    for root in num_roots:
        num0 *= (0 - root)
    den0 = lead_den
    for root in den_roots:
        den0 *= (0 - root)
    y = Fraction(num0, den0)
    func = (f"\\frac{{{_factored(num_roots, lead_num)}}}"
            f"{{{_factored(den_roots, lead_den)}}}")
    problem = (
        f"Find the y-intercept of $f(x) = {func}$. Give the y-value as an "
        f"integer or fraction a/b."
    )
    solution = _frac_from(y)

    def plugged(roots, lead):
        return ("" if lead == 1 else paren(lead)) + "".join(_at(0, r) for r in roots)

    s = Steps()
    s.step("The $y$-intercept is where the graph crosses the $y$-axis, at $x = 0$. "
           "Evaluate $f(0)$.",
           rf"f(0) = \frac{{{plugged(num_roots, lead_num)}}}{{{plugged(den_roots, lead_den)}}}")
    s.step("Multiply out the numerator and denominator, then simplify.",
           rf"f(0) = {_divide(num0, den0)}")
    s.answer(solution, lead=f"The $y$-intercept is $(0, {_tex_fraction(y)})$, so the "
                            f"answer is")
    return problem, solution, s.done()


@register
@with_variants
def pc_rational_inequality():
    r"""Rational Inequality

    Solve ``(x - z)/(x - p) [rel] 0`` for one numerator zero ``z`` and one
    vertical asymptote ``p``. The sign chart gives a union of two rays (for
    ``>``/``>=``) or a single interval (for ``<``/``<=``); the numerator zero is
    included only for the non-strict relations, the asymptote never is.
    """
    z, p = _distinct_ints(2)
    relation = random.choice([">", ">=", "<", "<="])
    lo, hi = sorted([z, p])
    if relation in (">", ">="):
        inc_lo = relation == ">=" and lo == z
        inc_hi = relation == ">=" and hi == z
        left = f"x {'<=' if inc_lo else '<'} {lo}"
        right = f"x {'>=' if inc_hi else '>'} {hi}"
        solution = f"{left} or {right}"
    else:
        inc_lo = relation == "<=" and lo == z
        inc_hi = relation == "<=" and hi == z
        solution = f"{lo} {'<=' if inc_lo else '<'} x {'<=' if inc_hi else '<'} {hi}"
    rel_latex = {">": ">", ">=": r"\ge", "<": "<", "<=": r"\le"}[relation]
    problem = (
        f"Solve $\\frac{{{_linear_factor(z)}}}{{{_linear_factor(p)}}} "
        f"{rel_latex} 0$. Express your solution as an inequality in x using "
        f"'<', '<=', '>', '>=' and 'or' for a union "
        f"(e.g. 'x < -2 or x >= 1' or '-2 < x <= 1')."
    )

    s = Steps()
    s.step(f"Find the critical values: the numerator is $0$ at $x = {z}$ and the "
           f"denominator is $0$ at $x = {p}$.")
    s.step(f"Test the sign on each interval. For $x < {lo}$ both factors are "
           f"negative, between ${lo}$ and ${hi}$ they have opposite signs, and for "
           f"$x > {hi}$ both are positive.",
           rf"x < {lo}: +, \quad {lo} < x < {hi}: -, \quad x > {hi}: +")
    if relation in (">", ">="):
        s.step("The quotient must be positive, so keep the two outer intervals.")
    else:
        s.step("The quotient must be negative, so keep the middle interval.")
    zero_note = ("is included because the quotient equals $0$ there"
                 if relation in (">=", "<=") else
                 "is excluded because the inequality is strict")
    pretty = (solution.replace("<=", r"\le").replace(">=", r"\ge")
              .replace(" or ", r" \text{ or } "))
    s.step(f"Check the endpoints: $x = {z}$ {zero_note}; $x = {p}$ is always "
           f"excluded because it makes the denominator $0$.", pretty)
    s.answer(solution)
    return problem, solution, s.done()


# --------------------------- sinusoids ---------------------------

@register
@with_variants
def pc_sinusoid_features():
    r"""Sinusoid Features

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | For $y = 3\sin(2x - 4) + 5$, state the amplitude as an integer. | $3$ |
    """
    A = random.choice([i for i in range(-6, 7) if i != 0])
    B = random.randint(1, 6)
    C = random.choice([i for i in range(-8, 9) if i != 0])
    D = random.randint(-6, 6)
    trig = random.choice(["sin", "cos"])
    feature = random.choice(["amplitude", "period", "midline", "phase shift"])

    b_term = "x" if B == 1 else f"{B}x"
    inner = f"{b_term} - {C}" if C > 0 else f"{b_term} + {abs(C)}"
    if D > 0:
        tail = f" + {D}"
    elif D < 0:
        tail = f" - {abs(D)}"
    else:
        tail = ""
    if A == 1:
        amp_str = ""
    elif A == -1:
        amp_str = "-"
    else:
        amp_str = str(A)
    equation = f"y = {amp_str}\\{trig}({inner}){tail}"

    if feature == "amplitude":
        ask = "state the amplitude as an integer"
        solution = f"${abs(A)}$"
    elif feature == "period":
        ask = ("state the period, rounded to the nearest thousandth")
        solution = f"${_num(2 * pi / B)}$"
    elif feature == "midline":
        ask = "give the equation of the midline in the form y = c"
        solution = f"$y = {D}$"
    else:  # phase shift
        ask = ("state the phase shift (a positive value denotes a shift to the "
               "right) as an integer or fraction a/b")
        solution = f"${_frac_from(Fraction(C, B))}$"
    problem = f"For ${equation}$, {ask}."

    s = Steps()
    s.step(f"Match ${equation}$ to $y = A\\{trig}(Bx - C) + D$: here $A = {A}$, "
           f"$B = {B}$, $C = {C}$, and $D = {D}$"
           + (f" (since ${inner} = {b_term} - ({C})$)." if C < 0 else "."))
    if feature == "amplitude":
        s.step("The amplitude is $|A|$, the distance from the midline to a peak.",
               f"|{A}| = {abs(A)}")
    elif feature == "period":
        s.step("The period is $\\frac{2\\pi}{B}$.",
               rf"\frac{{2\pi}}{{{B}}} \approx {_num(2 * pi / B)}")
    elif feature == "midline":
        s.step("The midline is the horizontal line halfway between the maximum "
               "and minimum, $y = D$.", f"y = {D}")
    else:
        s.step("Factor $B$ out of the inside to read off the shift: "
               "$Bx - C = B\\left(x - \\frac{C}{B}\\right)$, so the phase shift is "
               "$\\frac{C}{B}$.")
        direction = "right" if C > 0 else "left"
        s.substitute(rf"\frac{{C}}{{B}} = {_divide(C, B)}",
                     text=f"Substitute. The value is "
                          f"{'positive' if C > 0 else 'negative'}, so the "
                          f"shift is to the {direction}.")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is"
             if feature == "period" else "The answer is")
    return problem, solution, s.done()


# --------------------- sum/difference & half-angle ---------------------

_SPECIAL_ANGLES = [30, 45, 60, 90, 120, 135, 150]


@register
@with_variants
def pc_sum_difference_values():
    r"""Sum and Difference Formula Values

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the exact value of $\sin(45^\circ + 30^\circ)$. Round to the nearest thousandth if irrational. | $0.966$ |
    """
    fn_name = random.choice(["sin", "cos", "tan"])
    fn = {"sin": sin, "cos": cos, "tan": tan}[fn_name]
    a, b, op, angle = 45, 30, "+", 75
    for _ in range(100):
        a = random.choice(_SPECIAL_ANGLES)
        b = random.choice(_SPECIAL_ANGLES)
        op = random.choice(["+", "-"])
        angle = a + b if op == "+" else a - b
        if fn_name == "tan" and angle % 180 == 90:
            continue
        break
    value = fn(radians(angle))
    problem = (
        f"Find the exact value of $\\{fn_name}({a}^\\circ {op} {b}^\\circ)$ "
        f"using a sum or difference identity. "
        f"Round to the nearest thousandth if irrational."
    )
    solution = f"${_num(value)}$"

    opp = "-" if op == "+" else "+"
    lhs = rf"\{fn_name}({a}^\circ {op} {b}^\circ)"
    s = Steps()
    if fn_name == "tan" and 90 in (a, b):
        s.step("$\\tan 90^\\circ$ is undefined, so the tangent identity can't be "
               "used. Instead use $\\tan\\theta = \\frac{\\sin\\theta}{\\cos\\theta}$ "
               "with the sine and cosine identities.")
        parts = {}
        for f in ("sin", "cos"):
            substituted, _, total = _sum_diff_expansion(f, a, b, op)
            parts[f] = total
            s.step(f"Expand $\\{f}({a}^\\circ {op} {b}^\\circ)$.",
                   rf"\{f}({a}^\circ {op} {b}^\circ) = {substituted} = {_s_tex(total)}")
        final = _quotient_steps(s, lhs, parts["sin"], parts["cos"],
                                "Write the tangent as the sine over the cosine.")
    elif fn_name == "tan":
        s.formula("The tangent sum/difference identity",
                  rf"\tan(A {op} B) = \frac{{\tan A {op} \tan B}}{{1 {opp} \tan A\tan B}}")
        ta, tb = _exact_trig("tan", a), _exact_trig("tan", b)
        top = _s_add(ta, _s_scale(tb, 1 if op == "+" else -1))
        bottom = _s_add({1: Fraction(1)}, _s_scale(_s_mul(ta, tb), -1 if op == "+" else 1))
        s.substitute(rf"{lhs} = \frac{{{_s_tex(ta)} {op} {_wrap(_s_tex(tb))}}}"
                     rf"{{1 {opp} \left({_s_tex(ta)}\right)\left({_s_tex(tb)}\right)}}",
                     text=f"Substitute $\\tan {a}^\\circ = {_s_tex(ta)}$"
                          + (" for both angles." if a == b else
                             f" and $\\tan {b}^\\circ = {_s_tex(tb)}$."))
        final = _quotient_steps(s, lhs, top, bottom,
                                "Simplify the numerator and the denominator.")
    else:
        if fn_name == "sin":
            s.formula("The sine sum/difference identity",
                      rf"\sin(A {op} B) = \sin A\cos B {op} \cos A\sin B")
        else:
            s.formula("The cosine sum/difference identity",
                      rf"\cos(A {op} B) = \cos A\cos B {opp} \sin A\sin B")
        substituted, multiplied, final = _sum_diff_expansion(fn_name, a, b, op)
        s.substitute(rf"{lhs} = {substituted}",
                     text=f"Substitute the special-angle values for $A = {a}^\\circ$ "
                          f"and $B = {b}^\\circ$.")
        s.step("Multiply, then combine.", rf"{lhs} = {multiplied} = {_approx(final)}")
    s.answer(solution, lead="The answer is" if _s_rational(final)
             else "Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


def _sum_diff_expansion(fn, a, b, op):
    """Expand ``fn(a op b)`` (sin or cos) with exact special-angle values.

    Returns the substituted products, the multiplied-out terms (both LaTeX) and
    the exact total as a surd.
    """
    sa, ca = _exact_trig("sin", a), _exact_trig("cos", a)
    sb, cb = _exact_trig("sin", b), _exact_trig("cos", b)
    if fn == "sin":
        first, second, join = (sa, cb), (ca, sb), op
    else:
        first, second, join = (ca, cb), (sa, sb), "-" if op == "+" else "+"

    def factors(pair):
        return "".join(rf"\left({_s_tex(x)}\right)" for x in pair)

    p1, p2 = _s_mul(*first), _s_mul(*second)
    total = _s_add(p1, _s_scale(p2, 1 if join == "+" else -1))
    substituted = f"{factors(first)} {join} {factors(second)}"
    multiplied = f"{_s_tex(p1)} {join} {_wrap(_s_tex(p2))}"
    return substituted, multiplied, total


_HALF_FULL_ANGLES = [30, 45, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]


@register
@with_variants
def pc_half_angle_values():
    r"""Half-Angle Formula Values

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the exact value of $\cos\left(\frac{30^\circ}{2}\right)$. Round to the nearest thousandth if irrational. | $0.966$ |
    """
    fn_name = random.choice(["sin", "cos", "tan"])
    fn = {"sin": sin, "cos": cos, "tan": tan}[fn_name]
    full, half = 45, 22.5
    for _ in range(100):
        full = random.choice(_HALF_FULL_ANGLES)
        half = full / 2
        if fn_name == "tan" and half % 180 == 90:
            continue
        break
    value = fn(radians(half))
    problem = (
        f"Find the exact value of "
        f"$\\{fn_name}\\left(\\frac{{{full}^\\circ}}{{2}}\\right)$ using a "
        f"half-angle identity. Round to the nearest thousandth if irrational."
    )
    solution = f"${_num(value)}$"

    cos_full, sin_full = _exact_trig("cos", full), _exact_trig("sin", full)
    lhs = rf"\{fn_name}\left(\frac{{{full}^\circ}}{{2}}\right)"
    half_tex = f"{_num(half)}^\\circ"
    s = Steps()
    if fn_name == "tan":
        s.formula("The half-angle identity for tangent",
                  r"\tan\frac{\theta}{2} = \frac{1 - \cos\theta}{\sin\theta}")
        top = _s_add({1: Fraction(1)}, _s_scale(cos_full, -1))
        s.substitute(rf"{lhs} = \frac{{1 - {_wrap(_s_tex(cos_full))}}}{{{_s_tex(sin_full)}}}",
                     text=f"Substitute $\\cos {full}^\\circ = {_s_tex(cos_full)}$ and "
                          f"$\\sin {full}^\\circ = {_s_tex(sin_full)}$.")
        final = _quotient_steps(s, lhs, top, sin_full, "Simplify the numerator.")
        exact = _s_rational(final)
    else:
        sign_op = "-" if fn_name == "sin" else "+"
        s.formula(f"The half-angle identity for {_FN_NAMES[fn_name]}",
                  rf"\{fn_name}\frac{{\theta}}{{2}} = \pm\sqrt{{\frac{{1 {sign_op} "
                  rf"\cos\theta}}{{2}}}}")
        negative = fn_name == "cos" and half > 90
        if fn_name == "cos" and half == 90:
            s.step("Here $\\frac{\\theta}{2} = 90^\\circ$, on an axis; the value "
                   "under the root will be $0$, so the sign doesn't matter.")
        else:
            where = ("lies on the positive $y$-axis" if half == 90 else
                     f"is in Quadrant {'I' if half < 90 else 'II'}")
            s.step(f"Choose the sign: ${half_tex}$ {where}, where "
                   f"{_FN_NAMES[fn_name]} is {'negative' if negative else 'positive'}.")
        inside = _s_scale(_s_add({1: Fraction(1)},
                                 _s_scale(cos_full, -1 if fn_name == "sin" else 1)),
                          Fraction(1, 2))
        sign = "-" if negative else ""
        s.substitute(rf"{lhs} = {sign}\sqrt{{\frac{{1 {sign_op} {_wrap(_s_tex(cos_full))}}}{{2}}}}",
                     text=f"Substitute $\\cos {full}^\\circ = {_s_tex(cos_full)}$.")
        line = rf"{lhs} = {sign}\sqrt{{{_s_tex(inside)}}}"
        if _s_rational(inside):
            # sqrt(p/q) = sqrt(pq)/q, simplified.
            p_q = inside.get(1, Fraction(0))
            root = _surd([(Fraction(1, p_q.denominator), p_q.numerator * p_q.denominator)])
            root = _s_scale(root, -1 if negative else 1)
            line += f" = {_approx(root)}"
            exact = _s_rational(root)
        else:
            line += rf" \approx {_num(value)}"
            exact = False
        s.step("Simplify inside the square root, then evaluate.", line)
    s.answer(solution, lead="The answer is" if exact
             else "Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


# --------------------- binomial theorem & complex ---------------------

@register
@with_variants
def pc_binomial_term():
    r"""Binomial Theorem Term

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the coefficient of the $x^2$ term in the expansion of $(2x + 3)^4$. Give your answer as an integer. | $216$ |
    """
    n = random.randint(3, 6)
    k = random.randint(1, n)
    a = random.choice([1, 2, -1, -2])
    b = random.choice([1, 2, 3, -1, -2, -3])
    coeff = comb(n, k) * a ** k * b ** (n - k)
    if a == 1:
        ax = "x"
    elif a == -1:
        ax = "-x"
    else:
        ax = f"{a}x"
    bpart = f" + {b}" if b > 0 else f" - {abs(b)}"
    base = f"({ax}{bpart})"
    xk = "x" if k == 1 else f"x^{{{k}}}"
    problem = (
        f"Find the coefficient of the ${xk}$ term in the expansion of "
        f"${base}^{{{n}}}$. Give your answer as an integer."
    )
    solution = f"${coeff}$"

    s = Steps()
    s.step(f"By the Binomial Theorem, the term of $(ax + b)^n$ containing $x^k$ is "
           f"$\\binom{{n}}{{k}}(ax)^k b^{{n-k}}$. Here $a = {a}$, $b = {b}$, $n = {n}$, "
           f"and $k = {k}$.",
           rf"\binom{{{n}}}{{{k}}}({ax})^{{{k}}}({b})^{{{n - k}}}")
    s.step("Evaluate the binomial coefficient.",
           rf"\binom{{{n}}}{{{k}}} = \frac{{{n}!}}{{{k}!\,{n - k}!}} = {comb(n, k)}")
    s.step(f"The coefficient is $\\binom{{{n}}}{{{k}}} \\cdot a^{{{k}}} \\cdot b^{{{n - k}}}$.",
           rf"{comb(n, k)} \cdot {paren(a)}^{{{k}}} \cdot {paren(b)}^{{{n - k}}} = "
           rf"{comb(n, k)} \cdot {paren(a ** k)} \cdot {paren(b ** (n - k))} = {coeff}")
    s.answer(solution)
    return problem, solution, s.done()


def _complex_str(a, b):
    """Render a complex number as a typeable ``a+bi`` / ``a-bi`` string."""
    a_s, b_s = _num(a), _num(b)
    if b_s.startswith("-"):
        return f"{a_s}-{b_s[1:]}i"
    return f"{a_s}+{b_s}i"


@register
@with_variants
def pc_de_moivre():
    r"""De Moivre's Theorem

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Use De Moivre's Theorem to evaluate $\left(2(\cos 30^\circ + i\sin 30^\circ)\right)^3$. | $0+8i$ |
    """
    r = random.randint(1, 4)
    theta = random.choice([0, 30, 45, 60, 90, 120, 135, 150, 180,
                           210, 225, 240, 270, 300, 315, 330])
    n = random.randint(2, 4)
    mag = r ** n
    ang = radians(n * theta)
    x = mag * cos(ang)
    y = mag * sin(ang)
    problem = (
        f"Use De Moivre's Theorem to evaluate "
        f"$\\left({r}(\\cos {theta}^\\circ + i\\sin {theta}^\\circ)\\right)"
        f"^{{{n}}}$. Express your answer in rectangular form a+bi, rounding "
        f"each part to the nearest thousandth if necessary."
    )
    solution = f"${_complex_str(x, y)}$"

    total = n * theta
    angle = total % 360
    cos_v, sin_v = _exact_trig("cos", angle), _exact_trig("sin", angle)
    s = Steps()
    s.formula("De Moivre's Theorem",
              r"\left(r(\cos\theta + i\sin\theta)\right)^n = r^n(\cos n\theta + i\sin n\theta)")
    s.substitute(rf"{r}^{{{n}}}\left(\cos({n} \cdot {theta}^\circ) + i\sin({n} \cdot "
                 rf"{theta}^\circ)\right) = {mag}(\cos {total}^\circ + i\sin {total}^\circ)")
    if total >= 360:
        s.step(f"Subtract multiples of $360^\\circ$ to get a coterminal angle: "
               f"${total}^\\circ$ is coterminal with ${angle}^\\circ$.")
    s.step("Use the special-angle values.",
           rf"\cos {angle}^\circ = {_s_tex(cos_v)}, \quad \sin {angle}^\circ = {_s_tex(sin_v)}")
    x_v, y_v = _s_scale(cos_v, mag), _s_scale(sin_v, mag)
    y_tex = _s_tex(y_v)
    rect = (f"{_s_tex(x_v)} - {y_tex[1:]}i" if y_tex.startswith("-")
            else f"{_s_tex(x_v)} + {y_tex}i")
    line = rf"{mag}\left({_s_tex(cos_v)} + {_wrap(_s_tex(sin_v))}i\right) = {rect}"
    if not (_s_rational(x_v) and _s_rational(y_v)):
        line += rf" \approx {_complex_str(x, y)}"
    s.step(f"Distribute ${mag}$.", line)
    s.answer(solution)
    return problem, solution, s.done()


# --------------------- trig-identity simplification ---------------------

# Fixed set of identity simplifications, each an (LHS LaTeX, typeable answer)
# pair with a known simple result. The answer is either an integer or a single
# trig function of x; correctness is verified numerically at sample x.
_TRIG_IDENTITIES = [
    (r"\sin^2(x) + \cos^2(x)", "1"),
    (r"\sec^2(x) - \tan^2(x)", "1"),
    (r"\csc^2(x) - \cot^2(x)", "1"),
    (r"\csc(x)\sin(x)", "1"),
    (r"\sec(x)\cos(x)", "1"),
    (r"\cot(x)\tan(x)", "1"),
    (r"\tan(x)\cos(x)", "sin(x)"),
    (r"\cot(x)\sin(x)", "cos(x)"),
    (r"\frac{\sin(x)}{\cos(x)}", "tan(x)"),
    (r"\frac{\cos(x)}{\sin(x)}", "cot(x)"),
    (r"\frac{1}{\sec(x)}", "cos(x)"),
    (r"\frac{1}{\csc(x)}", "sin(x)"),
]


@register
@with_variants
def pc_simplify_trig_identity():
    r"""Simplify Using Trig Identities

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify the expression $\tan(x)\cos(x)$ using trigonometric identities. Write your answer as an integer or a single trig function of x such as sin(x). | $sin(x)$ |
    """
    lhs, ans = random.choice(_TRIG_IDENTITIES)
    problem = (
        f"Simplify the expression ${lhs}$ using trigonometric identities. "
        f"Write your answer as an integer or a single trig function of x such "
        f"as sin(x), cos(x), tan(x), or cot(x)."
    )
    solution = f"${ans}$"
    s = Steps()
    for text, math in _TRIG_IDENTITY_STEPS[lhs]:
        s.step(text, math)
    s.answer(solution)
    return problem, solution, s.done()


# Worked steps for each entry of ``_TRIG_IDENTITIES``, keyed by its LHS.
_TRIG_IDENTITY_STEPS = {
    r"\sin^2(x) + \cos^2(x)": [
        ("This is the Pythagorean identity.", r"\sin^2(x) + \cos^2(x) = 1"),
    ],
    r"\sec^2(x) - \tan^2(x)": [
        ("Start from the Pythagorean identity $1 + \\tan^2(x) = \\sec^2(x)$.", None),
        ("Subtract $\\tan^2(x)$ from both sides.", r"\sec^2(x) - \tan^2(x) = 1"),
    ],
    r"\csc^2(x) - \cot^2(x)": [
        ("Start from the Pythagorean identity $1 + \\cot^2(x) = \\csc^2(x)$.", None),
        ("Subtract $\\cot^2(x)$ from both sides.", r"\csc^2(x) - \cot^2(x) = 1"),
    ],
    r"\csc(x)\sin(x)": [
        ("Use the reciprocal identity $\\csc(x) = \\frac{1}{\\sin(x)}$.",
         r"\csc(x)\sin(x) = \frac{1}{\sin(x)} \cdot \sin(x) = 1"),
    ],
    r"\sec(x)\cos(x)": [
        ("Use the reciprocal identity $\\sec(x) = \\frac{1}{\\cos(x)}$.",
         r"\sec(x)\cos(x) = \frac{1}{\cos(x)} \cdot \cos(x) = 1"),
    ],
    r"\cot(x)\tan(x)": [
        ("Use the reciprocal identity $\\cot(x) = \\frac{1}{\\tan(x)}$.",
         r"\cot(x)\tan(x) = \frac{1}{\tan(x)} \cdot \tan(x) = 1"),
    ],
    r"\tan(x)\cos(x)": [
        ("Use the quotient identity $\\tan(x) = \\frac{\\sin(x)}{\\cos(x)}$.",
         r"\tan(x)\cos(x) = \frac{\sin(x)}{\cos(x)} \cdot \cos(x)"),
        ("Cancel $\\cos(x)$.", r"\tan(x)\cos(x) = \sin(x)"),
    ],
    r"\cot(x)\sin(x)": [
        ("Use the quotient identity $\\cot(x) = \\frac{\\cos(x)}{\\sin(x)}$.",
         r"\cot(x)\sin(x) = \frac{\cos(x)}{\sin(x)} \cdot \sin(x)"),
        ("Cancel $\\sin(x)$.", r"\cot(x)\sin(x) = \cos(x)"),
    ],
    r"\frac{\sin(x)}{\cos(x)}": [
        ("This is the quotient identity for tangent.",
         r"\frac{\sin(x)}{\cos(x)} = \tan(x)"),
    ],
    r"\frac{\cos(x)}{\sin(x)}": [
        ("This is the quotient identity for cotangent.",
         r"\frac{\cos(x)}{\sin(x)} = \cot(x)"),
    ],
    r"\frac{1}{\sec(x)}": [
        ("Secant is the reciprocal of cosine, $\\sec(x) = \\frac{1}{\\cos(x)}$, so "
         "its reciprocal is cosine.", r"\frac{1}{\sec(x)} = \cos(x)"),
    ],
    r"\frac{1}{\csc(x)}": [
        ("Cosecant is the reciprocal of sine, $\\csc(x) = \\frac{1}{\\sin(x)}$, so "
         "its reciprocal is sine.", r"\frac{1}{\csc(x)} = \sin(x)"),
    ],
}


# --------------------- recursive sequences ---------------------

@register
@with_variants
def pc_recursive_sequence_term():
    r"""Recursive Sequence Nth Term

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A sequence is defined by $a_1 = 3$ and $a_n = 2a_{n-1} + 1$ for $n \ge 2$. Find $a_{4}$. Give your answer as an integer. | $31$ |
    """
    a1 = random.randint(-9, 9)
    r = random.choice([-2, -1, 1, 2, 3])
    d = random.choice([i for i in range(-9, 10) if i != 0])
    n = random.randint(2, 5)
    value = a1
    for _ in range(n - 1):
        value = value * r + d
    if r == 1:
        coeff = ""
    elif r == -1:
        coeff = "-"
    else:
        coeff = str(r)
    d_str = f"+ {d}" if d > 0 else f"- {abs(d)}"
    problem = (
        f"A sequence is defined by $a_1 = {a1}$ and "
        f"$a_n = {coeff}a_{{n-1}} {d_str}$ for $n \\ge 2$. Find $a_{{{n}}}$. "
        f"Give your answer as an integer."
    )
    solution = f"${value}$"

    s = Steps()
    change = f"plus ${d}$" if d > 0 else f"minus ${-d}$"
    previous = "the previous term" if r == 1 else f"${r}$ times the previous term"
    s.step(f"Each term is {previous}, {change}. Start from $a_1 = {a1}$ and apply "
           f"the rule one term at a time.")
    term = a1
    for i in range(2, n + 1):
        new = term * r + d
        s.step(f"Find $a_{{{i}}}$.",
               rf"a_{{{i}}} = {coeff}a_{{{i - 1}}} {d_str} = {coeff}({term}) {d_str} = {new}")
        term = new
    s.answer(solution)
    return problem, solution, s.done()


# --------------------- partial fractions ---------------------

@register
@with_variants
def pc_partial_fractions():
    r"""Partial Fraction Decomposition

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Decompose $\frac{5x-7}{(x-2)(x-1)}$ into partial fractions of the form $\frac{A}{x-2} + \frac{B}{x-1}$. Find the numerator placed over the factor $(x-2)$. Give your answer as an integer or fraction a/b. | $3$ |
    """
    p, q = _distinct_ints(2, lo=-5, hi=5, exclude=(0,))
    a0 = random.choice([i for i in range(-6, 7) if i != 0])  # over (x - p)
    b0 = random.choice([i for i in range(-6, 7) if i != 0])  # over (x - q)
    # numerator = a0*(x - q) + b0*(x - p) = (a0+b0)x - (a0*q + b0*p)
    lin = a0 + b0
    const = -(a0 * q + b0 * p)
    num_poly = _format_poly([(lin, 1), (const, 0)], "x")
    den_poly = f"{_linear_factor(p)}{_linear_factor(q)}"
    if random.random() < 0.5:
        target, answer = p, a0
    else:
        target, answer = q, b0
    problem = (
        f"Decompose $\\frac{{{num_poly}}}{{{den_poly}}}$ into partial fractions "
        f"of the form $\\frac{{A}}{{{_linear_factor(p)}}} + "
        f"\\frac{{B}}{{{_linear_factor(q)}}}$. Find the numerator placed over "
        f"the factor ${_linear_factor(target)}$. Give your answer as an integer "
        f"or fraction a/b."
    )
    solution = _frac_from(answer)

    letter, other_letter, other = ("A", "B", q) if target == p else ("B", "A", p)
    value = lin * target + const
    gap = target - other
    plugged = (f"{lin}({target})" if lin else "") + (
        _signed(const) if lin else str(const))
    s = Steps()
    s.step(f"Multiply both sides by ${den_poly}$ to clear the denominators.",
           rf"{num_poly} = A{_linear_factor(q)} + B{_linear_factor(p)}")
    s.step(f"Let $x = {target}$. This makes the ${other_letter}$ term $0$, leaving "
           f"only ${letter}$.",
           rf"{plugged} = {letter}({target} - {paren(other)})")
    s.step("Simplify both sides.", f"{value} = {_coef(gap, letter)}")
    if gap != 1:
        s.step(f"Divide both sides by ${gap}$.",
               rf"{letter} = \frac{{{value}}}{{{gap}}} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


# --------------------- polar / rectangular equations ---------------------

@register
@with_variants
def pc_polar_rectangular_equation():
    r"""Polar and Rectangular Equation Conversion

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert the polar equation $r = 3\cos\theta$ to a rectangular equation. Write your answer as an equation in x and y. | $x^2 + y^2 = 3x$ |
    """
    kind = random.choice(["circle_r", "vline", "hline", "circle_cos", "circle_sin"])
    if kind == "circle_r":
        c = random.randint(1, 6)
        polar = f"r = {c}"
        answer = f"x^2 + y^2 = {c * c}"
    elif kind == "vline":
        c = random.randint(1, 6)
        polar = r"r\cos\theta = " + str(c)
        answer = f"x = {c}"
    elif kind == "hline":
        c = random.randint(1, 6)
        polar = r"r\sin\theta = " + str(c)
        answer = f"y = {c}"
    elif kind == "circle_cos":
        a = random.randint(2, 6)
        polar = f"r = {a}" + r"\cos\theta"
        answer = f"x^2 + y^2 = {a}x"
    else:  # circle_sin
        a = random.randint(2, 6)
        polar = f"r = {a}" + r"\sin\theta"
        answer = f"x^2 + y^2 = {a}y"
    problem = (
        f"Convert the polar equation ${polar}$ to a rectangular equation. "
        f"Write your answer as an equation in x and y."
    )
    solution = f"${answer}$"

    s = Steps()
    s.step("Use the conversions $x = r\\cos\\theta$, $y = r\\sin\\theta$, and "
           "$r^2 = x^2 + y^2$.")
    if kind == "circle_r":
        s.step("Square both sides to get $r^2$.", f"r^2 = {c * c}")
        s.step("Replace $r^2$ with $x^2 + y^2$.", answer)
    elif kind in ("vline", "hline"):
        var, fn = ("x", "cos") if kind == "vline" else ("y", "sin")
        s.step(f"Replace $r\\{fn}\\theta$ with ${var}$.", answer)
    else:
        var, fn = ("x", "cos") if kind == "circle_cos" else ("y", "sin")
        s.step(f"Multiply both sides by $r$ to create $r^2$ and $r\\{fn}\\theta$.",
               rf"r^2 = {a}r\{fn}\theta")
        s.step(f"Replace $r^2$ with $x^2 + y^2$ and $r\\{fn}\\theta$ with ${var}$.",
               answer)
    s.answer(solution)
    return problem, solution, s.done()


# 2D vectors whose Euclidean norm is an integer (as ``(x, y, |v|)``), so a
# scalar projection onto them stays rational and therefore typeable.
_INTEGER_NORM_VECTORS = [
    (3, 4, 5), (4, 3, 5), (6, 8, 10), (8, 6, 10), (5, 12, 13), (12, 5, 13),
    (9, 12, 15), (12, 9, 15), (8, 15, 17), (15, 8, 17),
]


@register
@with_variants
def pc_orthogonal_projection(max_component=8):
    r"""Orthogonal Projection

    The scalar projection of $\vec{a}$ onto $\vec{b}$ is
    $\frac{\vec{a}\cdot\vec{b}}{|\vec{b}|}$. ``b`` is chosen with integer
    length, so the answer is a whole number or a reduced fraction.
    """
    bx, by, norm = random.choice(_INTEGER_NORM_VECTORS)
    ax = random.randint(-max_component, max_component)
    ay = random.randint(-max_component, max_component)
    dot = ax * bx + ay * by
    proj = Fraction(dot, norm)
    problem = (
        f"Find the scalar projection of $\\vec{{a}} = \\langle {ax}, {ay} "
        f"\\rangle$ onto $\\vec{{b}} = \\langle {bx}, {by} \\rangle$. "
        f"Express your answer as a fraction in the form a/b, or an integer."
    )
    solution = f"${_frac_from(proj)}$"

    s = Steps()
    s.formula("The scalar projection of $\\vec{a}$ onto $\\vec{b}$",
              r"\text{comp}_{\vec{b}}\vec{a} = \frac{\vec{a} \cdot \vec{b}}{|\vec{b}|}")
    s.step("Find the dot product: multiply matching components and add.",
           rf"\vec{{a}} \cdot \vec{{b}} = {ax}({bx}) + {paren(ay)}({by}) = {dot}")
    s.step("Find the length of $\\vec{b}$.",
           rf"|\vec{{b}}| = \sqrt{{{bx}^2 + {by}^2}} = \sqrt{{{norm * norm}}} = {norm}")
    s.step("Divide.", rf"\text{{comp}}_{{\vec{{b}}}}\vec{{a}} = {_divide(dot, norm)}")
    s.answer(solution)
    return problem, solution, s.done()
