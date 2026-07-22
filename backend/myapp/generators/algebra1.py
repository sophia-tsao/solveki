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


def _fmt_frac(value):
    """Format a Fraction/int as ``'n'`` (integer) or reduced ``'p/q'``."""
    frac = Fraction(value)
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


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
def alg1_absolute_value_equation():
    r"""Absolute Value Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve for $x$: $|2x+3|=7$ | $x = -5$ or $x = 2$ |
    """
    a = random.randint(1, 6)
    b = random.choice([n for n in range(-10, 11) if n != 0])
    # Construct c >= 0 most of the time; occasionally c < 0 (no solution).
    if random.random() < 0.12:
        c = random.randint(-8, -1)
    else:
        c = random.randint(1, 15)

    problem = f"Solve for $x$: $|{a}x{_signed(b)}|={c}$"
    if c < 0:
        return problem, "no solution"

    roots = sorted([Fraction(c - b, a), Fraction(-c - b, a)])
    solution = f"$x = {_fmt_frac(roots[0])}$ or $x = {_fmt_frac(roots[1])}$"
    return problem, solution


@register
def alg1_exponential_growth_decay():
    r"""Exponential Growth / Decay

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | An initial amount of $1000$ grows at a rate of $5\%$ per period. Find the amount after $3$ periods. | $1157.63$ |
    """
    principal = random.randint(100, 5000)
    rate = random.randint(1, 25)
    periods = random.randint(1, 8)
    kind = random.choice(["grows", "decays"])
    factor = 1 + rate / 100 if kind == "grows" else 1 - rate / 100
    final = round(principal * factor ** periods, 2)

    verb = "grows" if kind == "grows" else "decays"
    problem = (
        f"An initial amount of ${principal}$ {verb} at a rate of "
        f"${rate}\\%$ per period. Find the amount after ${periods}$ periods."
    )
    return problem, f"${final}$"


@register
def alg1_evaluate_exponential():
    r"""Evaluate an Exponential Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $f(x)=3 \cdot 2^x$, evaluate $f(4)$. | $48$ |
    """
    a = random.randint(1, 10)
    b = random.randint(2, 6)
    x = random.randint(-3, 4)
    value = Fraction(a) * Fraction(b) ** x

    problem = f"Given $f(x)={a} \\cdot {b}^x$, evaluate $f({x})$."
    return problem, f"${_fmt_frac(value)}$"


@register
def alg1_domain_of_function():
    r"""Domain of a Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the domain of $f(x)=\sqrt{x-3}$. | $x \geq 3$ |
    | Find the domain of $f(x)=\frac{1}{x-5}$. | $x \neq 5$ |
    """
    b = random.choice([n for n in range(-9, 10) if n != 0])
    threshold = -b  # value that makes the inner expression zero
    if random.choice(["sqrt", "rational"]) == "sqrt":
        # sqrt(x + b) is real when x + b >= 0, i.e. x >= -b.
        problem = f"Find the domain of $f(x)=\\sqrt{{x{_signed(b)}}}$."
        solution = f"$x \\geq {threshold}$"
    else:
        # 1/(x + b) is defined when x + b != 0, i.e. x != -b.
        problem = f"Find the domain of $f(x)=\\frac{{1}}{{x{_signed(b)}}}$."
        solution = f"$x \\neq {threshold}$"
    return problem, solution


@register
def alg1_discriminant():
    r"""Discriminant and Number of Real Roots

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the discriminant of $x^2-5x+6$ and the number of real roots. | $D=1$, 2 real roots |
    """
    a = random.choice([n for n in range(-5, 6) if n != 0])
    b = random.randint(-9, 9)
    c = random.randint(-9, 9)
    disc = b * b - 4 * a * c
    n = 2 if disc > 0 else (1 if disc == 0 else 0)
    word = "root" if n == 1 else "roots"

    problem = (
        f"Find the discriminant of ${_quadratic(a, b, c)}$ and the number of "
        f"real roots."
    )
    return problem, f"$D={disc}$, {n} real {word}"


@register
def alg1_axis_of_symmetry():
    r"""Axis of Symmetry of a Parabola

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the axis of symmetry of $2x^2+4x-1$. | $x = -1$ |
    """
    a = random.choice([n for n in range(-5, 6) if n != 0])
    b = random.randint(-9, 9)
    c = random.randint(-9, 9)
    axis = Fraction(-b, 2 * a)

    problem = f"Find the axis of symmetry of ${_quadratic(a, b, c)}$."
    return problem, f"$x = {_fmt_frac(axis)}$"


@register
def alg1_sum_product_roots():
    r"""Sum and Product of the Roots

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | For $2x^2-6x+4$, find the sum and product of the roots. | sum=3, product=2 |
    """
    a = random.choice([n for n in range(-5, 6) if n != 0])
    b = random.randint(-9, 9)
    c = random.randint(-9, 9)
    root_sum = Fraction(-b, a)
    root_product = Fraction(c, a)

    problem = (
        f"For ${_quadratic(a, b, c)}$, find the sum and product of the roots."
    )
    solution = f"sum={_fmt_frac(root_sum)}, product={_fmt_frac(root_product)}"
    return problem, solution


@register
def alg1_linear_inequality_solve():
    r"""Solve a Linear Inequality

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve for $x$: $2x+1 < 7$ | $x < 3$ |
    | Solve for $x$: $-2x+1 < 7$ | $x > -3$ |
    """
    a = random.choice([n for n in range(-6, 7) if n != 0])
    b = random.randint(-10, 10)
    c = random.randint(-10, 10)
    op = random.choice(["<", ">", "\\leq", "\\geq"])
    threshold = Fraction(c - b, a)

    result_op = op
    if a < 0:  # dividing by a negative flips the inequality
        result_op = {"<": ">", ">": "<", "\\leq": "\\geq", "\\geq": "\\leq"}[op]

    problem = f"Solve for $x$: ${a}x{_signed(b)} {op} {c}$"
    solution = f"$x {result_op} {_fmt_frac(threshold)}$"
    return problem, solution
