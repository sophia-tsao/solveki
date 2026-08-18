"""Solveki-local generators for Georgia "Algebra: Concepts & Connections".

These fill computable gaps in the standard course. Every generator here is
zero-required-arg, decorated with ``@register``, and returns a ``(problem,
solution)`` pair of strings with math wrapped in ``$...$``. Answers are kept
clean: integers, decimals to at most three places, or reduced ``a/b`` fractions.

Import this module for its ``@register`` side effects (see ``__init__`` /
tests). ``random`` is used directly and never seeded here.
"""
import random
from fractions import Fraction

from ._registry import register
from ._format import frac_from as _fmt_frac, num, pair

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."


def _signed(n):
    """Render a signed additive term: ``+3``, ``-3``, or ``''`` for zero."""
    if n == 0:
        return ""
    return f"+{n}" if n > 0 else f"-{abs(n)}"


def _quadratic(a, b, c):
    """Render ``ax^2+bx+c`` (a != 0), omitting zero and unit coefficients."""
    if a == 1:
        parts = ["x^2"]
    elif a == -1:
        parts = ["-x^2"]
    else:
        parts = [f"{a}x^2"]
    if b != 0:
        sign = "+" if b > 0 else "-"
        mag = abs(b)
        parts.append(f"{sign}{'' if mag == 1 else mag}x")
    if c != 0:
        sign = "+" if c > 0 else "-"
        parts.append(f"{sign}{abs(c)}")
    return "".join(parts)


@register
def alg1_absolute_value_equation(max_a=6, min_b=-10, max_b=10, max_c=15):
    r"""Absolute Value Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve for $x$: $|2x+3|=7$ | $x = -5$ or $x = 2$ |
    """
    a = random.randint(1, max_a)
    b = random.choice([n for n in range(min_b, max_b + 1) if n != 0])
    # Construct c >= 0 most of the time; occasionally c < 0 (no solution).
    if random.random() < 0.12:
        c = random.randint(-8, -1)
    else:
        c = random.randint(1, max_c)

    problem = (
        f"Solve for $x$: $|{a}x{_signed(b)}|={c}$. "
        f"Give each solution as an integer or fraction a/b, or 'no solution'."
    )
    if c < 0:
        return problem, "no solution"

    roots = sorted([Fraction(c - b, a), Fraction(-c - b, a)])
    solution = f"$x = {_fmt_frac(roots[0])}$ or $x = {_fmt_frac(roots[1])}$"
    return problem, solution


@register
def alg1_exponential_growth_decay(min_principal=100, max_principal=5000,
                                  max_rate=25, max_periods=8):
    r"""Exponential Growth / Decay

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | An initial amount of $1000$ grows at a rate of $5\%$ per period. Find the amount after $3$ periods. | $1157.625$ |
    """
    principal = random.randint(min_principal, max_principal)
    rate = random.randint(1, max_rate)
    periods = random.randint(1, max_periods)
    kind = random.choice(["grows", "decays"])
    factor = 1 + rate / 100 if kind == "grows" else 1 - rate / 100
    final = principal * factor ** periods

    verb = "grows" if kind == "grows" else "decays"
    problem = (
        f"An initial amount of ${principal}$ {verb} at a rate of "
        f"${rate}\\%$ per period. Find the amount after ${periods}$ periods. "
        f"Round your answer to the nearest thousandth."
    )
    return problem, f"${num(final)}$"


@register
def alg1_evaluate_exponential(max_a=10, min_base=2, max_base=6,
                              min_x=-3, max_x=4):
    r"""Evaluate an Exponential Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $f(x)=3 \cdot 2^x$, evaluate $f(4)$. | $48$ |
    """
    a = random.randint(1, max_a)
    b = random.randint(min_base, max_base)
    x = random.randint(min_x, max_x)
    value = Fraction(a) * Fraction(b) ** x

    problem = (
        f"Given $f(x)={a} \\cdot {b}^x$, evaluate $f({x})$. {_FRACTION_HINT}"
    )
    return problem, f"${_fmt_frac(value)}$"


@register
def alg1_domain_of_function(min_b=-9, max_b=9):
    r"""Domain of a Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the domain of $f(x)=\sqrt{x-3}$. | $x >= 3$ |
    | Find the domain of $f(x)=\frac{1}{x-5}$. | $x != 5$ |
    """
    b = random.choice([n for n in range(min_b, max_b + 1) if n != 0])
    threshold = -b  # value that makes the inner expression zero
    hint = "Write your answer using >=, <=, >, <, or !=."
    if random.choice(["sqrt", "rational"]) == "sqrt":
        # sqrt(x + b) is real when x + b >= 0, i.e. x >= -b.
        problem = f"Find the domain of $f(x)=\\sqrt{{x{_signed(b)}}}$. {hint}"
        solution = f"$x >= {threshold}$"
    else:
        # 1/(x + b) is defined when x + b != 0, i.e. x != -b.
        problem = f"Find the domain of $f(x)=\\frac{{1}}{{x{_signed(b)}}}$. {hint}"
        solution = f"$x != {threshold}$"
    return problem, solution


@register
def alg1_discriminant(max_a=5, min_bc=-9, max_bc=9):
    r"""Discriminant and Number of Real Roots

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the discriminant of $x^2-5x+6$ and the number of real roots. | $D=1$, 2 real roots |
    """
    a = random.choice([n for n in range(-max_a, max_a + 1) if n != 0])
    b = random.randint(min_bc, max_bc)
    c = random.randint(min_bc, max_bc)
    disc = b * b - 4 * a * c
    n = 2 if disc > 0 else (1 if disc == 0 else 0)
    word = "root" if n == 1 else "roots"

    problem = (
        f"Find the discriminant of ${_quadratic(a, b, c)}$ and the number of "
        f"real roots."
    )
    return problem, f"$D={disc}$, {n} real {word}"


@register
def alg1_axis_of_symmetry(max_a=5, min_bc=-9, max_bc=9):
    r"""Axis of Symmetry of a Parabola

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the axis of symmetry of $2x^2+4x-1$. | $x = -1$ |
    """
    a = random.choice([n for n in range(-max_a, max_a + 1) if n != 0])
    b = random.randint(min_bc, max_bc)
    c = random.randint(min_bc, max_bc)
    axis = Fraction(-b, 2 * a)

    problem = (
        f"Find the axis of symmetry of ${_quadratic(a, b, c)}$. {_FRACTION_HINT}"
    )
    return problem, f"$x = {_fmt_frac(axis)}$"


@register
def alg1_sum_product_roots(max_a=5, min_bc=-9, max_bc=9):
    r"""Sum and Product of the Roots

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | For $2x^2-6x+4$, find the sum and product of the roots. | sum=3, product=2 |
    """
    a = random.choice([n for n in range(-max_a, max_a + 1) if n != 0])
    b = random.randint(min_bc, max_bc)
    c = random.randint(min_bc, max_bc)
    root_sum = Fraction(-b, a)
    root_product = Fraction(c, a)

    problem = (
        f"For ${_quadratic(a, b, c)}$, find the sum and product of the roots. "
        f"Give each as an integer or fraction a/b, formatted as "
        f"'sum=..., product=...'."
    )
    solution = f"sum={_fmt_frac(root_sum)}, product={_fmt_frac(root_product)}"
    return problem, solution


@register
def alg1_linear_inequality_solve(max_a=6, min_bc=-10, max_bc=10):
    r"""Solve a Linear Inequality

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve for $x$: $2x+1 < 7$ | $x < 3$ |
    | Solve for $x$: $-2x+1 < 7$ | $x > -3$ |
    """
    a = random.choice([n for n in range(-max_a, max_a + 1) if n != 0])
    b = random.randint(min_bc, max_bc)
    c = random.randint(min_bc, max_bc)
    op = random.choice(["<", ">", "\\leq", "\\geq"])
    threshold = Fraction(c - b, a)

    result_op = op
    if a < 0:  # dividing by a negative flips the inequality
        result_op = {"<": ">", ">": "<", "\\leq": "\\geq", "\\geq": "\\leq"}[op]
    # Solution uses typeable ASCII relations.
    ascii_op = {"<": "<", ">": ">", "\\leq": "<=", "\\geq": ">="}[result_op]

    problem = (
        f"Solve for $x$: ${a}x{_signed(b)} {op} {c}$. "
        f"Write your answer using >=, <=, >, or <, with the value as an "
        f"integer or fraction a/b."
    )
    solution = f"$x {ascii_op} {_fmt_frac(threshold)}$"
    return problem, solution


@register
def factoring(max_root=9):
    r"""Factoring Quadratic

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Factor the quadratic $x^2+2x-48$. | $(x-6)(x+8)$ |

    Overrides the stock ``mathgenerator`` ``factoring`` generator, which returns
    the bare expression with no instruction (so a student can't tell what to
    do). We build a monic quadratic from two integer roots and ask explicitly to
    factor it. The two binomials are ordered by their constant term (ascending)
    so the exact-match answer box has one canonical, stated form to expect.
    """
    # Roots -r1, -r2 (nonzero so both binomials are genuine, e.g. no bare "x").
    r1 = random.choice([n for n in range(-max_root, max_root + 1) if n != 0])
    r2 = random.choice([n for n in range(-max_root, max_root + 1) if n != 0])
    p, q = sorted((r1, r2))  # constant terms; ascending for a canonical order
    b = p + q
    c = p * q

    problem = (
        f"Factor the quadratic ${_quadratic(1, b, c)}$. "
        f"Write your answer as (x+a)(x+b), with the two factors ordered by "
        f"their constant term from least to greatest."
    )
    solution = f"$(x{_signed(p)})(x{_signed(q)})$"
    return problem, solution


@register
def alg1_product_of_powers(min_base=2, max_base=12, min_exp=2, max_exp=8):
    r"""Product of Powers with the Same Base

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $7^{3} \cdot 7^{5}$ | 7^8 |

    ``a^m * a^n = a^(m+n)``. The answer stays in ``a^b`` form (ASCII caret, no
    braces) so it is typeable and never a huge number.
    """
    a = random.randint(min_base, max_base)
    m = random.randint(min_exp, max_exp)
    n = random.randint(min_exp, max_exp)
    problem = (
        f"Simplify ${a}^{{{m}}} \\cdot {a}^{{{n}}}$. "
        f"Write your answer in the form a^b."
    )
    return problem, f"{a}^{m + n}"


@register
def alg1_power_of_product(min_exp=2, max_exp=6):
    r"""Power of a Product

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $(xy)^{4}$ | x^4*y^4 |

    ``(xy)^n = x^n * y^n``. Kept purely symbolic so the rule is isolated and the
    answer carries no large numbers.
    """
    n = random.randint(min_exp, max_exp)
    problem = (
        f"Simplify $(xy)^{{{n}}}$. Write your answer in the form x^a*y^b."
    )
    return problem, f"x^{n}*y^{n}"


@register
def alg1_negative_exponent(min_base=2, max_base=5, min_exp=2, max_exp=3):
    r"""Negative Exponents

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $2^{-3}$ | 1/8 |

    ``a^(-n) = 1/a^n``. Bases and exponents are small so the denominator stays
    modest (at most 125). The answer is a reduced ``1/k`` fraction.
    """
    a = random.randint(min_base, max_base)
    n = random.randint(min_exp, max_exp)
    problem = (
        f"Evaluate ${a}^{{-{n}}}$. Express your answer as a fraction a/b."
    )
    return problem, f"1/{a ** n}"


@register
def alg1_complete_the_square(max_shift=8, min_c=-10, max_c=10):
    r"""Completing the Square

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Write $x^2+6x+4$ in vertex form $(x - h)^2 + k$. | $(x+3)^2-5$ |
    | Write $x^2-4x+1$ in vertex form $(x - h)^2 + k$. | $(x-2)^2-3$ |

    ``x^2 + bx + c = (x + b/2)^2 + (c - (b/2)^2)``. ``b`` is forced even so the
    shift ``b/2`` is an integer and the answer stays keyboard-typeable.
    """
    shift = random.choice([n for n in range(-max_shift, max_shift + 1) if n != 0])
    b = 2 * shift
    c = random.randint(min_c, max_c)
    k = c - shift * shift

    problem = (
        f"Write ${_quadratic(1, b, c)}$ in vertex form $(x - h)^2 + k$. "
        f"Write your answer in the form (x - h)^2 + k."
    )
    solution = f"$(x{_signed(shift)})^2{_signed(k)}$"
    return problem, solution


# Curated literal equations: (equation, variable to solve for, answer). Each
# answer is a typeable expression; the test rearranges numerically to confirm.
_LITERAL_EQUATIONS = [
    ("P = 2l + 2w", "l", "(P - 2w)/2"),
    ("P = 2l + 2w", "w", "(P - 2l)/2"),
    ("A = lw", "l", "A/w"),
    ("A = lw", "w", "A/l"),
    ("d = rt", "r", "d/t"),
    ("d = rt", "t", "d/r"),
    ("F = ma", "a", "F/m"),
    ("F = ma", "m", "F/a"),
    ("V = lwh", "h", "V/(lw)"),
    ("V = lwh", "l", "V/(wh)"),
    ("y = mx + b", "m", "(y - b)/x"),
    ("y = mx + b", "x", "(y - b)/m"),
    ("I = prt", "r", "I/(pt)"),
    ("I = prt", "p", "I/(rt)"),
    ("ax + b = c", "x", "(c - b)/a"),
]


@register
def alg1_literal_equation():
    r"""Solve a Literal Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the formula $P = 2l + 2w$ for $l$. | $(P - 2w)/2$ |
    | Solve the formula $d = rt$ for $r$. | $d/t$ |

    Rearranges a familiar formula to isolate one variable. The answer is a
    typeable expression built from ``+ - * /`` and parentheses.
    """
    equation, var, answer = random.choice(_LITERAL_EQUATIONS)
    problem = (
        f"Solve the formula ${equation}$ for ${var}$. "
        f"Write your answer as a typeable expression using +, -, *, /, and "
        f"parentheses."
    )
    return problem, f"${answer}$"


@register
def alg1_point_slope_form(coord_max=8, slope_max=6):
    r"""Point-Slope Form

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Write the equation of the line through $(1, 3)$ with slope $2$ in point-slope form. | $y - 3 = 2(x - 1)$ |
    | Write the equation of the line through $(-2, -5)$ with slope $-1$ in point-slope form. | $y + 5 = -(x + 2)$ |

    Point-slope form ``y - y1 = m(x - x1)``. Signs collapse so that, e.g.,
    ``y - (-5)`` reads ``y + 5`` and slope ``-1`` shows as a bare ``-``.
    """
    x1 = random.randint(-coord_max, coord_max)
    y1 = random.randint(-coord_max, coord_max)
    m = random.choice([n for n in range(-slope_max, slope_max + 1) if n != 0])

    # "y - y1": subtract a positive, add a negative; drop the term when zero.
    left = "y" if y1 == 0 else f"y - {y1}" if y1 > 0 else f"y + {abs(y1)}"
    # "(x - x1)" with the same sign collapsing.
    x_term = "(x)" if x1 == 0 else f"(x - {x1})" if x1 > 0 else f"(x + {abs(x1)})"
    if m == 1:
        right = x_term
    elif m == -1:
        right = f"-{x_term}"
    else:
        right = f"{m}{x_term}"

    problem = (
        f"Write the equation of the line through $({x1}, {y1})$ with slope "
        f"${m}$ in point-slope form. Give your answer in the form "
        f"y - y1 = m(x - x1)."
    )
    return problem, f"${left} = {right}$"


def _linear_factor(coef, const):
    """Render ``(coef*x + const)`` with unit/negative coefficients collapsed."""
    if coef == 1:
        head = "x"
    elif coef == -1:
        head = "-x"
    else:
        head = f"{coef}x"
    return f"({head}{_signed(const)})"


@register
def alg1_multiply_binomials(max_coef=6, max_const=8):
    r"""Multiply Binomials

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Expand $(2x+3)(x-4)$. | $2x^2-5x-12$ |
    | Expand $(x-1)(x+5)$. | $x^2+4x-5$ |

    ``(ax + b)(cx + d) = ac x^2 + (ad + bc) x + bd``. Coefficients are kept small
    so the expanded polynomial has tidy integer terms.
    """
    a = random.choice([n for n in range(-max_coef, max_coef + 1) if n != 0])
    c = random.choice([n for n in range(-max_coef, max_coef + 1) if n != 0])
    b = random.choice([n for n in range(-max_const, max_const + 1) if n != 0])
    d = random.choice([n for n in range(-max_const, max_const + 1) if n != 0])
    p = a * c
    q = a * d + b * c
    r = b * d

    problem = (
        f"Expand ${_linear_factor(a, b)}{_linear_factor(c, d)}$. "
        f"Write your answer as a polynomial in the form px^2 + qx + r."
    )
    return problem, f"${_quadratic(p, q, r)}$"


def _two_var_line(a, b, e):
    """Render ``ax + by = e`` (a, b != 0) with unit/negative coefficients tidy."""
    if a == 1:
        head = "x"
    elif a == -1:
        head = "-x"
    else:
        head = f"{a}x"
    if b > 0:
        y_term = f" + {'' if b == 1 else b}y"
    else:
        y_term = f" - {'' if b == -1 else abs(b)}y"
    return f"{head}{y_term} = {e}"


@register
def alg1_solve_system(coef_max=6, sol_max=8):
    r"""Solve a System of Equations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the system: $2x + y = 8$ and $x - y = 1$. | $(3, 2)$ |

    Builds a 2x2 linear system from a known integer solution ``(x, y)`` and
    integer coefficients with a nonzero determinant, so the unique solution is
    exactly that pair.
    """
    x = random.randint(-sol_max, sol_max)
    y = random.randint(-sol_max, sol_max)
    nonzero = [n for n in range(-coef_max, coef_max + 1) if n != 0]
    for _ in range(100):
        a = random.choice(nonzero)
        b = random.choice(nonzero)
        c = random.choice(nonzero)
        d = random.choice(nonzero)
        if a * d - b * c != 0:  # nonzero determinant -> unique solution
            break
    else:  # deterministic fallback guaranteeing a nonzero determinant
        a, b, c, d = 1, 1, 1, -1  # det = 1*(-1) - 1*1 = -2
    e = a * x + b * y
    f = c * x + d * y

    problem = (
        f"Solve the system: ${_two_var_line(a, b, e)}$ and "
        f"${_two_var_line(c, d, f)}$. Format your answer as (x, y)."
    )
    return problem, f"${pair(x, y)}$"


@register
def alg1_variation(max_k=6, max_x=9):
    r"""Direct and Inverse Variation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $y$ varies directly with $x$. When $x = 4$, $y = 12$. Find the constant of variation $k$. | $3$ |
    | $y$ varies inversely with $x$. When $x = 2$, $y = 6$. Find $y$ when $x = 4$. | $3$ |

    For direct variation ``y = kx`` so ``k = y/x``; for inverse variation
    ``xy = k``. Points are built from a small integer ``k`` so the constant is
    tidy; requested values may reduce to a simple ``a/b`` fraction.
    """
    kind = random.choice(["directly", "inversely"])
    ask = random.choice(["k", "value"])
    k = random.randint(1, max_k)

    if kind == "directly":
        # y = k*x. Build the given point from an integer k so k = y1/x1 exactly.
        x1 = random.choice([n for n in range(-max_x, max_x + 1) if n != 0])
        y1 = k * x1
        const = Fraction(y1, x1)  # == k
    else:
        # x*y = k' where k' = x1*y1 for the chosen point.
        x1 = random.choice([n for n in range(-max_x, max_x + 1) if n != 0])
        y1 = random.choice([n for n in range(-max_x, max_x + 1) if n != 0])
        const = Fraction(x1 * y1)

    hint = _FRACTION_HINT
    stem = (
        f"$y$ varies {kind} with $x$. When $x = {x1}$, $y = {y1}$. "
    )
    if ask == "k":
        problem = stem + f"Find the constant of variation $k$. {hint}"
        answer = const
    else:
        x2 = random.choice([n for n in range(-max_x, max_x + 1) if n != 0])
        problem = stem + f"Find $y$ when $x = {x2}$. {hint}"
        if kind == "directly":
            answer = const * x2      # y = k * x2
        else:
            answer = const / x2      # y = k / x2
    return problem, f"${_fmt_frac(answer)}$"


@register
def alg1_simplify_rational(max_root=7):
    r"""Simplify a Rational Expression

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $\frac{x^2+5x+6}{x^2+x-6}$. | $(x+2)/(x-3)$ |

    Numerator ``(x+r)(x+a)`` and denominator ``(x+r)(x+b)`` share the factor
    ``(x+r)``; cancelling it leaves ``(x+a)/(x+b)``. All of ``r, a, b`` are
    distinct and nonzero so no further cancellation is possible.
    """
    choices = [n for n in range(-max_root, max_root + 1) if n != 0]
    for _ in range(100):
        r = random.choice(choices)
        a = random.choice(choices)
        b = random.choice(choices)
        if len({r, a, b}) == 3:
            break
    else:  # deterministic fallback with three distinct nonzero values
        r, a, b = 1, 2, 3

    num_quad = _quadratic(1, r + a, r * a)   # (x+r)(x+a)
    den_quad = _quadratic(1, r + b, r * b)   # (x+r)(x+b)
    problem = (
        f"Simplify $\\frac{{{num_quad}}}{{{den_quad}}}$. "
        f"Write your answer in the form (x + a)/(x + b)."
    )
    solution = f"${_linear_factor(1, a)}/{_linear_factor(1, b)}$"
    return problem, solution


@register
def alg1_abs_value_inequality(max_a=5, max_b=10, min_c=2, max_c=12):
    r"""Absolute-Value Inequality

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $|2x-3| < 5$. | $-1 < x < 4$ |
    | Solve $|x+1| > 3$. | $x < -4 U x > 2$ |

    ``|ax + b| < c`` becomes the compound inequality ``-c < ax + b < c``;
    ``|ax + b| > c`` becomes ``ax + b < -c`` OR ``ax + b > c``. Boundaries are
    the values where ``ax + b = +/- c``; they are sorted so the reported
    interval reads low-to-high regardless of the sign of ``a``.
    """
    a = random.choice([n for n in range(-max_a, max_a + 1) if n != 0])
    b = random.randint(-max_b, max_b)
    c = random.randint(min_c, max_c)
    op = random.choice(["<", ">"])

    if a == 1:
        head = "x"
    elif a == -1:
        head = "-x"
    else:
        head = f"{a}x"
    inner = f"{head}{_signed(b)}"

    hint = (
        "Write your answer as a compound inequality using <, >, and U, for "
        "example -3 < x < 5 or x < -3 U x > 5."
    )
    problem = f"Solve $|{inner}| {op} {c}$. {hint}"

    # Boundaries where ax + b = -c and ax + b = c.
    bounds = sorted([Fraction(-c - b, a), Fraction(c - b, a)])
    lo, hi = _fmt_frac(bounds[0]), _fmt_frac(bounds[1])
    if op == "<":
        solution = f"${lo} < x < {hi}$"
    else:
        solution = f"$x < {lo} U x > {hi}$"
    return problem, solution


# Square-free integers >= 2: valid radicands that leave nothing more to factor
# out of the radical, so ``a*sqrt(b)`` is fully simplified.
_SQUAREFREE = [2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23]


@register
def alg1_simplify_radical(min_factor=2, max_factor=9):
    r"""Simplify Square Root

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $\sqrt{72}$. | $6*sqrt(2)$ |

    The radicand is built as $a^2 b$ with $b$ square-free, so the fully
    simplified form is $a\sqrt{b}$, typed as ``a*sqrt(b)``.
    """
    a = random.randint(min_factor, max_factor)
    b = random.choice(_SQUAREFREE)
    n = a * a * b
    problem = (
        f"Simplify $\\sqrt{{{n}}}$. Write your answer in the form "
        f"a*sqrt(b), for example 6*sqrt(2)."
    )
    return problem, f"${a}*sqrt({b})$"
