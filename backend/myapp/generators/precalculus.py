"""Solveki-local generators for Georgia "Precalculus".

Every generator here takes no required arguments, is decorated with
``@register``, and returns a ``(problem, solution)`` pair of LaTeX strings.
Answers are kept clean: integers, values rounded to at most three decimal
places, or reduced ``"a/b"`` fractions. Never seed ``random`` inside a
generator.
"""
import random
from fractions import Fraction
from math import atan2, comb, cos, degrees, gcd, hypot, pi, radians, sin, sqrt, tan

from ._registry import register
from ._format import num as _num, frac_from as _frac_from

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


@register
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
    return problem, f"${_num(ans)}$"


@register
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
    return problem, f"${_num(ans)}$"


@register
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
    return problem, f"${_num(ans)}$"


@register
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
        from math import acos, asin
        deg = round(degrees(asin(value) if func == "sin" else acos(value)))
    problem = f"Evaluate $\\arc{func}\\left({latex}\\right)$ in degrees."
    return problem, f"${deg}$"


@register
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
    return problem, f"${frac.numerator}/{frac.denominator}$"


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
    return problem, "$" + ", ".join(str(d) for d in sorted(sols)) + "$"


def _clean(value):
    """Round to 3 dp and normalise ``-0.0`` to ``0.0``."""
    return round(value, 3) + 0.0


def _pt(value):
    """Typeable coordinate component: 3dp, trailing ``.0`` dropped."""
    return _num(value)


@register
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
    return problem, f"({_pt(x)}, {_pt(y)})"


@register
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
    return problem, f"({_pt(r)}, {_pt(theta)})"


@register
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
    return problem, f"${total}$"


@register
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
    return problem, f"${total}$"


@register
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
    return problem, solution


@register
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
    return problem, f"({rx}, {ry})"


@register
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
    return problem, f"$y = {rhs}$"


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


@register
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
    return problem, f"({_num(x)}, {_num(y)})"


@register
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
    return problem, f"${_num(value)}$"


@register
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
    return problem, f"${_num(value)}$"


@register
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
    return problem, f"${_num(value)}$"


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
    return problem, "$" + ", ".join(str(d) for d in sorted(sols)) + "$"


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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, f"({shared}, {_frac_from(y)})"


@register
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
    return problem, solution


@register
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
    return problem, f"y = {_line_rhs(m, b)}"


@register
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
    return problem, _frac_from(y)


@register
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
        left = f"(-inf, {lo}" + ("]" if inc_lo else ")")
        right = ("[" if inc_hi else "(") + f"{hi}, inf)"
        solution = f"{left} U {right}"
    else:
        inc_lo = relation == "<=" and lo == z
        inc_hi = relation == "<=" and hi == z
        left_br = "[" if inc_lo else "("
        right_br = "]" if inc_hi else ")"
        solution = f"{left_br}{lo}, {hi}{right_br}"
    rel_latex = {">": ">", ">=": r"\ge", "<": "<", "<=": r"\le"}[relation]
    problem = (
        f"Solve $\\frac{{{_linear_factor(z)}}}{{{_linear_factor(p)}}} "
        f"{rel_latex} 0$. Express your solution in interval notation using "
        f"'inf' and '-inf' for infinity, 'U' for union, ( ) for excluded and "
        f"[ ] for included endpoints (e.g. (-inf, -2) U [1, inf))."
    )
    return problem, solution


# --------------------------- sinusoids ---------------------------

@register
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
    return problem, solution


# --------------------- sum/difference & half-angle ---------------------

_SPECIAL_ANGLES = [30, 45, 60, 90, 120, 135, 150]


@register
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
    return problem, f"${_num(value)}$"


_HALF_FULL_ANGLES = [30, 45, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]


@register
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
    return problem, f"${_num(value)}$"


# --------------------- binomial theorem & complex ---------------------

@register
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
    return problem, f"${coeff}$"


def _complex_str(a, b):
    """Render a complex number as a typeable ``a+bi`` / ``a-bi`` string."""
    a_s = _num(a)
    b_val = round(b, 3) + 0.0
    if b_val >= 0:
        return f"{a_s}+{_num(b_val)}i"
    return f"{a_s}-{_num(abs(b_val))}i"


@register
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
    return problem, f"${_complex_str(x, y)}$"


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
    return problem, f"${ans}$"


# --------------------- recursive sequences ---------------------

@register
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
    return problem, f"${value}$"


# --------------------- partial fractions ---------------------

@register
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
    return problem, _frac_from(answer)


# --------------------- polar / rectangular equations ---------------------

@register
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
    return problem, f"${answer}$"


# 2D vectors whose Euclidean norm is an integer (as ``(x, y, |v|)``), so a
# scalar projection onto them stays rational and therefore typeable.
_INTEGER_NORM_VECTORS = [
    (3, 4, 5), (4, 3, 5), (6, 8, 10), (8, 6, 10), (5, 12, 13), (12, 5, 13),
    (9, 12, 15), (12, 9, 15), (8, 15, 17), (15, 8, 17),
]


@register
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
    return problem, f"${_frac_from(proj)}$"
