"""Solveki-local generators for Georgia "Geometry: Concepts & Connections".

Every generator here takes no required arguments, is decorated with
``@register``, and returns a ``(problem, solution)`` pair of LaTeX strings.
Answers are kept clean: integers, values rounded to at most three decimal
places, or reduced ``"a/b"`` fractions. Never seed ``random`` inside a
generator.
"""
import random
from math import atan2, cos, gcd, pi, sin, sqrt, tan

from ._registry import register
from ._format import num as _num, frac as _frac


# Integer-sided right triangles, used where an exact answer is required.
_PYTHAG_TRIPLES = [
    (3, 4, 5),
    (5, 12, 13),
    (8, 15, 17),
    (7, 24, 25),
    (20, 21, 29),
    (9, 40, 41),
    (12, 35, 37),
]


def _signed_factor(var, val):
    """Render ``(var - val)`` with the sign folded in; ``val`` must be nonzero."""
    if val >= 0:
        return f"({var} - {val})"
    return f"({var} + {-val})"


def _reduce(num, den):
    """Return ``(num, den)`` reduced to lowest terms with a positive denominator."""
    if den < 0:
        num, den = -num, -den
    g = gcd(abs(num), den) or 1
    return num // g, den // g


@register
def geo_right_triangle_side(min_angle=15, max_angle=75, min_len=5, max_len=30):
    r"""Right Triangle: Solve for a Side with Trig

    Given one acute angle and one side of a right triangle, find another side
    using sine, cosine, or tangent (answer rounded to 3 decimal places).
    """
    ratios = {
        "opposite side": sin,
        "adjacent side": cos,
        "hypotenuse": lambda t: 1.0,
    }
    given, target = random.sample(list(ratios), 2)
    theta = random.randint(min_angle, max_angle)
    length = random.randint(min_len, max_len)

    rad = theta * 3.141592653589793 / 180
    r_given = ratios[given](rad)
    r_target = ratios[target](rad)
    answer = length * r_target / r_given

    problem = (
        f"In a right triangle, one acute angle measures ${theta}^\\circ$. "
        f"The {given} measures ${length}$. "
        f"Find the {target}, rounded to the nearest thousandth."
    )
    return problem, f"${_num(answer)}$"


@register
def geo_solve_right_triangle_pythag(max_scale=5):
    r"""Right Triangle: Pythagorean Theorem

    Using a Pythagorean triple (scaled), either find the hypotenuse from two
    legs or find the missing leg from a leg and the hypotenuse.
    """
    a, b, c = random.choice(_PYTHAG_TRIPLES)
    scale = random.randint(1, max_scale)
    a, b, c = a * scale, b * scale, c * scale

    if random.random() < 0.5:
        problem = (
            f"A right triangle has legs of length ${a}$ and ${b}$. "
            f"Find the length of the hypotenuse."
        )
        return problem, f"${c}$"

    problem = (
        f"A right triangle has a leg of length ${a}$ and a hypotenuse of "
        f"length ${c}$. Find the length of the other leg."
    )
    return problem, f"${b}$"


@register
def geo_circle_equation_from_center_radius(max_center=9, max_radius=12):
    r"""Circle: Equation from Center and Radius

    Given center ``(h, k)`` and radius ``r``, write the standard-form equation
    ``(x-h)^2 + (y-k)^2 = r^2``.
    """
    h = random.choice([n for n in range(-max_center, max_center + 1) if n != 0])
    k = random.choice([n for n in range(-max_center, max_center + 1) if n != 0])
    r = random.randint(1, max_radius)

    problem = (
        f"Write the equation of the circle with center $({h}, {k})$ and "
        f"radius ${r}$. Write your answer in the form (x-h)^2 + (y-k)^2 = c."
    )
    solution = (
        f"${_signed_factor('x', h)}^2 + {_signed_factor('y', k)}^2 = {r * r}$"
    )
    return problem, solution


@register
def geo_circle_center_radius_from_equation(max_center=9, max_radius=12):
    r"""Circle: Center and Radius from Equation

    Given a circle in standard form ``(x-h)^2 + (y-k)^2 = r^2``, state the
    center ``(h, k)`` and the radius ``r``.
    """
    h = random.choice([n for n in range(-max_center, max_center + 1) if n != 0])
    k = random.choice([n for n in range(-max_center, max_center + 1) if n != 0])
    r = random.randint(1, max_radius)

    problem = (
        f"Find the center and radius of the circle "
        f"${_signed_factor('x', h)}^2 + {_signed_factor('y', k)}^2 = {r * r}$. "
        f"Format your answer as such: center (1, 2), r=3."
    )
    return problem, f"center ({h}, {k}), r={r}"


@register
def geo_translate_point(max_coord=10):
    r"""Transformation: Translate a Point

    Translate a point by a vector and give the image point.
    """
    x, y = random.randint(-max_coord, max_coord), random.randint(-max_coord, max_coord)
    a, b = random.randint(-max_coord, max_coord), random.randint(-max_coord, max_coord)
    problem = (
        f"Translate the point $({x}, {y})$ by the vector "
        f"$\\langle {a}, {b} \\rangle$. Give the image point as (x, y)."
    )
    return problem, f"({x + a}, {y + b})"


@register
def geo_reflect_point(max_coord=10):
    r"""Transformation: Reflect a Point

    Reflect a point over the x-axis, y-axis, or the line ``y = x``.
    """
    x, y = random.randint(-max_coord, max_coord), random.randint(-max_coord, max_coord)
    line = random.choice(["x-axis", "y-axis", "line $y=x$"])
    if line == "x-axis":
        image = (x, -y)
    elif line == "y-axis":
        image = (-x, y)
    else:
        image = (y, x)
    problem = (
        f"Reflect the point $({x}, {y})$ over the {line}. "
        f"Give the image point as (x, y)."
    )
    return problem, f"({image[0]}, {image[1]})"


@register
def geo_rotate_point(max_coord=10):
    r"""Transformation: Rotate a Point

    Rotate a point 90, 180, or 270 degrees counterclockwise about the origin.
    """
    x, y = random.randint(-max_coord, max_coord), random.randint(-max_coord, max_coord)
    angle = random.choice([90, 180, 270])
    if angle == 90:
        image = (-y, x)
    elif angle == 180:
        image = (-x, -y)
    else:  # 270 CCW
        image = (y, -x)
    problem = (
        f"Rotate the point $({x}, {y})$ by ${angle}^\\circ$ counterclockwise "
        f"about the origin. Give the image point as (x, y)."
    )
    return problem, f"({image[0]}, {image[1]})"


@register
def geo_dilate_point(max_coord=6):
    r"""Transformation: Dilate a Point

    Dilate a point from the origin by an integer or simple fractional scale
    factor.
    """
    factor = random.choice(["2", "3", "4", "5", "1/2", "1/3"])
    if "/" in factor:
        num, den = (int(t) for t in factor.split("/"))
    else:
        num, den = int(factor), 1
    # Choose coordinates divisible by the denominator so the image is integer.
    x = den * random.randint(-max_coord, max_coord)
    y = den * random.randint(-max_coord, max_coord)
    nx, ny = x * num // den, y * num // den
    problem = (
        f"Dilate the point $({x}, {y})$ from the origin by a scale factor of "
        f"${factor}$. Give the image point as (x, y)."
    )
    return problem, f"({nx}, {ny})"


@register
def geo_inscribed_angle(min_half=10, max_half=89):
    r"""Circle: Inscribed Angle Theorem

    An inscribed angle is half of the central angle subtending the same arc;
    given one, find the other. The answer is the number of degrees only.
    """
    if random.random() < 0.5:
        central = 2 * random.randint(min_half, max_half)
        problem = (
            f"An inscribed angle and a central angle of a circle intercept the "
            f"same arc. The central angle measures ${central}^\\circ$. Find the "
            f"measure of the inscribed angle in degrees."
        )
        return problem, f"${central // 2}$"

    inscribed = random.randint(min_half, min(80, max_half))
    problem = (
        f"An inscribed angle and a central angle of a circle intercept the "
        f"same arc. The inscribed angle measures ${inscribed}^\\circ$. Find the "
        f"measure of the central angle in degrees."
    )
    return problem, f"${2 * inscribed}$"


@register
def geo_conditional_probability_table(max_count=40):
    r"""Probability: Conditional Probability from a Two-Way Table

    Given a 2x2 two-way frequency table, compute a conditional probability
    ``P(target | condition)`` as a reduced fraction.
    """
    # Rows A/B, columns X/Y.
    n_ax = random.randint(1, max_count)
    n_ay = random.randint(1, max_count)
    n_bx = random.randint(1, max_count)
    n_by = random.randint(1, max_count)

    condition = random.choice(["A", "B", "X", "Y"])
    if condition in ("A", "B"):
        target = random.choice(["X", "Y"])
    else:
        target = random.choice(["A", "B"])

    counts = {
        ("A", "X"): n_ax, ("A", "Y"): n_ay,
        ("B", "X"): n_bx, ("B", "Y"): n_by,
    }
    if condition in ("A", "B"):
        denom = counts[(condition, "X")] + counts[(condition, "Y")]
        numer = counts[(condition, target)]
    else:
        denom = counts[("A", condition)] + counts[("B", condition)]
        numer = counts[(target, condition)]
    num, den = _reduce(numer, denom)

    problem = (
        f"A two-way frequency table has these counts: A&X: {n_ax}, "
        f"A&Y: {n_ay}, B&X: {n_bx}, B&Y: {n_by}. "
        f"Find $P({target} \\mid {condition})$ as a reduced fraction."
    )
    return problem, f"${num}/{den}$"


@register
def geo_compound_probability():
    r"""Probability: Compound Probability of Independent Events

    For independent events A and B with given simple fractions, compute
    ``P(A and B)`` or ``P(A or B)`` as a reduced fraction.
    """
    simple = [(1, 2), (1, 3), (2, 3), (1, 4), (3, 4), (1, 5), (2, 5),
              (3, 5), (4, 5), (1, 6), (5, 6)]
    (a, b) = random.choice(simple)
    (c, d) = random.choice(simple)

    if random.random() < 0.5:
        # P(A and B) = P(A) * P(B)
        num, den = _reduce(a * c, b * d)
        connector = "and"
    else:
        # P(A or B) = P(A) + P(B) - P(A)P(B), common denominator b*d.
        num, den = _reduce(a * d + c * b - a * c, b * d)
        connector = "or"

    problem = (
        f"Events A and B are independent with $P(A) = {a}/{b}$ and "
        f"$P(B) = {c}/{d}$. Find $P(A \\text{{ {connector} }} B)$ as a reduced "
        f"fraction."
    )
    return problem, f"${num}/{den}$"


@register
def geo_expected_value():
    r"""Probability: Expected Value of a Discrete Distribution

    Compute the expected value of a small discrete distribution whose
    probabilities are stated as fractions (answer rounded to 3 decimal places).
    """
    k = random.choice([3, 4])
    den = random.choice([4, 5, 6, 8, 10, 12])
    # Random positive integer numerators summing to `den`.
    nums = [1] * k
    for _ in range(den - k):
        nums[random.randrange(k)] += 1
    values = random.sample(range(-5, 11), k)

    ev = sum(v * n for v, n in zip(values, nums)) / den

    parts = ", ".join(f"P(X={v})={n}/{den}" for v, n in zip(values, nums))
    problem = (
        f"A discrete random variable X has the distribution: {parts}. "
        f"Find the expected value E(X), rounded to the nearest thousandth."
    )
    return problem, f"${_num(ev)}$"


@register
def geo_special_right_triangle(min_len=2, max_len=20):
    r"""Special Right Triangles

    In a 30-60-90 or 45-45-90 right triangle, one side is given and another is
    requested. Since a side may be irrational, the answer is rounded to the
    nearest thousandth.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | In a 45-45-90 right triangle, the leg measures $5$. Find the length of the hypotenuse, rounded to the nearest thousandth if the value is irrational. | $7.071$ |
    """
    if random.random() < 0.5:
        kind = "45-45-90"
        ratios = {"leg": 1.0, "hypotenuse": 2 ** 0.5}
    else:
        kind = "30-60-90"
        ratios = {"shorter leg": 1.0, "longer leg": 3 ** 0.5, "hypotenuse": 2.0}
    given, target = random.sample(list(ratios), 2)
    length = random.randint(min_len, max_len)
    answer = length * ratios[target] / ratios[given]

    problem = (
        f"In a {kind} right triangle, the {given} measures ${length}$. Find "
        f"the length of the {target}, rounded to the nearest thousandth if the "
        f"value is irrational."
    )
    return problem, f"${_num(answer)}$"


@register
def geo_similar_triangle_side(min_scale=2, max_scale=5, min_base=2, max_base=8):
    r"""Similar Triangles Missing Side

    Two similar triangles are given with three known corresponding sides; set up
    a proportion and solve for the missing side.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Triangle ABC is similar to triangle DEF, with vertices listed in corresponding order. In triangle ABC, AB = $6$ and BC = $9$. In triangle DEF, the corresponding side DE = $10$. Find the length of side EF. Round to the nearest thousandth if necessary. | $15$ |
    """
    # Pick a coprime ratio m:n so every stated length is a clean integer.
    while True:
        m = random.randint(min_scale, max_scale)
        n = random.randint(min_scale, max_scale + 1)
        if m != n and gcd(m, n) == 1:
            break
    p = random.randint(min_base, max_base)
    q = random.randint(min_base, max_base)
    s1, s2 = m * p, m * q            # sides AB, BC of triangle ABC
    t1 = n * p                       # side DE of triangle DEF (corresponds to AB)
    answer = s2 * t1 / s1            # side EF (corresponds to BC) = n * q

    problem = (
        f"Triangle ABC is similar to triangle DEF, with vertices listed in "
        f"corresponding order. In triangle ABC, AB = ${s1}$ and BC = ${s2}$. In "
        f"triangle DEF, the corresponding side DE = ${t1}$. Find the length of "
        f"side EF. Round to the nearest thousandth if necessary."
    )
    return problem, f"${_num(answer)}$"


@register
def geo_scale_factor_ratio(min_part=1, max_part=6):
    r"""Scale Factor to Area or Volume Ratio

    Given the linear scale factor between two similar figures, find the ratio of
    their areas (scale factor squared) or volumes (scale factor cubed).

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Two similar figures have a linear scale factor of $2/3$ (ratio of corresponding lengths). Find the ratio of their areas. Express your answer as a reduced fraction a/b or an integer. | $4/9$ |
    """
    while True:
        p = random.randint(min_part, max_part)
        q = random.randint(min_part, max_part)
        if (p, q) != (1, 1) and gcd(p, q) == 1:
            break
    scale = str(p) if q == 1 else f"{p}/{q}"

    if random.random() < 0.5:
        kind = "areas"
        answer = _frac(p * p, q * q)
    else:
        kind = "volumes"
        answer = _frac(p ** 3, q ** 3)

    problem = (
        f"Two similar figures have a linear scale factor of ${scale}$ (ratio of "
        f"corresponding lengths). Find the ratio of their {kind}. Express your "
        f"answer as a reduced fraction a/b or an integer."
    )
    return problem, f"${answer}$"


@register
def geo_circle_segments():
    r"""Segment Lengths in Circles

    Apply the power of a point: either two chords intersecting inside a circle
    (chord-chord product) or a tangent and secant from an external point.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Two chords of a circle intersect. The first chord is divided into segments of length $6$ and $4$. The second chord is divided into segments of length $8$ and x. Find x. Round to the nearest thousandth if necessary. | $3$ |
    """
    if random.random() < 0.5:
        a = random.randint(2, 12)
        b = random.randint(2, 12)
        product = a * b
        divisors = [x for x in range(1, product + 1) if product % x == 0]
        c = random.choice(divisors)
        d = product // c
        problem = (
            f"Two chords of a circle intersect. The first chord is divided into "
            f"segments of length ${a}$ and ${b}$. The second chord is divided "
            f"into segments of length ${c}$ and x. Find x. Round to the nearest "
            f"thousandth if necessary."
        )
        return problem, f"${_num(d)}$"

    external = random.randint(2, 10)
    total = external + random.randint(2, 12)
    tangent = sqrt(external * total)
    problem = (
        f"From an external point, a tangent segment and a secant are drawn to a "
        f"circle. The secant has external segment ${external}$ and total length "
        f"${total}$ (from the external point to the far intersection). Find the "
        f"length of the tangent segment. Round to the nearest thousandth if "
        f"necessary."
    )
    return problem, f"${_num(tangent)}$"


@register
def geo_regular_polygon_area(min_side=2, max_side=15):
    r"""Area of a Regular Polygon

    Given the number of sides and the side length of a regular polygon, find its
    area, rounded to the nearest thousandth.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A regular polygon has $6$ sides, each of length $4$. Find its area. Round to the nearest thousandth. | $41.569$ |
    """
    n = random.choice([3, 4, 5, 6, 8, 10, 12])
    s = random.randint(min_side, max_side)
    area = n * s * s / (4 * tan(pi / n))

    problem = (
        f"A regular polygon has ${n}$ sides, each of length ${s}$. Find its "
        f"area. Round to the nearest thousandth."
    )
    return problem, f"${_num(area)}$"


@register
def geo_composite_solid():
    r"""Composite Solid Volume

    Find the total volume of a composite solid: a cylinder topped by a cone, or
    two stacked rectangular prisms.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A composite solid is made of two rectangular prisms. The first measures $2$ by $3$ by $4$, and the second measures $1$ by $1$ by $5$. Find the total volume. Round to the nearest thousandth if necessary. | $29$ |
    """
    if random.random() < 0.5:
        r = random.randint(2, 8)
        h_cyl = random.randint(3, 12)
        h_cone = random.randint(3, 9)
        volume = pi * r * r * h_cyl + pi * r * r * h_cone / 3
        problem = (
            f"A solid consists of a cylinder of radius ${r}$ and height "
            f"${h_cyl}$ topped by a cone of the same radius ${r}$ and height "
            f"${h_cone}$. Find the total volume, using your calculator's full "
            f"value of pi. Round to the nearest thousandth if necessary."
        )
        return problem, f"${_num(volume)}$"

    a, b, c = (random.randint(1, 8) for _ in range(3))
    d, e, f = (random.randint(1, 8) for _ in range(3))
    volume = a * b * c + d * e * f
    problem = (
        f"A composite solid is made of two rectangular prisms. The first "
        f"measures ${a}$ by ${b}$ by ${c}$, and the second measures ${d}$ by "
        f"${e}$ by ${f}$. Find the total volume. Round to the nearest "
        f"thousandth if necessary."
    )
    return problem, f"${_num(volume)}$"


@register
def geo_polygon_area_vertices(coord=6):
    r"""Polygon Area from Vertices

    Given the integer coordinates of a triangle's or quadrilateral's vertices
    (listed in order around the figure), find its area with the shoelace
    formula. The area is an integer or ends in .5.

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the area of the triangle with vertices $(0, 0)$, $(4, 0)$, $(0, 3)$ (given in order around the figure). Give your answer as a number (it may end in .5). | $6$ |
    """
    n = random.choice([3, 4])
    while True:
        pts = set()
        while len(pts) < n:
            pts.add((random.randint(-coord, coord), random.randint(-coord, coord)))
        pts = list(pts)
        cx = sum(x for x, _ in pts) / n
        cy = sum(y for _, y in pts) / n
        pts.sort(key=lambda p: atan2(p[1] - cy, p[0] - cx))
        cross = 0
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            cross += x1 * y2 - x2 * y1
        area = abs(cross) / 2
        if area > 0:
            break

    coords = ", ".join(f"$({x}, {y})$" for x, y in pts)
    shape = "triangle" if n == 3 else "quadrilateral"
    problem = (
        f"Find the area of the {shape} with vertices {coords} (given in order "
        f"around the figure). Give your answer as a number (it may end in .5)."
    )
    return problem, f"${_num(area)}$"


@register
def geo_frustum_volume(min_r=1, max_r=8, min_h=3, max_h=15):
    r"""Volume of the Frustum of a Cone

    Volume $= \frac{1}{3}\pi h (R^2 + Rr + r^2)$, where $R$ and $r$ are the
    lower and upper base radii ($R > r$). Answer rounded to three decimals.
    """
    r = random.randint(min_r, max_r)
    big_r = r + random.randint(1, max_r)
    h = random.randint(min_h, max_h)
    volume = pi * h * (big_r ** 2 + big_r * r + r ** 2) / 3
    problem = (
        f"A frustum of a cone has height ${h}$, lower base radius ${big_r}$, "
        f"and upper base radius ${r}$. Find its volume. "
        f"Round your answer to the nearest thousandth."
    )
    return problem, f"${_num(volume)}$"
