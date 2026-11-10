"""Extra question types for the Algebra II topics.

Variants for the generators in ``algebra2`` and for the library-override
generators the Algebra II course uses (``lib_algebra_extra_gen``,
``lib_seqstats_gen``, ``sets_gen``). Each attaches to its topic's dispatcher
(see ``_variants.with_variants``); the original question stays as the
``classic`` variant. Variants only use their own topic's skill. See
docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num
from ._steps import Steps, paren, tex_frac
from . import algebra2, lib_algebra_extra_gen, lib_seqstats_gen, sets_gen
from .prealgebra_variants import _table

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."
_ROUND = "Round your answer to the nearest thousandth."


def _nonzero(lo, hi):
    return random.choice([i for i in range(lo, hi + 1) if i != 0])


def _tex(value):
    v = Fraction(value)
    return str(v.numerator) if v.denominator == 1 else tex_frac(v.numerator, v.denominator)


def _poly(coeffs):
    """LaTeX for a polynomial from coefficients, highest degree first."""
    deg = len(coeffs) - 1
    out = ""
    for i, c in enumerate(coeffs):
        p = deg - i
        if c == 0:
            continue
        mag = abs(c)
        body = ("" if mag == 1 and p else str(mag)) + ("x" if p >= 1 else "") + (f"^{p}" if p >= 2 else "")
        if not out:
            out = ("-" if c < 0 else "") + body
        else:
            out += (" - " if c < 0 else " + ") + body
    return out or "0"


def _evaluate(coeffs, x):
    value = 0
    for c in coeffs:
        value = value * x + c
    return value


def _factor(r):
    """(x - r) in LaTeX."""
    return "x" if r == 0 else (f"(x - {r})" if r > 0 else f"(x + {-r})")


# --- Polynomials -------------------------------------------------------------------------

@algebra2.alg2_evaluate_polynomial.variant("coefficient_sum")
def _polynomial_coefficient_sum():
    """SAT-style: the sum of the coefficients is p(1); the constant term is p(0)."""
    factors = [(_nonzero(-4, 4), random.randint(1, 3)) for _ in range(2)]
    k = _nonzero(-3, 3)
    shown = (f"{k}" if k not in (1, -1) else ("-" if k < 0 else "")) + "".join(
        f"{_factor(r)}^{e}" if e > 1 else _factor(r) for r, e in factors)
    p = lambda x: k * math.prod((x - r) ** e for r, e in factors)  # noqa: E731
    if random.random() < 0.5:
        problem = (f"When $p(x) = {shown}$ is multiplied out, what is the sum of its coefficients?")
        answer = p(1)
        s = Steps()
        s.step("Substituting $x = 1$ makes every power of $x$ equal $1$, so $p(1)$ is the sum of the coefficients.",
               f"p(1) = {answer}")
    else:
        problem = (f"When $p(x) = {shown}$ is multiplied out, what is its constant term?")
        answer = p(0)
        s = Steps()
        s.step("Substituting $x = 0$ wipes out every term with $x$, leaving the constant term.", f"p(0) = {answer}")
    solution = f"{answer}"
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_polynomial_division.variant("remainder_parameter")
def _division_remainder_parameter():
    """For what k does dividing by (x - r) leave a given remainder?"""
    r = _nonzero(-4, 4)
    k = random.randint(-9, 9)
    c = random.randint(-9, 9)
    rem = r ** 3 + k * r + c
    problem = (
        f"When $x^3 + kx {'+' if c >= 0 else '-'} {abs(c)}$ is divided by ${_factor(r)}$, the remainder is "
        f"${rem}$. What is $k$?"
    )
    solution = f"{k}"
    s = Steps()
    s.step(f"By the remainder theorem, the remainder is $p({r})$.", f"({r})^3 + {paren(r)}k {'+' if c >= 0 else '-'} {abs(c)} = {rem}")
    s.step("Solve for $k$.", f"{r}k = {rem - r ** 3 - c} \\Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_remainder_theorem.variant("factor_parameter")
def _remainder_factor_parameter():
    """For what k is (x - r) a factor?"""
    r = _nonzero(-4, 4)
    a, k = random.randint(-6, 6), random.randint(-12, 12)
    c = -(r ** 3 + a * r * r + k * r)
    poly = f"x^3{' + ' + str(a) + 'x^2' if a > 0 else (' - ' + str(-a) + 'x^2' if a < 0 else '')} + kx {'+' if c >= 0 else '-'} {abs(c)}"
    problem = f"For what value of $k$ is ${_factor(r)}$ a factor of ${poly}$?"
    solution = f"{k}"
    s = Steps()
    s.step(f"By the factor theorem, ${_factor(r)}$ is a factor exactly when $p({r}) = 0$.",
           f"({r})^3 + {a}({r})^2 + {paren(r)}k + {paren(c)} = 0")
    s.step("Solve for $k$.", f"{r}k = {-(r ** 3 + a * r * r + c)} \\Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_remainder_theorem.variant("two_remainders")
def _remainder_two_conditions():
    """SAT-hard: two remainders pin down two unknown coefficients."""
    a, b, c = random.randint(-6, 6), random.randint(-6, 6), random.randint(-9, 9)
    r1 = 1 + a + b + c
    r2 = -1 + a - b + c
    problem = (
        f"$p(x) = x^3 + ax^2 + bx {'+' if c >= 0 else '-'} {abs(c)}$ leaves a remainder of ${r1}$ when divided by "
        f"$x - 1$ and ${r2}$ when divided by $x + 1$. What is $a$?"
    )
    solution = f"{a}"
    s = Steps()
    s.step("By the remainder theorem, $p(1)$ and $p(-1)$ are the remainders.",
           rf"1 + a + b + {paren(c)} = {r1}, \quad -1 + a - b + {paren(c)} = {r2}")
    s.step("Add the equations: the $b$-terms cancel.", f"2a + {2 * c} = {r1 + r2}")
    s.step("Solve.", f"a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_build_polynomial_from_roots.variant("leading_from_intercept")
def _build_leading_from_intercept():
    """A cubic's leading coefficient from its x-intercepts and y-intercept."""
    roots = random.sample([n for n in range(-5, 6) if n != 0], 3)
    a = _nonzero(-4, 4)
    y0 = a * math.prod(-r for r in roots)
    problem = (
        f"A cubic polynomial has x-intercepts {', '.join(f'${r}$' for r in roots)} and y-intercept ${y0}$. What is "
        "its leading coefficient?"
    )
    solution = f"{a}"
    s = Steps()
    s.step("Write it in factored form with an unknown leading coefficient.",
           "p(x) = a" + "".join(_factor(r) for r in roots))
    s.step("Substitute the y-intercept $(0, " + str(y0) + ")$.", f"{y0} = a \\cdot {math.prod(-r for r in roots)}")
    s.step("Solve for $a$.", f"a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_polynomial_factoring.variant("count_real_solutions")
def _polynomial_count_real():
    """Real solutions of a biquadratic (x^2 - p)(x^2 - q) = 0."""
    p, q = random.sample(range(-9, 10), 2)
    b, c = -(p + q), p * q
    count = sum(2 if v > 0 else (1 if v == 0 else 0) for v in (p, q))
    if p == 0 or q == 0:
        count = sum(2 if v > 0 else 0 for v in (p, q)) + 1
    poly = _poly([1, 0, b, 0, c])
    problem = f"How many real solutions does ${poly} = 0$ have?"
    solution = f"{count}"
    s = Steps()
    s.step("Treat it as a quadratic in $x^2$ and factor.", f"(x^2 - {paren(p)})(x^2 - {paren(q)}) = 0")
    s.step("$x^2 = k$ has two real solutions if $k > 0$, one if $k = 0$, none if $k < 0$.", f"x^2 = {p}, \\quad x^2 = {q}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_rational_root_list.variant("count_candidates")
def _rational_root_count():
    """How many candidates the rational root theorem gives."""
    a = random.randint(1, 12)
    c = _nonzero(-30, 30)
    cands = {Fraction(sign * p, q) for p in range(1, abs(c) + 1) if c % p == 0
             for q in range(1, a + 1) if a % q == 0 for sign in (1, -1)}
    problem = (
        f"How many different possible rational roots does the rational root theorem give for "
        f"${_poly([a, 3, -2, c])}$?"
    )
    solution = f"{len(cands)}"
    s = Steps()
    s.step(f"Candidates are $\\pm p/q$ with $p$ dividing ${abs(c)}$ and $q$ dividing ${a}$.")
    s.step("List them, removing duplicates such as $2/2 = 1$, and count.", f"{len(cands)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_polynomial_end_behavior.variant("minimum_degree")
def _end_behavior_minimum_degree():
    """The least degree consistent with end behavior and x-intercepts."""
    n = random.randint(1, 6)
    same = random.random() < 0.5
    degree = n if (n % 2 == 0) == same else n + 1
    ends = random.choice(["rises", "falls"]) if same else random.choice(["rises on the left and falls on the right",
                                                                        "falls on the left and rises on the right"])
    shape = f"{ends} on both ends" if same else ends
    problem = (
        f"The graph of a polynomial {shape} and crosses the x-axis at exactly ${n}$ points. What is the smallest "
        "possible degree?"
    )
    solution = f"{degree}"
    s = Steps()
    s.step("Both ends going the same way means even degree; opposite ways means odd degree.")
    s.step(f"It needs at least ${n}$ roots, so the degree is at least ${n}$, then adjusted to the right parity.",
           f"{degree}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Complex numbers ------------------------------------------------------------------------

@algebra2.alg2_add_complex.variant("unknown_parts")
def _complex_unknown_parts():
    """Match real and imaginary parts to find two unknowns."""
    a, b = random.randint(-9, 9), random.randint(-9, 9)
    p, c = random.randint(-9, 9), random.randint(-9, 9)
    real, imag = a - c, p + b
    problem = (
        f"If $(a {'+' if p >= 0 else '-'} {abs(p)}i) - ({c} - bi) = {real} {'+' if imag >= 0 else '-'} {abs(imag)}i$ "
        "for real numbers $a$ and $b$, what is $a + b$?"
    )
    solution = f"{a + b}"
    s = Steps()
    s.step("Match the real parts.", f"a - {paren(c)} = {real} \\Rightarrow a = {a}")
    s.step("Match the imaginary parts.", f"{p} + b = {imag} \\Rightarrow b = {b}")
    s.step("Add.", f"{a} + {paren(b)} = {a + b}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.multiply_complex_numbers.variant("real_product")
def _complex_real_product():
    """For what k is (p + qi)(k + ri) a real number?"""
    while True:
        p, q, r = _nonzero(-6, 6), _nonzero(-6, 6), _nonzero(-6, 6)
        if (p * r) % q == 0:
            break
    k = -p * r // q
    problem = (
        f"For what real number $k$ is $({p} {'+' if q > 0 else '-'} {abs(q)}i)(k {'+' if r > 0 else '-'} {abs(r)}i)$ a "
        "real number?"
    )
    solution = f"{k}"
    s = Steps()
    s.step("The product is real when its imaginary part is $0$. The imaginary part comes from the two cross terms.",
           f"{p}({r}) + {paren(q)}k = 0")
    s.step("Solve for $k$.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_complex_modulus.variant("product_rule")
def _modulus_product_rule():
    """|zw| = |z||w| and |z^n| = |z|^n."""
    a, b = random.randint(1, 9), random.randint(1, 9)
    if random.random() < 0.5:
        problem = f"If $|z| = {a}$ and $|w| = {b}$, what is $|zw|$?"
        answer = a * b
        s = Steps()
        s.step("Moduli multiply.", f"|zw| = |z||w| = {a}({b}) = {a * b}")
    else:
        n = random.randint(2, 4)
        a = random.randint(1, 5)
        problem = f"If $|z| = {a}$, what is $|z^{n}|$?"
        answer = a ** n
        s = Steps()
        s.step("The modulus of a power is the power of the modulus.", f"|z^{n}| = |z|^{n} = {a ** n}")
    solution = f"{answer}"
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_complex_division.variant("modulus_of_quotient")
def _division_modulus_of_quotient():
    """|z/w| = |z|/|w| without dividing."""
    (p1, q1, r1), (p2, q2, r2) = random.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)]), \
        random.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)])
    s1, s2 = random.choice([1, -1]), random.choice([1, -1])
    value = Fraction(r1, r2)
    problem = (
        f"What is the modulus of $\\frac{{{p1} {'+' if s1 > 0 else '-'} {q1}i}}{{{p2} {'+' if s2 > 0 else '-'} {q2}i}}$? "
        f"{_FRACTION_HINT}"
    )
    solution = frac_from(value)
    s = Steps()
    s.step("The modulus of a quotient is the quotient of the moduli.",
           rf"\frac{{\sqrt{{{p1}^2 + {q1}^2}}}}{{\sqrt{{{p2}^2 + {q2}^2}}}} = \frac{{{r1}}}{{{r2}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Exponents, radicals and logarithms ---------------------------------------------------------

@algebra2.alg2_rational_exponent.variant("solve_for_base")
def _rational_exponent_solve():
    r"""Reverse: $x^{m/n} = v$, find x."""
    n = random.choice([2, 3])
    m = random.choice([v for v in (1, 2, 3, 4, 5) if math.gcd(v, n) == 1 and v != 1] or [2])
    t = random.randint(2, 5 if m * n < 9 else 3)
    x, v = t ** n, t ** m
    problem = rf"Solve $x^{{{m}/{n}}} = {v}$ for $x > 0$."
    solution = f"{x}"
    s = Steps()
    s.step(f"Raise both sides to the power ${n}/{m}$, the reciprocal of the exponent.",
           rf"x = {v}^{{{n}/{m}}}")
    s.step(f"${v} = {t}^{m}$, so", rf"x = {t}^{{{n}}} = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_radical_equation.variant("extraneous_root")
def _radical_extraneous():
    """Squaring creates an extra root that must be checked and rejected."""
    while True:
        r1, r2 = sorted(random.sample(range(-8, 12), 2), reverse=True)
        if (r1 + r2) % 2 == 0:
            continue
        b = (1 - r1 - r2) // 2
        a = b * b - r1 * r2
        if r1 + b >= 0 and r2 + b < 0 and r1 + a >= 0:
            break
    problem = f"Solve $\\sqrt{{x {'+' if a >= 0 else '-'} {abs(a)}}} = x {'+' if b >= 0 else '-'} {abs(b)}$."
    solution = f"x={r1}"
    s = Steps()
    s.step("Square both sides and collect terms.", f"{_poly([1, 2 * b - 1, b * b - a])} = 0")
    s.step("Factor.", f"{_factor(r1)}{_factor(r2)} = 0 \\Rightarrow x = {r1} \\text{{ or }} x = {r2}")
    s.step(f"Check in the original: at $x = {r2}$ the right side is ${r2 + b}$, negative, but a square root is never "
           f"negative, so $x = {r2}$ is extraneous.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_exponential_log.variant("shifted_power")
def _exponential_shifted_power():
    """SAT-style: from b^x = v, find b^(x + k) or b^(2x) without solving for x."""
    b = random.randint(2, 5)
    v = random.randint(2, 30)
    if random.random() < 0.5:
        k = random.randint(1, 3)
        problem = f"If ${b}^x = {v}$, what is ${b}^{{x + {k}}}$?"
        answer = v * b ** k
        s = Steps()
        s.step("Split the exponent.", rf"{b}^{{x + {k}}} = {b}^x \cdot {b}^{{{k}}} = {v} \cdot {b ** k} = {answer}")
    else:
        problem = f"If ${b}^x = {v}$, what is ${b}^{{2x}}$?"
        answer = v * v
        s = Steps()
        s.step("A power of a power.", rf"{b}^{{2x}} = ({b}^x)^2 = {v}^2 = {answer}")
    solution = f"{answer}"
    s.answer(solution)
    return problem, solution, s.done()


def _log_reverse():
    """Reverse: find the base, or the argument, of a logarithm."""
    b, k = random.randint(2, 9), random.randint(2, 4 if random.random() < 0.5 else 3)
    if b ** k > 10000:
        k = 2
    if random.random() < 0.5:
        problem = rf"If $\log_b {b ** k} = {k}$, what is $b$?"
        answer = b
        s = Steps()
        s.step("Rewrite in exponential form.", f"b^{k} = {b ** k}")
        s.step("Take the root.", f"b = {b}")
    else:
        problem = rf"If $\log_{{{b}}} x = {k}$, what is $x$?"
        answer = b ** k
        s = Steps()
        s.step("Rewrite in exponential form.", f"x = {b}^{k} = {b ** k}")
    solution = f"{answer}"
    s.answer(solution)
    return problem, solution, s.done()


algebra2.alg2_evaluate_log.variant("reverse")(_log_reverse)
lib_algebra_extra_gen.log.variant("reverse")(_log_reverse)


@algebra2.alg2_log_product_rule.variant("missing_log")
def _log_product_missing():
    r"""Reverse: $\log_b(xy)$ and $\log_b x$ give $\log_b y$."""
    a, c = random.randint(-5, 9), random.randint(-5, 9)
    problem = rf"If $\log_b x = {a}$ and $\log_b(xy) = {a + c}$, what is $\log_b y$?"
    solution = f"{c}"
    s = Steps()
    s.step("The product rule splits the log of a product into a sum.", rf"\log_b(xy) = \log_b x + \log_b y")
    s.step("Substitute and solve.", rf"{a + c} = {a} + \log_b y \Rightarrow \log_b y = {c}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_log_quotient_rule.variant("missing_log")
def _log_quotient_missing():
    r"""Reverse: $\log_b(x/y)$ and $\log_b x$ give $\log_b y$."""
    a, c = random.randint(-5, 9), random.randint(-5, 9)
    problem = rf"If $\log_b x = {a}$ and $\log_b\left(\frac{{x}}{{y}}\right) = {a - c}$, what is $\log_b y$?"
    solution = f"{c}"
    s = Steps()
    s.step("The quotient rule turns the log of a quotient into a difference.", r"\log_b\frac{x}{y} = \log_b x - \log_b y")
    s.step("Substitute and solve.", rf"{a - c} = {a} - \log_b y \Rightarrow \log_b y = {c}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_log_power_rule.variant("missing_exponent")
def _log_power_missing():
    r"""$\log_b(x^k) = n$ and $\log_b x = m$ give k."""
    m, k = _nonzero(-5, 6), random.randint(2, 6)
    problem = rf"If $\log_b x = {m}$ and $\log_b(x^k) = {m * k}$, what is $k$?"
    solution = f"{k}"
    s = Steps()
    s.step("The power rule brings the exponent to the front.", rf"\log_b(x^k) = k\log_b x")
    s.step("Substitute and solve.", rf"{m * k} = {m}k \Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_log_change_of_base.variant("chain")
def _log_chain():
    r"""$\log_a b \cdot \log_b c = \log_a c$."""
    a = random.randint(2, 5)
    k = random.randint(2, 4)
    b = random.choice([v for v in range(2, 12) if v != a])
    problem = rf"Evaluate $\log_{{{a}}} {b} \cdot \log_{{{b}}} {a ** k}$."
    solution = f"{k}"
    s = Steps()
    s.step("Change both to a common base: the $\\ln " + str(b) + "$ cancels.",
           rf"\frac{{\ln {b}}}{{\ln {a}}} \cdot \frac{{\ln {a ** k}}}{{\ln {b}}} = \frac{{\ln {a ** k}}}{{\ln {a}}} = \log_{{{a}}} {a ** k}")
    s.step("Evaluate.", rf"\log_{{{a}}} {a ** k} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_radical_equation_conjugate.variant("conjugate_sum")
def _radical_conjugate_sum():
    """SAT-hard: from the difference of two roots, the sum without solving."""
    t = random.randint(1, 9)
    d = random.randint(1, 6)
    s_ = t + d
    x = random.randint(-10, 30)
    p, q = s_ * s_ - x, t * t - x
    problem = (
        rf"If $\sqrt{{x {'+' if p >= 0 else '-'} {abs(p)}}} - \sqrt{{x {'+' if q >= 0 else '-'} {abs(q)}}} = {d}$, what "
        rf"is $\sqrt{{x {'+' if p >= 0 else '-'} {abs(p)}}} + \sqrt{{x {'+' if q >= 0 else '-'} {abs(q)}}}$?"
    )
    solution = f"{s_ + t}"
    s = Steps()
    s.step("Multiply the difference by the sum: the cross terms cancel.",
           rf"(\sqrt{{A}} - \sqrt{{B}})(\sqrt{{A}} + \sqrt{{B}}) = A - B = {p} - {paren(q)} = {p - q}")
    s.step(f"The difference is ${d}$, so divide.", rf"\sqrt{{A}} + \sqrt{{B}} = \frac{{{p - q}}}{{{d}}} = {s_ + t}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_rationalize_denominator.variant("conjugate_factor")
def _rationalize_conjugate_factor():
    r"""$\frac{6}{\sqrt{5} - \sqrt{2}} = a(\sqrt{5} + \sqrt{2})$."""
    m, n = random.sample([2, 3, 5, 6, 7, 10, 11, 13], 2)
    m, n = max(m, n), min(m, n)
    a = random.randint(1, 6)
    top = a * (m - n)
    problem = rf"If $\frac{{{top}}}{{\sqrt{{{m}}} - \sqrt{{{n}}}}} = a(\sqrt{{{m}}} + \sqrt{{{n}}})$, what is $a$?"
    solution = f"{a}"
    s = Steps()
    s.step("Multiply top and bottom by the conjugate.",
           rf"\frac{{{top}(\sqrt{{{m}}} + \sqrt{{{n}}})}}{{{m} - {n}}} = {a}(\sqrt{{{m}}} + \sqrt{{{n}}})")
    s.answer(solution)
    return problem, solution, s.done()


# --- Functions ------------------------------------------------------------------------------------

def _inverse_from_table():
    """f^-1 read from a table of f: swap the roles of input and output."""
    xs = sorted(random.sample(range(-6, 10), 5))
    ys = random.sample(range(-20, 21), 5)
    i = random.randrange(5)
    problem = f"The table shows values of a one-to-one function $f$. ${_table('x', xs, 'f(x)', ys)}$ What is $f^{{-1}}({ys[i]})$?"
    solution = f"{xs[i]}"
    s = Steps()
    s.step(f"$f^{{-1}}({ys[i]})$ is the input that $f$ sends to ${ys[i]}$.", f"f({xs[i]}) = {ys[i]}")
    s.answer(solution)
    return problem, solution, s.done()


algebra2.alg2_inverse_linear_function.variant("from_table")(_inverse_from_table)
algebra2.alg2_inverse_nonlinear.variant("from_table")(_inverse_from_table)


@algebra2.alg2_function_composition.variant("from_tables")
def _composition_from_tables():
    """Composition with f and g given as tables."""
    xs = list(range(1, 6))
    g = [random.randint(1, 5) for _ in xs]
    f = [random.randint(-9, 9) for _ in xs]
    a = random.choice(xs)
    inner = g[a - 1]
    problem = (
        f"The tables give $f$ and $g$. ${_table('x', xs, 'f(x)', f)}$ ${_table('x', xs, 'g(x)', g)}$ What is "
        f"$f(g({a}))$?"
    )
    solution = f"{f[inner - 1]}"
    s = Steps()
    s.step("Work from the inside out: read $g$ first.", f"g({a}) = {inner}")
    s.step("Then read $f$ at that value.", f"f({inner}) = {f[inner - 1]}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_rational_equation.variant("extraneous_root")
def _rational_extraneous():
    r"""$\frac{x^2}{x - a} = \frac{a^2}{x - a} + k$: one root is excluded."""
    a = _nonzero(-6, 6)
    k = random.choice([v for v in range(-10, 13) if v != 2 * a])
    x = k - a
    problem = (
        rf"Solve $\frac{{x^2}}{{x {'-' if a > 0 else '+'} {abs(a)}}} = \frac{{{a * a}}}{{x {'-' if a > 0 else '+'} {abs(a)}}} + {paren(k)}$."
    )
    solution = f"x={x}"
    s = Steps()
    s.step(f"Multiply by $x - {paren(a)}$ (remembering $x \\neq {a}$).", f"x^2 - {a * a} = {k}(x - {paren(a)})")
    s.step("Factor the difference of squares and collect.", f"(x - {paren(a)})(x + {paren(a)} - {paren(k)}) = 0")
    s.step(f"$x = {a}$ makes the original denominators $0$, so it's excluded.", f"x = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_rational_expression_ops.variant("excluded_values")
def _rational_ops_excluded():
    """Dividing by a fraction also excludes the zeros of its numerator."""
    a, b, c, d = random.sample([n for n in range(-6, 7) if n != 0], 4)
    excluded = {b, c, d}
    problem = (
        rf"How many values of $x$ must be excluded from $\frac{{x - {paren(a)}}}{{x - {paren(b)}}} \div "
        rf"\frac{{x - {paren(c)}}}{{x - {paren(d)}}}$?"
    )
    solution = f"{len(excluded)}"
    s = Steps()
    s.step(f"Both denominators can't be zero: $x \\neq {b}$ and $x \\neq {d}$.")
    s.step(f"Dividing by the second fraction means it can't be zero either: $x \\neq {c}$.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Systems and matrices -------------------------------------------------------------------------

@algebra2.alg2_solve_system_three.variant("sum_without_solving")
def _system_three_sum():
    """Columns that add to the same k: adding the equations gives x + y + z."""
    k = random.randint(3, 9)
    rows = [[random.randint(-3, 5) for _ in range(3)] for _ in range(2)]
    rows.append([k - rows[0][j] - rows[1][j] for j in range(3)])
    x, y, z = (random.randint(-5, 5) for _ in range(3))
    rhs = [r[0] * x + r[1] * y + r[2] * z for r in rows]

    def eq(r, v):
        parts = []
        for c, var in zip(r, "xyz"):
            if c == 0:
                continue
            term = (var if abs(c) == 1 else f"{abs(c)}{var}")
            parts.append(("-" if c < 0 else "+") + " " + term)
        text = " ".join(parts).lstrip("+ ")
        if text.startswith("- "):
            text = "-" + text[2:]
        return f"{text or '0'} = {v}"
    problem = "If " + ", ".join(f"${eq(r, v)}$" for r, v in zip(rows, rhs)) + ", what is $x + y + z$?"
    solution = f"{x + y + z}"
    s = Steps()
    s.step("Add all three equations: each variable's coefficients add up to the same number.",
           f"{k}x + {k}y + {k}z = {sum(rhs)}")
    s.step(f"Divide by ${k}$.", f"x + y + z = {x + y + z}")
    s.answer(solution)
    return problem, solution, s.done()


def _matrix_tex(m):
    return r"\begin{bmatrix}" + r" \\ ".join(" & ".join(map(str, row)) for row in m) + r"\end{bmatrix}"


@algebra2.alg2_matrix_operation.variant("commutator_entry")
def _matrix_commutator():
    """Matrix multiplication isn't commutative: an entry of AB - BA."""
    A = [[random.randint(-4, 4) for _ in range(2)] for _ in range(2)]
    B = [[random.randint(-4, 4) for _ in range(2)] for _ in range(2)]
    mul = lambda P, Q: [[sum(P[i][k] * Q[k][j] for k in range(2)) for j in range(2)] for i in range(2)]  # noqa: E731
    AB, BA = mul(A, B), mul(B, A)
    i, j = random.randrange(2), random.randrange(2)
    problem = (
        f"Let $A = {_matrix_tex(A)}$ and $B = {_matrix_tex(B)}$. What is the entry in row {i + 1}, column {j + 1} of "
        "$AB - BA$?"
    )
    solution = f"{AB[i][j] - BA[i][j]}"
    s = Steps()
    s.step("Compute the entry of each product: row of the first times column of the second.",
           rf"(AB)_{{{i + 1}{j + 1}}} = {AB[i][j]}, \quad (BA)_{{{i + 1}{j + 1}}} = {BA[i][j]}")
    s.step("Subtract. (They usually differ: $AB \\neq BA$.)", f"{AB[i][j]} - {paren(BA[i][j])} = {AB[i][j] - BA[i][j]}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.int_matrix_22_determinant.variant("singular_parameter")
def _determinant_singular():
    """For what k is the matrix singular (determinant 0)?"""
    while True:
        a, c, d = _nonzero(-9, 9), _nonzero(-9, 9), _nonzero(-9, 9)
        if (a * d) % c == 0:
            break
    k = a * d // c
    problem = f"For what value of $k$ is ${_matrix_tex([[a, 'k'], [c, d]])}$ not invertible?"
    solution = f"{k}"
    s = Steps()
    s.step("A matrix has no inverse when its determinant is $0$.", f"{a}({d}) - k({c}) = 0")
    s.step("Solve for $k$.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Conics and statistics ----------------------------------------------------------------------

@algebra2.alg2_conic_equation.variant("focal_distance")
def _conic_focal_distance():
    """The center-to-focus distance c from an ellipse or hyperbola equation."""
    A, B = random.sample([n * n for n in range(1, 11)], 2)
    hyperbola = random.random() < 0.5
    c = math.sqrt(A + B) if hyperbola else math.sqrt(abs(A - B))
    sign = "-" if hyperbola else "+"
    problem = (
        f"For the {'hyperbola' if hyperbola else 'ellipse'} $\\frac{{x^2}}{{{A}}} {sign} \\frac{{y^2}}{{{B}}} = 1$, how far "
        f"is each focus from the center? {_ROUND}"
    )
    solution = num(c)
    s = Steps()
    if hyperbola:
        s.step("For a hyperbola, $c^2 = a^2 + b^2$.", rf"c = \sqrt{{{A} + {B}}} \approx {solution}")
    else:
        s.step("For an ellipse, $c^2$ is the difference of the two denominators.", rf"c = \sqrt{{|{A} - {B}|}} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


_EMPIRICAL = {(-3, -2): 2.35, (-2, -1): 13.5, (-1, 0): 34, (0, 1): 34, (1, 2): 13.5, (2, 3): 2.35}


@algebra2.alg2_empirical_rule.variant("band_percent")
def _empirical_band():
    """Add up the empirical rule's bands between two whole-SD cut points."""
    lo, hi = sorted(random.sample(range(-3, 4), 2))
    pct = sum(v for (a, b), v in _EMPIRICAL.items() if lo <= a and b <= hi)
    mu, sd = random.randint(20, 100), random.randint(2, 15)
    problem = (
        f"A normal distribution has mean ${mu}$ and standard deviation ${sd}$. By the 68-95-99.7 rule, about what "
        f"percent of the data lies between ${mu + lo * sd}$ and ${mu + hi * sd}$? Give just the number, without a % sign."
    )
    solution = num(pct)
    s = Steps()
    s.step(f"Those values are ${lo}$ and ${hi}$ standard deviations from the mean.")
    s.step("Add the percent in each one-standard-deviation band: 34, 13.5, and 2.35 moving out from the mean.",
           f"{solution}\\%")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.confidence_interval.variant("from_interval")
def _confidence_from_interval():
    """Reverse: the sample mean or margin of error from the endpoints."""
    mean = Fraction(random.randint(100, 9000), 10)
    e = Fraction(random.randint(5, 500), 100)
    low, high = mean - e, mean + e
    ask_mean = random.random() < 0.5
    problem = (
        f"A confidence interval for a mean is $({num(low)}, {num(high)})$. What is the "
        f"{'sample mean' if ask_mean else 'margin of error'}?"
    )
    solution = num(mean if ask_mean else e)
    s = Steps()
    if ask_mean:
        s.step("The interval is centered on the sample mean: average the endpoints.", rf"\frac{{{num(low)} + {num(high)}}}{{2}} = {solution}")
    else:
        s.step("The margin of error is half the width.", rf"\frac{{{num(high)} - {num(low)}}}{{2}} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Sequences ------------------------------------------------------------------------------------

@lib_algebra_extra_gen.arithmetic_progression_term.variant("from_two_terms")
def _ap_term_from_two_terms():
    """Hidden first term and difference: two terms give any other."""
    a1, d = random.randint(-20, 20), _nonzero(-9, 9)
    m, n = sorted(random.sample(range(2, 12), 2))
    k = random.randint(n + 1, 30)
    term = lambda i: a1 + (i - 1) * d  # noqa: E731
    problem = f"In an arithmetic sequence, $a_{{{m}}} = {term(m)}$ and $a_{{{n}}} = {term(n)}$. What is $a_{{{k}}}$?"
    solution = f"{term(k)}"
    s = Steps()
    s.step("The terms are $n - m$ steps apart, so divide to find the common difference.",
           rf"d = \frac{{{term(n)} - {paren(term(m))}}}{{{n} - {m}}} = {d}")
    s.step(f"Step from $a_{{{n}}}$ to $a_{{{k}}}$.", f"a_{{{k}}} = {term(n)} + ({k} - {n})({d}) = {term(k)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.arithmetic_progression_sum.variant("from_two_terms")
def _ap_sum_from_two_terms():
    """A sum when only two terms are given."""
    a1, d = random.randint(-20, 20), _nonzero(-9, 9)
    m, n = sorted(random.sample(range(2, 10), 2))
    count = random.randint(n, 25)
    term = lambda i: a1 + (i - 1) * d  # noqa: E731
    total = count * (a1 + term(count)) // 2
    problem = (
        f"An arithmetic sequence has $a_{{{m}}} = {term(m)}$ and $a_{{{n}}} = {term(n)}$. What is the sum of its first "
        f"${count}$ terms?"
    )
    solution = f"{total}"
    s = Steps()
    s.step("Find the common difference and the first term.",
           rf"d = \frac{{{term(n)} - {paren(term(m))}}}{{{n - m}}} = {d}, \quad a_1 = {term(m)} - {m - 1}({d}) = {a1}")
    s.formula("The sum", rf"S_{{{count}}} = \frac{{{count}}}{{2}}(a_1 + a_{{{count}}}) = \frac{{{count}}}{{2}}({a1} + {paren(term(count))}) = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.geometric_progression.variant("from_two_terms")
def _gp_from_two_terms():
    """Hidden ratio: two terms of a geometric sequence give another."""
    a1, r = _nonzero(-5, 5), random.choice([2, 3, -2, -3])
    m = random.randint(1, 3)
    n = m + random.randint(1, 3)
    k = n + random.randint(1, 2)
    term = lambda i: a1 * r ** (i - 1)  # noqa: E731
    gap = n - m
    note = " The common ratio is positive." if gap % 2 == 0 else ""
    if gap % 2 == 0 and r < 0:
        r = -r
    problem = (
        f"In a geometric sequence, $a_{{{m}}} = {term(m)}$ and $a_{{{n}}} = {term(n)}$.{note} What is $a_{{{k}}}$?"
    )
    solution = f"{term(k)}"
    s = Steps()
    s.step(f"From $a_{{{m}}}$ to $a_{{{n}}}$ the sequence multiplies by $r^{{{gap}}}$.",
           rf"r^{{{gap}}} = \frac{{{term(n)}}}{{{term(m)}}} = {r ** gap} \Rightarrow r = {r}")
    s.step(f"Multiply on to $a_{{{k}}}$.", f"a_{{{k}}} = {term(n)} \\cdot ({r})^{{{k - n}}} = {term(k)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Counting and sets ------------------------------------------------------------------------------

@lib_algebra_extra_gen.combinations.variant("handshakes")
def _combinations_handshakes():
    """Reverse: everyone shakes hands once; how many people?"""
    n = random.randint(3, 30)
    problem = f"At a party, every person shakes hands with every other person exactly once. There are ${math.comb(n, 2)}$ handshakes. How many people are there?"
    solution = f"{n}"
    s = Steps()
    s.step("Each handshake is a choice of $2$ people.", rf"\binom{{n}}{{2}} = \frac{{n(n - 1)}}{{2}} = {math.comb(n, 2)}")
    s.step("Solve.", f"n(n - 1) = {n * (n - 1)} \\Rightarrow n = {n}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.permutation.variant("officers")
def _permutation_officers():
    """Reverse: ordered pairs of officers; how many members?"""
    n = random.randint(3, 25)
    problem = (
        f"A club can choose a president and a vice president (two different members) in ${n * (n - 1)}$ ways. How "
        "many members does the club have?"
    )
    solution = f"{n}"
    s = Steps()
    s.step("Order matters, so there are $n$ choices for president and $n - 1$ for vice president.", f"n(n - 1) = {n * (n - 1)}")
    s.step("Find the consecutive numbers with that product.", f"{n} \\times {n - 1} = {n * (n - 1)}")
    s.answer(solution)
    return problem, solution, s.done()


@sets_gen.set_operation.variant("inclusion_exclusion")
def _sets_inclusion_exclusion():
    """How many are in neither set, by inclusion-exclusion."""
    both = random.randint(0, 15)
    only_a, only_b = random.randint(0, 20), random.randint(0, 20)
    neither = random.randint(0, 15)
    total = both + only_a + only_b + neither
    a, b = only_a + both, only_b + both
    problem = (
        f"Of ${total}$ students, ${a}$ take art, ${b}$ take music, and ${both}$ take both. How many take neither?"
    )
    solution = f"{neither}"
    s = Steps()
    s.step("Count those taking at least one, without counting the overlap twice.", f"{a} + {b} - {both} = {a + b - both}")
    s.step("Subtract from the total.", f"{total} - {a + b - both} = {neither}")
    s.answer(solution)
    return problem, solution, s.done()


# =============================================================================
# Further variants (beyond each topic's first new question type)
# =============================================================================

@algebra2.alg2_evaluate_polynomial.variant("coefficient_from_value")
def _polynomial_coefficient_from_value():
    """Reverse: an unknown coefficient from one value of the polynomial."""
    x0 = _nonzero(-3, 3)
    k = random.randint(-9, 9)
    c = random.randint(-9, 9)
    value = x0 ** 3 + k * x0 + c
    problem = f"$p(x) = x^3 + kx {'+' if c >= 0 else '-'} {abs(c)}$ and $p({x0}) = {value}$. What is $k$?"
    solution = f"{k}"
    s = Steps()
    s.substitute(f"({x0})^3 + {paren(x0)}k {'+' if c >= 0 else '-'} {abs(c)} = {value}", text=f"Substitute $x = {x0}$.")
    s.step("Solve for $k$.", f"{x0}k = {value - x0 ** 3 - c} \\Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_evaluate_polynomial.variant("box_volume")
def _polynomial_box_volume():
    """An open box from a sheet with squares cut from the corners: V(x) = x(L - 2x)(W - 2x)."""
    L, W = random.randint(10, 30), random.randint(8, 24)
    x = random.randint(1, min(L, W) // 2 - 1)
    v = x * (L - 2 * x) * (W - 2 * x)
    problem = (
        f"An open box is made from a ${L}$ by ${W}$ inch sheet by cutting $x$-inch squares from each corner and folding "
        f"up the sides, so $V(x) = x({L} - 2x)({W} - 2x)$. What is the volume when $x = {x}$, in cubic inches?"
    )
    solution = f"{v}"
    s = Steps()
    s.substitute(f"V({x}) = {x}({L} - {2 * x})({W} - {2 * x}) = {x}({L - 2 * x})({W - 2 * x}) = {v}", text=f"Substitute $x = {x}$.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_polynomial_division.variant("quotient_constant")
def _division_quotient_constant():
    """Just one number from a division: the quotient's constant term."""
    r = _nonzero(-4, 4)
    coeffs = [1] + [random.randint(-6, 6) for _ in range(3)]
    q, carry = [], 0
    for c in coeffs:
        carry = carry * r + c
        q.append(carry)
    quotient, rem = q[:-1], q[-1]
    problem = f"When ${_poly(coeffs)}$ is divided by ${_factor(r)}$, what is the constant term of the quotient?"
    solution = f"{quotient[-1]}"
    s = Steps()
    s.step(f"Use synthetic division with ${r}$.", r"\text{bottom row: } " + ", ".join(map(str, q)))
    s.step("The bottom row (except the last entry, the remainder) is the quotient's coefficients.",
           f"{_poly(quotient)}, \\quad \\text{{remainder }} {rem}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_remainder_theorem.variant("linear_divisor")
def _remainder_linear_divisor():
    """Dividing by (ax - b): the remainder is p(b/a)."""
    a = random.choice([2, 3])
    b = random.choice([v for v in range(-5, 6) if v and math.gcd(v, a) == 1])
    coeffs = [random.randint(-5, 5) or 1 for _ in range(3)]
    root = Fraction(b, a)
    rem = sum(c * root ** (len(coeffs) - 1 - i) for i, c in enumerate(coeffs))
    problem = (
        f"What is the remainder when ${_poly(coeffs)}$ is divided by ${a}x {'-' if b > 0 else '+'} {abs(b)}$? {_FRACTION_HINT}"
    )
    solution = frac_from(rem)
    s = Steps()
    s.step(f"The divisor is zero at $x = {_tex(root)}$, so the remainder is $p({_tex(root)})$.", f"p\\left({_tex(root)}\\right) = {_tex(rem)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_remainder_theorem.variant("is_factor")
def _remainder_is_factor():
    """Is (x - r) a factor? Check whether p(r) = 0."""
    r = _nonzero(-4, 4)
    if random.random() < 0.5:
        others = [random.randint(-4, 4), random.randint(-4, 4)]
        coeffs = [1, -(r + sum(others)), r * sum(others) + others[0] * others[1], -r * others[0] * others[1]]
    else:
        coeffs = [1] + [random.randint(-6, 6) for _ in range(3)]
    value = _evaluate(coeffs, r)
    answer = "yes" if value == 0 else "no"
    problem = f"Is ${_factor(r)}$ a factor of ${_poly(coeffs)}$? Answer yes or no."
    s = Steps()
    s.step(f"By the factor theorem, check whether $p({r}) = 0$.", f"p({r}) = {value}")
    s.answer(answer)
    return problem, answer, s.done()


@algebra2.alg2_build_polynomial_from_roots.variant("one_coefficient")
def _build_one_coefficient():
    """One coefficient of the monic polynomial with given roots (Vieta)."""
    roots = random.sample([n for n in range(-6, 7) if n != 0], 3)
    if random.random() < 0.5:
        roots[2] = roots[1]   # a double root
    which = random.choice(["constant term", "coefficient of $x^2$"])
    value = -math.prod(roots) if which == "constant term" else -sum(roots)
    roots_text = ", ".join(f"${r}$" for r in roots)
    problem = (
        f"A monic cubic has roots {roots_text} (counted with multiplicity). What is its {which}?"
    )
    solution = f"{value}"
    s = Steps()
    s.step("Write it as a product of factors.", "".join(_factor(r) for r in roots))
    consts = [paren(-r) for r in roots]
    if which == "constant term":
        s.step("The constant term is the product of the constants in the factors.",
               r" \cdot ".join(consts) + f" = {value}")
    else:
        s.step("The $x^2$ coefficient is the sum of the constants in the factors.", " + ".join(consts) + f" = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_add_complex.variant("missing_addend")
def _complex_missing_addend():
    r"""$(3 + 2i) + z = 5 - i$: find z."""
    a, b, c, d = (random.randint(-9, 9) for _ in range(4))
    re_, im = c - a, d - b
    problem = (
        f"If $({a} {'+' if b >= 0 else '-'} {abs(b)}i) + z = {c} {'+' if d >= 0 else '-'} {abs(d)}i$, what is $z$? Format "
        "your answer as such: 4-2i."
    )
    solution = f"{re_}{'+' if im >= 0 else '-'}{abs(im)}i"
    s = Steps()
    s.step("Subtract the real parts and the imaginary parts.", f"z = ({c} - {paren(a)}) + ({d} - {paren(b)})i = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_add_complex.variant("plus_conjugate")
def _complex_plus_conjugate():
    """z plus its conjugate is twice the real part (z minus it is 2bi)."""
    a, b = random.randint(-15, 15), _nonzero(-15, 15)
    problem = f"If $z = {a} {'+' if b > 0 else '-'} {abs(b)}i$, what is $z + \\bar{{z}}$?"
    solution = f"{2 * a}"
    s = Steps()
    s.step("The conjugate flips the sign of the imaginary part, so the imaginary parts cancel.", f"({a} + {b}i) + ({a} - {b}i) = {2 * a}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.multiply_complex_numbers.variant("conjugate_product")
def _complex_conjugate_product():
    """(a + bi)(a - bi) = a^2 + b^2."""
    a, b = _nonzero(-12, 12), _nonzero(-12, 12)
    problem = f"Multiply $({a} {'+' if b > 0 else '-'} {abs(b)}i)({a} {'-' if b > 0 else '+'} {abs(b)}i)$."
    solution = f"{a * a + b * b}"
    s = Steps()
    s.step("These are conjugates: the middle terms cancel and $i^2 = -1$.", f"{a}^2 - ({abs(b)}i)^2 = {a * a} + {b * b} = {a * a + b * b}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.multiply_complex_numbers.variant("power_of_i")
def _complex_power_of_i():
    """Powers of i cycle with period 4."""
    n = random.randint(5, 200)
    value = {0: "1", 1: "i", 2: "-1", 3: "-i"}[n % 4]
    problem = f"Simplify $i^{{{n}}}$. Answer 1, -1, i, or -i."
    s = Steps()
    s.step("The powers of $i$ repeat every $4$: $i, -1, -i, 1$. Divide the exponent by $4$.", f"{n} = 4({n // 4}) + {n % 4}")
    s.step(f"So $i^{{{n}}} = i^{{{n % 4}}}$.")
    s.answer(value)
    return problem, value, s.done()


@algebra2.alg2_rational_exponent.variant("negative_exponent")
def _rational_exponent_negative():
    r"""$8^{-2/3} = 1/4$."""
    t = random.randint(2, 5)
    n = random.choice([2, 3])
    m = random.choice([1, 2, 3] if n == 2 else [1, 2])
    base = t ** n
    value = Fraction(1, t ** m)
    problem = rf"Evaluate ${base}^{{-{m}/{n}}}$. {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step("A negative exponent takes the reciprocal; the denominator is the root.",
           rf"{base}^{{-{m}/{n}}} = \frac{{1}}{{(\sqrt[{n}]{{{base}}})^{{{m}}}}} = \frac{{1}}{{{t}^{{{m}}}}}")
    s.step("Evaluate.", _tex(value))
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_rational_exponent.variant("radical_to_exponent")
def _rational_exponent_from_radical():
    r"""$\sqrt[n]{x^m} = x^{m/n}$: give the exponent."""
    n = random.randint(2, 6)
    m = random.randint(1, 9)
    value = Fraction(m, n)
    root = "" if n == 2 else str(n)
    problem = rf"Write $\sqrt[{root}]{{x^{{{m}}}}}$ as $x^k$. What is $k$? {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step("The index of the root is the denominator of the exponent.", rf"\sqrt[{n}]{{x^{{{m}}}}} = x^{{{m}/{n}}} = x^{{{_tex(value)}}}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_radical_equation.variant("cube_root")
def _radical_cube_root():
    r"""$\sqrt[3]{ax + b} = c$."""
    c = _nonzero(-5, 5)
    a = _nonzero(-6, 6)
    x = random.randint(-10, 10)
    b = c ** 3 - a * x
    problem = f"Solve $\\sqrt[3]{{{a}x {'+' if b >= 0 else '-'} {abs(b)}}} = {c}$ for x"
    solution = f"x={x}"
    s = Steps()
    s.step("Cube both sides (no extraneous roots: cubing is reversible).", f"{a}x {'+' if b >= 0 else '-'} {abs(b)} = {c ** 3}")
    s.step("Solve.", f"x = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_radical_equation.variant("pendulum")
def _radical_pendulum():
    r"""Solve $T = 2\pi\sqrt{L/9.8}$ for the length."""
    T = Fraction(random.randint(5, 60), 10)
    L = 9.8 * (float(T) / (2 * math.pi)) ** 2
    problem = (
        f"A pendulum's period is $T = 2\\pi\\sqrt{{\\frac{{L}}{{9.8}}}}$ seconds for length $L$ meters. What length gives "
        f"a period of ${num(T)}$ seconds? {_ROUND}"
    )
    solution = num(L)
    s = Steps()
    s.step(r"Divide by $2\pi$ and square both sides.", rf"\frac{{L}}{{9.8}} = \left(\frac{{{num(T)}}}{{2\pi}}\right)^2")
    s.step("Multiply by $9.8$.", rf"L \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_exponential_log.variant("common_base")
def _exponential_common_base():
    r"""$3^{x+1} = 27^{x-1}$: rewrite both sides with one base."""
    base = random.choice([2, 3, 5])
    p = random.randint(2, 3 if base < 5 else 2)
    a, b = random.randint(-4, 4), random.randint(-4, 4)
    # base^(x + a) = (base^p)^(x + b)  =>  x + a = p x + p b  =>  x = (a - p b)/(p - 1)
    x = Fraction(a - p * b, p - 1)
    problem = (
        f"Solve ${base}^{{x {'+' if a >= 0 else '-'} {abs(a)}}} = {base ** p}^{{x {'+' if b >= 0 else '-'} {abs(b)}}}$. "
        f"{_FRACTION_HINT}"
    )
    solution = frac_from(x)
    s = Steps()
    s.step(f"Write ${base ** p} = {base}^{p}$ so both sides have the same base.", f"{base}^{{x + {paren(a)}}} = {base}^{{{p}(x + {paren(b)})}}")
    s.step("Set the exponents equal and solve.", f"x + {paren(a)} = {p}x + {p * b} \\Rightarrow x = {_tex(x)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_exponential_log.variant("doubling_time")
def _exponential_doubling_time():
    """How long money takes to double at an annual rate, compounded yearly."""
    r = random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
    t = math.log(2) / math.log(1 + r / 100)
    problem = f"At ${r}\\%$ annual interest compounded once a year, how many years does it take money to double? {_ROUND}"
    solution = num(t)
    s = Steps()
    s.step("Solve $(1 + r)^t = 2$ with logarithms.", rf"t = \frac{{\ln 2}}{{\ln {num(1 + Fraction(r, 100))}}} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


def _log_fractional():
    r"""Logs with fractional or negative values: $\log_4 8 = 3/2$, $\log_2\frac{1}{8} = -3$."""
    b = random.choice([2, 3, 4, 8, 9, 16, 25, 27])
    root = {2: 2, 3: 3, 4: 2, 8: 2, 9: 3, 16: 2, 25: 5, 27: 3}[b]
    k = round(math.log(b, root))
    e = random.choice([v for v in range(-4, 6) if v])
    arg = Fraction(root) ** e
    value = Fraction(e, k)
    arg_tex = _tex(arg)
    problem = rf"Evaluate $\log_{{{b}}} {arg_tex if arg.denominator == 1 else '{' + arg_tex + '}'}$. {_FRACTION_HINT}"
    solution = frac_from(value)
    s = Steps()
    s.step(f"Write both as powers of ${root}$.", rf"{b} = {root}^{{{k}}}, \quad {arg_tex} = {root}^{{{e}}}")
    s.step(f"So the log is the ratio of exponents.", rf"\log_{{{b}}} {arg_tex} = \frac{{{e}}}{{{k}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


algebra2.alg2_evaluate_log.variant("fractional_value")(_log_fractional)
lib_algebra_extra_gen.log.variant("fractional_value")(_log_fractional)


@algebra2.alg2_evaluate_log.variant("between_integers")
def _log_between_integers():
    r"""Estimate: $\log_2 50$ lies between which consecutive integers?"""
    b = random.choice([2, 3, 5, 10])
    k = random.randint(1, 5 if b < 5 else 3)
    n = random.randint(b ** k + 1, b ** (k + 1) - 1)
    problem = rf"$\log_{{{b}}} {n}$ lies between two consecutive integers. What is the smaller one?"
    solution = f"{k}"
    s = Steps()
    s.step(f"Find the powers of ${b}$ around ${n}$.", f"{b}^{k} = {b ** k} < {n} < {b ** (k + 1)} = {b}^{k + 1}")
    s.step("So the log is between the exponents.", f"{k} < \\log_{{{b}}} {n} < {k + 1}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_log_change_of_base.variant("reciprocal")
def _log_reciprocal():
    r"""$\log_a b = k \Rightarrow \log_b a = 1/k$."""
    k = Fraction(_nonzero(-6, 6), random.choice([1, 1, 2, 3]))
    problem = rf"If $\log_a b = {_tex(k)}$, what is $\log_b a$? {_FRACTION_HINT}"
    solution = frac_from(1 / k)
    s = Steps()
    s.step("By change of base, the two logs are reciprocals.", rf"\log_b a = \frac{{\ln a}}{{\ln b}} = \frac{{1}}{{\log_a b}} = {_tex(1 / k)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_inverse_linear_function.variant("inverse_slope")
def _inverse_slope():
    """The slope of the inverse of a line is the reciprocal of its slope."""
    m = Fraction(_nonzero(-9, 9), random.choice([1, 1, 2, 3]))
    b = random.randint(-9, 9)
    problem = (
        f"$f(x) = {_tex(m)}x {'+' if b >= 0 else '-'} {abs(b)}$. What is the slope of the graph of $f^{{-1}}$? {_FRACTION_HINT}"
    )
    solution = frac_from(1 / m)
    s = Steps()
    s.step("The inverse swaps $x$ and $y$, so rise and run swap: the slope is the reciprocal.", rf"\frac{{1}}{{{_tex(m)}}} = {_tex(1 / m)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_inverse_nonlinear.variant("restricted_quadratic")
def _inverse_restricted_quadratic():
    """f(x) = (x - h)^2 + k with x >= h: evaluate the inverse."""
    h, k = random.randint(-6, 6), random.randint(-9, 9)
    x = h + random.randint(0, 8)
    v = (x - h) ** 2 + k
    problem = (
        f"$f(x) = {_factor(h).strip('()') if h == 0 else _factor(h)}^2 {'+' if k >= 0 else '-'} {abs(k)}$ for $x \\geq {h}$. "
        f"What is $f^{{-1}}({v})$?"
    )
    solution = f"{x}"
    s = Steps()
    s.step(f"Solve $f(x) = {v}$.", f"{_factor(h)}^2 = {v - k}")
    s.step(f"Take the square root that keeps $x \\geq {h}$.", f"x = {h} + {math.isqrt(v - k)} = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_function_composition.variant("solve_composite")
def _composition_solve():
    """Reverse: solve f(g(x)) = v for linear f and g."""
    a, b = _nonzero(-5, 5), random.randint(-9, 9)
    c, d = _nonzero(-5, 5), random.randint(-9, 9)
    x = random.randint(-8, 8)
    v = a * (c * x + d) + b
    problem = (
        f"$f(x) = {a}x {'+' if b >= 0 else '-'} {abs(b)}$ and $g(x) = {c}x {'+' if d >= 0 else '-'} {abs(d)}$. For what $x$ is "
        f"$f(g(x)) = {v}$?"
    )
    solution = f"{x}"
    s = Steps()
    s.step("Build the composite.", f"f(g(x)) = {a}({c}x {'+' if d >= 0 else '-'} {abs(d)}) {'+' if b >= 0 else '-'} {abs(b)} = {a * c}x {'+' if a * d + b >= 0 else '-'} {abs(a * d + b)}")
    s.step("Set it equal and solve.", f"{a * c}x = {v - a * d - b} \\Rightarrow x = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_function_composition.variant("decompose")
def _composition_decompose():
    r"""Decomposition: $h = (ax + b)^2 = f(g(x))$ with $f(x) = x^2$; find $g(t)$."""
    a, b = _nonzero(-5, 5), random.randint(-9, 9)
    n = random.choice([2, 3])
    t = random.randint(-5, 5)
    problem = (
        f"$h(x) = ({a}x {'+' if b >= 0 else '-'} {abs(b)})^{n}$ is written as $h(x) = f(g(x))$ with $f(x) = x^{n}$. What is "
        f"$g({t})$?"
    )
    solution = f"{a * t + b}"
    s = Steps()
    s.step(f"$f$ raises to the power ${n}$, so $g$ is what's inside the parentheses.", f"g(x) = {a}x {'+' if b >= 0 else '-'} {abs(b)}")
    s.step("Evaluate.", f"g({t}) = {a * t + b}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_rational_equation.variant("work_rate")
def _rational_work_rate():
    """Two workers together: 1/a + 1/b = 1/t."""
    a, b = random.sample(range(2, 13), 2)
    t = Fraction(a * b, a + b)
    problem = (
        f"One pump fills a tank in ${a}$ hours and another in ${b}$ hours. Working together, how many hours do they take? "
        f"{_FRACTION_HINT}"
    )
    solution = frac_from(t)
    s = Steps()
    s.step("Add the rates (tanks per hour).", rf"\frac{{1}}{{{a}}} + \frac{{1}}{{{b}}} = \frac{{{a + b}}}{{{a * b}}}")
    s.step("The time is the reciprocal of the combined rate.", rf"t = \frac{{{a * b}}}{{{a + b}}} = {_tex(t)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_rational_equation.variant("round_trip_speed")
def _rational_round_trip():
    """Average speed for a round trip is the harmonic mean, not the plain average."""
    v1, v2 = random.sample(range(20, 81, 5), 2)
    avg = Fraction(2 * v1 * v2, v1 + v2)
    problem = (
        f"A car drives to a town at ${v1}$ mph and back along the same road at ${v2}$ mph. What is its average speed for the "
        f"whole trip, in mph? {_ROUND}"
    )
    solution = num(avg)
    s = Steps()
    s.step("Let the distance each way be $d$. Total time is the sum of the two times.", rf"t = \frac{{d}}{{{v1}}} + \frac{{d}}{{{v2}}}")
    s.step("Average speed is total distance over total time.", rf"\frac{{2d}}{{t}} = \frac{{2({v1})({v2})}}{{{v1} + {v2}}} \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_complex_modulus.variant("missing_part")
def _modulus_missing_part():
    """Reverse: a missing real part from the modulus."""
    p, q, r = random.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)])
    a, b = (p, q) if random.random() < 0.5 else (q, p)
    problem = f"If $|a {'+' if random.random() < 0.5 else '-'} {b}i| = {r}$ and $a > 0$, what is $a$?"
    solution = f"{a}"
    s = Steps()
    s.step("The modulus squared is the sum of the squared parts.", f"a^2 + {b}^2 = {r}^2 \\Rightarrow a^2 = {r * r - b * b}")
    s.step("Take the positive root.", f"a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_complex_modulus.variant("distance")
def _modulus_distance():
    """The distance between two complex numbers is |z - w|."""
    z = complex(random.randint(-9, 9), random.randint(-9, 9))
    w = complex(random.randint(-9, 9), random.randint(-9, 9))
    d = abs(z - w)
    fmt = lambda c: f"{int(c.real)} {'+' if c.imag >= 0 else '-'} {abs(int(c.imag))}i"  # noqa: E731
    problem = f"How far apart are ${fmt(z)}$ and ${fmt(w)}$ in the complex plane? {_ROUND}"
    solution = num(d)
    s = Steps()
    s.step("The distance is the modulus of the difference.", rf"|({fmt(z)}) - ({fmt(w)})| = |{fmt(z - w)}| \approx {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_rational_root_list.variant("is_candidate")
def _rational_root_is_candidate():
    """Is a given fraction on the rational-root candidate list?"""
    a = random.randint(2, 12)
    c = _nonzero(-30, 30)
    p, q = random.randint(1, 12), random.randint(1, 12)
    g = math.gcd(p, q)
    p, q = p // g, q // g
    candidate = Fraction(random.choice([1, -1]) * p, q)
    ok = abs(c) % p == 0 and a % q == 0
    problem = (
        f"Could ${frac_from(candidate)}$ be a rational root of ${_poly([a, 0, 5, c])}$ according to the rational root theorem? "
        "Answer yes or no."
    )
    answer = "yes" if ok else "no"
    s = Steps()
    s.step(f"In lowest terms ${frac_from(candidate)}$, the numerator must divide ${abs(c)}$ and the denominator must divide ${a}$.")
    s.step(f"${p}$ {'divides' if abs(c) % p == 0 else 'does not divide'} ${abs(c)}$; ${q}$ {'divides' if a % q == 0 else 'does not divide'} ${a}$.")
    s.answer(answer)
    return problem, answer, s.done()


@algebra2.alg2_solve_system_three.variant("ticket_types")
def _system_three_tickets():
    """Three ticket types: how many of one kind?"""
    while True:   # the system's determinant is p1 + p3 - 2*p2; nonzero means one answer
        prices = random.sample(range(4, 20), 3)
        if prices[0] + prices[2] != 2 * prices[1]:
            break
    counts = [random.randint(1, 30) for _ in range(3)]
    total = sum(counts)
    revenue = sum(p * c for p, c in zip(prices, counts))
    extra = counts[0] - counts[2]
    problem = (
        f"A theater sold ${total}$ tickets: adult (${prices[0]}$ dollars), student (${prices[1]}$ dollars), and child "
        f"(${prices[2]}$ dollars), for ${revenue}$ dollars in all. It sold ${abs(extra)}$ {'more' if extra >= 0 else 'fewer'} "
        "adult tickets than child tickets. How many student tickets were sold?"
    )
    solution = f"{counts[1]}"
    s = Steps()
    s.step("Let $a, s, c$ be the counts.", rf"a + s + c = {total}, \quad {prices[0]}a + {prices[1]}s + {prices[2]}c = {revenue}, \quad a - c = {extra}")
    s.step("Solving the system gives", f"a = {counts[0]}, s = {counts[1]}, c = {counts[2]}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_matrix_operation.variant("missing_matrix_entry")
def _matrix_missing_entry():
    """A + X = B: an entry of X."""
    A = [[random.randint(-9, 9) for _ in range(2)] for _ in range(2)]
    B = [[random.randint(-9, 9) for _ in range(2)] for _ in range(2)]
    i, j = random.randrange(2), random.randrange(2)
    problem = (
        f"If ${_matrix_tex(A)} + X = {_matrix_tex(B)}$, what is the entry of $X$ in row {i + 1}, column {j + 1}?"
    )
    solution = f"{B[i][j] - A[i][j]}"
    s = Steps()
    s.step("Matrices add entry by entry, so subtract.", f"x_{{{i + 1}{j + 1}}} = {B[i][j]} - {paren(A[i][j])} = {B[i][j] - A[i][j]}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.int_matrix_22_determinant.variant("scaled_matrix")
def _determinant_scaled():
    """det(kA) = k^2 det(A) for a 2x2 matrix."""
    d = _nonzero(-12, 12)
    k = random.randint(2, 5)
    problem = f"A $2 \\times 2$ matrix $A$ has $\\det A = {d}$. What is $\\det({k}A)$?"
    solution = f"{k * k * d}"
    s = Steps()
    s.step(f"Multiplying a $2 \\times 2$ matrix by ${k}$ multiplies each of its $2$ rows by ${k}$, so the determinant is multiplied by ${k}^2$.",
           f"{k}^2 \\times {paren(d)} = {k * k * d}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.int_matrix_22_determinant.variant("parallelogram_area")
def _determinant_area():
    """The area of the parallelogram spanned by two vectors is |det|."""
    u = (random.randint(-9, 9), random.randint(-9, 9))
    v = (random.randint(-9, 9), random.randint(-9, 9))
    if u[0] * v[1] - u[1] * v[0] == 0:
        v = (v[0] + 1, v[1])
    area = abs(u[0] * v[1] - u[1] * v[0])
    problem = f"What is the area of the parallelogram with sides along the vectors $({u[0]}, {u[1]})$ and $({v[0]}, {v[1]})$?"
    solution = f"{area}"
    s = Steps()
    s.step("The area is the absolute value of the determinant of the vectors.", rf"\left|{u[0]}({v[1]}) - ({u[1]})({v[0]})\right| = {area}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_solve_polynomial_factoring.variant("by_grouping")
def _polynomial_by_grouping():
    """x^3 + ax^2 - b^2x - ab^2 = (x + a)(x^2 - b^2): the largest root."""
    a, b = _nonzero(-8, 8), random.randint(1, 8)
    coeffs = [1, a, -b * b, -a * b * b]
    roots = {-a, b, -b}
    problem = f"Factor by grouping to solve ${_poly(coeffs)} = 0$. What is the largest solution?"
    solution = f"{max(roots)}"
    s = Steps()
    s.step("Group the first two and last two terms.", f"x^2(x {'+' if a > 0 else '-'} {abs(a)}) - {b * b}(x {'+' if a > 0 else '-'} {abs(a)})")
    s.step("Factor out the common binomial, then the difference of squares.", f"(x {'+' if a > 0 else '-'} {abs(a)})(x - {b})(x + {b}) = 0")
    s.answer(solution, lead="The largest solution is")
    return problem, solution, s.done()


@algebra2.alg2_solve_polynomial_factoring.variant("sum_of_roots")
def _polynomial_sum_of_roots():
    """Vieta: the sum of a monic cubic's roots is minus its x^2 coefficient."""
    roots = random.sample(range(-9, 10), 3)
    coeffs = [1, -sum(roots), roots[0] * roots[1] + roots[0] * roots[2] + roots[1] * roots[2], -math.prod(roots)]
    problem = f"What is the sum of the solutions of ${_poly(coeffs)} = 0$?"
    solution = f"{sum(roots)}"
    s = Steps()
    s.step("For a monic cubic, the roots add up to minus the $x^2$ coefficient (no need to solve).", f"-({coeffs[1]}) = {sum(roots)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_conic_equation.variant("asymptote_slope")
def _conic_asymptote_slope():
    r"""The positive asymptote slope of $\frac{x^2}{a^2} - \frac{y^2}{b^2} = 1$ is b/a."""
    a, b = random.sample(range(1, 11), 2)
    problem = (
        f"What is the positive slope of an asymptote of the hyperbola $\\frac{{x^2}}{{{a * a}}} - \\frac{{y^2}}{{{b * b}}} = 1$? "
        f"{_FRACTION_HINT}"
    )
    solution = frac_from(Fraction(b, a))
    s = Steps()
    s.step("The asymptotes are $y = \\pm\\frac{b}{a}x$.", rf"\frac{{\sqrt{{{b * b}}}}}{{\sqrt{{{a * a}}}}} = {_tex(Fraction(b, a))}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_polynomial_end_behavior.variant("turning_points")
def _end_behavior_turning_points():
    """A degree-n polynomial has at most n - 1 turning points."""
    n = random.randint(2, 9)
    coeffs = [_nonzero(-5, 5)] + [random.randint(-5, 5) for _ in range(n)]
    problem = f"What is the greatest number of turning points the graph of ${_poly(coeffs)}$ can have?"
    solution = f"{n - 1}"
    s = Steps()
    s.step(f"The degree is ${n}$, and a polynomial of degree $n$ has at most $n - 1$ turning points.", f"{n} - 1 = {n - 1}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_empirical_rule.variant("count_in_range")
def _empirical_count():
    """How many of N values fall within k standard deviations."""
    n = random.choice([200, 400, 500, 1000, 2000])
    k = random.choice([1, 2, 3])
    pct = {1: Fraction(68), 2: Fraction(95), 3: Fraction(997, 10)}[k]
    mu, sd = random.randint(20, 100), random.randint(2, 15)
    problem = (
        f"Scores are normally distributed with mean ${mu}$ and standard deviation ${sd}$. Out of ${n}$ scores, about how many "
        f"are between ${mu - k * sd}$ and ${mu + k * sd}$? Use the 68-95-99.7 rule."
    )
    solution = num(n * pct / 100)
    s = Steps()
    s.step(f"That range is within ${k}$ standard deviation{'s' if k > 1 else ''} of the mean: about ${num(pct)}\\%$.",
           rf"{num(pct / 100)} \times {n} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra2.alg2_empirical_rule.variant("sd_from_range")
def _empirical_sd_from_range():
    """Reverse: the middle 95% spans 4 standard deviations."""
    mu, sd = random.randint(20, 200), random.randint(1, 20)
    k = random.choice([1, 2, 3])
    pct = {1: "68", 2: "95", 3: "99.7"}[k]
    problem = (
        f"For a normal distribution, the middle {pct}% of values lie between ${mu - k * sd}$ and ${mu + k * sd}$. What is the "
        "standard deviation?"
    )
    solution = f"{sd}"
    s = Steps()
    s.step(f"The middle {pct}% is within ${k}$ standard deviation{'s' if k > 1 else ''} on each side, ${2 * k}$ in all.",
           rf"\frac{{{mu + k * sd} - {mu - k * sd}}}{{{2 * k}}} = {sd}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.arithmetic_progression_term.variant("which_term")
def _ap_which_term():
    """Reverse: which term has a given value (or how many terms a list has)?"""
    a1, d = random.randint(-20, 20), _nonzero(-9, 9)
    n = random.randint(5, 60)
    last = a1 + (n - 1) * d
    if random.random() < 0.5:
        problem = f"In the arithmetic sequence ${a1}, {a1 + d}, {a1 + 2 * d}, \\ldots$, which term is ${last}$?"
    else:
        problem = f"How many terms are in the list ${a1}, {a1 + d}, {a1 + 2 * d}, \\ldots, {last}$?"
    solution = f"{n}"
    s = Steps()
    s.step("Solve $a_1 + (n - 1)d = a_n$ for $n$.", f"{a1} + (n - 1)({d}) = {last} \\Rightarrow n - 1 = {n - 1}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.arithmetic_progression_sum.variant("odd_numbers")
def _ap_sum_odd_numbers():
    """The first n odd numbers add up to n^2."""
    n = random.randint(5, 60)
    problem = f"What is $1 + 3 + 5 + \\cdots + {2 * n - 1}$?"
    solution = f"{n * n}"
    s = Steps()
    s.step(f"These are the first ${n}$ odd numbers, which always add to $n^2$.", f"{n}^2 = {n * n}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.arithmetic_progression_sum.variant("theater_rows")
def _ap_sum_theater():
    """Seats in a theater whose rows grow by a fixed amount."""
    first, d, rows = random.randint(10, 30), random.randint(1, 4), random.randint(8, 30)
    total = rows * (2 * first + (rows - 1) * d) // 2
    problem = (
        f"A theater's first row has ${first}$ seats, and each row has ${d}$ more than the row before. How many seats are in "
        f"${rows}$ rows?"
    )
    solution = f"{total}"
    last = first + (rows - 1) * d
    s = Steps()
    s.step("The last row has", f"{first} + {rows - 1}({d}) = {last}")
    s.formula("The sum", rf"\frac{{{rows}}}{{2}}({first} + {last}) = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.geometric_progression.variant("geometric_mean")
def _gp_geometric_mean():
    """The missing middle term of three positive terms in a geometric sequence."""
    a, r = random.randint(1, 9), random.randint(2, 6)
    problem = f"$ {a}, x, {a * r * r}$ are consecutive terms of a geometric sequence with $x > 0$. What is $x$?"
    solution = f"{a * r}"
    s = Steps()
    s.step("The middle term of a geometric sequence is the geometric mean of its neighbors.", rf"x = \sqrt{{{a} \times {a * r * r}}} = {a * r}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.combinations.variant("at_least_one")
def _combinations_at_least_one():
    """Committees with at least one member from a group (complement counting)."""
    girls, boys = random.randint(2, 7), random.randint(2, 7)
    k = random.randint(2, min(4, girls + boys - 1))
    total = math.comb(girls + boys, k)
    none = math.comb(boys, k)
    problem = (
        f"A committee of ${k}$ is chosen from ${girls}$ girls and ${boys}$ boys. How many committees include at least one girl?"
    )
    solution = f"{total - none}"
    s = Steps()
    s.step("Count all committees, then subtract those with no girls.",
           rf"\binom{{{girls + boys}}}{{{k}}} - \binom{{{boys}}}{{{k}}} = {total} - {none} = {total - none}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.combinations.variant("symmetry")
def _combinations_symmetry():
    r"""$\binom{n}{r} = \binom{n}{n - r}$: compute the easy side."""
    n = random.randint(10, 30)
    r = n - random.randint(1, 3)
    problem = rf"Evaluate $\binom{{{n}}}{{{r}}}$."
    solution = f"{math.comb(n, r)}"
    s = Steps()
    s.step("Choosing what to take is the same as choosing what to leave.", rf"\binom{{{n}}}{{{r}}} = \binom{{{n}}}{{{n - r}}} = {math.comb(n, r)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.permutation.variant("repeated_letters")
def _permutation_repeated_letters():
    """Arrangements of a word with repeated letters."""
    word = random.choice(["LEVEL", "BANANA", "PEPPER", "BOOK", "APPLE", "TOOTH", "COFFEE", "LETTER", "PIZZA", "ASSESS"])
    from collections import Counter
    counts = Counter(word)
    total = math.factorial(len(word)) // math.prod(math.factorial(c) for c in counts.values())
    problem = f"How many different arrangements are there of the letters in {word}?"
    solution = f"{total}"
    reps = ", ".join(f"{ch} {c} times" for ch, c in counts.items() if c > 1)
    s = Steps()
    divisors = r" \cdot ".join(f"{c}!" for c in counts.values() if c > 1)
    s.step(f"Arrange all {len(word)} letters, then divide out the repeats ({reps}).",
           rf"\frac{{{len(word)}!}}{{{divisors}}} = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_algebra_extra_gen.permutation.variant("pair_together")
def _permutation_pair_together():
    """Arrangements in a row with two particular people side by side."""
    n = random.randint(4, 8)
    total = 2 * math.factorial(n - 1)
    problem = f"In how many ways can ${n}$ people stand in a line if two of them, Ana and Ben, must stand next to each other?"
    solution = f"{total}"
    s = Steps()
    s.step("Glue Ana and Ben into one block: arrange the block with the others.", f"({n} - 1)! = {math.factorial(n - 1)}")
    s.step("Inside the block they can be in either order.", rf"2 \times {math.factorial(n - 1)} = {total}")
    s.answer(solution)
    return problem, solution, s.done()


@sets_gen.set_operation.variant("missing_region")
def _sets_missing_region():
    """A missing Venn-diagram count from the totals."""
    both = random.randint(1, 15)
    only_a, only_b = random.randint(1, 20), random.randint(1, 20)
    a, b = only_a + both, only_b + both
    union = only_a + only_b + both
    problem = (
        f"$|A| = {a}$, $|B| = {b}$, and $|A \\cup B| = {union}$. How many elements are in both $A$ and $B$?"
    )
    solution = f"{both}"
    s = Steps()
    s.step("Inclusion-exclusion: $|A \\cup B| = |A| + |B| - |A \\cap B|$.", f"{union} = {a} + {b} - x \\Rightarrow x = {both}")
    s.answer(solution)
    return problem, solution, s.done()
