"""Extra question types for the Calculus topics.

Variants for the generators in ``calculus`` and the library-override calculus
generators (``lib_algebra_extra_gen.power_rule_differentiation``,
``lib_seqstats_gen.definite_integral`` / ``power_rule_integration``). Each
attaches to its topic's dispatcher (see ``_variants.with_variants``); the
original question stays as the ``classic`` variant. Variants only use their own
topic's skill. See docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num
from ._steps import Steps, paren, tex_frac
from . import calculus as calc, lib_algebra_extra_gen, lib_seqstats_gen
from .calculus import _ftex, _poly_deriv, _poly_eval, _poly_tex
from .prealgebra_variants import _table

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."
_ROUND = "Round your answer to the nearest thousandth."
_ROUNDED = "Rounded to the nearest thousandth, the answer is"


def _nonzero(lo, hi):
    return random.choice([i for i in range(lo, hi + 1) if i != 0])


def _antideriv(poly):
    return {e + 1: Fraction(c, e + 1) for e, c in poly.items()}


def _integral(poly, a, b):
    F = _antideriv(poly)
    return _poly_eval(F, Fraction(b)) - _poly_eval(F, Fraction(a))


def _rand_poly(degree, lo=-5, hi=5):
    poly = {e: random.randint(lo, hi) for e in range(degree)}
    poly[degree] = _nonzero(lo, hi)
    return poly


# --- Limits ---------------------------------------------------------------------------------

@calc.calc_limit_rational.variant("hidden_parameter")
def _limit_hidden_parameter():
    """The limit exists only if the numerator vanishes at a; that pins down k first."""
    a, s = random.sample([n for n in range(-6, 7) if n != 0], 2)
    k, m = -(a + s), a * s
    problem = (
        f"For some constant $k$, $\\lim_{{x \\to {a}}} \\frac{{x^2 + kx {'+' if m >= 0 else '-'} {abs(m)}}}{{x - {paren(a)}}}$ "
        f"exists. What is the limit? {_FRACTION_HINT}"
    )
    solution = frac_from(a - s)
    s_ = Steps()
    s_.step(f"The denominator is $0$ at $x = {a}$, so the limit can exist only if the numerator is $0$ there too.",
            f"{a}^2 + {paren(a)}k + {paren(m)} = 0 \\Rightarrow k = {k}")
    s_.step("Factor and cancel.", f"\\frac{{(x - {paren(a)})(x - {paren(s)})}}{{x - {paren(a)}}} = x - {paren(s)}")
    s_.step(f"Substitute $x = {a}$.", f"{a} - {paren(s)} = {a - s}")
    s_.answer(solution)
    return problem, solution, s_.done()


@calc.calc_limit_rational.variant("at_infinity")
def _limit_at_infinity():
    """Limits at infinity: compare degrees and leading coefficients."""
    dn, dd = random.randint(1, 3), random.randint(1, 3)
    num_p, den_p = _rand_poly(dn), _rand_poly(dd)
    if dn > dd:
        dn, dd = dd, dn
        num_p, den_p = _rand_poly(dn), _rand_poly(dd)
    value = Fraction(num_p[dn], den_p[dd]) if dn == dd else Fraction(0)
    problem = (
        f"Evaluate $\\lim_{{x \\to \\infty}} \\frac{{{_poly_tex(num_p)}}}{{{_poly_tex(den_p)}}}$. {_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    if dn == dd:
        s.step("The degrees match, so the limit is the ratio of the leading coefficients.", rf"\frac{{{num_p[dn]}}}{{{den_p[dd]}}} = {_ftex(value)}")
    else:
        s.step("The denominator has the higher degree, so the fraction goes to $0$.")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_limit_conjugate.variant("at_infinity")
def _conjugate_at_infinity():
    r"""$\lim_{x\to\infty}(\sqrt{x^2 + ax} - x) = a/2$, via the conjugate."""
    a = _nonzero(-12, 12)
    b = random.randint(-9, 9)
    inside = f"x^2 {'+' if a > 0 else '-'} {abs(a)}x" + (f" {'+' if b >= 0 else '-'} {abs(b)}" if b else "")
    problem = rf"Evaluate $\lim_{{x \to \infty}} \left(\sqrt{{{inside}}} - x\right)$. {_FRACTION_HINT}"
    solution = frac_from(Fraction(a, 2))
    s = Steps()
    s.step("Multiply by the conjugate over itself.", rf"\frac{{({inside}) - x^2}}{{\sqrt{{{inside}}} + x}}")
    s.step("Divide the top and bottom by $x$; the square root tends to $x$.", rf"\frac{{{a}}}{{1 + 1}} = {_ftex(Fraction(a, 2))}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Derivatives -----------------------------------------------------------------------------

@calc.calc_derivative_polynomial.variant("horizontal_tangent")
def _derivative_horizontal_tangent():
    """Where the tangent is horizontal (f' = 0) for a quadratic, or where f' equals a value."""
    a, b, c = _nonzero(-5, 5), random.randint(-9, 9), random.randint(-9, 9)
    v = random.choice([0, random.randint(-9, 9)])
    x = Fraction(v - b, 2 * a)
    f = {2: a, 1: b, 0: c}
    if v == 0:
        problem = f"Where is the tangent to $f(x) = {_poly_tex(f)}$ horizontal? Give the x-value. {_FRACTION_HINT}"
    else:
        problem = f"For $f(x) = {_poly_tex(f)}$, at what $x$ is $f'(x) = {v}$? {_FRACTION_HINT}"
    solution = frac_from(x)
    s = Steps()
    s.step("Differentiate.", f"f'(x) = {_poly_tex(_poly_deriv(f))}")
    s.step(f"Set it equal to ${v}$ and solve.", f"{_poly_tex(_poly_deriv(f))} = {v} \\Rightarrow x = {_ftex(x)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.power_rule_differentiation.variant("slope_at_point")
def _power_rule_slope():
    """The slope of the tangent at a point."""
    f = _rand_poly(random.randint(2, 4))
    x0 = random.randint(-3, 3)
    slope = _poly_eval(_poly_deriv(f), x0)
    problem = f"What is the slope of the tangent to $f(x) = {_poly_tex(f)}$ at $x = {x0}$?"
    solution = f"{slope}"
    s = Steps()
    s.step("Differentiate with the power rule.", f"f'(x) = {_poly_tex(_poly_deriv(f))}")
    s.step(f"Evaluate at $x = {x0}$.", f"f'({x0}) = {slope}")
    s.answer(solution)
    return problem, solution, s.done()


def _rule_table():
    """An AP-style table of f, f', g, g' at x = 1..4 with g's values inside 1..4."""
    xs = [1, 2, 3, 4]
    f = [random.randint(-6, 6) for _ in xs]
    fp = [random.randint(-6, 6) for _ in xs]
    g = [random.randint(1, 4) for _ in xs]
    gp = [random.randint(-6, 6) for _ in xs]
    return xs, f, fp, g, gp


def _rule_table_tex(xs, f, fp, g, gp):
    rows = [("x", xs), ("f(x)", f), ("f'(x)", fp), ("g(x)", g), ("g'(x)", gp)]
    body = r" \\ \hline ".join(" & ".join([label] + [str(v) for v in vals]) for label, vals in rows)
    return r"\begin{array}{c|cccc} " + body + r" \end{array}"


@calc.calc_product_rule.variant("from_table")
def _product_from_table():
    """(fg)'(a) from a table of values."""
    xs, f, fp, g, gp = _rule_table()
    i = random.randrange(4)
    a = xs[i]
    value = fp[i] * g[i] + f[i] * gp[i]
    problem = f"Use the table. ${_rule_table_tex(xs, f, fp, g, gp)}$ If $h(x) = f(x)g(x)$, what is $h'({a})$?"
    solution = f"{value}"
    s = Steps()
    s.formula("The product rule", "h' = f'g + fg'")
    s.substitute(f"h'({a}) = ({fp[i]})({g[i]}) + ({f[i]})({gp[i]}) = {value}", text=f"Read the values at $x = {a}$.")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_quotient_rule.variant("from_table")
def _quotient_from_table():
    """(f/g)'(a) from a table of values."""
    xs, f, fp, g, gp = _rule_table()
    i = random.randrange(4)
    a = xs[i]
    value = Fraction(fp[i] * g[i] - f[i] * gp[i], g[i] ** 2)
    problem = (
        f"Use the table. ${_rule_table_tex(xs, f, fp, g, gp)}$ If $h(x) = \\frac{{f(x)}}{{g(x)}}$, what is $h'({a})$? {_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    s.formula("The quotient rule", r"h' = \frac{f'g - fg'}{g^2}")
    s.substitute(rf"h'({a}) = \frac{{({fp[i]})({g[i]}) - ({f[i]})({gp[i]})}}{{({g[i]})^2}} = {_ftex(value)}", text=f"Read the values at $x = {a}$.")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_chain_rule.variant("from_table")
def _chain_from_table():
    """(f o g)'(a) = f'(g(a)) g'(a) from a table."""
    xs, f, fp, g, gp = _rule_table()
    i = random.randrange(4)
    a = xs[i]
    inner = g[i]
    value = fp[inner - 1] * gp[i]
    problem = f"Use the table. ${_rule_table_tex(xs, f, fp, g, gp)}$ If $h(x) = f(g(x))$, what is $h'({a})$?"
    solution = f"{value}"
    s = Steps()
    s.formula("The chain rule", "h'(x) = f'(g(x))\\,g'(x)")
    s.step(f"Inside first: $g({a}) = {inner}$, so we need $f'({inner})$.", f"h'({a}) = f'({inner})\\,g'({a}) = ({fp[inner - 1]})({gp[i]}) = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_derivative_exp_log_trig.variant("critical_point")
def _exp_critical_point():
    """Where f(x) = a e^(bx) - cx has f' = 0."""
    a, b = random.randint(1, 5), random.randint(1, 3)
    c = random.randint(1, 30)
    x = math.log(c / (a * b)) / b
    problem = f"Where does $f(x) = {a if a > 1 else ''}e^{{{b if b > 1 else ''}x}} - {c}x$ have a horizontal tangent? {_ROUND}"
    solution = num(x)
    s = Steps()
    s.step("Differentiate and set the derivative to $0$.", rf"f'(x) = {a * b}e^{{{b if b > 1 else ''}x}} - {c} = 0")
    s.step("Solve with the natural log.", rf"x = \frac{{1}}{{{b}}}\ln\frac{{{c}}}{{{a * b}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@calc.calc_higher_order_derivative.variant("power_pattern")
def _higher_order_pattern():
    """The n-th derivative of x^n is n!; acceleration from a position polynomial."""
    if random.random() < 0.5:
        n = random.randint(3, 7)
        c = random.randint(1, 5)
        problem = f"What is the ${n}$th derivative of $f(x) = {c if c > 1 else ''}x^{{{n}}}$?"
        solution = f"{c * math.factorial(n)}"
        s = Steps()
        s.step(f"Each derivative lowers the power by one; after ${n}$ of them only the constant $n! \\cdot c$ is left.",
               f"{c} \\cdot {n}! = {c * math.factorial(n)}")
    else:
        pos = _rand_poly(3)
        t = random.randint(-3, 3)
        acc = _poly_eval(_poly_deriv(_poly_deriv(pos)), t)
        problem = f"A particle's position is $s(t) = {_poly_tex(pos, 't')}$. What is its acceleration at $t = {t}$?"
        solution = f"{acc}"
        s = Steps()
        s.step("Acceleration is the second derivative of position.", f"s''(t) = {_poly_tex(_poly_deriv(_poly_deriv(pos)), 't')}")
        s.step(f"Evaluate at $t = {t}$.", f"s''({t}) = {acc}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_tangent_line.variant("linear_approximation")
def _tangent_linear_approximation():
    """Estimate f(a + h) with the tangent line at a."""
    f = _rand_poly(random.randint(2, 3))
    a = random.randint(-3, 3)
    h = Fraction(random.choice([-3, -2, -1, 1, 2, 3]), random.choice([10, 100]))
    approx = _poly_eval(f, a) + _poly_eval(_poly_deriv(f), a) * h
    problem = (
        f"Use the tangent line to $f(x) = {_poly_tex(f)}$ at $x = {a}$ to approximate $f({num(a + h)})$. "
        "Round to the nearest thousandth if needed."
    )
    solution = num(approx)
    s = Steps()
    s.step("Find the value and slope at the point.", f"f({a}) = {_poly_eval(f, a)}, \\quad f'({a}) = {_poly_eval(_poly_deriv(f), a)}")
    s.step("Use $L(x) = f(a) + f'(a)(x - a)$.", f"L({num(a + h)}) = {_poly_eval(f, a)} + {paren(_poly_eval(_poly_deriv(f), a))}({num(h)}) = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_tangent_line.variant("through_origin")
def _tangent_through_origin():
    """For f(x) = x^2 + c, the tangent at x = a passes through the origin when a^2 = c."""
    a = random.randint(1, 9)
    c = a * a
    problem = f"The tangent line to $f(x) = x^2 + {c}$ at $x = a$ passes through the origin, with $a > 0$. What is $a$?"
    solution = f"{a}"
    s = Steps()
    s.step("The tangent at $a$ is $y = (a^2 + " + str(c) + ") + 2a(x - a)$.")
    s.step("Substitute $(0, 0)$.", f"0 = a^2 + {c} - 2a^2 \\Rightarrow a^2 = {c} \\Rightarrow a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Optimization, critical points, concavity ---------------------------------------------------

@calc.calc_extrema.variant("optimization")
def _extrema_optimization():
    """Classic optimization: an open box from a square sheet, or a fence against a wall."""
    s = Steps()
    if random.random() < 0.5:
        side = random.choice(range(6, 61, 6))
        x = Fraction(side, 6)
        vol = x * (side - 2 * x) ** 2
        problem = (
            f"Squares of side $x$ are cut from the corners of a ${side}$ cm square sheet, and the sides are folded up to make "
            "an open box. What cut size $x$ gives the largest volume, in cm?"
        )
        solution = num(x)
        s.step("The volume is $V(x) = x(" + str(side) + " - 2x)^2$. Differentiate and set to zero.",
               rf"V'(x) = ({side} - 2x)({side} - 6x) = 0")
        s.step(f"$x = {side // 2}$ makes a flat box, so the maximum is at the other critical point.", rf"x = \frac{{{side}}}{{6}} = {solution}")
    else:
        L = random.choice(range(20, 401, 4))
        problem = (
            f"A farmer has ${L}$ m of fence to enclose a rectangle against a straight wall (no fence on the wall side). What is "
            "the largest area that can be enclosed, in square meters?"
        )
        area = Fraction(L * L, 8)
        solution = num(area)
        s.step("With width $x$ (two sides) and length $" + str(L) + " - 2x$, the area is $A = x(" + str(L) + " - 2x)$.")
        s.step("Set $A'(x) = " + str(L) + " - 4x = 0$.", rf"x = {num(Fraction(L, 4))}, \quad A = {num(Fraction(L, 4))}({num(Fraction(L, 2))}) = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_extrema.variant("absolute_on_interval")
def _extrema_absolute():
    """Absolute max or min on a closed interval: check critical points and endpoints."""
    r1, r2 = sorted(random.sample(range(-4, 5), 2))
    a = random.choice([1, -1])
    # f' = 3a(x - r1)(x - r2): f = a(x^3 - 3/2(r1+r2)x^2 + 3 r1 r2 x) scaled by 2 to stay integral
    f = {3: 2 * a, 2: -3 * a * (r1 + r2), 1: 6 * a * r1 * r2, 0: random.randint(-9, 9)}
    lo, hi = r1 - random.randint(0, 2), r2 + random.randint(0, 2)
    candidates = sorted({lo, hi, r1, r2})
    values = {x: _poly_eval(f, x) for x in candidates}
    ask_max = random.random() < 0.5
    best = max(values.values()) if ask_max else min(values.values())
    problem = f"What is the absolute {'maximum' if ask_max else 'minimum'} value of $f(x) = {_poly_tex(f)}$ on $[{lo}, {hi}]$?"
    solution = f"{best}"
    s = Steps()
    s.step("Find the critical points.", f"f'(x) = {_poly_tex(_poly_deriv(f))} = 0 \\Rightarrow x = {r1}, {r2}")
    s.step("Compare $f$ at the critical points and the endpoints.", r",\ ".join(f"f({x}) = {v}" for x, v in values.items()))
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_extrema.variant("parameter_for_critical_point")
def _extrema_parameter():
    """For what k is x = c a critical point of x^3 + ax^2 + kx?"""
    c, a = _nonzero(-4, 4), random.randint(-6, 6)
    k = -(3 * c * c + 2 * a * c)
    problem = f"For what value of $k$ does $f(x) = x^3 {'+' if a >= 0 else '-'} {abs(a)}x^2 + kx$ have a critical point at $x = {c}$?"
    solution = f"{k}"
    s = Steps()
    s.step("A critical point has $f'(c) = 0$.", f"f'(x) = 3x^2 + {2 * a}x + k \\Rightarrow 3({c})^2 + {2 * a}({c}) + k = 0")
    s.step("Solve for $k$.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_inflection_point.variant("parameter")
def _inflection_parameter():
    """For what k does x^3 + kx^2 + ... inflect at x = c? f'' = 6x + 2k."""
    c = _nonzero(-6, 6)
    k = -3 * c
    b, d = random.randint(-9, 9), random.randint(-9, 9)
    problem = (
        f"For what value of $k$ does $f(x) = x^3 + kx^2 {'+' if b >= 0 else '-'} {abs(b)}x {'+' if d >= 0 else '-'} {abs(d)}$ "
        f"have an inflection point at $x = {c}$?"
    )
    solution = f"{k}"
    s = Steps()
    s.step("At an inflection point of a cubic, $f'' = 0$.", f"f''(x) = 6x + 2k \\Rightarrow 6({c}) + 2k = 0")
    s.step("Solve.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_inflection_point.variant("y_coordinate")
def _inflection_y():
    """The y-coordinate of a cubic's inflection point."""
    a = _nonzero(-3, 3)
    c = _nonzero(-3, 3)
    b = -3 * a * c
    f = {3: a, 2: b, 1: random.randint(-9, 9), 0: random.randint(-9, 9)}
    y = _poly_eval(f, c)
    problem = f"What is the y-coordinate of the inflection point of $f(x) = {_poly_tex(f)}$?"
    solution = f"{y}"
    s = Steps()
    s.step("Set the second derivative to $0$.", f"f''(x) = {6 * a}x + {2 * b} = 0 \\Rightarrow x = {c}")
    s.step("Evaluate $f$ there.", f"f({c}) = {y}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_concavity_interval.variant("concave_down")
def _concavity_down():
    """The interval where a cubic is concave down."""
    a = _nonzero(-3, 3)
    c = _nonzero(-6, 6)                      # the inflection point
    f = {3: a, 2: -3 * a * c, 1: random.randint(-9, 9), 0: random.randint(-9, 9)}
    infl = Fraction(c)
    down = f"(-inf, {frac_from(infl)})" if a > 0 else f"({frac_from(infl)}, inf)"
    problem = f"On what interval is $f(x) = {_poly_tex(f)}$ concave down? Answer as an interval like (a, inf) or (-inf, a)."
    solution = down
    s = Steps()
    s.step("Find where $f''$ is negative.", f"f''(x) = {6 * a}x + {2 * f[2]}, \\quad f''(x) = 0 \\text{{ at }} x = {_ftex(infl)}")
    s.step(f"$f''$ has slope ${6 * a}$, so it is negative {'left' if a > 0 else 'right'} of that point.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Integrals ------------------------------------------------------------------------------------

def _integral_properties():
    """Combine known integrals using linearity and additivity."""
    a, b = sorted(random.sample(range(-5, 10), 2))
    c = random.randint(b + 1, b + 8)
    P, Q = random.randint(-20, 20), random.randint(-20, 20)
    m, n = _nonzero(-5, 5), random.randint(-5, 5)
    value = m * (P - Q) + n * (c - b)
    problem = (
        f"$\\int_{{{a}}}^{{{c}}} f(x)\\,dx = {P}$ and $\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {Q}$. What is "
        f"$\\int_{{{b}}}^{{{c}}} \\left({m if m != 1 else ''}f(x) {'+' if n >= 0 else '-'} {abs(n)}\\right)dx$?"
    )
    solution = f"{value}"
    s = Steps()
    s.step("Split the interval: the integral over the right piece is the difference.", rf"\int_{{{b}}}^{{{c}}} f = {P} - {paren(Q)} = {P - Q}")
    s.step("Integrals are linear; a constant integrates to itself times the length.",
           rf"{m}({P - Q}) + {paren(n)}({c} - {paren(b)}) = {value}")
    s.answer(solution)
    return problem, solution, s.done()


calc.calc_definite_integral_poly.variant("properties")(_integral_properties)
lib_seqstats_gen.definite_integral.variant("properties")(_integral_properties)


@calc.calc_definite_integral_poly.variant("upper_limit")
def _integral_upper_limit():
    r"""Reverse: $\int_0^k cx\,dx = A$, find k > 0."""
    c, k = random.randint(1, 6), random.randint(1, 10)
    area = Fraction(c * k * k, 2)
    problem = f"For what $k > 0$ is $\\int_0^k {c if c > 1 else ''}x\\,dx = {_ftex(area)}$?"
    solution = f"{k}"
    s = Steps()
    s.step("Integrate.", rf"\left[\frac{{{c}x^2}}{{2}}\right]_0^k = \frac{{{c}k^2}}{{2}} = {_ftex(area)}")
    s.step("Solve.", f"k^2 = {k * k} \\Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_definite_integral_poly.variant("area_from_graph")
def _integral_from_graph():
    """A definite integral of a piecewise-linear graph, from its vertices (signed area)."""
    xs = sorted(random.sample(range(-4, 10), 4))
    ys = [random.randint(-6, 6) for _ in xs]
    area = sum(Fraction((ys[i] + ys[i + 1]) * (xs[i + 1] - xs[i]), 2) for i in range(3))
    pts = ", ".join(f"$({x}, {y})$" for x, y in zip(xs, ys))
    problem = (
        f"The graph of $f$ is made of straight segments joining {pts}. What is $\\int_{{{xs[0]}}}^{{{xs[-1]}}} f(x)\\,dx$? "
        f"(Area below the x-axis counts as negative.) {_FRACTION_HINT}"
    )
    solution = frac_from(area)
    s = Steps()
    s.step("Each segment contributes a trapezoid's signed area: the average height times the width.",
           " + ".join(rf"\frac{{({ys[i]}) + ({ys[i + 1]})}}{{2}}({xs[i + 1] - xs[i]})" for i in range(3)))
    s.step("Add them.", _ftex(area))
    s.answer(solution)
    return problem, solution, s.done()


def _initial_value():
    """An antiderivative with an initial condition: F' = f, F(0) = c, find F(x0)."""
    f = _rand_poly(random.randint(1, 3))
    c = random.randint(-9, 9)
    x0 = random.randint(-3, 3)
    F = _antideriv(f)
    value = _poly_eval(F, Fraction(x0)) + c
    problem = f"If $F'(x) = {_poly_tex(f)}$ and $F(0) = {c}$, what is $F({x0})$? {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step("Antidifferentiate; the constant is $F(0)$.", f"F(x) = {_poly_tex(F)} + {paren(c)}")
    s.step(f"Evaluate at $x = {x0}$.", f"F({x0}) = {_ftex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


calc.calc_indefinite_integral_poly.variant("initial_value")(_initial_value)
lib_seqstats_gen.power_rule_integration.variant("initial_value")(_initial_value)


@calc.calc_usub_integral.variant("new_limits")
def _usub_new_limits():
    """After u = ax + b, the limits change: the new upper limit."""
    a, b = _nonzero(-5, 5), random.randint(-9, 9)
    p, q = sorted(random.sample(range(-4, 6), 2))
    n = random.randint(2, 5)
    which = random.choice(["upper", "lower"])
    problem = (
        f"In $\\int_{{{p}}}^{{{q}}} ({a}x {'+' if b >= 0 else '-'} {abs(b)})^{{{n}}}\\,dx$, substitute $u = {a}x "
        f"{'+' if b >= 0 else '-'} {abs(b)}$. What is the new {which} limit of integration?"
    )
    value = a * (q if which == "upper" else p) + b
    solution = f"{value}"
    s = Steps()
    s.step(f"The {which} limit $x = {q if which == 'upper' else p}$ becomes", f"u = {a}({q if which == 'upper' else p}) + {paren(b)} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_area_between_curves.variant("find_intersections")
def _area_find_intersections():
    """The bounds aren't given: find where the curves meet first."""
    s = Steps()
    if random.random() < 0.5:
        k = random.randint(1, 8)
        area = Fraction(k ** 3, 6)
        problem = f"Find the area of the region enclosed by $y = x^2$ and $y = {k}x$. {_FRACTION_HINT}"
        s.step("Find where they meet.", f"x^2 = {k}x \\Rightarrow x = 0, {k}")
        s.step("Integrate the top minus the bottom.", rf"\int_0^{{{k}}} ({k}x - x^2)\,dx = {_ftex(area)}")
    else:
        t = random.randint(1, 4)
        c = 2 * t * t
        area = Fraction(8 * t ** 3, 3)
        problem = f"Find the area of the region enclosed by $y = x^2$ and $y = {c} - x^2$. {_FRACTION_HINT}"
        s.step("Find where they meet.", f"x^2 = {c} - x^2 \\Rightarrow x = \\pm {t}")
        s.step("Integrate the top minus the bottom.", rf"\int_{{-{t}}}^{{{t}}} ({c} - 2x^2)\,dx = {_ftex(area)}")
    solution = frac_from(area)
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_average_value.variant("where_attained")
def _average_where_attained():
    """Reverse: c in [0, b] where f(c) = the average value, for f(x) = x^2."""
    b = random.randint(1, 12)
    c = b / math.sqrt(3)
    problem = f"$f(x) = x^2$ on $[0, {b}]$. At what $c$ in $[0, {b}]$ does $f(c)$ equal the average value of $f$? {_ROUND}"
    solution = num(c)
    s = Steps()
    s.step("Find the average value.", rf"\frac{{1}}{{{b}}}\int_0^{{{b}}} x^2\,dx = \frac{{{b * b}}}{{3}}")
    s.step("Solve $c^2 = $ the average.", rf"c = \sqrt{{\frac{{{b * b}}}{{3}}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@calc.calc_average_value.variant("temperature")
def _average_temperature():
    """Average temperature from a quadratic model over a time window."""
    a, b = random.randint(40, 70), random.randint(1, 6)
    c = Fraction(random.randint(1, 4), 10)
    h = random.randint(4, 12)
    T = {0: a, 1: b, 2: -c}
    avg = _integral(T, 0, h) / h
    problem = (
        f"The temperature $t$ hours after 6 a.m. is $T(t) = {a} + {b}t - {num(c)}t^2$ degrees. What is the average temperature "
        f"over the first ${h}$ hours? Round to the nearest thousandth if needed."
    )
    solution = num(avg)
    s = Steps()
    s.formula("The average value", rf"\frac{{1}}{{{h}}}\int_0^{{{h}}} T(t)\,dt")
    s.step("Integrate and divide.", rf"\frac{{1}}{{{h}}}\left[{a}t + \frac{{{b}}}{{2}}t^2 - \frac{{{num(c)}}}{{3}}t^3\right]_0^{{{h}}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_riemann_sum.variant("from_table")
def _riemann_from_table():
    """AP-style: a left or right sum from a table with unequal widths."""
    xs = sorted(random.sample(range(0, 16), 5))
    ys = [random.randint(0, 20) for _ in xs]
    left = random.random() < 0.5
    total = sum((xs[i + 1] - xs[i]) * (ys[i] if left else ys[i + 1]) for i in range(4))
    problem = (
        f"The table gives values of $f$. ${_table('x', xs, 'f(x)', ys)}$ Use a {'left' if left else 'right'} Riemann sum with the "
        f"four subintervals shown to estimate $\\int_{{{xs[0]}}}^{{{xs[-1]}}} f(x)\\,dx$."
    )
    solution = f"{total}"
    s = Steps()
    s.step(f"Multiply each width by the {'left' if left else 'right'} endpoint's value and add.",
           " + ".join(f"{xs[i + 1] - xs[i]}({ys[i] if left else ys[i + 1]})" for i in range(4)) + f" = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_riemann_sum.variant("over_or_under")
def _riemann_over_under():
    """Left sums underestimate an increasing function; right sums overestimate it."""
    inc = random.random() < 0.5
    left = random.random() < 0.5
    over = (inc and not left) or (not inc and left)
    problem = (
        f"$f$ is {'increasing' if inc else 'decreasing'} on $[a, b]$. Is a {'left' if left else 'right'} Riemann sum an "
        "overestimate or an underestimate of $\\int_a^b f(x)\\,dx$? Answer overestimate or underestimate."
    )
    answer = "overestimate" if over else "underestimate"
    s = Steps()
    s.step(f"On each subinterval the {'left' if left else 'right'} endpoint is the {'lowest' if (inc == left) else 'highest'} "
           "point, so each rectangle is " + ("above" if over else "below") + " the curve.")
    s.answer(answer)
    return problem, answer, s.done()


@calc.calc_trapezoidal_rule.variant("from_table")
def _trapezoid_from_table():
    """The trapezoidal rule from a table with unequal widths."""
    xs = sorted(random.sample(range(0, 16), 5))
    ys = [random.randint(0, 20) for _ in xs]
    total = sum(Fraction((ys[i] + ys[i + 1]) * (xs[i + 1] - xs[i]), 2) for i in range(4))
    problem = (
        f"The table gives values of $f$. ${_table('x', xs, 'f(x)', ys)}$ Use the trapezoidal rule with the four subintervals "
        f"shown to estimate $\\int_{{{xs[0]}}}^{{{xs[-1]}}} f(x)\\,dx$. Round to the nearest thousandth if needed."
    )
    solution = num(total)
    s = Steps()
    s.step("Each trapezoid is the average of its two heights times its width.",
           " + ".join(rf"\frac{{{ys[i]} + {ys[i + 1]}}}{{2}}({xs[i + 1] - xs[i]})" for i in range(4)) + f" = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_volume_revolution.variant("square_cross_sections")
def _volume_square_sections():
    """A solid whose cross sections are squares: V = integral of side^2."""
    m, k = random.randint(1, 4), random.randint(1, 6)
    f = {1: m}
    vol = _integral({2: m * m}, 0, k)
    problem = (
        f"The base of a solid is the region under $y = {m if m > 1 else ''}x$ from $x = 0$ to $x = {k}$. Cross sections perpendicular "
        f"to the x-axis are squares with one side in the base. Find the volume. {_FRACTION_HINT}"
    )
    solution = frac_from(vol)
    s = Steps()
    s.step("Each square's side is the height of the region, so its area is $(" + _poly_tex(f) + ")^2$.")
    s.step("Integrate the areas.", rf"\int_0^{{{k}}} {m * m}x^2\,dx = {_ftex(vol)}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_volume_revolution.variant("shells_about_y")
def _volume_shells():
    """Revolve y = ax - x^2 (between its roots) about the y-axis: shells."""
    a = random.randint(1, 6)
    k = _integral({2: a, 3: -1}, 0, a) * 2   # V = 2 pi * integral x f(x) dx = k pi
    problem = (
        f"The region between $y = {a}x - x^2$ and the x-axis is revolved about the y-axis. The volume has the form k*pi; give the "
        "value of k as a fraction a/b or an integer."
    )
    solution = frac_from(k)
    s = Steps()
    s.step("Use shells: radius $x$, height $" + f"{a}x - x^2" + "$, from $x = 0$ to $x = " + str(a) + "$.",
           rf"V = 2\pi\int_0^{{{a}}} x({a}x - x^2)\,dx")
    s.step("Integrate.", rf"V = {_ftex(k)}\pi")
    s.answer(solution)
    return problem, solution, s.done()


# --- Motion, related rates, differential equations ----------------------------------------------

@calc.calc_particle_motion.variant("total_distance")
def _motion_total_distance():
    """Total distance vs displacement when the velocity changes sign."""
    a = random.randint(1, 6)
    b = random.randint(a + 1, a + 5)
    v = {2: 1, 1: -a}      # v(t) = t^2 - a t, negative on (0, a)
    disp = _integral(v, 0, b)
    dist = -_integral(v, 0, a) + _integral(v, a, b)
    ask_distance = random.random() < 0.5
    problem = (
        f"A particle's velocity is $v(t) = t^2 - {a}t$ for $0 \\leq t \\leq {b}$. What is its total "
        f"{'distance traveled' if ask_distance else 'displacement'}? {_FRACTION_HINT}"
    )
    solution = frac_from(dist if ask_distance else disp)
    s = Steps()
    if ask_distance:
        s.step(f"The velocity changes sign at $t = {a}$, so integrate the speed in two pieces.",
               rf"\left|\int_0^{{{a}}} v\,dt\right| + \int_{{{a}}}^{{{b}}} v\,dt = {_ftex(-_integral(v, 0, a))} + {_ftex(_integral(v, a, b))} = {_ftex(dist)}")
    else:
        s.step("Displacement is the plain integral of velocity.", rf"\int_0^{{{b}}} (t^2 - {a}t)\,dt = {_ftex(disp)}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_particle_motion.variant("speeding_up")
def _motion_speeding_up():
    """Speeding up when velocity and acceleration have the same sign."""
    pos = _rand_poly(3)
    t = random.randint(-3, 3)
    v = _poly_eval(_poly_deriv(pos), t)
    acc = _poly_eval(_poly_deriv(_poly_deriv(pos)), t)
    while v == 0 or acc == 0:
        pos = _rand_poly(3)
        v = _poly_eval(_poly_deriv(pos), t)
        acc = _poly_eval(_poly_deriv(_poly_deriv(pos)), t)
    answer = "yes" if v * acc > 0 else "no"
    problem = f"A particle's position is $s(t) = {_poly_tex(pos, 't')}$. Is it speeding up at $t = {t}$? Answer yes or no."
    s = Steps()
    s.step("Find velocity and acceleration there.", f"v({t}) = {v}, \\quad a({t}) = {acc}")
    s.step("It speeds up exactly when they have the same sign.")
    s.answer(answer)
    return problem, answer, s.done()


@calc.calc_related_rates.variant("new_contexts")
def _related_rates_contexts():
    """Related rates: a filling cone, a moving shadow, or an inflating balloon."""
    kind = random.choice(["cone", "shadow", "balloon"])
    s = Steps()
    if kind == "cone":
        ratio = random.randint(1, 4)          # r = h / ratio
        rate = random.randint(1, 20)          # dV/dt
        h = random.randint(1, 12)
        # V = pi/3 (h/ratio)^2 h = pi h^3 / (3 ratio^2)  =>  dV/dt = pi h^2/ratio^2 dh/dt
        dhdt = Fraction(rate * ratio * ratio, h * h)
        shape = "the radius of the water's surface equals its depth" if ratio == 1 else \
            f"the water's depth is always ${ratio}$ times the radius of its surface"
        problem = (
            f"Water pours into an upside-down cone at ${rate}$ cubic ft/min, and {shape}. How fast is the water level rising "
            f"when it is ${h}$ ft deep? The answer has the form k/pi ft/min; give k as a fraction a/b or an integer."
        )
        solution = frac_from(dhdt)
        s.step("Write the volume in terms of $h$ alone.", rf"V = \frac{{\pi}}{{3}}\left(\frac{{h}}{{{ratio}}}\right)^2 h = \frac{{\pi h^3}}{{{3 * ratio * ratio}}}")
        s.step("Differentiate and solve for $dh/dt$.", rf"{rate} = \frac{{\pi ({h})^2}}{{{ratio * ratio}}}\frac{{dh}}{{dt}} \Rightarrow \frac{{dh}}{{dt}} = \frac{{{_ftex(dhdt)}}}{{\pi}}")
    elif kind == "shadow":
        H, p = random.randint(12, 25), random.randint(5, 6)
        v = random.randint(2, 8)
        # similar triangles: shadow s, distance x: s/p = (x + s)/H => s = p x/(H - p)
        dsdt = Fraction(p * v, H - p)
        problem = (
            f"A ${p}$ ft tall person walks away from a ${H}$ ft street light at ${v}$ ft/s. How fast is the length of their "
            f"shadow growing, in ft/s? {_FRACTION_HINT}"
        )
        solution = frac_from(dsdt)
        s.step("Similar triangles relate the shadow $s$ to the distance $x$ from the light.", rf"\frac{{s}}{{{p}}} = \frac{{x + s}}{{{H}}} \Rightarrow s = \frac{{{p}}}{{{H - p}}}x")
        s.step("Differentiate.", rf"\frac{{ds}}{{dt}} = \frac{{{p}}}{{{H - p}}}({v}) = {_ftex(dsdt)}")
    else:
        rate = random.randint(1, 50)          # dV/dt in pi units? keep plain
        r = random.randint(1, 10)
        drdt = Fraction(rate, 4 * r * r)
        problem = (
            f"A spherical balloon is inflated at ${rate}$ cubic cm/s. How fast is its radius growing when the radius is ${r}$ cm? "
            "The answer has the form k/pi cm/s; give k as a fraction a/b or an integer."
        )
        solution = frac_from(drdt)
        s.step("Differentiate the volume of a sphere.", rf"\frac{{dV}}{{dt}} = 4\pi r^2\frac{{dr}}{{dt}}")
        s.step("Solve.", rf"\frac{{dr}}{{dt}} = \frac{{{rate}}}{{4\pi({r})^2}} = \frac{{{_ftex(drdt)}}}{{\pi}}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_mvt_find_c.variant("rolle")
def _mvt_rolle():
    """Rolle's theorem on a quadratic with equal endpoint values: c is the midpoint."""
    a, b = sorted(random.sample(range(-9, 10), 2))
    k = _nonzero(-4, 4)
    problem = (
        f"$f(x) = {k if k not in (1, -1) else ('-' if k < 0 else '')}(x - {paren(a)})(x - {paren(b)})$ on $[{a}, {b}]$ satisfies "
        f"Rolle's theorem. What value $c$ does it guarantee? {_FRACTION_HINT}"
    )
    c = Fraction(a + b, 2)
    solution = frac_from(c)
    s = Steps()
    s.step(f"$f({a}) = f({b}) = 0$, so some $c$ has $f'(c) = 0$.", f"f'(x) = {k}(2x - {a + b}) = 0")
    s.step("Solve.", rf"c = \frac{{{a + b}}}{{2}} = {_ftex(c)}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_mvt_find_c.variant("guaranteed_rate")
def _mvt_guaranteed_rate():
    """From a table: the derivative value the MVT guarantees on an interval."""
    x1, x2 = sorted(random.sample(range(0, 12), 2))
    y1, y2 = random.randint(-20, 20), random.randint(-20, 20)
    rate = Fraction(y2 - y1, x2 - x1)
    problem = (
        f"$f$ is differentiable everywhere, with $f({x1}) = {y1}$ and $f({x2}) = {y2}$. What value must $f'(c)$ equal for some $c$ "
        f"in $({x1}, {x2})$? {_FRACTION_HINT}"
    )
    solution = frac_from(rate)
    s = Steps()
    s.step("The mean value theorem guarantees the derivative equals the average rate of change somewhere.",
           rf"\frac{{{y2} - {paren(y1)}}}{{{x2} - {x1}}} = {_ftex(rate)}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_separable_ode.variant("growth_constant")
def _ode_growth_constant():
    """Reverse: k in y = y0 e^(kt) from two measurements."""
    y0 = random.choice(range(100, 1001, 100))
    t = random.randint(1, 10)
    y1 = Fraction(random.randint(int(y0 * 1.1), int(y0 * 4)))
    k = math.log(float(y1) / y0) / t
    problem = (
        f"A population follows $\\frac{{dP}}{{dt}} = kP$. It starts at ${y0}$ and is ${num(y1)}$ after ${t}$ years. What is $k$? {_ROUND}"
    )
    solution = num(k)
    s = Steps()
    s.step("The solution is $P = P_0e^{kt}$.", rf"{num(y1)} = {y0}e^{{{t}k}}")
    s.step("Solve with the natural log.", rf"k = \frac{{1}}{{{t}}}\ln\frac{{{num(y1)}}}{{{y0}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@calc.calc_separable_ode.variant("cooling")
def _ode_cooling():
    """Newton's law of cooling: when does the object reach a temperature?"""
    room = random.randint(15, 25)
    T0 = random.randint(60, 100)
    k = Fraction(random.randint(5, 30), 100)
    target = random.randint(room + 5, T0 - 5)
    t = math.log((T0 - room) / (target - room)) / float(k)
    problem = (
        f"Tea at ${T0}^\\circ$C cools in a ${room}^\\circ$C room, following $T(t) = {room} + {T0 - room}e^{{-{num(k)}t}}$ ($t$ in "
        f"minutes). When does it reach ${target}^\\circ$C? {_ROUND}"
    )
    solution = num(t)
    s = Steps()
    s.step("Set $T(t)$ equal to the target and isolate the exponential.", rf"e^{{-{num(k)}t}} = \frac{{{target - room}}}{{{T0 - room}}}")
    s.step("Take the natural log.", rf"t = \frac{{1}}{{{num(k)}}}\ln\frac{{{T0 - room}}}{{{target - room}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


# --- L'Hopital, limit definition, parts, Taylor ----------------------------------------------------

@calc.calc_lhopital.variant("parameter")
def _lhopital_parameter():
    r"""For what k is $\lim_{x\to0}\frac{\sin(kx)}{cx} = L$?"""
    c = random.randint(1, 6)
    k = _nonzero(-9, 9)
    L = Fraction(k, c)
    problem = f"For what value of $k$ does $\\lim_{{x \\to 0}} \\frac{{\\sin(kx)}}{{{c if c > 1 else ''}x}} = {_ftex(L)}$?"
    solution = f"{k}"
    s = Steps()
    s.step("L'Hopital: differentiate the top and the bottom.", rf"\lim_{{x \to 0}} \frac{{k\cos(kx)}}{{{c}}} = \frac{{k}}{{{c}}}")
    s.step("Set it equal and solve.", rf"\frac{{k}}{{{c}}} = {_ftex(L)} \Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_lhopital.variant("infinity_over_infinity")
def _lhopital_infinity():
    r"""$\lim_{x\to\infty}\frac{ax + \ln x}{bx} = a/b$."""
    a, b = random.randint(1, 9), random.randint(1, 9)
    problem = f"Evaluate $\\lim_{{x \\to \\infty}} \\frac{{{a if a > 1 else ''}x + \\ln x}}{{{b if b > 1 else ''}x}}$. {_FRACTION_HINT}"
    solution = frac_from(Fraction(a, b))
    s = Steps()
    s.step("It's $\\infty/\\infty$, so differentiate the top and the bottom.", rf"\frac{{{a} + \frac{{1}}{{x}}}}{{{b}}}")
    s.step(r"As $x \to \infty$, $\frac{1}{x} \to 0$.", rf"\frac{{{a}}}{{{b}}} = {_ftex(Fraction(a, b))}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_limit_definition_derivative.variant("recognize_limit")
def _limit_definition_recognize():
    r"""Recognize $\lim_{h\to0}\frac{(a+h)^n - a^n}{h}$ as a derivative."""
    a, n = _nonzero(-4, 5), random.randint(2, 5)
    problem = f"Evaluate $\\lim_{{h \\to 0}} \\frac{{({a} + h)^{{{n}}} - {paren(a)}^{{{n}}}}}{{h}}$."
    solution = f"{n * a ** (n - 1)}"
    s = Steps()
    s.step(f"This is the definition of the derivative of $x^{{{n}}}$ at $x = {a}$.", rf"\frac{{d}}{{dx}}x^{{{n}}} = {n}x^{{{n - 1}}}")
    s.step("Evaluate.", f"{n}({a})^{{{n - 1}}} = {n * a ** (n - 1)}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_integration_by_parts.variant("twice")
def _parts_twice():
    r"""$\int_0^b x^2e^x\,dx = e^b(b^2 - 2b + 2) - 2$, by parts twice."""
    b = random.choice([1, 2, 3])
    value = math.exp(b) * (b * b - 2 * b + 2) - 2
    problem = f"Evaluate $\\int_0^{{{b}}} x^2 e^x\\,dx$. {_ROUND}"
    solution = num(value)
    s = Steps()
    s.step("Integrate by parts twice (tabular method).", r"\int x^2e^x\,dx = e^x(x^2 - 2x + 2) + C")
    s.step("Evaluate from $0$ to $" + str(b) + "$.", rf"e^{{{b}}}({b * b - 2 * b + 2}) - 2 \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


_TAYLOR = {"e^x": lambda n: Fraction(1, math.factorial(n)),
           "\\sin x": lambda n: Fraction((-1) ** ((n - 1) // 2), math.factorial(n)) if n % 2 else Fraction(0),
           "\\cos x": lambda n: Fraction((-1) ** (n // 2), math.factorial(n)) if n % 2 == 0 else Fraction(0)}


@calc.calc_taylor_coefficient.variant("derivative_from_coefficient")
def _taylor_derivative():
    """Reverse: f^(n)(0) = n! times the n-th Maclaurin coefficient."""
    n = random.randint(2, 6)
    c = Fraction(random.randint(-9, 9), random.choice([1, 2, 3, 4, 6]))
    value = c * math.factorial(n)
    problem = f"The coefficient of $x^{{{n}}}$ in the Maclaurin series of $f$ is ${_ftex(c)}$. What is $f^{{({n})}}(0)$? {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step("The coefficient of $x^n$ is $\\frac{f^{(n)}(0)}{n!}$.", rf"f^{{({n})}}(0) = {n}! \times {_ftex(c)} = {_ftex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_taylor_coefficient.variant("substitution")
def _taylor_substitution():
    """A coefficient of f(kx) by substituting into a known series."""
    func = random.choice(list(_TAYLOR))
    k = _nonzero(-3, 3)
    n = random.randint(1, 5)
    value = _TAYLOR[func](n) * Fraction(k) ** n
    shown = f"e^{{{k}x}}" if func == "e^x" else f"{func.split()[0]}({k}x)"
    problem = f"What is the coefficient of $x^{{{n}}}$ in the Maclaurin series of ${shown}$? {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step(f"Take the known series for ${func}$ and replace $x$ with ${k}x$: the $x^{{{n}}}$ term picks up $({k})^{{{n}}}$.",
           rf"{_ftex(_TAYLOR[func](n))} \times ({k})^{{{n}}} = {_ftex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@calc.calc_taylor_coefficient.variant("approximate")
def _taylor_approximate():
    """Approximate e^h with the degree-2 Maclaurin polynomial."""
    h = Fraction(random.randint(-30, 30), 100)
    approx = 1 + h + h * h / 2
    problem = f"Use the degree-2 Maclaurin polynomial of $e^x$ to approximate $e^{{{num(h)}}}$. {_ROUND}"
    solution = num(approx)
    s = Steps()
    s.step("The polynomial is $1 + x + \\frac{x^2}{2}$.", rf"1 + {paren(num(h))} + \frac{{({num(h)})^2}}{{2}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@calc.calc_implicit_differentiation.variant("find_the_point")
def _implicit_find_point():
    """dy/dx on a circle at the point with a given x (y > 0 must be found first)."""
    p, q, r = random.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)])
    x, y = random.choice([(p, q), (q, p), (-p, q), (-q, p)])
    slope = Fraction(-x, y)
    problem = f"Find $dy/dx$ for $x^2 + y^2 = {r * r}$ at the point where $x = {x}$ and $y > 0$. {_FRACTION_HINT}"
    solution = frac_from(slope)
    s = Steps()
    s.step("First find $y$.", f"y = \\sqrt{{{r * r} - {x * x}}} = {y}")
    s.step("Differentiate implicitly.", rf"2x + 2y\frac{{dy}}{{dx}} = 0 \Rightarrow \frac{{dy}}{{dx}} = -\frac{{x}}{{y}} = {_ftex(slope)}")
    s.answer(solution)
    return problem, solution, s.done()
