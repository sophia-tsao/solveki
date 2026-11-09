"""Extra question types for the geometry, angle, and solid topics.

Variants for the generators in ``geometry_hs``, ``lib_geometry_gen``,
``lib_angles_gen``, ``lib_solids_gen`` and ``geometry``. Each attaches to its
topic's dispatcher (see ``_variants.with_variants``); the original question
stays as the ``classic`` variant. Variants only use their own topic's skill
(a cone variant never needs the Pythagorean theorem, for instance). See
docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num, pair
from ._steps import Steps, paren, tex_frac
from . import (geometry, geometry_hs, lib_algebra_extra_gen, lib_angles_gen, lib_geometry_gen,
               lib_solids_gen)
from .geometry_hs import _PYTHAG_TRIPLES, _pi_times, _signed_factor

_ROUND = "Round your answer to the nearest thousandth."
_ROUNDED = "Rounded to the nearest thousandth, the answer is"
_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."
_PAIR_HINT = "Give the point as (x, y)."


def _nonzero(lo, hi):
    return random.choice([i for i in range(lo, hi + 1) if i != 0])


def _frac(value):
    return f"${frac_from(value)}$"


def _tex(value):
    v = Fraction(value)
    return str(v.numerator) if v.denominator == 1 else tex_frac(v.numerator, v.denominator)


def _proper(max_den=6):
    d = random.randint(2, max_den)
    return Fraction(random.randint(1, d - 1), d)


# --- Right triangles -----------------------------------------------------------

@geometry_hs.geo_right_triangle_side.variant("angle_from_sides")
def _right_triangle_angle_from_sides():
    """Reverse: an acute angle from two sides (inverse trig)."""
    sides = {"opposite": None, "adjacent": None, "hypotenuse": None}
    a, b = random.randint(2, 20), random.randint(2, 20)
    sides["opposite"], sides["adjacent"] = a, b
    sides["hypotenuse"] = math.hypot(a, b)
    pair_ = random.choice([("opposite", "adjacent"), ("opposite", "hypotenuse"), ("adjacent", "hypotenuse")])
    if "hypotenuse" in pair_:
        h = random.randint(max(a, b) + 1, max(a, b) + 15)
        sides["hypotenuse"] = h
        other = pair_[0]
        value = sides[other]
        ratio = value / h
        func = "sin" if other == "opposite" else "cos"
        angle = math.degrees(math.asin(ratio) if func == "sin" else math.acos(ratio))
        where = "opposite" if other == "opposite" else "adjacent to"
        given = f"the side {where} angle $A$ is ${value}$ and the hypotenuse is ${h}$"
        frac_tex = rf"\frac{{{value}}}{{{h}}}"
    else:
        func = "tan"
        angle = math.degrees(math.atan2(a, b))
        given = f"the side opposite angle $A$ is ${a}$ and the side adjacent to it is ${b}$"
        frac_tex = rf"\frac{{{a}}}{{{b}}}"
    problem = f"In a right triangle, {given}. Find the measure of angle $A$ in degrees. {_ROUND}"
    solution = num(angle)
    s = Steps()
    s.step(rf"Pick the ratio that uses the two known sides: $\{func}$.", rf"\{func} A = {frac_tex}")
    s.step(rf"Undo $\{func}$ with its inverse.", rf"A = \{func}^{{-1}}\left({frac_tex}\right) \approx {solution}^\circ")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@geometry_hs.geo_solve_right_triangle_pythag.variant("isosceles_height")
def _pythag_isosceles_height():
    """The height of an isosceles triangle splits it into two right triangles."""
    p, q, r = random.choice(_PYTHAG_TRIPLES)
    k = random.randint(1, 3)
    half, height, side = (p * k, q * k, r * k) if random.random() < 0.5 else (q * k, p * k, r * k)
    problem = (
        f"An isosceles triangle has two sides of length ${side}$ and a base of length ${2 * half}$. "
        "What is its height (from the base to the opposite vertex)?"
    )
    solution = f"${height}$"
    s = Steps()
    s.step(f"The height meets the base at its midpoint, making two right triangles with legs "
           f"${half}$ and $h$ and hypotenuse ${side}$.")
    s.step("Use the Pythagorean theorem.", f"h^2 = {side}^2 - {half}^2 = {side ** 2 - half ** 2}")
    s.step("Take the square root.", f"h = {height}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.pythagorean_theorem.variant("isosceles_height")
def _pythagorean_isosceles_height():
    """Isosceles triangle height, usually irrational (rounded)."""
    half = random.randint(2, 15)
    side = random.randint(half + 1, half + 15)
    height = math.sqrt(side * side - half * half)
    problem = (
        f"An isosceles triangle has two sides of length ${side}$ and a base of length ${2 * half}$. "
        f"What is its height? {_ROUND}"
    )
    solution = f"${num(height)}$"
    s = Steps()
    s.step(f"The height splits the base in half, giving a right triangle with legs ${half}$ and "
           f"$h$ and hypotenuse ${side}$.")
    s.step("Use the Pythagorean theorem.", rf"h = \sqrt{{{side}^2 - {half}^2}} = \sqrt{{{side ** 2 - half ** 2}}} \approx {num(height)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@geometry_hs.geo_special_right_triangle.variant("in_shapes")
def _special_triangle_in_shapes():
    """Special right triangles hiding in a square's diagonal or an equilateral triangle."""
    s_len = random.randint(2, 20)
    s = Steps()
    if random.random() < 0.5:
        value = s_len * math.sqrt(2)
        problem = f"A square has sides of length ${s_len}$. How long is its diagonal? {_ROUND}"
        s.step("The diagonal splits the square into two 45-45-90 triangles; the diagonal is the "
               "hypotenuse.", rf"d = {s_len}\sqrt{{2}} \approx {num(value)}")
    else:
        value = s_len * math.sqrt(3) / 2
        problem = (f"An equilateral triangle has sides of length ${s_len}$. What is its height? {_ROUND}")
        s.step("The height splits it into two 30-60-90 triangles: the short leg is half a side and the "
               "height is the long leg.", rf"h = \frac{{{s_len}}}{{2}}\sqrt{{3}} \approx {num(value)}")
    solution = f"${num(value)}$"
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


# --- Circles ---------------------------------------------------------------------

@geometry_hs.geo_circle_equation_from_center_radius.variant("from_diameter")
def _circle_equation_from_diameter(max_center=9):
    """Hidden center and radius: the endpoints of a diameter."""
    h, k = _nonzero(-max_center, max_center), _nonzero(-max_center, max_center)
    dx, dy = random.randint(-6, 6), random.randint(-6, 6)
    if dx == 0 and dy == 0:
        dx = 3
    p1, p2 = (h - dx, k - dy), (h + dx, k + dy)
    r2 = dx * dx + dy * dy
    problem = (
        f"A diameter of a circle has endpoints $({p1[0]}, {p1[1]})$ and $({p2[0]}, {p2[1]})$. Write the "
        "equation of the circle in the form (x-h)^2 + (y-k)^2 = c."
    )
    solution = f"${_signed_factor('x', h)}^2 + {_signed_factor('y', k)}^2 = {r2}$"
    s = Steps()
    s.step("The center is the midpoint of the diameter.",
           rf"\left(\frac{{{p1[0]} + {paren(p2[0])}}}{{2}}, \frac{{{p1[1]} + {paren(p2[1])}}}{{2}}\right) = ({h}, {k})")
    s.step("The radius squared is the squared distance from the center to an endpoint.",
           f"r^2 = ({dx})^2 + ({dy})^2 = {r2}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_circle_center_radius_from_equation.variant("general_form_radius")
def _circle_general_form_radius(max_center=9, max_radius=10):
    """The radius from the expanded (general) form, by completing the square."""
    h, k = random.randint(-max_center, max_center), random.randint(-max_center, max_center)
    r = random.randint(1, max_radius)
    D, E, F = -2 * h, -2 * k, h * h + k * k - r * r

    def term(c, var):
        return "" if c == 0 else f" {'+' if c > 0 else '-'} {abs(c)}{var}"
    eq = f"x^2 + y^2{term(D, 'x')}{term(E, 'y')}{term(F, '')} = 0"
    problem = f"What is the radius of the circle ${eq}$?"
    solution = f"${r}$"
    s = Steps()
    s.step("Complete the square in $x$ and in $y$: add $(D/2)^2$ and $(E/2)^2$ to both sides.",
           f"(x{'' if h == 0 else (' - ' if h > 0 else ' + ') + str(abs(h))})^2 + "
           f"(y{'' if k == 0 else (' - ' if k > 0 else ' + ') + str(abs(k))})^2 = {h * h} + {k * k} - {paren(F)} = {r * r}")
    s.step("The right side is $r^2$.", f"r = \\sqrt{{{r * r}}} = {r}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.area_of_circle.variant("radius_from_area")
def _circle_radius_from_area():
    """Reverse: radius from an area written as a multiple of pi."""
    r = random.randint(1, 20)
    problem = rf"A circle has an area of ${r * r}\pi$ square units. What is its radius?"
    solution = f"{r}"
    s = Steps()
    s.formula("The area of a circle", r"A = \pi r^2")
    s.substitute(rf"{r * r}\pi = \pi r^2")
    s.step(r"Divide by $\pi$ and take the square root.", f"r = \\sqrt{{{r * r}}} = {r}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.circumference.variant("radius_from_circumference")
def _circle_radius_from_circumference():
    """Reverse: radius from a circumference written as a multiple of pi."""
    r = random.randint(1, 30)
    problem = rf"A circle has a circumference of ${2 * r}\pi$ units. What is its radius?"
    solution = f"{r}"
    s = Steps()
    s.formula("The circumference of a circle", r"C = 2\pi r")
    s.substitute(rf"{2 * r}\pi = 2\pi r")
    s.step(r"Divide both sides by $2\pi$.", f"r = {r}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.area_of_circle_given_center_and_point.variant("tangent_to_axis")
def _circle_tangent_to_axis():
    """Hidden radius: a circle tangent to an axis reaches it from its center."""
    h, k = _nonzero(-12, 12), _nonzero(-12, 12)
    axis = random.choice(["x", "y"])
    r = abs(k) if axis == "x" else abs(h)
    area = math.pi * r * r
    problem = (
        f"A circle with center $({h}, {k})$ is tangent to the {axis}-axis. What is its area? {_ROUND}"
    )
    solution = num(area)
    s = Steps()
    s.step(f"A circle tangent to the {axis}-axis touches it at one point, so the radius is the "
           f"distance from the center to that axis: the {'y' if axis == 'x' else 'x'}-coordinate's "
           "absolute value.", f"r = {r}")
    s.formula("The area", rf"A = \pi ({r})^2 = {r * r}\pi \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_geometry_gen.sector_area.variant("angle_from_area")
def _sector_angle_from_area():
    """Reverse: the central angle from a sector's area (a multiple of pi)."""
    while True:
        r = random.randint(2, 12)
        theta = random.choice(range(10, 360, 5))
        if (theta * r * r) % 360 == 0:
            break
    k = theta * r * r // 360
    problem = (
        rf"A sector of a circle with radius ${r}$ has an area of ${k}\pi$ square units. What is its "
        "central angle, in degrees?"
    )
    solution = f"{theta}"
    s = Steps()
    s.formula("The area of a sector", r"A = \frac{\theta}{360}\pi r^2")
    s.substitute(rf"{k}\pi = \frac{{\theta}}{{360}}\pi ({r})^2")
    s.step(rf"Divide by ${r * r}\pi$ and multiply by $360$.", rf"\theta = \frac{{{k} \times 360}}{{{r * r}}} = {theta}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.arc_length.variant("angle_from_arc")
def _arc_angle_from_arc():
    """Reverse: the central angle from an arc length (a multiple of pi)."""
    while True:
        r = random.randint(2, 18)
        theta = random.choice(range(10, 360, 5))
        if (theta * 2 * r) % 360 == 0:
            break
    k = theta * 2 * r // 360
    problem = (
        rf"An arc of a circle with radius ${r}$ has length ${k}\pi$. What is its central angle, in "
        "degrees?"
    )
    solution = f"{theta}"
    s = Steps()
    s.formula("The length of an arc", r"s = \frac{\theta}{360} \cdot 2\pi r")
    s.substitute(rf"{k}\pi = \frac{{\theta}}{{360}} \cdot 2\pi({r})")
    s.step(rf"Divide by ${2 * r}\pi$ and multiply by $360$.", rf"\theta = \frac{{{k} \times 360}}{{{2 * r}}} = {theta}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_inscribed_angle.variant("cyclic_quadrilateral")
def _inscribed_cyclic_quadrilateral():
    """Opposite angles of a quadrilateral inscribed in a circle are supplementary."""
    a = random.randint(40, 140)
    problem = (
        f"Quadrilateral $ABCD$ is inscribed in a circle. Angle $A$ measures ${a}^\\circ$. What is "
        "the measure of angle $C$, in degrees?"
    )
    solution = f"${180 - a}$"
    s = Steps()
    s.step("Angles $A$ and $C$ are opposite, so together they intercept the whole circle: their "
           "arcs add to $360^\\circ$, and each angle is half its arc.")
    s.step("So opposite angles of an inscribed quadrilateral add to $180^\\circ$.", f"C = 180 - {a} = {180 - a}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_circle_segments.variant("secant_secant")
def _circle_secant_secant():
    """Two secants from one point: external times whole is the same for both."""
    while True:
        a, whole1 = random.randint(2, 10), random.randint(4, 20)
        c = random.choice([v for v in range(2, 12) if v != a])
        whole2 = Fraction(a * whole1, c)
        if whole1 > a and whole2 > c:   # each whole secant is longer than its outside part
            break
    problem = (
        f"Two secants are drawn to a circle from the same outside point. The first has an external "
        f"segment of ${a}$ and a total length of ${whole1}$. The second has an external segment of "
        f"${c}$. What is the total length of the second secant? Round to the nearest thousandth if "
        "necessary."
    )
    solution = f"${num(whole2)}$"
    s = Steps()
    s.step("For two secants from one point, external segment times whole secant is the same.",
           rf"{a} \times {whole1} = {c} \times w")
    s.step(f"Divide by ${c}$.", rf"w = \frac{{{a * whole1}}}{{{c}}} {'=' if whole2.denominator in (1, 2, 4, 5, 8) else r'\approx'} {num(whole2)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Transformations (reverse: find the pre-image) --------------------------------

@geometry_hs.geo_translate_point.variant("preimage")
def _translate_preimage():
    """Reverse: where was the point before the translation?"""
    x, y = random.randint(-9, 9), random.randint(-9, 9)
    a, b = random.randint(-8, 8), random.randint(-8, 8)
    image = (x + a, y + b)
    problem = (
        rf"A point is translated by the vector $\langle {a}, {b} \rangle$, and its image is "
        f"$({image[0]}, {image[1]})$. What was the original point? {_PAIR_HINT}"
    )
    solution = pair(x, y)
    s = Steps()
    s.step("Undo the translation: subtract the vector from the image.",
           f"({image[0]} - {paren(a)}, {image[1]} - {paren(b)}) = ({x}, {y})")
    s.answer(solution)
    return problem, solution, s.done()


_REFLECT = {"x-axis": lambda x, y: (x, -y), "y-axis": lambda x, y: (-x, y), "line y = x": lambda x, y: (y, x)}


@geometry_hs.geo_reflect_point.variant("preimage")
def _reflect_preimage():
    """Reverse: reflecting is its own inverse."""
    x, y = random.randint(-9, 9), random.randint(-9, 9)
    line = random.choice(list(_REFLECT))
    image = _REFLECT[line](x, y)
    problem = (
        f"A point is reflected over the {line}, and its image is $({image[0]}, {image[1]})$. What was "
        f"the original point? {_PAIR_HINT}"
    )
    solution = pair(x, y)
    s = Steps()
    s.step(f"Reflecting twice over the {line} returns a point to where it started, so reflect the "
           "image back.", f"({image[0]}, {image[1]}) \\to ({x}, {y})")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_rotate_point.variant("preimage")
def _rotate_preimage():
    """Reverse: undo a counterclockwise rotation about the origin."""
    x, y = random.randint(-9, 9), random.randint(-9, 9)
    deg = random.choice([90, 180, 270])
    image = {90: (-y, x), 180: (-x, -y), 270: (y, -x)}[deg]
    problem = (
        f"A point is rotated ${deg}^\\circ$ counterclockwise about the origin, and its image is "
        f"$({image[0]}, {image[1]})$. What was the original point? {_PAIR_HINT}"
    )
    solution = pair(x, y)
    s = Steps()
    s.step(f"Undo it by rotating the image ${deg}^\\circ$ clockwise, which is the same as "
           f"${360 - deg}^\\circ$ counterclockwise.", f"({image[0]}, {image[1]}) \\to ({x}, {y})")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_dilate_point.variant("preimage")
def _dilate_preimage():
    """Reverse: undo a dilation centered at the origin."""
    k = random.choice([2, 3, 4, 5])
    x, y = random.randint(-6, 6), random.randint(-6, 6)
    image = (k * x, k * y)
    problem = (
        f"A point is dilated by a scale factor of ${k}$ centered at the origin, and its image is "
        f"$({image[0]}, {image[1]})$. What was the original point? {_PAIR_HINT}"
    )
    solution = pair(x, y)
    s = Steps()
    s.step(f"Undo the dilation: divide each coordinate by ${k}$.",
           rf"\left(\frac{{{image[0]}}}{{{k}}}, \frac{{{image[1]}}}{{{k}}}\right) = ({x}, {y})")
    s.answer(solution)
    return problem, solution, s.done()


# --- Probability (geometry course) ---------------------------------------------------

@geometry_hs.geo_conditional_probability_table.variant("missing_cell")
def _conditional_missing_cell():
    """A cell is missing but its row total is given."""
    ax, ay = random.randint(1, 30), random.randint(1, 30)
    row = ax + ay
    ask_x = random.random() < 0.5
    known, unknown = (ay, "X") if ask_x else (ax, "Y")
    problem = (
        f"A two-way table shows that ${row}$ people are in group A, and ${known}$ of them chose "
        f"option {'Y' if ask_x else 'X'}. Everyone chose X or Y. Find $P({unknown} \\mid A)$ as a "
        "reduced fraction."
    )
    count = row - known
    value = Fraction(count, row)
    solution = _frac(value)
    s = Steps()
    s.step("Find the missing count: everyone in A chose X or Y.", f"{row} - {known} = {count}")
    reduced = "" if value.denominator == row else f" = {_tex(value)}"
    s.step("Divide by the number in group A.",
           rf"P({unknown} \mid A) = \frac{{{count}}}{{{row}}}{reduced}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_compound_probability.variant("missing_probability")
def _compound_missing_probability():
    """Reverse: P(B) from P(A) and P(A or B), for independent events."""
    pa, pb = _proper(), _proper()
    p_or = pa + pb - pa * pb
    problem = (
        f"Events $A$ and $B$ are independent, with $P(A) = {frac_from(pa)}$ and "
        f"$P(A \\text{{ or }} B) = {frac_from(p_or)}$. Find $P(B)$ as a reduced fraction."
    )
    solution = _frac(pb)
    s = Steps()
    s.step("For independent events, $P(A \\text{ or } B) = P(A) + P(B) - P(A)P(B)$.",
           f"{_tex(p_or)} = {_tex(pa)} + P(B) - {_tex(pa)}P(B)")
    s.step("Collect the $P(B)$ terms.", f"{_tex(p_or - pa)} = {_tex(1 - pa)}P(B)")
    s.step(f"Divide by ${_tex(1 - pa)}$.", f"P(B) = {_tex(pb)}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_expected_value.variant("fair_price")
def _expected_fair_price():
    """The price that makes a game fair is its expected payout."""
    prizes = [random.choice([0, 0, 1, 2, 3, 5, 10, 20]) for _ in range(4)]
    if not any(prizes):
        prizes[0] = 5
    ev = Fraction(sum(prizes), 4)
    problem = (
        "A spinner has $4$ equal sections. Landing on them pays "
        + ", ".join(f"${p}$" for p in prizes)
        + " dollars. What price to play makes the game fair (expected profit $0$)? Give your answer "
        "in dollars, for example 1.25."
    )
    solution = f"${num(ev)}$"
    s = Steps()
    s.step("A game is fair when the price equals the expected payout.")
    s.step("Each section has probability $\\frac{1}{4}$.",
           rf"E = \frac{{{' + '.join(map(str, prizes))}}}{{4}} = {num(ev)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Similarity and scale -------------------------------------------------------------

@geometry_hs.geo_similar_triangle_side.variant("shadows")
def _similar_shadows():
    """Similar triangles in context: heights and shadows at the same time of day."""
    h1 = random.randint(4, 7)
    s1 = random.randint(2, 9)
    s2 = random.randint(10, 60)
    tree = Fraction(h1 * s2, s1)
    problem = (
        f"A ${h1}$-foot person casts a ${s1}$-foot shadow. At the same time, a tree casts a "
        f"${s2}$-foot shadow. How tall is the tree, in feet? Round to the nearest thousandth if "
        "necessary."
    )
    solution = f"${num(tree)}$"
    s = Steps()
    s.step("The sun makes the same angle with both, so the triangles are similar: height over "
           "shadow is the same.", rf"\frac{{{h1}}}{{{s1}}} = \frac{{t}}{{{s2}}}")
    s.step(f"Multiply both sides by ${s2}$.", rf"t = \frac{{{h1} \times {s2}}}{{{s1}}} {'=' if tree.denominator in (1, 2, 4, 5, 8) else r'\approx'} {num(tree)}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_scale_factor_ratio.variant("reverse")
def _scale_ratio_reverse():
    """Reverse: from an area ratio to lengths, or a volume ratio to areas."""
    a, b = random.sample(range(1, 7), 2)
    if math.gcd(a, b) != 1:
        a, b = 2, 3
    k = Fraction(a, b)
    s = Steps()
    if random.random() < 0.5:
        given, answer = k ** 2, k
        problem = (f"Two similar figures have areas in the ratio ${frac_from(given)}$. What is the "
                   f"ratio of their corresponding lengths? {_FRACTION_HINT}")
        s.step("Areas scale by the square of the length ratio, so take the square root.",
               rf"\sqrt{{{_tex(given)}}} = {_tex(k)}")
    else:
        given, answer = k ** 3, k ** 2
        problem = (f"Two similar solids have volumes in the ratio ${frac_from(given)}$. What is the "
                   f"ratio of their surface areas? {_FRACTION_HINT}")
        s.step("Volumes scale by the cube of the length ratio; take the cube root to get the length "
               "ratio.", rf"\sqrt[3]{{{_tex(given)}}} = {_tex(k)}")
        s.step("Areas scale by its square.", rf"\left({_tex(k)}\right)^2 = {_tex(answer)}")
    solution = _frac(answer)
    s.answer(solution)
    return problem, solution, s.done()


# --- Areas and volumes (geometry course) ----------------------------------------------

@geometry_hs.geo_regular_polygon_area.variant("hexagon_triangles")
def _hexagon_from_triangles():
    """A regular hexagon is six equilateral triangles."""
    side = random.randint(2, 20)
    area = 3 * math.sqrt(3) / 2 * side * side
    problem = (
        f"A regular hexagon has sides of length ${side}$. Split it into equilateral triangles to find "
        f"its area. {_ROUND}"
    )
    solution = f"${num(area)}$"
    s = Steps()
    s.step("Lines from the center to the vertices split a regular hexagon into $6$ equilateral "
           f"triangles with side ${side}$.")
    s.formula("The area of an equilateral triangle", rf"\frac{{\sqrt{{3}}}}{{4}}({side})^2")
    s.step("Multiply by $6$.", rf"6 \cdot \frac{{\sqrt{{3}}}}{{4}}({side})^2 \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@geometry_hs.geo_composite_solid.variant("hollow_pipe")
def _composite_hollow_pipe():
    """A hollow solid is the outer solid minus the hole."""
    r = random.randint(1, 8)
    R = r + random.randint(1, 5)
    L = random.randint(2, 30)
    volume = math.pi * (R * R - r * r) * L
    problem = (
        f"A pipe is a cylinder of radius ${R}$ and length ${L}$ with a cylindrical hole of radius ${r}$ "
        f"through its center. What volume of material does it contain? {_ROUND}"
    )
    solution = f"${num(volume)}$"
    s = Steps()
    s.step("The material is the outer cylinder minus the hole.",
           rf"V = \pi({R})^2({L}) - \pi({r})^2({L}) = {(R * R - r * r) * L}\pi")
    s.step("Evaluate.", rf"{(R * R - r * r) * L}\pi \approx {num(volume)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@geometry_hs.geo_frustum_volume.variant("difference_of_cones")
def _frustum_difference_of_cones():
    """A frustum is a big cone with a small cone cut off the top."""
    # Whole-number cones: the removed top is the big cone scaled down by 1/m.
    small_r, small_h = random.randint(1, 6), random.randint(2, 8)
    m = random.randint(2, 4)
    R, H = m * small_r, m * small_h
    volume = math.pi / 3 * (R * R * H - small_r * small_r * small_h)
    problem = (
        f"A cone with base radius ${R}$ and height ${H}$ has its top cut off by a plane parallel to the "
        f"base. The removed top is a cone with base radius ${num(small_r)}$ and height ${num(small_h)}$. "
        f"What is the volume of the remaining frustum? {_ROUND}"
    )
    solution = f"${num(volume)}$"
    s = Steps()
    s.step("The frustum is the big cone minus the small cone.",
           rf"V = \frac{{1}}{{3}}\pi({R})^2({H}) - \frac{{1}}{{3}}\pi({num(small_r)})^2({num(small_h)})")
    s.step("Evaluate.", rf"V \approx {num(volume)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@geometry_hs.geo_polygon_area_vertices.variant("missing_vertex")
def _polygon_missing_vertex():
    """Reverse: a vertex coordinate from the area."""
    b = random.randint(2, 12)
    k = random.randint(1, 12)
    p = random.randint(-5, 15)
    area = Fraction(b * k, 2)
    problem = (
        f"A triangle has vertices $(0, 0)$, $({b}, 0)$, and $({p}, k)$ with $k > 0$. Its area is "
        f"${num(area)}$ square units. What is $k$?"
    )
    solution = f"${k}$"
    s = Steps()
    s.step(f"The side from $(0, 0)$ to $({b}, 0)$ is a base of length ${b}$ on the x-axis, so the "
           "height is $k$.")
    s.formula("The area of a triangle", rf"{num(area)} = \frac{{1}}{{2}}({b})k")
    s.step(f"Solve for $k$.", rf"k = \frac{{2 \times {num(area)}}}{{{b}}} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Coordinate geometry ----------------------------------------------------------------

@lib_geometry_gen.distance_two_points.variant("missing_coordinate")
def _distance_missing_coordinate():
    """Reverse: a coordinate from the distance (exactly one answer above the point)."""
    p, q, r = random.choice(_PYTHAG_TRIPLES[:4])
    k = random.randint(1, 2)
    dx, dy, d = (p * k, q * k, r * k) if random.random() < 0.5 else (q * k, p * k, r * k)
    x1, y1 = random.randint(-9, 9), random.randint(-9, 9)
    x2 = x1 + dx * random.choice([1, -1])
    y2 = y1 + dy
    problem = (
        f"The distance from $({x1}, {y1})$ to $({x2}, k)$ is ${d}$, and $k > {y1}$. What is $k$?"
    )
    solution = f"{y2}"
    s = Steps()
    s.formula("The distance formula", rf"{d}^2 = ({x2} - {paren(x1)})^2 + (k - {paren(y1)})^2")
    s.step("Simplify.", f"{d * d} = {dx * dx} + (k - {paren(y1)})^2")
    s.step(f"So $(k - {paren(y1)})^2 = {dy * dy}$; with $k > {y1}$, take the positive root.",
           f"k = {y1} + {dy} = {y2}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.midpoint_of_two_points.variant("missing_endpoint")
def _midpoint_missing_endpoint():
    """Reverse: an endpoint from the midpoint and the other endpoint."""
    a = (random.randint(-12, 12), random.randint(-12, 12))
    m = (random.randint(-10, 10), random.randint(-10, 10))
    b = (2 * m[0] - a[0], 2 * m[1] - a[1])
    problem = (
        f"$M({m[0]}, {m[1]})$ is the midpoint of segment $AB$, and $A$ is $({a[0]}, {a[1]})$. Find $B$. "
        f"{_PAIR_HINT}"
    )
    solution = pair(*b)
    s = Steps()
    s.step("The midpoint averages the coordinates, so each coordinate of $B$ is twice the midpoint's "
           "minus $A$'s.", f"B = (2({m[0]}) - {paren(a[0])}, 2({m[1]}) - {paren(a[1])}) = ({b[0]}, {b[1]})")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.euclidian_norm.variant("missing_component")
def _norm_missing_component():
    """Reverse: a vector's missing (positive) component from its length."""
    p, q, r = random.choice(_PYTHAG_TRIPLES[:4])
    k = random.randint(1, 3)
    known, missing, length = (p * k, q * k, r * k) if random.random() < 0.5 else (q * k, p * k, r * k)
    sign = random.choice([1, -1])
    problem = (
        f"The vector $({sign * known}, a)$ has length ${length}$, and $a > 0$. What is $a$?"
    )
    solution = f"{missing}"
    s = Steps()
    s.step("The length is the square root of the sum of squared components.",
           f"{length}^2 = {paren(sign * known)}^2 + a^2")
    s.step("Solve for $a$.", f"a^2 = {length * length} - {known * known} = {missing * missing} \\Rightarrow a = {missing}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.equation_of_line_from_two_points.variant("collinear")
def _line_collinear():
    """For what k are three points on one line?"""
    m = _nonzero(-6, 6)
    x1, y1 = random.randint(-8, 8), random.randint(-8, 8)
    x2, x3 = random.sample([v for v in range(-8, 9) if v != x1], 2)
    y2, k = y1 + m * (x2 - x1), y1 + m * (x3 - x1)
    problem = (
        f"The points $({x1}, {y1})$, $({x2}, {y2})$, and $({x3}, k)$ lie on one line. What is $k$?"
    )
    solution = f"{k}"
    s = Steps()
    s.step("Find the slope from the two known points.",
           rf"m = \frac{{{y2} - {paren(y1)}}}{{{x2} - {paren(x1)}}} = {m}")
    s.step(f"The third point must give the same slope from $({x1}, {y1})$.",
           f"k = {y1} + {m}({x3} - {paren(x1)}) = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.perimeter_of_polygons.variant("missing_side")
def _perimeter_missing_side():
    """Reverse: one side from the perimeter."""
    n = random.randint(3, 7)
    sides = [random.randint(2, 20) for _ in range(n)]
    names = {3: "triangle", 4: "quadrilateral", 5: "pentagon", 6: "hexagon", 7: "heptagon"}
    known = ", ".join(f"${v}$" for v in sides[:-1])
    problem = (
        f"A {names[n]} has a perimeter of ${sum(sides)}$ cm. {n - 1} of its sides measure {known} cm. "
        "How long is the last side, in cm?"
    )
    solution = f"{sides[-1]}"
    s = Steps()
    s.step("Subtract the known sides from the perimeter.",
           f"{sum(sides)} - ({' + '.join(map(str, sides[:-1]))}) = {sum(sides)} - {sum(sides[:-1])} = {sides[-1]}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.valid_triangle.variant("count_third_sides")
def _triangle_count_third_sides():
    """How many whole-number third sides the triangle inequality allows."""
    a, b = random.randint(2, 20), random.randint(2, 20)
    count = (a + b - 1) - abs(a - b)
    problem = (
        f"A triangle has sides of length ${a}$ and ${b}$. How many whole-number lengths are possible "
        "for the third side?"
    )
    solution = f"{count}"
    s = Steps()
    s.step("The third side must be longer than the difference and shorter than the sum of the other "
           "two.", f"{abs(a - b)} < c < {a + b}")
    s.step("Count the whole numbers strictly between them.", f"{a + b - 1} - {abs(a - b)} = {count}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Angles ---------------------------------------------------------------------------

@lib_angles_gen.angle_regular_polygon.variant("sides_from_angle")
def _polygon_sides_from_angle():
    """Reverse: the number of sides from one interior angle."""
    n = random.choice([n for n in range(3, 37) if 360 % n == 0])
    angle = 180 - 360 // n
    problem = f"Each interior angle of a regular polygon measures ${angle}^\\circ$. How many sides does it have?"
    solution = f"{n}"
    s = Steps()
    s.step("Each exterior angle is the supplement of an interior angle.", f"180 - {angle} = {180 - angle}")
    s.step("The exterior angles of any polygon add to $360^\\circ$.", rf"n = \frac{{360}}{{{180 - angle}}} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.sum_of_polygon_angles.variant("sides_from_sum")
def _polygon_sides_from_sum():
    """Reverse: the number of sides from the interior-angle sum."""
    n = random.randint(3, 20)
    total = (n - 2) * 180
    problem = f"The interior angles of a polygon add up to ${total}^\\circ$. How many sides does it have?"
    solution = f"{n}"
    s = Steps()
    s.formula("The interior angle sum", f"(n - 2) \\times 180 = {total}")
    s.step("Divide by $180$, then add $2$.", f"n = {total // 180} + 2 = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.complementary_and_supplementary_angle.variant("complement_to_supplement")
def _complement_to_supplement():
    """From an angle's complement to its supplement (always 90 more)."""
    comp = random.randint(1, 89)
    problem = f"The complement of an angle measures ${comp}^\\circ$. What is the measure of its supplement?"
    solution = f"{comp + 90}"
    s = Steps()
    s.step("Find the angle from its complement.", f"90 - {comp} = {90 - comp}")
    s.step("Find its supplement.", f"180 - {90 - comp} = {comp + 90}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.third_angle_of_triangle.variant("isosceles")
def _third_angle_isosceles():
    """Isosceles triangles: base angles from the vertex angle, or the reverse."""
    base = random.randint(20, 85)
    vertex = 180 - 2 * base
    if random.random() < 0.5:
        problem = (f"An isosceles triangle has a vertex angle of ${vertex}^\\circ$. What is the measure "
                   "of each base angle?")
        answer = base
        s = Steps()
        s.step("The two base angles are equal, and all three angles add to $180^\\circ$.",
               rf"\frac{{180 - {vertex}}}{{2}} = {base}")
    else:
        problem = (f"Each base angle of an isosceles triangle measures ${base}^\\circ$. What is the "
                   "measure of the vertex angle?")
        answer = vertex
        s = Steps()
        s.step("The base angles are equal; subtract both from $180^\\circ$.", f"180 - 2({base}) = {vertex}")
    solution = f"{answer}"
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.fourth_angle_of_quadrilateral.variant("parallelogram")
def _fourth_angle_parallelogram():
    """Parallelogram angles: consecutive are supplementary, opposite are equal."""
    a = random.randint(30, 150)
    if a == 90:
        a = 70
    which = random.choice(["B", "C", "D"])
    answer = a if which == "C" else 180 - a
    problem = (
        f"In parallelogram $ABCD$, angle $A$ measures ${a}^\\circ$. What is the measure of angle "
        f"${which}$?"
    )
    solution = f"{answer}"
    s = Steps()
    if which == "C":
        s.step("Opposite angles of a parallelogram are equal.", f"C = A = {a}")
    else:
        s.step(f"Angles $A$ and ${which}$ are consecutive, and consecutive angles of a parallelogram "
               "are supplementary.", f"{which} = 180 - {a} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.degree_to_rad.variant("exact_multiple_of_pi")
def _degrees_exact_pi():
    r"""An exact radian measure as a multiple of $\pi$: $150^\circ = k\pi$."""
    deg = random.choice([d for d in range(15, 721, 15) if d % 180])
    k = Fraction(deg, 180)
    problem = rf"Write ${deg}^\circ$ in radians as $k\pi$. What is $k$? {_FRACTION_HINT}"
    solution = frac_from(k)
    s = Steps()
    s.step(r"Multiply by $\frac{\pi}{180}$.", rf"{deg} \times \frac{{\pi}}{{180}} = {_tex(k)}\pi")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.radian_to_deg.variant("exact_multiple_of_pi")
def _radians_exact_pi():
    r"""An exact multiple of $\pi$ radians in degrees."""
    k = Fraction(random.randint(1, 23), random.choice([2, 3, 4, 6, 12]))
    deg = k * 180
    problem = rf"Convert ${_pi_times(k)}$ radians to degrees."
    solution = num(deg)
    s = Steps()
    s.step(r"Multiply by $\frac{180}{\pi}$.", rf"{_pi_times(k)} \times \frac{{180}}{{\pi}} = {num(deg)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.angle_btw_vectors.variant("dot_from_angle")
def _vectors_dot_from_angle():
    """Reverse: the dot product from the lengths and the angle between them."""
    a, b = random.randint(1, 12), random.randint(1, 12)
    theta = random.choice([0, 30, 45, 60, 90, 120, 135, 150, 180])
    value = a * b * math.cos(math.radians(theta))
    problem = (
        f"Vectors $u$ and $v$ have lengths ${a}$ and ${b}$, and the angle between them is "
        f"${theta}^\\circ$. What is $u \\cdot v$? {_ROUND}"
    )
    solution = num(value)
    s = Steps()
    s.formula("The dot product", rf"u \cdot v = |u||v|\cos\theta = {a} \times {b} \times \cos {theta}^\circ")
    s.step("Evaluate.", f"u \\cdot v \\approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.complex_to_polar.variant("argument_degrees")
def _complex_argument_degrees():
    """The argument in degrees, watching the quadrant."""
    a, b = _nonzero(-12, 12), _nonzero(-12, 12)
    theta = math.degrees(math.atan2(b, a))
    problem = (
        f"What is the argument of ${a} {'+' if b > 0 else '-'} {abs(b)}i$, in degrees between $-180$ "
        f"and $180$? {_ROUND}"
    )
    solution = num(theta)
    quadrant = {(True, True): "I", (False, True): "II", (False, False): "III", (True, False): "IV"}[(a > 0, b > 0)]
    s = Steps()
    s.step(f"The point $({a}, {b})$ is in quadrant {quadrant}, so check the angle lands there.")
    s.step("Use the angle of the point $(a, b)$ measured from the positive real axis.",
           rf"\theta = \operatorname{{atan2}}({b}, {a}) \approx {solution}^\circ")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_angles_gen.trig_differentiation.variant("value_at_angle")
def _trig_derivative_value():
    """The derivative's value at a special angle."""
    cases = [
        ("sin", r"\cos x", lambda x: math.cos(x)),
        ("cos", r"-\sin x", lambda x: -math.sin(x)),
        ("tan", r"\sec^2 x", lambda x: 1 / math.cos(x) ** 2),
        ("cot", r"-\csc^2 x", lambda x: -1 / math.sin(x) ** 2),
    ]
    angles = [(r"\frac{\pi}{6}", math.pi / 6), (r"\frac{\pi}{4}", math.pi / 4), (r"\frac{\pi}{3}", math.pi / 3)]
    func, deriv, f = random.choice(cases)
    label, x = random.choice(angles)
    value = f(x)
    problem = (
        rf"If $f(x) = \{func} x$, what is $f'\left({label}\right)$? Round to the nearest thousandth if "
        "necessary."
    )
    solution = num(value)
    s = Steps()
    s.step(f"The derivative of $\\{func} x$ is ${deriv}$.")
    s.step("Evaluate at the angle.", rf"f'\left({label}\right) \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.fraction_to_decimal.variant("terminates")
def _fraction_terminates():
    """Does a fraction's decimal terminate? Only 2s and 5s in the reduced denominator."""
    d = random.randint(2, 99)
    n = random.randint(1, 3 * d)
    fr = Fraction(n, d)
    rest = fr.denominator
    for p in (2, 5):
        while rest % p == 0:
            rest //= p
    answer = "yes" if rest == 1 else "no"
    problem = f"Does the decimal form of ${n}/{d}$ terminate? Answer yes or no."
    s = Steps()
    s.step("Reduce the fraction.", rf"\frac{{{n}}}{{{d}}} = {_tex(fr)}")
    s.step("A reduced fraction's decimal terminates exactly when its denominator has no prime "
           f"factors other than $2$ and $5$. Here the denominator is ${fr.denominator}$.")
    s.answer(answer)
    return problem, answer, s.done()


@lib_angles_gen.celsius_to_fahrenheit.variant("change")
def _celsius_change():
    """A temperature change: 1 degree C is 1.8 degrees F, and the +32 cancels."""
    c = random.randint(1, 40)
    f = Fraction(9, 5) * c
    problem = (
        f"The temperature rises by ${c}$ degrees Celsius. By how many degrees Fahrenheit does it rise? "
        f"{_ROUND}"
    )
    solution = num(f)
    s = Steps()
    s.step(r"In $F = \frac{9}{5}C + 32$ the $32$ is the same before and after, so a change only "
           r"multiplies by $\frac{9}{5}$.", rf"\frac{{9}}{{5}} \times {c} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry.angle_sum.variant("tangent")
def _angle_sum_tangent():
    """tan(A + B) from tangents read off right-triangle ratios."""
    while True:
        (p1, q1, _), (p2, q2, _) = random.choice(_PYTHAG_TRIPLES[:4]), random.choice(_PYTHAG_TRIPLES[:4])
        t1, t2 = Fraction(p1, q1), Fraction(p2, q2)
        if t1 * t2 != 1:
            break
    value = (t1 + t2) / (1 - t1 * t2)
    problem = (
        f"For acute angles $A$ and $B$, $\\tan A = {frac_from(t1)}$ and $\\tan B = {frac_from(t2)}$. "
        f"Find $\\tan(A + B)$. Give your answer as a reduced fraction a/b or an integer."
    )
    solution = frac_from(value)
    s = Steps()
    s.formula("The tangent sum formula", r"\tan(A + B) = \frac{\tan A + \tan B}{1 - \tan A \tan B}")
    s.substitute(rf"\frac{{{_tex(t1)} + {_tex(t2)}}}{{1 - {_tex(t1)} \cdot {_tex(t2)}}} = "
                 rf"\frac{{{_tex(t1 + t2)}}}{{{_tex(1 - t1 * t2)}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.vector_dot.variant("perpendicular_parameter")
def _dot_perpendicular_parameter():
    """For what k are two vectors perpendicular (dot product zero)?"""
    while True:
        a, c = _nonzero(-6, 6), _nonzero(-6, 6)
        ds = [d for d in range(-9, 10) if d and (a * c) % d == 0]
        d = random.choice(ds)
        k = -a * c // d
        if abs(k) <= 20:
            break
    problem = (
        f"For what value of $k$ are the vectors $({a}, k)$ and $({c}, {d})$ perpendicular?"
    )
    solution = f"{k}"
    s = Steps()
    s.step("Perpendicular vectors have a dot product of $0$.", f"{a}({c}) + k({d}) = 0")
    s.step("Solve for $k$.", rf"{d}k = {-a * c} \Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


# =============================================================================
# Further variants (beyond each topic's first new question type)
# =============================================================================

def _exact_or_round(value):
    """The answer text and its lead: rounded only when it isn't already short."""
    text = num(value)
    return text, (_ROUNDED if text != num(value, 6) else "The answer is")


# --- Right triangles -------------------------------------------------------------------

@geometry_hs.geo_right_triangle_side.variant("complementary_ratio")
def _right_triangle_complementary_ratio():
    """In a right triangle sin A = cos B: the side opposite A is adjacent to B."""
    p, q, r = random.choice(_PYTHAG_TRIPLES)
    given, ask = random.choice([("sin A", "cos B"), ("cos A", "sin B"), ("tan A", "cot B")])
    value = {"sin A": Fraction(p, r), "cos A": Fraction(q, r), "tan A": Fraction(p, q)}[given]
    problem = (
        f"In right triangle $ABC$ with the right angle at $C$, $\\{given.split()[0]} A = {frac_from(value)}$. "
        f"What is $\\{ask.split()[0]} B$? {_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    s.step("Angles $A$ and $B$ are complementary, so the side opposite $A$ is the side adjacent to $B$.")
    s.step(f"So ${given}$ and ${ask}$ are the same ratio.", rf"\{ask.split()[0]} B = \{given.split()[0]} A = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_right_triangle_side.variant("angle_of_elevation")
def _right_triangle_elevation():
    """Height from a distance and an angle of elevation."""
    d = random.randint(10, 200)
    theta = random.randint(10, 75)
    h = d * math.tan(math.radians(theta))
    problem = (
        f"From a point ${d}$ meters from the base of a tower, the angle of elevation to its top is "
        f"${theta}^\\circ$. How tall is the tower, in meters? {_ROUND}"
    )
    solution = num(h)
    s = Steps()
    s.step("The height is opposite the angle and the distance is adjacent, so use tangent.",
           rf"\tan {theta}^\circ = \frac{{h}}{{{d}}}")
    s.step(f"Multiply by ${d}$.", rf"h = {d}\tan {theta}^\circ \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@geometry_hs.geo_solve_right_triangle_pythag.variant("ladder")
def _pythag_ladder():
    """A ladder against a wall (whole-number answer)."""
    p, q, r = random.choice(_PYTHAG_TRIPLES[:4])
    k = random.randint(1, 2)
    base, height, ladder = (p * k, q * k, r * k) if random.random() < 0.5 else (q * k, p * k, r * k)
    problem = (
        f"A ${ladder}$-foot ladder leans against a wall with its foot ${base}$ feet from the wall. How high "
        "up the wall does it reach, in feet?"
    )
    solution = f"${height}$"
    s = Steps()
    s.step("The wall, the ground and the ladder form a right triangle with the ladder as hypotenuse.",
           f"h^2 = {ladder}^2 - {base}^2 = {ladder ** 2 - base ** 2}")
    s.step("Take the square root.", f"h = {height}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_solve_right_triangle_pythag.variant("is_right")
def _pythag_is_right():
    """The converse: do three sides make a right triangle?"""
    p, q, r = random.choice(_PYTHAG_TRIPLES)
    k = random.randint(1, 3)
    sides = [p * k, q * k, r * k]
    right = random.random() < 0.5
    if not right:
        sides[random.randrange(3)] += random.choice([-1, 1])
    a, b, c = sorted(sides)
    problem = f"Is a triangle with sides ${a}$, ${b}$, and ${c}$ a right triangle? Answer yes or no."
    answer = "yes" if a * a + b * b == c * c else "no"
    s = Steps()
    s.step("By the converse of the Pythagorean theorem, check whether the two shorter sides' squares add "
           "to the longest side's square.", f"{a}^2 + {b}^2 = {a * a + b * b}, \\quad {c}^2 = {c * c}")
    s.answer(answer)
    return problem, answer, s.done()


@lib_solids_gen.pythagorean_theorem.variant("space_diagonal")
def _pythagorean_space_diagonal():
    """The longest diagonal of a box."""
    l, w, h = (random.randint(1, 15) for _ in range(3))
    d = math.sqrt(l * l + w * w + h * h)
    problem = (
        f"A box measures ${l}$ by ${w}$ by ${h}$. How long is the diagonal from one corner to the opposite "
        f"corner? {_ROUND}"
    )
    solution, lead = _exact_or_round(d)
    solution = f"${solution}$"
    s = Steps()
    s.step("First the diagonal of the base, then use it as a leg with the height.",
           rf"d^2 = ({l}^2 + {w}^2) + {h}^2 = {l * l + w * w + h * h}")
    s.step("Take the square root.", rf"d = \sqrt{{{l * l + w * w + h * h}}} \approx {num(d)}")
    s.answer(solution, lead=lead)
    return problem, solution, s.done()


@geometry_hs.geo_special_right_triangle.variant("leg_from_hypotenuse")
def _special_leg_from_hypotenuse():
    """Reverse: a 45-45-90 leg from its hypotenuse."""
    h = random.randint(2, 30)
    leg = h / math.sqrt(2)
    problem = f"A 45-45-90 triangle has a hypotenuse of length ${h}$. How long is each leg? {_ROUND}"
    solution = f"${num(leg)}$"
    s = Steps()
    s.step(r"In a 45-45-90 triangle the hypotenuse is $\sqrt{2}$ times a leg, so divide.",
           rf"\frac{{{h}}}{{\sqrt{{2}}}} \approx {num(leg)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


# --- Circles -----------------------------------------------------------------------------

@geometry_hs.geo_circle_equation_from_center_radius.variant("center_and_point")
def _circle_equation_center_and_point(max_center=9):
    """Hidden radius: the circle's center and one point on it."""
    h, k = _nonzero(-max_center, max_center), _nonzero(-max_center, max_center)
    x, y = random.randint(-10, 10), random.randint(-10, 10)
    if (x, y) == (h, k):
        x += 3
    r2 = (x - h) ** 2 + (y - k) ** 2
    problem = (
        f"A circle has center $({h}, {k})$ and passes through $({x}, {y})$. Write its equation in the form "
        "(x-h)^2 + (y-k)^2 = c."
    )
    solution = f"${_signed_factor('x', h)}^2 + {_signed_factor('y', k)}^2 = {r2}$"
    s = Steps()
    s.step("The radius squared is the squared distance from the center to the point.",
           f"r^2 = ({x} - {paren(h)})^2 + ({y} - {paren(k)})^2 = {r2}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_circle_equation_from_center_radius.variant("inside_or_outside")
def _circle_inside_or_outside(max_center=9, max_radius=12):
    """Is a point inside, on, or outside a circle?"""
    h, k = _nonzero(-max_center, max_center), _nonzero(-max_center, max_center)
    r = random.randint(2, max_radius)
    if random.random() < 0.3:
        p, q, r = random.choice(_PYTHAG_TRIPLES[:3])   # a point exactly on the circle
        x, y = h + p, k + q
    else:
        x, y = h + random.randint(-r - 3, r + 3), k + random.randint(-r - 3, r + 3)
    d2 = (x - h) ** 2 + (y - k) ** 2
    where = "inside" if d2 < r * r else ("on" if d2 == r * r else "outside")
    problem = (
        f"Is the point $({x}, {y})$ inside, on, or outside the circle "
        f"${_signed_factor('x', h)}^2 + {_signed_factor('y', k)}^2 = {r * r}$? Answer inside, on, or outside."
    )
    s = Steps()
    s.step("Substitute the point into the left side and compare with $r^2$.",
           f"({x} - {paren(h)})^2 + ({y} - {paren(k)})^2 = {d2}")
    s.step(f"${d2}$ is {'less than' if where == 'inside' else ('equal to' if where == 'on' else 'greater than')} "
           f"${r * r}$.")
    s.answer(where)
    return problem, where, s.done()


@geometry_hs.geo_circle_center_radius_from_equation.variant("constant_for_radius")
def _circle_constant_for_radius(max_center=9, max_radius=10):
    """For what constant does the general-form circle have a given radius?"""
    h, k = _nonzero(-max_center, max_center), _nonzero(-max_center, max_center)
    r = random.randint(1, max_radius)
    D, E = -2 * h, -2 * k
    c = h * h + k * k - r * r
    problem = (
        f"For what value of $c$ does $x^2 + y^2 {'+' if D > 0 else '-'} {abs(D)}x {'+' if E > 0 else '-'} "
        f"{abs(E)}y + c = 0$ describe a circle of radius ${r}$?"
    )
    solution = f"${c}$"
    s = Steps()
    s.step("Complete the square in $x$ and $y$.",
           f"{_signed_factor('x', h)}^2 + {_signed_factor('y', k)}^2 = {h * h} + {k * k} - c")
    s.step(f"Set the right side equal to $r^2 = {r * r}$.", f"{h * h + k * k} - c = {r * r} \\Rightarrow c = {c}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_circle_center_radius_from_equation.variant("diameter")
def _circle_diameter_from_equation(max_center=9, max_radius=12):
    """The diameter read from standard form."""
    h, k = _nonzero(-max_center, max_center), _nonzero(-max_center, max_center)
    r = random.randint(1, max_radius)
    problem = (
        f"What is the diameter of the circle ${_signed_factor('x', h)}^2 + {_signed_factor('y', k)}^2 = {r * r}$?"
    )
    solution = f"${2 * r}$"
    s = Steps()
    s.step("The right side is $r^2$.", f"r = \\sqrt{{{r * r}}} = {r}")
    s.step("The diameter is twice the radius.", f"2 \\times {r} = {2 * r}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_inscribed_angle.variant("tangent_chord")
def _inscribed_tangent_chord():
    """The angle between a tangent and a chord is half the intercepted arc."""
    arc = random.choice(range(20, 341, 2))
    if random.random() < 0.5:
        problem = (f"A tangent and a chord meet at a point on a circle. The arc they intercept measures "
                   f"${arc}^\\circ$. What is the angle between the tangent and the chord, in degrees?")
        answer = arc // 2
        s = Steps()
        s.step("A tangent-chord angle is half its intercepted arc.", rf"\frac{{{arc}}}{{2}} = {answer}")
    else:
        problem = (f"A tangent and a chord meet at a point on a circle, forming a ${arc // 2}^\\circ$ angle. "
                   "What is the measure of the intercepted arc, in degrees?")
        answer = arc
        s = Steps()
        s.step("The intercepted arc is twice the tangent-chord angle.", rf"2 \times {arc // 2} = {arc}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_circle_segments.variant("whole_chord")
def _circle_whole_chord():
    """Intersecting chords: find a whole chord from its segments."""
    a, b = random.randint(1, 12), random.randint(1, 12)
    c = random.choice([d for d in range(1, 25) if (a * b) % d == 0])
    d = a * b // c
    problem = (
        f"Two chords intersect inside a circle. One is split into segments of ${a}$ and ${b}$. The other has "
        f"one segment of length ${c}$. How long is the whole second chord?"
    )
    solution = f"${c + d}$"
    s = Steps()
    s.step("The products of the segments of intersecting chords are equal.", rf"{a} \times {b} = {c} \times x")
    s.step(f"Solve for the other segment, then add the two segments.", f"x = {d}, \\quad {c} + {d} = {c + d}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_circle_segments.variant("tangent_length")
def _circle_tangent_length():
    """Tangent from an external point: t^2 = external x whole secant."""
    t = random.randint(2, 15)
    choices = [e for e in range(1, t) if (t * t) % e == 0 and t * t // e > e]
    e = random.choice(choices)
    whole = t * t // e
    problem = (
        f"From an outside point, a secant with external segment ${e}$ and total length ${whole}$ and a tangent "
        "are drawn to a circle. How long is the tangent segment?"
    )
    solution = f"${t}$"
    s = Steps()
    s.step("The tangent squared equals external segment times whole secant.", rf"t^2 = {e} \times {whole} = {t * t}")
    s.step("Take the square root.", f"t = {t}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.area_of_circle.variant("scale_radius")
def _circle_area_scale():
    """Scaling the radius by k scales the area by k^2."""
    k = random.choice([2, 3, 4, 5, 10])
    problem = f"A circle's radius is multiplied by ${k}$. By what number is its area multiplied?"
    solution = f"{k * k}"
    s = Steps()
    s.step(r"Area is $\pi r^2$, so replacing $r$ with $kr$ multiplies the area by $k^2$.",
           f"{k}^2 = {k * k}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.area_of_circle.variant("annulus")
def _circle_annulus():
    """The area of a ring between two circles with the same center."""
    r = random.randint(1, 10)
    R = r + random.randint(1, 10)
    area = math.pi * (R * R - r * r)
    problem = (
        f"A ring is the region between two circles with the same center, of radii ${r}$ and ${R}$. What is "
        f"the area of the ring? {_ROUND}"
    )
    solution = num(area)
    s = Steps()
    s.step("Subtract the inner circle's area from the outer circle's.",
           rf"\pi({R})^2 - \pi({r})^2 = {R * R - r * r}\pi \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_geometry_gen.circumference.variant("wheel_revolutions")
def _circumference_wheel():
    """How many turns a wheel makes over a distance."""
    d = random.randint(20, 80)          # cm
    meters = random.randint(10, 500)
    turns = meters * 100 / (math.pi * d)
    problem = (
        f"A wheel has a diameter of ${d}$ cm. How many full or partial turns does it make rolling "
        f"${meters}$ meters? {_ROUND}"
    )
    solution = num(turns)
    s = Steps()
    s.step("One turn covers one circumference.", rf"C = \pi({d}) \approx {num(math.pi * d)} \text{{ cm}}")
    s.step("Convert the distance to cm and divide.", rf"\frac{{{meters * 100}}}{{{num(math.pi * d)}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_geometry_gen.circumference.variant("semicircle_perimeter")
def _circumference_semicircle():
    """The perimeter of a semicircle: half the circumference plus the diameter."""
    r = random.randint(1, 20)
    p = math.pi * r + 2 * r
    problem = f"What is the perimeter of a semicircle with radius ${r}$ (curved edge plus diameter)? {_ROUND}"
    solution = num(p)
    s = Steps()
    s.step("Half the circumference plus the straight diameter.", rf"\pi({r}) + 2({r}) \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_geometry_gen.sector_area.variant("radians")
def _sector_radians():
    r"""Sector area with the angle in radians: $A = \frac{1}{2}r^2\theta$."""
    r = random.randint(1, 15)
    theta = Fraction(random.randint(1, 60), 10)
    area = Fraction(1, 2) * r * r * theta
    problem = (
        f"A sector has radius ${r}$ and a central angle of ${num(theta)}$ radians. What is its area? "
        "Round to the nearest thousandth if needed."
    )
    solution = num(area)
    s = Steps()
    s.formula("With the angle in radians, the sector area", rf"A = \frac{{1}}{{2}}r^2\theta = \frac{{1}}{{2}}({r})^2({num(theta)}) = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.arc_length.variant("radians")
def _arc_radians():
    r"""Arc length with the angle in radians: $s = r\theta$."""
    r = random.randint(1, 30)
    theta = Fraction(random.randint(1, 60), 10)
    problem = (
        f"An arc on a circle of radius ${r}$ has a central angle of ${num(theta)}$ radians. How long is the "
        "arc? Round to the nearest thousandth if needed."
    )
    solution = num(r * theta)
    s = Steps()
    s.formula("With the angle in radians, arc length", rf"s = r\theta = {r}({num(theta)}) = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.arc_length.variant("clock_hand")
def _arc_clock_hand():
    """How far the tip of a clock's minute hand travels."""
    length = random.randint(3, 30)
    minutes = random.choice([5, 10, 15, 20, 25, 30, 40, 45, 50])
    dist = 2 * math.pi * length * minutes / 60
    problem = (
        f"A clock's minute hand is ${length}$ cm long. How far does its tip travel in ${minutes}$ minutes, "
        f"in cm? {_ROUND}"
    )
    solution = num(dist)
    s = Steps()
    s.step(f"In ${minutes}$ minutes the hand turns ${minutes}/60$ of a full circle.",
           rf"\frac{{{minutes}}}{{60}} \times 2\pi({length}) \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


# --- Transformations --------------------------------------------------------------------

@geometry_hs.geo_translate_point.variant("find_the_vector")
def _translate_find_vector():
    """Reverse: one component of the translation vector taking P to P'."""
    x, y = random.randint(-9, 9), random.randint(-9, 9)
    a, b = random.randint(-9, 9), random.randint(-9, 9)
    horizontal = random.random() < 0.5
    problem = (
        f"A translation takes $({x}, {y})$ to $({x + a}, {y + b})$. What is the "
        f"{'horizontal' if horizontal else 'vertical'} shift?"
    )
    solution = f"{a if horizontal else b}"
    s = Steps()
    if horizontal:
        s.step("Subtract the x-coordinates.", f"{x + a} - {paren(x)} = {a}")
    else:
        s.step("Subtract the y-coordinates.", f"{y + b} - {paren(y)} = {b}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_translate_point.variant("two_translations")
def _translate_twice():
    """Two translations in a row add their vectors."""
    x, y = random.randint(-9, 9), random.randint(-9, 9)
    (a, b), (c, d) = [(random.randint(-6, 6), random.randint(-6, 6)) for _ in range(2)]
    problem = (
        rf"The point $({x}, {y})$ is translated by $\langle {a}, {b} \rangle$ and then by "
        rf"$\langle {c}, {d} \rangle$. Where does it end up? {_PAIR_HINT}"
    )
    solution = pair(x + a + c, y + b + d)
    s = Steps()
    s.step("Two translations combine into one: add the vectors.", rf"\langle {a + c}, {b + d} \rangle")
    s.step("Apply it.", f"({x} + {paren(a + c)}, {y} + {paren(b + d)}) = ({x + a + c}, {y + b + d})")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_reflect_point.variant("two_reflections")
def _reflect_twice():
    """Reflecting over both axes is a 180-degree rotation."""
    x, y = _nonzero(-9, 9), _nonzero(-9, 9)
    first, second = random.sample(["x-axis", "y-axis"], 2)
    problem = (
        f"The point $({x}, {y})$ is reflected over the {first} and then over the {second}. Where does it end "
        f"up? {_PAIR_HINT}"
    )
    solution = pair(-x, -y)
    s = Steps()
    s.step("Reflecting over one axis negates one coordinate; over the other axis, the other.",
           f"({x}, {y}) \\to ({-x}, {-y})")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_rotate_point.variant("about_a_point")
def _rotate_about_point():
    """Rotation about a center other than the origin."""
    cx, cy = random.randint(-5, 5), random.randint(-5, 5)
    x, y = random.randint(-9, 9), random.randint(-9, 9)
    deg = random.choice([90, 180, 270])
    dx, dy = x - cx, y - cy
    rx, ry = {90: (-dy, dx), 180: (-dx, -dy), 270: (dy, -dx)}[deg]
    image = (cx + rx, cy + ry)
    problem = (
        f"Rotate the point $({x}, {y})$ by ${deg}^\\circ$ counterclockwise about the point $({cx}, {cy})$. "
        f"{_PAIR_HINT}"
    )
    solution = pair(*image)
    s = Steps()
    s.step("Shift so the center is at the origin.", f"({x} - {paren(cx)}, {y} - {paren(cy)}) = ({dx}, {dy})")
    s.step(f"Rotate ${deg}^\\circ$ about the origin.", f"({dx}, {dy}) \\to ({rx}, {ry})")
    s.step("Shift back.", f"({rx} + {paren(cx)}, {ry} + {paren(cy)}) = ({image[0]}, {image[1]})")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_dilate_point.variant("about_a_point")
def _dilate_about_point():
    """Dilation about a center other than the origin."""
    cx, cy = random.randint(-5, 5), random.randint(-5, 5)
    x, y = random.randint(-8, 8), random.randint(-8, 8)
    k = random.choice([2, 3, Fraction(1, 2)])
    if k == Fraction(1, 2) and ((x - cx) % 2 or (y - cy) % 2):
        k = 2
    image = (cx + k * (x - cx), cy + k * (y - cy))
    problem = (
        f"Dilate the point $({x}, {y})$ by a scale factor of ${frac_from(k)}$ centered at $({cx}, {cy})$. "
        f"{_PAIR_HINT}"
    )
    solution = pair(*image)
    s = Steps()
    s.step("Find the point's offset from the center.", f"({x - cx}, {y - cy})")
    s.step(f"Scale the offset by ${frac_from(k)}$ and add it back to the center.",
           f"({cx} + {num(k * (x - cx))}, {cy} + {num(k * (y - cy))}) = ({num(image[0])}, {num(image[1])})")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_dilate_point.variant("image_length")
def _dilate_image_length():
    """A dilation multiplies every length by the scale factor."""
    k = Fraction(random.choice([Fraction(1, 2), Fraction(1, 3), 2, 3, 4, Fraction(3, 2)]))
    length = random.randint(2, 24) * k.denominator
    image = k * length
    problem = (
        f"Segment $AB$ is ${length}$ units long. It is dilated by a scale factor of ${frac_from(k)}$. How "
        "long is its image?"
    )
    solution = num(image)
    s = Steps()
    s.step("A dilation multiplies every length by the scale factor.", rf"{frac_from(k)} \times {length} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Probability (geometry course) --------------------------------------------------------

def _two_way_counts():
    return {key: random.randint(1, 30) for key in ("AX", "AY", "BX", "BY")}


@geometry_hs.geo_conditional_probability_table.variant("independent")
def _conditional_independent():
    """Are A and X independent? P(X | A) = P(X) exactly when the table is proportional."""
    if random.random() < 0.5:
        a, b = random.randint(1, 6), random.randint(1, 6)
        x, y = random.randint(1, 6), random.randint(1, 6)
        c = {"AX": a * x, "AY": a * y, "BX": b * x, "BY": b * y}
    else:
        c = _two_way_counts()
    total = sum(c.values())
    p_x = Fraction(c["AX"] + c["BX"], total)
    p_x_a = Fraction(c["AX"], c["AX"] + c["AY"])
    answer = "yes" if p_x == p_x_a else "no"
    problem = (
        f"A two-way frequency table has these counts: A&X: {c['AX']}, A&Y: {c['AY']}, B&X: {c['BX']}, "
        f"B&Y: {c['BY']}. Are the events A and X independent? Answer yes or no."
    )
    s = Steps()
    s.step("A and X are independent when $P(X \\mid A) = P(X)$.",
           rf"P(X \mid A) = \frac{{{c['AX']}}}{{{c['AX'] + c['AY']}}} = {_tex(p_x_a)}, \quad "
           rf"P(X) = \frac{{{c['AX'] + c['BX']}}}{{{total}}} = {_tex(p_x)}")
    s.answer(answer)
    return problem, answer, s.done()


@geometry_hs.geo_conditional_probability_table.variant("joint")
def _conditional_joint():
    """A joint probability from the table: P(A and X)."""
    c = _two_way_counts()
    total = sum(c.values())
    row, col = random.choice("AB"), random.choice("XY")
    value = Fraction(c[row + col], total)
    problem = (
        f"A two-way frequency table has these counts: A&X: {c['AX']}, A&Y: {c['AY']}, B&X: {c['BX']}, "
        f"B&Y: {c['BY']}. One person is chosen at random. Find $P({row} \\text{{ and }} {col})$ as a reduced "
        "fraction."
    )
    solution = _frac(value)
    s = Steps()
    s.step("A joint probability divides one cell by the grand total.",
           rf"\frac{{{c[row + col]}}}{{{total}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_compound_probability.variant("at_least_one_of_n")
def _compound_at_least_one():
    """At least one success in n independent tries with the same probability."""
    p = _proper(5)
    n = random.randint(2, 4)
    value = 1 - (1 - p) ** n
    problem = (
        f"A player makes each free throw with probability ${frac_from(p)}$, independently. In ${n}$ attempts, "
        "what is the probability of making at least one? Give your answer as a reduced fraction."
    )
    solution = _frac(value)
    s = Steps()
    s.step("At least one make is the complement of missing them all.",
           rf"1 - \left(1 - {_tex(p)}\right)^{{{n}}} = 1 - {_tex((1 - p) ** n)} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_compound_probability.variant("a_and_not_b")
def _compound_a_and_not_b():
    """P(A and not B) for independent events."""
    pa, pb = _proper(), _proper()
    value = pa * (1 - pb)
    problem = (
        f"Events $A$ and $B$ are independent with $P(A) = {frac_from(pa)}$ and $P(B) = {frac_from(pb)}$. "
        "Find $P(A \\text{ and not } B)$ as a reduced fraction."
    )
    solution = _frac(value)
    s = Steps()
    s.step("Not $B$ has probability $1 - P(B)$, and it's independent of $A$ too.",
           rf"{_tex(pa)} \times \left(1 - {_tex(pb)}\right) = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_expected_value.variant("missing_probability")
def _expected_missing_probability():
    """A probability distribution's probabilities add to 1."""
    values = random.sample(range(-5, 11), 3)
    probs = [Fraction(random.randint(1, 4), 10) for _ in range(2)]
    while sum(probs) >= 1:
        probs = [Fraction(random.randint(1, 4), 10) for _ in range(2)]
    missing = 1 - sum(probs)
    problem = (
        f"$X$ takes the values ${values[0]}$, ${values[1]}$, and ${values[2]}$ with probabilities "
        f"${num(probs[0])}$, ${num(probs[1])}$, and $p$. What is $p$?"
    )
    solution = num(missing)
    s = Steps()
    s.step("The probabilities of a distribution add to $1$.", f"p = 1 - {num(probs[0])} - {num(probs[1])} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_expected_value.variant("raffle")
def _expected_raffle():
    """Expected net winnings of a raffle ticket."""
    tickets = random.choice([100, 200, 250, 500, 1000])
    price = random.randint(1, 10)
    prize = random.choice([50, 100, 200, 250, 500])
    ev = Fraction(prize, tickets) - price
    problem = (
        f"A raffle sells ${tickets}$ tickets for ${price}$ dollars each, and one ticket wins ${prize}$ dollars. "
        "What is the expected net gain from buying one ticket, in dollars? (A loss is negative.)"
    )
    solution = num(ev)
    s = Steps()
    s.step("Expected winnings: the prize times the chance of winning.", rf"\frac{{{prize}}}{{{tickets}}} = {num(Fraction(prize, tickets))}")
    s.step("Subtract the ticket price.", f"{num(Fraction(prize, tickets))} - {price} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Similarity --------------------------------------------------------------------------

@geometry_hs.geo_similar_triangle_side.variant("side_splitter")
def _similar_side_splitter():
    """A segment parallel to one side cuts the other two sides proportionally."""
    ad, db = random.randint(1, 12), random.randint(1, 12)
    ae = random.randint(1, 12)
    ec = Fraction(ae * db, ad)
    problem = (
        f"In triangle $ABC$, $D$ is on $AB$ and $E$ is on $AC$ with $DE$ parallel to $BC$. $AD = {ad}$, "
        f"$DB = {db}$, and $AE = {ae}$. Find $EC$. Round to the nearest thousandth if necessary."
    )
    solution = num(ec)
    s = Steps()
    s.step("A line parallel to one side divides the other two sides proportionally.",
           rf"\frac{{AD}}{{DB}} = \frac{{AE}}{{EC}} \Rightarrow \frac{{{ad}}}{{{db}}} = \frac{{{ae}}}{{EC}}")
    s.step("Solve.", rf"EC = \frac{{{ae} \times {db}}}{{{ad}}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_similar_triangle_side.variant("scale_from_perimeters")
def _similar_scale_from_perimeters():
    """Reverse: the scale factor from two perimeters."""
    p1 = random.randint(10, 60)
    k = Fraction(random.randint(1, 5), random.randint(1, 5))
    if k == 1:
        k = Fraction(3, 2)
    p1 *= k.denominator
    p2 = p1 * k
    problem = (
        f"Two similar triangles have perimeters ${p1}$ and ${num(p2)}$. What is the scale factor from the "
        f"first triangle to the second? {_FRACTION_HINT}"
    )
    solution = frac_from(k)
    s = Steps()
    s.step("Perimeters scale by the same factor as sides.", rf"\frac{{{num(p2)}}}{{{p1}}} = {_tex(k)}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_scale_factor_ratio.variant("scaled_area")
def _scale_scaled_area():
    """A known area scaled by k^2 (or a volume by k^3)."""
    k = random.choice([2, 3, 4, 5, Fraction(1, 2), Fraction(3, 2)])
    k = Fraction(k)
    if random.random() < 0.5:
        area = random.randint(2, 40) * k.denominator ** 2
        problem = (f"A figure with area ${area}$ is enlarged by a linear scale factor of ${frac_from(k)}$. What "
                   "is the new area?")
        answer = area * k * k
        s = Steps()
        s.step("Areas scale by the square of the scale factor.", rf"{area} \times \left({_tex(k)}\right)^2 = {num(answer)}")
    else:
        vol = random.randint(2, 40) * k.denominator ** 3
        problem = (f"A solid with volume ${vol}$ is scaled by a linear scale factor of ${frac_from(k)}$. What is "
                   "the new volume?")
        answer = vol * k ** 3
        s = Steps()
        s.step("Volumes scale by the cube of the scale factor.", rf"{vol} \times \left({_tex(k)}\right)^3 = {num(answer)}")
    solution = num(answer)
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_regular_polygon_area.variant("apothem_from_area")
def _regular_polygon_apothem():
    """Reverse: the apothem from the area and the perimeter (A = aP/2)."""
    n = random.choice([5, 6, 8, 10, 12])
    side = random.randint(2, 12)
    a = Fraction(random.randint(10, 100), 10)
    perimeter = n * side
    area = a * perimeter / 2
    problem = (
        f"A regular {n}-sided polygon has sides of length ${side}$ and an area of ${num(area)}$. What is its "
        "apothem?"
    )
    solution = num(a)
    s = Steps()
    s.formula("The area of a regular polygon", r"A = \frac{1}{2}aP")
    s.substitute(rf"{num(area)} = \frac{{1}}{{2}}a({perimeter})", text=f"The perimeter is ${n} \\times {side} = {perimeter}$.")
    s.step(f"Solve for $a$.", rf"a = \frac{{2 \times {num(area)}}}{{{perimeter}}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@geometry_hs.geo_composite_solid.variant("fill_time")
def _composite_fill_time():
    """How long a hose takes to fill a box-shaped pool."""
    l, w, d = random.randint(4, 20), random.randint(3, 10), random.randint(1, 3)
    rate = random.choice([Fraction(1, 2), Fraction(1, 4), 1, 2])
    minutes = l * w * d / rate
    problem = (
        f"A pool is a rectangular box ${l}$ m long, ${w}$ m wide, and ${d}$ m deep. A hose fills it at "
        f"${num(rate)}$ cubic meters per minute. How many minutes does it take to fill?"
    )
    solution = num(minutes)
    s = Steps()
    s.step("Find the volume.", rf"V = {l} \times {w} \times {d} = {l * w * d}")
    s.step("Divide by the fill rate.", rf"\frac{{{l * w * d}}}{{{num(rate)}}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Coordinate geometry, lengths and angles ------------------------------------------------

@lib_geometry_gen.euclidian_norm.variant("unit_vector")
def _norm_unit_vector():
    """A component of the unit vector in the same direction."""
    a, b = _nonzero(-12, 12), _nonzero(-12, 12)
    length = math.hypot(a, b)
    which = random.choice(["first", "second"])
    value = (a if which == "first" else b) / length
    problem = (
        f"What is the {which} component of the unit vector pointing in the same direction as $({a}, {b})$? "
        f"{_ROUND}"
    )
    solution = num(value)
    s = Steps()
    s.step("Divide the vector by its length.", rf"|v| = \sqrt{{{a}^2 + {b}^2}} \approx {num(length)}")
    s.step(f"The {which} component:", rf"\frac{{{a if which == 'first' else b}}}{{{num(length)}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_geometry_gen.equation_of_line_from_two_points.variant("x_intercept")
def _line_x_intercept():
    """The x-intercept of the line through two points."""
    while True:
        x1, y1, x2, y2 = (random.randint(-9, 9) for _ in range(4))
        if x1 != x2 and y1 != y2:
            break
    m = Fraction(y2 - y1, x2 - x1)
    x0 = x1 - y1 / m
    problem = (
        f"Where does the line through $({x1}, {y1})$ and $({x2}, {y2})$ cross the x-axis? Give the x-value. "
        f"{_FRACTION_HINT}"
    )
    solution = frac_from(x0)
    s = Steps()
    s.step("Find the slope.", rf"m = \frac{{{y2} - {paren(y1)}}}{{{x2} - {paren(x1)}}} = {_tex(m)}")
    s.step("Set $y = 0$ in $y - y_1 = m(x - x_1)$ and solve.", rf"0 - {paren(y1)} = {_tex(m)}(x - {paren(x1)}) \Rightarrow x = {_tex(x0)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.equation_of_line_from_two_points.variant("receipts")
def _line_receipts():
    """A linear cost from two data points (a fixed fee plus a rate)."""
    fee, rate = random.randint(5, 60), random.randint(2, 20)
    h1, h2 = random.sample(range(1, 12), 2)
    problem = (
        f"A repair shop charged ${fee + rate * h1}$ dollars for a ${h1}$-hour job and ${fee + rate * h2}$ "
        f"dollars for a ${h2}$-hour job. The cost is linear in the hours. Write the cost $y$ for $x$ hours in "
        "slope-intercept form y = mx+b."
    )
    solution = f"y = {rate}x + {fee}"
    s = Steps()
    s.step("The rate is the slope between the two jobs.",
           rf"m = \frac{{{fee + rate * h2} - {fee + rate * h1}}}{{{h2} - {h1}}} = {rate}")
    s.step("The fixed fee is the y-intercept.", f"b = {fee + rate * h1} - {rate}({h1}) = {fee}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.perimeter_of_polygons.variant("regular_side")
def _perimeter_regular_side():
    """Reverse: the side of a regular polygon from its perimeter."""
    n = random.randint(3, 12)
    side = random.randint(2, 25)
    problem = f"A regular polygon with ${n}$ sides has a perimeter of ${n * side}$ cm. How long is each side, in cm?"
    solution = f"{side}"
    s = Steps()
    s.step("All sides of a regular polygon are equal, so divide.", rf"{n * side} \div {n} = {side}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.perimeter_of_polygons.variant("fence_with_gate")
def _perimeter_fence_gate():
    """Fencing for a rectangle, leaving room for a gate."""
    l, w = random.randint(5, 50), random.randint(5, 40)
    gate = random.randint(1, 5)
    problem = (
        f"A rectangular garden is ${l}$ m by ${w}$ m. It needs a fence all the way around except for a "
        f"${gate}$ m gate. How many meters of fencing are needed?"
    )
    solution = f"{2 * (l + w) - gate}"
    s = Steps()
    s.step("Find the perimeter, then subtract the gate.", f"2({l} + {w}) - {gate} = {2 * (l + w) - gate}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_geometry_gen.valid_triangle.variant("longest_third_side")
def _triangle_longest_third_side():
    """The largest (or smallest) whole-number third side."""
    a, b = random.randint(2, 30), random.randint(2, 30)
    largest = random.random() < 0.5
    answer = a + b - 1 if largest else abs(a - b) + 1
    problem = (
        f"Two sides of a triangle are ${a}$ and ${b}$. What is the {'largest' if largest else 'smallest'} "
        "whole-number length the third side can have?"
    )
    solution = f"{answer}"
    s = Steps()
    s.step("The third side is between the difference and the sum of the other two, not including them.",
           f"{abs(a - b)} < c < {a + b}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.angle_regular_polygon.variant("exterior_angle")
def _polygon_exterior_angle():
    """One exterior angle of a regular polygon: 360/n."""
    n = random.randint(3, 20)
    problem = (
        f"What is the measure of one exterior angle of a regular polygon with ${n}$ sides, in degrees? "
        f"{_ROUND}"
    )
    solution = num(Fraction(360, n))
    s = Steps()
    s.step("The exterior angles of any polygon add to $360^\\circ$; a regular polygon's are equal.",
           rf"\frac{{360}}{{{n}}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.sum_of_polygon_angles.variant("missing_angle")
def _polygon_missing_angle():
    """The last angle of a polygon from the others."""
    n = random.randint(5, 8)
    total = (n - 2) * 180
    while True:
        angles = [random.randint(80, 170) for _ in range(n - 1)]
        last = total - sum(angles)
        if 30 <= last < 180:
            break
    problem = (
        f"A convex polygon with ${n}$ sides has angles of "
        + ", ".join(f"${v}^\\circ$" for v in angles)
        + ", and one more angle. What is the missing angle, in degrees?"
    )
    solution = f"{last}"
    s = Steps()
    s.step("The interior angles add to $(n - 2) \\times 180$.", f"({n} - 2) \\times 180 = {total}")
    s.step("Subtract the known angles.", f"{total} - {sum(angles)} = {last}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.angle_regular_polygon.variant("tiles_the_plane")
def _polygon_tiles():
    """A regular polygon tiles the plane when its interior angle divides 360."""
    n = random.choice([3, 4, 5, 6, 7, 8, 9, 10, 12])
    angle = Fraction((n - 2) * 180, n)
    answer = "yes" if (360 / angle).denominator == 1 else "no"
    problem = f"Can copies of a regular polygon with ${n}$ sides tile a flat surface with no gaps or overlaps? Answer yes or no."
    s = Steps()
    s.step("Copies fit around a point only if the interior angle divides $360^\\circ$ evenly.",
           rf"\frac{{({n} - 2)180}}{{{n}}} = {num(angle)}, \quad \frac{{360}}{{{num(angle)}}} = {num(360 / angle)}")
    s.answer(answer)
    return problem, answer, s.done()


@lib_algebra_extra_gen.vector_dot.variant("revenue")
def _dot_revenue():
    """A dot product in context: total revenue = prices . quantities."""
    items = random.sample(["shirts", "hats", "mugs", "posters"], 3)
    prices = [random.randint(2, 30) for _ in items]
    qty = [random.randint(1, 40) for _ in items]
    total = sum(p * q for p, q in zip(prices, qty))
    problem = (
        f"A store sells {', '.join(items)} for ${prices[0]}$, ${prices[1]}$, and ${prices[2]}$ dollars. It sells "
        f"${qty[0]}$, ${qty[1]}$, and ${qty[2]}$ of them. What is the total revenue, in dollars? (This is the "
        "dot product of the price and quantity vectors.)"
    )
    solution = f"{total}"
    s = Steps()
    s.step("Multiply matching entries and add.", " + ".join(f"{p}({q})" for p, q in zip(prices, qty)) + f" = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.vector_dot.variant("self_dot")
def _dot_self():
    """u . u is the squared length."""
    u = [random.randint(-9, 9) for _ in range(3)]
    problem = f"Find $u \\cdot u$ for $u = \\langle {u[0]}, {u[1]}, {u[2]} \\rangle$."
    total = sum(v * v for v in u)
    solution = f"{total}"
    s = Steps()
    s.step("A vector dotted with itself is the sum of its squared components (its length squared).",
           " + ".join(f"{paren(v)}^2" for v in u) + f" = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.angle_btw_vectors.variant("degrees")
def _vectors_angle_degrees():
    """The angle between two vectors, in degrees."""
    u = (_nonzero(-9, 9), random.randint(-9, 9))
    v = (random.randint(-9, 9), _nonzero(-9, 9))
    cos_t = (u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))
    angle = math.degrees(math.acos(max(-1, min(1, cos_t))))
    problem = f"Find the angle between the vectors $({u[0]}, {u[1]})$ and $({v[0]}, {v[1]})$ in degrees. {_ROUND}"
    solution = num(angle)
    s = Steps()
    s.formula("The angle", rf"\cos\theta = \frac{{u \cdot v}}{{|u||v|}} = \frac{{{u[0] * v[0] + u[1] * v[1]}}}{{{num(math.hypot(*u) * math.hypot(*v))}}}")
    s.step("Take the inverse cosine.", rf"\theta \approx {solution}^\circ")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_angles_gen.degree_to_rad.variant("coterminal")
def _degrees_coterminal():
    """The coterminal angle in [0, 360)."""
    deg = random.choice([random.randint(361, 1500), -random.randint(1, 1000)])
    problem = f"What angle between $0^\\circ$ and $360^\\circ$ (including $0$) is coterminal with ${deg}^\\circ$?"
    solution = f"{deg % 360}"
    s = Steps()
    s.step("Add or subtract full turns of $360^\\circ$ until the angle is in range.", f"{deg} \\to {deg % 360}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.radian_to_deg.variant("wheel_turns")
def _radians_wheel():
    """Revolutions to radians."""
    turns = Fraction(random.randint(1, 40), 4)
    rad = 2 * math.pi * turns
    problem = f"A wheel turns ${num(turns)}$ revolutions. Through how many radians does it turn? {_ROUND}"
    solution = num(rad)
    s = Steps()
    s.step(r"One revolution is $2\pi$ radians.", rf"{num(turns)} \times 2\pi = {num(2 * turns)}\pi \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_angles_gen.complex_to_polar.variant("modulus")
def _complex_modulus_only():
    """Just the modulus of a complex number."""
    a, b = _nonzero(-15, 15), _nonzero(-15, 15)
    r = math.hypot(a, b)
    problem = f"What is the modulus of ${a} {'+' if b > 0 else '-'} {abs(b)}i$? {_ROUND}"
    solution, lead = _exact_or_round(r)
    s = Steps()
    s.step("The modulus is the distance from $0$ in the complex plane.", rf"\sqrt{{{a}^2 + {b}^2}} = \sqrt{{{a * a + b * b}}}")
    s.answer(solution, lead=lead)
    return problem, solution, s.done()


@lib_angles_gen.fraction_to_decimal.variant("repeating_block")
def _fraction_repeating_block():
    """The length of the repeating block of 1/d (the multiplicative order of 10)."""
    d = random.choice([3, 7, 9, 11, 13, 21, 27, 33, 37, 41, 99, 101])
    n = random.randint(1, d - 1)
    fr = Fraction(n, d)
    q = fr.denominator
    for p in (2, 5):
        while q % p == 0:
            q //= p
    length, rem = 1, 10 % q
    while rem != 1 % q and q > 1:
        rem = rem * 10 % q
        length += 1
    if q == 1:
        length = 0
    problem = f"How many digits are in the repeating block of the decimal for ${fr.numerator}/{fr.denominator}$?"
    solution = f"{length}"
    s = Steps()
    s.step("Long division repeats when a remainder repeats. Divide and watch the remainders.")
    s.step(f"The block repeats every ${length}$ digit{'s' if length != 1 else ''}.")
    s.answer(solution)
    return problem, solution, s.done()


@lib_angles_gen.celsius_to_fahrenheit.variant("fahrenheit_to_celsius")
def _fahrenheit_to_celsius():
    """Reverse: Fahrenheit to Celsius."""
    f = random.randint(-40, 220)
    c = Fraction(5, 9) * (f - 32)
    problem = f"Convert ${f}$ degrees Fahrenheit to degrees Celsius. {_ROUND}"
    solution = num(c)
    s = Steps()
    s.formula("Solving the conversion for C", rf"C = \frac{{5}}{{9}}(F - 32) = \frac{{5}}{{9}}({f} - 32) \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Solids ------------------------------------------------------------------------------------

def _cubic(value, unit="m^3"):
    return f"{num(value)} {unit}"


@lib_solids_gen.volume_cube.variant("edge_from_volume")
def _cube_edge_from_volume():
    """Reverse: the edge of a cube from its volume."""
    s_len = random.randint(2, 15)
    problem = f"A cube has a volume of ${s_len ** 3}$ cubic meters. How long is each edge, in meters?"
    solution = f"{s_len} m"
    s = Steps()
    s.step("Take the cube root of the volume.", rf"\sqrt[3]{{{s_len ** 3}}} = {s_len}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.volume_cube.variant("scale_edge")
def _cube_scale_edge():
    """Scaling the edge by k scales the volume by k^3."""
    k = random.randint(2, 5)
    v = random.randint(1, 20)
    problem = f"A cube has a volume of ${v}$ cubic meters. Every edge is made ${k}$ times as long. What is the new volume?"
    solution = _cubic(v * k ** 3)
    s = Steps()
    s.step("Volume scales by the cube of the length factor.", rf"{v} \times {k}^3 = {v * k ** 3}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.surface_area_cube.variant("edge_from_area")
def _cube_edge_from_area():
    """Reverse: the edge of a cube from its surface area."""
    s_len = random.randint(2, 20)
    problem = f"A cube has a surface area of ${6 * s_len * s_len}$ square meters. How long is each edge, in meters?"
    solution = f"{s_len} m"
    s = Steps()
    s.step("A cube has $6$ equal square faces.", rf"{6 * s_len * s_len} \div 6 = {s_len * s_len}")
    s.step("Each face is $s^2$, so take the square root.", f"s = {s_len}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.surface_area_cube.variant("paint_cans")
def _cube_paint_cans():
    """Paint cans needed for a cube's surface (round up)."""
    s_len = random.randint(2, 12)
    cover = random.choice([10, 15, 20, 25])
    area = 6 * s_len * s_len
    cans = math.ceil(area / cover)
    problem = (
        f"Every face of a cube with ${s_len}$ m edges is painted. One can of paint covers ${cover}$ square "
        "meters. How many cans are needed?"
    )
    solution = f"{cans}"
    s = Steps()
    s.step("Find the surface area.", f"6({s_len})^2 = {area}")
    s.step("Divide by the coverage and round up: a partial can still has to be bought.",
           rf"{area} \div {cover} \approx {num(Fraction(area, cover))} \to {cans}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.volume_cuboid.variant("missing_dimension")
def _cuboid_missing_dimension():
    """Reverse: a missing dimension of a box from its volume."""
    l, w, h = (random.randint(1, 15) for _ in range(3))
    problem = f"A box has a volume of ${l * w * h}$ cubic meters, a length of ${l}$ m, and a width of ${w}$ m. How tall is it, in meters?"
    solution = f"{h} m"
    s = Steps()
    s.step("Volume is length times width times height, so divide.", rf"\frac{{{l * w * h}}}{{{l} \times {w}}} = {h}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.volume_cuboid.variant("liters")
def _cuboid_liters():
    """Tank capacity: 1 liter is 1000 cubic centimeters."""
    l, w, h = random.randint(10, 100), random.randint(10, 60), random.randint(10, 60)
    liters = Fraction(l * w * h, 1000)
    problem = f"A fish tank measures ${l}$ cm by ${w}$ cm by ${h}$ cm. How many liters does it hold? (1 liter = 1000 cubic cm)"
    solution = num(liters)
    s = Steps()
    s.step("Find the volume in cubic centimeters.", rf"{l} \times {w} \times {h} = {l * w * h}")
    s.step("Divide by $1000$.", f"{num(liters)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.surface_area_cuboid.variant("missing_dimension")
def _cuboid_area_missing_dimension():
    """Reverse: a box's height from its surface area."""
    l, w, h = (random.randint(1, 12) for _ in range(3))
    area = 2 * (l * w + l * h + w * h)
    problem = (
        f"A box has a surface area of ${area}$ square meters, a length of ${l}$ m, and a width of ${w}$ m. "
        "What is its height, in meters?"
    )
    solution = f"{h} m"
    s = Steps()
    s.formula("Surface area", rf"{area} = 2({l} \cdot {w} + {l}h + {w}h)")
    s.step("Divide by $2$ and subtract the base.", f"{area // 2} - {l * w} = {l + w}h")
    s.step(f"Divide by ${l + w}$.", f"h = {h}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.volume_cylinder.variant("height_from_volume")
def _cylinder_height_from_volume():
    """Reverse: a cylinder's height from its volume (a multiple of pi)."""
    r, h = random.randint(1, 10), random.randint(1, 20)
    problem = rf"A cylinder has radius ${r}$ m and volume ${r * r * h}\pi$ cubic meters. What is its height, in meters?"
    solution = f"{h} m"
    s = Steps()
    s.formula("The volume of a cylinder", rf"V = \pi r^2 h \Rightarrow {r * r * h}\pi = \pi({r})^2 h")
    s.step(rf"Divide by ${r * r}\pi$.", f"h = {h}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.curved_surface_area_cylinder.variant("can_label")
def _cylinder_can_label():
    """The label of a can is the curved surface."""
    d, h = random.randint(4, 15), random.randint(5, 25)
    area = math.pi * d * h
    problem = (
        f"A label wraps exactly once around a can with diameter ${d}$ m and height ${h}$ m, covering the side but "
        f"not the top or bottom. What is the label's area? {_ROUND}"
    )
    solution = _cubic(area, "m^2")
    s = Steps()
    s.step("Unrolled, the label is a rectangle: the circumference by the height.",
           rf"\pi({d}) \times {h} = {d * h}\pi \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_solids_gen.surface_area_cylinder.variant("open_top")
def _cylinder_open_top():
    """An open-top cylinder: one base plus the side."""
    r, h = random.randint(1, 12), random.randint(1, 20)
    area = math.pi * r * r + 2 * math.pi * r * h
    problem = f"A cylindrical cup with no lid has radius ${r}$ m and height ${h}$ m. What is its surface area? {_ROUND}"
    solution = _cubic(area, "m^2")
    s = Steps()
    s.step("There is only one circular base, plus the side.",
           rf"\pi({r})^2 + 2\pi({r})({h}) = {r * r + 2 * r * h}\pi \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_solids_gen.volume_cone.variant("from_cylinder")
def _cone_from_cylinder():
    """A cone holds 1/3 of the cylinder with the same base and height."""
    v = random.choice(range(3, 301, 3))
    problem = (
        f"A cylinder holds ${v}$ cubic meters. How much does a cone with the same base and height hold, in "
        "cubic meters?"
    )
    solution = _cubic(v // 3)
    s = Steps()
    s.step(r"A cone's volume is $\frac{1}{3}$ of the cylinder with the same base and height.", rf"\frac{{{v}}}{{3}} = {v // 3}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.surface_area_cone.variant("lateral_only")
def _cone_lateral():
    """Only the slanted (lateral) surface of a cone."""
    r, l = random.randint(1, 12), random.randint(13, 30)
    area = math.pi * r * l
    problem = f"A cone has radius ${r}$ m and slant height ${l}$ m. What is its lateral (side) surface area, not counting the base? {_ROUND}"
    solution = _cubic(area, "m^2")
    s = Steps()
    s.formula("The lateral area of a cone", rf"\pi r l = \pi({r})({l}) = {r * l}\pi \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_solids_gen.volume_sphere.variant("radius_from_volume")
def _sphere_radius_from_volume():
    """Reverse: a sphere's radius from its volume (a multiple of pi)."""
    r = random.randint(1, 12)
    coef = Fraction(4 * r ** 3, 3)
    problem = f"A sphere has a volume of ${_pi_times(coef)}$ cubic meters. What is its radius, in meters?"
    solution = f"{r} m"
    s = Steps()
    s.formula("The volume of a sphere", rf"\frac{{4}}{{3}}\pi r^3 = {_pi_times(coef)}")
    s.step(r"Multiply by $\frac{3}{4\pi}$ and take the cube root.", rf"r^3 = {r ** 3} \Rightarrow r = {r}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.volume_sphere.variant("how_many_fit")
def _sphere_how_many():
    """How many small balls have the same total volume as a big one: (R/r)^3."""
    r = random.randint(1, 3)
    k = random.randint(2, 5)
    problem = (
        f"How many solid balls of radius ${r}$ cm have the same total volume as one ball of radius ${k * r}$ cm?"
    )
    solution = f"{k ** 3}"
    s = Steps()
    s.step("Volume scales with the cube of the radius.", rf"\left(\frac{{{k * r}}}{{{r}}}\right)^3 = {k}^3 = {k ** 3}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.volume_hemisphere.variant("from_diameter")
def _hemisphere_from_diameter():
    """A hemisphere given by its diameter."""
    d = random.randint(2, 30)
    v = 2 / 3 * math.pi * (d / 2) ** 3
    problem = f"A hemispherical bowl has a diameter of ${d}$ m. What is its volume? {_ROUND}"
    solution = _cubic(v)
    s = Steps()
    s.step("The radius is half the diameter.", f"r = {num(Fraction(d, 2))}")
    s.formula("The volume of a hemisphere", rf"\frac{{2}}{{3}}\pi r^3 \approx {num(v)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@lib_solids_gen.surface_area_sphere.variant("radius_from_area")
def _sphere_radius_from_area():
    """Reverse: a sphere's radius from its surface area (a multiple of pi)."""
    r = random.randint(1, 15)
    problem = rf"A sphere has a surface area of ${4 * r * r}\pi$ square meters. What is its radius, in meters?"
    solution = f"{r} m"
    s = Steps()
    s.formula("The surface area of a sphere", rf"4\pi r^2 = {4 * r * r}\pi")
    s.step(r"Divide by $4\pi$ and take the square root.", f"r^2 = {r * r} \\Rightarrow r = {r}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.volume_pyramid.variant("height_from_volume")
def _pyramid_height_from_volume():
    """Reverse: a pyramid's height from its volume and base area."""
    while True:   # keep the volume a whole number, so nothing in the problem is rounded
        base, h = random.randint(4, 60), random.randint(2, 20)
        if base * h % 3 == 0:
            break
    vol = Fraction(base * h, 3)
    problem = f"A pyramid has a base area of ${base}$ square meters and a volume of ${num(vol)}$ cubic meters. How tall is it, in meters?"
    solution = f"{h} m"
    s = Steps()
    s.formula("The volume of a pyramid", rf"V = \frac{{1}}{{3}}Bh \Rightarrow {num(vol)} = \frac{{1}}{{3}}({base})h")
    s.step("Solve for $h$.", rf"h = \frac{{3 \times {num(vol)}}}{{{base}}} = {h}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.surface_area_pyramid.variant("slant_from_area")
def _pyramid_slant_from_area():
    """Reverse: a square pyramid's slant height from its surface area."""
    side, slant = random.randint(2, 20), random.randint(2, 25)
    area = side * side + 2 * side * slant
    problem = (
        f"A square pyramid has base edges of ${side}$ m and a total surface area of ${area}$ square meters. What "
        "is the slant height of its triangular faces, in meters?"
    )
    solution = f"{slant} m"
    s = Steps()
    s.formula("Surface area: the base plus four triangles", rf"{area} = {side}^2 + 4 \cdot \frac{{1}}{{2}}({side})\ell")
    s.step("Solve for the slant height.", rf"{area - side * side} = {2 * side}\ell \Rightarrow \ell = {slant}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_solids_gen.area_of_triangle.variant("height_from_area")
def _triangle_height_from_area():
    """Reverse: a triangle's height from its area and base."""
    b, h = random.randint(2, 30), random.randint(2, 30)
    area = Fraction(b * h, 2)
    problem = f"A triangle has an area of ${num(area)}$ square meters and a base of ${b}$ m. What is its height, in meters?"
    solution = f"{h} m"
    s = Steps()
    s.formula("The area of a triangle", rf"A = \frac{{1}}{{2}}bh \Rightarrow {num(area)} = \frac{{1}}{{2}}({b})h")
    s.step("Solve for $h$.", rf"h = \frac{{2 \times {num(area)}}}{{{b}}} = {h}")
    s.answer(solution)
    return problem, solution, s.done()
