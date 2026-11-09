"""Solveki-local overrides for ``mathgenerator`` angle/trig/conversion generators.

Group G3. Each generator's ``__name__`` deliberately matches a stock
``mathgenerator`` generator so ``_make_problem_for_topic`` (which resolves
``LOCAL_GENERATORS`` before the library) uses ours instead. The stock versions
are unusable here for the usual reasons: untypeable LaTeX answers
(``\\sec^{{2}}``, ``\\theta``), float noise like ``3.1999999999999993``, giant
random-float vectors, answers that don't state a required rounding format
for a non-integer result, and terse problems like ``The complementary angle of
35 =`` or ``Third angle of triangle with angles $50$ and $60 = $``.

Every generator is zero-required-arg, returns ``(problem, solution, steps)``,
and produces a typeable solution (plain integers/decimals to 3dp, or a small
ASCII function string for the derivative). ``steps`` is a step-by-step
explanation built with :class:`~._steps.Steps`.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._variants import with_variants
from ._format import num
from ._steps import Steps, paren, tex_frac
from .lib_geometry_gen import rounded_answer, tex_pi_multiple

_ROUND_HINT = "Give your answer as a decimal rounded to the nearest thousandth."
_RAD_HINT = "Give your answer in radians rounded to the nearest thousandth."


@register
@with_variants
def angle_regular_polygon():
    r"""Interior Angle of a Regular Polygon

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the measure of one interior angle of a regular polygon with $7$ sides... | 128.571 |

    Overrides the stock generator, which rounds to 2dp and states no format.
    Interior angle = ``(n - 2) * 180 / n`` degrees, often non-integer.
    """
    n = random.randint(3, 20)
    angle = (n - 2) * 180 / n
    problem = (
        f"Find the measure of one interior angle, in degrees, of a regular "
        f"polygon with ${n}$ sides. {_ROUND_HINT}"
    )
    solution = num(angle)

    total = (n - 2) * 180
    relation = "=" if total % n == 0 else r"\approx"
    s = Steps()
    s.step(
        rf"The interior angles of a polygon with $n$ sides add up to "
        rf"$(n - 2) \cdot 180^\circ$. Substitute $n = {n}$.",
        rf"({n} - 2) \cdot 180^\circ = {n - 2} \cdot 180^\circ = {total}^\circ",
    )
    s.step(
        f"A regular polygon's ${n}$ angles are all equal, so divide the sum by ${n}$.",
        rf"\frac{{{total}^\circ}}{{{n}}} {relation} {solution}^\circ",
    )
    rounded_answer(s, solution, angle)
    return problem, solution, s.done()


def _vector_str(vec):
    """Render an integer vector as a typeable comma list, e.g. ``2, -3, 1``."""
    return ", ".join(str(v) for v in vec)


def _magnitude_tex(name, vec):
    """``\\|\\vec{u}\\| = \\sqrt{2^2 + (-3)^2} = \\sqrt{13}`` for a step."""
    squares = " + ".join(f"{paren(c)}^2" for c in vec)
    total = sum(c * c for c in vec)
    root = math.isqrt(total)
    value = f" = {root}" if root * root == total else ""
    return rf"\|\vec{{{name}}}\| = \sqrt{{{squares}}} = \sqrt{{{total}}}{value}"


@register
@with_variants
def angle_btw_vectors():
    r"""Angle Between Two Vectors

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the angle between the vectors (2, -3) and (1, 4)... | 2.034 |

    Overrides the stock generator, which uses huge random floats and rounds to
    2dp. We use small integer vectors (2D or 3D) and compute
    ``arccos(dot / (|a| |b|))`` in radians. Vectors are guaranteed non-zero.
    """
    dim = random.choice([2, 3])

    def _nonzero_vec():
        while True:
            v = [random.randint(-6, 6) for _ in range(dim)]
            if any(c != 0 for c in v):
                return v

    a = _nonzero_vec()
    b = _nonzero_vec()
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    cos_theta = dot / (mag_a * mag_b)
    # Guard against tiny floating-point overshoot outside [-1, 1].
    cos_theta = max(-1.0, min(1.0, cos_theta))
    angle = math.acos(cos_theta)

    problem = (
        f"Find the angle between the vectors ({_vector_str(a)}) and "
        f"({_vector_str(b)}). {_RAD_HINT}"
    )
    solution = num(angle)

    sq_a, sq_b = sum(x * x for x in a), sum(x * x for x in b)
    s = Steps()
    s.step(
        r"The angle $\theta$ between vectors $\vec{u}$ and $\vec{v}$ satisfies:",
        r"\cos\theta = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \, \|\vec{v}\|}",
    )
    s.step(
        "Find the dot product: multiply matching components and add.",
        rf"\vec{{u}} \cdot \vec{{v}} = "
        + " + ".join(f"({x})({y})" for x, y in zip(a, b))
        + f" = {dot}",
    )
    s.step(
        "Find the length (magnitude) of each vector.",
        rf"{_magnitude_tex('u', a)}, \quad {_magnitude_tex('v', b)}",
    )
    s.step(
        r"Substitute into the formula and take the inverse cosine, "
        r"in radians.",
        rf"\theta = \cos^{{-1}}\left(\frac{{{dot}}}{{\sqrt{{{sq_a}}}\,\sqrt{{{sq_b}}}}}\right)"
        rf" \approx \cos^{{-1}}({num(cos_theta)}) \approx {solution}",
    )
    rounded_answer(s, solution, angle)
    return problem, solution, s.done()


@register
@with_variants
def degree_to_rad():
    r"""Convert Degrees to Radians

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert $68$ degrees to radians... | 1.187 |

    Overrides the stock generator (2dp, no stated format). Radians =
    ``degrees * pi / 180``.
    """
    degrees = random.randint(0, 360)
    radians = degrees * math.pi / 180
    problem = (
        f"Convert ${degrees}$ degrees to radians. {_ROUND_HINT}"
    )
    solution = num(radians)

    s = Steps()
    s.formula(
        r"Since $180^\circ = \pi$ radians, the conversion from degrees to radians",
        r"\text{radians} = \text{degrees} \cdot \frac{\pi}{180^\circ}",
    )
    s.substitute(
        rf"{degrees}^\circ \cdot \frac{{\pi}}{{180^\circ}} = "
        rf"{tex_pi_multiple(Fraction(degrees, 180))}",
        text="Multiply and simplify the fraction.",
    )
    if degrees:
        s.step(r"Multiply, using the $\pi$ key on a calculator.", rf"\approx {solution}")
    rounded_answer(s, solution, radians)
    return problem, solution, s.done()


@register
@with_variants
def radian_to_deg():
    r"""Convert Radians to Degrees

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert $1.25$ radians to degrees... | 71.62 |

    Overrides the stock generator (2dp, no stated format). Degrees =
    ``radians * 180 / pi``. The input radian value is kept simple (a two-decimal
    value in [0, 6.28]).
    """
    # Simple two-decimal radian value so the problem statement is clean.
    radians = random.randint(0, 628) / 100
    degrees = radians * 180 / math.pi
    problem = (
        f"Convert ${num(radians)}$ radians to degrees. {_ROUND_HINT}"
    )
    solution = num(degrees)

    s = Steps()
    s.formula(
        r"Since $\pi$ radians $= 180^\circ$, the conversion from radians to degrees",
        r"\text{degrees} = \text{radians} \cdot \frac{180^\circ}{\pi}",
    )
    s.substitute(
        rf"{num(radians)} \cdot \frac{{180^\circ}}{{\pi}} = "
        rf"\frac{{{num(radians * 180)}^\circ}}{{\pi}}" + ("" if radians else r" = 0^\circ"),
        text="Substitute and multiply the top.",
    )
    if radians:
        s.step(r"Divide, using the $\pi$ key on a calculator.", rf"\approx {solution}^\circ")
    rounded_answer(s, solution, degrees)
    return problem, solution, s.done()


@register
@with_variants
def complex_to_polar():
    r"""Convert a Complex Number to Polar Form

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Write $3+4i$ in polar form (modulus and argument)... | 5, 0.927 |

    Overrides the stock generator, whose problem is malformed (stray
    ``\\theta``) and whose answer is a single number. Given ``a + bi`` we return
    the modulus ``r = sqrt(a^2 + b^2)`` and argument ``theta = atan2(b, a)`` in
    radians, formatted ``r, theta``.
    """
    a = random.randint(-12, 12)
    b = random.randint(-12, 12)
    # Avoid the origin, whose argument is undefined.
    while a == 0 and b == 0:
        a = random.randint(-12, 12)
        b = random.randint(-12, 12)

    modulus = math.sqrt(a * a + b * b)
    argument = math.atan2(b, a)

    # Render a + bi cleanly (handle sign of the imaginary part).
    if b >= 0:
        expr = f"{a}+{b}i"
    else:
        expr = f"{a}-{abs(b)}i"

    problem = (
        f"Write the complex number ${expr}$ in polar form. Give the modulus "
        f"and the argument (in radians), each rounded to the nearest "
        f"thousandth, formatted as 'r, theta' (e.g. 5, 0.927)."
    )
    solution = f"{num(modulus)}, {num(argument)}"

    total = a * a + b * b
    root = math.isqrt(total)
    r_value = f"= {root}" if root * root == total else rf"\approx {num(modulus)}"
    theta = num(argument)
    arctan = rf"\tan^{{-1}}\left({tex_frac(b, a)}\right)" if a else ""
    s = Steps()
    s.step(
        f"For $a + bi$, the modulus is the distance from $0$ to the point $(a, b)$. "
        f"Here $a = {a}$ and $b = {b}$.",
        rf"r = \sqrt{{a^2 + b^2}} = \sqrt{{{paren(a)}^2 + {paren(b)}^2}} = \sqrt{{{total}}} {r_value}",
    )
    if a > 0:
        s.step(r"The argument $\theta$ is the angle to the point $(a, b)$, between "
               r"$-\pi$ and $\pi$. Since $a > 0$, it is just the inverse tangent of $\frac{b}{a}$.",
               rf"\theta = {arctan} \approx {theta}")
    elif a < 0 and b >= 0:
        s.step(r"The argument $\theta$ is the angle to the point $(a, b)$, between "
               r"$-\pi$ and $\pi$. Since $a < 0$ and $b \ge 0$, the point is on the left, "
               r"above (or on) the real axis, so add $\pi$ to the inverse tangent.",
               rf"\theta = {arctan} + \pi \approx {theta}")
    elif a < 0:
        s.step(r"The argument $\theta$ is the angle to the point $(a, b)$, between "
               r"$-\pi$ and $\pi$. Since $a < 0$ and $b < 0$, the point is in "
               r"Quadrant III, so subtract $\pi$ from the inverse tangent.",
               rf"\theta = {arctan} - \pi \approx {theta}")
    else:
        sign, side = ("", "positive") if b > 0 else ("-", "negative")
        s.step(rf"The argument $\theta$ is the angle to the point $(0, {b})$, which "
               rf"lies on the {side} imaginary axis.",
               rf"\theta = {sign}\frac{{\pi}}{{2}} \approx {theta}")
    s.answer(solution, lead="Rounded to the nearest thousandth and formatted as r, theta, the answer is")
    return problem, solution, s.done()


# Fixed set of basic functions whose derivative is typeable in pure ASCII.
# (function-as-written, derivative-as-ASCII).
_DERIVATIVES = [
    ("sin(x)", "cos(x)"),
    ("cos(x)", "-sin(x)"),
    ("tan(x)", "sec(x)^2"),
    ("sec(x)", "sec(x)*tan(x)"),
    ("csc(x)", "-csc(x)*cot(x)"),
    ("cot(x)", "-csc(x)^2"),
]

# For each function above: its derivative rule in LaTeX, and (for the four
# that aren't sin/cos) how the rule follows from the quotient rule.
_DERIVATIVE_TEX = {
    "sin(x)": (r"\frac{d}{dx}\sin x = \cos x", None),
    "cos(x)": (r"\frac{d}{dx}\cos x = -\sin x", None),
    "tan(x)": (
        r"\frac{d}{dx}\tan x = \sec^2 x",
        (r"\tan x = \frac{\sin x}{\cos x}",
         r"\frac{\cos x \cos x - \sin x(-\sin x)}{\cos^2 x} = \frac{1}{\cos^2 x} = \sec^2 x"),
    ),
    "sec(x)": (
        r"\frac{d}{dx}\sec x = \sec x \tan x",
        (r"\sec x = \frac{1}{\cos x}",
         r"\frac{0 - 1 \cdot (-\sin x)}{\cos^2 x} = \frac{1}{\cos x} \cdot \frac{\sin x}{\cos x}"
         r" = \sec x \tan x"),
    ),
    "csc(x)": (
        r"\frac{d}{dx}\csc x = -\csc x \cot x",
        (r"\csc x = \frac{1}{\sin x}",
         r"\frac{0 - 1 \cdot \cos x}{\sin^2 x} = -\frac{1}{\sin x} \cdot \frac{\cos x}{\sin x}"
         r" = -\csc x \cot x"),
    ),
    "cot(x)": (
        r"\frac{d}{dx}\cot x = -\csc^2 x",
        (r"\cot x = \frac{\cos x}{\sin x}",
         r"\frac{-\sin x \sin x - \cos x \cos x}{\sin^2 x} = -\frac{1}{\sin^2 x} = -\csc^2 x"),
    ),
}


@register
@with_variants
def trig_differentiation():
    r"""Differentiate a Basic Trigonometric Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Differentiate $tan(x)$ with respect to $x$... | sec(x)^2 |

    Overrides the stock generator, whose answers use untypeable LaTeX
    (``\\sec^{{2}}``). We pick from a fixed set of basic functions and return the
    derivative as a canonical ASCII string.
    """
    func, derivative = random.choice(_DERIVATIVES)
    problem = (
        f"Differentiate ${func}$ with respect to $x$. Write your answer using "
        f"ASCII function notation, e.g. cos(x) or sec(x)^2."
    )

    rule, derivation = _DERIVATIVE_TEX[func]
    s = Steps()
    if derivation is None:
        s.step(rf"The derivative of $\{func[:3]} x$ is one of the basic trigonometric "
               "derivative rules.", rule)
    else:
        rewrite, quotient = derivation
        s.step(f"Write ${rewrite}$ as a quotient and apply the quotient rule, "
               r"using $\frac{d}{dx}\sin x = \cos x$ and $\frac{d}{dx}\cos x = -\sin x$.",
               quotient)
        s.step("This is the standard derivative rule:", rule)
    s.answer(derivative, lead="In ASCII function notation, the answer is")
    return problem, derivative, s.done()


@register
@with_variants
def fraction_to_decimal():
    r"""Convert a Fraction to a Decimal

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert the fraction $17/73$ to a decimal... | 0.233 |

    Overrides the stock generator (2dp, no stated format, ``\\div`` markup).
    Denominators are chosen so the result may not terminate. Exact ties (e.g.
    ``1/16 = 0.0625``) round half up, as a student would by hand.
    """
    numerator = random.randint(1, 99)
    denominator = random.randint(2, 99)
    problem = (
        f"Convert the fraction ${numerator}/{denominator}$ to a decimal. "
        f"{_ROUND_HINT}"
    )
    solution = num(Fraction(numerator, denominator))

    s = Steps()
    s.step("A fraction means division: divide the top number (numerator) by "
           "the bottom number (denominator).",
           rf"\frac{{{numerator}}}{{{denominator}}} = {numerator} \div {denominator}")
    if numerator * 1000 % denominator == 0:
        s.step("Divide. The decimal ends, so there is nothing to round.",
               rf"{numerator} \div {denominator} = {solution}")
        s.answer(solution)
    else:
        four_places = numerator * 10000 // denominator
        whole, thousandths = divmod(four_places // 10, 1000)
        next_digit = four_places % 10
        shown = rf"{whole}.{thousandths:03d}\ldots"
        s.step("Divide. The decimal keeps going past the thousandths place.",
               rf"{numerator} \div {denominator} = {shown}")
        if next_digit >= 5:
            action = rf"Since ${next_digit} \ge 5$, round the thousandths digit up."
        else:
            action = rf"Since ${next_digit} < 5$, keep the thousandths digit the same."
        s.step(f"To round to the nearest thousandth, look at the next digit, "
               f"${next_digit}$. {action}",
               rf"{shown} \approx {solution}")
        s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def celsius_to_fahrenheit():
    r"""Convert Celsius to Fahrenheit

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Convert $-16$ degrees Celsius to degrees Fahrenheit... | 3.2 |

    Overrides the stock generator, which emits float noise like
    ``3.1999999999999993``. For an integer Celsius input the exact Fahrenheit
    value terminates at one decimal; :func:`num` renders it cleanly.
    """
    celsius = random.randint(-50, 50)
    fahrenheit = Fraction(celsius) * 9 / 5 + 32
    problem = (
        f"Convert ${celsius}$ degrees Celsius to degrees Fahrenheit. "
        f"{_ROUND_HINT}"
    )
    solution = num(fahrenheit)

    product = num(Fraction(celsius) * 9 / 5)
    s = Steps()
    s.formula("The formula to convert Celsius ($C$) to Fahrenheit ($F$)",
              r"F = \frac{9}{5}C + 32")
    s.substitute(rf"F = \frac{{9}}{{5}}({celsius}) + 32", text=f"Substitute $C = {celsius}$.")
    s.step(rf"Multiply first: $\frac{{9}}{{5}} \cdot ({celsius}) = {product}$.",
           f"F = {product} + 32")
    s.step("Add.", f"F = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def complementary_and_supplementary_angle(comp_min=1, comp_max=89, supp_min=1, supp_max=179):
    r"""Complementary and Supplementary Angles

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the measure, in degrees, of the angle that is complementary to an angle measuring $35^\circ$. | 55 |
    | Find the measure, in degrees, of the angle that is supplementary to an angle measuring $120^\circ$. | 60 |

    Overrides the stock version, whose problem reads ``The complementary angle
    of 35 =`` and which can ask for the complement of $90^\circ$ (answer $0$).
    Complementary angles sum to $90^\circ$, supplementary ones to $180^\circ$.
    """
    kind = random.choice(["complementary", "supplementary"])
    if kind == "complementary":
        total = 90
        angle = random.randint(comp_min, comp_max)
    else:
        total = 180
        angle = random.randint(supp_min, supp_max)
    answer = total - angle
    problem = (
        f"Find the measure, in degrees, of the angle that is {kind} to an "
        rf"angle measuring ${angle}^\circ$."
    )
    solution = str(answer)

    s = Steps()
    s.step(rf"{kind.capitalize()} angles add up to ${total}^\circ$. "
           "Call the unknown angle $x$.",
           rf"x + {angle}^\circ = {total}^\circ")
    s.step(rf"Subtract ${angle}^\circ$ from both sides.",
           rf"x = {total}^\circ - {angle}^\circ = {answer}^\circ")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def third_angle_of_triangle(min_angle=10, max_angle=89):
    r"""Third Angle of a Triangle

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Two angles of a triangle measure $50^\circ$ and $60^\circ$. Find the measure of the third angle, in degrees. | 70 |

    Overrides the stock version (``Third angle of triangle with angles $50$
    and $60 = $``). Both known angles are below $90^\circ$, so the third angle
    is always positive.
    """
    a = random.randint(min_angle, max_angle)
    b = random.randint(min_angle, max_angle)
    known = a + b
    third = 180 - known
    problem = (
        rf"Two angles of a triangle measure ${a}^\circ$ and ${b}^\circ$. "
        "Find the measure of the third angle, in degrees."
    )
    solution = str(third)

    s = Steps()
    s.step(r"The three angles of a triangle add up to $180^\circ$. "
           "Call the third angle $x$.",
           rf"{a}^\circ + {b}^\circ + x = 180^\circ")
    s.step("Add the two known angles.", rf"{known}^\circ + x = 180^\circ")
    s.step(rf"Subtract ${known}^\circ$ from both sides.",
           rf"x = 180^\circ - {known}^\circ = {third}^\circ")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def fourth_angle_of_quadrilateral(min_angle=20, max_angle=160):
    r"""Fourth Angle of a Quadrilateral

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Three angles of a quadrilateral measure $85^\circ$, $100^\circ$, and $70^\circ$. Find the measure of the fourth angle, in degrees. | 105 |

    Overrides the stock version (``Fourth angle of quadrilateral with angles
    $85 , 100, 70 =$``), which also allows straight $180^\circ$ angles. We
    redraw until all four angles lie in ``[min_angle, max_angle]``, so the
    quadrilateral is convex.
    """
    while True:
        angles = [random.randint(min_angle, max_angle) for _ in range(3)]
        fourth = 360 - sum(angles)
        if min_angle <= fourth <= max_angle:
            break
    a, b, c = angles
    known = a + b + c
    problem = (
        rf"Three angles of a quadrilateral measure ${a}^\circ$, ${b}^\circ$, "
        rf"and ${c}^\circ$. Find the measure of the fourth angle, in degrees."
    )
    solution = str(fourth)

    s = Steps()
    s.step(r"The four angles of a quadrilateral add up to $360^\circ$. "
           "Call the fourth angle $x$.",
           rf"{a}^\circ + {b}^\circ + {c}^\circ + x = 360^\circ")
    s.step("Add the three known angles.", rf"{known}^\circ + x = 360^\circ")
    s.step(rf"Subtract ${known}^\circ$ from both sides.",
           rf"x = 360^\circ - {known}^\circ = {fourth}^\circ")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def sum_of_polygon_angles(min_sides=3, max_sides=12):
    r"""Sum of the Interior Angles of a Polygon

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is the sum of the interior angles, in degrees, of a polygon with $9$ sides? | 1260 |

    Overrides the stock version, which wraps the answer in ``$`` and doesn't
    give the unit. The sum is ``(n - 2) * 180`` degrees.
    """
    n = random.randint(min_sides, max_sides)
    total = (n - 2) * 180
    problem = (
        f"What is the sum of the interior angles, in degrees, of a polygon "
        f"with ${n}$ sides?"
    )
    solution = str(total)

    s = Steps()
    s.formula(
        r"Diagonals from one vertex split a polygon with $n$ sides into $n - 2$ "
        r"triangles, and each triangle's angles add up to $180^\circ$. So the "
        "interior angle sum",
        r"S = (n - 2) \cdot 180^\circ",
    )
    s.substitute(rf"S = ({n} - 2) \cdot 180^\circ = {n - 2} \cdot 180^\circ",
                 text=f"Substitute $n = {n}$: the polygon splits into ${n - 2}$ triangles.")
    s.step("Multiply.", rf"S = {total}^\circ")
    s.answer(solution)
    return problem, solution, s.done()
