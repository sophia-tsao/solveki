"""Solveki-local generators filling gaps in AP Precalculus Unit 3 (trigonometric and polar functions).

Every generator here takes no required arguments, is decorated with
``@register``, and returns ``(problem, solution, steps)``: LaTeX strings plus a
step-by-step explanation built with ``_steps.Steps``. Never seed ``random``
inside a generator.

Answers stay typeable: integers, decimals rounded to the nearest thousandth,
degree measures, the words ``increasing``/``decreasing``/``undefined``, or a
compound inequality like ``30 < x < 150``. Radian angles appear only in the
problem text (rendered by KaTeX), never in an answer.
"""
import random
from fractions import Fraction
from math import cos, pi

from ._registry import register
from ._variants import with_variants
from ._format import num as _num
from ._steps import Steps
from .precalculus import (_UNIT_ANGLES, _angle_latex, _approx, _exact_trig,
                          _exact_trig_line, _reference_step, _s_add, _s_div,
                          _s_float, _s_rational, _s_scale, _s_tex, _signed)

_ROUND_HINT = "Round your answer to the nearest thousandth."
_ROUND_LEAD = "Rounded to the nearest thousandth, the answer is"


def _deg(value):
    r"""A degree measure as LaTeX: ``30^\circ``."""
    return rf"{value}^\circ"


def _times(k, body):
    """``k`` times ``body`` with unit coefficients dropped: ``3\\sin``, ``-\\cos``."""
    if k == 1:
        return body
    if k == -1:
        return f"-{body}"
    return f"{k}{body}"


def _wrap_tex(tex):
    r"""Parenthesise LaTeX that starts with a minus sign (for products)."""
    return rf"\left({tex}\right)" if tex.startswith("-") else tex


def _lead(exact):
    """The closing lead for an answer that is exact or was rounded."""
    return "The answer is" if exact else _ROUND_LEAD


# --------------------- AP 3.1 periodic phenomena ---------------------

def _primitive_cycle(p, lo, hi):
    """``p`` random integers whose smallest repeating block is all ``p`` of them."""
    while True:
        values = [random.randint(lo, hi) for _ in range(p)]
        if not any(p % d == 0 and all(values[i] == values[(i + d) % p] for i in range(p))
                   for d in range(1, p)):
            return values


@register
@with_variants
def pc_periodic_values(min_period=3, max_period=7, min_value=-9, max_value=9,
                       min_input=20, max_input=99):
    r"""Values of a Periodic Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $f$ is periodic with period $4$, and $f(0) = 3$, $f(1) = -2$, $f(2) = 5$, $f(3) = 0$. Find $f(37)$. | $-2$ |
    | The values of $f$ at $x = 0, 1, 2, \ldots$ are $1, 4, 2, 1, 4, 2, 1, 4$. Find the period of $f$. | $3$ |

    Either reduce a far input modulo the period and read it off one cycle, or
    find the period of repeating data (at least two full cycles are shown, so
    the period is determined).
    """
    p = random.randint(min_period, max_period)
    values = _primitive_cycle(p, min_value, max_value)
    s = Steps()

    if random.random() < 0.5:
        # Far input: one cycle is listed starting at x = start.
        start = random.randint(0, 3)
        n = random.randint(min_input, max_input) * random.choice([1, 1, -1])
        r = (n - start) % p
        target, k = start + r, (n - start - r) // p
        listed = ", ".join(f"$f({start + i}) = {v}$" for i, v in enumerate(values))
        problem = (f"The function $f$ is periodic with period ${p}$, and over one "
                   f"period its values are {listed}. Find $f({n})$.")
        solution = f"${values[r]}$"
        s.step(f"A function with period ${p}$ repeats every ${p}$ units: "
               f"$f(x + {p}k) = f(x)$ for every integer $k$.")
        s.step(f"Write ${n}$ as an input from the listed cycle plus a multiple of "
               f"the period.", f"{n} = {target} + {p}({k})")
        s.step("Shifting by whole periods doesn't change the value.",
               f"f({n}) = f({target}) = {values[r]}")
    else:
        count = 2 * p + random.randint(0, 2)
        data = [values[i % p] for i in range(count)]
        problem = (f"The values of a periodic function $f$ at $x = 0, 1, 2, "
                   f"\\ldots, {count - 1}$ are ${', '.join(map(str, data))}$. "
                   f"What is the period of $f$?")
        solution = f"${p}$"
        s.step("The period is the length of the smallest block of values that "
               "repeats over and over.")
        s.step(f"The block ${', '.join(map(str, values))}$ (that is, $f(0)$ "
               f"through $f({p - 1})$) repeats, starting again at $f({p}) = "
               f"{values[0]}$, and no shorter block repeats.")
        s.step(f"The block has ${p}$ values, so $f(x + {p}) = f(x)$.")
    s.answer(solution)
    return problem, solution, s.done()


# ------------------ AP 3.7 sinusoidal modeling ------------------

def _model_context():
    """A context as ``(description, max, min, period, starts_at_max, var, unit)``."""
    kind = random.choice(["wheel", "tide", "temperature"])
    if kind == "wheel":
        r, base, T = random.randint(10, 30), random.randint(2, 5), random.randint(2, 10)
        text = (f"A Ferris wheel has a diameter of ${2 * r}$ feet, and its lowest "
                f"point is ${base}$ feet above the ground. It completes one "
                f"revolution every ${T}$ minutes. A rider boards at the lowest point "
                f"at $t = 0$, and $h(t)$ is the rider's height in feet after $t$ "
                f"minutes.")
        return text, base + 2 * r, base, T, False, "h", "minutes"
    if kind == "tide":
        low = random.randint(1, 6)
        high = low + 2 * random.randint(3, 8)
        T = random.randint(10, 14)
        text = (f"The water depth at a harbor varies sinusoidally between a high "
                f"tide of ${high}$ feet and a low tide of ${low}$ feet, with ${T}$ "
                f"hours between consecutive high tides. High tide occurs at $t = 0$, "
                f"and $h(t)$ is the depth in feet after $t$ hours.")
        return text, high, low, T, True, "h", "hours"
    low = random.randint(40, 70)
    high = low + 2 * random.randint(5, 15)
    text = (f"The temperature in a city varies sinusoidally over a $24$-hour day "
            f"between a low of ${low}^\\circ$F and a high of ${high}^\\circ$F. The "
            f"low occurs at $t = 0$, and $T(t)$ is the temperature in degrees "
            f"Fahrenheit $t$ hours later.")
    return text, high, low, 24, False, "T", "hours"


@register
@with_variants
def pc_sinusoidal_model():
    r"""Sinusoidal Models in Context

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A Ferris wheel has a diameter of $40$ feet, its lowest point is $3$ feet up, and one revolution takes $8$ minutes. A rider boards at the bottom at $t = 0$. Find the height after $3$ minutes, rounded to the nearest thousandth. | $37.142$ |

    Build ``A cos(Bt) + D`` from the maximum, minimum, and period: ``|A|`` is
    half the range, ``D`` the average, ``B = 2*pi/period``, and ``A`` is
    negative when the context starts at its minimum.
    """
    text, high, low, T, starts_at_max, var, unit = _model_context()
    amp, mid = (high - low) // 2, (high + low) // 2
    A = amp if starts_at_max else -amp
    B = 2 * pi / T
    ask = random.choice(["amplitude", "midline", "B", "value"])
    model = rf"{var}(t) = {_times(A, r'\cos')}\left(\frac{{2\pi}}{{{T}}}t\right) + {mid}"

    if ask == "amplitude":
        problem = f"{text} What is the amplitude of ${var}$?"
        solution = f"${amp}$"
    elif ask == "midline":
        problem = (f"{text} Give the equation of the midline of ${var}$ in the "
                   f"form y = c.")
        solution = f"$y = {mid}$"
    elif ask == "B":
        problem = (f"{text} If ${var}(t) = A\\cos(Bt) + D$ with $B > 0$, what is "
                   f"$B$? {_ROUND_HINT}")
        solution = f"${_num(B)}$"
    else:
        t = random.randint(1, 2 * T - 1) / 2  # a half-unit time within one cycle
        value = mid + A * cos(B * t)
        problem = (f"{text} Find ${var}({_num(t)})$, the value after ${_num(t)}$ "
                   f"{unit}. {_ROUND_HINT}")
        solution = f"${_num(value)}$"

    s = Steps()
    s.step("The amplitude is half the distance from the maximum to the minimum.",
           rf"|A| = \frac{{{high} - {low}}}{{2}} = {amp}")
    if ask == "amplitude":
        s.answer(solution)
        return problem, solution, s.done()
    s.step("The midline is halfway between the maximum and minimum.",
           rf"D = \frac{{{high} + {low}}}{{2}} = {mid}")
    if ask == "midline":
        s.answer(solution)
        return problem, solution, s.done()
    s.step(f"One full cycle takes ${T}$ {unit}, so $B = \\frac{{2\\pi}}{{\\text{{period}}}}$.",
           rf"B = \frac{{2\pi}}{{{T}}} \approx {_num(B)}")
    if ask == "B":
        s.answer(solution, lead=_ROUND_LEAD)
        return problem, solution, s.done()
    where = "maximum" if starts_at_max else "minimum"
    s.step(f"At $t = 0$ the value is at its {where}, so use cosine"
           + ("." if starts_at_max else " with a negative $A$ (a reflected cosine starts at its minimum)."),
           model)
    s.substitute(rf"{var}({_num(t)}) = {mid} {'+' if A > 0 else '-'} {amp}\cos\left("
                 rf"\frac{{2\pi}}{{{T}}} \cdot {_num(t)}\right) \approx {_num(value)}",
                 text=f"Substitute $t = {_num(t)}$ (calculator in radian mode).")
    s.answer(solution, lead=_ROUND_LEAD)
    return problem, solution, s.done()


# ------------------- AP 3.6 sinusoid transformations -------------------

# Horizontal translations as (num, den) of pi, sampled for g(x) = A f(b(x - h)) + d.
_SHIFTS = [(0, 1), (1, 6), (1, 4), (1, 3), (1, 2)]


@register
@with_variants
def pc_sinusoid_transformations(max_stretch=5, max_b=4, max_shift_up=5):
    r"""Sinusoid Transformations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $f(x) = \sin x$ is dilated vertically by $3$, horizontally by $\frac{1}{2}$, then translated $4$ units up to give $g$. What is the maximum value of $g$? | $7$ |

    Translate a verbal list of transformations of ``sin x``/``cos x`` into
    ``g(x) = A f(b(x - h)) + d``, then report its maximum, minimum, period
    (rounded), or value at a standard angle (rounded).
    """
    fn = random.choice(["sin", "cos"])
    a = random.randint(2, max_stretch)
    reflect = random.random() < 0.4
    b = random.randint(2, max_b)
    hn, hd = random.choice(_SHIFTS)
    h_dir = random.choice([1, -1])
    d = random.choice([i for i in range(-max_shift_up, max_shift_up + 1) if i != 0])
    A = -a if reflect else a
    ask = random.choice(["max", "min", "period", "value"])

    parts = [f"a vertical dilation by a factor of ${a}$"]
    if reflect:
        parts.append("a reflection over the $x$-axis")
    parts.append(f"a horizontal dilation by a factor of $\\frac{{1}}{{{b}}}$")
    if hn:
        parts.append(f"a horizontal translation of ${_angle_latex(hn, hd)}$ units "
                     f"{'right' if h_dir > 0 else 'left'}")
    parts.append(f"a vertical translation of ${abs(d)}$ units "
                 f"{'up' if d > 0 else 'down'}")
    listed = ", ".join(parts[:-1]) + ", and " + parts[-1]
    intro = (f"The graph of $f(x) = \\{fn} x$ is transformed into the graph of "
             f"$g$ by {listed}, in that order.")

    h_tex = _angle_latex(hn, hd)
    if hn == 0:
        inner = f"{b}x"
    else:
        inner = f"{b}\\left(x {'-' if h_dir > 0 else '+'} {h_tex}\\right)"
    g_tex = rf"g(x) = {_times(A, '\\' + fn)}\left({inner}\right){_signed(d)}"

    if ask == "max":
        problem = f"{intro} What is the maximum value of $g$?"
        solution = f"${a + d}$"
    elif ask == "min":
        problem = f"{intro} What is the minimum value of $g$?"
        solution = f"${d - a}$"
    elif ask == "period":
        problem = f"{intro} What is the period of $g$? {_ROUND_HINT}"
        solution = f"${_num(2 * pi / b)}$"
    else:
        # Pick x so that x - h is a multiple of 30 or 45 degrees (an exact value).
        h_deg = h_dir * hn * 180 // hd
        while True:
            xn, xd = random.choice(_UNIT_ANGLES[1:])
            x_deg = xn * 180 // xd
            if (x_deg - h_deg) % 30 == 0 or (x_deg - h_deg) % 45 == 0:
                break
        arg_deg = b * (x_deg - h_deg)
        exact = _s_add({1: Fraction(d)}, _s_scale(_exact_trig(fn, arg_deg), A))
        x_tex = _angle_latex(xn, xd)
        problem = (f"{intro} Evaluate $g\\left({x_tex}\\right)$. Round your "
                   f"answer to the nearest thousandth if it is irrational.")
        solution = f"${_num(_s_float(exact))}$"

    s = Steps()
    s.step(f"Each transformation changes one parameter of $g(x) = A\\{fn}(b(x - h)) + d$: "
           f"the vertical dilation{' and reflection give' if reflect else ' gives'} $A = {A}$, "
           f"the horizontal dilation by $\\frac{{1}}{{{b}}}$ gives $b = {b}$, "
           + (f"the horizontal translation gives $h = {'-' if h_dir < 0 else ''}{h_tex}$, "
              if hn else "")
           + f"and the vertical translation gives $d = {d}$.", g_tex)
    if ask in ("max", "min"):
        s.step("The sinusoid swings $|A|$ above and below its midline $y = d$.",
               rf"d + |A| = {d} + {a} = {a + d}, \quad d - |A| = {d} - {a} = {d - a}")
        s.answer(solution, lead=f"The {'maximum' if ask == 'max' else 'minimum'} value is")
    elif ask == "period":
        s.step(r"Only the horizontal dilation changes the period: it is $\frac{2\pi}{b}$.",
               rf"\frac{{2\pi}}{{{b}}} \approx {_num(2 * pi / b)}")
        s.answer(solution, lead=_ROUND_LEAD)
    else:
        s.step(f"Substitute $x = {x_tex}$ and work out the angle in degrees.",
               rf"{b}\left({_deg(x_deg)} - {_deg(h_deg) if h_deg >= 0 else '(' + _deg(h_deg) + ')'}"
               rf"\right) = {_deg(arg_deg)}")
        s.step("Use the special-angle value.",
               _exact_trig_line(fn, arg_deg % 360, _deg(arg_deg)))
        s.step(f"Multiply by ${A}$ and add ${d}$.",
               rf"g\left({x_tex}\right) = {_approx(exact)}")
        s.answer(solution, lead=_lead(_s_rational(exact)))
    return problem, solution, s.done()


# ---------------------- AP 3.8 the tangent function ----------------------

# Horizontal scale factors b with 90/b a whole number of degrees.
_TAN_B = [1, 2, 3, 5, 6]


def _tan_equation(a, b, c, d):
    r"""``y = a\tan(b(x - c^\circ)) + d`` with signs and unit factors folded."""
    if c == 0:
        inside = "x" if b == 1 else f"{b}x"
    else:
        shifted = f"x {'-' if c > 0 else '+'} {_deg(abs(c))}"
        inside = shifted if b == 1 else f"{b}({shifted})"
    return rf"y = {_times(a, r'\tan')}\left({inside}\right){_signed(d)}"


@register
@with_variants
def pc_tangent_features(max_a=4, max_shift=60, max_d=5):
    r"""Tangent Function Features

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | For $y = 2\tan(3(x - 10^\circ)) + 1$, with $x$ in degrees, what is the period in degrees? | $60$ |
    | For $y = 2\tan(3(x - 10^\circ)) + 1$, find the smallest positive $x$ (in degrees) of a vertical asymptote. | $40$ |

    ``y = a tan(b(x - c)) + d`` has period ``180/b`` degrees (``pi/b``
    radians), vertical asymptotes where ``b(x - c) = 90 + 180k``, and is
    increasing between asymptotes exactly when ``a > 0``.
    """
    a = random.choice([i for i in range(-max_a, max_a + 1) if i != 0])
    b = random.choice(_TAN_B)
    c = random.choice(range(-max_shift, max_shift + 1, 5))
    d = random.randint(-max_d, max_d)
    ask = random.choice(["period", "period_rad", "asymptote", "direction", "value"])
    s = Steps()

    if ask == "period_rad":
        b = random.randint(2, 6)
        eq = rf"y = {_times(a, r'\tan')}({b}x){_signed(d)}"
        problem = (f"What is the period of ${eq}$, where $x$ is in radians? "
                   f"{_ROUND_HINT}")
        solution = f"${_num(pi / b)}$"
        s.step("$\\tan x$ repeats every $\\pi$ radians, so $\\tan(bx)$ has period "
               "$\\frac{\\pi}{b}$. The values of $a$ and $d$ don't change the period.")
        s.step("Substitute.", rf"\frac{{\pi}}{{{b}}} \approx {_num(pi / b)}")
        s.answer(solution, lead=_ROUND_LEAD)
        return problem, solution, s.done()

    eq = _tan_equation(a, b, c, d)
    where = f"For ${eq}$, where $x$ is in degrees,"
    match = (f"Match ${eq}$ to $y = a\\tan(b(x - c)) + d$: $a = {a}$, $b = {b}$, "
             f"$c = {_deg(c)}$, $d = {d}$.")
    if ask == "period":
        problem = f"{where} what is the period in degrees?"
        solution = f"${180 // b}$"
        s.step(match)
        s.step("$\\tan x$ repeats every $180^\\circ$, so the period is "
               "$\\frac{180^\\circ}{b}$.", rf"\frac{{180^\circ}}{{{b}}} = {_deg(180 // b)}")
    elif ask == "asymptote":
        step = 180 // b
        x0 = c + 90 // b
        first = x0 - ((x0 - 1) // step) * step  # smallest positive member of x0 + step*k
        problem = (f"{where} find the smallest positive $x$-value (in degrees) at "
                   f"which the graph has a vertical asymptote.")
        solution = f"${first}$"
        s.step(match)
        s.step("$\\tan\\theta$ is undefined where $\\theta = 90^\\circ + 180^\\circ k$. "
               "Set the inside equal to that and solve for $x$.",
               rf"{b}(x - {_deg(c) if c >= 0 else '(' + _deg(c) + ')'}) = 90^\circ + 180^\circ k"
               rf"\;\Rightarrow\; x = {_deg(x0)} + {_deg(step)} k")
        s.step(f"Try integers $k$: the asymptotes are ${_deg(x0)}$ shifted by "
               f"multiples of ${_deg(step)}$, and the smallest positive one is "
               f"${_deg(first)}$.")
    elif ask == "direction":
        problem = (f"{where} is the graph increasing or decreasing between "
                   f"consecutive vertical asymptotes? Type increasing or decreasing.")
        solution = "increasing" if a > 0 else "decreasing"
        s.step(match)
        s.step("$\\tan x$ is increasing on every branch between its asymptotes. "
               "Shifts and a positive horizontal factor $b$ don't change that, but "
               "a negative $a$ reflects the graph over its midline, turning it "
               "decreasing.")
        s.step(f"Here $a = {a}$ is {'positive' if a > 0 else 'negative'}.")
    else:
        theta = random.choice([t for t in (-60, -45, -30, 30, 45, 60) if t % b == 0])
        x = c + theta // b
        exact = _s_add({1: Fraction(d)}, _s_scale(_exact_trig("tan", theta), a))
        problem = (f"{where} find $y$ when $x = {_deg(x)}$. Round your answer to "
                   f"the nearest thousandth if it is irrational.")
        solution = f"${_num(_s_float(exact))}$"
        s.step(match)
        s.step(f"Substitute $x = {_deg(x)}$ and simplify the angle.",
               rf"{b}\left({_deg(x)} - {_deg(c) if c >= 0 else '(' + _deg(c) + ')'}\right) = {_deg(theta)}")
        s.step("Use the special-angle value.",
               _exact_trig_line("tan", theta % 360, _deg(theta)))
        s.step(f"Multiply by ${a}$ and add ${d}$.", rf"y = {_approx(exact)}")
        s.answer(solution, lead=_lead(_s_rational(exact)))
        return problem, solution, s.done()
    s.answer(solution)
    return problem, solution, s.done()


# -------------------- AP 3.10 trigonometric inequalities --------------------

_REL_TEX = {">": ">", ">=": r"\geq", "<": "<", "<=": r"\leq"}
# Domain shown in the problem for each case, as (lo, lo_rel, hi_rel, hi).
_DOMAIN_0_360 = (0, "<=", "<", 360)


def _interval(lo, lo_rel, hi_rel, hi):
    """Typeable compound inequality ``lo REL x REL hi``."""
    return f"{lo} {lo_rel} x {hi_rel} {hi}"


@register
@with_variants
def pc_trig_inequality():
    r"""Trigonometric Inequalities

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $\sin x > \frac{1}{2}$ for $0^\circ \leq x < 360^\circ$. | 30 < x < 150 |

    Each case is chosen so the solution is a single interval inside the stated
    domain: ``sin x > c`` (c >= 0) and ``sin x < c`` (c <= 0) and ``cos x < c``
    on ``[0, 360)``, ``cos x > c`` on ``(-180, 180]``, ``tan x`` on
    ``(-90, 90)``. Non-strict inequalities include their boundary angles.
    """
    case = random.choice(["sin>", "sin<", "cos<", "cos>", "tan>", "tan<"])
    rel = random.choice([case[-1], case[-1] + "="])
    strict = len(rel) == 1
    fn = case[:3]
    open_end = "<" if strict else "<="

    if case == "sin>":
        b1 = random.choice([0, 30, 45, 60])
        b2 = 180 - b1
        domain = _DOMAIN_0_360
        why = (f"On the unit circle, $\\sin x$ (the height) is above that value "
               f"between the two angles, ${_deg(b1)} < x < {_deg(b2)}$.")
    elif case == "sin<":
        ref = random.choice([0, 30, 45, 60] if strict else [30, 45, 60])
        b1, b2 = 180 + ref, 360 - ref
        domain = _DOMAIN_0_360
        why = (f"On the unit circle, $\\sin x$ (the height) is below that value "
               f"between the two angles, ${_deg(b1)} < x < {_deg(b2)}$.")
    elif case == "cos<":
        b1 = random.choice([30, 45, 60, 90, 120, 135, 150])
        b2 = 360 - b1
        domain = _DOMAIN_0_360
        why = (f"On the unit circle, $\\cos x$ (the horizontal coordinate) is "
               f"left of that value between the two angles, "
               f"${_deg(b1)} < x < {_deg(b2)}$.")
    elif case == "cos>":
        b2 = random.choice([30, 45, 60, 90, 120, 135, 150])
        b1 = -b2
        domain = (-180, "<", "<=", 180)
        why = (f"On the unit circle, $\\cos x$ (the horizontal coordinate) is "
               f"right of that value between the two angles, "
               f"${_deg(b1)} < x < {_deg(b2)}$.")
    else:
        t = random.choice([-60, -45, -30, 0, 30, 45, 60])
        domain = (-90, "<", "<", 90)
        if case == "tan>":
            b1, b2 = t, 90
        else:
            b1, b2 = -90, t
        why = ("$\\tan x$ increases on this whole domain, rising toward the "
               "asymptote at $90^\\circ$, so it is "
               + ("above" if case == "tan>" else "below")
               + f" the value on the side of ${_deg(t)}$ "
               + ("toward $90^\\circ$." if case == "tan>" else "toward $-90^\\circ$."))
        boundary = t

    if fn == "tan":
        c_deg = boundary
        lo_rel = open_end if case == "tan>" else "<"
        hi_rel = "<" if case == "tan>" else open_end
    else:
        c_deg = b1  # fn(b1) = fn(b2) = c
        lo_rel = hi_rel = open_end
    c_tex = _s_tex(_exact_trig(fn, c_deg))
    lo, dlo, dhi, hi = domain
    domain_tex = (f"{_deg(lo)} {_REL_TEX[dlo]} x {_REL_TEX[dhi]} {_deg(hi)}")
    problem = (f"Solve $\\{fn} x {_REL_TEX[rel]} {c_tex}$ for ${domain_tex}$. Give "
               f"your answer in degrees as a compound inequality such as "
               f"30 < x < 150, using < or <= on each side as needed.")
    solution = _interval(b1, lo_rel, hi_rel, b2)

    s = Steps()
    if fn == "tan":
        s.step(f"First solve the equation $\\tan x = {c_tex}$ on the domain. "
               f"Tangent takes each value once there.",
               rf"\tan {_deg(boundary)} = {c_tex}")
    else:
        s.step(f"First solve the equation $\\{fn} x = {c_tex}$ on the domain to "
               f"find the boundary angles.",
               rf"x = {_deg(b1)} \quad \text{{or}} \quad x = {_deg(b2)}")
    s.step(why)
    if strict:
        s.step("The inequality is strict, so the boundary angles themselves are "
               "not solutions.")
    else:
        s.step(f"The inequality includes equality, so the angle"
               f"{'' if fn == 'tan' else 's'} where $\\{fn} x = {c_tex}$ "
               f"{'is' if fn == 'tan' else 'are'} included"
               + (" (the asymptote at $\\pm 90^\\circ$ never is)." if fn == "tan" else "."))
    s.answer(solution)
    return problem, solution, s.done()


# ------------------ AP 3.11 secant, cosecant, cotangent ------------------

_RECIPROCAL = {
    "sec": ("cos", r"\sec\theta = \frac{1}{\cos\theta}"),
    "csc": ("sin", r"\csc\theta = \frac{1}{\sin\theta}"),
    "cot": ("tan", r"\cot\theta = \frac{\cos\theta}{\sin\theta}"),
}


@register
@with_variants
def pc_reciprocal_trig_values():
    r"""Secant, Cosecant, and Cotangent Values

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\sec\left(\frac{\pi}{6}\right)$. Round to the nearest thousandth if irrational; type undefined if it is undefined. | $1.155$ |

    Evaluate sec/csc/cot at a standard unit-circle angle as the reciprocal (or
    cos/sin quotient) of an exact value; "undefined" where the denominator is 0.
    """
    fn = random.choice(["sec", "csc", "cot"])
    num, den = random.choice(_UNIT_ANGLES)
    angle = _angle_latex(num, den)
    deg = num * 180 // den
    base, identity = _RECIPROCAL[fn]
    cos_v, sin_v = _exact_trig("cos", deg), _exact_trig("sin", deg)
    bottom = sin_v if fn in ("csc", "cot") else cos_v
    top = cos_v if fn == "cot" else {1: Fraction(1)}

    problem = (f"Evaluate $\\{fn}\\left({angle}\\right)$. Round your answer to the "
               f"nearest thousandth if it is irrational. If the value is "
               f"undefined, type undefined.")
    if not bottom:
        value = None
        solution = "undefined"
    else:
        value = _s_div(top, bottom)
        solution = f"${_num(_s_float(value))}$"

    s = Steps()
    s.formula("The reciprocal identity" if fn != "cot" else "The quotient identity", identity)
    if num:
        s.step("Convert to degrees by multiplying by $\\frac{180^\\circ}{\\pi}$.",
               rf"{angle} \cdot \frac{{180^\circ}}{{\pi}} = {_deg(deg)}")
    if fn == "cot":
        s.step("Read the cosine and sine off the unit circle.",
               rf"\cos {_deg(deg)} = {_s_tex(cos_v)}, \quad \sin {_deg(deg)} = {_s_tex(sin_v)}")
    else:
        _reference_step(s, base, deg)
        s.step("Use the special-angle value.", _exact_trig_line(base, deg, _deg(deg)))
    if value is None:
        s.step(f"The denominator $\\{'sin' if fn != 'sec' else 'cos'} {_deg(deg)}$ is "
               f"$0$, and division by zero is undefined.")
        s.answer(solution)
    else:
        line = (rf"\{fn} {_deg(deg)} = \frac{{{_s_tex(top)}}}{{{_s_tex(bottom)}}} = "
                rf"{_approx(value)}")
        s.step("Divide" + (", rationalizing the denominator if needed." if not
                           _s_rational(bottom) else "."), line)
        s.answer(solution, lead=_lead(_s_rational(value)))
    return problem, solution, s.done()


# ---------------------- AP 3.14 polar function graphs ----------------------

def _polar_trig(fn, n=1):
    r"""``\cos\theta`` / ``\sin(3\theta)``."""
    return rf"\{fn}\theta" if n == 1 else rf"\{fn}({n}\theta)"


def _limacon(a, b, fn):
    r"""``r = a + b\cos\theta`` with the sign of ``b`` folded in."""
    term = _times(abs(b), _polar_trig(fn))
    return rf"r = {a} {'+' if b > 0 else '-'} {term}"


@register
@with_variants
def pc_polar_graph_features(max_coeff=6, max_n=6):
    r"""Polar Graph Features

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | How many petals does the rose curve $r = 4\cos(3\theta)$ have? | $3$ |
    | What is the greatest distance from the origin of a point on $r = 2 - 5\sin\theta$? | $7$ |

    Rose curves ``r = a cos(n theta)`` (petal count ``n`` if odd, ``2n`` if
    even; petal length ``|a|``), limacons ``r = a + b cos theta`` (farthest
    distance ``a + |b|``, nearest ``a - |b|`` or ``0`` with an inner loop),
    and ``r`` at a standard angle (rounded).
    """
    ask = random.choice(["petals", "petal_length", "max", "min", "value"])
    fn = random.choice(["sin", "cos"])
    s = Steps()

    if ask in ("petals", "petal_length") or (ask == "value" and random.random() < 0.5):
        a = random.choice([i for i in range(-max_coeff, max_coeff + 1) if abs(i) >= 2])
        n = random.randint(2, max_n)
        eq = rf"r = {_times(a, _polar_trig(fn, n))}"
        if ask == "petals":
            petals = n if n % 2 else 2 * n
            problem = f"How many petals does the rose curve ${eq}$ have?"
            solution = f"${petals}$"
            s.step(f"For a rose curve $r = a\\{fn}(n\\theta)$, there are $n$ petals "
                   f"when $n$ is odd and $2n$ petals when $n$ is even.")
            s.step(f"Here $n = {n}$ is {'odd' if n % 2 else 'even'}.",
                   rf"\text{{petals}} = {petals if n % 2 else f'2({n}) = {petals}'}")
            s.answer(solution)
            return problem, solution, s.done()
        if ask == "petal_length":
            problem = (f"How long is each petal of the rose curve ${eq}$ (the "
                       f"greatest distance from the origin)?")
            solution = f"${abs(a)}$"
            s.step(f"$\\{fn}(n\\theta)$ ranges from $-1$ to $1$, so $|r|$ is at "
                   f"most $|a|$, reached at each petal tip.")
            s.step("Take the absolute value of the coefficient.", rf"|{a}| = {abs(a)}")
            s.answer(solution)
            return problem, solution, s.done()
        num, den = random.choice(_UNIT_ANGLES)
        arg = n * num * 180 // den
        trig = _exact_trig(fn, arg)
        exact = _s_scale(trig, a)
        theta = _angle_latex(num, den)
        problem = (f"For the rose curve ${eq}$, find $r$ when $\\theta = {theta}$. "
                   f"Round your answer to the nearest thousandth if it is irrational.")
        solution = f"${_num(_s_float(exact))}$"
        s.step(f"Substitute $\\theta = {theta}$ and convert the angle "
               f"${n}\\theta$ to degrees.",
               rf"{n} \cdot {theta} \;\to\; {n} \cdot {_deg(num * 180 // den)} = {_deg(arg)}")
        s.step("Use the special-angle value.", _exact_trig_line(fn, arg % 360, _deg(arg)))
        s.step(f"Multiply by ${a}$.", rf"r = {a} \cdot {_wrap_tex(_s_tex(trig))} = {_approx(exact)}")
        s.answer(solution, lead=_lead(_s_rational(exact)))
        return problem, solution, s.done()

    a = random.randint(1, max_coeff)
    b = random.choice([i for i in range(-max_coeff, max_coeff + 1) if i != 0])
    eq = _limacon(a, b, fn)
    if ask == "max":
        problem = (f"What is the greatest distance from the origin of a point on "
                   f"the graph of ${eq}$?")
        solution = f"${a + abs(b)}$"
        s.step(f"$\\{fn}\\theta$ ranges from $-1$ to $1$, so $r$ ranges from "
               f"${a} - {abs(b)}$ to ${a} + {abs(b)}$.",
               rf"{a - abs(b)} \le r \le {a + abs(b)}")
        s.step("The distance from the origin is $|r|$, which is largest at the end "
               "of the range farthest from $0$.",
               rf"\max |r| = {a + abs(b)}")
    elif ask == "min":
        nearest = max(a - abs(b), 0)
        problem = (f"What is the least distance from the origin of a point on the "
                   f"graph of ${eq}$?")
        solution = f"${nearest}$"
        s.step(f"$\\{fn}\\theta$ ranges from $-1$ to $1$, so $r$ ranges from "
               f"${a} - {abs(b)}$ to ${a} + {abs(b)}$.",
               rf"{a - abs(b)} \le r \le {a + abs(b)}")
        if a > abs(b):
            s.step("$r$ is always positive, so the nearest point is at the smallest "
                   "value of $r$ (the graph is a dimpled or convex limaçon).",
                   rf"\min |r| = {a} - {abs(b)} = {nearest}")
        else:
            s.step("The range of $r$ includes $0$, so the graph passes through "
                   + ("the origin (a cardioid)." if a == abs(b)
                      else "the origin (a limaçon with an inner loop)."),
                   r"\min |r| = 0")
    else:
        num, den = random.choice(_UNIT_ANGLES)
        deg = num * 180 // den
        trig = _exact_trig(fn, deg)
        exact = _s_add({1: Fraction(a)}, _s_scale(trig, b))
        theta = _angle_latex(num, den)
        problem = (f"For ${eq}$, find $r$ when $\\theta = {theta}$. Round your "
                   f"answer to the nearest thousandth if it is irrational.")
        solution = f"${_num(_s_float(exact))}$"
        s.step(f"Substitute $\\theta = {theta}$, which is ${_deg(deg)}$.",
               _exact_trig_line(fn, deg, theta))
        s.step("Multiply and add.",
               rf"r = {a} {'+' if b > 0 else '-'} {abs(b)} \cdot {_wrap_tex(_s_tex(trig))} = {_approx(exact)}")
        s.answer(solution, lead=_lead(_s_rational(exact)))
        return problem, solution, s.done()
    s.answer(solution)
    return problem, solution, s.done()


# ---------------- AP 3.15 rates of change in polar functions ----------------

# The four quarter-turns, as (start, end) multiples of pi/2.
_QUARTERS = [(0, 1), (1, 2), (2, 3), (3, 4)]


@register
@with_variants
def pc_polar_rate_of_change(max_a=5, max_b=5):
    r"""Rates of Change in Polar Functions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | For $r = 3 + 2\sin\theta$, find the average rate of change of $r$ on $0 \leq \theta \leq \frac{\pi}{2}$. | $1.273$ |
    | For $r = 1 + 2\cos\theta$ on $\frac{\pi}{2} < \theta < \pi$, is the distance from the origin increasing or decreasing? | increasing |

    The average rate of change is ``(r(t2) - r(t1)) / (t2 - t1)``. On a quarter
    turn, ``sin``/``cos`` are monotonic, so if ``r`` keeps one sign the
    distance ``|r|`` grows exactly when ``r`` moves away from 0.
    """
    fn = random.choice(["sin", "cos"])
    a = random.randint(0, max_a)
    b = random.choice([i for i in range(-max_b, max_b + 1) if i != 0])
    eq = _limacon(a, b, fn) if a else rf"r = {_times(b, _polar_trig(fn))}"
    s = Steps()

    def r_exact(deg):
        return _s_add({1: Fraction(a)}, _s_scale(_exact_trig(fn, deg), b))

    if random.random() < 0.5:
        (n1, d1), (n2, d2) = sorted(random.sample(_UNIT_ANGLES, 2),
                                    key=lambda p: Fraction(*p))
        t1, t2 = _angle_latex(n1, d1), _angle_latex(n2, d2)
        g1, g2 = n1 * 180 // d1, n2 * 180 // d2
        r1, r2 = r_exact(g1), r_exact(g2)
        dt = Fraction(n2, d2) - Fraction(n1, d1)
        rate = (_s_float(r2) - _s_float(r1)) / (float(dt) * pi)
        problem = (f"For ${eq}$, find the average rate of change of $r$ with "
                   f"respect to $\\theta$ on the interval ${t1} \\leq \\theta \\leq "
                   f"{t2}$. {_ROUND_HINT}")
        solution = f"${_num(rate)}$"
        s.formula("The average rate of change of $r$ on $[\\theta_1, \\theta_2]$",
                  r"\frac{r(\theta_2) - r(\theta_1)}{\theta_2 - \theta_1}")
        s.step(f"Evaluate $r$ at both endpoints (${t1} = {_deg(g1)}$ and "
               f"${t2} = {_deg(g2)}$).",
               rf"r\left({t1}\right) = {_approx(r1)}, \quad r\left({t2}\right) = {_approx(r2)}")
        diff = _s_add(r2, _s_scale(r1, -1))
        s.step("Subtract the values of $r$ and the angles.",
               rf"r({t2}) - r({t1}) = {_approx(diff)}, \quad "
               rf"{t2} - {t1} = {_angle_latex(dt.numerator, dt.denominator)}")
        s.step("Divide.",
               rf"\frac{{{_s_tex(diff)}}}{{{_angle_latex(dt.numerator, dt.denominator)}}} "
               rf"\approx {_num(rate)}")
        s.answer(solution, lead=_ROUND_LEAD)
        return problem, solution, s.done()

    while True:
        q1, q2 = random.choice(_QUARTERS)
        r1, r2 = _s_float(r_exact(90 * q1)), _s_float(r_exact(90 * q2))
        if r1 * r2 >= 0:  # r keeps one sign inside the interval
            break
    f1, f2 = Fraction(q1, 2), Fraction(q2, 2)
    t1 = _angle_latex(f1.numerator, f1.denominator)
    t2 = _angle_latex(f2.numerator, f2.denominator)
    increasing = r2 * r2 > r1 * r1
    solution = "increasing" if increasing else "decreasing"
    problem = (f"For ${eq}$ on the interval ${t1} < \\theta < {t2}$, is the "
               f"distance between the point $(r, \\theta)$ and the origin "
               f"increasing or decreasing? Type increasing or decreasing.")
    s.step("The distance from the origin is $|r|$. It increases when $r$ is "
           "positive and increasing, or negative and decreasing.")
    s.step(f"$\\{fn}\\theta$ is monotonic on this quarter turn, so $r$ moves "
           f"steadily from one endpoint value to the other.",
           rf"r\left({t1}\right) = {_num(r1)}, \quad r\left({t2}\right) = {_num(r2)}")
    sign = "positive" if r1 + r2 > 0 else "negative"
    moving = "increasing" if r2 > r1 else "decreasing"
    s.step(f"So on the interval $r$ is {sign} and {moving}, which means $|r|$ is "
           f"{'getting larger' if increasing else 'getting smaller'}.")
    s.answer(solution)
    return problem, solution, s.done()
