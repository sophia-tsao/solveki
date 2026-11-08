"""Solveki-local generators for Georgia "Algebra: Concepts & Connections".

These fill computable gaps in the standard course. Every generator here is
zero-required-arg, decorated with ``@register``, and returns ``(problem,
solution, steps)``: two strings with math wrapped in ``$...$`` plus a worked
explanation built with ``_steps.Steps``. Answers are kept
clean: integers, decimals to at most three places, or reduced ``a/b`` fractions.

Import this module for its ``@register`` side effects (see ``__init__`` /
tests). ``random`` is used directly and never seeded here.
"""
import random
from fractions import Fraction
from math import gcd

from ._registry import register
from ._format import frac_from as _fmt_frac, num, pair
from ._steps import Steps, paren, tex_frac

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


def _tex(value):
    r"""A ``Fraction`` (or int) as LaTeX: ``3``, ``-\frac{5}{2}``."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return tex_frac(fr.numerator, fr.denominator)


def _term(coef, var="x"):
    """A monomial with unit coefficients collapsed: ``x``, ``-x``, ``3x``."""
    if coef == 1:
        return var
    if coef == -1:
        return f"-{var}"
    return f"{coef}{var}"


def _undo_constant(b):
    """The step text that removes the constant ``b`` from one side."""
    if b > 0:
        return f"Subtract ${b}$ from both sides."
    return f"Add ${abs(b)}$ to both sides."


def _aligned(lines):
    """Stack equations in an ``aligned`` block, lined up on their first ``=``."""
    rows = [line.replace(" = ", " &= ", 1) for line in lines]
    return r"\begin{aligned} " + r" \\ ".join(rows) + r" \end{aligned}"


def _chain(*parts):
    """Join expressions with ``=``, dropping any that repeat the previous one."""
    kept = [p for i, p in enumerate(parts) if i == 0 or p != parts[i - 1]]
    return " = ".join(kept)


def _typed_answer(s, latex, typed, lead="The answer is"):
    """Close on the answer rendered as ``latex``, then as the student types it.

    For answers like ``9^63`` whose typed form doesn't render correctly as
    LaTeX (``$9^63$`` shows as 9 to the 6th, then 3).
    """
    s.answer(f"${latex}$, typed as {typed}", lead=lead)


def _elimination_steps(s, a, b, c, d, e, f, x, y):
    """Steps solving ``ax + by = e``, ``cx + dy = f`` by eliminating ``x``.

    Shared with ``lib_powers_gen.system_of_equations``. Each equation is scaled
    by a positive multiplier so the ``x``-terms match (or are opposites), then
    the equations are subtracted (or added) and ``y`` back-substituted.
    """
    g = gcd(a, c)
    m1, m2 = abs(c) // g, abs(a) // g
    a1, b1, e1 = m1 * a, m1 * b, m1 * e
    a2, b2, e2 = m2 * c, m2 * d, m2 * f
    if m1 == 1 and m2 == 1:
        relation = "equal" if a1 == a2 else "opposites"
        s.step(f"Eliminate $x$. Its coefficients are already {relation}.",
               _aligned([_two_var_line(a1, b1, e1), _two_var_line(a2, b2, e2)]))
    else:
        scaled = [f"the {which} equation by ${m}$"
                  for which, m in (("first", m1), ("second", m2)) if m != 1]
        goal = (f"both $x$-terms are ${_term(a1)}$" if a1 == a2
                else f"the $x$-terms are ${_term(a1)}$ and ${_term(a2)}$")
        s.step(f"Eliminate $x$. Multiply {' and '.join(scaled)} so {goal}.",
               _aligned([_two_var_line(a1, b1, e1), _two_var_line(a2, b2, e2)]))
    if a1 == a2:
        coef, rhs = b1 - b2, e1 - e2
        s.step("Subtract the second equation from the first.",
               f"{_term(coef, 'y')} = {rhs}")
    else:
        coef, rhs = b1 + b2, e1 + e2
        s.step("Add the two equations.", f"{_term(coef, 'y')} = {rhs}")
    if coef != 1:
        s.step(f"Divide both sides by ${coef}$.", f"y = {y}")
    by = b * y
    sign = "+" if b > 0 else "-"
    lines = [f"{_term(a)} {sign} {abs(b)}({y}) = {e}"]
    if by != 0:
        lines.append(f"{_term(a)} {'+' if by > 0 else '-'} {abs(by)} = {e}")
    lines.append(f"{_term(a)} = {e - by}")
    if a != 1:
        lines.append(f"x = {x}")
    s.step(f"Substitute $y = {y}$ into the first equation and solve for $x$.",
           _aligned(lines))


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
        f"Solve for $x$: $|{_term(a)}{_signed(b)}|={c}$. "
        f"Give each solution as an integer or fraction a/b, or 'no solution'."
    )
    inner = f"{_term(a)}{_signed(b)}"
    s = Steps()
    if c < 0:
        s.step("An absolute value is a distance from zero, so it is never negative.")
        s.step(f"$|{inner}|$ can't equal ${c}$ for any $x$.")
        s.answer("no solution", lead="So there is")
        return problem, "no solution", s.done()

    roots = sorted([Fraction(c - b, a), Fraction(-c - b, a)])
    solution = f"$x = {_fmt_frac(roots[0])}$ or $x = {_fmt_frac(roots[1])}$"

    s.step(f"If $|u| = {c}$, then $u = {c}$ or $u = {-c}$. Split into two equations.",
           rf"{inner} = {c} \quad \text{{or}} \quad {inner} = {-c}")
    s.step(_undo_constant(b),
           rf"{_term(a)} = {c - b} \quad \text{{or}} \quad {_term(a)} = {-c - b}")
    if a != 1:
        s.step(f"Divide both sides by ${a}$.",
               rf"x = {_tex(Fraction(c - b, a))} \quad \text{{or}} \quad "
               rf"x = {_tex(Fraction(-c - b, a))}")
    s.answer(solution)
    return problem, solution, s.done()


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
    solution = f"${num(final)}$"

    sign = "+" if kind == "grows" else "-"
    signed_rate = rate if kind == "grows" else -rate
    exact = principal * Fraction(100 + signed_rate, 100) ** periods
    rounded = (exact * 1000).denominator != 1
    rel = r"\approx" if rounded else "="
    s = Steps()
    s.formula(f"The exponential {'growth' if kind == 'grows' else 'decay'} formula",
              f"A = P(1 {sign} r)^t")
    s.step(f"Write ${rate}\\%$ as the decimal $r = {num(rate / 100)}$, so each period "
           f"multiplies by $1 {sign} {num(rate / 100)} = {num(factor)}$.")
    s.substitute(f"A = {principal}({num(factor)})^{{{periods}}}")
    s.step(f"Evaluate the power, then multiply by ${principal}$.",
           f"A {rel} {num(final)}")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is"
             if rounded else "The answer is")
    return problem, solution, s.done()


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
    solution = f"${_fmt_frac(value)}$"

    s = Steps()
    s.substitute(rf"f({x}) = {a} \cdot {b}^{{{x}}}", text=f"Substitute $x = {x}$.")
    if x > 0:
        power = b ** x
        repeated = r" \cdot ".join([str(b)] * x)
        s.step("Evaluate the power first.",
               rf"{b}^{{{x}}} = {repeated} = {power}" if x > 1 else f"{b}^{{1}} = {b}")
        if a != 1:
            s.step(f"Multiply by ${a}$.", rf"f({x}) = {a} \cdot {power} = {a * power}")
    elif x == 0:
        s.step("Any nonzero number to the power $0$ is $1$.", f"{b}^{{0}} = 1")
        if a != 1:
            s.step(f"Multiply by ${a}$.", rf"f(0) = {a} \cdot 1 = {a}")
    else:
        power = b ** -x
        s.step("A negative exponent means take the reciprocal of the positive power.",
               rf"{b}^{{{x}}} = \frac{{1}}{{{b}^{{{-x}}}}} = \frac{{1}}{{{power}}}")
        if a != 1:
            product = rf"f({x}) = {a} \cdot \frac{{1}}{{{power}}} = \frac{{{a}}}{{{power}}}"
            if Fraction(a, power).denominator != power:
                product += f" = {_tex(value)}"
            s.step(f"Multiply by ${a}$ and simplify.", product)
    s.answer(solution)
    return problem, solution, s.done()


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
    inner = f"x{_signed(b)}"
    s = Steps()
    if random.choice(["sqrt", "rational"]) == "sqrt":
        # sqrt(x + b) is real when x + b >= 0, i.e. x >= -b.
        problem = f"Find the domain of $f(x)=\\sqrt{{x{_signed(b)}}}$. {hint}"
        solution = f"$x >= {threshold}$"
        s.step("You can't take the square root of a negative number, so the "
               "expression under the root must be at least $0$.",
               rf"{inner} \geq 0")
        s.step(_undo_constant(b), rf"x \geq {threshold}")
    else:
        # 1/(x + b) is defined when x + b != 0, i.e. x != -b.
        problem = f"Find the domain of $f(x)=\\frac{{1}}{{x{_signed(b)}}}$. {hint}"
        solution = f"$x != {threshold}$"
        s.step("Division by zero is undefined, so the denominator can't be $0$.",
               rf"{inner} \neq 0")
        s.step(_undo_constant(b), rf"x \neq {threshold}")
    s.answer(solution)
    return problem, solution, s.done()


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
    solution = f"$D={disc}$, {n} real {word}"

    four_ac = 4 * a * c
    s = Steps()
    s.formula("For $ax^2+bx+c$, the discriminant", "D = b^2 - 4ac")
    s.substitute(rf"D = {paren(b)}^2 - 4({a})({c})",
                 text=f"Here $a = {a}$, $b = {b}$, and $c = {c}$.")
    s.step("Simplify.",
           f"D = {b * b} {'-' if four_ac >= 0 else '+'} {abs(four_ac)} = {disc}")
    if disc > 0:
        s.step(f"Since $D = {disc} > 0$, the quadratic has two real roots.")
    elif disc == 0:
        s.step("Since $D = 0$, the quadratic has exactly one real root (a double root).")
    else:
        s.step(f"Since $D = {disc} < 0$, the quadratic has no real roots.")
    s.answer(solution)
    return problem, solution, s.done()


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
    solution = f"$x = {_fmt_frac(axis)}$"

    s = Steps()
    s.formula("For $ax^2+bx+c$, the axis of symmetry", r"x = -\frac{b}{2a}")
    s.substitute(rf"x = -\frac{{{b}}}{{2({a})}}",
                 text=f"Here $a = {a}$ and $b = {b}$.")
    s.step("Simplify.", _chain("x", tex_frac(-b, 2 * a) if b else "0", _tex(axis)))
    s.answer(solution)
    return problem, solution, s.done()


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

    s = Steps()
    s.step("By Vieta's formulas, the roots of $ax^2+bx+c$ have:",
           r"\text{sum} = -\frac{b}{a}, \qquad \text{product} = \frac{c}{a}")
    s.step(f"Here $a = {a}$, $b = {b}$, and $c = {c}$.")
    s.step("Find the sum.", _chain(r"\text{sum}", rf"-\frac{{{b}}}{{{a}}}",
                                   tex_frac(-b, a) if b else "0", _tex(root_sum)))
    s.step("Find the product.", _chain(r"\text{product}", rf"\frac{{{c}}}{{{a}}}",
                                       tex_frac(c, a) if c else "0", _tex(root_product)))
    s.answer(solution)
    return problem, solution, s.done()


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
        f"Solve for $x$: ${_term(a)}{_signed(b)} {op} {c}$. "
        f"Write your answer using >=, <=, >, or <, with the value as an "
        f"integer or fraction a/b."
    )
    solution = f"$x {ascii_op} {_fmt_frac(threshold)}$"

    s = Steps()
    s.step("Isolate $x$ as you would in an equation. The one difference: "
           "multiplying or dividing both sides by a negative number flips the "
           "inequality sign.")
    if b != 0:
        s.step(_undo_constant(b), f"{_term(a)} {op} {c - b}")
    if a < 0:
        s.step(f"Divide both sides by ${a}$. It's negative, so flip the sign.",
               f"x {result_op} {_tex(threshold)}")
    elif a != 1:
        s.step(f"Divide both sides by ${a}$. It's positive, so the sign stays the same.",
               f"x {result_op} {_tex(threshold)}")
    s.answer(solution)
    return problem, solution, s.done()


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

    s = Steps()
    s.step(f"To factor $x^2+bx+c$, find two numbers that multiply to $c = {c}$ "
           f"and add to $b = {b}$.")
    s.step(f"The numbers ${p}$ and ${q}$ work.",
           rf"{p} \cdot {paren(q)} = {c}, \qquad {p} + {paren(q)} = {b}")
    s.step("Use them as the constant terms of the two factors, the smaller one first.",
           f"{_quadratic(1, b, c)} = (x{_signed(p)})(x{_signed(q)})")
    s.answer(solution)
    return problem, solution, s.done()


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
    solution = f"{a}^{m + n}"

    s = Steps()
    s.formula("The product of powers rule", r"a^m \cdot a^n = a^{m+n}")
    s.step(f"The bases are both ${a}$, so keep the base and add the exponents.",
           rf"{a}^{{{m}}} \cdot {a}^{{{n}}} = {a}^{{{m}+{n}}} = {a}^{{{m + n}}}")
    _typed_answer(s, f"{a}^{{{m + n}}}", solution)
    return problem, solution, s.done()


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
    solution = f"x^{n}*y^{n}"

    s = Steps()
    s.formula("The power of a product rule", r"(xy)^n = x^n y^n")
    s.step(f"Raise each factor inside the parentheses to the power ${n}$.",
           f"(xy)^{{{n}}} = x^{{{n}}} y^{{{n}}}")
    _typed_answer(s, f"x^{{{n}}} y^{{{n}}}", solution)
    return problem, solution, s.done()


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
    solution = f"1/{a ** n}"

    repeated = r" \cdot ".join([str(a)] * n)
    s = Steps()
    s.formula("The negative exponent rule", r"a^{-n} = \frac{1}{a^n}")
    s.step("Rewrite the power as a reciprocal with a positive exponent.",
           rf"{a}^{{-{n}}} = \frac{{1}}{{{a}^{{{n}}}}}")
    s.step(f"Evaluate ${a}^{{{n}}} = {repeated} = {a ** n}$.",
           rf"\frac{{1}}{{{a}^{{{n}}}}} = \frac{{1}}{{{a ** n}}}")
    s.answer(solution)
    return problem, solution, s.done()


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

    square = shift * shift
    tail = f" {'+' if c > 0 else '-'} {abs(c)}" if c else ""
    s = Steps()
    s.step("Take half of the $x$-coefficient and square it.",
           rf"\left(\frac{{{b}}}{{2}}\right)^2 = {paren(shift)}^2 = {square}")
    s.step(f"Add and subtract ${square}$, which doesn't change the value.",
           f"x^2{_signed(b)}x + {square} - {square}{tail}")
    s.step(f"The first three terms form a perfect square: "
           f"$x^2{_signed(b)}x + {square} = (x{_signed(shift)})^2$.",
           f"(x{_signed(shift)})^2 - {square}{tail}")
    if c != 0:
        s.step(f"Combine the constants: $-{square}{tail} = {k}$.",
               f"(x{_signed(shift)})^2{_signed(k)}")
    s.answer(solution)
    return problem, solution, s.done()


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

# Worked steps for each entry above, keyed by (equation, variable): the
# (text, math) pairs between the opening "undo the operations" step and the
# answer.
_LITERAL_STEPS = {
    ("P = 2l + 2w", "l"): [
        ("Subtract $2w$ from both sides.", "P - 2w = 2l"),
        ("Divide both sides by $2$.", r"l = \frac{P - 2w}{2}"),
    ],
    ("P = 2l + 2w", "w"): [
        ("Subtract $2l$ from both sides.", "P - 2l = 2w"),
        ("Divide both sides by $2$.", r"w = \frac{P - 2l}{2}"),
    ],
    ("A = lw", "l"): [("$l$ is multiplied by $w$, so divide both sides by $w$.",
                       r"l = \frac{A}{w}")],
    ("A = lw", "w"): [("$w$ is multiplied by $l$, so divide both sides by $l$.",
                       r"w = \frac{A}{l}")],
    ("d = rt", "r"): [("$r$ is multiplied by $t$, so divide both sides by $t$.",
                       r"r = \frac{d}{t}")],
    ("d = rt", "t"): [("$t$ is multiplied by $r$, so divide both sides by $r$.",
                       r"t = \frac{d}{r}")],
    ("F = ma", "a"): [("$a$ is multiplied by $m$, so divide both sides by $m$.",
                       r"a = \frac{F}{m}")],
    ("F = ma", "m"): [("$m$ is multiplied by $a$, so divide both sides by $a$.",
                       r"m = \frac{F}{a}")],
    ("V = lwh", "h"): [("$h$ is multiplied by $lw$, so divide both sides by $lw$.",
                        r"h = \frac{V}{lw}")],
    ("V = lwh", "l"): [("$l$ is multiplied by $wh$, so divide both sides by $wh$.",
                        r"l = \frac{V}{wh}")],
    ("y = mx + b", "m"): [
        ("Subtract $b$ from both sides.", "y - b = mx"),
        ("Divide both sides by $x$.", r"m = \frac{y - b}{x}"),
    ],
    ("y = mx + b", "x"): [
        ("Subtract $b$ from both sides.", "y - b = mx"),
        ("Divide both sides by $m$.", r"x = \frac{y - b}{m}"),
    ],
    ("I = prt", "r"): [("$r$ is multiplied by $pt$, so divide both sides by $pt$.",
                        r"r = \frac{I}{pt}")],
    ("I = prt", "p"): [("$p$ is multiplied by $rt$, so divide both sides by $rt$.",
                        r"p = \frac{I}{rt}")],
    ("ax + b = c", "x"): [
        ("Subtract $b$ from both sides.", "ax = c - b"),
        ("Divide both sides by $a$.", r"x = \frac{c - b}{a}"),
    ],
}


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
    solution = f"${answer}$"

    s = Steps()
    s.step(f"Treat every letter except ${var}$ like a number, and undo the "
           f"operations on ${var}$ one at a time.")
    for text, math in _LITERAL_STEPS[(equation, var)]:
        s.step(text, math)
    s.answer(solution, lead="Written on one line, the answer is")
    return problem, solution, s.done()


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
    solution = f"${left} = {right}$"

    s = Steps()
    s.formula("Point-slope form", "y - y_1 = m(x - x_1)")
    substituted = f"y - {paren(y1)} = {m}(x - {paren(x1)})"
    s.substitute(substituted,
                 text=f"Substitute the point $(x_1, y_1) = ({x1}, {y1})$ and the slope $m = {m}$.")
    if substituted != f"{left} = {right}":
        notes = []
        if x1 < 0 or y1 < 0:
            notes.append("subtracting a negative is the same as adding")
        if x1 == 0 or y1 == 0:
            notes.append("subtracting $0$ changes nothing")
        if m == 1:
            notes.append("a slope of $1$ doesn't need to be written")
        elif m == -1:
            notes.append("a slope of $-1$ is written as just a minus sign")
        s.step(f"Simplify: {'; '.join(notes)}.", f"{left} = {right}")
    s.answer(solution)
    return problem, solution, s.done()


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
    solution = f"${_quadratic(p, q, r)}$"

    first, second = _term(a), _term(c)
    s = Steps()
    s.step("Multiply each term of the first binomial by each term of the second "
           "(FOIL: First, Outer, Inner, Last).",
           r"\begin{aligned} "
           rf"\text{{First: }} & ({first})({second}) = {_term(p, 'x^2')} \\ "
           rf"\text{{Outer: }} & ({first})({d}) = {_term(a * d)} \\ "
           rf"\text{{Inner: }} & ({b})({second}) = {_term(b * c)} \\ "
           rf"\text{{Last: }} & ({b})({d}) = {r} "
           r"\end{aligned}")
    if q == 0:
        combine = f"The $x$-terms ${_term(a * d)}$ and ${_term(b * c)}$ cancel out."
    else:
        combine = (f"Combine the like terms: ${_term(a * d)} {'+' if b * c > 0 else '-'} "
                   f"{_term(abs(b * c))} = {_term(q)}$.")
    s.step(combine, _quadratic(p, q, r))
    s.answer(solution)
    return problem, solution, s.done()


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
    solution = f"${pair(x, y)}$"

    s = Steps()
    _elimination_steps(s, a, b, c, d, e, f, x, y)
    s.answer(solution)
    return problem, solution, s.done()


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
    solution = f"${_fmt_frac(answer)}$"

    s = Steps()
    if kind == "directly":
        s.formula("Direct variation", "y = kx")
        s.step("Divide $y$ by $x$ using the given point to find $k$.",
               rf"k = \frac{{{y1}}}{{{x1}}} = {_tex(const)}")
        if ask == "value":
            s.step(f"So $y = {_tex(const)}x$. Substitute $x = {x2}$.",
                   rf"y = {_tex(const)} \cdot {paren(x2)} = {_tex(answer)}")
    else:
        s.formula("Inverse variation", "xy = k")
        s.step("Multiply $x$ and $y$ from the given point to find $k$.",
               f"k = ({x1})({y1}) = {_tex(const)}")
        if ask == "value":
            s.step(f"So $xy = {_tex(const)}$. Substitute $x = {x2}$ and divide "
                   f"to find $y$.",
                   _chain("y", rf"\frac{{{const}}}{{{x2}}}",
                          tex_frac(const.numerator, x2), _tex(answer)))
    s.answer(solution)
    return problem, solution, s.done()


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

    common, top, bottom = (_linear_factor(1, v) for v in (r, a, b))
    s = Steps()
    s.step(f"Factor the numerator: find two numbers that multiply to ${r * a}$ "
           f"and add to ${r + a}$. They are ${r}$ and ${a}$.",
           f"{num_quad} = {common}{top}")
    s.step(f"Factor the denominator: find two numbers that multiply to ${r * b}$ "
           f"and add to ${r + b}$. They are ${r}$ and ${b}$.",
           f"{den_quad} = {common}{bottom}")
    s.step(f"Cancel the common factor ${common}$ from the top and bottom.",
           rf"\frac{{{common}{top}}}{{{common}{bottom}}} = \frac{{{top}}}{{{bottom}}}")
    s.answer(solution, lead="Written on one line, the answer is")
    return problem, solution, s.done()


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

    left, right = -c - b, c - b  # head's bounds once b is moved across
    at_left, at_right = _tex(Fraction(left, a)), _tex(Fraction(right, a))
    shift = f"Subtract ${b}$ from" if b > 0 else f"Add ${abs(b)}$ to"
    s = Steps()
    if op == "<":
        s.step(f"$|u| < {c}$ means $u$ is less than ${c}$ away from zero, so "
               f"$-{c} < u < {c}$.", f"-{c} < {inner} < {c}")
        if b != 0:
            s.step(f"{shift} all three parts.", f"{left} < {head} < {right}")
        if a > 1:
            s.step(f"Divide all three parts by ${a}$.", f"{at_left} < x < {at_right}")
        elif a < 0:
            s.step(f"Divide all three parts by ${a}$. It's negative, so both signs "
                   "flip. Then rewrite it from least to greatest.",
                   rf"{at_left} > x > {at_right} \quad \Rightarrow \quad "
                   rf"{at_right} < x < {at_left}")
        s.answer(solution)
    else:
        s.step(f"$|u| > {c}$ means $u$ is more than ${c}$ away from zero, so "
               f"$u < -{c}$ or $u > {c}$.",
               rf"{inner} < -{c} \quad \text{{or}} \quad {inner} > {c}")
        if b != 0:
            s.step(f"{shift} both sides of each inequality.",
                   rf"{head} < {left} \quad \text{{or}} \quad {head} > {right}")
        if a > 1:
            s.step(f"Divide by ${a}$.",
                   rf"x < {at_left} \quad \text{{or}} \quad x > {at_right}")
        elif a < 0:
            s.step(f"Divide by ${a}$. It's negative, so both signs flip.",
                   rf"x > {at_left} \quad \text{{or}} \quad x < {at_right}")
        s.answer(solution, lead='Writing the smaller piece first and "U" for "or", '
                                'the answer is')
    return problem, solution, s.done()


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
    solution = f"${a}*sqrt({b})$"

    s = Steps()
    s.step(f"Find the largest perfect square that divides ${n}$: it's "
           rf"${a * a} = {a}^2$, since ${n} = {a * a} \cdot {b}$.",
           rf"\sqrt{{{n}}} = \sqrt{{{a * a} \cdot {b}}}")
    s.step(r"Use $\sqrt{ab} = \sqrt{a}\sqrt{b}$ and take the square root of the "
           "perfect square.",
           rf"\sqrt{{{a * a}}} \cdot \sqrt{{{b}}} = {a}\sqrt{{{b}}}")
    _typed_answer(s, rf"{a}\sqrt{{{b}}}", f"{a}*sqrt({b})")
    return problem, solution, s.done()
