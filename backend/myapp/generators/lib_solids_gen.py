"""Solveki-local overrides for broken ``mathgenerator`` solids & roots generators.

Each generator here is named to *exactly* match a stock ``mathgenerator``
generator so ``_make_problem_for_topic`` (which resolves ``LOCAL_GENERATORS``
before the library) overrides the broken library version.

The library versions in this group share two families of defects:

* **Silent, wrong-precision rounding** — several pre-round to 2 decimals with no
  instruction (``pythagorean_theorem`` emits ``9.43`` when the true 3dp value is
  ``9.434``; ``area_of_triangle`` and ``curved_surface_area_cylinder`` likewise),
  so a student who rounds correctly to the thousandth is marked wrong. Others
  emit full unrounded floats (``314.1592653589793``) that no one could type.
* **Malformed / untypeable problem text** — ``area_of_triangle`` renders sides as
  ``$5, 19 16 = $`` (missing comma, dangling ``=``) and can emit degenerate
  triangles; ``cube_root`` uses ``\\sqrt[3]{...}``.

Every override computes at full precision, formats the number with :func:`num`
(round to the nearest thousandth, drop a trailing ``.0``), and — whenever the
answer is not always a plain integer — states the required rounding in the
problem text. Units match the library (``m^2`` / ``m^3``).
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._format import num
from ._steps import Steps, tex_frac

_ROUND_HINT = "Round your answer to the nearest thousandth."
_ROUNDED = "Rounded to the nearest thousandth, the answer is"
_CALC_PI = r"Multiply, using your calculator's value of $\pi$."


def _pi_times(coefficient):
    r"""LaTeX for ``coefficient * pi``, e.g. ``100\pi`` or ``\frac{500}{3}\pi``."""
    c = Fraction(coefficient)
    if c.denominator == 1:
        return rf"{c.numerator}\pi"
    return rf"{tex_frac(c.numerator, c.denominator)}\pi"


def _rel(exact):
    r"""``=`` for an exact value, ``\approx`` for a rounded one."""
    return "=" if exact else r"\approx"


def _reduced(numerator, denominator):
    f = Fraction(numerator, denominator)
    return f.numerator, f.denominator


def _lead(value):
    """The answer lead-in: mention rounding only when the value was rounded."""
    return "The answer is" if round(value, 3) == value else _ROUNDED


@register
def surface_area_sphere(min_r=2, max_r=20):
    r"""Surface Area of a Sphere

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Surface area of a sphere with radius $= 5 m$. Round... | $314.159 m^2$ |

    Overrides the stock generator, which emits an untypeable full-precision
    float (e.g. ``314.1592653589793``) with no rounding instruction.
    """
    r = random.randint(min_r, max_r)
    area = 4 * math.pi * r ** 2
    problem = (
        f"Find the surface area of a sphere with radius $= {r} m$. {_ROUND_HINT}"
    )
    solution = f"${num(area)} m^2$"

    s = Steps()
    s.formula("The surface area of a sphere", r"A = 4\pi r^2")
    s.substitute(rf"A = 4\pi ({r})^2")
    s.step(
        rf"Square the radius and multiply by $4$: $4 \times {r ** 2} = {4 * r ** 2}$.",
        rf"A = {4 * r ** 2}\pi",
    )
    s.step(_CALC_PI, rf"A \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@register
def volume_sphere(min_r=2, max_r=20):
    r"""Volume of a Sphere

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Volume of a sphere with radius $9 m$. Round... | $3053.628 m^3$ |

    Overrides the stock generator, which emits an untypeable full-precision
    float with no rounding instruction.
    """
    r = random.randint(min_r, max_r)
    volume = (4 / 3) * math.pi * r ** 3
    problem = (
        f"Find the volume of a sphere with radius $= {r} m$. {_ROUND_HINT}"
    )
    solution = f"${num(volume)} m^3$"

    s = Steps()
    s.formula("The volume of a sphere", r"V = \frac{4}{3}\pi r^3")
    s.substitute(rf"V = \frac{{4}}{{3}}\pi ({r})^3")
    s.step(
        f"Cube the radius: ${r}^3 = {r ** 3}$. Then multiply by $4/3$.",
        rf"V = \frac{{4}}{{3}} \times {r ** 3}\pi = {_pi_times(Fraction(4 * r ** 3, 3))}",
    )
    s.step(_CALC_PI, rf"V \approx {num(volume)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@register
def volume_hemisphere(min_r=2, max_r=20):
    r"""Volume of a Hemisphere

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Volume of a hemisphere with radius $9 m$. Round... | $1526.814 m^3$ |

    Overrides the stock generator, which pre-rounds to 3dp without instruction.
    """
    r = random.randint(min_r, max_r)
    volume = (2 / 3) * math.pi * r ** 3
    problem = (
        f"Find the volume of a hemisphere with radius $= {r} m$. {_ROUND_HINT}"
    )
    solution = f"${num(volume)} m^3$"

    s = Steps()
    s.step(
        "A hemisphere is half of a sphere, so its volume is half of "
        r"$\frac{4}{3}\pi r^3$:",
        r"V = \frac{2}{3}\pi r^3",
    )
    s.substitute(rf"V = \frac{{2}}{{3}}\pi ({r})^3")
    s.step(
        f"Cube the radius: ${r}^3 = {r ** 3}$. Then multiply by $2/3$.",
        rf"V = \frac{{2}}{{3}} \times {r ** 3}\pi = {_pi_times(Fraction(2 * r ** 3, 3))}",
    )
    s.step(_CALC_PI, rf"V \approx {num(volume)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@register
def volume_pyramid(min_dim=2, max_dim=20):
    r"""Volume of a Pyramid

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Volume of a pyramid with base area $= 45 m^2$ and height $= 8 m$. | $120 m^3$ |

    Overrides the stock generator, which emits trailing-``.0`` answers (``220.0``)
    and long unrounded decimals (``1551.6666666666667``) with no instruction.
    ``num`` drops the ``.0`` and rounds long decimals to the thousandth.
    """
    base_area = random.randint(min_dim, max_dim) * random.randint(min_dim, max_dim)
    height = random.randint(min_dim, max_dim)
    volume = (1 / 3) * base_area * height
    problem = (
        f"Find the volume of a pyramid with base area $= {base_area} m^2$ and "
        f"height $= {height} m$. {_ROUND_HINT}"
    )
    solution = f"${num(volume)} m^3$"

    s = Steps()
    s.formula("The volume of a pyramid", r"V = \frac{1}{3}Bh")
    s.substitute(
        rf"V = \frac{{1}}{{3}} \times {base_area} \times {height}",
        text=f"Substitute the base area $B = {base_area}$ and the height $h = {height}$.",
    )
    s.step(rf"Multiply: ${base_area} \times {height} = {base_area * height}$.",
           rf"V = \frac{{{base_area * height}}}{{3}}")
    exact = base_area * height % 3 == 0
    s.step("Divide by $3$.", rf"V {_rel(exact)} {num(volume)}")
    s.answer(solution, lead="The answer is" if exact else _ROUNDED)
    return problem, solution, s.done()


@register
def curved_surface_area_cylinder(min_r=2, max_r=20, min_h=2, max_h=20):
    r"""Curved Surface Area of a Cylinder

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Curved surface area of a cylinder with radius $9 m$, height $73 m$. | $4128.052 m^2$ |

    Overrides the stock generator, which silently pre-rounds to 2dp (``4128.05``)
    with no instruction, marking a correct 3dp answer wrong.
    """
    r = random.randint(min_r, max_r)
    h = random.randint(min_h, max_h)
    area = 2 * math.pi * r * h
    problem = (
        f"Find the curved surface area of a cylinder with radius $= {r} m$ and "
        f"height $= {h} m$. {_ROUND_HINT}"
    )
    solution = f"${num(area)} m^2$"

    s = Steps()
    s.formula(
        "The curved (side) surface of a cylinder unrolls into a rectangle, so its area",
        r"A = 2\pi r h",
    )
    s.substitute(rf"A = 2\pi ({r})({h})")
    s.step(rf"Multiply the numbers: $2 \times {r} \times {h} = {2 * r * h}$.",
           rf"A = {2 * r * h}\pi")
    s.step(_CALC_PI, rf"A \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@register
def cube_root(min_root=1, max_root=20):
    r"""Cube Root

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is the cube root of $2744$? | $14$ |

    Overrides the stock generator, whose problem uses ``\sqrt[3]{...}`` and
    pre-rounds to 2dp with no instruction. We pick a *perfect cube* so the cube
    root is always a clean integer — no rounding needed, no instruction required.
    """
    root = random.randint(min_root, max_root)
    n = root ** 3
    problem = f"What is the cube root of ${n}$?"
    solution = f"${num(root)}$"

    s = Steps()
    s.step(f"The cube root of ${n}$ is the number that, multiplied by itself three "
           f"times, gives ${n}$.")
    s.step(f"Try ${root}$:", rf"{root} \times {root} \times {root} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def area_of_triangle(min_side=3, max_side=20):
    r"""Area of a Triangle (Heron's Formula)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Area of a triangle with side lengths $6$, $7$, and $9$. Round... | $20.976 m^2$ |

    Overrides the stock generator, which renders sides poorly (``$5, 19 16 = $``),
    can emit degenerate (non-triangle) side sets, and pre-rounds to 2dp with no
    instruction. We resample until the triangle inequality is *strictly*
    satisfied, then apply Heron's formula at full precision.
    """
    while True:
        a = random.randint(min_side, max_side)
        b = random.randint(min_side, max_side)
        c = random.randint(min_side, max_side)
        # Strict triangle inequality: every side less than the sum of the others.
        if a + b > c and a + c > b and b + c > a:
            break
    s = (a + b + c) / 2
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    problem = (
        f"Find the area of a triangle with side lengths $= {a} m$, $= {b} m$, "
        f"and $= {c} m$. {_ROUND_HINT}"
    )
    solution = f"${num(area)} m^2$"

    # s(s-a)(s-b)(s-c) is P/16 for an integer P; show it as a fraction if it
    # doesn't fit in three decimals.
    p16 = (a + b + c) * (b + c - a) * (a + c - b) * (a + b - c)
    product = num(p16 / 16) if p16 * 1000 % 16 == 0 else tex_frac(*_reduced(p16, 16))
    st = Steps()
    st.step(
        "Heron's formula finds the area from the three sides. First find "
        "$s$, half of the perimeter:",
        rf"s = \frac{{{a} + {b} + {c}}}{{2}} = {num(s)}",
    )
    st.formula("Heron's formula", r"A = \sqrt{s(s-a)(s-b)(s-c)}")
    st.substitute(
        rf"A = \sqrt{{{num(s)}({num(s)} - {a})({num(s)} - {b})({num(s)} - {c})}}"
        rf" = \sqrt{{{num(s)} \times {num(s - a)} \times {num(s - b)} \times {num(s - c)}}}"
    )
    st.step("Multiply under the square root, then take the square root.",
            rf"A = \sqrt{{{product}}} {_rel(round(area, 3) == area)} {num(area)}")
    st.answer(solution, lead=_lead(area))
    return problem, solution, st.done()


@register
def pythagorean_theorem(min_leg=2, max_leg=15):
    r"""Pythagorean Theorem (Hypotenuse)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Hypotenuse of a right triangle with legs $5$ and $19$. Round... | $19.647 |

    Overrides the stock generator, which pre-rounds to 2dp (``19.65``) with no
    instruction, so a student who rounds correctly to the thousandth
    (``19.647``) is marked wrong. We compute at full precision and round to 3dp.
    """
    a = random.randint(min_leg, max_leg)
    b = random.randint(min_leg, max_leg)
    hypotenuse = math.sqrt(a ** 2 + b ** 2)
    problem = (
        f"What is the length of the hypotenuse of a right triangle whose legs "
        f"have lengths $= {a}$ and $= {b}$? {_ROUND_HINT}"
    )
    solution = f"${num(hypotenuse)}$"

    s = Steps()
    s.formula("The Pythagorean theorem, with legs $a$ and $b$ and hypotenuse $c$,",
              r"a^2 + b^2 = c^2")
    s.substitute(rf"{a}^2 + {b}^2 = c^2")
    s.step("Square the legs and add.", rf"{a ** 2} + {b ** 2} = {a ** 2 + b ** 2} = c^2")
    exact = round(hypotenuse) ** 2 == a ** 2 + b ** 2
    s.step("Take the square root of both sides.",
           rf"c = \sqrt{{{a ** 2 + b ** 2}}} {_rel(exact)} {num(hypotenuse)}")
    s.answer(solution, lead="The answer is" if exact else _ROUNDED)
    return problem, solution, s.done()


@register
def volume_cube(min_side=2, max_side=20):
    r"""Volume of a Cube

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the volume of a cube with side length $= 5 m$. | $125 m^3$ |

    Overrides the stock generator, whose problem trails off ("... is") and
    runs the value into the unit (``$5m$``).
    """
    a = random.randint(min_side, max_side)
    problem = f"Find the volume of a cube with side length $= {a} m$."
    solution = f"${a ** 3} m^3$"

    s = Steps()
    s.formula("The volume of a cube with side length $s$", r"V = s \times s \times s")
    s.substitute(rf"V = {a} \times {a} \times {a}")
    s.step(f"Multiply: ${a} \\times {a} = {a * a}$, then ${a * a} \\times {a} = {a ** 3}$.",
           rf"V = {a ** 3}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def volume_cuboid(min_side=2, max_side=20):
    r"""Volume of a Cuboid

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the volume of a cuboid (rectangular prism) with length $= 4 m$, width $= 3 m$, and height $= 5 m$. | $60 m^3$ |

    Overrides the stock generator, whose problem trails off ("... is") and
    runs the values into the unit (``$4m, 3m, 5m$``).
    """
    length = random.randint(min_side, max_side)
    width = random.randint(min_side, max_side)
    height = random.randint(min_side, max_side)
    volume = length * width * height
    problem = (
        f"Find the volume of a cuboid (rectangular prism) with length "
        f"$= {length} m$, width $= {width} m$, and height $= {height} m$."
    )
    solution = f"${volume} m^3$"

    s = Steps()
    s.formula("The volume of a cuboid",
              r"V = \text{length} \times \text{width} \times \text{height}")
    s.substitute(rf"V = {length} \times {width} \times {height}")
    s.step(f"Multiply the length and width: ${length} \\times {width} = {length * width}$.",
           rf"V = {length * width} \times {height}")
    s.step("Multiply by the height.", rf"V = {volume}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def volume_cylinder(min_r=2, max_r=20, min_h=2, max_h=20):
    r"""Volume of a Cylinder

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the volume of a cylinder with radius $= 3 m$ and height $= 10 m$. Round... | $282.743 m^3$ |

    Overrides the stock generator, which truncates the answer to an integer
    (``int(...)``: ``282.74`` becomes ``282``) with no instruction, marking a
    correctly rounded answer wrong.
    """
    r = random.randint(min_r, max_r)
    h = random.randint(min_h, max_h)
    volume = math.pi * r ** 2 * h
    problem = (
        f"Find the volume of a cylinder with radius $= {r} m$ and "
        f"height $= {h} m$. {_ROUND_HINT}"
    )
    solution = f"${num(volume)} m^3$"

    s = Steps()
    s.formula("The volume of a cylinder (base area times height)", r"V = \pi r^2 h")
    s.substitute(rf"V = \pi ({r})^2 ({h})")
    s.step(f"Square the radius and multiply by the height: "
           f"${r ** 2} \\times {h} = {r ** 2 * h}$.", rf"V = {r ** 2 * h}\pi")
    s.step(_CALC_PI, rf"V \approx {num(volume)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@register
def volume_cone(min_r=2, max_r=20, min_h=2, max_h=20):
    r"""Volume of a Cone

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the volume of a cone with radius $= 3 m$ and height $= 10 m$. Round... | $94.248 m^3$ |

    Overrides the stock generator, which truncates the answer to an integer
    (``int(...)``) with no instruction, marking a correctly rounded answer wrong.
    """
    r = random.randint(min_r, max_r)
    h = random.randint(min_h, max_h)
    volume = math.pi * r ** 2 * h / 3
    problem = (
        f"Find the volume of a cone with radius $= {r} m$ and "
        f"height $= {h} m$. {_ROUND_HINT}"
    )
    solution = f"${num(volume)} m^3$"

    s = Steps()
    s.formula("The volume of a cone", r"V = \frac{1}{3}\pi r^2 h")
    s.substitute(rf"V = \frac{{1}}{{3}}\pi ({r})^2 ({h})")
    s.step(f"Square the radius and multiply by the height: "
           f"${r ** 2} \\times {h} = {r ** 2 * h}$. Then divide by $3$.",
           rf"V = \frac{{{r ** 2 * h}}}{{3}}\pi = {_pi_times(Fraction(r ** 2 * h, 3))}")
    s.step(_CALC_PI, rf"V \approx {num(volume)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@register
def surface_area_cube(min_side=2, max_side=20):
    r"""Surface Area of a Cube

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the surface area of a cube with side length $= 5 m$. | $150 m^2$ |

    Overrides the stock generator, whose problem trails off ("... is") and
    runs the value into the unit (``$5m$``).
    """
    a = random.randint(min_side, max_side)
    problem = f"Find the surface area of a cube with side length $= {a} m$."
    solution = f"${6 * a ** 2} m^2$"

    s = Steps()
    s.step("A cube has $6$ faces, and each face is a square with the same side "
           "length, so:", r"SA = 6 \times s^2")
    s.step(f"Find the area of one face: ${a} \\times {a} = {a * a}$.")
    s.step("Multiply by the $6$ faces.", rf"SA = 6 \times {a * a} = {6 * a * a}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def surface_area_cuboid(min_side=2, max_side=20):
    r"""Surface Area of a Cuboid

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the surface area of a cuboid (rectangular prism) with length $= 4 m$, width $= 3 m$, and height $= 5 m$. | $94 m^2$ |

    Overrides the stock generator, whose problem trails off ("... is") and
    runs the values into the unit (``$4m, 3m, 5m$``).
    """
    length = random.randint(min_side, max_side)
    width = random.randint(min_side, max_side)
    height = random.randint(min_side, max_side)
    lw, lh, wh = length * width, length * height, width * height
    area = 2 * (lw + lh + wh)
    problem = (
        f"Find the surface area of a cuboid (rectangular prism) with length "
        f"$= {length} m$, width $= {width} m$, and height $= {height} m$."
    )
    solution = f"${area} m^2$"

    s = Steps()
    s.formula("A cuboid has $3$ pairs of matching rectangular faces, so its surface area",
              r"SA = 2(lw + lh + wh)")
    s.step(
        "Find the area of one face from each pair.",
        rf"lw = {length} \times {width} = {lw}, \quad lh = {length} \times {height} = {lh}, "
        rf"\quad wh = {width} \times {height} = {wh}",
    )
    s.step("Add them, then double to count both faces of each pair.",
           rf"SA = 2({lw} + {lh} + {wh}) = 2 \times {lw + lh + wh} = {area}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def surface_area_cone(min_r=2, max_r=15, max_slant=25):
    r"""Surface Area of a Cone

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the total surface area of a cone with radius $= 3 m$ and slant height $= 5 m$. Round... | $75.398 m^2$ |

    Overrides the stock generator, which truncates the answer to an integer
    (``int(...)``) with no instruction. We give the slant height directly (it
    is always longer than the radius) rather than the vertical height, so a
    Grade 7 problem doesn't hide a Pythagorean-theorem step.
    """
    r = random.randint(min_r, max_r)
    slant = random.randint(r + 1, max(r + 1, max_slant))
    area = math.pi * r ** 2 + math.pi * r * slant
    problem = (
        f"Find the total surface area of a cone with radius $= {r} m$ and "
        f"slant height $= {slant} m$. {_ROUND_HINT}"
    )
    solution = f"${num(area)} m^2$"

    s = Steps()
    s.formula("The surface area of a cone (the circular base plus the curved side), "
              "with slant height $l$,", r"SA = \pi r^2 + \pi r l")
    s.substitute(rf"SA = \pi ({r})^2 + \pi ({r})({slant})")
    s.step(f"Multiply: ${r}^2 = {r ** 2}$ and ${r} \\times {slant} = {r * slant}$. "
           r"Then add the multiples of $\pi$.",
           rf"SA = {r ** 2}\pi + {r * slant}\pi = {r ** 2 + r * slant}\pi")
    s.step(_CALC_PI, rf"SA \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@register
def surface_area_cylinder(min_r=2, max_r=20, min_h=2, max_h=20):
    r"""Surface Area of a Cylinder

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the total surface area of a cylinder with radius $= 3 m$ and height $= 10 m$. Round... | $245.044 m^2$ |

    Overrides the stock generator, which truncates the answer to an integer
    (``int(...)``) with no instruction, marking a correctly rounded answer wrong.
    """
    r = random.randint(min_r, max_r)
    h = random.randint(min_h, max_h)
    area = 2 * math.pi * r ** 2 + 2 * math.pi * r * h
    problem = (
        f"Find the total surface area of a cylinder with radius $= {r} m$ and "
        f"height $= {h} m$. {_ROUND_HINT}"
    )
    solution = f"${num(area)} m^2$"

    s = Steps()
    s.formula("The surface area of a cylinder (two circular bases plus the curved side)",
              r"SA = 2\pi r^2 + 2\pi r h")
    s.substitute(rf"SA = 2\pi ({r})^2 + 2\pi ({r})({h})")
    s.step(f"Multiply: $2 \\times {r ** 2} = {2 * r ** 2}$ and "
           f"$2 \\times {r} \\times {h} = {2 * r * h}$. Then add the multiples of $\\pi$.",
           rf"SA = {2 * r ** 2}\pi + {2 * r * h}\pi = {2 * r ** 2 + 2 * r * h}\pi")
    s.step(_CALC_PI, rf"SA \approx {num(area)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


def _pyramid_legs(height, max_half):
    """Half-base lengths ``a`` for which ``height**2 + a**2`` is a perfect square."""
    return [a for a in range(1, max_half + 1)
            if math.isqrt(height ** 2 + a ** 2) ** 2 == height ** 2 + a ** 2]


@register
def surface_area_pyramid(min_h=3, max_h=20, max_half=16):
    r"""Surface Area of a Rectangular Pyramid

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A rectangular pyramid has a base with length $= 10 m$ and width $= 18 m$. Each triangular face on a length side has slant height $= 15 m$, and each face on a width side has slant height $= 13 m$. Find its total surface area. | $564 m^2$ |

    Overrides the stock generator, which shuffles a Pythagorean triple — so the
    pyramid's height can come out as a triple's hypotenuse and the "slant
    heights" it uses don't fit the stated dimensions, giving wrong answers. We
    pick a height and half-base lengths that form right triangles with integer
    slant heights, and state the slant heights directly (as Grade 7 problems
    do), so the answer is always an integer.
    """
    heights = [h for h in range(min_h, max_h + 1) if _pyramid_legs(h, max_half)]
    height = random.choice(heights)
    legs = _pyramid_legs(height, max_half)
    half_length, half_width = random.choice(legs), random.choice(legs)
    length, width = 2 * half_length, 2 * half_width
    # A face on a length side leans in over half the width, and vice versa.
    slant_l = math.isqrt(height ** 2 + half_width ** 2)
    slant_w = math.isqrt(height ** 2 + half_length ** 2)
    base = length * width
    area = base + length * slant_l + width * slant_w
    problem = (
        f"A rectangular pyramid has a base with length $= {length} m$ and width "
        f"$= {width} m$. Each triangular face on a length side has slant height "
        f"$= {slant_l} m$, and each face on a width side has slant height "
        f"$= {slant_w} m$. Find its total surface area."
    )
    solution = f"${area} m^2$"

    s = Steps()
    s.step("The surface area is the rectangular base plus the four triangular faces. "
           "Start with the base.", rf"{length} \times {width} = {base}")
    s.step(
        r"Each face on a length side is a triangle with area "
        r"$\frac{1}{2} \times \text{base} \times \text{slant height}$, and there are two of them.",
        rf"2 \times \frac{{1}}{{2}} \times {length} \times {slant_l} = {length * slant_l}",
    )
    s.step("Do the same for the two faces on the width sides.",
           rf"2 \times \frac{{1}}{{2}} \times {width} \times {slant_w} = {width * slant_w}")
    s.step("Add the base and the four faces.",
           rf"SA = {base} + {length * slant_l} + {width * slant_w} = {area}")
    s.answer(solution)
    return problem, solution, s.done()
