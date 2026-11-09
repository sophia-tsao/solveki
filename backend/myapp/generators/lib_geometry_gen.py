"""Solveki-local overrides for ``mathgenerator`` circle & coordinate geometry.

Every generator here is named to *exactly* match a stock ``mathgenerator``
generator so it overrides the library version (``_make_problem_for_topic``
resolves ``LOCAL_GENERATORS`` before the library). The library versions are
unusable in Solveki's exact-match answer box for a mix of reasons:

* ``distance_two_points`` answers with ``\\sqrt{...}`` (untypeable).
* ``euclidian_norm`` builds a vector of random floats (untypeable, unparseable).
* ``equation_of_line_from_two_points`` is arithmetically *wrong* — it returns
  strings like ``9y = 22x + 184`` instead of proper slope-intercept form.
* The circle/sector/midpoint generators are close but we restate the required
  answer format explicitly (rounding, ``(x, y)``) so a student knows what to
  type, and we keep every input a small integer suitable for review.
* ``perimeter_of_polygons`` gives no units in the answer and up to 12 sides of
  length 120; ``valid_triangle`` answers ``$Yes$`` without saying what to type;
  ``arc_length`` answers ``Arc length of the angle $= 12.34567$``.

Each generator returns typeable answers only: integers, decimals rounded to the
nearest thousandth via :func:`num`, ``a/b`` fractions, ``(x, y)`` pairs, or the
words ``yes``/``no``. ``random`` is used directly and never seeded here. Every
generator also returns a step-by-step explanation built with
:class:`~._steps.Steps`.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._variants import with_variants
from ._format import num, pair, frac_from
from ._steps import Steps, paren, tex_frac

_ROUND_HINT = "Round your answer to the nearest thousandth."
_ROUNDED_LEAD = "Rounded to the nearest thousandth, the answer is"


def _coord(lo, hi):
    """A random integer coordinate in ``[lo, hi]``."""
    return random.randint(lo, hi)


def tex_number(value):
    """An int or ``Fraction`` as LaTeX: ``3`` or ``-\\frac{2}{3}``."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return tex_frac(fr.numerator, fr.denominator)


def tex_pi_multiple(value):
    """A non-negative rational multiple of pi as LaTeX: ``64\\pi``,
    ``\\frac{17\\pi}{45}``, ``\\pi``, or ``0``."""
    fr = Fraction(value)
    if fr == 0:
        return "0"
    coef = "" if fr.numerator == 1 else str(fr.numerator)
    if fr.denominator == 1:
        return rf"{coef}\pi"
    return rf"\frac{{{coef}\pi}}{{{fr.denominator}}}"


def _sqrt_value(n):
    """``\\sqrt{25} = 5`` or ``\\sqrt{13} \\approx 3.606`` for an integer ``n``."""
    root = math.isqrt(n)
    if root * root == n:
        return rf"\sqrt{{{n}}} = {root}"
    return rf"\sqrt{{{n}}} \approx {num(math.sqrt(n))}"


def rounded_answer(s, solution, value):
    """Close ``s`` on ``solution``, mentioning rounding only if it happened."""
    if float(value) == float(solution):
        return s.answer(solution)
    return s.answer(solution, lead=_ROUNDED_LEAD)


def _times_pi(s, symbol, solution):
    """The step that turns an exact multiple of pi into a decimal."""
    s.step(r"Multiply, using the $\pi$ key on a calculator.", rf"{symbol} \approx {solution}")


@register
@with_variants
def area_of_circle(min_radius=1, max_radius=20):
    r"""Area of a Circle

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the area of a circle with radius $8$. ... | 201.062 |

    Overrides the stock ``area_of_circle``. Area $= \pi r^2$; answer is a
    decimal, so the problem states the rounding the answer box expects.
    """
    r = random.randint(min_radius, max_radius)
    area = math.pi * r * r
    problem = (
        f"Find the area of a circle with radius ${r}$. {_ROUND_HINT}"
    )
    solution = num(area)

    s = Steps()
    s.formula("The area of a circle with radius $r$", r"A = \pi r^2")
    s.substitute(rf"A = \pi ({r})^2 = {tex_pi_multiple(r * r)}",
                 text=f"Substitute $r = {r}$ and square it.")
    _times_pi(s, "A", solution)
    rounded_answer(s, solution, area)
    return problem, solution, s.done()


@register
@with_variants
def area_of_circle_given_center_and_point(coord_min=-10, coord_max=10):
    r"""Area of a Circle Given Center and a Point On It

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | ...center $(2, -4)$ passing through $(12, -4)$... | 314.159 |

    Overrides the stock version. The radius is the distance from the center to
    the given point, then area $= \pi r^2$. Both points are integers (the point
    is forced distinct from the center so the radius is positive).
    """
    cx = _coord(coord_min, coord_max)
    cy = _coord(coord_min, coord_max)
    while True:
        px = _coord(coord_min, coord_max)
        py = _coord(coord_min, coord_max)
        if (px, py) != (cx, cy):
            break
    r2 = (px - cx) ** 2 + (py - cy) ** 2
    area = math.pi * r2
    problem = (
        f"Find the area of the circle with center $({cx}, {cy})$ that passes "
        f"through the point $({px}, {py})$. {_ROUND_HINT}"
    )
    solution = num(area)

    dx, dy = px - cx, py - cy
    s = Steps()
    s.step(
        "The radius is the distance from the center to the point on the circle. "
        "By the distance formula, the radius squared is:",
        rf"r^2 = ({px} - {paren(cx)})^2 + ({py} - {paren(cy)})^2",
    )
    s.step("Subtract inside the parentheses, then square and add.",
           rf"r^2 = ({dx})^2 + ({dy})^2 = {dx * dx} + {dy * dy} = {r2}")
    s.step(
        rf"The area of a circle is $A = \pi r^2$. Since $r^2 = {r2}$, "
        "there's no need to find $r$ itself.",
        rf"A = \pi \cdot {r2} = {tex_pi_multiple(r2)}",
    )
    _times_pi(s, "A", solution)
    rounded_answer(s, solution, area)
    return problem, solution, s.done()


@register
@with_variants
def circumference(min_radius=1, max_radius=20):
    r"""Circumference of a Circle

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the circumference of a circle with radius $8$. ... | 50.265 |

    Overrides the stock version. Circumference $= 2\pi r$; decimal answer, so
    the problem states the rounding.
    """
    r = random.randint(min_radius, max_radius)
    circ = 2 * math.pi * r
    problem = (
        f"Find the circumference of a circle with radius ${r}$. {_ROUND_HINT}"
    )
    solution = num(circ)

    s = Steps()
    s.formula("The circumference of a circle with radius $r$", r"C = 2\pi r")
    s.substitute(rf"C = 2\pi ({r}) = {tex_pi_multiple(2 * r)}",
                 text=f"Substitute $r = {r}$.")
    _times_pi(s, "C", solution)
    rounded_answer(s, solution, circ)
    return problem, solution, s.done()


@register
@with_variants
def sector_area(min_radius=1, max_radius=20, min_angle=1, max_angle=359):
    r"""Area of a Sector

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | ...radius $9$ and central angle $292$ degrees... | 206.428 |

    Overrides the stock version. Sector area $= (\theta/360)\,\pi r^2$ for an
    angle in degrees; decimal answer, so the problem states the rounding.
    """
    r = random.randint(min_radius, max_radius)
    theta = random.randint(min_angle, max_angle)
    area = (theta / 360) * math.pi * r * r
    problem = (
        f"Find the area of a sector with radius ${r}$ and central angle "
        f"${theta}$ degrees. {_ROUND_HINT}"
    )
    solution = num(area)

    s = Steps()
    s.formula(
        r"A sector with central angle $\theta$ is the fraction "
        r"$\frac{\theta}{360^\circ}$ of the whole circle, so its area",
        r"A = \frac{\theta}{360^\circ} \cdot \pi r^2",
    )
    s.substitute(rf"A = \frac{{{theta}^\circ}}{{360^\circ}} \cdot \pi ({r})^2")
    s.step(
        r"Multiply, keeping $\pi$ as a factor, and simplify the fraction.",
        rf"A = \frac{{{theta} \cdot {r * r}}}{{360}}\pi = "
        rf"{tex_pi_multiple(Fraction(theta * r * r, 360))}",
    )
    _times_pi(s, "A", solution)
    rounded_answer(s, solution, area)
    return problem, solution, s.done()


@register
@with_variants
def distance_two_points(coord_min=-15, coord_max=15):
    r"""Distance Between Two Points

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the distance between $(-12, 16)$ and $(-16, -4)$. ... | 20.396 |

    Overrides the stock version, which answers with an untypeable
    ``\sqrt{...}``. We return the distance as a decimal rounded to the nearest
    thousandth and state the rounding.
    """
    x1 = _coord(coord_min, coord_max)
    y1 = _coord(coord_min, coord_max)
    x2 = _coord(coord_min, coord_max)
    y2 = _coord(coord_min, coord_max)
    dist = math.hypot(x2 - x1, y2 - y1)
    problem = (
        f"Find the distance between the points $({x1}, {y1})$ and "
        f"$({x2}, {y2})$. {_ROUND_HINT}"
    )
    solution = num(dist)

    dx, dy = x2 - x1, y2 - y1
    s = Steps()
    s.formula("The distance formula", r"d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}")
    s.substitute(rf"d = \sqrt{{({x2} - {paren(x1)})^2 + ({y2} - {paren(y1)})^2}}")
    s.step("Subtract inside the parentheses, then square each difference.",
           rf"d = \sqrt{{({dx})^2 + ({dy})^2}} = \sqrt{{{dx * dx} + {dy * dy}}}")
    s.step("Add, then take the square root.", rf"d = {_sqrt_value(dx * dx + dy * dy)}")
    rounded_answer(s, solution, dist)
    return problem, solution, s.done()


@register
@with_variants
def midpoint_of_two_points(coord_min=-15, coord_max=15):
    r"""Midpoint of Two Points

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | The midpoint of $(-13, 11)$ and $(8, 10)$... | (-2.5, 10.5) |

    Overrides the stock version. Midpoint $= ((x_1+x_2)/2, (y_1+y_2)/2)$; each
    component may be a half-integer, so the problem states the ``(x, y)`` format
    and each component is rendered via :func:`num`.
    """
    x1 = _coord(coord_min, coord_max)
    y1 = _coord(coord_min, coord_max)
    x2 = _coord(coord_min, coord_max)
    y2 = _coord(coord_min, coord_max)
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    problem = (
        f"Find the midpoint of the points $({x1}, {y1})$ and $({x2}, {y2})$. "
        f"Format your answer as (x, y)."
    )
    solution = pair(mx, my)

    s = Steps()
    s.formula(
        "The midpoint averages the $x$-coordinates and the $y$-coordinates. "
        "The midpoint formula",
        r"M = \left(\frac{x_1 + x_2}{2}, \frac{y_1 + y_2}{2}\right)",
    )
    s.substitute(
        rf"M = \left(\frac{{{x1} + {paren(x2)}}}{{2}}, \frac{{{y1} + {paren(y2)}}}{{2}}\right)"
        rf" = \left(\frac{{{x1 + x2}}}{{2}}, \frac{{{y1 + y2}}}{{2}}\right)"
    )
    s.step("Divide each sum by $2$.", rf"M = ({num(mx)}, {num(my)})")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def euclidian_norm(min_dim=2, max_dim=4, comp_min=-10, comp_max=10):
    r"""Euclidian (L2) Norm of a Vector

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the L2 norm of the vector $(3, -4)$. ... | 5 |

    Overrides the stock version, which uses a long vector of random floats. We
    use a short small-integer vector and return the L2 norm as a decimal
    rounded to the nearest thousandth (an integer when the norm is whole).
    """
    dim = random.randint(min_dim, max_dim)
    # At least one nonzero component so the norm is positive and meaningful.
    while True:
        components = [random.randint(comp_min, comp_max) for _ in range(dim)]
        if any(components):
            break
    norm = math.sqrt(sum(c * c for c in components))
    vector = ", ".join(str(c) for c in components)
    problem = (
        f"Find the Euclidean norm (L2 norm) of the vector $({vector})$. "
        f"{_ROUND_HINT}"
    )
    solution = num(norm)

    squares = [c * c for c in components]
    s = Steps()
    s.formula(
        "The Euclidean norm is the square root of the sum of the squared components. "
        "For a vector with $n$ components it",
        r"\|\vec{v}\| = \sqrt{v_1^2 + v_2^2 + \cdots + v_n^2}",
    )
    s.substitute(
        rf"\|\vec{{v}}\| = \sqrt{{{' + '.join(f'{paren(c)}^2' for c in components)}}}"
        rf" = \sqrt{{{' + '.join(map(str, squares))}}}",
        text="Substitute the components and square each one.",
    )
    s.step("Add, then take the square root.",
           rf"\|\vec{{v}}\| = {_sqrt_value(sum(squares))}")
    rounded_answer(s, solution, norm)
    return problem, solution, s.done()


def _line_solution(m, b):
    """Render ``y = mx + b`` typeably from ``Fraction`` slope ``m`` and
    intercept ``b`` (m != 0). Coefficients render as integers or ``a/b``."""
    if m == 1:
        slope_term = "x"
    elif m == -1:
        slope_term = "-x"
    else:
        slope_term = f"{frac_from(m)}x"
    out = f"y = {slope_term}"
    if b > 0:
        out += f" + {frac_from(b)}"
    elif b < 0:
        out += f" - {frac_from(-b)}"
    return out


@register
@with_variants
def equation_of_line_from_two_points(coord_min=-10, coord_max=10):
    r"""Equation of a Line From Two Points

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | ...line through $(0, 5)$ and $(1, 8)$... | y = 3x + 5 |
    | ...line through $(0, 1)$ and $(3, 3)$... | y = 2/3x + 1 |

    Overrides the stock version, which is arithmetically WRONG (it returns
    strings like ``9y = 22x + 184`` rather than slope-intercept form). We
    compute slope $m=(y_2-y_1)/(x_2-x_1)$ and intercept $b=y_1-m x_1$ exactly
    with fractions, then render a canonical ``y = mx + b`` (slope and intercept
    as integers or typeable ``a/b`` fractions). ``x_2 != x_1`` and ``y_2 != y_1``
    are enforced so the line is neither vertical nor horizontal.
    """
    while True:
        x1 = _coord(coord_min, coord_max)
        y1 = _coord(coord_min, coord_max)
        x2 = _coord(coord_min, coord_max)
        y2 = _coord(coord_min, coord_max)
        if x2 != x1 and y2 != y1:
            break
    m = Fraction(y2 - y1, x2 - x1)
    b = Fraction(y1) - m * x1
    problem = (
        f"Find the equation of the line through the points $({x1}, {y1})$ and "
        f"$({x2}, {y2})$. Give your answer in slope-intercept form y = mx+b."
    )
    solution = _line_solution(m, b)

    m_tex, b_tex = tex_number(m), tex_number(b)
    raw_slope = tex_frac(y2 - y1, x2 - x1)
    s = Steps()
    s.formula("The slope of the line through two points", r"m = \frac{y_2 - y_1}{x_2 - x_1}")
    s.substitute(
        rf"m = \frac{{{y2} - {paren(y1)}}}{{{x2} - {paren(x1)}}} = {raw_slope}"
        + ("" if raw_slope == m_tex else f" = {m_tex}")
    )
    s.step(
        f"To find the $y$-intercept $b$, substitute the slope and the point "
        f"$({x1}, {y1})$ into $y = mx + b$, then solve for $b$.",
        rf"{y1} = {m_tex} \cdot ({x1}) + b \quad\Rightarrow\quad "
        rf"b = {y1} - {paren(tex_number(m * x1))} = {b_tex}",
    )
    s.answer(solution, lead=f"With $m = {m_tex}$ and $b = {b_tex}$, the answer is")
    return problem, solution, s.done()


_POLYGON_NAMES = {
    3: "triangle", 4: "quadrilateral", 5: "pentagon", 6: "hexagon",
    7: "heptagon", 8: "octagon", 9: "nonagon", 10: "decagon",
    11: "hendecagon", 12: "dodecagon",
}


@register
@with_variants
def perimeter_of_polygons(min_sides=3, max_sides=8, min_length=1, max_length=50):
    r"""Perimeter of a Polygon

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A pentagon has sides of length $4$ cm, $7$ cm, $9$ cm, $12$ cm, and $3$ cm... | 35 |

    Overrides the stock version (up to 12 sides of length 120, the answer
    wrapped in ``$``). The perimeter is the sum of the side lengths, always a
    whole number of centimeters.
    """
    n = random.randint(min_sides, max_sides)
    sides = [random.randint(min_length, max_length) for _ in range(n)]
    perimeter = sum(sides)
    lengths = ", ".join(f"${side}$ cm" for side in sides[:-1]) + f", and ${sides[-1]}$ cm"
    shape = _POLYGON_NAMES.get(n, "polygon")
    problem = (
        f"A {shape} has ${n}$ sides with lengths {lengths}. What is its "
        f"perimeter, in centimeters?"
    )
    solution = str(perimeter)

    s = Steps()
    s.step("The perimeter is the total distance around the shape. "
           "To find it, add up the lengths of all the sides.")
    s.step(f"Add the ${n}$ side lengths.",
           f"{' + '.join(map(str, sides))} = {perimeter}")
    s.answer(solution, lead=f"The perimeter is ${perimeter}$ cm, so the answer is")
    return problem, solution, s.done()


@register
@with_variants
def valid_triangle(min_side=1, max_side=50):
    r"""Can Three Lengths Form a Triangle?

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Can a triangle have side lengths $7$, $10$, and $20$? Type yes or no. | no |

    Overrides the stock version, whose answer ``$Yes$`` doesn't say what to
    type. By the Triangle Inequality, three lengths form a triangle exactly
    when the two shorter ones add up to more than the longest (a sum equal to
    the longest side gives a flat segment, not a triangle).
    """
    a = random.randint(min_side, max_side)
    b = random.randint(min_side, max_side)
    c = random.randint(min_side, max_side)
    short1, short2, longest = sorted((a, b, c))
    exists = short1 + short2 > longest
    problem = (
        f"Can a triangle have side lengths ${a}$, ${b}$, and ${c}$? "
        f"Type yes or no."
    )
    solution = "yes" if exists else "no"

    total = short1 + short2
    s = Steps()
    s.step("The Triangle Inequality Theorem says the sum of any two sides of a "
           "triangle must be greater than the third side. It's enough to check "
           "that the two shortest sides add up to more than the longest side.")
    s.step(f"The two shortest sides are ${short1}$ and ${short2}$. Add them.",
           f"{short1} + {short2} = {total}")
    if exists:
        s.step(f"Compare the sum with the longest side, ${longest}$. "
               "The sum is greater, so these sides do form a triangle.",
               f"{total} > {longest}")
    else:
        relation = "=" if total == longest else "<"
        why = ("is only equal to it, so the sides would lie flat in a straight line"
               if total == longest
               else "is smaller, so the two short sides are too short to meet")
        s.step(f"Compare the sum with the longest side, ${longest}$. The sum {why}. "
               "These sides can't form a triangle.",
               rf"{total} {relation} {longest}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def arc_length(min_radius=1, max_radius=20, min_angle=1, max_angle=359):
    r"""Arc Length

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | ...arc of a circle with radius $9$ and central angle $120^\circ$... | 18.85 |

    Overrides the stock version, which answers with a sentence and a
    five-decimal number. Arc length $= (\theta/360) \cdot 2\pi r$ for an angle
    in degrees; the problem states the rounding.
    """
    r = random.randint(min_radius, max_radius)
    theta = random.randint(min_angle, max_angle)
    exact = Fraction(theta * 2 * r, 360)
    length = float(exact) * math.pi
    problem = (
        f"Find the length of an arc of a circle with radius ${r}$ and central "
        rf"angle ${theta}^\circ$. {_ROUND_HINT}"
    )
    solution = num(length)

    s = Steps()
    s.formula(
        r"An arc with central angle $\theta$ is the fraction "
        r"$\frac{\theta}{360^\circ}$ of the whole circumference, so its length",
        r"L = \frac{\theta}{360^\circ} \cdot 2\pi r",
    )
    s.substitute(rf"L = \frac{{{theta}^\circ}}{{360^\circ}} \cdot 2\pi ({r})")
    s.step(
        r"Multiply, keeping $\pi$ as a factor, and simplify the fraction.",
        rf"L = \frac{{{theta} \cdot {2 * r}}}{{360}}\pi = {tex_pi_multiple(exact)}",
    )
    _times_pi(s, "L", solution)
    rounded_answer(s, solution, length)
    return problem, solution, s.done()
