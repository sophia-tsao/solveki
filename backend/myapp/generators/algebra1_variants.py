"""Extra question types for the Algebra I topics.

Variants for the generators in ``algebra1.py`` and for the library-override
generators the Algebra I course uses (``lib_powers_gen``, ``lib_fractions_gen``,
``lib_algebra_extra_gen``, ``algebra``). Each attaches to its topic's
dispatcher (see ``_variants.with_variants``); the original question stays as
the ``classic`` variant. Variants only use their own topic's skill. See
docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num
from ._steps import Steps, paren, tex_frac
from . import algebra, algebra1, lib_algebra_extra_gen, lib_fractions_gen, lib_powers_gen
from .algebra1 import _FRACTION_HINT, _quadratic, _tex, _term
from .algebra2 import alg2_solve_system_matrix
from .prealgebra_variants import _table, _two_step_think_of_a_number


def _nonzero(lo, hi):
    return random.choice([i for i in range(lo, hi + 1) if i != 0])


def _plus(n):
    """`` + n`` / `` - n`` for a nonzero int, ``""`` for zero."""
    if n == 0:
        return ""
    return f" + {n}" if n > 0 else f" - {-n}"


def _linear(a, b):
    """``ax + b`` in LaTeX."""
    return f"{_term(a)}{_plus(b)}"


def _xy(a, b, c):
    sign = "+" if b > 0 else "-"
    return f"{_term(a)} {sign} {_term(abs(b), 'y')} = {c}"


def _frac(value):
    return f"${frac_from(value)}$"


# --- Systems (shared by every 2x2-system topic) --------------------------------

def _system_sum_without_solving(max_coeff=6):
    """SAT-style: x + y from a symmetric system, by adding the equations."""
    while True:
        p, q = random.sample(range(1, max_coeff + 1), 2)
        x, y = random.randint(-8, 8), random.randint(-8, 8)
        if (x + y) != 0:
            break
    e1, e2 = p * x + q * y, q * x + p * y
    problem = (
        f"If ${_xy(p, q, e1)}$ and ${_xy(q, p, e2)}$, what is the value of $x + y$?"
    )
    solution = f"${x + y}$"
    s = Steps()
    s.step("You don't need $x$ and $y$ separately. Add the two equations: the $x$ and "
           "$y$ coefficients match.", f"{p + q}x + {p + q}y = {e1 + e2}")
    s.step(f"Factor out ${p + q}$.", f"{p + q}(x + y) = {e1 + e2}")
    s.step(f"Divide both sides by ${p + q}$.", f"x + y = {x + y}")
    s.answer(solution)
    return problem, solution, s.done()


def _system_no_solution_parameter(max_coeff=6):
    """For what k does the system have no solution?"""
    from .prealgebra_variants import _system_no_solution_parameter as pre_version
    return pre_version(max_coeff=max_coeff)


for _gen in (algebra1.alg1_solve_system, lib_powers_gen.system_of_equations,
             lib_algebra_extra_gen.linear_equations, alg2_solve_system_matrix):
    _gen.variant("sum_without_solving")(_system_sum_without_solving)
    _gen.variant("no_solution_parameter")(_system_no_solution_parameter)


@lib_algebra_extra_gen.intersection_of_two_lines.variant("line_through_points")
def _intersection_line_through_points(max_slope=5, max_intercept=10):
    """One line is given by two of its points instead of its equation."""
    x0, y0 = random.randint(-6, 6), random.randint(-10, 10)
    m1, m2 = random.sample([m for m in range(-max_slope, max_slope + 1) if m != 0], 2)
    b2 = y0 - m2 * x0
    # Line 1 through the intersection point's neighbours: (x0 - d, ...) and (x0 + d, ...).
    xa, xb = x0 + random.randint(-4, -1), x0 + random.randint(1, 4)
    ya, yb = y0 + m1 * (xa - x0), y0 + m1 * (xb - x0)
    b1 = y0 - m1 * x0
    problem = (
        f"Line $L$ passes through $({xa}, {ya})$ and $({xb}, {yb})$. Line $M$ is "
        f"$y = {_linear(m2, b2)}$. Where do they intersect? Format your answer as (x, y)."
    )
    solution = f"({x0}, {y0})"
    s = Steps()
    s.step("Find the slope of $L$.",
           rf"m = \frac{{{yb} - {paren(ya)}}}{{{xb} - {paren(xa)}}} = {m1}")
    s.step(f"Find $L$'s y-intercept from $({xa}, {ya})$.",
           f"b = {ya} - {paren(m1)}({xa}) = {b1}")
    s.step("Set the two lines equal and solve for $x$.",
           f"{_linear(m1, b1)} = {_linear(m2, b2)} \\Rightarrow x = {x0}")
    s.step("Substitute into either line to find $y$.", f"y = {y0}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Equations, inequalities, absolute value ----------------------------------

lib_algebra_extra_gen.basic_algebra.variant("think_of_a_number")(_two_step_think_of_a_number)


@algebra1.alg1_absolute_value_equation.variant("sum_of_solutions")
def _abs_sum_of_solutions(max_a=6, min_b=-10, max_b=10, max_c=15):
    """SAT-style: the sum of the solutions of |ax + b| = c is -2b/a."""
    a = random.randint(1, max_a)
    b = _nonzero(min_b, max_b)
    c = random.randint(1, max_c)
    total = Fraction(-2 * b, a)
    problem = f"What is the sum of the solutions of $|{_linear(a, b)}| = {c}$? {_FRACTION_HINT}"
    solution = _frac(total)
    r1, r2 = Fraction(c - b, a), Fraction(-c - b, a)
    s = Steps()
    s.step("The expression inside is either $c$ or $-c$.",
           f"{_linear(a, b)} = {c} \\quad \\text{{or}} \\quad {_linear(a, b)} = {-c}")
    s.step("Solve each.", f"x = {_tex(r1)} \\quad \\text{{or}} \\quad x = {_tex(r2)}")
    s.step("Add them.", f"{_tex(r1)} + {paren(_tex(r2))} = {_tex(total)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_absolute_value_equation.variant("count_solutions")
def _abs_count_solutions(max_a=6, min_b=-10, max_b=10, max_c=15):
    """How many solutions |ax + b| + d = e has (0, 1, or 2)."""
    a = random.randint(1, max_a)
    b = _nonzero(min_b, max_b)
    d = random.randint(-9, 9)
    c = random.choice([random.randint(1, max_c), 0, -random.randint(1, max_c)])
    e = c + d
    count = 2 if c > 0 else (1 if c == 0 else 0)
    problem = f"How many solutions does $|{_linear(a, b)}|{_plus(d)} = {e}$ have?"
    solution = f"${count}$"
    s = Steps()
    if d:
        s.step("Isolate the absolute value.", f"|{_linear(a, b)}| = {c}")
    if c > 0:
        s.step(f"An absolute value equal to a positive number (${c}$) has two solutions: the "
               "inside is $c$ or $-c$.")
    elif c == 0:
        s.step("An absolute value equal to $0$ has one solution: the inside must be $0$.")
    else:
        s.step(f"An absolute value is never negative, so it can't equal ${c}$: no solutions.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_linear_inequality_solve.variant("count_integers")
def _inequality_count_integers(max_a=6):
    """How many integers satisfy a compound inequality lo < ax + b <= hi."""
    a = random.randint(2, max_a)
    b = random.randint(-9, 9)
    lo = random.randint(-20, 10)
    hi = lo + random.randint(a, 6 * a)
    count = sum(1 for x in range(-100, 101) if lo < a * x + b <= hi)
    problem = f"How many integers $x$ satisfy ${lo} < {_linear(a, b)} \\leq {hi}$?"
    solution = f"${count}$"
    left, right = Fraction(lo - b, a), Fraction(hi - b, a)
    s = Steps()
    s.step(f"Subtract ${b}$ from all three parts, then divide by ${a}$." if b
           else f"Divide all three parts by ${a}$.",
           f"{_tex(left)} < x \\leq {_tex(right)}")
    first, last = math.floor(left) + 1, math.floor(right)
    s.step(f"The integers in that range run from ${first}$ to ${last}$.",
           f"{last} - {paren(first)} + 1 = {count}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_abs_value_inequality.variant("write_as_absolute")
def _abs_inequality_write_as_absolute():
    """Reverse: write lo < x < hi as |x - c| < r; give c or r."""
    c = random.randint(-10, 10)
    r = random.randint(1, 10)
    lo, hi = c - r, c + r
    ask_center = random.random() < 0.5
    want = "c" if ask_center else "r"
    problem = (
        f"The inequality ${lo} < x < {hi}$ can be written as $|x - c| < r$. "
        f"What is ${want}$?"
    )
    solution = f"${c if ask_center else r}$"
    s = Steps()
    s.step("$|x - c| < r$ means $x$ is within $r$ of $c$: $c$ is the midpoint of the "
           "interval and $r$ is half its length.")
    s.step("Find the midpoint.", rf"c = \frac{{{lo} + {paren(hi)}}}{{2}} = {c}")
    s.step("Find half the length.", rf"r = \frac{{{hi} - {paren(lo)}}}{{2}} = {r}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Exponents and radicals -----------------------------------------------------

@algebra1.alg1_product_of_powers.variant("missing_exponent")
def _product_missing_exponent(min_base=2, max_base=12, min_exp=2, max_exp=8):
    r"""$a^m \cdot a^{\square} = a^n$."""
    a = random.randint(min_base, max_base)
    m = random.randint(min_exp, max_exp)
    k = random.randint(min_exp, max_exp)
    problem = rf"Fill in the box: ${a}^{{{m}}} \cdot {a}^{{\square}} = {a}^{{{m + k}}}$."
    solution = f"${k}$"
    s = Steps()
    s.step("Multiplying powers with the same base adds the exponents.",
           f"{m} + \\square = {m + k}")
    s.step(f"Subtract ${m}$.", f"\\square = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_power_of_product.variant("missing_power")
def _power_of_product_missing(min_exp=2, max_exp=6):
    r"""$(cx^p)^{\square} = c^n x^{pn}$."""
    c = random.randint(2, 4)
    p = random.randint(1, 4)
    n = random.randint(min_exp, 4 if c > 2 else max_exp)
    coef = c ** n
    var = "x" if p == 1 else f"x^{{{p}}}"
    problem = rf"Fill in the box: $({c}{var})^{{\square}} = {coef}x^{{{p * n}}}$."
    solution = f"${n}$"
    s = Steps()
    s.step("A power of a product raises each factor to that power, and a power of a power "
           "multiplies the exponents.", rf"({c}{var})^n = {c}^n x^{{{p}n}}")
    s.step(f"Match the exponent of $x$: ${p}n = {p * n}$.", f"n = {n}")
    s.step("Check the coefficient.", f"{c}^{{{n}}} = {coef}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_negative_exponent.variant("as_power")
def _negative_exponent_as_power(min_base=2, max_base=5, min_exp=2, max_exp=5):
    r"""$\frac{1}{32} = 2^{\square}$."""
    a = random.randint(min_base, max_base)
    n = random.randint(min_exp, max_exp if a < 4 else 3)
    problem = rf"Fill in the box: $\frac{{1}}{{{a ** n}}} = {a}^{{\square}}$."
    solution = f"${-n}$"
    s = Steps()
    s.step(f"Write the denominator as a power of ${a}$.", rf"\frac{{1}}{{{a ** n}}} = \frac{{1}}{{{a}^{{{n}}}}}")
    s.step("A reciprocal of a power is the power with a negative exponent.",
           rf"\frac{{1}}{{{a}^{{{n}}}}} = {a}^{{{-n}}}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_simplify_radical.variant("add_radicals")
def _radical_add(min_factor=2, max_factor=9):
    r"""$\sqrt{8} + \sqrt{18} = \square\sqrt{2}$."""
    b = random.choice([2, 3, 5, 6, 7])
    p, q = random.sample(range(1, 7), 2)
    problem = (
        rf"Fill in the box: $\sqrt{{{p * p * b}}} + \sqrt{{{q * q * b}}} = \square\sqrt{{{b}}}$."
    )
    solution = f"${p + q}$"
    s = Steps()
    s.step(f"Simplify each radical by pulling out a perfect square factor of ${b}$'s multiple.",
           rf"\sqrt{{{p * p * b}}} = {p}\sqrt{{{b}}}, \quad \sqrt{{{q * q * b}}} = {q}\sqrt{{{b}}}")
    s.step("Add like radicals the way you add like terms.",
           rf"{p}\sqrt{{{b}}} + {q}\sqrt{{{b}}} = {p + q}\sqrt{{{b}}}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_powers_gen.power_of_powers.variant("rewrite_base")
def _power_of_powers_rewrite_base():
    r"""$8^4 = 2^{\square}$: a base that is itself a power."""
    base = random.choice([2, 3, 5])
    p = random.randint(2, 4 if base < 5 else 3)
    n = random.randint(2, 6)
    problem = rf"Fill in the box: ${base ** p}^{{{n}}} = {base}^{{\square}}$."
    solution = f"${p * n}$"
    s = Steps()
    s.step(f"Write ${base ** p}$ as a power of ${base}$.", f"{base ** p} = {base}^{{{p}}}")
    s.step("A power of a power multiplies the exponents.",
           rf"({base}^{{{p}}})^{{{n}}} = {base}^{{{p * n}}}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_powers_gen.quotient_of_power_same_base.variant("missing_exponent")
def _quotient_missing_exponent(min_base=2, max_base=20, min_exp=2, max_exp=9):
    r"""$\frac{a^m}{a^{\square}} = a^n$."""
    a = random.randint(min_base, max_base)
    k = random.randint(min_exp, max_exp)
    n = random.randint(1, max_exp)
    m = n + k
    problem = rf"Fill in the box: $\frac{{{a}^{{{m}}}}}{{{a}^{{\square}}}} = {a}^{{{n}}}$."
    solution = f"${k}$"
    s = Steps()
    s.step("Dividing powers with the same base subtracts the exponents.",
           f"{m} - \\square = {n}")
    s.step("Solve.", f"\\square = {m} - {n} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_powers_gen.quotient_of_power_same_power.variant("evaluate_base_first")
def _quotient_same_power_evaluate():
    r"""$\frac{12^3}{4^3} = (12/4)^3 = 27$: divide the bases first."""
    q = random.randint(2, 5)
    b = random.randint(2, 9)
    n = random.randint(2, 4 if q <= 3 else 3)
    a = q * b
    problem = rf"Evaluate $\frac{{{a}^{{{n}}}}}{{{b}^{{{n}}}}}$."
    solution = f"${q ** n}$"
    s = Steps()
    s.step("Powers with the same exponent can be divided by dividing the bases.",
           rf"\frac{{{a}^{{{n}}}}}{{{b}^{{{n}}}}} = \left(\frac{{{a}}}{{{b}}}\right)^{{{n}}} = {q}^{{{n}}}")
    s.step("Evaluate.", f"{q}^{{{n}}} = {q ** n}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_powers_gen.product_of_scientific_notations.variant("missing_factor")
def _sci_product_missing_factor(min_exp=-9, max_exp=9):
    r"""$(3 \times 10^4)(\square \times 10^5) = 6 \times 10^9$."""
    m1 = random.randint(2, 4)
    m2 = random.randint(1, 9 // m1)
    e1, e2 = random.randint(min_exp, max_exp), random.randint(min_exp, max_exp)
    problem = (
        rf"Fill in the box: $({m1} \times 10^{{{e1}}})(\square \times 10^{{{e2}}}) = "
        rf"{m1 * m2} \times 10^{{{e1 + e2}}}$."
    )
    solution = f"${m2}$"
    s = Steps()
    s.step("Multiplying multiplies the numbers in front and adds the exponents. The exponents "
           f"already add up: ${e1} + {paren(e2)} = {e1 + e2}$.")
    s.step("So the numbers in front must multiply to the product's number.",
           rf"{m1} \times \square = {m1 * m2} \Rightarrow \square = {m2}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Polynomials ------------------------------------------------------------------

def _binomial_missing_constant(max_coef=6, max_const=8):
    """Reverse: (ax + b)(x + k) expanded is given; find k."""
    a = random.randint(1, max_coef)
    b = _nonzero(-max_const, max_const)
    k = _nonzero(-max_const, max_const)
    expanded = _quadratic(a, a * k + b, b * k)
    problem = f"If $({_linear(a, b)})(x + k) = {expanded}$, what is $k$?"
    solution = f"${k}$"
    s = Steps()
    s.step("Expand the left side. Its constant term is the product of the constants.",
           f"({_linear(a, b)})(x + k) = {_term(a, 'x^2')} + ({_term(a, 'k')}{_plus(b)})x + {_term(b, 'k')}")
    s.step("Match the constant terms.", f"{_term(b, 'k')} = {b * k}")
    if b != 1:
        s.step(f"Divide by ${b}$.", f"k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


algebra1.alg1_multiply_binomials.variant("missing_constant")(_binomial_missing_constant)
lib_algebra_extra_gen.expanding.variant("missing_constant")(_binomial_missing_constant)


@algebra1.factoring.variant("count_factorable")
def _factoring_count_factorable():
    """For how many integers b is x^2 + bx + c factorable over the integers?"""
    c = random.choice([n for n in range(-36, 37) if n != 0])
    sums = {p + c // p for p in range(-abs(c), abs(c) + 1) if p != 0 and c % p == 0}
    problem = (
        f"For how many integers $b$ can $x^2 + bx {'+' if c > 0 else '-'} {abs(c)}$ be "
        "factored as $(x + p)(x + q)$ with integers $p$ and $q$?"
    )
    solution = f"${len(sums)}$"
    pairs = sorted({tuple(sorted((p, c // p))) for p in range(-abs(c), abs(c) + 1)
                    if p != 0 and c % p == 0})
    s = Steps()
    s.step(f"$(x + p)(x + q) = x^2 + (p + q)x + pq$, so $pq = {c}$ and $b = p + q$.")
    s.step(f"List the integer pairs with product ${c}$.",
           r",\ ".join(f"({p}, {q})" for p, q in pairs))
    s.step("Each pair gives $b = p + q$; count the different sums.",
           r",\ ".join(sorted({str(p + q) for p, q in pairs}, key=int)))
    s.answer(solution)
    return problem, solution, s.done()


@lib_powers_gen.combine_like_terms.variant("coefficient_after_distributing")
def _combine_coefficient_after_distributing():
    """The x-coefficient of a(x + b) - c(x + d) + ex."""
    a, c, e = random.randint(2, 9), random.randint(2, 9), _nonzero(-9, 9)
    b, d = _nonzero(-9, 9), _nonzero(-9, 9)
    coef = a - c + e
    problem = (
        f"Simplify ${a}(x{_plus(b)}) - {c}(x{_plus(d)}) {'+' if e > 0 else '-'} {_term(abs(e))}$. "
        "What is the coefficient of $x$?"
    )
    solution = f"${coef}$"
    s = Steps()
    s.step("Distribute.", f"{a}x{_plus(a * b)} - {c}x{_plus(-c * d)}{_plus(e)}x")
    s.step("Combine the $x$-terms.", f"{a} - {c} + {paren(e)} = {coef}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_complete_the_square.variant("missing_constant")
def _complete_square_missing_constant(max_shift=8):
    r"""$x^2 + bx + \square$ is a perfect square trinomial."""
    b = _nonzero(-2 * max_shift, 2 * max_shift)
    value = Fraction(b, 2) ** 2
    hint = "" if b % 2 == 0 else f" {_FRACTION_HINT}"
    problem = (
        f"What number goes in the box to make $x^2 {'+' if b > 0 else '-'} "
        f"{_term(abs(b))} + \\square$ a perfect square trinomial?{hint}"
    )
    solution = _frac(value)
    s = Steps()
    s.step("A perfect square trinomial $x^2 + bx + c$ has $c = (b/2)^2$.")
    s.step("Halve the coefficient of $x$ and square it.",
           rf"\left({_tex(Fraction(b, 2))}\right)^2 = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_simplify_rational.variant("missing_factor")
def _rational_missing_factor(max_root=7):
    r"""$\frac{x^2 + 5x + 6}{x + 2} = x + \square$."""
    a, b = random.sample([n for n in range(-max_root, max_root + 1) if n != 0], 2)
    numerator = _quadratic(1, a + b, a * b)
    problem = (
        rf"For $x \neq {-a}$, $\frac{{{numerator}}}{{{_linear(1, a)}}} = x + \square$. "
        "What number goes in the box?"
    )
    solution = f"${b}$"
    s = Steps()
    s.step(f"Factor the numerator: find two numbers with product ${a * b}$ and sum ${a + b}$.",
           f"{numerator} = ({_linear(1, a)})({_linear(1, b)})")
    s.step(f"Cancel the common factor ${_linear(1, a)}$.", f"x{_plus(b)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Quadratics -----------------------------------------------------------------

@algebra1.alg1_discriminant.variant("largest_c")
def _discriminant_largest_c(max_a=5, min_bc=-9, max_bc=9):
    """Largest integer c giving two real roots of ax^2 + bx + c (a > 0)."""
    a = random.randint(1, max_a)
    b = _nonzero(min_bc, max_bc)
    bound = Fraction(b * b, 4 * a)
    c = math.ceil(bound) - 1
    problem = (
        f"What is the largest integer $c$ for which ${_term(a, 'x^2')} "
        f"{'+' if b > 0 else '-'} {_term(abs(b))} + c = 0$ has two different real solutions?"
    )
    solution = f"${c}$"
    s = Steps()
    s.step("Two different real solutions need a positive discriminant.",
           f"b^2 - 4ac = {b}^2 - 4({a})c = {b * b} - {4 * a}c > 0")
    s.step("Solve for $c$.", f"c < {_tex(bound)}")
    s.step("The largest integer strictly less than that is the answer.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_axis_of_symmetry.variant("from_symmetric_points")
def _axis_from_symmetric_points():
    """The axis from two points with the same y-value."""
    p, q = sorted(random.sample(range(-12, 13), 2))
    v = random.randint(-20, 20)
    axis = Fraction(p + q, 2)
    problem = (
        f"A parabola passes through $({p}, {v})$ and $({q}, {v})$. What is its axis of "
        "symmetry? Give your answer in the form x = a/b, or x = n for an integer."
    )
    solution = f"$x = {frac_from(axis)}$"
    s = Steps()
    s.step("The two points have the same $y$-value, so they are mirror images across the axis "
           "of symmetry: it is halfway between them.")
    s.step("Average the $x$-values.", rf"x = \frac{{{p} + {paren(q)}}}{{2}} = {_tex(axis)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_sum_product_roots.variant("symmetric_expression")
def _roots_symmetric_expression(max_a=5, min_bc=-9, max_bc=9):
    """Sum of reciprocals (-b/c) or of squares (s^2 - 2p) of the roots."""
    a = random.randint(1, max_a)
    b = _nonzero(min_bc, max_bc)
    c = _nonzero(min_bc, max_bc)
    total, product = Fraction(-b, a), Fraction(c, a)
    quad = _quadratic(a, b, c)
    s = Steps()
    s.step("For $ax^2 + bx + c$, the roots $r$ and $s$ have",
           rf"r + s = -\frac{{b}}{{a}} = {_tex(total)}, \quad rs = \frac{{c}}{{a}} = {_tex(product)}")
    if random.random() < 0.5:
        value = total / product
        problem = (
            f"Let $r$ and $s$ be the roots of ${quad} = 0$. What is "
            rf"$\frac{{1}}{{r}} + \frac{{1}}{{s}}$? {_FRACTION_HINT}"
        )
        s.step("Combine the fractions.",
               rf"\frac{{1}}{{r}} + \frac{{1}}{{s}} = \frac{{r + s}}{{rs}} = {_tex(value)}")
    else:
        value = total ** 2 - 2 * product
        problem = (
            f"Let $r$ and $s$ be the roots of ${quad} = 0$. What is $r^2 + s^2$? "
            f"{_FRACTION_HINT}"
        )
        s.step("Use $(r + s)^2 = r^2 + 2rs + s^2$.",
               f"r^2 + s^2 = (r + s)^2 - 2rs = {_tex(value)}")
    solution = _frac(value)
    s.answer(solution)
    return problem, solution, s.done()


@algebra.vertex_form.variant("leading_coefficient")
def _vertex_leading_coefficient(min_val=-10, max_val=10, min_a=-5, max_a=5):
    """Vertex and one more point determine a in y = a(x - h)^2 + k."""
    h, k = random.randint(min_val, max_val), random.randint(min_val, max_val)
    a = _nonzero(min_a, max_a)
    x = h + _nonzero(-3, 3)
    y = a * (x - h) ** 2 + k
    problem = (
        f"A parabola has its vertex at $({h}, {k})$ and passes through $({x}, {y})$. "
        "In the form $y = a(x - h)^2 + k$, what is $a$?"
    )
    solution = f"${a}$"
    s = Steps()
    s.step("Substitute the vertex for $h$ and $k$, and the point for $x$ and $y$.",
           f"{y} = a({x} - {paren(h)})^2 + {paren(k)}")
    s.step("Simplify.", f"{y - k} = {(x - h) ** 2}a")
    s.step(f"Divide by ${(x - h) ** 2}$.", f"a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra.aroc_over_interval.variant("table")
def _aroc_table():
    """Average rate of change between two columns of a table of values."""
    xs = sorted(random.sample(range(-5, 9), 5))
    ys = [random.randint(-30, 30) for _ in xs]
    i, j = sorted(random.sample(range(5), 2))
    rate = Fraction(ys[j] - ys[i], xs[j] - xs[i])
    problem = (
        f"The table shows values of a function $f$. ${_table('x', xs, 'f(x)', ys)}$ "
        f"What is the average rate of change of $f$ from $x = {xs[i]}$ to $x = {xs[j]}$? "
        f"{_FRACTION_HINT}"
    )
    solution = f"${frac_from(rate)}$"
    s = Steps()
    s.formula("The average rate of change", r"\frac{f(b) - f(a)}{b - a}")
    s.substitute(rf"\frac{{{ys[j]} - {paren(ys[i])}}}{{{xs[j]} - {paren(xs[i])}}} = "
                 rf"\frac{{{ys[j] - ys[i]}}}{{{xs[j] - xs[i]}}} = {_tex(rate)}",
                 text="Read the two values from the table and substitute.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Functions and lines ----------------------------------------------------------

@algebra1.alg1_evaluate_exponential.variant("solve_for_x")
def _exponential_solve_for_x(max_a=10, min_base=2, max_base=6):
    """Reverse: a * b^x = N, find the whole-number x."""
    a = random.randint(1, max_a)
    b = random.randint(min_base, max_base)
    x = random.randint(1, 5 if b <= 3 else 4)
    value = a * b ** x
    problem = f"If $f(x) = {a} \\cdot {b}^x$ and $f(x) = {value}$, what is $x$?"
    solution = f"${x}$"
    s = Steps()
    s.step(f"Divide both sides by ${a}$.", f"{b}^x = {b ** x}")
    s.step(f"Write ${b ** x}$ as a power of ${b}$.", f"{b ** x} = {b}^{{{x}}}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_exponential_growth_decay.variant("doubling_period")
def _growth_doubling_period():
    """Hidden rate: a quantity doubling every n years grows by what factor per year?"""
    n = random.randint(2, 10)
    kind = random.choice(["doubles", "triples"])
    k = 2 if kind == "doubles" else 3
    factor = Fraction(k) ** Fraction(1, n)
    value = k ** (1 / n)
    problem = (
        f"A population {kind} every ${n}$ years. By what factor does it grow each year? "
        "Round your answer to the nearest thousandth."
    )
    solution = f"${num(value)}$"
    s = Steps()
    s.step(f"If the yearly growth factor is $b$, then ${n}$ years of growth multiply by $b^{{{n}}}$, "
           f"which must equal ${k}$.", f"b^{{{n}}} = {k}")
    s.step(f"Take the ${n}$th root.", rf"b = {k}^{{1/{n}}} \approx {num(value)}")
    s.answer(solution, lead="Rounded to the nearest thousandth, the factor is")
    return problem, solution, s.done()


@algebra1.alg1_domain_of_function.variant("smallest_integer")
def _domain_smallest_integer():
    """Smallest integer in the domain of sqrt(ax + b)."""
    a = random.randint(1, 6)
    b = _nonzero(-20, 20)
    bound = Fraction(-b, a)
    smallest = math.ceil(bound)
    problem = f"What is the smallest integer in the domain of $f(x) = \\sqrt{{{_linear(a, b)}}}$?"
    solution = f"${smallest}$"
    s = Steps()
    s.step("A square root is defined only when the expression inside is $0$ or more.",
           f"{_linear(a, b)} \\geq 0")
    s.step("Solve.", f"x \\geq {_tex(bound)}")
    s.step("Take the smallest integer that satisfies this.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_point_slope_form.variant("y_intercept")
def _point_slope_y_intercept(coord_max=8, slope_max=6):
    """The y-intercept of a line written in point-slope form."""
    x1, y1 = random.randint(-coord_max, coord_max), random.randint(-coord_max, coord_max)
    m = _nonzero(-slope_max, slope_max)
    b = y1 - m * x1
    left = f"y{_plus(-y1)}"
    right = f"{m}(x{_plus(-x1)})" if x1 else f"{_term(m)}"
    problem = f"What is the y-intercept of the line ${left} = {right}$?"
    solution = f"${b}$"
    s = Steps()
    s.step("The y-intercept is the value of $y$ when $x = 0$.",
           f"y{_plus(-y1)} = {m}(0{_plus(-x1)}) = {-m * x1}")
    s.step("Solve for $y$.", f"y = {-m * x1}{_plus(y1)} = {b}")
    s.answer(solution)
    return problem, solution, s.done()


_SCALING = [
    # (formula, solved-for, varied, held fixed, exponent of varied in solved-for)
    ("d = rt", "r", "t", ["d"], -1),
    ("A = lw", "l", "w", ["A"], -1),
    ("F = ma", "a", "m", ["F"], -1),
    ("A = lw", "A", "w", ["l"], 1),
    ("I = Prt", "I", "r", ["P", "t"], 1),
    ("V = lwh", "h", "l", ["V", "w"], -1),
]


@algebra1.alg1_literal_equation.variant("scaling")
def _literal_scaling():
    """How a variable changes when another one is scaled and the rest are fixed."""
    formula, target, varied, fixed, power = random.choice(_SCALING)
    k = random.randint(2, 5)
    factor = Fraction(k) ** power
    held = " and ".join(f"${v}$" for v in fixed)
    problem = (
        f"In the formula ${formula}$, ${varied}$ is multiplied by ${k}$ while {held} "
        f"stay{'s' if len(fixed) == 1 else ''} the same. By what number is ${target}$ "
        f"multiplied? {_FRACTION_HINT}"
    )
    solution = _frac(factor)
    s = Steps()
    if power == 1:
        s.step(f"${target}$ is a product that includes ${varied}$, so it changes by the same "
               f"factor as ${varied}$.")
    else:
        s.step(f"Solve for ${target}$: it equals the fixed quantity divided by an expression "
               f"containing ${varied}$, so it changes by the reciprocal factor.")
    s.step(f"${varied}$ is multiplied by ${k}$.", f"{target} \\to {_tex(factor)} \\times {target}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_variation.variant("scaling")
def _variation_scaling():
    """y varies directly/inversely with x (or x^2): x is scaled, what happens to y?"""
    kind = random.choice(["directly", "inversely"])
    square = random.random() < 0.3
    k = random.randint(2, 5)
    power = (2 if square else 1) * (1 if kind == "directly" else -1)
    factor = Fraction(k) ** power
    what = "the square of $x$" if square else "$x$"
    problem = (
        f"$y$ varies {kind} with {what}. If $x$ is multiplied by ${k}$, by what number is "
        f"$y$ multiplied? {_FRACTION_HINT}"
    )
    solution = _frac(factor)
    model = {("directly", False): "y = kx", ("inversely", False): r"y = \frac{k}{x}",
             ("directly", True): "y = kx^2", ("inversely", True): r"y = \frac{k}{x^2}"}[(kind, square)]
    s = Steps()
    s.step("Write the variation.", model)
    s.step(f"Replace $x$ with ${k}x$.", f"y \\to {_tex(factor)} y")
    s.answer(solution)
    return problem, solution, s.done()


# --- Fractions and factors ------------------------------------------------------

@lib_fractions_gen.divide_fractions.variant("how_many_servings")
def _divide_how_many_servings():
    """Quotative division: how many a/b-size servings fit in n."""
    d = random.randint(2, 8)
    p = random.choice([n for n in range(1, d) if math.gcd(n, d) == 1])
    servings = random.randint(2, 12)
    unit = Fraction(p, d)
    total = servings * unit
    problem = (
        f"A recipe uses ${_tex(unit)}$ cup of rice per serving. How many servings can be made "
        f"from ${_tex(total)}$ cups of rice? {_FRACTION_HINT}"
    )
    answer = total / unit
    solution = _frac(answer)
    s = Steps()
    s.step("To find how many servings fit, divide the total by the size of one serving.",
           rf"{_tex(total)} \div {_tex(unit)}")
    s.step("Multiply by the reciprocal.",
           rf"{_tex(total)} \times \frac{{{d}}}{{{p}}} = {_tex(answer)}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_fractions_gen.fraction_multiplication.variant("fraction_of_a_fraction")
def _multiply_fraction_of_fraction(max_val=10):
    """'Part of a part': 1/2 of 2/3 of a garden."""
    b, d = random.randint(2, max_val), random.randint(2, max_val)
    a, c = random.randint(1, b - 1), random.randint(1, d - 1)
    first, second = Fraction(a, b), Fraction(c, d)
    answer = first * second
    problem = (
        f"${_tex(second)}$ of a garden is planted with vegetables. ${_tex(first)}$ of the "
        "vegetable section is tomatoes. What fraction of the whole garden is tomatoes? "
        f"{_FRACTION_HINT}"
    )
    solution = _frac(answer)
    s = Steps()
    s.step('"A fraction of" a quantity means multiply.', rf"{_tex(first)} \times {_tex(second)}")
    s.step("Multiply numerators and denominators, then simplify.",
           rf"\frac{{{a * c}}}{{{b * d}}} = {_tex(answer)}")
    s.answer(solution)
    return problem, solution, s.done()


def _divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


@lib_fractions_gen.factors.variant("count")
def _factors_count(min_val=2, max_val=100):
    """How many factors n has."""
    n = random.randint(min_val, max_val)
    divs = _divisors(n)
    problem = f"How many positive factors does ${n}$ have?"
    solution = f"${len(divs)}$"
    s = Steps()
    s.step("List the factor pairs: test each number up to the square root.",
           r",\ ".join(f"{d} \\times {n // d}" for d in divs if d * d <= n))
    s.step("Count every number that appears.", ", ".join(map(str, divs)))
    s.answer(solution)
    return problem, solution, s.done()


@lib_fractions_gen.common_factors.variant("count")
def _common_factors_count(min_val=2, max_val=100):
    """How many factors two numbers share."""
    a, b = random.sample(range(min_val, max_val + 1), 2)
    common = [d for d in _divisors(min(a, b)) if a % d == 0 and b % d == 0]
    problem = f"How many positive factors do ${a}$ and ${b}$ have in common?"
    solution = f"${len(common)}$"
    s = Steps()
    s.step(f"Factors of ${a}$:", ", ".join(map(str, _divisors(a))))
    s.step(f"Factors of ${b}$:", ", ".join(map(str, _divisors(b))))
    s.step("Count the numbers in both lists.", ", ".join(map(str, common)))
    s.answer(solution)
    return problem, solution, s.done()


# =============================================================================
# Further variants (beyond each topic's first new question types)
# =============================================================================

from . import lib_seqstats_gen  # noqa: E402


# --- Systems --------------------------------------------------------------------

_TICKETS = [("adult", "child", "tickets"), ("large", "small", "pizzas"),
            ("hardcover", "paperback", "books")]


def _system_tickets():
    """A two-item purchase: how many of the first kind were bought?"""
    first, second, things = random.choice(_TICKETS)
    p1, p2 = random.sample(range(3, 16), 2)
    n1, n2 = random.randint(1, 30), random.randint(1, 30)
    total, cost = n1 + n2, p1 * n1 + p2 * n2
    problem = (
        f"A group bought ${total}$ {things}. {first.capitalize()} {things} cost ${p1}$ dollars each "
        f"and {second} {things} cost ${p2}$ dollars each. The total was ${cost}$ dollars. How many "
        f"{first} {things} were bought?"
    )
    solution = f"${n1}$"
    s = Steps()
    s.step(f"Let $a$ be the {first} {things} and $c$ the {second} {things}.",
           rf"a + c = {total}, \quad {p1}a + {p2}c = {cost}")
    s.step(f"Substitute $c = {total} - a$ into the cost equation.",
           f"{p1}a + {p2}({total} - a) = {cost}")
    s.step("Simplify and solve.", f"{p1 - p2}a = {cost - p2 * total} \\Rightarrow a = {n1}")
    s.answer(solution)
    return problem, solution, s.done()


def _system_coefficient_from_solution():
    """Reverse: the solution is known; find a coefficient."""
    x, y = _nonzero(-6, 6), random.randint(-6, 6)
    a, b = _nonzero(-6, 6), _nonzero(-6, 6)
    c = a * x + b * y
    sign = "+" if b > 0 else "-"
    problem = (
        f"The point $({x}, {y})$ is a solution of $ax {sign} {_term(abs(b), 'y')} = {c}$. "
        "What is $a$?"
    )
    solution = f"${a}$"
    s = Steps()
    s.step("A solution makes the equation true. Substitute the point.",
           f"a({x}) {sign} {abs(b)}({y}) = {c}")
    s.step("Simplify.", f"{_term(x, 'a')}{_plus(b * y)} = {c}")
    s.step("Solve for $a$.", f"a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


for _gen in (algebra1.alg1_solve_system, lib_powers_gen.system_of_equations,
             lib_algebra_extra_gen.linear_equations, alg2_solve_system_matrix):
    _gen.variant("purchase")(_system_tickets)
    _gen.variant("coefficient_from_solution")(_system_coefficient_from_solution)


# --- Binomials and factoring --------------------------------------------------------

def _binomial_coefficient_of_x(max_coef=6, max_const=8):
    """Just the middle coefficient of (ax + b)(cx + d)."""
    a, c = _nonzero(-max_coef, max_coef), _nonzero(-max_coef, max_coef)
    b, d = _nonzero(-max_const, max_const), _nonzero(-max_const, max_const)
    problem = (
        f"When $({_linear(a, b)})({_linear(c, d)})$ is expanded, what is the coefficient of $x$?"
    )
    solution = f"${a * d + b * c}$"
    s = Steps()
    s.step("The $x$-terms come from the outer and inner products only.",
           f"{_term(a)} \\cdot {paren(d)} + {paren(b)} \\cdot {_term(c)} = {_term(a * d)} {'+' if b * c >= 0 else '-'} {_term(abs(b * c))}")
    s.step("Add their coefficients.", f"{a * d} + {paren(b * c)} = {a * d + b * c}")
    s.answer(solution)
    return problem, solution, s.done()


def _binomial_difference_of_squares():
    r"""Mental math: $51 \times 49 = (50 + 1)(50 - 1)$."""
    base = random.choice([20, 30, 40, 50, 60, 70, 80, 90, 100])
    k = random.randint(1, 4)
    problem = (
        rf"Use $(a + b)(a - b) = a^2 - b^2$ to find ${base + k} \times {base - k}$."
    )
    solution = f"${base * base - k * k}$"
    s = Steps()
    s.step(f"Write the numbers as ${base} + {k}$ and ${base} - {k}$.",
           f"({base} + {k})({base} - {k}) = {base}^2 - {k}^2")
    s.step("Evaluate.", f"{base * base} - {k * k} = {base * base - k * k}")
    s.answer(solution)
    return problem, solution, s.done()


def _binomial_rectangle_area(max_const=9):
    """Area of a rectangle with sides x + p and x + q, as a polynomial."""
    p, q = random.randint(1, max_const), random.randint(1, max_const)
    a = random.randint(1, 3)
    problem = (
        f"A rectangle is ${_linear(a, p)}$ units long and ${_linear(1, q)}$ units wide. Write its "
        "area as a polynomial in the form ax^2+bx+c."
    )
    solution = f"${_quadratic(a, a * q + p, p * q)}$"
    s = Steps()
    s.step("Area is length times width.", f"({_linear(a, p)})({_linear(1, q)})")
    s.step("Multiply each term of the first by each term of the second and combine like terms.",
           f"{_term(a, 'x^2')} + {a * q}x + {p}x + {p * q} = {_quadratic(a, a * q + p, p * q)}")
    s.answer(solution)
    return problem, solution, s.done()


for _gen in (algebra1.alg1_multiply_binomials, lib_algebra_extra_gen.expanding):
    _gen.variant("coefficient_of_x")(_binomial_coefficient_of_x)
    _gen.variant("difference_of_squares")(_binomial_difference_of_squares)
    _gen.variant("rectangle_area")(_binomial_rectangle_area)


def _monic(p, q):
    """x^2 + (p+q)x + pq for (x + p)(x + q)."""
    return _quadratic(1, p + q, p * q)


@algebra1.factoring.variant("middle_coefficient")
def _factoring_middle_coefficient(max_root=9):
    """Reverse: x^2 + bx + c = (x + p)(x + q) is given; find b."""
    p, q = _nonzero(-max_root, max_root), _nonzero(-max_root, max_root)
    c = p * q
    problem = (
        f"If $x^2 + bx {'+' if c > 0 else '-'} {abs(c)} = (x{_plus(p)})(x{_plus(q)})$, what is $b$?"
    )
    solution = f"${p + q}$"
    s = Steps()
    s.step("Expand the right side: the middle coefficient is the sum of the constants.",
           f"(x{_plus(p)})(x{_plus(q)}) = x^2 + ({p} + {paren(q)})x + {paren(c)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.factoring.variant("larger_root")
def _factoring_larger_root(max_root=9):
    """Factor to solve, and report the larger root."""
    p, q = random.sample([n for n in range(-max_root, max_root + 1) if n != 0], 2)
    problem = f"What is the larger solution of ${_monic(-p, -q)} = 0$?"
    solution = f"${max(p, q)}$"
    s = Steps()
    s.step(f"Factor: find two numbers with product ${p * q}$ and sum ${-(p + q)}$.",
           f"(x{_plus(-p)})(x{_plus(-q)}) = 0")
    s.step("Set each factor to zero.", rf"x = {p} \quad \text{{or}} \quad x = {q}")
    s.answer(solution, lead="The larger solution is")
    return problem, solution, s.done()


@algebra1.factoring.variant("other_side")
def _factoring_other_side(max_root=9):
    """A rectangle's area and one side are given; find the other side."""
    p, q = random.sample(range(1, max_root + 1), 2)
    problem = (
        f"A rectangle has area ${_monic(p, q)}$ and one side of length $x + {p}$. What is the "
        "length of the other side? Write it in the form x+n."
    )
    solution = f"$x+{q}$"
    s = Steps()
    s.step("The other side is the area divided by the known side. Factor the area.",
           f"{_monic(p, q)} = (x + {p})(x + {q})")
    s.step(f"Remove the factor $x + {p}$.", f"x + {q}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Quadratics ---------------------------------------------------------------------

@lib_seqstats_gen.quadratic_equation.variant("double_root")
def _quadratic_double_root():
    """For what c does x^2 + bx + c = 0 have exactly one solution?"""
    h = _nonzero(-9, 9)
    b = -2 * h
    problem = (
        f"For what value of $c$ does $x^2 {'+' if b > 0 else '-'} {abs(b)}x + c = 0$ have exactly "
        "one solution?"
    )
    solution = f"${h * h}$"
    s = Steps()
    s.step("Exactly one solution means the discriminant is zero.", f"b^2 - 4c = {b * b} - 4c = 0")
    s.step("Solve for $c$.", f"c = {h * h}")
    s.answer(solution)
    return problem, solution, s.done()


@lib_seqstats_gen.quadratic_equation.variant("projectile")
def _quadratic_projectile():
    """When a ball thrown upward lands: the positive root of -16t^2 + vt + h."""
    v = random.choice(range(16, 97, 8))
    h = random.randint(0, 80)
    t = (v + math.sqrt(v * v + 64 * h)) / 32
    problem = (
        f"A ball's height in feet after $t$ seconds is $h(t) = -16t^2 + {v}t + {h}$. When does it "
        "hit the ground? Round your answer to the nearest thousandth."
    )
    solution = f"${num(t)}$"
    s = Steps()
    s.step("It hits the ground when the height is $0$.", f"-16t^2 + {v}t + {h} = 0")
    s.step("Use the quadratic formula and keep the positive root (time can't be negative).",
           rf"t = \frac{{-{v} - \sqrt{{{v}^2 - 4(-16)({h})}}}}{{2(-16)}} \approx {num(t)}")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()


@lib_seqstats_gen.quadratic_equation.variant("positive_root")
def _quadratic_positive_root():
    """A quadratic with one positive and one negative root: give the positive one."""
    r1, r2 = random.randint(1, 12), -random.randint(1, 12)
    problem = f"What is the positive solution of ${_monic(-r1, -r2)} = 0$?"
    solution = f"${r1}$"
    s = Steps()
    s.step(f"Factor: two numbers with product ${r1 * r2}$ and sum ${-(r1 + r2)}$.",
           f"(x{_plus(-r1)})(x{_plus(-r2)}) = 0")
    s.step("Solve each factor and keep the positive one.", rf"x = {r1} \quad \text{{or}} \quad x = {r2}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra.vertex_form.variant("extreme_value")
def _vertex_extreme_value(min_val=-10, max_val=10, min_a=-5, max_a=5):
    """The maximum or minimum value of a(x - h)^2 + k."""
    a = _nonzero(min_a, max_a)
    h, k = random.randint(min_val, max_val), random.randint(min_val, max_val)
    kind = "minimum" if a > 0 else "maximum"
    problem = (
        f"What is the {kind} value of $y = {a if a not in (1, -1) else ('-' if a < 0 else '')}"
        f"(x{_plus(-h)})^2{_plus(k)}$?"
    )
    solution = f"${k}$"
    s = Steps()
    s.step(f"A square is never negative, and $a = {a}$ is {'positive' if a > 0 else 'negative'}, "
           f"so the parabola opens {'up' if a > 0 else 'down'}: its vertex is the {kind}.")
    s.step(f"The {kind} happens at $x = {h}$, where the squared term is $0$.", f"y = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra.vertex_form.variant("max_height")
def _vertex_max_height():
    """Maximum height of a projectile written in vertex form."""
    a = -random.choice([4.9, 16])
    t, top = random.randint(1, 6), random.randint(20, 200)
    a_text = num(a)
    problem = (
        f"A rocket's height in meters after $t$ seconds is $h(t) = {a_text}(t - {t})^2 + {top}$. "
        "What is its maximum height, in meters?"
    )
    solution = f"${top}$"
    s = Steps()
    s.step(f"In vertex form $a(t - h)^2 + k$, the vertex is $({t}, {top})$. Since $a < 0$ the "
           "parabola opens down, so the vertex is the highest point.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra.aroc_over_interval.variant("endpoint_from_rate")
def _aroc_endpoint_from_rate():
    """Reverse: the AROC of x^2 on [a, b] is a + b; find b."""
    a = random.randint(-5, 5)
    b = random.randint(a + 1, a + 10)
    rate = a + b
    problem = (
        f"The average rate of change of $f(x) = x^2$ from $x = {a}$ to $x = b$ is ${rate}$, with "
        f"$b > {a}$. What is $b$?"
    )
    solution = f"${b}$"
    s = Steps()
    s.step("Write the average rate of change and factor the difference of squares.",
           rf"\frac{{b^2 - {paren(a)}^2}}{{b - {paren(a)}}} = \frac{{(b - {paren(a)})(b + {paren(a)})}}{{b - {paren(a)}}} = b + {paren(a)}")
    s.step("Set it equal to the rate.", f"b + {paren(a)} = {rate} \\Rightarrow b = {b}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra.aroc_over_interval.variant("average_speed")
def _aroc_average_speed():
    """Average speed from a position function."""
    p, q = random.randint(1, 5), random.randint(0, 10)
    t1, t2 = sorted(random.sample(range(0, 9), 2))
    d = lambda t: p * t * t + q * t  # noqa: E731
    rate = Fraction(d(t2) - d(t1), t2 - t1)
    tail = f" + {q}t" if q else ""
    problem = (
        f"A cart's distance in meters after $t$ seconds is $d(t) = {_term(p, 't^2')}{tail}$. What is "
        f"its average speed from $t = {t1}$ to $t = {t2}$, in meters per second? {_FRACTION_HINT}"
    )
    solution = _frac(rate)
    s = Steps()
    s.step("Average speed is the change in distance over the change in time.",
           rf"\frac{{d({t2}) - d({t1})}}{{{t2} - {t1}}} = \frac{{{d(t2)} - {d(t1)}}}{{{t2 - t1}}} = {_tex(rate)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_discriminant.variant("one_root_parameter")
def _discriminant_one_root_parameter():
    """Positive k giving exactly one root of x^2 + kx + c (c a perfect square)."""
    r = random.randint(1, 9)
    a = random.choice([1, 1, 4, 9])
    c = r * r
    k = 2 * r * math.isqrt(a)
    problem = (
        f"For what positive value of $k$ does ${_term(a, 'x^2')} + kx + {c} = 0$ have exactly one "
        "real solution?"
    )
    solution = f"${k}$"
    s = Steps()
    s.step("Exactly one real solution means the discriminant is $0$.", f"k^2 - 4({a})({c}) = 0")
    s.step("Solve for the positive $k$.", rf"k = \sqrt{{{4 * a * c}}} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_discriminant.variant("x_intercepts")
def _discriminant_x_intercepts(max_a=5):
    """How many x-intercepts a parabola has."""
    a = _nonzero(-max_a, max_a)
    b = random.randint(-9, 9)
    c = random.randint(-9, 9)
    if random.random() < 0.3:          # make a double root fairly common
        r = random.randint(-4, 4)
        a, b, c = 1, -2 * r, r * r
    disc = b * b - 4 * a * c
    count = 2 if disc > 0 else (1 if disc == 0 else 0)
    problem = f"How many x-intercepts does the graph of $y = {_quadratic(a, b, c) if (b or c) else _term(a, 'x^2')}$ have?"
    solution = f"${count}$"
    s = Steps()
    s.step("The x-intercepts are the real solutions of $y = 0$. Count them with the discriminant.",
           f"b^2 - 4ac = {paren(b)}^2 - 4({a})({c}) = {disc}")
    s.step("Positive: two, zero: one, negative: none.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_discriminant.variant("reaches_height")
def _discriminant_reaches_height():
    """Does a ball reach a given height? (yes/no via the discriminant)."""
    v = random.choice(range(16, 97, 8))
    h0 = random.randint(0, 30)
    top = Fraction(v * v, 64) + h0
    target = random.randint(max(1, int(top) - 20), int(top) + 20)
    if target == top:
        target += 1
    reaches = target <= top
    problem = (
        f"A ball's height in feet is $h(t) = -16t^2 + {v}t + {h0}$. Does the ball ever reach "
        f"${target}$ feet? Answer yes or no."
    )
    answer = "yes" if reaches else "no"
    disc = v * v - 64 * (target - h0)
    s = Steps()
    s.step(f"It reaches ${target}$ feet if $-16t^2 + {v}t + {h0} = {target}$ has a real solution.",
           f"-16t^2 + {v}t{_plus(h0 - target)} = 0")
    s.step("Check the discriminant.", f"{v}^2 - 4(-16)({h0 - target}) = {disc}")
    s.step("A negative discriminant means no real solution." if disc < 0
           else "A discriminant of zero or more means there is a real solution.")
    s.answer(answer)
    return problem, answer, s.done()


@algebra1.alg1_axis_of_symmetry.variant("factored_form")
def _axis_factored_form():
    """The axis from factored form a(x - r)(x - s): halfway between the roots."""
    a = _nonzero(-5, 5)
    r, q = random.sample(range(-9, 10), 2)
    axis = Fraction(r + q, 2)
    lead = "" if a == 1 else ("-" if a == -1 else str(a))
    problem = (
        f"What is the axis of symmetry of $y = {lead}(x{_plus(-r)})(x{_plus(-q)})$? Give your answer "
        "in the form x = a/b, or x = n for an integer."
    )
    solution = f"$x = {frac_from(axis)}$"
    s = Steps()
    s.step(f"The x-intercepts are $x = {r}$ and $x = {q}$, and the axis is halfway between them.",
           rf"x = \frac{{{r} + {paren(q)}}}{{2}} = {_tex(axis)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_axis_of_symmetry.variant("missing_coefficient")
def _axis_missing_coefficient():
    """The axis is given; find b in ax^2 + bx + c."""
    a = _nonzero(-4, 4)
    h = _nonzero(-6, 6)
    c = random.randint(-9, 9)
    b = -2 * a * h
    problem = (
        f"The axis of symmetry of $y = {_term(a, 'x^2')} + bx{_plus(c)}$ is $x = {h}$. What is $b$?"
    )
    solution = f"${b}$"
    s = Steps()
    s.formula("The axis of symmetry", r"x = -\frac{b}{2a}")
    s.substitute(rf"{h} = -\frac{{b}}{{2({a})}}")
    s.step(f"Multiply both sides by ${-2 * a}$.", f"b = {b}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_sum_product_roots.variant("build_from_sum_product")
def _roots_build_from_sum_product():
    """Reverse: roots with a given sum and product -> c in x^2 + bx + c."""
    r1, r2 = random.randint(-9, 9), random.randint(-9, 9)
    total, product = r1 + r2, r1 * r2
    ask = random.choice(["b", "c"])
    problem = (
        f"The roots of $x^2 + bx + c = 0$ add up to ${total}$ and multiply to ${product}$. What is "
        f"${ask}$?"
    )
    solution = f"${-total if ask == 'b' else product}$"
    s = Steps()
    s.step("For $x^2 + bx + c$, the sum of the roots is $-b$ and the product is $c$.")
    s.step(f"So $b = {-total}$ and $c = {product}$.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_complete_the_square.variant("minimum_value")
def _complete_square_minimum(max_shift=8, min_c=-10, max_c=10):
    """The minimum of x^2 + bx + c by completing the square."""
    h = _nonzero(-max_shift, max_shift)
    c = random.randint(min_c, max_c)
    b = 2 * h
    problem = f"What is the minimum value of $y = {_quadratic(1, b, c)}$?"
    solution = f"${c - h * h}$"
    s = Steps()
    s.step(f"Complete the square: half of ${b}$ is ${h}$; add and subtract ${h * h}$.",
           f"y = (x{_plus(h)})^2 {_plus(c - h * h).strip() or '+ 0'}")
    s.step("A square is at least $0$, so the minimum is the constant left over.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_complete_the_square.variant("solve")
def _complete_square_solve(max_shift=8):
    """Solve x^2 + bx + c = 0 by completing the square (integer roots); larger root."""
    h = _nonzero(-max_shift, max_shift)
    d = random.randint(1, 9)
    roots = (-h + d, -h - d)
    b, c = 2 * h, h * h - d * d
    problem = f"Solve ${_quadratic(1, b, c)} = 0$ by completing the square. What is the larger solution?"
    solution = f"${max(roots)}$"
    s = Steps()
    s.step(f"Move the constant and add $({b}/2)^2 = {h * h}$ to both sides.",
           f"(x{_plus(h)})^2 = {d * d}")
    s.step("Take square roots.", f"x{_plus(h)} = \\pm {d}")
    s.step("Solve each.", rf"x = {roots[0]} \quad \text{{or}} \quad x = {roots[1]}")
    s.answer(solution, lead="The larger solution is")
    return problem, solution, s.done()


@algebra1.alg1_literal_equation.variant("use_formula")
def _literal_use_formula():
    """Solve a formula for one variable and evaluate it."""
    choice = random.randrange(4)
    s = Steps()
    if choice == 0:
        w, l = random.randint(1, 20), random.randint(1, 20)
        P = 2 * l + 2 * w
        problem = f"A rectangle's perimeter is $P = 2l + 2w$. If $P = {P}$ and $l = {l}$, what is $w$?"
        answer = w
        s.step("Solve for $w$.", r"w = \frac{P - 2l}{2}")
        s.substitute(rf"w = \frac{{{P} - 2({l})}}{{2}} = {w}")
    elif choice == 1:
        r, t = random.randint(5, 70), random.randint(2, 9)
        problem = f"Distance is $d = rt$. If $d = {r * t}$ and $t = {t}$, what is $r$?"
        answer = r
        s.step("Solve for $r$.", r"r = \frac{d}{t}")
        s.substitute(rf"r = \frac{{{r * t}}}{{{t}}} = {r}")
    elif choice == 2:
        c = random.choice(range(-40, 101, 5))
        f = Fraction(9, 5) * c + 32
        problem = (rf"Temperature converts by $F = \frac{{9}}{{5}}C + 32$. If $F = {num(f)}$, what is $C$?")
        answer = c
        s.step("Solve for $C$.", r"C = \frac{5}{9}(F - 32)")
        s.substitute(rf"C = \frac{{5}}{{9}}({num(f)} - 32) = {c}")
    else:
        P, r = random.choice(range(100, 2001, 100)), random.choice([2, 3, 4, 5, 6])
        t = random.randint(1, 10)
        I = P * r * t // 100
        problem = (f"Simple interest is $I = Prt$. If $I = {I}$, $P = {P}$, and $r = {r}\\%$ "
                   f"(so $r = {num(Fraction(r, 100))}$), how many years is $t$?")
        answer = t
        s.step("Solve for $t$.", r"t = \frac{I}{Pr}")
        s.substitute(rf"t = \frac{{{I}}}{{{P} \times {num(Fraction(r, 100))}}} = {t}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_point_slope_form.variant("point_on_line")
def _point_slope_point_on_line(coord_max=8, slope_max=6):
    """The y-value of the point on a point-slope line with a given x."""
    x1, y1 = random.randint(-coord_max, coord_max), random.randint(-coord_max, coord_max)
    m = _nonzero(-slope_max, slope_max)
    x = random.randint(-coord_max, coord_max)
    y = y1 + m * (x - x1)
    problem = (
        f"The point $({x}, k)$ lies on the line $y{_plus(-y1)} = {m}(x{_plus(-x1)})$. What is $k$?"
    )
    solution = f"${y}$"
    s = Steps()
    s.substitute(f"k{_plus(-y1)} = {m}({x}{_plus(-x1)}) = {m * (x - x1)}", text=f"Substitute $x = {x}$.")
    s.step("Solve for $k$.", f"k = {y}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_variation.variant("table_predict")
def _variation_table_predict():
    """Decide direct or inverse variation from a table, then predict."""
    direct = random.random() < 0.5
    k = random.randint(2, 12) if direct else random.choice([12, 24, 36, 48, 60, 72])
    xs = sorted(random.sample([1, 2, 3, 4, 6, 12], 3))
    ys = [k * x if direct else Fraction(k, x) for x in xs]
    target = random.choice([2, 3, 4, 6, 8, 12])
    value = Fraction(k * target) if direct else Fraction(k, target)
    shown = [num(y) for y in ys]
    problem = (
        f"The table shows how $y$ varies with $x$. ${_table('x', xs, 'y', shown)}$ Is this direct "
        f"or inverse variation? Use it to find $y$ when $x = {target}$. {_FRACTION_HINT}"
    )
    solution = _frac(value)
    s = Steps()
    if direct:
        s.step("$y/x$ is the same in every column, so it's direct variation.", f"y = {k}x")
    else:
        s.step("$xy$ is the same in every column, so it's inverse variation.", rf"y = \frac{{{k}}}{{x}}")
    s.step(f"Substitute $x = {target}$.", f"y = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_variation.variant("workers")
def _variation_workers():
    """Inverse variation in context: workers and days."""
    while True:
        w1, d1 = random.randint(2, 12), random.randint(2, 12)
        job = w1 * d1
        crews = [w for w in range(2, 25) if job % w == 0 and w != w1]
        if crews:
            break
    w2 = random.choice(crews)
    problem = (
        f"${w1}$ workers can paint a building in ${d1}$ days. Working at the same rate, how many "
        f"days would ${w2}$ workers take?"
    )
    solution = f"${job // w2}$"
    s = Steps()
    s.step("Days vary inversely with workers: the product workers times days stays the same.",
           rf"{w1} \times {d1} = {job}")
    s.step(f"Divide by ${w2}$.", rf"{job} \div {w2} = {job // w2}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_simplify_rational.variant("hole")
def _rational_hole(max_root=7):
    """The x-value of the hole of a rational function with a common factor."""
    r, a, b = random.sample([n for n in range(-max_root, max_root + 1) if n != 0], 3)
    num_ = _monic(r, a)
    den = _monic(r, b)
    problem = (
        rf"The graph of $f(x) = \frac{{{num_}}}{{{den}}}$ has a hole. At what $x$-value is the hole?"
    )
    solution = f"${-r}$"
    s = Steps()
    s.step("Factor the numerator and denominator.",
           rf"\frac{{(x{_plus(r)})(x{_plus(a)})}}{{(x{_plus(r)})(x{_plus(b)})}}")
    s.step(f"The common factor $x{_plus(r)}$ cancels, leaving a hole where it is zero.", f"x = {-r}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_abs_value_inequality.variant("count_integers")
def _abs_inequality_count(max_a=5, max_b=10, min_c=2, max_c=12):
    """How many integers satisfy |ax + b| <= c (or < c)."""
    a = random.randint(1, max_a)
    b = random.randint(-max_b, max_b)
    c = random.randint(min_c, max_c)
    op = random.choice(["<", "\\leq"])
    count = sum(1 for x in range(-200, 201) if (abs(a * x + b) < c if op == "<" else abs(a * x + b) <= c))
    problem = f"How many integers $x$ satisfy $|{_linear(a, b)}| {op} {c}$?"
    solution = f"${count}$"
    lo, hi = Fraction(-c - b, a), Fraction(c - b, a)
    s = Steps()
    s.step("Rewrite without the absolute value.", f"-{c} {op} {_linear(a, b)} {op} {c}")
    s.step("Solve for $x$.", f"{_tex(lo)} {op} x {op} {_tex(hi)}")
    s.step("Count the integers in that range.")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_abs_value_inequality.variant("tolerance")
def _abs_inequality_tolerance():
    """Within a tolerance of a target: the lowest (or highest) allowed value."""
    target, tol = random.randint(20, 90), random.randint(1, 9)
    low = random.random() < 0.5
    problem = (
        f"A thermostat keeps the temperature $T$ within ${tol}$ degrees of ${target}$ degrees, so "
        f"$|T - {target}| \\leq {tol}$. What is the {'lowest' if low else 'highest'} temperature it "
        "allows?"
    )
    solution = f"${target - tol if low else target + tol}$"
    s = Steps()
    s.step("Rewrite without the absolute value.", f"{target - tol} \\leq T \\leq {target + tol}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_simplify_radical.variant("missing_radicand")
def _radical_missing_radicand(min_factor=2, max_factor=9):
    r"""$\sqrt{72} = 6\sqrt{\square}$."""
    a = random.randint(min_factor, max_factor)
    b = random.choice(algebra1._SQUAREFREE)
    problem = rf"Fill in the box: $\sqrt{{{a * a * b}}} = {a}\sqrt{{\square}}$."
    solution = f"${b}$"
    s = Steps()
    s.step(f"Factor out the perfect square ${a * a}$.", rf"\sqrt{{{a * a * b}}} = \sqrt{{{a * a}}} \cdot \sqrt{{{b}}} = {a}\sqrt{{{b}}}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_simplify_radical.variant("move_inside")
def _radical_move_inside(min_factor=2, max_factor=9):
    r"""Reverse: $3\sqrt{5} = \sqrt{n}$."""
    a = random.randint(min_factor, max_factor)
    b = random.choice(algebra1._SQUAREFREE)
    problem = rf"If ${a}\sqrt{{{b}}} = \sqrt{{n}}$, what is $n$?"
    solution = f"${a * a * b}$"
    s = Steps()
    s.step(f"Move ${a}$ inside the root by squaring it.",
           rf"{a}\sqrt{{{b}}} = \sqrt{{{a}^2 \cdot {b}}} = \sqrt{{{a * a * b}}}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_negative_exponent.variant("fraction_base")
def _negative_exponent_fraction_base():
    r"""$(2/3)^{-2} = 9/4$: a negative exponent flips the fraction."""
    p, q = random.sample(range(1, 7), 2)
    if math.gcd(p, q) != 1:
        p, q = 2, 3
    n = random.randint(1, 3)
    value = Fraction(q, p) ** n
    problem = rf"Evaluate $\left(\frac{{{p}}}{{{q}}}\right)^{{-{n}}}$. {_FRACTION_HINT}"
    solution = _frac(value)
    s = Steps()
    s.step("A negative exponent takes the reciprocal.",
           rf"\left(\frac{{{p}}}{{{q}}}\right)^{{-{n}}} = \left(\frac{{{q}}}{{{p}}}\right)^{{{n}}}")
    s.step("Raise the numerator and denominator to the power.", rf"\frac{{{q ** n}}}{{{p ** n}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_exponential_growth_decay.variant("factor_from_table")
def _growth_factor_from_table():
    """The growth or decay factor of an exponential table."""
    a = random.choice([2, 3, 4, 5, 8, 10, 16, 32, 64])
    b = Fraction(random.choice([2, 3, 4, 5]), random.choice([1, 1, 2, 4]))
    if b == 1:
        b = Fraction(2)
    xs = [0, 1, 2, 3]
    scale = b.denominator ** 3
    ys = [a * scale * b ** x for x in xs]
    problem = (
        f"The table shows an exponential function. ${_table('x', xs, 'y', [num(y) for y in ys])}$ "
        f"By what factor does $y$ change each time $x$ increases by $1$? {_FRACTION_HINT}"
    )
    solution = _frac(b)
    s = Steps()
    s.step("In an exponential function, consecutive outputs have a constant ratio.",
           rf"\frac{{{num(ys[1])}}}{{{num(ys[0])}}} = {_tex(b)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_exponential_growth_decay.variant("half_life")
def _growth_half_life():
    """Fraction (or amount) left after a number of half-lives."""
    period = random.choice([2, 3, 5, 8, 10, 12])
    n = random.randint(1, 5)
    start = random.choice([None, 64, 80, 96, 160, 320, 640])
    elapsed = period * n
    if start is None:
        value = Fraction(1, 2 ** n)
        problem = (f"A substance has a half-life of ${period}$ years. What fraction of it remains after "
                   f"${elapsed}$ years? {_FRACTION_HINT}")
    else:
        value = Fraction(start, 2 ** n)
        problem = (f"A ${start}$-gram sample has a half-life of ${period}$ years. How many grams remain "
                   f"after ${elapsed}$ years? {_FRACTION_HINT}")
    solution = _frac(value)
    s = Steps()
    s.step(f"${elapsed}$ years is ${elapsed} \\div {period} = {n}$ half-lives.")
    s.step(f"Each half-life halves the amount, so multiply by $(1/2)^{{{n}}}$.",
           rf"{start if start else 1} \times \frac{{1}}{{{2 ** n}}} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_evaluate_exponential.variant("read_parameters")
def _exponential_read_parameters(max_a=10, min_base=2, max_base=6):
    """f(0) and f(x+1)/f(x) reveal a and b in a * b^x."""
    a = random.randint(1, max_a)
    b = random.randint(min_base, max_base)
    x = random.randint(1, 3)
    if random.random() < 0.5:
        problem = (f"For $f(x) = a \\cdot b^x$, $f(0) = {a}$ and $f({x}) = {a * b ** x}$. What is $b$?")
        answer = b
        s = Steps()
        s.step("$f(0) = a \\cdot b^0 = a$, so $a$ is the starting value.", f"a = {a}")
        s.step(f"Then $b^{{{x}}} = {a * b ** x} \\div {a} = {b ** x}$.", f"b = {b}")
    else:
        problem = (f"For $f(x) = a \\cdot b^x$, $f({x}) = {a * b ** x}$ and $f({x + 1}) = "
                   f"{a * b ** (x + 1)}$. What is $a$?")
        answer = a
        s = Steps()
        s.step("Consecutive outputs differ by a factor of $b$.",
               rf"b = \frac{{{a * b ** (x + 1)}}}{{{a * b ** x}}} = {b}")
        s.step(f"Then $a = f({x}) \\div b^{{{x}}}$.", rf"a = {a * b ** x} \div {b ** x} = {a}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@algebra1.alg1_domain_of_function.variant("count_excluded")
def _domain_count_excluded():
    """How many integers in a range are excluded from the domain of 1/(x^2 - k^2)."""
    k = random.randint(1, 6)
    lo, hi = -random.randint(k - 1 if k > 1 else 0, 8), random.randint(0, 8)
    excluded = [v for v in (k, -k) if lo <= v <= hi]
    problem = (
        rf"How many integers from ${lo}$ to ${hi}$ are not in the domain of "
        rf"$f(x) = \frac{{1}}{{x^2 - {k * k}}}$?"
    )
    solution = f"${len(excluded)}$"
    s = Steps()
    s.step("A fraction is undefined where its denominator is $0$.", f"x^2 - {k * k} = 0 \\Rightarrow x = \\pm {k}")
    s.step(f"Count which of ${k}$ and ${-k}$ are between ${lo}$ and ${hi}$.")
    s.answer(solution)
    return problem, solution, s.done()
