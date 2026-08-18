"""Solveki-local generators for Georgia Advanced Algebra: Concepts & Connections.

These fill computable gaps in the stock ``mathgenerator`` catalogue for the
"Advanced Algebra: Concepts & Connections" course. Every generator in this
module is named with an ``alg2_`` prefix, takes no required arguments, and
returns a ``(problem, solution)`` pair of LaTeX strings.
"""
import random
from math import copysign, log, sqrt
from fractions import Fraction

from ._registry import register
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


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, f"${p + q}$"


@register
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
    return problem, f"${p - q}$"


@register
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
    return problem, f"${k * p}$"


@register
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
    return problem, f"${_num(value)}$"


@register
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
    elif form == "radical_minus_int":
        a = random.choice(_NON_SQUARES)
        d = random.randint(1, 4)
        denom = f"\\sqrt{{{a}}}-{d}"
        result = a - d * d
    else:  # int_minus_radical
        a = random.choice(_NON_SQUARES)
        d = random.randint(1, 4)
        denom = f"{d}-\\sqrt{{{a}}}"
        result = d * d - a
    problem = (
        f"Rationalize the denominator of $\\frac{{1}}{{{denom}}}$ by multiplying "
        f"by the conjugate. What is the resulting rational denominator (an "
        f"integer)?"
    )
    return problem, f"${result}$"


@register
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
    return problem, f"$x={x}$"


def _linear_factor(k):
    """Signed linear factor text: k=2 -> 'x+2', k=-3 -> 'x-3' (k assumed nonzero)."""
    return f"x{'+' if k > 0 else '-'}{abs(k)}"


@register
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
    return problem, f"${value}$"


@register
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
    return problem, f"$x={_frac_from(s)}$"


@register
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
    return problem, solution


def _imag_str(mag_fraction):
    """'i', '-i', or '<frac>i' for an imaginary coefficient given |coeff| text."""
    return "i" if mag_fraction == "1" else f"{mag_fraction}i"


@register
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
    return problem, solution


@register
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
    return problem, f"${_num(value)}$"


@register
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
    return problem, solution


def _divisors(n):
    """Positive divisors of ``|n|`` in increasing order."""
    n = abs(n)
    return [d for d in range(1, n + 1) if n % d == 0]


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution


@register
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
    return problem, solution
