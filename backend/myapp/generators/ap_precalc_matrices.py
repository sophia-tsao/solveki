"""Solveki-local generators filling gaps in AP Precalculus Unit 4 (parametric functions, conics, vectors and matrices).

Every generator here takes no required arguments, is decorated with
``@register``, and returns ``(problem, solution, steps)``: LaTeX strings plus a
step-by-step explanation built with ``_steps.Steps``. Never seed ``random``
inside a generator.

Matrices may appear in the problem (rendered by katex), but every answer is a
single number, an ``a/b`` fraction, an ``(x, y)`` pair, a comma-separated
list, or a conic name, so it can be typed.
"""
import random
from fractions import Fraction
from math import cos, hypot, isqrt, radians, sin

from ._registry import register
from ._format import num as _num, frac_from as _frac_from, pair as _pair
from ._steps import Steps, paren, tex_frac

_ROUND_HINT = "Round your answer to the nearest thousandth."
_PAIR_HINT = "Format your answer as (x, y)."
_FRAC_HINT = "Express your answer as a fraction in the form a/b, or an integer."


# ----------------------------- rendering helpers -----------------------------

def _matrix(rows):
    r"""A ``bmatrix`` from a list of rows: ``[[1, 2], [3, 4]]``."""
    body = r" \\ ".join(" & ".join(str(v) for v in row) for row in rows)
    return rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"


def _col(*values):
    """A column vector as a ``bmatrix``."""
    return _matrix([[v] for v in values])


def _combo(terms):
    """Render ``(coefficient, token)`` pairs as a signed sum, e.g. ``2x^2-3y+1``.

    A ``""`` token is a constant. Zero terms are dropped and unit coefficients
    omit the ``1``.
    """
    out = ""
    for coeff, token in terms:
        if coeff == 0:
            continue
        mag = abs(coeff)
        body = (str(mag) if token == "" or mag != 1 else "") + token
        if not out:
            out = ("-" if coeff < 0 else "") + body
        else:
            out += ("-" if coeff < 0 else "+") + body
    return out or "0"


def _poly(coeffs, var="t"):
    """A polynomial in ``var`` from coefficients listed highest degree first."""
    deg = len(coeffs) - 1
    return _combo([(c, "" if deg - i == 0 else var if deg - i == 1 else f"{var}^{deg - i}")
                   for i, c in enumerate(coeffs)])


def _eval(coeffs, t):
    """Evaluate a highest-first coefficient list at ``t`` (Horner's rule)."""
    value = 0
    for c in coeffs:
        value = value * t + c
    return value


def _plug(coeffs, t):
    """The polynomial with ``t`` substituted, unsimplified: ``2(3)^2 - (3) + 1``."""
    deg = len(coeffs) - 1
    text = ""
    for i, c in enumerate(coeffs):
        e = deg - i
        if c == 0:
            continue
        if e == 0:
            body = str(abs(c))
        else:
            power = f"({t})" if e == 1 else f"({t})^{e}"
            body = ("" if abs(c) == 1 else str(abs(c))) + power
        if not text:
            text = ("-" if c < 0 else "") + body
        else:
            text += f" {'-' if c < 0 else '+'} {body}"
    return text or "0"


def _tex_fr(value):
    """LaTeX for a Fraction: an integer when whole, else ``\\frac``."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return tex_frac(fr.numerator, fr.denominator)


def _component(kind, lo, hi):
    """Random coefficients for a ``linear`` or ``quadratic`` x(t) or y(t)."""
    nonzero = [n for n in range(lo, hi + 1) if n != 0]
    if kind == "linear":
        return [random.choice(nonzero), random.randint(lo, hi)]
    return [random.choice(nonzero), random.randint(lo, hi), random.randint(lo, hi)]


def _random_kinds():
    """Which of x(t), y(t) are linear or quadratic (at least one linear)."""
    return random.choice([("linear", "quadratic"), ("quadratic", "linear"),
                          ("linear", "linear")])


def _shift_trig(center, coeff, fn):
    r"""``3 + 2\cos t`` (dropping a zero center or a unit coefficient)."""
    term = rf"{'' if coeff == 1 else coeff}\{fn} t"
    return term if center == 0 else f"{center} + {term}"


def _square_shift(var, center):
    """``(x-3)^2``, ``(x+3)^2``, or ``x^2`` when the center is 0."""
    if center == 0:
        return f"{var}^2"
    return f"({var}{'-' if center > 0 else '+'}{abs(center)})^2"


def _mat_vec(m, v):
    """The product of a 2x2 matrix and a 2-vector."""
    return (m[0][0] * v[0] + m[0][1] * v[1], m[1][0] * v[0] + m[1][1] * v[1])


def _mat_mul(a, b):
    """The 2x2 matrix product ``ab``."""
    return [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def _det(m):
    return m[0][0] * m[1][1] - m[0][1] * m[1][0]


def _product_step(s, m, v, text, name="M"):
    """A step multiplying matrix ``m`` by column ``v``, row by row."""
    rows = [rf"{r[0]} \cdot {paren(v[0])} + {paren(r[1])} \cdot {paren(v[1])}" for r in m]
    out = _mat_vec(m, v)
    s.step(text, rf"{name}{_col(*v)} = {_matrix(m)}{_col(*v)} = {_col(*rows)} = {_col(*out)}")
    return out


# Named linear transformations: (description, matrix). The dilation's scale
# factor is filled in when one is drawn.
_NAMED = [
    (r"a counterclockwise rotation of $90^\circ$ about the origin", [[0, -1], [1, 0]]),
    (r"a rotation of $180^\circ$ about the origin", [[-1, 0], [0, -1]]),
    (r"a clockwise rotation of $90^\circ$ about the origin", [[0, 1], [-1, 0]]),
    ("a reflection over the $x$-axis", [[1, 0], [0, -1]]),
    ("a reflection over the $y$-axis", [[-1, 0], [0, 1]]),
    ("a reflection over the line $y = x$", [[0, 1], [1, 0]]),
]


def _named_transform(max_scale=4):
    """A random named transformation, sometimes a dilation: ``(desc, matrix)``."""
    if random.random() < 1 / 7:
        k = random.randint(2, max_scale)
        return (f"a dilation centered at the origin with scale factor ${k}$",
                [[k, 0], [0, k]])
    return random.choice(_NAMED)


def _random_matrix(lo, hi, invertible=True):
    while True:
        m = [[random.randint(lo, hi) for _ in range(2)] for _ in range(2)]
        if (_det(m) != 0) if invertible else any(any(r) for r in m):
            return m


# --------------------------------- generators --------------------------------

@register
def pc_parametric_position(min_coef=-4, max_coef=4, max_t=5):
    r"""Position of a Parametric Particle

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A particle moves with $x(t) = 2t+1$ and $y(t) = t^2-3$. Find its position at $t = 2$. Format your answer as (x, y). | (5, 1) |
    | A particle moves with $x(t) = 2t+1$ and $y(t) = t^2-3$. At what time $t$ is its $x$-coordinate $7$? | 3 |

    AP Precalculus 4.1/4.2. Each coordinate is linear or quadratic in ``t``;
    the time question is always asked about a linear coordinate, so it has one
    answer, a whole number in ``[0, max_t]``.
    """
    kinds = _random_kinds()
    xs, ys = (_component(k, min_coef, max_coef) for k in kinds)
    intro = (f"A particle moves in the plane so that its position at time $t \\ge 0$ is "
             f"given by $x(t) = {_poly(xs)}$ and $y(t) = {_poly(ys)}$.")
    t0 = random.randint(0, max_t)

    s = Steps()
    if random.random() < 0.5:
        x0, y0 = _eval(xs, t0), _eval(ys, t0)
        problem = f"{intro} Find the position of the particle at $t = {t0}$. {_PAIR_HINT}"
        solution = _pair(x0, y0)
        s.step(f"The particle's position is $(x(t), y(t))$. Substitute $t = {t0}$ into "
               f"each equation.")
        s.step("Find the $x$-coordinate.", f"x({t0}) = {_plug(xs, t0)} = {x0}")
        s.step("Find the $y$-coordinate.", f"y({t0}) = {_plug(ys, t0)} = {y0}")
    else:
        name, coeffs = random.choice([(n, c) for n, c, k in zip("xy", (xs, ys), kinds)
                                      if k == "linear"])
        a, b = coeffs
        target = a * t0 + b
        problem = (f"{intro} At what time $t$ is the particle's ${name}$-coordinate "
                   f"equal to ${target}$?")
        solution = str(t0)
        s.step(f"Set ${name}(t)$ equal to ${target}$.", f"{_poly(coeffs)} = {target}")
        if b != 0:
            verb = f"Subtract ${b}$ from" if b > 0 else f"Add ${-b}$ to"
            s.step(f"{verb} both sides.", f"{_poly([a, 0])} = {target - b}")
        if a != 1:
            s.step(f"Divide both sides by ${a}$.", f"t = {t0}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_parametric_rate_of_change(min_coef=-4, max_coef=4, max_t=6):
    r"""Average Rate of Change of a Parametric Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | For $x(t) = t^2+1$, $y(t) = 3t-2$, find the average rate of change of $x(t)$ on $[1, 3]$. | 4 |
    | For $x(t) = t^2+1$, $y(t) = 3t-2$, find the average rate of change of $y$ with respect to $x$ from $t = 1$ to $t = 3$. | 3/4 |

    AP Precalculus 4.3. Asks the average rate of change of ``x(t)`` or
    ``y(t)`` with respect to ``t``, or the slope ``Δy/Δx`` of the secant
    between two times (never with ``Δx = 0``).
    """
    mode = random.choice(["x", "y", "slope"])
    while True:
        kinds = _random_kinds()
        xs, ys = (_component(k, min_coef, max_coef) for k in kinds)
        t1, t2 = sorted(random.sample(range(0, max_t + 1), 2))
        if mode != "slope" or _eval(xs, t2) != _eval(xs, t1):
            break
    intro = f"A curve is defined parametrically by $x(t) = {_poly(xs)}$ and $y(t) = {_poly(ys)}$."

    s = Steps()
    if mode in ("x", "y"):
        coeffs = xs if mode == "x" else ys
        v1, v2 = _eval(coeffs, t1), _eval(coeffs, t2)
        rate = Fraction(v2 - v1, t2 - t1)
        problem = (f"{intro} Find the average rate of change of ${mode}(t)$ with respect to "
                   f"$t$ on the interval $[{t1}, {t2}]$. {_FRAC_HINT}")
        s.formula(f"The average rate of change of ${mode}(t)$ on $[{t1}, {t2}]$",
                  rf"\frac{{{mode}({t2}) - {mode}({t1})}}{{{t2} - {t1}}}")
        s.step("Evaluate at both endpoints.",
               rf"{mode}({t1}) = {_plug(coeffs, t1)} = {v1}, \quad "
               rf"{mode}({t2}) = {_plug(coeffs, t2)} = {v2}")
        s.step("Substitute and simplify.",
               rf"\frac{{{v2} - {paren(v1)}}}{{{t2} - {t1}}} = "
               rf"\frac{{{v2 - v1}}}{{{t2 - t1}}} = {_tex_fr(rate)}")
    else:
        x1, x2, y1, y2 = _eval(xs, t1), _eval(xs, t2), _eval(ys, t1), _eval(ys, t2)
        rate = Fraction(y2 - y1, x2 - x1)
        problem = (f"{intro} Find the average rate of change of $y$ with respect to $x$ "
                   rf"(the slope $\frac{{\Delta y}}{{\Delta x}}$) as $t$ goes from $t = {t1}$ "
                   f"to $t = {t2}$. {_FRAC_HINT}")
        s.formula(r"The average rate of change of $y$ with respect to $x$",
                  rf"\frac{{\Delta y}}{{\Delta x}} = \frac{{y({t2}) - y({t1})}}{{x({t2}) - x({t1})}}")
        s.step(f"Find the points at $t = {t1}$ and $t = {t2}$.",
               rf"(x({t1}), y({t1})) = ({x1}, {y1}), \quad (x({t2}), y({t2})) = ({x2}, {y2})")
        s.step("Substitute and simplify.",
               rf"\frac{{{y2} - {paren(y1)}}}{{{x2} - {paren(x1)}}} = "
               rf"\frac{{{y2 - y1}}}{{{x2 - x1}}} = {_tex_fr(rate)}")
    solution = _frac_from(rate)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_parametric_circle_line(max_center=6, max_radius=8, max_coord=6):
    r"""Parametric Circles and Line Segments

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | The curve $x(t) = 3 + 2\cos t$, $y(t) = -1 + 2\sin t$ traces a circle. Find its center. | (3, -1) |
    | The segment from $(1, 2)$ to $(7, -4)$ is $x(t) = 1+6t$, $y(t) = 2-6t$. Find the point at $t = \frac{1}{3}$. | (3, 0) |

    AP Precalculus 4.4. Reads the center or radius off ``x = h + r cos t,
    y = k + r sin t``, or evaluates a segment parametrization at a fraction
    ``t = k/n`` (the coordinate changes are multiples of ``n``, so the point
    has integer coordinates).
    """
    mode = random.choice(["center", "radius", "segment", "segment"])
    s = Steps()
    if mode in ("center", "radius"):
        h = random.randint(-max_center, max_center)
        k = random.randint(-max_center, max_center)
        r = random.randint(1, max_radius)
        problem = (f"The curve $x(t) = {_shift_trig(h, r, 'cos')}$, "
                   f"$y(t) = {_shift_trig(k, r, 'sin')}$ for $0 \\le t \\le 2\\pi$ traces a circle. ")
        if mode == "center":
            problem += f"Find the center of the circle. {_PAIR_HINT}"
            solution = _pair(h, k)
        else:
            problem += "Find the radius of the circle."
            solution = str(r)
        s.step("The circle with center $(h, k)$ and radius $r$ is traced by:",
               r"x(t) = h + r\cos t, \quad y(t) = k + r\sin t")
        s.step(r"This works because $\cos^2 t + \sin^2 t = 1$, so the point is always $r$ "
               r"units from $(h, k)$:",
               rf"{_square_shift('x', h)} + {_square_shift('y', k)} = {r}^2")
        s.step("Match the constants to the given equations.",
               rf"h = {h}, \quad k = {k}, \quad r = {r}")
    else:
        n = random.choice([2, 3, 4])
        num = random.randint(1, n - 1)
        steps = [m for m in range(-3, 4) if m != 0]
        x1 = random.randint(-max_coord, max_coord)
        y1 = random.randint(-max_coord, max_coord)
        dx, dy = n * random.choice(steps), n * random.choice(steps)
        x2, y2 = x1 + dx, y1 + dy
        t = Fraction(num, n)
        px, py = x1 + dx * t, y1 + dy * t
        t_tex = tex_frac(num, n)
        problem = (f"The line segment from $({x1}, {y1})$ to $({x2}, {y2})$ is parametrized by "
                   f"$x(t) = {_combo([(x1, ''), (dx, 't')])}$, "
                   f"$y(t) = {_combo([(y1, ''), (dy, 't')])}$ for $0 \\le t \\le 1$. "
                   f"Find the point on the segment at $t = {t_tex}$. {_PAIR_HINT}")
        solution = _pair(px, py)
        s.step(f"The segment starts at $({x1}, {y1})$ when $t = 0$ and ends at $({x2}, {y2})$ "
               f"when $t = 1$. At $t = {t_tex}$ it has moved ${t_tex}$ of the way.",
               rf"x(t) = x_1 + (x_2 - x_1)t, \quad y(t) = y_1 + (y_2 - y_1)t")
        s.step(f"Find $x({t_tex})$.",
               rf"x\left({t_tex}\right) = {x1} + {paren(dx)} \cdot {t_tex} = "
               rf"{x1} + {paren(dx * t)} = {px}")
        s.step(f"Find $y({t_tex})$.",
               rf"y\left({t_tex}\right) = {y1} + {paren(dy)} \cdot {t_tex} = "
               rf"{y1} + {paren(dy * t)} = {py}")
    s.answer(solution)
    return problem, solution, s.done()


# Pythagorean triples (leg, leg, hypotenuse) for points on x^2 + y^2 = r^2.
_TRIPLES = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15)]


def _y_factor(root):
    """``(y-3)``, ``(y+3)``, or ``y`` for a root of 0."""
    if root == 0:
        return "y"
    return f"(y{'-' if root > 0 else '+'}{abs(root)})"


@register
def pc_implicit_curve_points(max_x=5, max_y=6):
    r"""Points on an Implicitly Defined Curve

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | The curve $x^2+y^2=25$. Find all $y$ with $(3, y)$ on the curve, least to greatest. | -4, 4 |
    | The curve $x^2+xy+y^2=7$. Find all $y$ with $(1, y)$ on the curve, least to greatest. | -3, 2 |

    AP Precalculus 4.5. Either a circle ``x^2 + y^2 = r^2`` built from a
    Pythagorean triple, or ``x^2 ± xy + y^2 = c`` with ``c`` chosen so the
    quadratic in ``y`` has integer roots. A tangent point gives one value.
    """
    s = Steps()
    if random.random() < 0.4:
        a, b, r = random.choice(_TRIPLES)
        if random.random() < 0.5:
            a, b = b, a
        if random.random() < 0.15:
            a, b = r, 0
        x0 = a * random.choice([1, -1])
        equation = f"x^2+y^2={r * r}"
        roots = sorted({-b, b})
        s.step(f"Substitute $x = {x0}$ into the equation.", f"{paren(x0)}^2 + y^2 = {r * r}")
        s.step(f"Subtract ${x0 * x0}$ from both sides.", f"y^2 = {b * b}")
        if b == 0:
            s.step("The only square root of $0$ is $0$.", "y = 0")
        else:
            s.step("Take the positive and negative square roots.", rf"y = \pm {b}")
    else:
        sign = random.choice([1, -1])
        x0 = random.choice([n for n in range(-max_x, max_x + 1) if n != 0])
        while True:
            y1 = random.randint(-max_y, max_y)
            y2 = -sign * x0 - y1
            if abs(y2) <= max_y + max_x:
                break
        c = x0 * x0 + sign * x0 * y1 + y1 * y1
        equation = f"x^2{'+' if sign > 0 else '-'}xy+y^2={c}"
        roots = sorted({y1, y2})
        quad = _combo([(1, "y^2"), (sign * x0, "y"), (x0 * x0 - c, "")])
        sub = rf"{paren(x0)}^2 {'+' if sign > 0 else '-'} {paren(x0)}y + y^2 = {c}"
        s.step(f"Substitute $x = {x0}$ into the equation.", sub)
        s.step("Move everything to one side to get a quadratic in $y$.", f"{quad} = 0")
        factored = (f"{_y_factor(y1)}^2" if y1 == y2 else
                    f"{_y_factor(roots[0])}{_y_factor(roots[1])}")
        s.step("Factor and solve for $y$.",
               f"{factored} = 0 " + (rf"\Rightarrow y = {y1}" if y1 == y2 else
                                      rf"\Rightarrow y = {roots[0]} \text{{ or }} y = {roots[1]}"))
    problem = (f"A curve is defined implicitly by ${equation}$. Find every value of $y$ for "
               f"which the point $({x0}, y)$ lies on the curve. List the values from least to "
               f"greatest, separated by commas.")
    solution = ", ".join(str(v) for v in roots)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_classify_conic(max_center=4):
    r"""Classify a Conic from General Form

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Classify $4x^2+9y^2-16x+18y-11=0$. | ellipse |
    | Classify $x^2-4x+2y+6=0$. | parabola |

    AP Precalculus 4.6. With no ``xy`` term, ``Ax^2 + Cy^2 + Dx + Ey + F = 0``
    is a circle when ``A = C``, an ellipse when ``AC > 0``, a hyperbola when
    ``AC < 0``, and a parabola when exactly one of ``A``, ``C`` is 0. Each is
    built by expanding a standard form, so it is never degenerate.
    """
    kind = random.choice(["circle", "ellipse", "parabola", "hyperbola"])
    h = random.randint(-max_center, max_center)
    k = random.randint(-max_center, max_center)
    if kind == "circle":
        m, r = random.randint(1, 3), random.randint(1, 6)
        A = C = m
        D, E, F = -2 * m * h, -2 * m * k, m * (h * h + k * k - r * r)
    elif kind in ("ellipse", "hyperbola"):
        p, q = random.sample(range(1, 7), 2)
        R = p * q * random.randint(1, 4)
        if kind == "hyperbola":
            q = -q
            R *= random.choice([1, -1])
        A, C = p, q
        if random.random() < 0.5:
            A, C, h, k = C, A, k, h
        D, E, F = -2 * A * h, -2 * C * k, A * h * h + C * k * k - R
    else:
        A, C = random.randint(1, 4), 0
        D, E, F = random.randint(-8, 8), random.choice([n for n in range(-6, 7) if n]), \
            random.randint(-10, 10)
        if random.random() < 0.5:
            A, C, D, E = C, A, E, D
    if random.random() < 0.3:
        A, C, D, E, F = -A, -C, -D, -E, -F
    general = _combo([(A, "x^2"), (C, "y^2"), (D, "x"), (E, "y"), (F, "")])
    problem = (f"Classify the conic section ${general}=0$. Answer circle, ellipse, parabola, "
               f"or hyperbola (if it is a circle, answer circle).")
    solution = kind

    s = Steps()
    s.step("With no $xy$-term, the type of conic depends only on $A$ and $C$, the "
           "coefficients of $x^2$ and $y^2$ in $Ax^2 + Cy^2 + Dx + Ey + F = 0$.",
           rf"A = {A}, \quad C = {C}")
    if kind == "parabola":
        s.step("Exactly one of $A$ and $C$ is $0$, so only one variable is squared: "
               "the conic is a parabola.")
    elif kind == "circle":
        s.step("$A$ and $C$ are equal (same sign and same size), so the conic is a circle.",
               f"A = C = {A}")
    elif kind == "ellipse":
        s.step("$A$ and $C$ have the same sign but are not equal, so the conic is an ellipse.",
               f"AC = {A * C} > 0, \\quad A \\ne C")
    else:
        s.step("$A$ and $C$ have opposite signs, so the conic is a hyperbola.",
               f"AC = {A * C} < 0")
    s.answer(solution, lead="So the conic is an" if kind == "ellipse" else "So the conic is a")
    return problem, solution, s.done()


# Exact cosines of the reference angles 0, 30, 45, 60, 90 degrees (the sine of
# each is the cosine of its complement).
_REF_COS = {0: "1", 30: r"\frac{\sqrt{3}}{2}", 45: r"\frac{\sqrt{2}}{2}",
            60: r"\frac{1}{2}", 90: "0"}
_STANDARD_DEGREES = [0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330]


def _radian_tex(deg):
    r"""A standard angle in radians: ``\frac{2\pi}{3}``, ``\pi``, ``0``."""
    fr = Fraction(deg, 180)
    if fr == 0:
        return "0"
    top = ("" if fr.numerator == 1 else str(fr.numerator)) + r"\pi"
    return top if fr.denominator == 1 else rf"\frac{{{top}}}{{{fr.denominator}}}"


def _exact_trig(fn, deg):
    """Exact LaTeX and float for ``cos``/``sin`` of a standard angle."""
    value = cos(radians(deg)) if fn == "cos" else sin(radians(deg))
    ref = deg % 180
    ref = min(ref, 180 - ref)
    tex = _REF_COS[ref if fn == "cos" else 90 - ref]
    if abs(value) < 1e-12:
        return "0", 0.0
    return (tex if value > 0 else f"-{tex}"), value


@register
def pc_parametrize_ellipse(max_center=5, min_axis=2, max_axis=6):
    r"""Parametrize an Ellipse

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $\frac{(x-1)^2}{9}+\frac{(y+2)^2}{4}=1$ is $x(t) = 1 + a\cos t$, $y(t) = -2 + b\sin t$. Find $a$. | 3 |
    | The same ellipse, $x(t) = h + a\cos t$, $y(t) = k + b\sin t$: the point at $t = \frac{\pi}{2}$. | (1, 0) |

    AP Precalculus 4.7. The ellipse ``(x-h)^2/a^2 + (y-k)^2/b^2 = 1`` (with
    ``a != b``) is ``x = h + a cos t, y = k + b sin t``. Asks for one of the
    coefficients (which square root goes with which coordinate) or the point
    at a standard angle, rounded to the nearest thousandth.
    """
    h = random.randint(-max_center, max_center)
    k = random.randint(-max_center, max_center)
    a, b = random.sample(range(min_axis, max_axis + 1), 2)
    ellipse = (rf"\frac{{{_square_shift('x', h)}}}{{{a * a}}} + "
               rf"\frac{{{_square_shift('y', k)}}}{{{b * b}}} = 1")

    s = Steps()
    s.step(r"The ellipse $\frac{(x-h)^2}{a^2} + \frac{(y-k)^2}{b^2} = 1$ is traced "
           "counterclockwise by:", r"x(t) = h + a\cos t, \quad y(t) = k + b\sin t")
    s.step(f"The denominator under the $x$-term is $a^2 = {a * a}$ and the one under the "
           f"$y$-term is $b^2 = {b * b}$. The center is $({h}, {k})$.",
           rf"a = {a}, \quad b = {b}, \quad h = {h}, \quad k = {k}")
    if random.random() < 0.5:
        coord, fn, letter, answer = random.choice([("x", "cos", "p", a), ("y", "sin", "p", b)])
        x_rhs = _shift_trig(h, "p", "cos") if coord == "x" else _shift_trig(h, a, "cos")
        y_rhs = _shift_trig(k, "p", "sin") if coord == "y" else _shift_trig(k, b, "sin")
        problem = (f"The ellipse ${ellipse}$ is parametrized by $x(t) = {x_rhs}$, "
                   f"$y(t) = {y_rhs}$ for $0 \\le t \\le 2\\pi$, with $p > 0$. "
                   f"What is the value of ${letter}$?")
        solution = str(answer)
        s.step(rf"$p$ multiplies $\{fn} t$ in ${coord}(t)$, so it is "
               f"${'a' if coord == 'x' else 'b'}$.", f"p = {answer}")
    else:
        deg = random.choice(_STANDARD_DEGREES)
        t_tex = _radian_tex(deg)
        cos_tex, cos_v = _exact_trig("cos", deg)
        sin_tex, sin_v = _exact_trig("sin", deg)
        x, y = h + a * cos_v, k + b * sin_v
        problem = (f"The ellipse ${ellipse}$ is parametrized by $x(t) = h + a\\cos t$, "
                   f"$y(t) = k + b\\sin t$ with $a, b > 0$, where $(h, k)$ is its center. "
                   f"Find the point on the ellipse at $t = {t_tex}$. Round to the nearest "
                   f"thousandth if needed. {_PAIR_HINT}")
        solution = _pair(x, y)
        s.step(f"Evaluate the cosine and sine at $t = {t_tex}$.",
               rf"\cos\left({t_tex}\right) = {cos_tex}, \quad \sin\left({t_tex}\right) = {sin_tex}")
        rel = lambda v: "=" if abs(v * 2 - round(v * 2)) < 1e-9 else r"\approx"  # noqa: E731
        s.step("Substitute into the parametrization.",
               rf"x = {h} + {a}\left({cos_tex}\right) {rel(x)} {_num(x)}, \quad "
               rf"y = {k} + {b}\left({sin_tex}\right) {rel(y)} {_num(y)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_vector_valued_function(min_coef=-4, max_coef=4, max_t=5):
    r"""Vector-Valued Functions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $p(t) = \langle 2t+1, t^2 \rangle$. Find $p(3)$. Format your answer as (x, y). | (7, 9) |
    | $p(t) = \langle 2t+1, t^2 \rangle$. Find the displacement from $t = 1$ to $t = 3$. | (4, 8) |
    | $p(t) = \langle 2t+1, t^2 \rangle$. Find the distance between $p(1)$ and $p(3)$. | 8.944 |

    AP Precalculus 4.9. Position vector at a time, the displacement vector
    ``p(t2) - p(t1)`` (typed as a pair), or its magnitude.
    """
    kinds = _random_kinds()
    xs, ys = (_component(k, min_coef, max_coef) for k in kinds)
    intro = (f"A particle's position is given by the vector-valued function "
             rf"$p(t) = \langle {_poly(xs)}, {_poly(ys)} \rangle$.")
    mode = random.choice(["position", "displacement", "magnitude"])

    s = Steps()
    if mode == "position":
        t0 = random.randint(0, max_t)
        x0, y0 = _eval(xs, t0), _eval(ys, t0)
        problem = (rf"{intro} Find the position vector $p({t0})$. Write the vector "
                   rf"$\langle a, b \rangle$ as (a, b).")
        solution = _pair(x0, y0)
        s.step(f"Substitute $t = {t0}$ into each component of $p(t)$.")
        s.step("Evaluate the components.",
               rf"x({t0}) = {_plug(xs, t0)} = {x0}, \quad y({t0}) = {_plug(ys, t0)} = {y0}")
        s.step("Write the position vector.", rf"p({t0}) = \langle {x0}, {y0} \rangle")
    else:
        t1, t2 = sorted(random.sample(range(0, max_t + 1), 2))
        x1, y1, x2, y2 = _eval(xs, t1), _eval(ys, t1), _eval(xs, t2), _eval(ys, t2)
        dx, dy = x2 - x1, y2 - y1
        s.step(f"Evaluate $p(t)$ at $t = {t1}$ and $t = {t2}$.",
               rf"p({t1}) = \langle {x1}, {y1} \rangle, \quad p({t2}) = \langle {x2}, {y2} \rangle")
        s.step("The displacement is the later position minus the earlier one.",
               rf"p({t2}) - p({t1}) = \langle {x2} - {paren(x1)}, {y2} - {paren(y1)} \rangle "
               rf"= \langle {dx}, {dy} \rangle")
        if mode == "displacement":
            problem = (rf"{intro} Find the displacement vector $p({t2}) - p({t1})$. Write the "
                       rf"vector $\langle a, b \rangle$ as (a, b).")
            solution = _pair(dx, dy)
        else:
            sq = dx * dx + dy * dy
            mag = hypot(dx, dy)
            problem = (f"{intro} Find the distance between the particle's positions at "
                       f"$t = {t1}$ and $t = {t2}$ (the magnitude of the displacement "
                       f"vector). {_ROUND_HINT}")
            solution = _num(mag)
            rel = "=" if isqrt(sq) ** 2 == sq else r"\approx"
            s.formula(r"The magnitude of $\langle a, b \rangle$",
                      rf"\sqrt{{a^2 + b^2}} = \sqrt{{{paren(dx)}^2 + {paren(dy)}^2}} = "
                      rf"\sqrt{{{sq}}} {rel} {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_inverse_matrix_entry(min_v=-5, max_v=5):
    r"""Entry of an Inverse Matrix

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Let $A = \begin{bmatrix} 2 & 1 \\ 5 & 3 \end{bmatrix}$. Find the entry in row 1, column 2 of $A^{-1}$. | -1 |
    | Let $A = \begin{bmatrix} 4 & 2 \\ 1 & 3 \end{bmatrix}$. Find the entry in row 2, column 2 of $A^{-1}$. | 2/5 |

    AP Precalculus 4.11. A random invertible 2x2 integer matrix; the answer is
    one entry of ``A^{-1} = (1/det) [[d, -b], [-c, a]]`` as a reduced fraction.
    """
    m = _random_matrix(min_v, max_v)
    (a, b), (c, d) = m
    det = _det(m)
    adj = [[d, -b], [-c, a]]
    i, j = random.randint(1, 2), random.randint(1, 2)
    entry = Fraction(adj[i - 1][j - 1], det)
    problem = (f"Let $A = {_matrix(m)}$. Find the entry in row {i}, column {j} of the inverse "
               f"matrix $A^{{-1}}$. {_FRAC_HINT}")
    solution = _frac_from(entry)

    s = Steps()
    s.formula(r"The inverse of $\begin{bmatrix} a & b \\ c & d \end{bmatrix}$",
              r"\frac{1}{ad - bc}\begin{bmatrix} d & -b \\ -c & a \end{bmatrix}")
    s.step("Find the determinant. It isn't $0$, so $A$ is invertible.",
           rf"ad - bc = {a} \cdot {paren(d)} - {paren(b)} \cdot {paren(c)} = {det}")
    s.step("Swap $a$ and $d$, and negate $b$ and $c$.",
           rf"A^{{-1}} = \frac{{1}}{{{det}}}{_matrix(adj)}")
    s.step(f"The row {i}, column {j} entry is ${adj[i - 1][j - 1]}$ divided by ${det}$.",
           rf"{tex_frac(adj[i - 1][j - 1], det)} = {_tex_fr(entry)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_matrix_transform_point(min_v=-4, max_v=4, max_coord=5):
    r"""Apply a Matrix Transformation to a Point

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $L$ has matrix $\begin{bmatrix} 2 & 1 \\ 0 & -1 \end{bmatrix}$. Find the image of $(3, 4)$. | (10, -4) |
    | $L$ is a counterclockwise rotation of $90^\circ$ about the origin. Find the image of $(3, 4)$. | (-4, 3) |

    AP Precalculus 4.12. Multiplies the point (as a column vector) by a
    random 2x2 matrix, or by the matrix of a named rotation, reflection, or
    dilation that the student must recall.
    """
    point = (random.randint(-max_coord, max_coord), random.randint(-max_coord, max_coord))
    s = Steps()
    if random.random() < 0.5:
        desc, m = _named_transform()
        problem = (f"The linear transformation $L$ is {desc}. Find the image of the point "
                   f"$({point[0]}, {point[1]})$ under $L$. {_PAIR_HINT}")
        s.step(f"The matrix for {desc} is:", f"M = {_matrix(m)}")
    else:
        m = _random_matrix(min_v, max_v, invertible=False)
        problem = (f"The linear transformation $L$ has matrix $M = {_matrix(m)}$. Find the image "
                   f"of the point $({point[0]}, {point[1]})$ under $L$. {_PAIR_HINT}")
        s.step("To apply a matrix transformation, write the point as a column vector and "
               "multiply it on the left by the matrix.")
    image = _product_step(s, m, point, "Multiply: each row of $M$ times the column vector "
                                       "gives one coordinate of the image.")
    solution = _pair(*image)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_matrix_composition(min_v=-3, max_v=3, max_coord=5, max_area=10):
    r"""Composition and Inverse of Matrix Transformations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Apply $A$, then $B$, to $(1, 2)$, where $A = \begin{bmatrix} 1 & 1 \\ 0 & 1 \end{bmatrix}$, $B = \begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix}$. | (-2, 3) |
    | $A = \begin{bmatrix} 2 & 1 \\ 1 & 3 \end{bmatrix}$ maps a region of area $4$. Find the image's area. | 20 |
    | $A = \begin{bmatrix} 2 & 1 \\ 1 & 1 \end{bmatrix}$ maps $P$ to $(5, 3)$. Find $P$. | (2, 1) |

    AP Precalculus 4.13. Composition of two transformations applied to a
    point (as matrices or as named rotations/reflections/dilations), the area
    of an image region via ``|det A|``, or undoing a transformation with
    ``A^{-1}`` (the original point has integer coordinates).
    """
    mode = random.choice(["compose", "area", "inverse"])
    s = Steps()
    if mode == "compose":
        point = (random.randint(-max_coord, max_coord), random.randint(-max_coord, max_coord))
        p_tex = f"$({point[0]}, {point[1]})$"
        if random.random() < 0.5:
            (desc_a, a), (desc_b, b) = _named_transform(3), _named_transform(3)
            problem = (f"The point {p_tex} is first transformed by {desc_a}, and the result "
                       f"is then transformed by {desc_b}. Find the final image. {_PAIR_HINT}")
            s.step("Write the matrix for each transformation.",
                   rf"A = {_matrix(a)}, \quad B = {_matrix(b)}")
        else:
            a = _random_matrix(min_v, max_v, invertible=False)
            b = _random_matrix(min_v, max_v, invertible=False)
            problem = (f"Let $A = {_matrix(a)}$ and $B = {_matrix(b)}$. The point {p_tex} is "
                       f"transformed by $A$, and the result is then transformed by $B$. "
                       f"Find the final image. {_PAIR_HINT}")
            s.step("Applying $A$ first and then $B$ means computing $B(AP)$, which is the "
                   "composition $(BA)P$.")
        mid = _product_step(s, a, point, "Apply $A$ first.", name="A")
        final = _product_step(s, b, mid, "Then apply $B$ to that result.", name="B")
        solution = _pair(*final)
    elif mode == "area":
        m = _random_matrix(min_v - 1, max_v + 1)
        det = _det(m)
        area = random.randint(2, max_area)
        shape = random.choice(["a triangle", "a square", "a region"])
        (a, b), (c, d) = m
        s.step("A linear transformation with matrix $A$ multiplies every area by "
               r"$|\det A|$.")
        s.step("Find the determinant.",
               rf"\det A = {a} \cdot {paren(d)} - {paren(b)} \cdot {paren(c)} = {det}")
        if random.random() < 0.5:
            problem = (f"The linear transformation with matrix $A = {_matrix(m)}$ is applied to "
                       f"{shape} with area ${area}$. What is the area of the image?")
            solution = str(abs(det) * area)
            s.step("Multiply the original area by the scale factor.",
                   rf"|{det}| \cdot {area} = {solution}")
        else:
            problem = (f"By what factor does the linear transformation with matrix "
                       f"$A = {_matrix(m)}$ scale areas?")
            solution = str(abs(det))
            s.step("The area scale factor is the absolute value of the determinant.",
                   rf"|{det}| = {solution}")
    else:
        m = _random_matrix(min_v, max_v)
        (a, b), (c, d) = m
        det = _det(m)
        point = (random.randint(-max_coord, max_coord), random.randint(-max_coord, max_coord))
        image = _mat_vec(m, point)
        adj = [[d, -b], [-c, a]]
        problem = (f"The linear transformation with matrix $A = {_matrix(m)}$ maps a point $P$ "
                   f"to $({image[0]}, {image[1]})$. Find $P$. {_PAIR_HINT}")
        solution = _pair(*point)
        s.step("Undo the transformation with the inverse matrix: if $AP = Q$, then "
               "$P = A^{-1}Q$.")
        s.step("Find the inverse: swap $a$ and $d$, negate $b$ and $c$, and divide by the "
               "determinant.",
               rf"\det A = {det}, \quad A^{{-1}} = \frac{{1}}{{{det}}}{_matrix(adj)}")
        scaled = _mat_vec(adj, image)
        s.step("Multiply $A^{-1}$ by the image.",
               rf"P = \frac{{1}}{{{det}}}{_matrix(adj)}{_col(*image)} = "
               rf"\frac{{1}}{{{det}}}{_col(*scaled)} = {_col(*point)}")
    s.answer(solution)
    return problem, solution, s.done()


# Markov-chain contexts: (people, state 1, state 2, time step).
_MARKOV_CONTEXTS = [
    ("customers", "Store A", "Store B", "week"),
    ("subscribers", "Service X", "Service Y", "month"),
    ("bikes", "the North station", "the South station", "day"),
    ("members", "Gym P", "Gym Q", "month"),
]


def _dec(percent):
    """A whole percent as a decimal string: 70 -> 0.7."""
    return _num(Fraction(percent, 100))


@register
def pc_markov_transition(min_stay=50, max_stay=90, max_count=9):
    r"""Two-State Markov Transition

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Each week $80\%$ of Store A's customers stay and $30\%$ of Store B's switch to A. A has 500, B has 500. How many at A after 1 week? | 550 |

    AP Precalculus 4.14. A 2x2 transition matrix described in words, applied
    to an initial distribution once or twice. Percents are multiples of 10 and
    counts multiples of 100, so every count stays a whole number.
    """
    people, s1, s2, period = random.choice(_MARKOV_CONTEXTS)
    stay1 = random.randrange(min_stay, max_stay + 1, 10)
    switch2 = random.randrange(10, 60, 10)
    n1, n2 = 100 * random.randint(1, max_count), 100 * random.randint(1, max_count)
    steps_n = random.choice([1, 2])
    target = random.choice([0, 1])
    names = (s1, s2)

    # Column-stochastic T: column j is where state j's people go.
    T = [[Fraction(stay1, 100), Fraction(switch2, 100)],
         [Fraction(100 - stay1, 100), Fraction(100 - switch2, 100)]]
    T_tex = [[_dec(stay1), _dec(switch2)], [_dec(100 - stay1), _dec(100 - switch2)]]
    states = [(n1, n2)]
    for _ in range(steps_n):
        states.append(tuple(int(v) for v in _mat_vec(T, states[-1])))
    answer = states[-1][target]

    when = f"after 1 {period}" if steps_n == 1 else f"after 2 {period}s"
    problem = (f"Each {period}, ${stay1}\\%$ of the {people} at {s1} stay there and the rest move "
               f"to {s2}, while ${switch2}\\%$ of the {people} at {s2} move to {s1} and the rest "
               f"stay. Right now {s1} has ${n1}$ {people} and {s2} has ${n2}$. How many {people} "
               f"will be at {names[target]} {when}?")
    solution = str(answer)

    s = Steps()
    s.step(f"Write the transition matrix $T$. Column 1 is where {s1}'s {people} go and column 2 "
           f"is where {s2}'s go; each column sums to $1$.", f"T = {_matrix(T_tex)}")
    s.step("Write the current distribution as a column vector.", rf"x_0 = {_col(n1, n2)}")
    for k in range(1, steps_n + 1):
        (p1, p2), (q1, q2) = states[k - 1], states[k]
        rows = [rf"{T_tex[0][0]}({p1}) + {T_tex[0][1]}({p2})",
                rf"{T_tex[1][0]}({p1}) + {T_tex[1][1]}({p2})"]
        s.step(f"Multiply by $T$ to get the distribution after {k} {period}"
               f"{'' if k == 1 else 's'}.",
               rf"x_{k} = T x_{k - 1} = {_col(*rows)} = {_col(q1, q2)}")
    s.step(f"The {'first' if target == 0 else 'second'} entry is the number at {names[target]}.")
    s.answer(solution)
    return problem, solution, s.done()
