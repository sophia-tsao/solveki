"""Extra question types for the Precalculus topics (``precalculus.py``).

Each function is a variant of one topic's generator; that generator's original
question stays as the ``classic`` variant (see ``_variants.with_variants``).
Variants only use their own topic's skill. See docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num, pair
from ._steps import Steps, paren, tex_frac
from . import ap_precalc_trig
from . import precalculus as pc

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."
_ROUND = "Round your answer to the nearest thousandth."
_ROUNDED = "Rounded to the nearest thousandth, the answer is"
_TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29)]


def _nonzero(lo, hi):
    return random.choice([i for i in range(lo, hi + 1) if i != 0])


def _tex(value):
    v = Fraction(value)
    return str(v.numerator) if v.denominator == 1 else tex_frac(v.numerator, v.denominator)


def _factor(r):
    return "x" if r == 0 else (f"(x - {r})" if r > 0 else f"(x + {-r})")


# --- Triangles ---------------------------------------------------------------------------

@pc.pc_law_of_sines.variant("ambiguous_case")
def _sines_ambiguous_case():
    """SSA: how many triangles fit (0, 1 or 2)?"""
    while True:
        A = random.randint(20, 150)
        b = random.randint(4, 20)
        a = random.randint(2, 25)
        h = b * math.sin(math.radians(A))
        if A < 90:
            if abs(a - h) < 0.05 or a == b:
                continue
            count = 0 if a < h else (2 if a < b else 1)
        else:
            if a == b:
                continue
            count = 1 if a > b else 0
        break
    problem = (
        f"In triangle $ABC$, angle $A = {A}^\\circ$, side $a = {a}$ (opposite $A$), and side $b = {b}$. How many "
        "different triangles fit this information? Answer 0, 1, or 2."
    )
    solution = f"{count}"
    s = Steps()
    if A < 90:
        s.step("With an acute angle, compare $a$ with the height $h = b\\sin A$ and with $b$.",
               rf"h = {b}\sin {A}^\circ \approx {num(h)}")
        s.step("$a < h$: no triangle. $h < a < b$: two triangles. $a \\geq b$: one triangle.")
    else:
        s.step("With an obtuse angle, the side opposite it must be the longest: one triangle if $a > b$, else none.")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_law_of_cosines_side.variant("angle_from_sides")
def _cosines_angle_from_sides():
    """Reverse: an angle from all three sides."""
    while True:
        a, b, c = (random.randint(2, 20) for _ in range(3))
        if a + b > c and a + c > b and b + c > a:
            break
    C = math.degrees(math.acos((a * a + b * b - c * c) / (2 * a * b)))
    problem = f"A triangle has sides $a = {a}$, $b = {b}$, and $c = {c}$. Find angle $C$ (opposite side $c$) in degrees. {_ROUND}"
    solution = num(C)
    s = Steps()
    s.formula("The law of cosines solved for the angle", rf"\cos C = \frac{{a^2 + b^2 - c^2}}{{2ab}} = \frac{{{a * a + b * b - c * c}}}{{{2 * a * b}}}")
    s.step("Take the inverse cosine.", rf"C \approx {solution}^\circ")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_oblique_triangle_area.variant("side_from_area")
def _oblique_side_from_area():
    """Reverse: a side from the area and the included angle."""
    C = random.choice([30, 90, 150])
    sin_c = Fraction(1, 2) if C != 90 else Fraction(1)
    a, b = random.randint(2, 20), random.randint(2, 20)
    area = Fraction(1, 2) * a * b * sin_c
    problem = (
        f"A triangle has sides $a = {a}$ and $b$ with included angle $C = {C}^\\circ$. Its area is ${num(area)}$. What "
        "is $b$?"
    )
    solution = f"{b}"
    s = Steps()
    s.formula("The area of a triangle from two sides and the included angle", rf"A = \frac{{1}}{{2}}ab\sin C")
    s.substitute(rf"{num(area)} = \frac{{1}}{{2}}({a})b\sin {C}^\circ = {num(Fraction(a, 2) * sin_c)}b")
    s.step("Solve for $b$.", f"b = {b}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Trig values and identities -----------------------------------------------------------

@pc.pc_inverse_trig.variant("range_restriction")
def _inverse_range_restriction():
    """An inverse function undoes its function only on its restricted range."""
    kind = random.choice(["sin", "cos", "tan"])
    if kind == "sin":
        t = random.choice(range(95, 180, 5))
        answer, why = 180 - t, f"$\\sin {t}^\\circ = \\sin {180 - t}^\\circ$, and arcsin returns angles from $-90^\\circ$ to $90^\\circ$."
    elif kind == "cos":
        t = random.choice(range(185, 360, 5))
        answer, why = 360 - t, f"$\\cos {t}^\\circ = \\cos {360 - t}^\\circ$, and arccos returns angles from $0^\\circ$ to $180^\\circ$."
    else:
        t = random.choice([v for v in range(95, 270, 5) if v != 180])
        answer, why = t - 180, f"$\\tan {t}^\\circ = \\tan {t - 180}^\\circ$, and arctan returns angles between $-90^\\circ$ and $90^\\circ$."
    problem = f"Evaluate $\\arc{kind}(\\{kind} {t}^\\circ)$ in degrees."
    solution = f"{answer}"
    s = Steps()
    s.step(why)
    s.answer(solution)
    return problem, solution, s.done()


_SIN = {0: Fraction(0), 30: Fraction(1, 2), 90: Fraction(1), 150: Fraction(1, 2), 180: Fraction(0),
        210: Fraction(-1, 2), 270: Fraction(-1), 330: Fraction(-1, 2)}
_COS = {0: Fraction(1), 60: Fraction(1, 2), 90: Fraction(0), 120: Fraction(-1, 2), 180: Fraction(-1),
        240: Fraction(-1, 2), 270: Fraction(0), 300: Fraction(1, 2)}


@pc.pc_double_angle.variant("recognize_identity")
def _double_angle_recognize():
    r"""$2\sin\theta\cos\theta = \sin 2\theta$ and $\cos^2\theta - \sin^2\theta = \cos 2\theta$."""
    if random.random() < 0.5:
        double = random.choice([d for d in _SIN if d])
        t = Fraction(double, 2)
        expr, value, name = rf"2\sin {num(t)}^\circ \cos {num(t)}^\circ", _SIN[double], rf"\sin {double}^\circ"
    else:
        double = random.choice([d for d in _COS if d])
        t = Fraction(double, 2)
        expr, value, name = rf"\cos^2 {num(t)}^\circ - \sin^2 {num(t)}^\circ", _COS[double], rf"\cos {double}^\circ"
    problem = f"Evaluate ${expr}$ without a calculator. {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step("Recognize a double-angle identity.", f"{expr} = {name}")
    s.step("Evaluate.", f"{name} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_sum_difference_values.variant("recognize_identity")
def _sum_difference_recognize():
    r"""$\cos A\cos B + \sin A\sin B = \cos(A - B)$, and friends."""
    form = random.choice(["cos_diff", "cos_sum", "sin_sum", "sin_diff"])
    table = _COS if form.startswith("cos") else _SIN
    target = random.choice(list(table))
    B = random.choice(range(5, 80, 5))
    A = target - B if form.endswith("sum") else target + B
    A %= 360
    if form == "cos_diff":
        expr, name = rf"\cos {A}^\circ \cos {B}^\circ + \sin {A}^\circ \sin {B}^\circ", rf"\cos({A}^\circ - {B}^\circ)"
    elif form == "cos_sum":
        expr, name = rf"\cos {A}^\circ \cos {B}^\circ - \sin {A}^\circ \sin {B}^\circ", rf"\cos({A}^\circ + {B}^\circ)"
    elif form == "sin_sum":
        expr, name = rf"\sin {A}^\circ \cos {B}^\circ + \cos {A}^\circ \sin {B}^\circ", rf"\sin({A}^\circ + {B}^\circ)"
    else:
        expr, name = rf"\sin {A}^\circ \cos {B}^\circ - \cos {A}^\circ \sin {B}^\circ", rf"\sin({A}^\circ - {B}^\circ)"
    value = table[target]
    func = r"\cos" if form.startswith("cos") else r"\sin"
    problem = f"Evaluate ${expr}$ without a calculator. {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step("Recognize a sum or difference identity.", f"{expr} = {name}")
    s.step("Evaluate.", rf"{name} = {func} {target}^\circ = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_half_angle_values.variant("exact_from_triple")
def _half_angle_exact():
    r"""An exact half-angle value: $\cos\theta = 7/25 \Rightarrow \sin(\theta/2) = 3/5$."""
    p, q, r = random.choice(_TRIPLES)
    u, v = (p, q) if random.random() < 0.5 else (q, p)
    sin_half, cos_half = Fraction(u, r), Fraction(v, r)   # theta/2 is acute: the triple's legs
    cos_t = 1 - 2 * sin_half * sin_half
    ask_sin = random.random() < 0.5
    value = sin_half if ask_sin else cos_half
    problem = (
        f"An angle $\\theta$ between $0^\\circ$ and $180^\\circ$ has $\\cos\\theta = {frac_from(cos_t)}$. Find "
        f"$\\{'sin' if ask_sin else 'cos'}\\frac{{\\theta}}{{2}}$. {_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    if ask_sin:
        s.formula("The half-angle formula", rf"\sin\frac{{\theta}}{{2}} = \sqrt{{\frac{{1 - \cos\theta}}{{2}}}} = \sqrt{{{_tex((1 - cos_t) / 2)}}}")
    else:
        s.formula("The half-angle formula", rf"\cos\frac{{\theta}}{{2}} = \sqrt{{\frac{{1 + \cos\theta}}{{2}}}} = \sqrt{{{_tex((1 + cos_t) / 2)}}}")
    s.step("Half of an angle under $180^\\circ$ is acute, so take the positive root.", f"{_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_solve_trig_equation.variant("count_solutions")
def _trig_count_solutions():
    """How many solutions sin(kx) = v (or cos, tan) has in [0, 360)."""
    func = random.choice(["sin", "cos", "tan"])
    k = random.randint(1, 4)
    if func == "tan":
        v_tex, per = random.choice([("1", 2), ("-1", 2), (r"\sqrt{3}", 2), ("0", 2)])
    else:
        v_tex, per = random.choice([(r"\frac{1}{2}", 2), (r"-\frac{1}{2}", 2), ("1", 1), ("-1", 1),
                                    (r"\frac{\sqrt{2}}{2}", 2)])
    count = k * per
    arg = "x" if k == 1 else f"{k}x"
    problem = f"How many solutions does $\\{func}({arg}) = {v_tex}$ have for $x$ in $[0^\\circ, 360^\\circ)$?"
    solution = f"{count}"
    s = Steps()
    if func == "tan":
        s.step(f"$\\tan u = {v_tex}$ has one solution every $180^\\circ$, so $2$ in each full turn.")
    else:
        s.step(f"$\\{func} u = {v_tex}$ has {'two solutions' if per == 2 else 'one solution'} in each full turn.")
    if k > 1:
        s.step(f"As $x$ runs over $[0^\\circ, 360^\\circ)$, $u = {k}x$ runs over ${k}$ full turns.", f"{k} \\times {per} = {count}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Polar coordinates ------------------------------------------------------------------------

@pc.pc_polar_to_rectangular.variant("negative_radius")
def _polar_negative_radius():
    """A negative r points the opposite way from the angle."""
    r = -random.randint(1, 9)
    t = random.choice(range(0, 360, 15))
    x, y = r * math.cos(math.radians(t)), r * math.sin(math.radians(t))
    problem = (
        f"Convert the polar coordinates $(r, \\theta) = ({r}, {t}^\\circ)$ to rectangular coordinates, rounded to the "
        "nearest thousandth. Format your answer as (x, y)."
    )
    solution = pair(x, y)
    s = Steps()
    s.step("A negative $r$ means go the distance $|r|$ in the opposite direction; the formulas handle it.",
           rf"x = {r}\cos {t}^\circ \approx {num(x)}, \quad y = {r}\sin {t}^\circ \approx {num(y)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_rectangular_to_polar.variant("angle_by_quadrant")
def _rectangular_angle_by_quadrant():
    """The polar angle in [0, 360), placed in the right quadrant."""
    x, y = _nonzero(-9, 9), _nonzero(-9, 9)
    theta = math.degrees(math.atan2(y, x)) % 360
    problem = (
        f"The point $({x}, {y})$ is written in polar form with $r > 0$. What is $\\theta$, in degrees between $0$ and "
        f"$360$? {_ROUND}"
    )
    solution = num(theta)
    quadrant = {(True, True): "I", (False, True): "II", (False, False): "III", (True, False): "IV"}[(x > 0, y > 0)]
    s = Steps()
    s.step(f"The point is in quadrant {quadrant}. The reference angle is", rf"\tan^{{-1}}\left|\frac{{{y}}}{{{x}}}\right| \approx {num(math.degrees(math.atan(abs(y / x))))}^\circ")
    s.step(f"Place it in quadrant {quadrant}.", rf"\theta \approx {solution}^\circ")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_polar_rectangular_equation.variant("circle_radius")
def _polar_circle_radius():
    r"""$r = a\sin\theta$ is a circle of radius $|a|/2$."""
    a = _nonzero(-12, 12)
    func = random.choice(["sin", "cos"])
    problem = f"The polar graph $r = {a}\\{func}\\theta$ is a circle. What is its radius?"
    solution = num(Fraction(abs(a), 2))
    s = Steps()
    s.step("Multiply by $r$ and convert.", rf"r^2 = {a}r\{func}\theta \Rightarrow x^2 + y^2 = {a}{'y' if func == 'sin' else 'x'}")
    s.step("Complete the square: the radius is half the coefficient.", rf"\frac{{|{a}|}}{{2}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Sequences and series ------------------------------------------------------------------------

@pc.pc_finite_geometric_sum.variant("number_of_terms")
def _geometric_number_of_terms():
    """Reverse: how many terms give a stated sum."""
    a, r = _nonzero(-5, 5), random.choice([2, 3, -2, -3])
    n = random.randint(2, 8)
    total = a * (r ** n - 1) // (r - 1)
    problem = (
        f"A geometric series has first term ${a}$ and common ratio ${r}$. How many terms add up to ${total}$?"
    )
    solution = f"{n}"
    s = Steps()
    s.formula("The sum of n terms", rf"S_n = a\frac{{r^n - 1}}{{r - 1}} \Rightarrow {total} = {a}\cdot\frac{{({r})^n - 1}}{{{r - 1}}}")
    s.step("Solve for $r^n$.", f"({r})^n = {r ** n} \\Rightarrow n = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_sigma_arithmetic_sum.variant("upper_limit")
def _sigma_upper_limit():
    r"""Reverse: the upper limit of $\sum_{k=1}^{n}(Ak + B)$ from its value."""
    A, B = random.randint(1, 6), random.randint(-8, 8)
    n = random.randint(3, 20)
    total = A * n * (n + 1) // 2 + B * n
    problem = f"For what $n$ is $\\sum_{{k=1}}^{{n}} ({A}k {'+' if B >= 0 else '-'} {abs(B)}) = {total}$?"
    solution = f"{n}"
    s = Steps()
    s.step("Split the sum.", rf"{A}\cdot\frac{{n(n + 1)}}{{2}} + {paren(B)}n = {total}")
    s.step("Try or solve the quadratic for a positive whole $n$.", f"n = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_recursive_sequence_term.variant("long_run")
def _recursive_long_run():
    """The value a contracting recursion settles at: L = rL + d."""
    r = random.choice([Fraction(1, 2), Fraction(1, 3), Fraction(2, 3), Fraction(1, 4), Fraction(3, 4), Fraction(-1, 2)])
    d = random.randint(-20, 30)
    limit = d / (1 - r)
    problem = (
        f"A sequence is defined by $a_1 = {random.randint(-10, 10)}$ and $a_n = {_tex(r)}a_{{n-1}} {'+' if d >= 0 else '-'} "
        f"{abs(d)}$. What value does $a_n$ approach as $n$ grows? {_FRACTION_HINT}"
    )
    solution = frac_from(limit)
    s = Steps()
    s.step("If the terms settle at $L$, then $L$ must satisfy the rule itself.", rf"L = {_tex(r)}L {'+' if d >= 0 else '-'} {abs(d)}")
    s.step("Solve for $L$.", rf"L = \frac{{{d}}}{{1 - {paren(_tex(r))}}} = {_tex(limit)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_sequence_limit.variant("product_form")
def _sequence_limit_product():
    r"""Only the leading terms matter: $\frac{(3n + 1)(2n - 5)}{n^2 + 4}$."""
    a, c = _nonzero(-5, 5), _nonzero(-5, 5)
    b, d = random.randint(-9, 9), random.randint(-9, 9)
    e = _nonzero(-6, 6)
    f, g = random.randint(-9, 9), random.randint(1, 9)
    limit = Fraction(a * c, e)
    num_ = f"({_term_n(a, b)})({_term_n(c, d)})"
    den = f"{'' if e == 1 else ('-' if e == -1 else e)}n^2 {'+' if f >= 0 else '-'} {abs(f)}n + {g}"
    problem = f"Find $\\lim_{{n \\to \\infty}} \\frac{{{num_}}}{{{den}}}$. {_FRACTION_HINT}"
    solution = frac_from(limit)
    s = Steps()
    s.step("For large $n$ only the highest powers matter: the numerator behaves like "
           f"$({a}n)({c}n) = {a * c}n^2$.")
    s.step("Divide the leading coefficients.", rf"\frac{{{a * c}}}{{{e}}} = {_tex(limit)}")
    s.answer(solution)
    return problem, solution, s.done()


def _term_n(a, b):
    lead = "n" if a == 1 else ("-n" if a == -1 else f"{a}n")
    return lead if b == 0 else f"{lead} {'+' if b > 0 else '-'} {abs(b)}"


# --- Vectors and parametric equations ------------------------------------------------------------

@pc.pc_vector_add.variant("boat_in_current")
def _vector_boat():
    """Ground speed of a boat heading straight across a current."""
    b, c = random.randint(2, 30), random.randint(1, 15)
    speed = math.hypot(b, c)
    problem = (
        f"A boat heads straight across a river at ${b}$ km/h relative to the water, while the current flows at ${c}$ "
        f"km/h downstream. What is the boat's speed relative to the ground? {_ROUND}"
    )
    solution = num(speed)
    s = Steps()
    s.step("Add the velocity vectors: they are perpendicular.", f"\\langle {b}, 0 \\rangle + \\langle 0, {c} \\rangle = \\langle {b}, {c} \\rangle")
    s.step("The speed is the length of the resultant.", rf"\sqrt{{{b}^2 + {c}^2}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_orthogonal_projection.variant("projection_component")
def _projection_component():
    """A component of the vector projection of a onto b."""
    a = (random.randint(-9, 9), random.randint(-9, 9))
    b = (_nonzero(-6, 6), random.randint(-6, 6))
    scale = Fraction(a[0] * b[0] + a[1] * b[1], b[0] ** 2 + b[1] ** 2)
    proj = (scale * b[0], scale * b[1])
    which = random.choice([0, 1])
    problem = (
        f"Find the {'first' if which == 0 else 'second'} component of the vector projection of $\\vec a = \\langle {a[0]}, {a[1]} \\rangle$ "
        f"onto $\\vec b = \\langle {b[0]}, {b[1]} \\rangle$. {_FRACTION_HINT}"
    )
    solution = frac_from(proj[which])
    s = Steps()
    s.formula("The vector projection", rf"\frac{{\vec a \cdot \vec b}}{{|\vec b|^2}}\vec b = \frac{{{a[0] * b[0] + a[1] * b[1]}}}{{{b[0] ** 2 + b[1] ** 2}}}\vec b")
    s.step("Take the component.", rf"{_tex(scale)} \times {paren(b[which])} = {_tex(proj[which])}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_parametric_to_rectangular.variant("slope_only")
def _parametric_slope():
    """The slope of a linear parametric path: dy/dx = (dy/dt)/(dx/dt)."""
    a, c = _nonzero(-9, 9), _nonzero(-9, 9)
    b, d = random.randint(-9, 9), random.randint(-9, 9)
    slope = Fraction(c, a)
    problem = (
        f"A path is given by $x = {a}t {'+' if b >= 0 else '-'} {abs(b)}$ and $y = {c}t {'+' if d >= 0 else '-'} {abs(d)}$. "
        f"What is the slope of the line it traces? {_FRACTION_HINT}"
    )
    solution = frac_from(slope)
    s = Steps()
    s.step("Each unit of $t$ moves $x$ by $" + str(a) + "$ and $y$ by $" + str(c) + "$.", rf"m = \frac{{{c}}}{{{a}}} = {_tex(slope)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- The unit circle --------------------------------------------------------------------------------

def _quadrant_values():
    """A triple-based angle in a random quadrant: (quadrant, sin, cos)."""
    p, q, r = random.choice(_TRIPLES)
    if random.random() < 0.5:
        p, q = q, p
    quad = random.choice([1, 2, 3, 4])
    sx = 1 if quad in (1, 4) else -1
    sy = 1 if quad in (1, 2) else -1
    return quad, Fraction(sy * p, r), Fraction(sx * q, r)


_QUAD_NAME = {1: "I", 2: "II", 3: "III", 4: "IV"}


def _unit_circle_other(ask):
    quad, sin_t, cos_t = _quadrant_values()
    if ask == "cos":
        given, value, gname = sin_t, cos_t, "sin"
    elif ask == "sin":
        given, value, gname = cos_t, sin_t, "cos"
    else:
        given, value, gname = sin_t, sin_t / cos_t, "sin"
    problem = (
        f"An angle $\\theta$ in quadrant {_QUAD_NAME[quad]} has $\\{gname}\\theta = {frac_from(given)}$. Find "
        f"$\\{ask}\\theta$. {_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    other = cos_t if gname == "sin" else sin_t
    s.step("Use $\\sin^2\\theta + \\cos^2\\theta = 1$.", rf"\{'cos' if gname == 'sin' else 'sin'}^2\theta = 1 - \left({_tex(given)}\right)^2 = {_tex(other * other)}")
    s.step(f"Quadrant {_QUAD_NAME[quad]} fixes the sign.", rf"\{'cos' if gname == 'sin' else 'sin'}\theta = {_tex(other)}")
    if ask == "tan":
        s.step(r"$\tan\theta = \sin\theta / \cos\theta$.", rf"\frac{{{_tex(sin_t)}}}{{{_tex(cos_t)}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


pc.pc_unit_circle_cos.variant("from_sine_and_quadrant")(lambda: _unit_circle_other("cos"))
pc.pc_unit_circle_sin.variant("from_cosine_and_quadrant")(lambda: _unit_circle_other("sin"))
pc.pc_unit_circle_tan.variant("from_sine_and_quadrant")(lambda: _unit_circle_other("tan"))


@pc.pc_unit_circle_point.variant("from_one_coordinate")
def _unit_circle_point_from_one():
    """The point on the unit circle from one coordinate and the quadrant."""
    quad, sin_t, cos_t = _quadrant_values()
    give_x = random.random() < 0.5
    problem = (
        f"A point on the unit circle in quadrant {_QUAD_NAME[quad]} has "
        f"{'x' if give_x else 'y'}-coordinate ${frac_from(cos_t if give_x else sin_t)}$. What is the point? Give the "
        "coordinates as decimals, formatted as (x, y)."
    )
    solution = pair(cos_t, sin_t)
    s = Steps()
    s.step("Points on the unit circle satisfy $x^2 + y^2 = 1$; the quadrant gives the sign of the other coordinate.",
           f"({num(cos_t)}, {num(sin_t)})")
    s.answer(solution)
    return problem, solution, s.done()


@ap_precalc_trig.pc_reciprocal_trig_values.variant("from_secant")
def _reciprocal_from_secant():
    """From sec and the quadrant to sin."""
    quad, sin_t, cos_t = _quadrant_values()
    problem = (
        f"An angle in quadrant {_QUAD_NAME[quad]} has $\\sec\\theta = {frac_from(1 / cos_t)}$. Find $\\sin\\theta$. "
        f"{_FRACTION_HINT}"
    )
    solution = frac_from(sin_t)
    s = Steps()
    s.step("Secant is the reciprocal of cosine.", rf"\cos\theta = {_tex(cos_t)}")
    s.step(f"Use $\\sin^2 + \\cos^2 = 1$ and quadrant {_QUAD_NAME[quad]}'s sign.", rf"\sin\theta = {_tex(sin_t)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_simplify_trig_identity.variant("sum_to_product")
def _trig_sum_to_product():
    """SAT-hard: from sin x - cos x = s (or +), find sin x cos x by squaring."""
    plus = random.random() < 0.5
    s_val = Fraction(random.choice([1, 2, 3, 4, 6, 7]), random.choice([2, 3, 4, 5]))
    if s_val * s_val >= 2:
        s_val = Fraction(1, 2)
    product = (s_val * s_val - 1) / 2 if plus else (1 - s_val * s_val) / 2
    problem = (
        f"If $\\sin x {'+' if plus else '-'} \\cos x = {frac_from(s_val)}$, what is $\\sin x \\cos x$? {_FRACTION_HINT}"
    )
    solution = frac_from(product)
    s = Steps()
    s.step("Square both sides.", rf"\sin^2 x {'+' if plus else '-'} 2\sin x\cos x + \cos^2 x = {_tex(s_val * s_val)}")
    s.step("Use $\\sin^2 x + \\cos^2 x = 1$.", rf"1 {'+' if plus else '-'} 2\sin x\cos x = {_tex(s_val * s_val)}")
    s.step("Solve.", rf"\sin x\cos x = {_tex(product)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Rational functions -----------------------------------------------------------------------------

@pc.pc_rational_vertical_asymptotes.variant("coefficient_for_asymptote")
def _va_coefficient():
    """For what b does (x - p)/(x^2 + bx + c) have a vertical asymptote at x = r?"""
    r, s_ = random.sample([n for n in range(-6, 7) if n != 0], 2)
    p = random.choice([n for n in range(-6, 7) if n not in (r, s_)])   # no hole
    c, b = r * s_, -(r + s_)
    problem = (
        f"$f(x) = \\frac{{{_factor(p) if p else 'x'}}}{{x^2 + bx {'+' if c >= 0 else '-'} {abs(c)}}}$ has a vertical "
        f"asymptote at $x = {r}$. What is $b$?"
    )
    solution = f"{b}"
    s = Steps()
    s.step(f"The denominator must be $0$ at $x = {r}$ (and the numerator isn't).", f"{r}^2 + {paren(r)}b {'+' if c >= 0 else '-'} {abs(c)} = 0")
    s.step("Solve for $b$.", f"{r}b = {-(r * r + c)} \\Rightarrow b = {b}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_rational_zeros.variant("count_after_cancelling")
def _zeros_count():
    """How many zeros, when a numerator factor cancels into a hole."""
    roots = random.sample(range(-6, 7), 4)
    num_roots = roots[:random.randint(1, 3)]
    shared = random.choice(num_roots)
    den_roots = [shared, roots[3]]
    zeros = [r for r in num_roots if r != shared]
    problem = (
        f"How many zeros does $f(x) = \\frac{{{''.join(_factor(r) for r in num_roots)}}}{{{''.join(_factor(r) for r in den_roots)}}}$ have?"
    )
    solution = f"{len(zeros)}"
    s = Steps()
    s.step(f"The factor ${_factor(shared)}$ cancels: $x = {shared}$ is a hole, not a zero.")
    s.step("The remaining numerator factors give the zeros.", ", ".join(map(str, zeros)) if zeros else r"\text{none}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_rational_holes.variant("coefficient_for_hole")
def _holes_coefficient():
    """For what k does (x^2 + kx + m)/(x - r) have a hole (removable)?"""
    r = _nonzero(-6, 6)
    other = random.choice([n for n in range(-8, 9) if n != r])
    k, m = -(r + other), r * other
    problem = (
        f"For what value of $k$ does $f(x) = \\frac{{x^2 + kx {'+' if m >= 0 else '-'} {abs(m)}}}{{{_factor(r)}}}$ have a "
        "hole instead of a vertical asymptote?"
    )
    solution = f"{k}"
    s = Steps()
    s.step(f"A hole needs ${_factor(r)}$ to be a factor of the numerator, so the numerator is $0$ at $x = {r}$.",
           f"{r}^2 + {paren(r)}k {'+' if m >= 0 else '-'} {abs(m)} = 0")
    s.step("Solve for $k$.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_rational_horizontal_asymptote.variant("coefficient_for_asymptote")
def _ha_coefficient():
    """For what k is y = h the horizontal asymptote of (kx^2 + 1)/(cx^2 - 4)?"""
    c = _nonzero(-5, 5)
    h = Fraction(_nonzero(-6, 6), random.choice([1, 1, 2]))
    k = h * c
    while k.denominator != 1:
        c *= 2
        k = h * c
    lead = "" if c == 1 else ("-" if c == -1 else str(c))
    problem = (
        f"$f(x) = \\frac{{kx^2 + 1}}{{{lead}x^2 - 4}}$ has the horizontal asymptote $y = {_tex(h)}$. What is $k$?"
    )
    solution = f"{k}"
    s = Steps()
    s.step("The degrees are equal, so the asymptote is the ratio of the leading coefficients.", rf"\frac{{k}}{{{c}}} = {_tex(h)}")
    s.step(f"Multiply by ${c}$.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_rational_slant_asymptote.variant("asymptote_intercept")
def _slant_intercept():
    """The y-intercept of the slant asymptote (from the division)."""
    while True:   # a nonzero remainder, so the graph really has a slant asymptote
        a = _nonzero(-4, 4)
        p = _nonzero(-6, 6)
        b, c = random.randint(-9, 9), random.randint(-9, 9)
        if a * p * p + b * p + c != 0:
            break
    # (ax^2 + bx + c)/(x - p): quotient ax + (b + ap)
    intercept = b + a * p
    problem = (
        f"What is the y-intercept of the slant asymptote of $f(x) = \\frac{{{'' if a == 1 else ('-' if a == -1 else a)}x^2 "
        f"{'+' if b >= 0 else '-'} {abs(b)}x {'+' if c >= 0 else '-'} {abs(c)}}}{{{_factor(p)}}}$?"
    )
    solution = f"{intercept}"
    s = Steps()
    s.step(f"Divide by ${_factor(p)}$ (synthetic division with ${p}$): the quotient is the asymptote.",
           f"y = {a}x + ({b} + {a}({p})) = {a}x {'+' if intercept >= 0 else '-'} {abs(intercept)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_rational_y_intercept.variant("coefficient_from_intercept")
def _y_intercept_coefficient():
    """Reverse: the leading coefficient from the y-intercept."""
    p, q, r = random.sample([n for n in range(-6, 7) if n != 0], 3)
    a = _nonzero(-6, 6)
    y0 = Fraction(a * (-p), (-q) * (-r))
    problem = (
        f"$f(x) = \\frac{{a{_factor(p)}}}{{{_factor(q)}{_factor(r)}}}$ has y-intercept ${_tex(y0)}$. What is $a$?"
    )
    solution = f"{a}"
    s = Steps()
    s.step("The y-intercept is $f(0)$.", rf"f(0) = \frac{{a({-p})}}{{({-q})({-r})}} = {_tex(Fraction(-p, q * r))}a")
    s.step("Solve for $a$.", f"a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_rational_inequality.variant("count_integers")
def _rational_inequality_count():
    """How many integers satisfy (x - z)/(x - p) <= 0 (or < 0)?"""
    z, p = random.sample(range(-9, 10), 2)
    op = random.choice(["<", "\\leq"])
    count = sum(1 for x in range(-50, 51) if x != p and ((x - z) * (x - p) < 0 or (op == "\\leq" and x == z)))
    problem = f"How many integers $x$ satisfy $\\frac{{{_factor(z)}}}{{{_factor(p)}}} {op} 0$?"
    solution = f"{count}"
    lo, hi = min(z, p), max(z, p)
    s = Steps()
    s.step("The quotient is negative strictly between the zero and the asymptote.", f"{lo} < x < {hi}")
    if op == "\\leq":
        s.step(f"It also equals $0$ at $x = {z}$ (but $x = {p}$ is never allowed).")
    s.answer(solution)
    return problem, solution, s.done()


# --- Sinusoids, binomial theorem, complex numbers ---------------------------------------------------

@pc.pc_sinusoid_features.variant("from_max_min")
def _sinusoid_from_max_min():
    """Amplitude and midline from the maximum and minimum."""
    lo = random.randint(-20, 10)
    hi = lo + 2 * random.randint(1, 15)
    ask_amp = random.random() < 0.5
    problem = (
        f"A sinusoid has a maximum value of ${hi}$ and a minimum value of ${lo}$. What is its "
        f"{'amplitude' if ask_amp else 'midline? Write it in the form y = c'}{'?' if ask_amp else '.'}"
    )
    solution = f"{(hi - lo) // 2}" if ask_amp else f"y = {(hi + lo) // 2}"
    s = Steps()
    if ask_amp:
        s.step("The amplitude is half the distance from max to min.", rf"\frac{{{hi} - {paren(lo)}}}{{2}} = {(hi - lo) // 2}")
    else:
        s.step("The midline is halfway between max and min.", rf"\frac{{{hi} + {paren(lo)}}}{{2}} = {(hi + lo) // 2}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_binomial_term.variant("constant_term")
def _binomial_constant_term():
    r"""The constant term of $(x + \frac{c}{x})^n$."""
    n = random.choice([2, 4, 6, 8])
    c = random.randint(1, 3)
    k = n // 2
    value = math.comb(n, k) * c ** k
    inner = r"\frac{1}{x}" if c == 1 else rf"\frac{{{c}}}{{x}}"
    problem = f"What is the constant term in the expansion of $\\left(x + {inner}\\right)^{{{n}}}$?"
    solution = f"{value}"
    s = Steps()
    s.step(f"A term is $\\binom{{{n}}}{{k}} x^{{{n} - k}}\\left({inner}\\right)^k$, whose power of $x$ is ${n} - 2k$.")
    s.step(f"The power is $0$ when $k = {k}$.", rf"\binom{{{n}}}{{{k}}}({c})^{{{k}}} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_de_moivre.variant("first_real_power")
def _de_moivre_first_real():
    """The smallest n > 0 with z^n real: n * theta must be a multiple of 180."""
    theta = random.choice([15, 20, 30, 36, 40, 45, 60, 72, 75, 105, 120, 135, 150])
    r = random.randint(1, 4)
    n = 180 // math.gcd(180, theta)
    problem = (
        f"Let $z = {r}(\\cos {theta}^\\circ + i\\sin {theta}^\\circ)$. What is the smallest positive integer $n$ for which "
        "$z^n$ is a real number?"
    )
    solution = f"{n}"
    s = Steps()
    s.step("By De Moivre's theorem, $z^n$ has angle $n\\theta$; it's real when that angle is a multiple of $180^\\circ$.",
           f"{theta}n = 180m")
    s.step("Find the smallest such $n$.", rf"n = \frac{{180}}{{\gcd(180, {theta})}} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_partial_fractions.variant("sum_of_numerators")
def _partial_fraction_sum():
    """A + B equals the x-coefficient: no need to find A and B separately."""
    p, q = random.sample([n for n in range(-6, 7) if n != 0], 2)
    A, B = _nonzero(-9, 9), _nonzero(-9, 9)
    m, n = A + B, -(A * q + B * p)
    problem = (
        f"If $\\frac{{{m}x {'+' if n >= 0 else '-'} {abs(n)}}}{{{_factor(p)}{_factor(q)}}} = \\frac{{A}}{{{_factor(p)}}} + "
        f"\\frac{{B}}{{{_factor(q)}}}$, what is $A + B$?"
    )
    solution = f"{m}"
    s = Steps()
    s.step("Combine the right side over the common denominator.", f"A{_factor(q)} + B{_factor(p)} = {m}x {'+' if n >= 0 else '-'} {abs(n)}")
    s.step("Match the $x$-coefficients: they're exactly $A + B$.", f"A + B = {m}")
    s.answer(solution)
    return problem, solution, s.done()


# =============================================================================
# Further variants (beyond each topic's first new question type)
# =============================================================================

@pc.pc_law_of_sines.variant("find_angle")
def _sines_find_angle():
    """Reverse: an angle from two sides and a non-included angle (one triangle)."""
    while True:
        A = random.randint(20, 80)
        a, b = random.randint(5, 25), random.randint(3, 20)
        if a >= b:   # the side opposite the known angle is the longer one: a single triangle
            break
    B = math.degrees(math.asin(b * math.sin(math.radians(A)) / a))
    problem = (
        f"In triangle $ABC$, angle $A = {A}^\\circ$, side $a = {a}$, and side $b = {b}$. Find angle $B$ in degrees. {_ROUND}"
    )
    solution = num(B)
    s = Steps()
    s.formula("The law of sines", rf"\frac{{\sin B}}{{{b}}} = \frac{{\sin {A}^\circ}}{{{a}}}")
    s.step("Solve for $B$. Since $b \\leq a$, $B$ is acute.", rf"B = \sin^{{-1}}\left(\frac{{{b}\sin {A}^\circ}}{{{a}}}\right) \approx {solution}^\circ")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_law_of_sines.variant("river_width")
def _sines_river_width():
    """Surveying: two angles sighted from the ends of a baseline."""
    base = random.randint(50, 500)
    A, B = random.randint(30, 80), random.randint(30, 80)
    C = 180 - A - B
    dist = base * math.sin(math.radians(B)) / math.sin(math.radians(C))
    problem = (
        f"Two surveyors stand ${base}$ m apart at points $A$ and $B$ on one bank of a river. Each sights a tree $T$ across "
        f"the river: angle $TAB = {A}^\\circ$ and angle $TBA = {B}^\\circ$. How far is the tree from $A$, in meters? {_ROUND}"
    )
    solution = num(dist)
    s = Steps()
    s.step("The angle at the tree is what's left of $180^\\circ$.", f"T = 180 - {A} - {B} = {C}")
    s.formula("The law of sines", rf"\frac{{AT}}{{\sin {B}^\circ}} = \frac{{{base}}}{{\sin {C}^\circ}} \Rightarrow AT \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_law_of_cosines_side.variant("ships")
def _cosines_ships():
    """Two ships leave port on different headings: distance apart later."""
    v1, v2 = random.randint(5, 30), random.randint(5, 30)
    t = random.randint(1, 6)
    angle = random.randint(20, 160)
    a, b = v1 * t, v2 * t
    d = math.sqrt(a * a + b * b - 2 * a * b * math.cos(math.radians(angle)))
    problem = (
        f"Two ships leave a port at the same time. One sails at ${v1}$ km/h and the other at ${v2}$ km/h, with "
        f"${angle}^\\circ$ between their courses. How far apart are they after ${t}$ hours, in km? {_ROUND}"
    )
    solution = num(d)
    s = Steps()
    s.step("Their distances from port form two sides of a triangle with the angle between them.", f"{v1}({t}) = {a}, \\quad {v2}({t}) = {b}")
    s.formula("The law of cosines", rf"d^2 = {a}^2 + {b}^2 - 2({a})({b})\cos {angle}^\circ \Rightarrow d \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_law_of_cosines_side.variant("is_obtuse")
def _cosines_is_obtuse():
    """Is the largest angle obtuse? Compare c^2 with a^2 + b^2."""
    while True:
        a, b, c = sorted(random.randint(2, 20) for _ in range(3))
        if a + b > c and a * a + b * b != c * c:
            break
    obtuse = c * c > a * a + b * b
    problem = f"Is a triangle with sides ${a}$, ${b}$, and ${c}$ obtuse? Answer yes or no."
    answer = "yes" if obtuse else "no"
    s = Steps()
    s.step("The largest angle is opposite the longest side; by the law of cosines it's obtuse exactly when $c^2 > a^2 + b^2$.",
           f"{c}^2 = {c * c}, \\quad {a}^2 + {b}^2 = {a * a + b * b}")
    s.answer(answer)
    return problem, answer, s.done()


@pc.pc_oblique_triangle_area.variant("heron")
def _oblique_heron():
    """Area from three sides with Heron's formula."""
    while True:
        a, b, c = (random.randint(3, 20) for _ in range(3))
        if a + b > c and a + c > b and b + c > a:
            break
    sp = Fraction(a + b + c, 2)
    area = math.sqrt(float(sp * (sp - a) * (sp - b) * (sp - c)))
    problem = f"Find the area of a triangle with sides ${a}$, ${b}$, and ${c}$. {_ROUND}"
    solution = num(area)
    s = Steps()
    s.step("Find the semiperimeter.", rf"s = \frac{{{a} + {b} + {c}}}{{2}} = {num(sp)}")
    s.formula("Heron's formula", rf"A = \sqrt{{s(s - a)(s - b)(s - c)}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_oblique_triangle_area.variant("angle_from_area")
def _oblique_angle_from_area():
    """Reverse: the (acute) included angle from the area."""
    a, b = random.randint(3, 20), random.randint(3, 20)
    C = random.randint(10, 85)
    area = Fraction(round(0.5 * a * b * math.sin(math.radians(C)) * 100), 100)
    angle = math.degrees(math.asin(min(1, float(2 * area / (a * b)))))
    problem = (
        f"A triangle has sides ${a}$ and ${b}$ with an acute included angle $C$. Its area is ${num(area)}$. Find $C$ in "
        f"degrees. {_ROUND}"
    )
    solution = num(angle)
    s = Steps()
    s.formula("The area", rf"{num(area)} = \frac{{1}}{{2}}({a})({b})\sin C")
    s.step("Solve for $\\sin C$ and take the inverse sine (the angle is acute).", rf"C = \sin^{{-1}}\left(\frac{{2({num(area)})}}{{{a * b}}}\right) \approx {solution}^\circ")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@pc.pc_inverse_trig.variant("composition")
def _inverse_composition():
    r"""$\sin(\arccos\frac{3}{5}) = \frac{4}{5}$ from a right triangle."""
    p, q, r = random.choice(_TRIPLES)
    inner, outer = random.choice([("cos", "sin"), ("sin", "cos"), ("tan", "sin"), ("sin", "tan")])
    arg = Fraction(q, r) if inner == "cos" else (Fraction(p, r) if inner == "sin" else Fraction(p, q))
    opp, adj = (p, q)
    if inner == "cos":
        value = {"sin": Fraction(p, r), "tan": Fraction(p, q)}[outer]
    elif inner == "sin":
        value = {"cos": Fraction(q, r), "tan": Fraction(p, q)}[outer]
    else:
        value = Fraction(p, r)
    problem = rf"Evaluate $\{outer}\left(\arc{inner}\frac{{{arg.numerator}}}{{{arg.denominator}}}\right)$. {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step(f"Draw a right triangle for the angle $\\theta = \\arc{inner}\\frac{{{arg.numerator}}}{{{arg.denominator}}}$ "
           f"(first quadrant): legs ${opp}$ and ${adj}$, hypotenuse ${r}$.")
    s.step(f"Read $\\{outer}\\theta$ from the triangle.", _tex(value))
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_double_angle.variant("quadrant_sign")
def _double_angle_quadrant():
    """sin 2x when x is in a given quadrant (the sign of cos matters)."""
    p, q, r = random.choice(_TRIPLES)
    quad = random.choice([2, 3, 4])
    sx = 1 if quad == 4 else -1
    sy = 1 if quad == 2 else -1
    sin_x, cos_x = Fraction(sy * p, r), Fraction(sx * q, r)
    value = 2 * sin_x * cos_x
    problem = (
        f"$\\sin x = {frac_from(sin_x)}$ and $x$ is in quadrant {_QUAD_NAME[quad]}. Find $\\sin 2x$. {_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    s.step(f"In quadrant {_QUAD_NAME[quad]}, $\\cos x$ is {'positive' if sx > 0 else 'negative'}.", rf"\cos x = {_tex(cos_x)}")
    s.formula("The double-angle formula", rf"\sin 2x = 2\sin x\cos x = 2\left({_tex(sin_x)}\right)\left({_tex(cos_x)}\right) = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_double_angle.variant("square_from_double")
def _double_angle_square():
    r"""Reverse: $\cos 2x = c \Rightarrow \sin^2 x = (1 - c)/2$."""
    c = Fraction(random.randint(-9, 9), random.choice([10, 25, 13, 17]))
    ask_sin = random.random() < 0.5
    value = (1 - c) / 2 if ask_sin else (1 + c) / 2
    problem = f"If $\\cos 2x = {frac_from(c)}$, what is $\\{'sin' if ask_sin else 'cos'}^2 x$? {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    if ask_sin:
        s.step("Use $\\cos 2x = 1 - 2\\sin^2 x$.", rf"\sin^2 x = \frac{{1 - {paren(_tex(c))}}}{{2}} = {_tex(value)}")
    else:
        s.step("Use $\\cos 2x = 2\\cos^2 x - 1$.", rf"\cos^2 x = \frac{{1 + {paren(_tex(c))}}}{{2}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


_SOLUTIONS = {("sin", "1/2"): (30, 150), ("sin", "-1/2"): (210, 330), ("cos", "1/2"): (60, 300),
              ("cos", "-1/2"): (120, 240), ("tan", "1"): (45, 225), ("tan", "-1"): (135, 315),
              ("sin", "sqrt2/2"): (45, 135), ("cos", "-sqrt2/2"): (135, 225)}
_VALUE_TEX = {"1/2": r"\frac{1}{2}", "-1/2": r"-\frac{1}{2}", "1": "1", "-1": "-1", "sqrt2/2": r"\frac{\sqrt{2}}{2}",
              "-sqrt2/2": r"-\frac{\sqrt{2}}{2}"}


@pc.pc_solve_trig_equation.variant("sum_of_solutions")
def _trig_sum_of_solutions():
    """The sum of the solutions in [0, 360)."""
    (func, v), sols = random.choice(list(_SOLUTIONS.items()))
    problem = f"What is the sum of all solutions of $\\{func} x = {_VALUE_TEX[v]}$ for $x$ in $[0^\\circ, 360^\\circ)$?"
    solution = f"{sum(sols)}"
    s = Steps()
    s.step("Find the solutions from the reference angle and the quadrants where the sign fits.", f"x = {sols[0]}, {sols[1]}")
    s.step("Add them.", f"{sols[0]} + {sols[1]} = {sum(sols)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_solve_trig_equation.variant("smallest_multiple_angle")
def _trig_smallest_multiple_angle():
    """The smallest positive solution of f(kx) = v."""
    (func, v), sols = random.choice(list(_SOLUTIONS.items()))
    k = random.randint(2, 5)
    smallest = Fraction(sols[0], k)
    problem = (
        f"What is the smallest positive solution of $\\{func}({k}x) = {_VALUE_TEX[v]}$, in degrees? Round to the nearest "
        "thousandth if needed."
    )
    solution = num(smallest)
    s = Steps()
    s.step(f"Let $u = {k}x$. The smallest positive $u$ with $\\{func} u = {_VALUE_TEX[v]}$ is ${sols[0]}^\\circ$.")
    s.step(f"Divide by ${k}$.", rf"x = \frac{{{sols[0]}}}{{{k}}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_polar_to_rectangular.variant("equivalent_with_negative_r")
def _polar_equivalent_negative():
    """Another name for the same point: (r, theta) = (-r, theta + 180)."""
    r = random.randint(1, 12)
    t = random.choice(range(0, 360, 5))
    problem = (
        f"The point $({r}, {t}^\\circ)$ can also be written as $({-r}, \\theta)$. What is $\\theta$, in degrees between $0$ and "
        "$360$?"
    )
    solution = f"{(t + 180) % 360}"
    s = Steps()
    s.step("A negative radius points the opposite way, so turn half a circle.", f"{t} + 180 = {t + 180} \\to {(t + 180) % 360}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_finite_geometric_sum.variant("salary_raises")
def _geometric_salary():
    """Total pay over n years with a fixed percent raise each year."""
    start = random.choice(range(30000, 80001, 5000))
    pct = random.choice([2, 3, 4, 5])
    n = random.randint(3, 12)
    r = 1 + pct / 100
    total = start * (r ** n - 1) / (r - 1)
    problem = (
        f"A job pays ${start}$ dollars in the first year, with a ${pct}\\%$ raise every year after. What is the total pay over "
        f"${n}$ years, in dollars? Round to the nearest cent."
    )
    solution = num(total, 2)
    s = Steps()
    s.step(f"The yearly pay is geometric with ratio ${num(Fraction(100 + pct, 100))}$.")
    s.formula("The sum", rf"S_{{{n}}} = {start}\frac{{{num(Fraction(100 + pct, 100))}^{{{n}}} - 1}}{{{num(Fraction(pct, 100))}}} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_recursive_sequence_term.variant("first_term")
def _recursive_first_term():
    """Reverse: work backward from a later term to a_1."""
    r = random.choice([2, 3, -2, -1])
    d = random.randint(-9, 9)
    a1 = random.randint(-10, 10)
    terms = [a1]
    for _ in range(3):
        terms.append(r * terms[-1] + d)
    problem = (
        f"A sequence follows $a_n = {r}a_{{n-1}} {'+' if d >= 0 else '-'} {abs(d)}$, and $a_4 = {terms[3]}$. What is $a_1$?"
    )
    solution = f"{a1}"
    s = Steps()
    s.step("Undo the rule: $a_{n-1} = (a_n - d)/r$.", f"a_3 = {terms[2]}, \\quad a_2 = {terms[1]}, \\quad a_1 = {a1}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_sequence_limit.variant("average_cost")
def _sequence_average_cost():
    """Long-run average cost per item: (F + vn)/n approaches v."""
    fixed = random.choice(range(500, 20001, 500))
    per = Fraction(random.randint(50, 2000), 100)
    problem = (
        f"Making $n$ items costs $C(n) = {fixed} + {num(per)}n$ dollars. What does the average cost per item, $C(n)/n$, "
        "approach as $n$ grows?"
    )
    solution = num(per)
    s = Steps()
    s.step("Divide by $n$.", rf"\frac{{C(n)}}{{n}} = \frac{{{fixed}}}{{n}} + {num(per)}")
    s.step(f"The fixed cost's share $\\frac{{{fixed}}}{{n}}$ goes to $0$.", f"{num(per)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_vector_add.variant("missing_vector")
def _vector_missing():
    """Reverse: solve u + v = w for v."""
    u = (random.randint(-9, 9), random.randint(-9, 9))
    w = (random.randint(-12, 12), random.randint(-12, 12))
    problem = (
        f"If $\\vec u = \\langle {u[0]}, {u[1]} \\rangle$ and $\\vec u + \\vec v = \\langle {w[0]}, {w[1]} \\rangle$, what is "
        "$\\vec v$? Give the vector as (x, y)."
    )
    solution = pair(w[0] - u[0], w[1] - u[1])
    s = Steps()
    s.step("Subtract component by component.", rf"\vec v = \langle {w[0]} - {paren(u[0])}, {w[1]} - {paren(u[1])} \rangle = \langle {w[0] - u[0]}, {w[1] - u[1]} \rangle")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_vector_add.variant("linear_combination")
def _vector_linear_combination():
    """Find a in a*u + b*v = w (the system has one solution)."""
    while True:
        u = (random.randint(-5, 5), random.randint(-5, 5))
        v = (random.randint(-5, 5), random.randint(-5, 5))
        if u[0] * v[1] - u[1] * v[0] != 0:
            break
    a, b = random.randint(-5, 5), random.randint(-5, 5)
    w = (a * u[0] + b * v[0], a * u[1] + b * v[1])
    problem = (
        f"If $a\\langle {u[0]}, {u[1]} \\rangle + b\\langle {v[0]}, {v[1]} \\rangle = \\langle {w[0]}, {w[1]} \\rangle$, what "
        "is $a$?"
    )
    solution = f"{a}"
    s = Steps()
    s.step("Match components to get two equations.", rf"{u[0]}a + {paren(v[0])}b = {w[0]}, \quad {u[1]}a + {paren(v[1])}b = {w[1]}")
    s.step("Solve the system.", f"a = {a}, \\quad b = {b}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_unit_circle_sin.variant("coterminal")
def _unit_circle_coterminal():
    """sin of a large angle: reduce by full turns first."""
    base = random.choice([0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330])
    turns = random.choice([1, 2, 3, -1, -2])
    angle = base + 360 * turns
    value = math.sin(math.radians(base))
    problem = f"Evaluate $\\sin({angle}^\\circ)$. Round your answer to the nearest thousandth if it is irrational."
    solution = num(value)
    s = Steps()
    s.step("Remove full turns of $360^\\circ$.", f"{angle} - ({turns})(360) = {base}")
    s.step("Evaluate at the coterminal angle.", rf"\sin {base}^\circ \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_unit_circle_cos.variant("angle_from_value")
def _unit_circle_angle_from_value():
    """Reverse: the angle in [0, 2pi) with a given cosine and sign of sine, as k*pi."""
    choices = [(Fraction(1, 6), "\\frac{\\sqrt{3}}{2}"), (Fraction(1, 4), "\\frac{\\sqrt{2}}{2}"), (Fraction(1, 3), "\\frac{1}{2}"),
               (Fraction(2, 3), "-\\frac{1}{2}"), (Fraction(3, 4), "-\\frac{\\sqrt{2}}{2}"), (Fraction(5, 6), "-\\frac{\\sqrt{3}}{2}")]
    k, cos_tex = random.choice(choices)
    lower = random.random() < 0.5
    angle = 2 - k if lower else k
    problem = (
        f"An angle $\\theta$ in $[0, 2\\pi)$ has $\\cos\\theta = {cos_tex}$ and $\\sin\\theta {'<' if lower else '>'} 0$. Write "
        f"$\\theta = k\\pi$. What is $k$? {_FRACTION_HINT}"
    )
    solution = frac_from(angle)
    s = Steps()
    s.step(f"The angle in $[0, \\pi]$ with this cosine is ${_tex(k)}\\pi$.")
    if lower:
        s.step("Sine is negative, so reflect into the lower half: $2\\pi - \\theta$.", rf"2\pi - {_tex(k)}\pi = {_tex(angle)}\pi")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_sinusoid_features.variant("period_from_table")
def _sinusoid_period_from_table():
    """Read the period from one cycle of tabulated values."""
    period = random.choice([4, 8, 12, 16, 20, 24])   # four equal quarter-steps per cycle
    A, D = random.randint(1, 9), random.randint(-5, 10)
    step = period // 4
    xs = [i * step for i in range(5)]
    ys = [D, D + A, D, D - A, D]
    from .prealgebra_variants import _table
    problem = (
        f"The table shows one full cycle of a sinusoid. ${_table('x', xs, 'y', ys)}$ What is its period?"
    )
    solution = f"{period}"
    s = Steps()
    s.step("The values return to the start (rising through the midline again) after one period.", f"{xs[-1]} - {xs[0]} = {period}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_sinusoid_features.variant("maximum_value")
def _sinusoid_max_value():
    """The maximum of A sin(Bx + C) + D is |A| + D."""
    A, B, D = _nonzero(-9, 9), random.randint(1, 5), random.randint(-10, 10)
    ask_max = random.random() < 0.5
    func = random.choice(["sin", "cos"])
    problem = f"What is the {'maximum' if ask_max else 'minimum'} value of $y = {A}\\{func}({B}x) {'+' if D >= 0 else '-'} {abs(D)}$?"
    solution = f"{D + abs(A) if ask_max else D - abs(A)}"
    s = Steps()
    s.step(f"$\\{func}$ ranges from $-1$ to $1$, so $y$ ranges from $D - |A|$ to $D + |A|$.", f"{D} \\pm {abs(A)}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_binomial_term.variant("coefficient_sum")
def _binomial_coefficient_sum():
    """The sum of all coefficients of (ax + b)^n is (a + b)^n."""
    a, b = random.randint(1, 4), _nonzero(-4, 4)
    n = random.randint(2, 6)
    problem = f"What is the sum of all the coefficients in the expansion of $({a if a > 1 else ''}x {'+' if b > 0 else '-'} {abs(b)})^{{{n}}}$?"
    solution = f"{(a + b) ** n}"
    s = Steps()
    s.step("Substituting $x = 1$ adds up all the coefficients.", f"({a} + {paren(b)})^{{{n}}} = {(a + b) ** n}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_binomial_term.variant("unknown_constant")
def _binomial_unknown_constant():
    r"""Reverse: the coefficient of $x^2$ in $(1 + kx)^n$ is given; find k > 0."""
    n = random.randint(3, 7)
    k = random.randint(2, 5)
    coef = math.comb(n, 2) * k * k
    problem = f"The coefficient of $x^2$ in $(1 + kx)^{{{n}}}$ is ${coef}$, and $k > 0$. What is $k$?"
    solution = f"{k}"
    s = Steps()
    s.step("The $x^2$ term is $\\binom{n}{2}(kx)^2$.", rf"\binom{{{n}}}{{2}}k^2 = {math.comb(n, 2)}k^2 = {coef}")
    s.step("Solve.", f"k^2 = {k * k} \\Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_de_moivre.variant("argument_of_power")
def _de_moivre_argument():
    """The argument of z^n, reduced to [0, 360)."""
    theta = random.choice(range(5, 180, 5))
    n = random.randint(2, 12)
    r = random.randint(1, 3)
    problem = (
        f"$z = {r}(\\cos {theta}^\\circ + i\\sin {theta}^\\circ)$. What is the argument of $z^{{{n}}}$, in degrees in $[0, 360)$?"
    )
    solution = f"{n * theta % 360}"
    s = Steps()
    s.step("De Moivre's theorem multiplies the angle by $n$.", f"{n} \\times {theta} = {n * theta}")
    s.step("Reduce by full turns.", f"{n * theta} \\to {n * theta % 360}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_de_moivre.variant("root_modulus")
def _de_moivre_root_modulus():
    """Each n-th root of z has modulus |z|^(1/n)."""
    r = random.randint(2, 100)
    n = random.randint(2, 5)
    theta = random.choice(range(0, 360, 15))
    value = r ** (1 / n)
    problem = (
        f"What is the modulus of each {['', '', 'square', 'cube', 'fourth', 'fifth'][n]} root of "
        f"${r}(\\cos {theta}^\\circ + i\\sin {theta}^\\circ)$? {_ROUND}"
    )
    solution = num(value)
    s = Steps()
    s.step(f"Every {n}th root has modulus equal to the {n}th root of the modulus.", rf"\sqrt[{n}]{{{r}}} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_partial_fractions.variant("three_factors")
def _partial_three_factors():
    """One numerator of a three-factor decomposition, by cover-up."""
    p, q, t = random.sample([n for n in range(-5, 6) if n != 0], 3)
    A, B, C = (_nonzero(-6, 6) for _ in range(3))
    # numerator N(x) = A(x-q)(x-t) + B(x-p)(x-t) + C(x-p)(x-q)
    N = lambda x: A * (x - q) * (x - t) + B * (x - p) * (x - t) + C * (x - p) * (x - q)  # noqa: E731
    c2 = A + B + C
    c1 = N(1) - N(0) - c2
    c0 = N(0)
    from .algebra2_variants import _poly
    target = random.choice([(p, A), (q, B), (t, C)])
    problem = (
        f"$\\frac{{{_poly([c2, c1, c0])}}}{{{_factor(p)}{_factor(q)}{_factor(t)}}} = \\frac{{A}}{{{_factor(p)}}} + "
        f"\\frac{{B}}{{{_factor(q)}}} + \\frac{{C}}{{{_factor(t)}}}$. What is the numerator over ${_factor(target[0])}$?"
    )
    solution = f"{target[1]}"
    s = Steps()
    others = [r for r in (p, q, t) if r != target[0]]
    s.step(f"Cover up ${_factor(target[0])}$ and evaluate the rest at $x = {target[0]}$.",
           rf"\frac{{{N(target[0])}}}{{({target[0]} - {paren(others[0])})({target[0]} - {paren(others[1])})}} = {target[1]}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_polar_rectangular_equation.variant("circle_center")
def _polar_circle_center():
    r"""The center of the circle $r = a\sin\theta$ or $r = a\cos\theta$."""
    a = _nonzero(-12, 12)
    func = random.choice(["sin", "cos"])
    center = (0, Fraction(a, 2)) if func == "sin" else (Fraction(a, 2), 0)
    problem = f"The polar graph $r = {a}\\{func}\\theta$ is a circle. What is its center, in rectangular coordinates? Format your answer as (x, y)."
    solution = pair(*center)
    s = Steps()
    s.step("Multiply by $r$ and convert to $x$ and $y$.", rf"x^2 + y^2 = {a}{'y' if func == 'sin' else 'x'}")
    s.step("Complete the square.", f"{'x^2 + (y - ' + num(Fraction(a, 2)) + ')^2' if func == 'sin' else '(x - ' + num(Fraction(a, 2)) + ')^2 + y^2'} = {num(Fraction(a * a, 4))}")
    s.answer(solution)
    return problem, solution, s.done()


@pc.pc_orthogonal_projection.variant("zero_projection")
def _projection_zero():
    """For what k is the projection zero (the vectors are perpendicular)?"""
    while True:
        a1, b1, b2 = _nonzero(-9, 9), _nonzero(-9, 9), _nonzero(-9, 9)
        if (a1 * b1) % b2 == 0:
            break
    k = -a1 * b1 // b2
    problem = (
        f"For what value of $k$ is the projection of $\\langle {a1}, k \\rangle$ onto $\\langle {b1}, {b2} \\rangle$ the zero vector?"
    )
    solution = f"{k}"
    s = Steps()
    s.step("The projection is zero exactly when the dot product is zero.", f"{a1}({b1}) + k({b2}) = 0 \\Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()
