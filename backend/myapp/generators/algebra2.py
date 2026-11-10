"""Solveki-local generators for Georgia Advanced Algebra: Concepts & Connections.

These fill computable gaps in the stock ``mathgenerator`` catalogue for the
"Advanced Algebra: Concepts & Connections" course. Every generator in this
module is named with an ``alg2_`` prefix, takes no required arguments, and
returns ``(problem, solution, steps)``: two LaTeX strings plus a step-by-step
explanation built with ``_steps.Steps``.
"""
import random
from math import copysign, isqrt, lcm, log, sqrt
from fractions import Fraction

from ._registry import register
from ._variants import with_variants
from ._steps import Steps, paren, tex_frac
from ._format import num as _num
from ._format import frac_from as _frac_from

# Small non-perfect-square radicands used in conjugate/rationalizing problems,
# kept tiny so the resulting rational values stay clean.
_NON_SQUARES = [2, 3, 5, 6, 7, 10]


def _format_polynomial(terms):
    """Render ``(coefficient, exponent)`` pairs as a polynomial string.

    Zero-coefficient terms are dropped, signs are joined with the right
    operator, and unit coefficients omit the leading ``1`` (e.g. ``x^2``,
    ``-x``). ``terms`` should be ordered from the highest exponent down.
    """
    pieces = []
    for coeff, exp in terms:
        if coeff == 0:
            continue
        sign = "-" if coeff < 0 else "+"
        magnitude = abs(coeff)
        if exp == 0:
            body = str(magnitude)
        else:
            var = "x" if exp == 1 else f"x^{exp}"
            body = var if magnitude == 1 else f"{magnitude}{var}"
        pieces.append((sign, body))

    if not pieces:
        return "0"

    first_sign, first_body = pieces[0]
    result = first_body if first_sign == "+" else f"-{first_body}"
    for sign, body in pieces[1:]:
        result += f"{sign}{body}"
    return result


def _coeffs_to_terms(coeffs):
    """``[a, b, c]`` (highest degree first) -> ``[(a, 2), (b, 1), (c, 0)]``."""
    degree = len(coeffs) - 1
    return [(c, degree - i) for i, c in enumerate(coeffs)]


def _eval_coeffs(coeffs, x):
    """Evaluate a polynomial given as highest-degree-first coefficients."""
    degree = len(coeffs) - 1
    return sum(c * (x ** (degree - i)) for i, c in enumerate(coeffs))


def _random_poly(min_deg, max_deg):
    """Return highest-first coefficients with a nonzero leading coefficient."""
    degree = random.randint(min_deg, max_deg)
    coeffs = [random.choice([c for c in range(-6, 7) if c != 0])]
    coeffs += [random.randint(-6, 6) for _ in range(degree - 1)]
    coeffs.append(random.choice([c for c in range(-6, 7) if c != 0]))
    return coeffs


def _synthetic_division(coeffs, r):
    """Divide (highest-first) ``coeffs`` by ``(x - r)``.

    Returns ``(quotient_coeffs, remainder)``.
    """
    out = [coeffs[0]]
    for c in coeffs[1:]:
        out.append(c + out[-1] * r)
    return out[:-1], out[-1]


def _divisor_str(r):
    """``(x - r)`` inner text: r=2 -> 'x-2', r=-3 -> 'x+3'."""
    return f"x-{r}" if r > 0 else f"x+{-r}"


def _clean_num(value):
    """Format a number to at most 3 decimal places, trimming trailing zeros."""
    return _num(value)


def _complex_str(a, b):
    """Format ``a + b i`` (b assumed nonzero) as e.g. '3+2i', '1-i', '-4+i'."""
    connector = "+" if b > 0 else "-"
    mag = "i" if abs(b) == 1 else f"{abs(b)}i"
    return f"{a}{connector}{mag}"


def _complex_result_str(p, q):
    """Normalized complex result; p and q are assumed both nonzero here."""
    connector = "+" if q > 0 else "-"
    mag = "i" if abs(q) == 1 else f"{abs(q)}i"
    return f"{p}{connector}{mag}"


def _signed(coeff, var):
    """A trailing signed term, e.g. coeff=-4 var='y' -> '-4y'."""
    return f"{'+' if coeff >= 0 else '-'}{abs(coeff)}{var}"


# --- Step-by-step helpers -------------------------------------------------

def _join_signed(pieces):
    """Join ``(sign, body)`` pairs into ``a+b-c``, with no leading ``+``."""
    if not pieces:
        return "0"
    sign, body = pieces[0]
    out = body if sign == "+" else f"-{body}"
    for sign, body in pieces[1:]:
        out += f"{sign}{body}"
    return out


def _sum_str(values):
    """Integers as a signed sum: ``[18, 9, -1]`` -> ``'18+9-1'``."""
    return _join_signed([("-" if v < 0 else "+", str(abs(v))) for v in values])


def _linear(pairs):
    """``[(2, 'x'), (-1, 'y')]`` -> ``'2x-y'``, dropping zero terms."""
    return _join_signed([
        ("-" if coeff < 0 else "+", f"{'' if abs(coeff) == 1 else abs(coeff)}{var}")
        for coeff, var in pairs if coeff != 0
    ])


def _poly(coeffs):
    """Highest-first coefficients rendered as a polynomial."""
    return _format_polynomial(_coeffs_to_terms(coeffs))


def _subst_poly(coeffs, x):
    """The polynomial with ``x`` plugged into each term: ``2(3)^{2}+3(3)-1``."""
    pieces = []
    for coeff, exp in _coeffs_to_terms(coeffs):
        if coeff == 0:
            continue
        mag = abs(coeff)
        if exp == 0:
            body = str(mag)
        else:
            power = "" if exp == 1 else f"^{{{exp}}}"
            body = f"{'' if mag == 1 else mag}({x}){power}"
        pieces.append(("-" if coeff < 0 else "+", body))
    return _join_signed(pieces)


def _evaluate_steps(s, name, coeffs, x):
    """Substitute, evaluate each term, then add: the steps for ``name(x)``."""
    lhs = f"{name}({x})"
    s.substitute(f"{lhs} = {_subst_poly(coeffs, x)}", text=f"Substitute ${x}$ for every $x$.")
    terms = [(c, e) for c, e in _coeffs_to_terms(coeffs) if c != 0]
    values = [c * x ** e for c, e in terms]
    if len(values) == 1:
        text = "Multiply." if terms[0][1] <= 1 else "Evaluate the power, then multiply by the coefficient."
        s.step(text, f"{lhs} = {values[0]}")
    else:
        s.step("Evaluate each term: powers first, then multiply by the coefficient.",
               f"{lhs} = {_sum_str(values)}")
        s.step("Add the terms.", f"{lhs} = {sum(values)}")


def _root_factor(root):
    """The factor a root gives: ``2`` -> ``(x-2)``, ``-3`` -> ``(x+3)``, ``0`` -> ``x``."""
    return "x" if root == 0 else f"({_divisor_str(root)})"


def _times_linear(coeffs, root):
    """Multiply highest-first ``coeffs`` by ``(x - root)``."""
    shifted = coeffs + [0]
    scaled = [0] + [c * (-root) for c in coeffs]
    return [s + t for s, t in zip(shifted, scaled)]


def _multiply_out_step(s, coeffs, root):
    """Add the step multiplying ``coeffs`` by ``(x - root)``; return the product."""
    product = _times_linear(coeffs, root)
    current, result = _poly(coeffs), _poly(product)
    if root == 0:
        s.step("Multiply by $x$, which raises each power by one.", f"x({current}) = {result}")
        return product
    first = _format_polynomial([(c, e + 1) for c, e in _coeffs_to_terms(coeffs)])
    second = _format_polynomial([(-root * c, e) for c, e in _coeffs_to_terms(coeffs)])
    expanded = first + (second if second.startswith("-") else f"+{second}")
    sign = "-" if root > 0 else "+"
    scale = "" if abs(root) == 1 else abs(root)
    math = f"x({current}){sign}{scale}({current}) = {expanded}"
    if expanded != result:
        math += f" = {result}"
    s.step(f"Multiply $({current})$ by $({_divisor_str(root)})$: distribute, then combine like terms.",
           math)
    return product


def _tex_fraction(value):
    """A ``Fraction`` as LaTeX: an integer, or ``\\frac`` with the sign out front."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return tex_frac(value.numerator, value.denominator)


def _matrix(rows, kind="bmatrix"):
    body = r" \\ ".join(" & ".join(str(v) for v in row) for row in rows)
    return rf"\begin{{{kind}}} {body} \end{{{kind}}}"


def _det3(m):
    """Determinant of a 3x3 matrix and its first-row cofactor expansion."""
    (a, b, c), (d, e, f), (g, h, i) = m
    minors = (e * i - f * h, d * i - f * g, d * h - e * g)
    value = a * minors[0] - b * minors[1] + c * minors[2]
    expansion = f"{a}({minors[0]}) - {paren(b)}({minors[1]}) + {paren(c)}({minors[2]})"
    return value, expansion


@register
@with_variants
def alg2_evaluate_polynomial(min_degree=2, max_degree=3, min_x=-5, max_x=5):
    r"""Evaluate a Polynomial at a Value

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $p(x)=2x^2+3x-1$ at $x=4$ | $43$ |
    """
    coeffs = _random_poly(min_degree, max_degree)
    x = random.randint(min_x, max_x)
    value = _eval_coeffs(coeffs, x)
    poly = _format_polynomial(_coeffs_to_terms(coeffs))
    problem = f"Evaluate $p(x)={poly}$ at $x={x}$"
    solution = f"${value}$"

    s = Steps()
    _evaluate_steps(s, "p", coeffs, x)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_polynomial_division(min_degree=2, max_degree=3, max_root=5):
    r"""Polynomial Division by a Linear Factor

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Divide $p(x)=x^2+5x+6$ by $(x-2)$ | quotient $x+7$, remainder $20$ |
    """
    coeffs = _random_poly(min_degree, max_degree)
    r = random.choice([n for n in range(-max_root, max_root + 1) if n != 0])
    quotient, remainder = _synthetic_division(coeffs, r)
    poly = _format_polynomial(_coeffs_to_terms(coeffs))
    q_str = _format_polynomial(_coeffs_to_terms(quotient))
    problem = (
        f"Divide $p(x)={poly}$ by $({_divisor_str(r)})$. "
        f"Format your answer as 'quotient ..., remainder ...'."
    )
    solution = f"quotient ${q_str}$, remainder ${remainder}$"

    s = Steps()
    if r > 0:
        which = f"Dividing by $({_divisor_str(r)})$ means using ${r}$."
    else:
        which = f"Since $({_divisor_str(r)})$ is $x-({r})$, use ${r}$."
    missing = ", with $0$ for each missing power" if 0 in coeffs else ""
    s.step(f"Use synthetic division. {which} Write the coefficients of $p(x)${missing}:",
           r" \quad ".join(str(c) for c in coeffs))
    rows, prev = [], coeffs[0]
    for c in coeffs[1:]:
        rows.append(rf"{c} + {paren(prev)} \cdot {paren(r)} &= {c + prev * r}")
        prev = c + prev * r
    s.step(f"Bring down the leading coefficient ${coeffs[0]}$. Then repeatedly multiply by "
           f"${r}$ and add the result to the next coefficient:",
           r"\begin{aligned} " + r" \\ ".join(rows) + r" \end{aligned}")
    s.step(f"The last value, ${remainder}$, is the remainder. The other values are the "
           f"coefficients of the quotient, one degree lower than $p(x)$.",
           f"q(x) = {q_str}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_remainder_theorem(min_degree=2, max_degree=3, max_root=5):
    r"""Remainder Theorem

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the remainder when $p(x)=x^2+5x+6$ is divided by $(x-2)$ | $20$ |
    """
    coeffs = _random_poly(min_degree, max_degree)
    r = random.choice([n for n in range(-max_root, max_root + 1) if n != 0])
    poly = _format_polynomial(_coeffs_to_terms(coeffs))
    remainder = _eval_coeffs(coeffs, r)
    problem = (
        f"Find the remainder when $p(x)={poly}$ is divided by $({_divisor_str(r)})$"
    )
    solution = f"${remainder}$"

    s = Steps()
    which = "" if r > 0 else f" Here $({_divisor_str(r)})$ is $x-({r})$."
    s.step(f"By the Remainder Theorem, the remainder when $p(x)$ is divided by $(x-r)$ is "
           f"$p(r)$.{which} So evaluate $p({r})$.")
    _evaluate_steps(s, "p", coeffs, r)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_build_polynomial_from_roots(min_root=-4, max_root=4):
    r"""Build a Polynomial from Its Roots

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find a monic polynomial in standard form with roots $2$, $-3$, and $1$ | $x^3-7x+6$ |
    """
    count = random.choice([2, 3])
    roots = [random.randint(min_root, max_root) for _ in range(count)]

    coeffs = [1]  # start with the polynomial "1"
    for root in roots:
        shifted = coeffs + [0]
        scaled = [0] + [c * (-root) for c in coeffs]
        coeffs = [s + t for s, t in zip(shifted, scaled)]

    poly = _format_polynomial(_coeffs_to_terms(coeffs))
    if count == 2:
        roots_text = f"${roots[0]}$ and ${roots[1]}$"
    else:
        roots_text = f"${roots[0]}$, ${roots[1]}$, and ${roots[2]}$"
    problem = f"Find a monic polynomial in standard form with roots {roots_text}"
    solution = f"${poly}$"

    s = Steps()
    # Multiply the nonzero-root factors first; a root of 0 just contributes x
    # (written in front, as in x(x-3)(x+3)).
    zeros, nonzeros = [r for r in roots if r == 0], [r for r in roots if r != 0]
    order = nonzeros + zeros
    factored = "".join(_root_factor(r) for r in zeros + nonzeros)
    s.step("Each root $r$ gives a factor $(x-r)$, so multiply one factor per root:",
           f"p(x) = {factored}")
    product = [1, -order[0]]
    for root in order[1:]:
        product = _multiply_out_step(s, product, root)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_add_complex(min_val=-9, max_val=9):
    r"""Add and Subtract Complex Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $(3+2i)+(1-4i)$ | $4-2i$ |
    """
    while True:
        a = random.randint(min_val, max_val)
        b = random.choice([n for n in range(min_val, max_val + 1) if n != 0])
        c = random.randint(min_val, max_val)
        d = random.choice([n for n in range(min_val, max_val + 1) if n != 0])
        operator = random.choice(["+", "-"])
        if operator == "+":
            p, q = a + c, b + d
        else:
            p, q = a - c, b - d
        if p != 0 and q != 0:
            break

    problem = (
        f"Simplify $({_complex_str(a, b)}){operator}({_complex_str(c, d)})$. "
        f"Format your answer as such: 4-2i."
    )
    solution = f"${_complex_result_str(p, q)}$"

    s = Steps()
    if operator == "+":
        s.step("Add the real parts and the imaginary parts separately.")
    else:
        s.step("Subtract the real parts and the imaginary parts separately. The minus sign "
               "applies to both parts of the second number.")
    s.step("Real parts:", f"{a} {operator} {paren(c)} = {p}")
    s.step("Imaginary parts (the coefficients of $i$):", f"{b} {operator} {paren(d)} = {q}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_rational_exponent(min_m=2, max_m=5):
    r"""Rational Exponents

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $27^{2/3}$ | $9$ |
    """
    q = random.choice([2, 3])
    p = random.choice([pp for pp in (1, 2, 3) if pp != q])  # gcd(p, q) == 1
    m = random.randint(min_m, max_m)
    base = m ** q  # perfect q-th power so base^(p/q) is exactly m^p
    value = m ** p
    problem = f"Evaluate ${base}^{{{p}/{q}}}$"
    solution = f"${value}$"

    s = Steps()
    if q == 2:
        root_name, root_tex = "square root", rf"\sqrt{{{base}}}"
    else:
        root_name, root_tex = "cube root", rf"\sqrt[3]{{{base}}}"
    s.step("A rational exponent means a root, then a power:",
           r"a^{p/q} = \left(\sqrt[q]{a}\right)^{p}")
    s.step(f"The denominator ${q}$ means take the {root_name} of ${base}$. "
           f"Since ${m}^{{{q}}} = {base}$:", f"{root_tex} = {m}")
    s.step(f"The numerator ${p}$ is the power. Raise ${m}$ to it:", f"{m}^{{{p}}} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_solve_radical_equation(max_a=4, min_x=-5, max_x=5, max_c=8):
    r"""Solve a Radical Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $\sqrt{2x+3}=5$ for x | $x=11$ |
    """
    a = random.choice([n for n in range(-max_a, max_a + 1) if n != 0])
    x = random.randint(min_x, max_x)
    c = random.randint(0, max_c)  # c >= 0 so no extraneous root by construction
    b = c * c - a * x
    inside = f"{a}x{'+' if b >= 0 else '-'}{abs(b)}"
    problem = rf"Solve $\sqrt{{{inside}}}={c}$ for x"
    solution = f"$x={x}$"

    s = Steps()
    s.step("Square both sides to remove the square root.",
           f"{_format_polynomial([(a, 1), (b, 0)])} = {c * c}")
    if b > 0:
        s.step(f"Subtract ${b}$ from both sides.", f"{_linear([(a, 'x')])} = {c * c - b}")
    elif b < 0:
        s.step(f"Add ${-b}$ to both sides.", f"{_linear([(a, 'x')])} = {c * c - b}")
    if a != 1:
        s.step(f"Divide both sides by ${a}$.", f"x = {x}")
    s.step(rf"Check: substituting $x={x}$ gives $\sqrt{{{c * c}}} = {c}$, which matches the "
           f"right side, so the solution is not extraneous.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_solve_exponential_log(min_x=1, max_x=5):
    r"""Solve an Exponential Equation with Logarithms

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $2^x=32$ for x | $x=5$ |
    """
    base = random.choice([2, 3, 5, 10])
    x = random.randint(min_x, max_x)
    value = base ** x
    problem = f"Solve ${base}^x={value}$ for x"
    solution = f"$x={x}$"

    s = Steps()
    s.step(f"Write ${value}$ as a power of ${base}$.", f"{base}^x = {base}^{{{x}}}")
    s.step(rf"The bases are equal, so the exponents are equal. (Equivalently, take "
           rf"$\log_{{{base}}}$ of both sides.)", f"x = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_evaluate_log(min_exp=1, max_exp=5):
    r"""Evaluate a Logarithm

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\log_{2}(32)$ | $5$ |
    """
    base = random.choice([2, 3, 5, 10])
    exponent = random.randint(min_exp, max_exp)
    n = base ** exponent
    problem = rf"Evaluate $\log_{{{base}}}({n})$"
    solution = f"${exponent}$"

    s = Steps()
    s.step(rf"$\log_{{{base}}}({n})$ asks: what power of ${base}$ gives ${n}$?",
           f"{base}^{{?}} = {n}")
    power = f"{base}^{{{exponent}}}"
    if exponent > 1:
        power += " = " + r" \cdot ".join([str(base)] * exponent)
    s.step(f"The power ${exponent}$ works:", f"{power} = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_inverse_linear_function(max_m=6, max_b=10, min_t=-6, max_t=6):
    r"""Inverse of a Linear Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $f(x)=2x+3$, find $f^{-1}(11)$ | $4$ |
    """
    m = random.choice([n for n in range(-max_m, max_m + 1) if n != 0])
    b = random.choice([n for n in range(-max_b, max_b + 1) if n != 0])
    t = random.randint(min_t, max_t)  # the answer: f^{-1}(a) = t
    a = m * t + b
    problem = (
        f"Given $f(x)={m}x{'+' if b >= 0 else '-'}{abs(b)}$, find $f^{{-1}}({a})$"
    )
    solution = f"${t}$"

    s = Steps()
    s.step(f"$f^{{-1}}({a})$ is the input $x$ that $f$ sends to ${a}$, so solve $f(x)={a}$.",
           f"{_format_polynomial([(m, 1), (b, 0)])} = {a}")
    move = f"Subtract ${b}$ from" if b > 0 else f"Add ${-b}$ to"
    s.step(f"{move} both sides.", f"{_linear([(m, 'x')])} = {a - b}")
    if m != 1:
        s.step(f"Divide both sides by ${m}$.", f"x = {t}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_z_score(min_val=-20, max_val=20):
    r"""Z-Score

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | A value of $18$ comes from a distribution with mean $10$ and standard deviation $4$. Find its z-score. | $2$ |
    """
    mean = random.randint(min_val, max_val)
    sd = random.choice([1, 2, 4, 5, 8, 10])  # all give a terminating <=3dp z
    x = random.randint(min_val, max_val)
    z = (x - mean) / sd
    problem = (
        f"A value of ${x}$ comes from a distribution with mean ${mean}$ and "
        f"standard deviation ${sd}$. Find its z-score. "
        f"Round your answer to the nearest thousandth."
    )
    solution = f"${_clean_num(z)}$"

    s = Steps()
    s.formula("The z-score formula", r"z = \frac{x - \mu}{\sigma}")
    s.substitute(rf"z = \frac{{{x} - {paren(mean)}}}{{{sd}}}",
                 text=rf"Substitute $x = {x}$, $\mu = {mean}$, and $\sigma = {sd}$.")
    s.step("Subtract in the numerator.", rf"z = {tex_frac(x - mean, sd)}")
    s.step("Divide.", f"z = {_clean_num(z)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_empirical_rule(min_mean=0, max_mean=100, min_sd=1, max_sd=15):
    r"""Empirical Rule (68-95-99.7)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | In a normal distribution with mean $50$ and standard deviation $5$, approximately what percent of the data lies within $2$ standard deviation(s) of the mean? | 95% |
    """
    mean = random.randint(min_mean, max_mean)
    sd = random.randint(min_sd, max_sd)
    k = random.choice([1, 2, 3])
    percent = {1: "68%", 2: "95%", 3: "99.7%"}[k]
    problem = (
        f"In a normal distribution with mean ${mean}$ and standard deviation "
        f"${sd}$, approximately what percent of the data lies within ${k}$ "
        f"standard deviation(s) of the mean?"
    )
    solution = percent

    s = Steps()
    s.step("The Empirical Rule says that in a normal distribution, about 68% of the data lies "
           "within $1$ standard deviation of the mean, 95% within $2$, and 99.7% within $3$.")
    s.step(rf"Here ${k}$ standard deviation(s) is ${k} \cdot {sd} = {k * sd}$, so this is the "
           f"data between:",
           rf"{mean} - {k * sd} = {mean - k * sd} \quad\text{{and}}\quad "
           rf"{mean} + {k * sd} = {mean + k * sd}")
    # Not s.answer: it would wrap "68%" in $...$, where % starts a LaTeX comment.
    s.step(f"Within ${k}$ standard deviation(s), the answer is {percent}.")
    return problem, solution, s.done()


@register
@with_variants
def alg2_solve_system_matrix(max_coeff=5, min_sol=-6, max_sol=6):
    r"""Solve a 2x2 Linear System

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the system: $2x+3y=13$ and $1x-1y=1$ | $x=... , y=...$ |
    """
    nonzero = [n for n in range(-max_coeff, max_coeff + 1) if n != 0]
    while True:
        a, b, c, d = (random.choice(nonzero) for _ in range(4))
        if a * d - b * c != 0:
            break
    x = random.randint(min_sol, max_sol)
    y = random.randint(min_sol, max_sol)
    e = a * x + b * y
    f = c * x + d * y
    eq1 = f"{a}x{_signed(b, 'y')}={e}"
    eq2 = f"{c}x{_signed(d, 'y')}={f}"
    problem = (
        f"Solve the system: ${eq1}$ and ${eq2}$. "
        f"Format your answer as such: x=1, y=2."
    )
    solution = f"$x={x}, y={y}$"

    s = Steps()
    # Scale both equations so the x-coefficients match, then subtract.
    target = lcm(abs(a), abs(c))
    m1, m2 = target // a, target // c
    ky, rhs = b * m1 - d * m2, e * m1 - f * m2
    scaled = [f"{_linear([(m * a_, 'x'), (m * b_, 'y')])} &= {m * e_}"
              for m, a_, b_, e_ in ((m1, a, b, e), (m2, c, d, f))]
    multiply = [f"the {which} equation by ${m}$"
                for which, m in (("first", m1), ("second", m2)) if m != 1]
    if multiply:
        s.step(f"To eliminate $x$, multiply {' and '.join(multiply)} so both $x$-coefficients "
               f"are ${target}$.",
               r"\begin{aligned} " + r" \\ ".join(scaled) + r" \end{aligned}")
        s.step("Subtract the second equation from the first. The $x$-terms cancel.",
               f"{_linear([(ky, 'y')])} = {rhs}")
    else:
        s.step("The $x$-coefficients already match, so subtract the second equation from the "
               "first to eliminate $x$.", f"{_linear([(ky, 'y')])} = {rhs}")
    if ky != 1:
        s.step(f"Divide both sides by ${ky}$.", f"y = {y}")
    by = f"{'+' if b > 0 else '-'}{'' if abs(b) == 1 else abs(b)}({y})"
    lines = [f"{_linear([(a, 'x')])}{by} &= {e}", f"{_linear([(a, 'x')])} &= {e - b * y}"]
    if a != 1:
        lines.append(f"x &= {x}")
    s.step(f"Substitute $y = {y}$ into the first equation and solve for $x$.",
           r"\begin{aligned} " + r" \\ ".join(lines) + r" \end{aligned}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_log_product_rule(min_val=-6, max_val=6):
    r"""Logarithm Product Rule

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $\log_b(x)=3$ and $\log_b(y)=2$, find $\log_b(xy)$ | $5$ |

    Applies $\log_b(xy)=\log_b(x)+\log_b(y)$. The two given values are small
    integers, so the answer is a clean integer.
    """
    p = random.randint(min_val, max_val)
    q = random.randint(min_val, max_val)
    problem = (
        f"Using the product rule for logarithms: given $\\log_b(x)={p}$ and "
        f"$\\log_b(y)={q}$, find $\\log_b(xy)$."
    )
    solution = f"${p + q}$"

    s = Steps()
    s.formula("The product rule for logarithms", r"\log_b(xy) = \log_b(x) + \log_b(y)")
    s.substitute(rf"\log_b(xy) = {p} + {paren(q)}")
    s.step("Add.", rf"\log_b(xy) = {p + q}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_log_quotient_rule(min_val=-6, max_val=6):
    r"""Logarithm Quotient Rule

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $\log_b(x)=7$ and $\log_b(y)=3$, find $\log_b(x/y)$ | $4$ |

    Applies $\log_b(x/y)=\log_b(x)-\log_b(y)$.
    """
    p = random.randint(min_val, max_val)
    q = random.randint(min_val, max_val)
    problem = (
        f"Using the quotient rule for logarithms: given $\\log_b(x)={p}$ and "
        f"$\\log_b(y)={q}$, find $\\log_b(x/y)$."
    )
    solution = f"${p - q}$"

    s = Steps()
    s.formula("The quotient rule for logarithms",
              r"\log_b\left(\frac{x}{y}\right) = \log_b(x) - \log_b(y)")
    s.substitute(rf"\log_b\left(\frac{{x}}{{y}}\right) = {p} - {paren(q)}")
    s.step("Subtract.", rf"\log_b\left(\frac{{x}}{{y}}\right) = {p - q}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_log_power_rule(min_val=-5, max_val=5, min_k=2, max_k=5):
    r"""Logarithm Power Rule

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $\log_b(x)=3$, find $\log_b(x^{4})$ | $12$ |

    Applies $\log_b(x^{k})=k\,\log_b(x)$.
    """
    p = random.choice([n for n in range(min_val, max_val + 1) if n != 0])
    k = random.randint(min_k, max_k)
    problem = (
        f"Using the power rule for logarithms: given $\\log_b(x)={p}$, find "
        f"$\\log_b(x^{{{k}}})$."
    )
    solution = f"${k * p}$"

    s = Steps()
    s.formula("The power rule for logarithms", r"\log_b(x^{k}) = k \cdot \log_b(x)")
    s.substitute(rf"\log_b(x^{{{k}}}) = {k} \cdot {paren(p)}")
    s.step("Multiply.", rf"\log_b(x^{{{k}}}) = {k * p}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_log_change_of_base(min_arg=2, max_arg=50):
    r"""Change of Base Formula

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Use the change of base formula to evaluate $\log_{5}(20)$ | $1.861$ |

    Applies $\log_b(n)=\dfrac{\ln n}{\ln b}$. The argument is chosen so it is
    *not* an exact power of the base, so the change of base formula is genuinely
    needed and the answer is an irrational decimal.
    """
    base = random.choice([2, 3, 5, 6, 7])
    while True:
        n = random.randint(min_arg, max_arg)
        value = log(n) / log(base)
        if abs(value - round(value)) > 1e-6:
            break
    problem = (
        f"Use the change of base formula to evaluate $\\log_{{{base}}}({n})$. "
        f"Round your answer to the nearest thousandth."
    )
    solution = f"${_num(value)}$"

    s = Steps()
    s.formula("The change of base formula", r"\log_b(n) = \frac{\ln n}{\ln b}")
    s.substitute(rf"\log_{{{base}}}({n}) = \frac{{\ln {n}}}{{\ln {base}}}")
    s.step(rf"Use a calculator: $\ln {n} \approx {_num(log(n))}$ and "
           rf"$\ln {base} \approx {_num(log(base))}$.")
    s.step("Divide, using the unrounded logarithms to avoid rounding error.",
           rf"\log_{{{base}}}({n}) \approx {_num(value)}")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def alg2_rationalize_denominator():
    r"""Rationalize a Denominator Using the Conjugate

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Rationalize $\frac{1}{\sqrt{7}-\sqrt{3}}$; give the resulting denominator | $4$ |

    Multiplying by the conjugate turns the denominator into a difference of
    squares, an integer. The student reports that rational denominator. Radicands
    are small non-squares, so the result stays small.
    """
    form = random.choice(["two_radicals", "radical_minus_int", "int_minus_radical"])
    if form == "two_radicals":
        a, b = random.sample(_NON_SQUARES, 2)
        denom = f"\\sqrt{{{a}}}-\\sqrt{{{b}}}"
        result = a - b
        first, second = rf"\sqrt{{{a}}}", rf"\sqrt{{{b}}}"
        squares = f"{a} - {b}"
    elif form == "radical_minus_int":
        a = random.choice(_NON_SQUARES)
        d = random.randint(1, 4)
        denom = f"\\sqrt{{{a}}}-{d}"
        result = a - d * d
        first, second = rf"\sqrt{{{a}}}", str(d)
        squares = f"{a} - {d * d}"
    else:  # int_minus_radical
        a = random.choice(_NON_SQUARES)
        d = random.randint(1, 4)
        denom = f"{d}-\\sqrt{{{a}}}"
        result = d * d - a
        first, second = str(d), rf"\sqrt{{{a}}}"
        squares = f"{d * d} - {a}"
    problem = (
        f"Rationalize the denominator of $\\frac{{1}}{{{denom}}}$ by multiplying "
        f"by the conjugate. What is the resulting rational denominator (an "
        f"integer)?"
    )
    solution = f"${result}$"

    s = Steps()
    conjugate = f"{first}+{second}"
    s.step(f"The conjugate of ${denom}$ is ${conjugate}$. Multiply the numerator and "
           f"denominator by it.",
           rf"\frac{{1}}{{{denom}}} \cdot \frac{{{conjugate}}}{{{conjugate}}}")
    s.formula("The denominator is a difference of squares, and the rule", r"(p-q)(p+q) = p^2 - q^2")
    s.step("Apply it. Squaring removes the square roots.",
           rf"({denom})({conjugate}) = ({first})^2 - ({second})^2 = {squares} = {result}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_radical_equation_conjugate(min_root=2, max_root=6):
    r"""Solve a Radical Equation Using the Conjugate

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $\sqrt{x+13}-\sqrt{x+6}=1$ for x | $x=3$ |

    Built so both radicands are perfect squares at the solution, so multiplying
    by the conjugate (or squaring) yields a clean integer x. The two radicands
    equal $P^2$ and $Q^2$ at the answer; the right side is $P\pm Q$.
    """
    big = random.randint(min_root + 1, max_root)          # P
    small = random.randint(1, big - 1)                     # Q, strictly < P
    x = random.randint(0, small * small - 1)               # so b = Q^2 - x >= 1
    a = big * big - x                                       # x + a = P^2
    b = small * small - x                                   # x + b = Q^2
    op = random.choice(["+", "-"])
    c = big + small if op == "+" else big - small
    problem = (
        f"Solve $\\sqrt{{x+{a}}} {op} \\sqrt{{x+{b}}} = {c}$ for x."
    )
    solution = f"$x={x}$"

    s = Steps()
    other_op = "-" if op == "+" else "+"
    root_a, root_b = rf"\sqrt{{x+{a}}}", rf"\sqrt{{x+{b}}}"
    conjugate = f"{root_a} {other_op} {root_b}"
    other = (a - b) // c  # (P^2 - Q^2) / (P +- Q) = P -+ Q, exactly
    s.step(f"Multiply both sides by the conjugate ${conjugate}$. The left side becomes a "
           f"difference of squares.",
           rf"(x+{a}) - (x+{b}) = {c}\left({conjugate}\right)")
    divide = "" if c == 1 else f", then divide both sides by ${c}$"
    s.step(f"Simplify the left side to ${a - b}${divide}.", f"{conjugate} = {other}")
    s.step(f"Add this to the original equation. The ${root_b}$ terms cancel.",
           rf"2{root_a} = {c + other} \quad\Rightarrow\quad {root_a} = {big}")
    s.step("Square both sides and solve for $x$.",
           rf"x + {a} = {big * big} \quad\Rightarrow\quad x = {x}")
    s.step(rf"Check: $\sqrt{{{x}+{a}}} {op} \sqrt{{{x}+{b}}} = {big} {op} {small} = {c}$, "
           f"which matches.")
    s.answer(solution)
    return problem, solution, s.done()


def _linear_factor(k):
    """Signed linear factor text: k=2 -> 'x+2', k=-3 -> 'x-3' (k assumed nonzero)."""
    return f"x{'+' if k > 0 else '-'}{abs(k)}"


@register
@with_variants
def alg2_function_composition(min_c=-5, max_c=5, min_x=-4, max_x=4):
    r"""Function Composition

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Given $f(x)=2x+3$ and $g(x)=x^2-1$, find $(f \circ g)(2)$ | $9$ |

    ``f`` is linear and ``g`` is linear or quadratic; the answer is the integer
    $(f \circ g)(x_0)=f(g(x_0))$ evaluated at a small integer point.
    """
    nonzero = [n for n in range(min_c, max_c + 1) if n != 0]
    # f(x) = a x + b, a nonzero.
    a = random.choice(nonzero)
    b = random.randint(min_c, max_c)
    f_coeffs = [a, b]
    # g(x): linear a2 x + b2, or quadratic a2 x^2 + b2 x + c2.
    if random.random() < 0.5:
        a2 = random.choice(nonzero)
        b2 = random.randint(min_c, max_c)
        g_coeffs = [a2, b2]
    else:
        a2 = random.choice(nonzero)
        b2 = random.randint(min_c, max_c)
        c2 = random.randint(min_c, max_c)
        g_coeffs = [a2, b2, c2]
    x0 = random.randint(min_x, max_x)
    inner = _eval_coeffs(g_coeffs, x0)
    value = _eval_coeffs(f_coeffs, inner)
    f_str = _format_polynomial(_coeffs_to_terms(f_coeffs))
    g_str = _format_polynomial(_coeffs_to_terms(g_coeffs))
    problem = (
        f"Given $f(x)={f_str}$ and $g(x)={g_str}$, find $(f \\circ g)({x0})$"
    )
    solution = f"${value}$"

    s = Steps()
    s.step(rf"$(f \circ g)({x0})$ means $f(g({x0}))$. Work from the inside out: find "
           f"$g({x0})$ first.")
    _evaluate_steps(s, "g", g_coeffs, x0)
    outer = f"f({inner}) = {_subst_poly(f_coeffs, inner)}"
    if b != 0:
        outer += f" = {_sum_str([a * inner, b])}"
    s.step(f"Now substitute $g({x0}) = {inner}$ into $f$.", f"{outer} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_solve_rational_equation(min_v=-6, max_v=6, min_s=-5, max_s=5):
    r"""Solve a Rational Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $\frac{5}{x+2} = \frac{7}{x+4}$ for x. Express your answer as a fraction a/b or an integer. | $x=3$ |

    The two denominators differ and are nonzero at the solution, so the root is
    genuine (not extraneous). Answer is a reduced fraction or integer.
    """
    nonzero = [n for n in range(min_v, max_v + 1) if n != 0]
    for _ in range(200):
        s = random.randint(min_s, max_s)          # the true solution
        p = random.choice(nonzero)
        q = random.choice(nonzero)
        if p == q:
            continue
        a = s + p                                  # = value of (x+p) at the root
        c = s + q                                  # = value of (x+q) at the root
        if a == 0 or c == 0 or a == c:
            continue
        break
    else:  # deterministic fallback
        s, p, q, a, c = 3, 2, 4, 5, 7
    problem = (
        f"Solve $\\frac{{{a}}}{{{_linear_factor(p)}}} = "
        f"\\frac{{{c}}}{{{_linear_factor(q)}}}$ for x. "
        f"Express your answer as a fraction a/b or an integer."
    )
    solution = f"$x={_frac_from(s)}$"

    st = Steps()
    st.step("Cross-multiply.", f"{a}({_linear_factor(q)}) = {c}({_linear_factor(p)})")
    st.step("Distribute.",
            f"{_format_polynomial([(a, 1), (a * q, 0)])} = {_format_polynomial([(c, 1), (c * p, 0)])}")
    st.step("Move the $x$-terms to the left side and the constants to the right.",
            f"{_linear([(a - c, 'x')])} = {c * p - a * q}")
    if a - c != 1:
        st.step(f"Divide both sides by ${a - c}$.", f"x = {_frac_from(s)}")
    st.step(f"Check: $x={_frac_from(s)}$ makes the denominators ${s + p}$ and ${s + q}$, "
            f"neither of which is zero, so the solution is valid.")
    st.answer(solution)
    return problem, solution, st.done()


@register
@with_variants
def alg2_rational_expression_ops(min_c=-6, max_c=6):
    r"""Rational Expression Operations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $\frac{x+2}{x-1} \cdot \frac{x-1}{x+5}$. Give your answer as a simplified rational expression, e.g. (x+1)/(x-2). | $(x+2)/(x+5)$ |

    Multiplying or dividing two rational expressions built from linear factors
    cancels a common factor, leaving $(x+a)/(x+c)$.
    """
    nonzero = [n for n in range(min_c, max_c + 1) if n != 0]
    a, b, c = random.sample(nonzero, 3)
    op = random.choice(["\\cdot", "\\div"])
    if op == "\\cdot":
        # (x+a)/(x+b) * (x+b)/(x+c) -> (x+a)/(x+c)
        expr = (
            f"\\frac{{{_linear_factor(a)}}}{{{_linear_factor(b)}}} \\cdot "
            f"\\frac{{{_linear_factor(b)}}}{{{_linear_factor(c)}}}"
        )
    else:
        # (x+a)/(x+b) / ((x+c)/(x+b)) -> (x+a)/(x+c)
        expr = (
            f"\\frac{{{_linear_factor(a)}}}{{{_linear_factor(b)}}} \\div "
            f"\\frac{{{_linear_factor(c)}}}{{{_linear_factor(b)}}}"
        )
    problem = (
        f"Simplify ${expr}$. Give your answer as a simplified rational "
        f"expression, e.g. (x+1)/(x-2)."
    )
    solution = f"$({_linear_factor(a)})/({_linear_factor(c)})$"

    s = Steps()
    fa, fb, fc = _linear_factor(a), _linear_factor(b), _linear_factor(c)
    if op == "\\div":
        s.step("Dividing by a fraction means multiplying by its reciprocal.",
               rf"\frac{{{fa}}}{{{fb}}} \cdot \frac{{{fb}}}{{{fc}}}")
    s.step("Multiply the numerators and multiply the denominators.",
           rf"\frac{{({fa})({fb})}}{{({fb})({fc})}}")
    s.step(f"Cancel the common factor $({fb})$.", rf"\frac{{{fa}}}{{{fc}}}")
    s.answer(solution, lead="Written with a slash, the answer is")
    return problem, solution, s.done()


def _imag_str(mag_fraction):
    """'i', '-i', or '<frac>i' for an imaginary coefficient given |coeff| text."""
    return "i" if mag_fraction == "1" else f"{mag_fraction}i"


@register
@with_variants
def alg2_complex_division(min_v=-6, max_v=6):
    r"""Complex Number Division

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Simplify $(3+2i)/(1-2i)$. Format as a+bi (fractions allowed, like 3/5-1/5i). | $-1/5+8/5i$ |

    Multiply by the conjugate of the denominator; the real and imaginary parts
    are reduced fractions (or integers).
    """
    nonzero = [n for n in range(min_v, max_v + 1) if n != 0]
    for _ in range(200):
        a = random.randint(min_v, max_v)
        b = random.choice(nonzero)
        c = random.randint(min_v, max_v)
        d = random.choice(nonzero)
        denom = c * c + d * d
        real = Fraction(a * c + b * d, denom)
        imag = Fraction(b * c - a * d, denom)
        if real != 0 and imag != 0:
            break
    else:  # deterministic fallback: (3+2i)/(1-2i)
        a, b, c, d = 3, 2, 1, -2
        denom = c * c + d * d
        real = Fraction(a * c + b * d, denom)
        imag = Fraction(b * c - a * d, denom)
    problem = (
        f"Simplify $({_complex_str(a, b)})/({_complex_str(c, d)})$. "
        f"Format as a+bi (fractions allowed, like 3/5-1/5i)."
    )
    real_str = _frac_from(real)
    sign = "+" if imag > 0 else "-"
    imag_str = _imag_str(_frac_from(abs(imag)))
    solution = f"${real_str}{sign}{imag_str}$"

    s = Steps()
    num_z, den_z, conj = _complex_str(a, b), _complex_str(c, d), _complex_str(c, -d)
    s.step(f"Multiply the numerator and denominator by ${conj}$, the conjugate of the "
           f"denominator.",
           rf"\frac{{{num_z}}}{{{den_z}}} \cdot \frac{{{conj}}}{{{conj}}}")
    foil = [(a * c, ""), (-a * d, "i"), (b * c, "i"), (-b * d, "i^2")]
    expanded = _join_signed([
        ("-" if v < 0 else "+", f"{'' if abs(v) == 1 and unit else abs(v)}{unit}")
        for v, unit in foil if v != 0
    ])
    s.step("Expand the numerator with FOIL.", f"({num_z})({conj}) = {expanded}")
    numerator = _complex_str(a * c + b * d, b * c - a * d)
    s.step("Replace $i^2$ with $-1$ and combine like terms.", f"({num_z})({conj}) = {numerator}")
    s.step("Multiply out the denominator, using $(c+di)(c-di) = c^2+d^2$.",
           f"({den_z})({conj}) = {paren(c)}^2 + {paren(d)}^2 = {denom}")
    s.step("Divide each part by the denominator and simplify.",
           rf"\frac{{{numerator}}}{{{denom}}} = {_tex_fraction(real)} {sign} "
           rf"{_tex_fraction(abs(imag))}i")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_complex_modulus(min_v=-9, max_v=9):
    r"""Modulus of a Complex Number

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find $|3+4i|$. Round to the nearest thousandth if irrational. | $5$ |

    The modulus is $\sqrt{a^2+b^2}$; report it as an integer when it is a whole
    number, otherwise rounded to three decimal places.
    """
    nonzero = [n for n in range(min_v, max_v + 1) if n != 0]
    a = random.choice(nonzero)
    b = random.choice(nonzero)
    value = sqrt(a * a + b * b)
    problem = (
        f"Find $|{_complex_str(a, b)}|$. "
        f"Round to the nearest thousandth if irrational."
    )
    solution = f"${_num(value)}$"

    s = Steps()
    z, total = _complex_str(a, b), a * a + b * b
    s.formula("The modulus of $a+bi$", r"|a+bi| = \sqrt{a^2+b^2}")
    s.substitute(rf"|{z}| = \sqrt{{{paren(a)}^2 + {paren(b)}^2}}")
    s.step("Square and add.", rf"|{z}| = \sqrt{{{a * a} + {b * b}}} = \sqrt{{{total}}}")
    if isqrt(total) ** 2 == total:
        s.step(f"${total}$ is a perfect square.", rf"\sqrt{{{total}}} = {isqrt(total)}")
        s.answer(solution)
    else:
        s.step(f"${total}$ is not a perfect square, so use a calculator.",
               rf"\sqrt{{{total}}} \approx {_num(value)}")
        s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def alg2_inverse_nonlinear(min_v=-6, max_v=6):
    r"""Inverse of a Non-Linear Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the inverse of $f(x)=(x-2)^3+5$. Express your answer as an expression in x (write ^(1/3) for cube root), e.g. (x-5)^(1/3)+2. | $(x-5)^(1/3)+2$ |

    Inverting $y=(x-h)^3+k$ gives $f^{-1}(x)=(x-k)^{1/3}+h$.
    """
    nonzero = [n for n in range(min_v, max_v + 1) if n != 0]
    h = random.choice(nonzero)
    k = random.choice(nonzero)
    # f(x) = (x - h)^3 + k
    fx = f"({_linear_factor(-h)})^3{'+' if k > 0 else '-'}{abs(k)}"
    problem = (
        f"Find the inverse of $f(x)={fx}$. Express your answer as an expression "
        f"in x (write ^(1/3) for cube root), e.g. (x-5)^(1/3)+2."
    )
    # inverse: (x - k)^(1/3) + h
    solution = (
        f"$({_linear_factor(-k)})^(1/3){'+' if h > 0 else '-'}{abs(h)}$"
    )

    s = Steps()
    y_minus_h = _linear_factor(-h).replace("x", "y")
    k_term = f"{'+' if k > 0 else '-'}{abs(k)}"
    s.step("Replace $f(x)$ with $y$.", f"y = {fx}")
    s.step("Swap $x$ and $y$.", f"x = ({y_minus_h})^3{k_term}")
    move = f"Subtract ${k}$ from" if k > 0 else f"Add ${-k}$ to"
    s.step(f"{move} both sides.", f"{_linear_factor(-k)} = ({y_minus_h})^3")
    s.step("Take the cube root of both sides.", rf"\sqrt[3]{{{_linear_factor(-k)}}} = {y_minus_h}")
    move = f"Add ${h}$ to" if h > 0 else f"Subtract ${-h}$ from"
    s.step(f"{move} both sides. This is $f^{{-1}}(x)$.",
           rf"f^{{-1}}(x) = \sqrt[3]{{{_linear_factor(-k)}}}{'+' if h > 0 else '-'}{abs(h)}")
    s.answer(solution, lead="Writing the cube root as the power ^(1/3), the answer is")
    return problem, solution, s.done()


def _divisors(n):
    """Positive divisors of ``|n|`` in increasing order."""
    n = abs(n)
    return [d for d in range(1, n + 1) if n % d == 0]


@register
@with_variants
def alg2_rational_root_list():
    r"""Rational Root Theorem

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | List all possible rational roots of $2x^2+3x+3$ | 1/2, 1, 3/2, 3, -1/2, -1, -3/2, -3 |

    By the Rational Root Theorem the candidates are $\pm p/q$ where $p$ divides
    the constant term and $q$ divides the leading coefficient. Both are kept
    small so the candidate list stays short.
    """
    lead = random.choice([1, 2, 3])
    const = random.choice([2, 3, 4, 5, 6])
    degree = random.choice([2, 3])
    # middle coefficients are cosmetic; only lead and const drive the theorem.
    mids = [random.randint(-5, 5) for _ in range(degree - 1)]
    coeffs = [lead] + mids + [const]
    poly = _format_polynomial(_coeffs_to_terms(coeffs))

    positives = sorted({Fraction(p, q) for p in _divisors(const)
                        for q in _divisors(lead)})
    candidates = [_frac_from(c) for c in positives]
    candidates += [_frac_from(-c) for c in positives]
    problem = (
        f"List all possible rational roots of $p(x)={poly}$ given by the "
        f"Rational Root Theorem. List each candidate once as p/q (or an "
        f"integer), positive values in increasing order first, then their "
        f"negatives in the same order, separated by commas."
    )
    solution = ", ".join(candidates)

    s = Steps()
    s.step(rf"By the Rational Root Theorem, every rational root has the form "
           rf"$\pm\frac{{p}}{{q}}$, where $p$ divides the constant term ${const}$ and $q$ "
           rf"divides the leading coefficient ${lead}$.")
    s.step("List the factors of each.",
           rf"p: {', '.join(map(str, _divisors(const)))} \qquad q: {', '.join(map(str, _divisors(lead)))}")
    positives_tex = ", ".join(_tex_fraction(c) for c in positives)
    if lead == 1:
        s.step(r"Since $q$ can only be $1$, the positive candidates are just the factors of "
               f"${const}$:", positives_tex)
    else:
        s.step(r"Form every fraction $\frac{p}{q}$, reduce it, drop duplicates, and sort:",
               positives_tex)
    s.step("Each candidate can also be negative, so list the negatives after them in the "
           "same order.")
    s.answer(solution, lead="With the positives first and then the negatives, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def alg2_solve_system_three(max_coeff=3, min_sol=-4, max_sol=4):
    r"""System of Three Equations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve: $1x+1y+1z=6$; $2x-1y+1z=3$; $1x+2y-1z=1$ | $(1, 2, 3)$ |

    A 3x3 linear system with a unique small-integer solution. The coefficient
    matrix is guaranteed invertible.
    """
    coeff_range = [n for n in range(-max_coeff, max_coeff + 1)]
    x = random.randint(min_sol, max_sol)
    y = random.randint(min_sol, max_sol)
    z = random.randint(min_sol, max_sol)
    for _ in range(200):
        rows = [[random.choice(coeff_range) for _ in range(3)] for _ in range(3)]
        a, b, c = rows[0]
        d, e, f = rows[1]
        g, h, i = rows[2]
        det = (a * (e * i - f * h) - b * (d * i - f * g)
               + c * (d * h - e * g))
        if det != 0:
            break
    else:  # deterministic fallback: identity-like system
        rows = [[1, 1, 1], [2, -1, 1], [1, 2, -1]]
    eqs = []
    for (ca, cb, cc) in rows:
        d = ca * x + cb * y + cc * z
        eqs.append(f"{ca}x{_signed(cb, 'y')}{_signed(cc, 'z')}={d}")
    problem = (
        f"Solve the system: ${eqs[0]}$; ${eqs[1]}$; ${eqs[2]}$. "
        f"Format your answer as (x, y, z)."
    )
    solution = f"$({x}, {y}, {z})$"

    s = Steps()
    consts = [ca * x + cb * y + cc * z for ca, cb, cc in rows]
    det, expansion = _det3(rows)
    s.step("Use Cramer's rule. First find the determinant $D$ of the coefficient matrix, "
           "expanding along the first row.",
           f"D = {_matrix(rows, 'vmatrix')} = {expansion} = {det}")
    dets = []
    for col, var in enumerate("xyz"):
        replaced = [row[:col] + [k] + row[col + 1:] for row, k in zip(rows, consts)]
        value, expansion = _det3(replaced)
        dets.append(value)
        s.step(f"For $D_{var}$, replace the ${var}$-column with the constants "
               f"${', '.join(map(str, consts))}$.",
               f"D_{var} = {_matrix(replaced, 'vmatrix')} = {expansion} = {value}")
    s.step("Divide each by $D$.", r", \quad ".join(
        f"{var} = \\frac{{D_{var}}}{{D}} = {tex_frac(value, det)} = {answer}"
        for var, value, answer in zip("xyz", dets, (x, y, z))
    ))
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_matrix_operation(min_v=-6, max_v=6):
    r"""Matrix Operation (2x2)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Let $A=[[1, 2], [3, 4]]$ and $B=[[5, 6], [7, 8]]$. Compute A+B. Give the entry in row 1, column 2. | $8$ |

    Add or multiply two 2x2 integer matrices and report a single requested
    entry, so the answer is an integer.
    """
    A = [[random.randint(min_v, max_v) for _ in range(2)] for _ in range(2)]
    B = [[random.randint(min_v, max_v) for _ in range(2)] for _ in range(2)]
    op = random.choice(["add", "multiply"])
    i = random.choice([1, 2])
    j = random.choice([1, 2])
    if op == "add":
        entry = A[i - 1][j - 1] + B[i - 1][j - 1]
        verb = "Compute A+B."
    else:
        entry = sum(A[i - 1][k] * B[k][j - 1] for k in range(2))
        verb = "Compute the product AB."
    a_str = f"[[{A[0][0]}, {A[0][1]}], [{A[1][0]}, {A[1][1]}]]"
    b_str = f"[[{B[0][0]}, {B[0][1]}], [{B[1][0]}, {B[1][1]}]]"
    problem = (
        f"Let $A={a_str}$ and $B={b_str}$. {verb} "
        f"Give the entry in row {i}, column {j} (an integer)."
    )
    solution = f"${entry}$"

    s = Steps()
    s.step("Write the matrices.", rf"A = {_matrix(A)}, \quad B = {_matrix(B)}")
    if op == "add":
        s.step(f"To add matrices, add the entries in the same position. In row {i}, "
               f"column {j}:",
               f"{A[i - 1][j - 1]} + {paren(B[i - 1][j - 1])} = {entry}")
    else:
        row = A[i - 1]
        col = [B[0][j - 1], B[1][j - 1]]
        s.step(f"The row {i}, column {j} entry of $AB$ combines row {i} of $A$ with "
               f"column {j} of $B$.",
               rf"{_matrix([row])} \text{{ and }} {_matrix([[col[0]], [col[1]]])}")
        s.step("Multiply matching entries and add.",
               rf"{row[0]} \cdot {paren(col[0])} + {row[1]} \cdot {paren(col[1])} "
               f"= {row[0] * col[0]} + {paren(row[1] * col[1])} = {entry}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def alg2_solve_polynomial_factoring(min_root=-5, max_root=5):
    r"""Solve a Polynomial by Factoring

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $x^3-2x^2-5x+6=0$ by factoring. | -2, 1, 3 |

    A monic degree-3 polynomial with three distinct integer roots. The student
    lists the real roots from least to greatest.
    """
    roots = random.sample(range(min_root, max_root + 1), 3)
    coeffs = [1]
    for root in roots:
        shifted = coeffs + [0]
        scaled = [0] + [c * (-root) for c in coeffs]
        coeffs = [s + t for s, t in zip(shifted, scaled)]
    poly = _format_polynomial(_coeffs_to_terms(coeffs))
    problem = (
        f"Solve $p(x)={poly}=0$ by factoring. List the real roots from least "
        f"to greatest, separated by commas."
    )
    solution = ", ".join(str(r) for r in sorted(roots))

    s = Steps()
    # Pull out the root a student would find first: 0 if the constant term is
    # 0, else the smallest candidate (positive before negative).
    first = min(roots, key=lambda r: (abs(r), r < 0))
    rest = sorted(r for r in roots if r != first)
    quadratic = _poly(_synthetic_division(coeffs, first)[0])
    if first == 0:
        s.step("The constant term is $0$, so every term has a factor of $x$. Factor it out.",
               f"p(x) = x({quadratic})")
    else:
        s.step(f"By the Rational Root Theorem, any integer root divides the constant term "
               f"${coeffs[-1]}$. Testing these, $x={first}$ works:",
               f"p({first}) = {_subst_poly(coeffs, first)} = 0")
        s.step(f"So $({_divisor_str(first)})$ is a factor. Divide it out with synthetic division.",
               f"p(x) = ({_divisor_str(first)})({quadratic})")
    s.step(f"Factor ${quadratic}$: find two numbers that multiply to ${rest[0] * rest[1]}$ and add "
           f"to ${-(rest[0] + rest[1])}$. They are ${-rest[0]}$ and ${-rest[1]}$.",
           "p(x) = " + "".join(_root_factor(r) for r in [first] + rest))
    s.step("Set each factor equal to zero (Zero Product Property).",
           r", \quad ".join(f"x = {r}" for r in [first] + rest))
    s.answer(solution, lead="From least to greatest, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def alg2_conic_equation(min_axis=2, max_axis=8):
    r"""Conic Equation from Features

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | An ellipse centered at the origin has semi-axes a=3 along x and b=2 along y. | $x^2/9+y^2/4=1$ |

    Given the integer semi-axes ``a`` and ``b`` of an ellipse or a horizontally
    opening hyperbola centered at the origin, write the standard-form equation
    with integer denominators.
    """
    a = random.randint(min_axis, max_axis)
    b = random.choice([n for n in range(min_axis, max_axis + 1) if n != a])
    kind = random.choice(["ellipse", "hyperbola"])
    A = a * a
    B = b * b
    if kind == "ellipse":
        problem = (
            f"An ellipse centered at the origin has semi-axis a={a} along the "
            f"x-axis and semi-axis b={b} along the y-axis. Write its "
            f"standard-form equation as x^2/A+y^2/B=1 with integers A and B."
        )
        solution = f"$x^2/{A}+y^2/{B}=1$"
    else:
        problem = (
            f"A hyperbola centered at the origin opening left-right has "
            f"transverse semi-axis a={a} and conjugate semi-axis b={b}. Write "
            f"its standard-form equation as x^2/A-y^2/B=1 with integers A and B."
        )
        solution = f"$x^2/{A}-y^2/{B}=1$"

    s = Steps()
    sign = "+" if kind == "ellipse" else "-"
    if kind == "ellipse":
        s.formula("The standard form of an ellipse centered at the origin",
                  r"\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1")
    else:
        s.formula("The standard form of a left-right hyperbola centered at the origin",
                  r"\frac{x^2}{a^2} - \frac{y^2}{b^2} = 1")
    s.substitute(rf"\frac{{x^2}}{{{a}^2}} {sign} \frac{{y^2}}{{{b}^2}} = 1",
                 text=f"Substitute $a = {a}$ and $b = {b}$.")
    s.step("Square the semi-axes.", rf"\frac{{x^2}}{{{A}}} {sign} \frac{{y^2}}{{{B}}} = 1")
    s.answer(solution, lead="Written with slashes, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def alg2_polynomial_end_behavior(min_degree=2, max_degree=5):
    r"""End Behavior of a Polynomial

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Describe the end behavior of $p(x)=2x^3-x+1$. | -inf, inf |

    The end behavior is fixed by the leading term: the sign of the leading
    coefficient and the parity of the degree.
    """
    coeffs = _random_poly(min_degree, max_degree)
    degree = len(coeffs) - 1
    lead = coeffs[0]
    poly = _format_polynomial(_coeffs_to_terms(coeffs))
    right = "inf" if lead > 0 else "-inf"
    if degree % 2 == 0:
        left = right
    else:
        left = "-inf" if lead > 0 else "inf"
    problem = (
        f"Describe the end behavior of $p(x)={poly}$. As x -> -inf, y -> ? and "
        f"as x -> inf, y -> ? Answer with two values from {{inf, -inf}} "
        f"separated by a comma (the x -> -inf value first)."
    )
    solution = f"{left}, {right}"

    s = Steps()
    tex = {"inf": r"\infty", "-inf": r"-\infty"}
    s.step(f"For large $|x|$, the leading term ${_format_polynomial([(lead, degree)])}$ "
           f"controls the end behavior.")
    s.step(rf"The leading coefficient ${lead}$ is {'positive' if lead > 0 else 'negative'}, so "
           rf"the right end goes {'up' if lead > 0 else 'down'}: as $x \to \infty$, "
           rf"$y \to {tex[right]}$.")
    if degree % 2 == 0:
        s.step(rf"The degree ${degree}$ is even, so both ends go the same way: as "
               rf"$x \to -\infty$, $y \to {tex[left]}$.")
    else:
        s.step(rf"The degree ${degree}$ is odd, so the ends go opposite ways: as "
               rf"$x \to -\infty$, $y \to {tex[left]}$.")
    s.answer(solution, lead=r"Listing the $x \to -\infty$ value first, the answer is")
    return problem, solution, s.done()
