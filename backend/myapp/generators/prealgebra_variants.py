"""Extra question types for the pre-algebra topics.

Each function here is a variant of one topic's generator in ``prealgebra.py``
(see ``_variants.with_variants``); that generator's original question stays as
the ``classic`` variant. The variants ask the same concept a different way —
reversed, in context, from a table or a number line, or through structure —
and only ever use their own topic's skill. See docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num, pair
from ._steps import Steps, paren
from . import prealgebra as pre
from .prealgebra import (
    _FRACTION_HINT,
    _OPS,
    _dollars,
    _frac_solution,
    _line_equation,
    _money,
    _move_constant,
    _signed,
    _simplify,
    _tex,
    _tex_line,
    _term,
)

_PAIR_HINT = "Format your answer as (x, y)."


def _nonzero(lo, hi):
    return random.choice([i for i in range(lo, hi + 1) if i != 0])


def _table(top_label, top, bottom_label, bottom):
    """A two-row LaTeX table (inside ``$...$``): labels, then one column per value."""
    cols = "c|" + "c" * len(top)
    return (
        rf"\begin{{array}}{{{cols}}} {top_label} & "
        + " & ".join(str(v) for v in top)
        + rf" \\ \hline {bottom_label} & "
        + " & ".join(str(v) for v in bottom)
        + r" \end{array}"
    )


def _xy(a, b, c):
    """``ax + by = c`` in LaTeX, with unit coefficients dropped."""
    sign = "+" if b > 0 else "-"
    return f"{_term(a)} {sign} {_term(abs(b), 'y')} = {c}"


def _data_with_integer_mean(n, lo, hi):
    while True:
        values = [random.randint(lo, hi) for _ in range(n)]
        if sum(values) % n == 0:
            return values


# --- Ratios, rates, proportions ---------------------------------------------

@pre.pre_unit_rate.variant("better_buy")
def _unit_rate_better_buy(min_size=4, max_size=32):
    r"""Better buy: the lower of two unit prices, in dollars per ounce."""
    u1, u2 = random.sample(range(12, 61), 2)  # cents per ounce
    s1, s2 = random.sample(range(min_size, max_size + 1), 2)
    p1, p2 = u1 * s1, u2 * s2
    best = min(u1, u2)
    solution = _money(best)
    problem = (
        f"Brand A sells ${s1}$ ounces of cereal for ${_money(p1)}$ dollars. "
        f"Brand B sells ${s2}$ ounces for ${_money(p2)}$ dollars. "
        f"What is the unit price of the better buy, in dollars per ounce? "
        f"Give your answer in dollars, for example 0.25."
    )
    s = Steps()
    s.step("A unit price is the price divided by the number of ounces. For Brand A:",
           rf"{_money(p1)} \div {s1} = {_money(u1)}")
    s.step("For Brand B:", rf"{_money(p2)} \div {s2} = {_money(u2)}")
    s.step("The better buy is the one with the lower unit price.",
           rf"{_money(best)} < {_money(max(u1, u2))}")
    s.answer(solution, lead="The better buy costs")
    return problem, solution, s.done()


_PART_WHOLE = [
    ("boys", "girls", "students"),
    ("red marbles", "blue marbles", "marbles"),
    ("cats", "dogs", "animals"),
    ("adult tickets", "child tickets", "tickets"),
]


@pre.pre_equivalent_ratio.variant("part_of_whole")
def _ratio_part_of_whole(min_term=1, max_term=9, min_factor=2, max_factor=9):
    """Part-part-whole: the ratio and the total are given, find one part."""
    while True:
        a = random.randint(min_term, max_term)
        b = random.randint(min_term, max_term)
        if a != b and math.gcd(a, b) == 1:
            break
    k = random.randint(min_factor, max_factor)
    total = (a + b) * k
    first, second, whole = random.choice(_PART_WHOLE)
    problem = (
        f"The ratio of {first} to {second} is ${a}:{b}$. There are ${total}$ "
        f"{whole} in all. How many {second} are there?"
    )
    solution = f"${b * k}$"
    s = Steps()
    s.step(f"The ratio ${a}:{b}$ splits the {whole} into ${a} + {b} = {a + b}$ equal parts.")
    s.step("Find how many are in one part.", rf"{total} \div {a + b} = {k}")
    s.step(f"The {second} make up ${b}$ parts.", rf"{b} \times {k} = {b * k}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_solve_proportion.variant("binomial_numerator")
def _proportion_binomial_numerator(min_term=1, max_term=12):
    r"""A proportion whose unknown sits in a sum: $\frac{x + c}{a} = \frac{b}{d}$."""
    a = random.randint(2, max_term)
    d = random.randint(2, max_term)
    b = random.randint(min_term, max_term)
    c = _nonzero(-9, 9)
    rhs = Fraction(a * b, d)
    x = rhs - c
    problem = (
        rf"Solve for $x$: $\frac{{x {_signed(c)}}}{{{a}}} = \frac{{{b}}}{{{d}}}$. "
        f"{_FRACTION_HINT}"
    )
    solution = _frac_solution(x)
    s = Steps()
    s.step("Cross-multiply.", rf"{d}(x {_signed(c)}) = {a} \times {b} = {a * b}")
    s.step(f"Divide both sides by ${d}$.", f"x {_signed(c)} = {_tex(rhs)}")
    s.step(f"{_move_constant(c)}.", f"x = {_tex(x)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_scale_length.variant("find_the_scale")
def _scale_find_the_scale(min_k=2, max_k=9, min_len=2, max_len=15):
    """Reverse: find what 1 cm stands for from a map length and a real length."""
    k = random.randint(min_k, max_k)
    m = random.randint(min_len, max_len)
    problem = (
        f"On a map, ${m}$ cm represents ${m * k}$ km. How many kilometers does "
        f"$1$ cm represent?"
    )
    solution = f"${k}$"
    s = Steps()
    s.step("Divide the real distance by the map distance to find the distance for $1$ cm.",
           rf"{m * k} \div {m} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Integers, rationals, absolute value -------------------------------------

@pre.pre_integer_operations.variant("sum_and_product")
def _integers_sum_and_product(min_val=-12, max_val=12):
    """Two integers from their sum and product (the pair is unique)."""
    m, n = random.sample([i for i in range(min_val, max_val + 1) if i != 0], 2)
    total, product = m + n, m * n
    big, small = max(m, n), min(m, n)
    problem = (
        f"Two integers have a sum of ${total}$ and a product of ${product}$. "
        f"What is the larger integer?"
    )
    solution = f"${big}$"
    s = Steps()
    s.step(f"Look for two integers whose product is ${product}$ and whose sum is ${total}$. "
           "The signs of the product and sum tell you the signs of the integers.")
    s.step("These two integers work:",
           rf"{small} \times {paren(big)} = {product}, \quad {small} + {paren(big)} = {total}")
    s.answer(solution, lead="The larger integer is")
    return problem, solution, s.done()


@pre.pre_rational_operations.variant("signed_change")
def _rationals_signed_change(min_den=2, max_den=9):
    """A diver's position below sea level changes by a fraction of a meter."""
    d1 = random.randint(min_den, max_den)
    d2 = random.randint(min_den, max_den)
    start = -Fraction(random.randint(1, 3 * d1), d1)
    change = Fraction(random.randint(1, 2 * d2), d2)
    descends = random.random() < 0.5
    end = start - change if descends else start + change
    verb = "descends" if descends else "rises"
    problem = (
        f"A diver is at ${_tex(start)}$ meters (negative means below sea level). "
        f"The diver {verb} ${_tex(change)}$ meters. What is the diver's new position, "
        f"in meters? {_FRACTION_HINT}"
    )
    solution = _frac_solution(end)
    op = "-" if descends else "+"
    s = Steps()
    s.step(f"Moving down subtracts and moving up adds, so the diver {verb}: use ${op}$.",
           f"{_tex(start)} {op} {_tex(change)}")
    lcd = start.denominator * change.denominator // math.gcd(start.denominator, change.denominator)
    a, b = start * lcd, change * lcd
    s.step(f"Rewrite both fractions with the common denominator ${lcd}$ and combine the numerators.",
           rf"\frac{{{a}}}{{{lcd}}} {op} \frac{{{b}}}{{{lcd}}} = {_tex(end)}")
    s.answer(solution, lead="The new position is")
    return problem, solution, s.done()


@pre.pre_absolute_value.variant("number_line_distance")
def _absolute_number_line(min_val=-20, max_val=20):
    """Distance between two points on a number line."""
    a, b = random.sample(range(min_val, max_val + 1), 2)
    problem = (
        f"Point $A$ is at ${a}$ and point $B$ is at ${b}$ on a number line. "
        f"How far apart are they?"
    )
    solution = f"${abs(a - b)}$"
    s = Steps()
    s.step("The distance between two points on a number line is the absolute value of "
           "their difference.", f"|{a} - {paren(b)}| = |{a - b}| = {abs(a - b)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Inequalities -------------------------------------------------------------

@pre.pre_one_step_inequality.variant("integer_extreme")
def _one_step_integer_extreme():
    """The greatest (or smallest) integer solution of ``kx op c``."""
    k = random.randint(2, 9)
    c = random.randint(-40, 40)
    op = random.choice(_OPS)
    bound = Fraction(c, k)
    if op == "<":
        want, answer = "greatest", math.ceil(bound) - 1
    elif op == "\\leq":
        want, answer = "greatest", math.floor(bound)
    elif op == ">":
        want, answer = "smallest", math.floor(bound) + 1
    else:
        want, answer = "smallest", math.ceil(bound)
    problem = f"What is the {want} integer that satisfies ${k}x {op} {c}$?"
    solution = f"${answer}$"
    s = Steps()
    s.step(f"Divide both sides by ${k}$. It is positive, so the inequality keeps its direction.",
           f"x {op} {_tex(bound)}")
    if bound.denominator != 1:
        s.step(f"${_tex(bound)}$ is about ${num(bound)}$.")
    strict = op in ("<", ">")
    if strict and bound.denominator == 1:
        s.step(f"$x$ can't equal ${bound}$ itself, so step one integer past it.")
    s.answer(solution, lead=f"The {want} integer solution is")
    return problem, solution, s.done()


@pre.pre_multi_step_inequality.variant("budget")
def _multi_step_budget():
    """How many items fit in a budget after a fixed cost (a whole-number answer)."""
    fee = random.randint(10, 40)
    price = random.randint(3, 12)
    budget = random.randint(fee + 3 * price, fee + 20 * price)
    answer = (budget - fee) // price
    problem = (
        f"A club has ${budget}$ dollars. It spends ${fee}$ dollars on supplies and "
        f"wants to buy T-shirts that cost ${price}$ dollars each. What is the greatest "
        f"number of T-shirts it can buy?"
    )
    solution = f"${answer}$"
    s = Steps()
    s.step("Let $t$ be the number of T-shirts. The total spent can be at most the budget.",
           rf"{fee} + {price}t \leq {budget}")
    s.step(f"Subtract ${fee}$ from both sides.", rf"{price}t \leq {budget - fee}")
    s.step(f"Divide both sides by ${price}$.",
           rf"t \leq {_tex(Fraction(budget - fee, price))}")
    s.step("Only whole T-shirts can be bought, so take the greatest whole number that fits.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Scientific notation and exponents ----------------------------------------

@pre.pre_scientific_notation_ops.variant("how_many_times")
def _sci_how_many_times():
    """How many times greater one scientific-notation number is than another."""
    b = random.randint(1, 4)
    q = random.randint(2, 9 // b)
    a = b * q
    n = random.randint(-8, 12)
    k = random.randint(1, 4)
    m = n + k
    answer = q * 10 ** k
    problem = (
        rf"How many times greater is ${a} \times 10^{{{m}}}$ than "
        rf"${b} \times 10^{{{n}}}$? Give your answer as a whole number."
    )
    solution = f"${answer}$"
    s = Steps()
    s.step("To find how many times greater, divide. Divide the numbers and the powers of ten "
           "separately.",
           rf"\frac{{{a}}}{{{b}}} \times \frac{{10^{{{m}}}}}{{10^{{{n}}}}}")
    s.step("Subtract the exponents to divide the powers of ten.",
           rf"{q} \times 10^{{{m} - {paren(n)}}} = {q} \times 10^{{{k}}}")
    s.step("Write it as a whole number.", rf"{q} \times 10^{{{k}}} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


_POWERS = {2: [(4, 2), (8, 3), (16, 4), (32, 5)], 3: [(9, 2), (27, 3), (81, 4)]}


@pre.pre_integer_exponent_rules.variant("common_base")
def _exponents_common_base():
    r"""Rewrite powers with different bases over one base: $8^2 \cdot 4^3 = 2^{\square}$."""
    base = random.choice([2, 3])
    (v1, p1), (v2, p2) = random.sample(_POWERS[base], 2)
    m, n = random.randint(2, 4), random.randint(2, 4)
    exponent = p1 * m + p2 * n
    problem = (
        rf"Fill in the box: ${v1}^{{{m}}} \cdot {v2}^{{{n}}} = {base}^{{\square}}$."
    )
    solution = f"${exponent}$"
    s = Steps()
    s.step(f"Write each base as a power of ${base}$: ${v1} = {base}^{{{p1}}}$ and "
           f"${v2} = {base}^{{{p2}}}$.",
           rf"({base}^{{{p1}}})^{{{m}}} \cdot ({base}^{{{p2}}})^{{{n}}}")
    s.step("A power of a power multiplies the exponents.",
           rf"{base}^{{{p1 * m}}} \cdot {base}^{{{p2 * n}}}")
    s.step("Multiplying powers with the same base adds the exponents.",
           f"{base}^{{{p1 * m} + {p2 * n}}} = {base}^{{{exponent}}}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Functions, proportional relationships, lines ----------------------------

@pre.pre_constant_of_proportionality.variant("table")
def _proportionality_table(max_k=12):
    """The constant of proportionality read from a table of values."""
    k = Fraction(random.randint(1, max_k), random.choice([1, 1, 2, 3, 4, 5]))
    xs = [x * k.denominator for x in sorted(random.sample(range(1, 7), 4))]
    ys = [int(k * x) for x in xs]
    problem = (
        "The table shows a proportional relationship between $x$ and $y$. "
        f"${_table('x', xs, 'y', ys)}$ "
        f"What is the constant of proportionality $k$ in $y = kx$? {_FRACTION_HINT}"
    )
    solution = _frac_solution(k)
    s = Steps()
    s.step("In a proportional relationship $k = \\frac{y}{x}$ for every pair. Use the first column.",
           rf"k = \frac{{{ys[0]}}}{{{xs[0]}}} = {_tex(k)}")
    s.step("Check with another column.", rf"\frac{{{ys[1]}}}{{{xs[1]}}} = {_tex(k)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_evaluate_function.variant("table")
def _evaluate_function_table(min_x=-6, max_x=6):
    """A function given as a table: add two outputs, or find the input for an output."""
    xs = sorted(random.sample(range(min_x, max_x + 1), 5))
    ys = random.sample(range(-15, 16), 5)
    table = _table("x", xs, "f(x)", ys)
    s = Steps()
    if random.random() < 0.5:
        i, j = random.sample(range(5), 2)
        answer = ys[i] + ys[j]
        problem = (
            f"The function $f$ is given by the table. ${table}$ "
            f"What is $f({xs[i]}) + f({xs[j]})$?"
        )
        s.step("Read each output from the table: find the column for each input.",
               f"f({xs[i]}) = {ys[i]}, \\quad f({xs[j]}) = {ys[j]}")
        s.step("Add them.", f"{ys[i]} + {paren(ys[j])} = {answer}")
    else:
        i = random.randrange(5)
        answer = xs[i]
        problem = (
            f"The function $f$ is given by the table. ${table}$ "
            f"For what value of $x$ is $f(x) = {ys[i]}$?"
        )
        s.step(f"Find ${ys[i]}$ in the $f(x)$ row, then read the input above it.",
               f"f({xs[i]}) = {ys[i]}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_slope_from_two_points.variant("missing_coordinate")
def _slope_missing_coordinate(coord_min=-10, coord_max=10):
    """Reverse: the slope is known, find a missing y-coordinate."""
    m = _nonzero(-5, 5)
    x1, x2 = random.sample(range(coord_min, coord_max + 1), 2)
    k = random.randint(coord_min, coord_max)
    y2 = k + m * (x2 - x1)
    problem = f"A line with slope ${m}$ passes through $({x1}, k)$ and $({x2}, {y2})$. Find $k$."
    solution = f"${k}$"
    s = Steps()
    s.formula("The slope formula", r"m = \frac{y_2 - y_1}{x_2 - x_1}")
    s.substitute(rf"{m} = \frac{{{y2} - k}}{{{x2} - {paren(x1)}}} = \frac{{{y2} - k}}{{{x2 - x1}}}")
    s.step(f"Multiply both sides by ${x2 - x1}$.", f"{m * (x2 - x1)} = {y2} - k")
    s.step("Solve for $k$.", f"k = {y2} - {paren(m * (x2 - x1))} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_linear_function_value.variant("input_from_output")
def _linear_input_from_output(min_val=-10, max_val=10):
    """Reverse: find the x that gives a stated y."""
    m = _nonzero(min_val, max_val)
    b = random.randint(min_val, max_val)
    y = random.randint(-30, 30)
    x = Fraction(y - b, m)
    problem = (
        f"A line has slope $m = {m}$ and y-intercept $b = {b}$. "
        f"For what value of $x$ is $y = {y}$? {_FRACTION_HINT}"
    )
    solution = _frac_solution(x)
    s = Steps()
    s.formula("Slope-intercept form", "y = mx + b")
    s.substitute(f"{y} = {m}x {_signed(b)}")
    s.step(f"{_move_constant(b)}.", f"{y - b} = {m}x")
    s.step(f"Divide both sides by ${m}$.", rf"x = \frac{{{y - b}}}{{{m}}}")
    _simplify(s, y - b, m)
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_slope_intercept_form.variant("coefficient_from_slope")
def _slope_intercept_coefficient(min_coeff=-9, max_coeff=9):
    """Reverse: a standard-form coefficient from the line's slope."""
    B = _nonzero(min_coeff, max_coeff)
    m = _nonzero(-6, 6)
    A = -m * B
    C = random.randint(min_coeff, max_coeff)
    sign = "+" if B > 0 else "-"
    problem = f"The line $Ax {sign} {_term(abs(B), 'y')} = {C}$ has slope ${m}$. Find $A$."
    solution = f"${A}$"
    s = Steps()
    s.step("Solve for $y$ to see the slope.",
           rf"y = -\frac{{A}}{{{B}}}x + \frac{{{C}}}{{{B}}}")
    s.step("The slope is the coefficient of $x$.", rf"-\frac{{A}}{{{B}}} = {m}")
    s.step(f"Multiply both sides by ${-B}$.", f"A = {m} \\times {paren(-B)} = {A}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_line_from_slope_point.variant("parallel_or_perpendicular")
def _line_parallel_or_perpendicular(min_val=-8, max_val=8):
    """A line through a point, parallel or perpendicular to a given line."""
    m0 = Fraction(_nonzero(-6, 6))
    b0 = random.randint(min_val, max_val)
    x0 = random.randint(min_val, max_val)
    y0 = random.randint(min_val, max_val)
    parallel = random.random() < 0.5
    m = m0 if parallel else -1 / m0
    b = y0 - m * x0
    relation = "parallel" if parallel else "perpendicular"
    problem = (
        f"Find the line that is {relation} to ${_tex_line(m0, Fraction(b0))}$ and passes "
        f"through the point $({x0}, {y0})$. Give the equation in the form y = mx + b."
    )
    solution = _line_equation(m, b)
    s = Steps()
    if parallel:
        s.step(f"Parallel lines have the same slope, so $m = {_tex(m)}$.")
    else:
        s.step("Perpendicular slopes are negative reciprocals.",
               rf"m = -\frac{{1}}{{{_tex(m0)}}} = {_tex(m)}")
    s.step("Substitute the slope and the point into $y = mx + b$.",
           f"{y0} = {_tex(m)}({x0}) + b")
    s.step("Solve for $b$.", f"b = {y0} - {paren(_tex(m * x0))} = {_tex(b)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_compare_functions.variant("initial_value")
def _compare_initial_value(min_val=-9, max_val=9):
    """Compare y-intercepts: one function as a table (not at x = 0), one in words."""
    mA = _nonzero(-5, 5)
    bA = random.randint(min_val, max_val)
    mB = _nonzero(-5, 5)
    bB = random.choice([v for v in range(min_val, max_val + 1) if v != bA])
    step = random.choice([1, 2])
    xs = [step, 2 * step, 3 * step]
    ys = [mA * x + bA for x in xs]
    answer = "A" if bA > bB else "B"
    problem = (
        f"Function A is linear and given by the table ${_table('x', xs, 'y', ys)}$. "
        f"Function B is a line with slope ${mB}$ that crosses the y-axis at ${bB}$. "
        "Which function has the greater initial value (y-intercept)? Answer A or B."
    )
    s = Steps()
    s.step(f"Function A's slope from the table: $y$ changes by ${ys[1] - ys[0]}$ when $x$ "
           f"changes by ${step}$.", rf"m = \frac{{{ys[1] - ys[0]}}}{{{step}}} = {mA}")
    s.step(f"Work back to $x = 0$ from $({xs[0]}, {ys[0]})$.",
           f"b = {ys[0]} - {paren(mA)}({xs[0]}) = {bA}")
    s.step(f"Function B's initial value is ${bB}$. Compare.",
           f"{max(bA, bB)} > {min(bA, bB)}")
    s.answer(answer, lead="The function with the greater initial value is")
    return problem, answer, s.done()


@pre.pre_system_solution_count.variant("no_solution_parameter")
def _system_no_solution_parameter(min_coeff=2, max_coeff=6):
    """For what k does the system have no solution (parallel, distinct lines)?"""
    a1 = _nonzero(-max_coeff, max_coeff)
    b1 = _nonzero(-max_coeff, max_coeff)
    c1 = random.randint(-10, 10)
    t = random.choice([2, 3, -1, -2])
    b2 = t * b1
    c2 = random.choice([v for v in range(-20, 21) if v != t * c1])
    k = t * a1
    sign = "+" if b2 > 0 else "-"
    problem = (
        f"For what value of $k$ does the system ${_xy(a1, b1, c1)}$ and "
        f"$kx {sign} {_term(abs(b2), 'y')} = {c2}$ have no solution?"
    )
    solution = f"${k}$"
    s = Steps()
    s.step("A system has no solution when its lines are parallel: the $x$ and $y$ "
           "coefficients are in the same ratio, but the constants are not.")
    s.step(f"The $y$-coefficients are ${b1}$ and ${b2}$, so the second equation's "
           f"coefficients are ${t}$ times the first's.", rf"k = {t} \times {paren(a1)} = {k}")
    s.step(f"Check the constants: ${t} \\times {paren(c1)} = {t * c1}$, which is not ${c2}$, "
           "so the lines are distinct.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Statistics ---------------------------------------------------------------

@pre.pre_mean_absolute_deviation.variant("transform")
def _mad_transform(min_val=1, max_val=20):
    """MAD after adding a constant to, or multiplying, every value."""
    n = random.choice([4, 5])
    values = _data_with_integer_mean(n, min_val, max_val)
    mean = sum(values) // n
    mad = Fraction(sum(abs(v - mean) for v in values), n)
    data = ", ".join(map(str, values))
    s = Steps()
    if random.random() < 0.5:
        c = random.randint(2, 10)
        answer = mad
        problem = (
            f"The data set ${data}$ has a mean absolute deviation (MAD) of ${num(mad)}$. "
            f"If ${c}$ is added to every value, what is the MAD of the new data set?"
        )
        s.step(f"Adding ${c}$ to every value moves the mean up by ${c}$ too, so every "
               "distance from the mean stays the same.")
        s.step("The MAD is the average of those distances, so it doesn't change.")
    else:
        c = random.randint(2, 5)
        answer = mad * c
        problem = (
            f"The data set ${data}$ has a mean absolute deviation (MAD) of ${num(mad)}$. "
            f"If every value is multiplied by ${c}$, what is the MAD of the new data set?"
        )
        s.step(f"Multiplying every value by ${c}$ multiplies the mean by ${c}$, so every "
               f"distance from the mean is ${c}$ times as large.")
        s.step(f"So the MAD is ${c}$ times as large.", rf"{c} \times {num(mad)} = {num(answer)}")
    solution = f"${num(answer)}$"
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_range.variant("missing_maximum")
def _range_missing_maximum(min_val=1, max_val=50, min_n=4, max_n=7):
    """Reverse: the range and the other values are known, find the largest value."""
    values = random.sample(range(min_val, max_val + 1), random.randint(min_n, max_n) - 1)
    low, high = min(values), max(values)
    x = random.randint(high + 1, high + 30)
    r = x - low
    shown = values + ["x"]
    random.shuffle(shown)
    problem = (
        f"The data set ${', '.join(map(str, shown))}$ has a range of ${r}$, and $x$ is "
        f"its largest value. Find $x$."
    )
    solution = f"${x}$"
    s = Steps()
    s.formula("The range", r"\text{range} = \text{largest} - \text{smallest}")
    s.step(f"$x$ is the largest value and the smallest is ${low}$.", f"{r} = x - {low}")
    s.step(f"Add ${low}$ to both sides.", f"x = {r} + {low} = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_mode.variant("frequency_table")
def _mode_frequency_table(min_val=1, max_val=20):
    """The mode read from a frequency table."""
    values = sorted(random.sample(range(min_val, max_val + 1), 5))
    top = random.randint(4, 8)
    counts = [random.randint(1, top - 1) for _ in values]
    mode_index = random.randrange(5)
    counts[mode_index] = top
    table = _table(r"\text{Value}", values, r"\text{Frequency}", counts)
    problem = (
        "The table shows how many times each value appears in a data set. "
        f"${table}$ What is the mode?"
    )
    solution = f"${values[mode_index]}$"
    s = Steps()
    s.step("The mode is the value that appears most often: the one with the greatest frequency.")
    s.step(f"The greatest frequency is ${top}$, for the value ${values[mode_index]}$.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_interquartile_range.variant("box_plot")
def _iqr_box_plot(min_val=1, max_val=30):
    """IQR read from a box plot described in words."""
    mn, q1, med, q3, mx = sorted(random.sample(range(min_val, max_val + 1), 5))
    problem = (
        f"A box plot of a data set has whiskers from ${mn}$ to ${mx}$. The box runs from "
        f"${q1}$ to ${q3}$, with a line inside it at ${med}$. What is the interquartile range?"
    )
    solution = f"${q3 - q1}$"
    s = Steps()
    s.step("In a box plot, the box runs from the first quartile $Q_1$ to the third quartile "
           f"$Q_3$, so $Q_1 = {q1}$ and $Q_3 = {q3}$.")
    s.formula("The interquartile range", f"IQR = Q_3 - Q_1 = {q3} - {q1} = {q3 - q1}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_interquartile_range.variant("outlier_fence")
def _iqr_outlier_fence(min_val=1, max_val=30):
    """The smallest whole number that the 1.5 IQR rule would call an upper outlier."""
    q1 = random.randint(min_val, max_val)
    q3 = q1 + random.randint(2, 12)
    iqr = q3 - q1
    fence = q3 + Fraction(3, 2) * iqr
    answer = math.floor(fence) + 1
    problem = (
        f"A data set has $Q_1 = {q1}$ and $Q_3 = {q3}$. A value is an upper outlier if it is "
        rf"greater than $Q_3 + 1.5 \times IQR$. What is the smallest whole number that would "
        "be an upper outlier?"
    )
    solution = f"${answer}$"
    s = Steps()
    s.step("Find the interquartile range.", f"IQR = {q3} - {q1} = {iqr}")
    s.step("Find the upper fence.", rf"{q3} + 1.5 \times {iqr} = {num(fence)}")
    s.step(f"An outlier must be greater than ${num(fence)}$, so the smallest whole number "
           "that qualifies is the next whole number above it.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Number sense, geometry, expressions --------------------------------------

@pre.pre_approximate_irrational.variant("integers_between")
def _irrational_integers_between(min_n=2, max_n=120):
    """How many integers lie strictly between two square roots."""
    non_squares = [n for n in range(min_n, max_n + 1) if math.isqrt(n) ** 2 != n]
    while True:
        a, b = sorted(random.sample(non_squares, 2))
        count = math.isqrt(b) - math.isqrt(a)
        if count >= 1:
            break
    lo, hi = math.isqrt(a), math.isqrt(b)
    problem = rf"How many integers are between $\sqrt{{{a}}}$ and $\sqrt{{{b}}}$?"
    solution = f"${count}$"
    s = Steps()
    s.step(f"${lo}^2 = {lo * lo}$ and ${lo + 1}^2 = {(lo + 1) ** 2}$, so "
           rf"$\sqrt{{{a}}}$ is between ${lo}$ and ${lo + 1}$.")
    s.step(f"${hi}^2 = {hi * hi}$ and ${hi + 1}^2 = {(hi + 1) ** 2}$, so "
           rf"$\sqrt{{{b}}}$ is between ${hi}$ and ${hi + 1}$.")
    s.step(f"The integers between them are ${lo + 1}$ through ${hi}$.",
           f"{hi} - {lo + 1} + 1 = {count}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_area_of_trapezoid.variant("height_from_area")
def _trapezoid_height_from_area(min_base=2, max_base=20, min_height=2, max_height=14):
    """Reverse: find the height from the area and both bases."""
    b1, b2 = random.sample(range(min_base, max_base + 1), 2)
    h = random.randint(min_height, max_height)
    area = Fraction((b1 + b2) * h, 2)
    problem = (
        f"A trapezoid has parallel bases of ${b1}$ and ${b2}$ units and an area of "
        f"${num(area)}$ square units. What is its height?"
    )
    solution = f"${h}$"
    s = Steps()
    s.formula("The area of a trapezoid", r"A = \frac{1}{2}(b_1 + b_2)h")
    s.substitute(rf"{num(area)} = \frac{{1}}{{2}}({b1} + {b2})h = {num(Fraction(b1 + b2, 2))}h")
    s.step(f"Divide both sides by ${num(Fraction(b1 + b2, 2))}$.", f"h = {h}")
    s.answer(solution)
    return problem, solution, s.done()


_PERCENT_CONTEXTS = [
    ("students in a class", "walk to school"),
    ("seeds that were planted", "sprouted"),
    ("free throws", "went in"),
    ("people surveyed", "said yes"),
]


@pre.pre_convert_fdp.variant("percent_of_group")
def _fdp_percent_of_group():
    """Part of a group as a percent."""
    total = random.choice([4, 5, 8, 10, 20, 25, 40, 50])
    part = random.choice([p for p in range(1, total) if (100 * p) % total == 0])
    pct = 100 * part // total
    group, verb = random.choice(_PERCENT_CONTEXTS)
    problem = (
        f"Of the ${total}$ {group}, ${part}$ {verb}. What percent is that? "
        "Express your answer as a percent (e.g. 25%)."
    )
    solution = f"{pct}%"
    s = Steps()
    s.step("Write the part over the whole.", rf"\frac{{{part}}}{{{total}}} = {num(Fraction(part, total))}")
    s.step("Multiply by $100$ to write it as a percent.",
           rf"{num(Fraction(part, total))} \times 100 = {pct}\%")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_evaluate_expression.variant("scaled_expression")
def _expression_scaled(min_coeff=2, max_coeff=9, min_const=-9, max_const=9):
    """SAT-style: from ``ax + b = c``, find ``k(ax + b) + d`` without solving for x."""
    a = random.randint(min_coeff, max_coeff)
    b = _nonzero(min_const, max_const)
    c = random.randint(-20, 20)
    k = random.choice([2, 3, 4, 5, -1, -2])
    d = random.randint(min_const, max_const)
    const = k * b + d
    expr = _term(k * a) + (f" {_signed(const)}" if const else "")
    answer = k * c + d
    problem = f"If ${a}x {_signed(b)} = {c}$, what is the value of ${expr}$?"
    solution = f"${answer}$"
    s = Steps()
    rest = f" {_signed(d)}" if d else ""
    s.step(f"Look for ${a}x {_signed(b)}$ inside the expression: it is ${k}$ times it"
           + (f", plus ${d}$." if d else "."),
           f"{expr} = {paren(k)}({a}x {_signed(b)}){rest}")
    s.step(f"Substitute ${a}x {_signed(b)} = {c}$.", f"{paren(k)}({c}){rest} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_distributive_property.variant("factor_out")
def _distributive_factor_out(min_a=2, max_a=9, min_b=1, max_b=9):
    r"""Reverse: the factor in front, $6x + 15 = \square(2x + 5)$."""
    g = random.randint(min_a, max_a)
    b = random.randint(min_b, max_b)
    c = _nonzero(-max_b, max_b)
    problem = (
        rf"Fill in the box: ${_term(g * b)} {_signed(g * c)} = "
        rf"\square({_term(b)} {_signed(c)})$."
    )
    solution = f"${g}$"
    s = Steps()
    s.step("The distributive property multiplies the box by each term in the parentheses.",
           rf"\square \cdot {_term(b)} = {_term(g * b)}")
    s.step(f"So the box is ${g * b} \\div {b} = {g}$. Check the constant term.",
           rf"{g} \times {paren(c)} = {g * c}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_order_rational.variant("between")
def _order_between():
    """Which listed number lies between two others (exactly one does)."""
    values = []
    while len(values) < 5:
        v = Fraction(random.randint(-20, 20), random.choice([1, 2, 4, 5, 8, 10]))
        if v not in values:
            values.append(v)

    def disp(v):
        if v.denominator == 1:
            return str(v.numerator)
        return num(v) if random.random() < 0.5 else frac_from(v)

    shown = {v: disp(v) for v in values}
    ordered = sorted(values)
    i = random.randint(1, 3)
    low, mid, high = ordered[i - 1], ordered[i], ordered[i + 1]
    order = values[:]
    random.shuffle(order)
    problem = (
        f"Of the numbers ${', '.join(shown[v] for v in order)}$, which one is greater than "
        f"${shown[low]}$ and less than ${shown[high]}$? Write it as it appears in the list."
    )
    solution = f"${shown[mid]}$"
    s = Steps()
    s.step("Write each number as a decimal and order them.",
           " < ".join(num(v) for v in ordered))
    s.step(f"The only number between ${num(low)}$ and ${num(high)}$ is ${num(mid)}$.")
    s.answer(solution)
    return problem, solution, s.done()


_DIRECTIONS = {
    "above": (0, 1), "below": (0, -1), "to the right of": (1, 0), "to the left of": (-1, 0),
}


@pre.pre_coordinate_distance.variant("point_from_distance")
def _coordinate_point_from_distance(coord_min=-10, coord_max=10):
    """Reverse: the point a given distance above/below/left/right of another."""
    x, y = random.randint(coord_min, coord_max), random.randint(coord_min, coord_max)
    d = random.randint(1, 10)
    where, (dx, dy) = random.choice(list(_DIRECTIONS.items()))
    nx, ny = x + d * dx, y + d * dy
    problem = f"What point is ${d}$ units {where} $({x}, {y})$? {_PAIR_HINT}"
    solution = pair(nx, ny)
    s = Steps()
    if dx:
        s.step(f"Moving {where.replace('to the ', '').replace(' of', '')} changes only the "
               f"$x$-coordinate, by ${d * dx}$.", f"{x} {_signed(d * dx)} = {nx}")
    else:
        s.step(f"Moving {where} changes only the $y$-coordinate, by ${d * dy}$.",
               f"{y} {_signed(d * dy)} = {ny}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Equations ----------------------------------------------------------------

@pre.pre_two_step_equation.variant("think_of_a_number")
def _two_step_think_of_a_number(min_a=2, max_a=9, min_val=-12, max_val=12):
    """A number puzzle that is a two-step equation."""
    x = random.randint(min_val, max_val)
    a = random.randint(min_a, max_a)
    b = _nonzero(-15, 15)
    c = a * x + b
    then = f"add ${b}$" if b > 0 else f"subtract ${-b}$"
    problem = (
        f"I think of a number, multiply it by ${a}$, and then {then}. The result is "
        f"${c}$. What was my number?"
    )
    solution = f"${x}$"
    s = Steps()
    s.step("Let $n$ be the number and write the equation.", f"{a}n {_signed(b)} = {c}")
    s.step(f"{_move_constant(b)}.", f"{a}n = {c - b}")
    s.step(f"Divide both sides by ${a}$.", f"n = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_multi_step_equation.variant("infinitely_many")
def _multi_step_infinitely_many(min_a=2, max_a=9, min_val=-10, max_val=10):
    """For what k does ``a(x + b) = ax + k`` hold for every x?"""
    a = random.choice([i for i in range(-max_a, max_a + 1) if abs(i) >= min_a])
    b = _nonzero(min_val, max_val)
    problem = (
        f"For what value of $k$ does the equation ${a}(x {_signed(b)}) = {_term(a)} + k$ "
        "have infinitely many solutions?"
    )
    solution = f"${a * b}$"
    s = Steps()
    s.step("Distribute on the left.", f"{_term(a)} {_signed(a * b)} = {_term(a)} + k")
    s.step("An equation has infinitely many solutions when both sides are identical, "
           "so the constant terms must match.", f"k = {a * b}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_variables_both_sides.variant("break_even")
def _both_sides_break_even():
    """Two plans' costs are equal after how many months?"""
    months = random.randint(2, 15)
    r1, r2 = sorted(random.sample(range(2, 30), 2), reverse=True)
    f1 = random.randint(0, 40)
    f2 = f1 + (r1 - r2) * months
    problem = (
        f"Gym A charges ${f1}$ dollars to join plus ${r1}$ dollars per month. Gym B charges "
        f"${f2}$ dollars to join plus ${r2}$ dollars per month. After how many months do "
        "the two gyms cost the same?"
    )
    solution = f"${months}$"
    s = Steps()
    s.step("Let $m$ be the number of months and set the costs equal.",
           f"{f1} + {r1}m = {f2} + {r2}m")
    s.step(f"Subtract ${r2}m$ and ${f1}$ from both sides.", f"{r1 - r2}m = {f2 - f1}")
    s.step(f"Divide both sides by ${r1 - r2}$.", f"m = {months}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Percents and probability --------------------------------------------------

_PERCENTS = [10, 20, 25, 40, 50, 60, 75]


@pre.pre_percent_change.variant("original_from_new")
def _percent_original_from_new():
    """Reverse: the original amount from the new amount and the percent change."""
    pct = random.choice(_PERCENTS)
    up = random.random() < 0.5
    step = 100 // math.gcd(100, pct)
    original = step * random.randint(1, max(1, 400 // step))
    new = original * (100 + pct if up else 100 - pct) // 100
    change = "increase" if up else "decrease"
    factor = Fraction(100 + pct if up else 100 - pct, 100)
    problem = (
        f"After a ${pct}\\%$ {change}, a price is ${new}$ dollars. "
        "What was the original price, in dollars?"
    )
    solution = f"${original}$"
    s = Steps()
    s.step(f"A ${pct}\\%$ {change} multiplies the original price by "
           f"${'1 + ' if up else '1 - '}{num(Fraction(pct, 100))} = {num(factor)}$.",
           rf"\text{{original}} \times {num(factor)} = {new}")
    s.step(f"Divide by ${num(factor)}$ to undo it.",
           rf"\text{{original}} = {new} \div {num(factor)} = {original}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_discount_tax_tip.variant("original_price")
def _discount_original_price(min_price=10, max_price=200):
    """Reverse: the price before a discount from the sale price."""
    pct = random.choice([10, 20, 25, 40, 50])
    price = random.randint(min_price, max_price)
    sale_cents = price * (100 - pct)
    item = random.choice(["jacket", "book", "lamp", "backpack", "chair"])
    factor = Fraction(100 - pct, 100)
    problem = (
        f"After a ${pct}\\%$ discount, a {item} costs ${_money(sale_cents)}$ dollars. "
        "What was the original price? Give your answer in dollars and cents, "
        "for example 12.34."
    )
    solution = _dollars(price * 100)
    s = Steps()
    s.step(f"A ${pct}\\%$ discount leaves ${100 - pct}\\%$ of the price, so the sale price "
           f"is the original times ${num(factor)}$.",
           rf"\text{{original}} \times {num(factor)} = {_money(sale_cents)}")
    s.step(f"Divide by ${num(factor)}$.",
           rf"\text{{original}} = {_money(sale_cents)} \div {num(factor)} = {_money(price * 100)}")
    # The solution's literal dollar sign would read as a math delimiter here.
    s.answer(f"${_money(price * 100)}$ dollars")
    return problem, solution, s.done()


@pre.pre_compound_probability.variant("at_least_one")
def _probability_at_least_one(min_total=2, max_total=10):
    """P(at least one red) from two bags, through the complement."""
    t1, t2 = random.randint(min_total, max_total), random.randint(min_total, max_total)
    r1, r2 = random.randint(1, t1 - 1), random.randint(1, t2 - 1)
    none = Fraction((t1 - r1) * (t2 - r2), t1 * t2)
    answer = 1 - none
    problem = (
        f"Bag A has ${t1}$ marbles, ${r1}$ of them red. Bag B has ${t2}$ marbles, ${r2}$ "
        "of them red. One marble is drawn from each bag. What is the probability that at "
        f"least one of them is red? {_FRACTION_HINT}"
    )
    solution = _frac_solution(answer)
    s = Steps()
    s.step('"At least one red" is the opposite of "no red", so find the probability of '
           "no red first.",
           rf"P(\text{{no red}}) = \frac{{{t1 - r1}}}{{{t1}}} \times \frac{{{t2 - r2}}}{{{t2}}} = {_tex(none)}")
    s.step("Subtract from $1$.",
           rf"P(\text{{at least one red}}) = 1 - {_tex(none)} = {_tex(answer)}")
    s.answer(solution)
    return problem, solution, s.done()


# =============================================================================
# Further variants (beyond each topic's first new question type)
# =============================================================================

# --- Rates and ratios ---------------------------------------------------------

@pre.pre_unit_rate.variant("graph")
def _unit_rate_graph():
    """The unit rate read off a proportional graph through the origin."""
    rate = Fraction(random.randint(1, 30), random.choice([1, 1, 2, 4, 5]))
    x = rate.denominator * random.randint(1, 5)
    y = int(rate * x)
    problem = (
        f"The graph of a proportional relationship between time $x$ (hours) and distance $y$ "
        f"(miles) is a line through $(0, 0)$ and $({x}, {y})$. What is the unit rate, in miles "
        "per hour?"
    )
    solution = f"${num(rate)}$"
    s = Steps()
    s.step("A proportional graph passes through the origin, so the unit rate is $y$ divided by "
           "$x$ at any point on it.", rf"\frac{{{y}}}{{{x}}} = {num(rate)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_unit_rate.variant("complex_fraction")
def _unit_rate_complex_fraction():
    """A unit rate from fractional quantities: 2/3 meter in 1/4 hour."""
    a = Fraction(random.randint(1, 5), random.randint(2, 6))
    b = Fraction(random.randint(1, 3), random.randint(4, 8))
    rate = a / b
    problem = (
        f"A snail crawls ${_tex(a)}$ meter in ${_tex(b)}$ hour. What is its speed in meters per "
        f"hour? {_FRACTION_HINT}"
    )
    solution = _frac_solution(rate)
    s = Steps()
    s.step("Speed is distance divided by time.", rf"{_tex(a)} \div {_tex(b)}")
    s.step("Multiply by the reciprocal of the divisor.",
           rf"{_tex(a)} \times {_tex(1 / b)} = {_tex(rate)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_unit_rate.variant("distance_from_rate")
def _unit_rate_distance_from_rate():
    """Reverse: distance from a unit rate and a (decimal) time."""
    rate = random.randint(20, 70)
    hours = Fraction(random.randint(2, 20), 4)
    distance = rate * hours
    problem = (
        f"A car travels at a steady ${rate}$ miles per hour. How many miles does it travel in "
        f"${num(hours)}$ hours?"
    )
    solution = f"${num(distance)}$"
    s = Steps()
    s.step("Distance is the rate times the time.", rf"{rate} \times {num(hours)} = {num(distance)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_equivalent_ratio.variant("ratio_and_difference")
def _ratio_and_difference(min_term=1, max_term=9, min_factor=2, max_factor=9):
    """The ratio and the difference of two quantities are given; find the larger."""
    while True:
        a, b = sorted(random.sample(range(min_term, max_term + 1), 2))
        if math.gcd(a, b) == 1:
            break
    k = random.randint(min_factor, max_factor)
    problem = (
        f"The ratio of two numbers is ${a}:{b}$, and the larger number is ${(b - a) * k}$ more "
        "than the smaller. What is the larger number?"
    )
    solution = f"${b * k}$"
    s = Steps()
    s.step(f"Write the numbers as ${a}k$ and ${b}k$. Their difference is ${b - a}k$.",
           f"{b - a}k = {(b - a) * k}")
    s.step(f"Divide by ${b - a}$.", f"k = {k}")
    s.step("Find the larger number.", rf"{b} \times {k} = {b * k}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_equivalent_ratio.variant("ratio_table")
def _ratio_table(min_term=1, max_term=9):
    """A ratio table with one missing entry."""
    a, b = random.randint(min_term, max_term), random.randint(min_term, max_term)
    ks = sorted(random.sample(range(1, 11), 4))
    tops, bottoms = [a * k for k in ks], [b * k for k in ks]
    hole = random.randrange(4)
    answer = bottoms[hole]
    shown = [str(v) if i != hole else "?" for i, v in enumerate(bottoms)]
    table = _table(r"\text{Flour (cups)}", tops, r"\text{Sugar (cups)}", shown)
    problem = (
        f"The table shows equivalent ratios of flour to sugar. ${table}$ "
        "What number replaces the question mark?"
    )
    solution = f"${answer}$"
    ref = 0 if hole else 1
    s = Steps()
    s.step("Equivalent ratios scale both quantities by the same factor. Use a complete column.",
           rf"\frac{{{bottoms[ref]}}}{{{tops[ref]}}} = {_tex(Fraction(b, a))}")
    s.step(f"Multiply ${tops[hole]}$ by that ratio.",
           rf"{tops[hole]} \times {_tex(Fraction(b, a))} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_solve_proportion.variant("unknown_denominator")
def _proportion_unknown_denominator(min_term=1, max_term=12):
    r"""The unknown in the denominator: $\frac{a}{x} = \frac{b}{d}$."""
    a, b = random.randint(min_term, max_term), random.randint(min_term, max_term)
    d = random.randint(2, max_term)
    x = Fraction(a * d, b)
    problem = rf"Solve for $x$: $\frac{{{a}}}{{x}} = \frac{{{b}}}{{{d}}}$. {_FRACTION_HINT}"
    solution = _frac_solution(x)
    s = Steps()
    s.step("Cross-multiply.", rf"{b}x = {a} \times {d} = {a * d}")
    s.step(f"Divide both sides by ${b}$.", rf"x = \frac{{{a * d}}}{{{b}}}")
    _simplify(s, a * d, b)
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_scale_length.variant("model_scale")
def _scale_model(min_len=2, max_len=15):
    """A scale model at 1:n, in either direction."""
    n = random.choice([12, 18, 20, 24, 25, 32, 48, 50, 64])
    model = random.randint(min_len, max_len)
    real = model * n
    s = Steps()
    if random.random() < 0.5:
        problem = (f"A model car is built at a scale of $1:{n}$. The model is ${model}$ cm long. "
                   "How long is the real car, in cm?")
        answer = real
        s.step(f"Each centimeter on the model is ${n}$ cm on the real car.",
               rf"{model} \times {n} = {real}")
    else:
        problem = (f"A model car is built at a scale of $1:{n}$. The real car is ${real}$ cm long. "
                   "How long is the model, in cm?")
        answer = model
        s.step(f"The model is $1/{n}$ of the real size.", rf"{real} \div {n} = {model}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


# --- Integers and absolute value ------------------------------------------------

@pre.pre_integer_operations.variant("missing_addend")
def _integers_missing_addend(min_val=-20, max_val=20):
    r"""$(-6) + \square = 4$."""
    a, c = random.randint(min_val, max_val), random.randint(min_val, max_val)
    problem = rf"Fill in the box: ${paren(a)} + \square = {c}$."
    solution = f"${c - a}$"
    s = Steps()
    s.step(f"Subtract ${paren(a)}$ from both sides.", rf"\square = {c} - {paren(a)} = {c - a}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_integer_operations.variant("number_line_moves")
def _integers_number_line_moves():
    """Moves left and right on a number line."""
    start = random.randint(-10, 10)
    moves = [random.choice([-1, 1]) * random.randint(1, 12) for _ in range(random.randint(2, 3))]
    words = ", then ".join(f"${abs(m)}$ units {'right' if m > 0 else 'left'}" for m in moves)
    end = start + sum(moves)
    problem = f"Start at ${start}$ on a number line. Move {words}. Where do you end up?"
    solution = f"${end}$"
    s = Steps()
    s.step("Moving right adds and moving left subtracts.",
           f"{start}" + "".join(f" {_signed(m)}" for m in moves) + f" = {end}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_integer_operations.variant("temperature_change")
def _integers_temperature_change():
    """Temperature change across zero."""
    low = random.randint(-20, -1)
    high = random.randint(1, 25)
    s = Steps()
    if random.random() < 0.5:
        problem = (f"At dawn the temperature was ${low}^\\circ$F. By noon it was ${high}^\\circ$F. "
                   "How many degrees did it rise?")
        answer = high - low
        s.step("The change is the final temperature minus the starting one.",
               f"{high} - {paren(low)} = {answer}")
    else:
        drop = high - low
        problem = (f"At noon the temperature was ${high}^\\circ$F. By midnight it had fallen "
                   f"${drop}$ degrees. What was the temperature at midnight, in degrees F?")
        answer = low
        s.step("A fall subtracts from the starting temperature.", f"{high} - {drop} = {low}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_absolute_value.variant("negative_from_absolute")
def _absolute_negative_from_absolute(min_val=1, max_val=20):
    """Reverse: |x| = n and x < 0."""
    n = random.randint(min_val, max_val)
    problem = f"If $|x| = {n}$ and $x < 0$, what is $x$?"
    solution = f"${-n}$"
    s = Steps()
    s.step(f"Two numbers are ${n}$ units from $0$: ${n}$ and ${-n}$.")
    s.step("Only one of them is negative.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_absolute_value.variant("order_of_operations")
def _absolute_order_of_operations(min_val=-20, max_val=20):
    """|a| - |b| versus |a - b|: where the bars go matters."""
    a = random.randint(min_val, -1)
    b = random.randint(1, max_val)
    s = Steps()
    if random.random() < 0.5:
        expr, answer = f"|{a}| - |{b}|", abs(a) - abs(b)
        s.step("Take each absolute value first.", f"{abs(a)} - {abs(b)}")
        s.step("Subtract.", f"{abs(a)} - {abs(b)} = {answer}")
    else:
        expr, answer = f"|{a} - {b}|", abs(a - b)
        s.step("Work inside the absolute value bars first.", f"{a} - {b} = {a - b}")
        s.step("Take the absolute value.", f"|{a - b}| = {answer}")
    problem = f"Evaluate ${expr}$."
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


# --- Inequalities -------------------------------------------------------------------

@pre.pre_one_step_inequality.variant("from_number_line")
def _inequality_from_number_line():
    """Write the inequality a number-line graph shows."""
    v = random.randint(-10, 10)
    closed = random.random() < 0.5
    left = random.random() < 0.5
    op = ("<=" if closed else "<") if left else (">=" if closed else ">")
    circle = "a closed" if closed else "an open"
    problem = (
        f"A number line shows {circle} circle at ${v}$ with the line shaded to the "
        f"{'left' if left else 'right'}. Write the inequality it shows, using x. Type <= for "
        "at most and >= for at least, for example x <= 4."
    )
    solution = f"$x {op} {v}$"
    s = Steps()
    s.step(f"Shading to the {'left' if left else 'right'} means values "
           f"{'less' if left else 'greater'} than ${v}$.")
    s.step(f"A {'closed' if closed else 'open'} circle means ${v}$ itself is "
           f"{'included' if closed else 'not included'}.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_multi_step_inequality.variant("count_positive_integers")
def _multi_step_count_positive():
    """How many positive integers satisfy ax + b < c (or <=)."""
    a = random.randint(2, 9)
    b = random.randint(-10, 10)
    c = b + a * random.randint(2, 12) + random.randint(0, a - 1)
    op = random.choice(["<", "\\leq"])
    count = sum(1 for v in range(1, 200) if (a * v + b < c if op == "<" else a * v + b <= c))
    problem = f"How many positive integers $x$ satisfy ${a}x {_signed(b)} {op} {c}$?"
    solution = f"${count}$"
    bound = Fraction(c - b, a)
    s = Steps()
    s.step(f"{_move_constant(b)}, then divide by ${a}$.", f"x {op} {_tex(bound)}")
    s.step(f"The positive integers that fit are $1$ through ${count}$.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Scientific notation and exponents -----------------------------------------------

@pre.pre_scientific_notation_ops.variant("normalize")
def _sci_normalize():
    r"""Rewrite $45 \times 10^3$ or $0.045 \times 10^3$ in scientific notation."""
    digits = random.randint(11, 99)
    if random.random() < 0.5:
        coef, coef_text = Fraction(digits), str(digits)
    else:
        coef = Fraction(digits, 1000)
        coef_text = num(coef)
    e = random.randint(-6, 8)
    mant, exp = pre._normalize_sci(coef * Fraction(10) ** e)
    problem = (
        rf"Write ${coef_text} \times 10^{{{e}}}$ in scientific notation. "
        "Answers should be formatted as such: 5.0*10^4."
    )
    solution = f"${mant}*10^{exp}$"
    shift = exp - e
    s = Steps()
    s.step("In scientific notation the first factor is at least $1$ and less than $10$.")
    s.step(f"Move the decimal point ${abs(shift)}$ place{'s' if abs(shift) != 1 else ''} to turn "
           f"${coef_text}$ into ${mant}$, and change the exponent by ${shift}$ to balance it.",
           rf"{coef_text} \times 10^{{{e}}} = {mant} \times 10^{{{exp}}}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_integer_exponent_rules.variant("missing_inner_exponent")
def _exponents_missing_inner():
    r"""$(a^{\square})^m \cdot a^n = a^t$."""
    k, m, n = random.randint(2, 6), random.randint(2, 4), random.randint(1, 6)
    total = k * m + n
    problem = rf"Fill in the box: $(a^{{\square}})^{{{m}}} \cdot a^{{{n}}} = a^{{{total}}}$."
    solution = f"${k}$"
    s = Steps()
    s.step("A power of a power multiplies the exponents; a product adds them.",
           rf"{m} \cdot \square + {n} = {total}")
    s.step(f"Subtract ${n}$ and divide by ${m}$.", rf"\square = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_integer_exponent_rules.variant("evaluate_with_negative")
def _exponents_evaluate_with_negative(min_base=2, max_base=5):
    r"""Evaluate $2^{-3} \cdot 2^5$ or $\frac{3^2}{3^4}$ as a number."""
    b = random.randint(min_base, max_base)
    multiply = random.random() < 0.5
    while True:
        m, n = random.randint(-5, 5), random.randint(-5, 5)
        e = m + n if multiply else m - n
        if abs(e) <= 3:
            break
    if multiply:
        expr = rf"{b}^{{{m}}} \cdot {b}^{{{n}}}"
        rule = "Multiplying powers with the same base adds the exponents."
    else:
        expr = rf"\frac{{{b}^{{{m}}}}}{{{b}^{{{n}}}}}"
        rule = "Dividing powers with the same base subtracts the exponents."
    value = Fraction(b) ** e
    problem = f"Evaluate ${expr}$. {_FRACTION_HINT}"
    solution = _frac_solution(value)
    s = Steps()
    s.step(rule, f"{b}^{{{e}}}")
    if e < 0:
        s.step("A negative exponent means the reciprocal.", rf"{b}^{{{e}}} = \frac{{1}}{{{b ** -e}}}")
    elif e == 0:
        s.step("Any nonzero number to the power $0$ is $1$.")
    else:
        s.step("Evaluate.", f"{b}^{{{e}}} = {b ** e}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Proportional relationships, functions, slope --------------------------------------

@pre.pre_constant_of_proportionality.variant("graph")
def _proportionality_graph(max_k=12):
    """k from a graph through the origin and one point."""
    k = Fraction(random.randint(1, max_k), random.choice([1, 2, 3, 4]))
    x = k.denominator * random.randint(1, 4)
    y = int(k * x)
    problem = (
        f"The graph of a proportional relationship is a line through $(0, 0)$ and $({x}, {y})$. "
        f"What is the constant of proportionality $k$ in $y = kx$? {_FRACTION_HINT}"
    )
    solution = _frac_solution(k)
    s = Steps()
    s.step("For a proportional relationship $k = \\frac{y}{x}$ at any point except the origin.",
           rf"k = \frac{{{y}}}{{{x}}} = {_tex(k)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_constant_of_proportionality.variant("reverse")
def _proportionality_reverse(max_k=12):
    """Reverse: find x from k and y."""
    k = random.randint(2, max_k)
    x = random.randint(2, 12)
    problem = f"$y$ is proportional to $x$, with $y = {k}x$. What is $x$ when $y = {k * x}$?"
    solution = f"${x}$"
    s = Steps()
    s.substitute(f"{k * x} = {k}x")
    s.step(f"Divide both sides by ${k}$.", f"x = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_evaluate_function.variant("input_from_output")
def _evaluate_function_reverse(min_coeff=-9, max_coeff=9):
    """Reverse: for which x does f(x) equal a value?"""
    m = _nonzero(min_coeff, max_coeff)
    b = random.randint(min_coeff, max_coeff)
    x = random.randint(-10, 10)
    v = m * x + b
    problem = f"Given $f(x) = {_term(m)} {_signed(b)}$, for what value of $x$ is $f(x) = {v}$?"
    solution = f"${x}$"
    s = Steps()
    s.step("Set the function equal to the value.", f"{_term(m)} {_signed(b)} = {v}")
    s.step(f"{_move_constant(b)}.", f"{_term(m)} = {v - b}")
    s.step(f"Divide by ${m}$.", f"x = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_evaluate_function.variant("context")
def _evaluate_function_context():
    """A cost function in context."""
    rate, fee = random.randint(3, 15), random.randint(5, 40)
    n = random.randint(2, 20)
    problem = (
        f"A bike rental costs $C(h) = {rate}h + {fee}$ dollars for $h$ hours. "
        f"What does a ${n}$-hour rental cost, in dollars?"
    )
    solution = f"${rate * n + fee}$"
    s = Steps()
    s.substitute(rf"C({n}) = {rate}({n}) + {fee} = {rate * n} + {fee} = {rate * n + fee}",
                 text=f"Substitute $h = {n}$.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_slope_from_two_points.variant("table")
def _slope_table():
    """Slope from a table of a linear function."""
    m = Fraction(_nonzero(-6, 6), random.choice([1, 1, 2, 3]))
    step = m.denominator * random.randint(1, 2)
    # Start on a multiple of the denominator so every y in the table is an integer.
    x0, b = m.denominator * random.randint(-3, 2), random.randint(-10, 10)
    xs = [x0 + i * step for i in range(4)]
    ys = [int(m * x) + b for x in xs]
    problem = (
        f"The table shows points on a line. ${_table('x', xs, 'y', ys)}$ What is the slope of the "
        f"line? {_FRACTION_HINT}"
    )
    solution = _frac_solution(m)
    s = Steps()
    s.step("Slope is the change in $y$ over the change in $x$ between any two columns.",
           rf"\frac{{{ys[1]} - {paren(ys[0])}}}{{{xs[1]} - {paren(xs[0])}}} = "
           rf"\frac{{{ys[1] - ys[0]}}}{{{step}}} = {_tex(m)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_slope_from_two_points.variant("rise_over_run")
def _slope_rise_over_run():
    """Slope from a verbal description of rise and run."""
    rise, run = random.randint(1, 9), random.randint(1, 9)
    up = random.random() < 0.5
    m = Fraction(rise if up else -rise, run)
    problem = (
        f"A line {'rises' if up else 'falls'} ${rise}$ units for every ${run}$ units it moves to "
        f"the right. What is its slope? {_FRACTION_HINT}"
    )
    solution = _frac_solution(m)
    s = Steps()
    s.step(f"Slope is rise over run. A line that {'rises' if up else 'falls'} has a "
           f"{'positive' if up else 'negative'} slope.",
           rf"m = \frac{{{rise if up else -rise}}}{{{run}}} = {_tex(m)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_linear_function_value.variant("table_predict")
def _linear_table_predict():
    """Find the rule from a table, then predict an output beyond it."""
    m, b = _nonzero(-6, 6), random.randint(-10, 10)
    xs = sorted(random.sample(range(0, 6), 3))
    ys = [m * x + b for x in xs]
    target = random.randint(8, 15)
    problem = (
        f"The table shows a linear function. ${_table('x', xs, 'y', ys)}$ What is $y$ when "
        f"$x = {target}$?"
    )
    solution = f"${m * target + b}$"
    s = Steps()
    s.step("Find the slope from two columns.",
           rf"m = \frac{{{ys[1]} - {paren(ys[0])}}}{{{xs[1]} - {xs[0]}}} = {m}")
    s.step(f"Find the y-intercept from $({xs[0]}, {ys[0]})$.",
           f"b = {ys[0]} - {paren(m)}({xs[0]}) = {b}")
    s.step(f"Evaluate at $x = {target}$.", f"y = {m}({target}) {_signed(b)} = {m * target + b}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_linear_function_value.variant("taxi_fare")
def _linear_taxi_fare():
    """A linear cost in context, with cents."""
    base = random.randint(200, 500)       # cents
    per_mile = random.choice([150, 175, 200, 225, 250, 275, 300])
    miles = random.randint(2, 15)
    total = base + per_mile * miles
    problem = (
        f"A taxi charges ${_money(base)}$ dollars plus ${_money(per_mile)}$ dollars per mile. "
        f"What does a ${miles}$-mile ride cost? Give your answer in dollars and cents, for "
        "example 12.34."
    )
    solution = f"${_money(total)}$"
    s = Steps()
    s.step("The cost is the starting fee plus the per-mile rate times the miles.",
           rf"{_money(base)} + {_money(per_mile)} \times {miles} = {_money(total)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_line_from_slope_point.variant("table")
def _line_from_table(min_val=-8, max_val=8):
    """The equation of a line from a table of values."""
    m, b = Fraction(_nonzero(-5, 5)), Fraction(random.randint(min_val, max_val))
    xs = sorted(random.sample(range(-4, 7), 3))
    ys = [int(m * x + b) for x in xs]
    problem = (
        f"The table shows points on a line. ${_table('x', xs, 'y', ys)}$ Write the equation of "
        "the line. Give the equation in the form y = mx + b."
    )
    solution = _line_equation(m, b)
    s = Steps()
    s.step("Find the slope from two columns.",
           rf"m = \frac{{{ys[1]} - {paren(ys[0])}}}{{{xs[1]} - {paren(xs[0])}}} = {_tex(m)}")
    s.step(f"Use $({xs[0]}, {ys[0]})$ to find $b$.",
           f"b = {ys[0]} - {paren(_tex(m * xs[0]))} = {_tex(b)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_line_from_slope_point.variant("context")
def _line_from_context():
    """A linear situation described in words."""
    start, rate = random.randint(2, 40), random.randint(2, 9)
    if random.random() < 0.5:
        m, b, verb = Fraction(rate), Fraction(start), "is filled"
    else:
        start += rate * 10
        m, b, verb = Fraction(-rate), Fraction(start), "drains"
    problem = (
        f"A tank holds ${start}$ liters of water and {verb} at ${rate}$ liters per minute. "
        "Write the amount $y$ after $x$ minutes. Give the equation in the form y = mx + b."
    )
    solution = _line_equation(m, b)
    s = Steps()
    s.step(f"The starting amount is the y-intercept: $b = {_tex(b)}$.")
    s.step(f"The rate is the slope, negative when draining: $m = {_tex(m)}$.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_slope_intercept_form.variant("intercept_only")
def _slope_intercept_intercept_only(min_coeff=-9, max_coeff=9):
    """Just the x- or y-intercept of a line in standard form."""
    A, B = _nonzero(min_coeff, max_coeff), _nonzero(min_coeff, max_coeff)
    C = random.randint(-20, 20)
    which = random.choice(["x", "y"])
    coef = A if which == "x" else B
    value = Fraction(C, coef)
    other = "y" if which == "x" else "x"
    sign = "+" if B > 0 else "-"
    problem = (
        f"What is the {which}-intercept of the line ${_term(A)} {sign} {_term(abs(B), 'y')} = {C}$? "
        f"Give the {which}-value. {_FRACTION_HINT}"
    )
    solution = _frac_solution(value)
    s = Steps()
    s.step(f"At the {which}-intercept, ${other} = 0$.", f"{_term(coef, which)} = {C}")
    s.step(f"Divide by ${coef}$.", f"{which} = {_tex(value)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_system_solution_count.variant("from_descriptions")
def _system_count_from_descriptions():
    """Number of solutions from verbal descriptions of two lines."""
    m1, b1 = _nonzero(-5, 5), random.randint(-9, 9)
    kind = random.choice(["one", "none", "infinite"])
    if kind == "one":
        m2, b2 = random.choice([m for m in range(-5, 6) if m not in (0, m1)]), random.randint(-9, 9)
    elif kind == "none":
        m2, b2 = m1, random.choice([b for b in range(-9, 10) if b != b1])
    else:
        m2, b2 = m1, b1
    problem = (
        f"Line 1 has slope ${m1}$ and y-intercept ${b1}$. Line 2 has slope ${m2}$ and "
        f"y-intercept ${b2}$. How many solutions does the system of these two lines have? "
        "Answer one, none, or infinite."
    )
    s = Steps()
    if kind == "one":
        s.step("Different slopes mean the lines cross at exactly one point.")
    elif kind == "none":
        s.step("Same slope but different y-intercepts: the lines are parallel and never meet.")
    else:
        s.step("Same slope and same y-intercept: it's the same line, so every point is shared.")
    s.answer(kind)
    return problem, kind, s.done()


@pre.pre_system_solution_count.variant("infinitely_many_parameter")
def _system_infinitely_many_parameter():
    """For what k is the second equation a multiple of the first (infinitely many)?"""
    a1, b1 = _nonzero(-6, 6), _nonzero(-6, 6)
    c1 = random.randint(-10, 10)
    t = random.choice([2, 3, -1, -2, 4])
    sign = "+" if t * b1 > 0 else "-"
    problem = (
        f"For what value of $k$ does the system ${_xy(a1, b1, c1)}$ and "
        f"${_term(t * a1)} {sign} {_term(abs(t * b1), 'y')} = k$ have infinitely many solutions?"
    )
    solution = f"${t * c1}$"
    s = Steps()
    s.step(f"The second equation's left side is ${t}$ times the first's.")
    s.step("Infinitely many solutions means the equations describe the same line, so the right "
           f"side must also be ${t}$ times as large.", rf"k = {t} \times {paren(c1)} = {t * c1}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Statistics -----------------------------------------------------------------------

def _mad(values):
    mean = Fraction(sum(values), len(values))
    return mean, sum(abs(v - mean) for v in values) / len(values)


@pre.pre_mean_absolute_deviation.variant("compare_classes")
def _mad_compare_classes(min_val=1, max_val=20):
    """Which of two data sets is more spread out; give its MAD."""
    while True:
        a = _data_with_integer_mean(5, min_val, max_val)
        b = _data_with_integer_mean(5, min_val, max_val)
        if _mad(a)[1] != _mad(b)[1]:
            break
    big = max(_mad(a)[1], _mad(b)[1])
    problem = (
        f"Class A's quiz scores are ${', '.join(map(str, a))}$. Class B's are "
        f"${', '.join(map(str, b))}$. Find the mean absolute deviation (MAD) of the class whose "
        "scores are more spread out."
    )
    solution = f"${num(big)}$"
    s = Steps()
    for label, data in (("A", a), ("B", b)):
        mean, mad = _mad(data)
        s.step(f"Class {label}: the mean is ${num(mean)}$. Average the distances from it.",
               rf"\frac{{{' + '.join(str(abs(v - mean)) for v in data)}}}{{5}} = {num(mad)}")
    s.step("The larger MAD means more spread.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_range.variant("after_transformation")
def _range_after_transformation(min_val=1, max_val=50):
    """The range after adding a constant to, or multiplying, every value."""
    values = random.sample(range(min_val, max_val + 1), random.randint(4, 6))
    r = max(values) - min(values)
    data = ", ".join(map(str, values))
    s = Steps()
    if random.random() < 0.5:
        c = random.randint(2, 20)
        problem = (f"The data set ${data}$ has a range of ${r}$. If ${c}$ is added to every value, "
                   "what is the new range?")
        answer = r
        s.step(f"Adding ${c}$ moves the largest and smallest values by the same amount, so their "
               "difference doesn't change.")
    else:
        c = random.randint(2, 4)
        problem = (f"The data set ${data}$ has a range of ${r}$. If every value is multiplied by "
                   f"${c}$, what is the new range?")
        answer = r * c
        s.step(f"Multiplying by ${c}$ stretches every distance, including the range, by ${c}$.",
               rf"{c} \times {r} = {answer}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_range.variant("frequency_table")
def _range_frequency_table(min_val=1, max_val=50):
    """The range read from a frequency table (a zero-count value isn't in the data)."""
    values = sorted(random.sample(range(min_val, max_val + 1), 5))
    counts = [random.randint(1, 6) for _ in values]
    zero = random.choice([0, 4, None])
    if zero is not None:
        counts[zero] = 0
    present = [v for v, c in zip(values, counts) if c]
    table = _table(r"\text{Value}", values, r"\text{Frequency}", counts)
    problem = f"The table shows a data set. ${table}$ What is the range of the data?"
    solution = f"${max(present) - min(present)}$"
    s = Steps()
    if zero is not None:
        s.step(f"A value with frequency $0$ (here ${values[zero]}$) isn't in the data.")
    s.step("Subtract the smallest value in the data from the largest.",
           f"{max(present)} - {min(present)} = {max(present) - min(present)}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Square roots ---------------------------------------------------------------------

@pre.pre_approximate_irrational.variant("between_integers")
def _irrational_between_integers(min_n=2, max_n=120):
    """Between which consecutive integers a square root lies (enter the smaller)."""
    n = random.choice([v for v in range(min_n, max_n + 1) if math.isqrt(v) ** 2 != v])
    lo = math.isqrt(n)
    problem = rf"$\sqrt{{{n}}}$ lies between two consecutive integers. What is the smaller one?"
    solution = f"${lo}$"
    s = Steps()
    s.step("Find the perfect squares on either side.",
           f"{lo}^2 = {lo * lo} < {n} < {(lo + 1) ** 2} = {lo + 1}^2")
    s.step(rf"So $\sqrt{{{n}}}$ is between ${lo}$ and ${lo + 1}$.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_approximate_irrational.variant("largest_below")
def _irrational_largest_below():
    r"""Largest integer n with $\sqrt{n} < 7.5$ (or $< 7$)."""
    k = random.randint(3, 11)
    bound = Fraction(2 * k + 1, 2) if random.random() < 0.5 else Fraction(k)
    square = bound * bound
    answer = math.ceil(square) - 1
    problem = rf"What is the largest integer $n$ with $\sqrt{{n}} < {num(bound)}$?"
    solution = f"${answer}$"
    s = Steps()
    s.step("Both sides are positive, so square them.", f"n < {num(bound)}^2 = {num(square)}")
    s.step("Take the largest integer strictly less than that.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Geometry -------------------------------------------------------------------------

@pre.pre_area_of_trapezoid.variant("from_vertices")
def _trapezoid_from_vertices():
    """Area of a trapezoid with horizontal bases, from its vertices."""
    y1, h = random.randint(-6, 3), random.randint(2, 8)
    y2 = y1 + h
    xa, b1 = random.randint(-8, 0), random.randint(2, 10)
    xc, b2 = random.randint(-8, 0), random.choice([v for v in range(2, 11) if v != b1])
    pts = [(xa, y1), (xa + b1, y1), (xc + b2, y2), (xc, y2)]
    area = Fraction((b1 + b2) * h, 2)
    problem = (
        "A trapezoid has vertices " + ", ".join(f"$({x}, {y})$" for x, y in pts)
        + ". What is its area, in square units?"
    )
    solution = f"${num(area)}$"
    s = Steps()
    s.step(f"The bases are horizontal, with lengths ${b1}$ (at $y = {y1}$) and ${b2}$ "
           f"(at $y = {y2}$). The height is the vertical distance between them, ${h}$.")
    s.formula("The area of a trapezoid", rf"A = \frac{{1}}{{2}}({b1} + {b2})({h}) = {num(area)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_coordinate_distance.variant("reflection_distance")
def _coordinate_reflection_distance(coord_min=-10, coord_max=10):
    """Distance between a point and its reflection over an axis."""
    x, y = _nonzero(coord_min, coord_max), _nonzero(coord_min, coord_max)
    axis = random.choice(["x", "y"])
    image = (x, -y) if axis == "x" else (-x, y)
    moved, moved_image = (y, image[1]) if axis == "x" else (x, image[0])
    d = abs(moved - moved_image)
    problem = (
        f"The point $({x}, {y})$ is reflected over the {axis}-axis. How far is the point from its "
        "image?"
    )
    solution = f"${d}$"
    s = Steps()
    s.step(f"Reflecting over the {axis}-axis gives $({image[0]}, {image[1]})$.")
    s.step("Only one coordinate changed, so the distance is the difference in that coordinate.",
           f"|{moved} - {paren(moved_image)}| = {d}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Fractions, decimals, percents -----------------------------------------------------

@pre.pre_convert_fdp.variant("repeating_decimal")
def _fdp_repeating_decimal():
    r"""A repeating decimal as a fraction: $0.\overline{3} = 1/3$, $0.\overline{27} = 3/11$."""
    if random.random() < 0.5:
        digits, denom = random.randint(1, 8), 9
    else:
        digits, denom = random.choice([v for v in range(10, 99) if v % 11]), 99
    value = Fraction(digits, denom)
    shown = rf"0.\overline{{{digits}}}"
    problem = (
        f"Write ${shown}$ as a fraction in simplest form. "
        "Express your answer in the form a/b."
    )
    solution = f"${frac_from(value)}$"
    s = Steps()
    s.step(f"A repeating block of {'one digit' if denom == 9 else 'two digits'} equals that "
           f"block over ${denom}$.", rf"{shown} = \frac{{{digits}}}{{{denom}}}")
    _simplify(s, digits, denom)
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_convert_fdp.variant("percent_beyond")
def _fdp_percent_beyond():
    """Percents over 100% and under 1%."""
    s = Steps()
    if random.random() < 0.5:
        value = Fraction(random.randint(101, 400), 100)
        problem = (f"Convert the decimal ${num(value)}$ to a percent. "
                   "Express your answer as a percent (e.g. 25%).")
        solution = f"{num(value * 100)}%"
        s.step("Multiply by $100$. A number greater than $1$ is more than $100\\%$.",
               rf"{num(value)} \times 100 = {num(value * 100)}\%")
    else:
        pct = Fraction(random.randint(1, 9), random.choice([10, 2]))
        problem = f"Convert ${num(pct)}\\%$ to a decimal."
        solution = f"${num(pct / 100)}$"
        s.step("Divide by $100$: move the decimal point two places left.",
               rf"{num(pct)} \div 100 = {num(pct / 100)}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_evaluate_expression.variant("two_variables")
def _expression_two_variables():
    """Evaluate an expression in x and y."""
    a, b = _nonzero(-6, 6), _nonzero(-6, 6)
    c = random.randint(-9, 9)
    x, y = random.randint(-5, 5), random.randint(-5, 5)
    sign = "+" if b > 0 else "-"
    tail = f" {_signed(c)}" if c else ""
    expr = f"{_term(a)} {sign} {_term(abs(b), 'y')}{tail}"
    value = a * x + b * y + c
    problem = f"Evaluate ${expr}$ when $x = {x}$ and $y = {y}$."
    solution = f"${value}$"
    s = Steps()
    s.substitute(f"{a}({x}) {sign} {abs(b)}({y}){tail}",
                 text=f"Substitute $x = {x}$ and $y = {y}$.")
    s.step("Multiply, then add.", f"{a * x} {_signed(b * y)}{tail} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_distributive_property.variant("missing_inner")
def _distributive_missing_inner(min_a=2, max_a=9):
    r"""$3(2x + \square) = 6x + 15$."""
    a, b, c = random.randint(min_a, max_a), random.randint(1, 9), _nonzero(-9, 9)
    problem = rf"Fill in the box: ${a}({_term(b)} + \square) = {_term(a * b)} {_signed(a * c)}$."
    solution = f"${c}$"
    s = Steps()
    s.step(f"Distributing multiplies the box by ${a}$, which must give the constant ${a * c}$.",
           rf"{a} \cdot \square = {a * c}")
    s.step(f"Divide by ${a}$.", rf"\square = {c}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_distributive_property.variant("mental_math")
def _distributive_mental_math():
    r"""Mental math with the distributive property: $7 \times 98 = 7(100 - 2)$."""
    a = random.randint(3, 9)
    base = random.choice([10, 20, 50, 100])
    off = random.randint(1, 4) * random.choice([1, -1])
    n = base + off
    problem = (
        rf"Use the distributive property to find ${a} \times {n}$ by writing ${n}$ as "
        rf"${base} {_signed(off)}$."
    )
    solution = f"${a * n}$"
    s = Steps()
    s.step("Distribute.", rf"{a}({base} {_signed(off)}) = {a} \times {base} {_signed(a * off)}")
    s.step("Add.", f"{a * base} {_signed(a * off)} = {a * n}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_order_rational.variant("extreme")
def _order_extreme():
    """The least, greatest, or closest-to-zero number in a mixed list."""
    values = []
    while len(values) < 5:
        v = Fraction(random.randint(-20, 20), random.choice([1, 2, 4, 5, 8, 10]))
        if v not in values and -v not in values:
            values.append(v)

    def disp(v):
        if v.denominator == 1:
            return str(v.numerator)
        return num(v) if random.random() < 0.5 else frac_from(v)

    shown = {v: disp(v) for v in values}
    ask = random.choice(["least", "greatest", "closest to 0"])
    pick = {"least": min(values), "greatest": max(values),
            "closest to 0": min(values, key=abs)}[ask]
    problem = (
        f"Which number is the {ask}: ${', '.join(shown[v] for v in values)}$? Write it as it "
        "appears in the list."
    )
    solution = f"${shown[pick]}$"
    s = Steps()
    s.step("Write each as a decimal.", r",\ ".join(f"{shown[v]} = {num(v)}" for v in values))
    if ask == "closest to 0":
        s.step("The number closest to $0$ has the smallest absolute value.")
    s.answer(solution)
    return problem, solution, s.done()


# --- Equations ------------------------------------------------------------------------

@pre.pre_two_step_equation.variant("fraction_coefficient")
def _two_step_fraction_coefficient():
    r"""$\frac{x}{a} + b = c$."""
    a = random.randint(2, 9)
    q = random.randint(-10, 10)
    x = a * q
    b = _nonzero(-12, 12)
    c = q + b
    problem = rf"Solve $\frac{{x}}{{{a}}} {_signed(b)} = {c}$ for $x$."
    solution = f"${x}$"
    s = Steps()
    s.step(f"{_move_constant(b)}.", rf"\frac{{x}}{{{a}}} = {c - b}")
    s.step(f"Multiply both sides by ${a}$.", f"x = {x}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_multi_step_equation.variant("consecutive_integers")
def _multi_step_consecutive():
    """Consecutive (or consecutive even/odd) integers with a given sum."""
    count = random.choice([3, 4])
    kind = random.choice(["consecutive", "consecutive even", "consecutive odd"])
    gap = 1 if kind == "consecutive" else 2
    first = random.randint(-20, 40)
    if kind == "consecutive even" and first % 2:
        first += 1
    if kind == "consecutive odd" and first % 2 == 0:
        first += 1
    nums = [first + gap * i for i in range(count)]
    total = sum(nums)
    problem = f"The sum of {count} {kind} integers is ${total}$. What is the largest of them?"
    solution = f"${nums[-1]}$"
    offsets = sum(gap * i for i in range(count))
    terms = ", ".join("$n$" if i == 0 else f"$n + {gap * i}$" for i in range(count))
    s = Steps()
    s.step(f"Let $n$ be the smallest. The integers are {terms}. Add them.",
           f"{count}n + {offsets} = {total}")
    s.step(f"Subtract ${offsets}$ and divide by ${count}$.", f"n = {first}")
    s.step("Find the largest.", f"{first} + {gap * (count - 1)} = {nums[-1]}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_variables_both_sides.variant("no_solution_parameter")
def _both_sides_no_solution(min_coeff=-9, max_coeff=9):
    """For what a does ax + b = cx + d have no solution?"""
    c = _nonzero(min_coeff, max_coeff)
    b = random.randint(-10, 10)
    d = random.choice([v for v in range(-10, 11) if v != b])
    problem = (
        f"For what value of $a$ does the equation $ax {_signed(b)} = {_term(c)} {_signed(d)}$ "
        "have no solution?"
    )
    solution = f"${c}$"
    s = Steps()
    s.step("Collect the $x$-terms on one side.", f"(a - {paren(c)})x = {d - b}")
    s.step(f"If $a = {c}$, the left side is $0$ but the right side is ${d - b}$, which is "
           "impossible. Any other $a$ gives exactly one solution.")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_variables_both_sides.variant("expression_value")
def _both_sides_expression_value(min_coeff=-9, max_coeff=9):
    """Solve ax + b = cx + d, then report x + k."""
    a, c = random.sample([v for v in range(min_coeff, max_coeff + 1) if v != 0], 2)
    x = random.randint(-10, 10)
    b = random.randint(-15, 15)
    d = (a - c) * x + b
    k = _nonzero(-9, 9)
    problem = (
        f"If ${_term(a)} {_signed(b)} = {_term(c)} {_signed(d)}$, what is the value of "
        f"$x {_signed(k)}$?"
    )
    solution = f"${x + k}$"
    s = Steps()
    s.step("Collect $x$-terms on one side and constants on the other.", f"{_term(a - c)} = {d - b}")
    s.step(f"Divide by ${a - c}$.", f"x = {x}")
    s.step(f"Evaluate $x {_signed(k)}$.", f"{x} {_signed(k)} = {x + k}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Percents and probability ---------------------------------------------------------

def _to_cents(value):
    """A Fraction of dollars to whole cents, rounding half up."""
    return math.floor(value * 100 + Fraction(1, 2))


@pre.pre_discount_tax_tip.variant("discount_then_tax")
def _discount_then_tax(min_price=10, max_price=200):
    """A discount followed by sales tax on the sale price."""
    price = random.randint(min_price, max_price)
    off = random.choice([10, 20, 25, 30, 50])
    tax = random.choice([5, 6, 8, 10])
    sale = Fraction(price * (100 - off), 100)
    cents = _to_cents(sale * Fraction(100 + tax, 100))
    problem = (
        f"A ${price}$-dollar item is on sale for ${off}\\%$ off, and then a ${tax}\\%$ sales tax "
        "is added to the sale price. What is the final cost, to the nearest cent? Give your "
        "answer in dollars and cents, for example 12.34."
    )
    solution = _dollars(cents)
    s = Steps()
    s.step(f"Take ${off}\\%$ off: multiply by ${num(Fraction(100 - off, 100))}$.",
           rf"{price} \times {num(Fraction(100 - off, 100))} = {num(sale)}")
    s.step(f"Add ${tax}\\%$ tax: multiply by ${num(Fraction(100 + tax, 100))}$, then round to "
           "the nearest cent.",
           rf"{num(sale)} \times {num(Fraction(100 + tax, 100))} \approx {_money(cents)}")
    s.answer(f"${_money(cents)}$ dollars")
    return problem, solution, s.done()


@pre.pre_discount_tax_tip.variant("better_coupon")
def _discount_better_coupon(min_price=20, max_price=120):
    """Percent off versus dollars off: the lower final price."""
    price = random.randint(min_price, max_price)
    pct = random.choice([10, 15, 20, 25, 30])
    dollars = random.randint(5, 30)
    pct_cents = price * (100 - pct)
    if pct_cents == (price - dollars) * 100:
        dollars += 1
    flat_cents = (price - dollars) * 100
    best = min(pct_cents, flat_cents)
    problem = (
        f"An item costs ${price}$ dollars. Coupon A takes ${pct}\\%$ off; coupon B takes "
        f"${dollars}$ dollars off. Using the better coupon, what is the price? Give your answer "
        "in dollars and cents, for example 12.34."
    )
    solution = _dollars(best)
    s = Steps()
    s.step(f"Coupon A: ${pct}\\%$ off leaves ${100 - pct}\\%$ of the price.",
           rf"{price} \times {num(Fraction(100 - pct, 100))} = {_money(pct_cents)}")
    s.step("Coupon B:", f"{price} - {dollars} = {_money(flat_cents)}")
    s.step("The better coupon gives the lower price.")
    s.answer(f"${_money(best)}$ dollars")
    return problem, solution, s.done()


@pre.pre_discount_tax_tip.variant("successive_discounts")
def _discount_successive():
    """Two discounts in a row (not the same as their sum)."""
    price = random.choice(range(20, 201, 4))
    p1, p2 = random.choice([10, 20, 25, 50]), random.choice([10, 20, 25, 50])
    first = Fraction(price * (100 - p1), 100)
    cents = _to_cents(first * Fraction(100 - p2, 100))
    problem = (
        f"A ${price}$-dollar coat is marked ${p1}\\%$ off. At the register, another ${p2}\\%$ is "
        "taken off the reduced price. What is the final price, to the nearest cent? Give your "
        "answer in dollars and cents, for example 12.34."
    )
    solution = _dollars(cents)
    s = Steps()
    s.step(f"First discount: keep ${100 - p1}\\%$.",
           rf"{price} \times {num(Fraction(100 - p1, 100))} = {num(first)}")
    s.step(f"The second discount applies to the new price: keep ${100 - p2}\\%$.",
           rf"{num(first)} \times {num(Fraction(100 - p2, 100))} \approx {_money(cents)}")
    s.answer(f"${_money(cents)}$ dollars")
    return problem, solution, s.done()


@pre.pre_compound_probability.variant("without_replacement")
def _probability_without_replacement(min_total=3, max_total=10):
    """Two draws from one bag without replacement."""
    total = random.randint(min_total, max_total)
    red = random.randint(2, total - 1)
    answer = Fraction(red, total) * Fraction(red - 1, total - 1)
    problem = (
        f"A bag has ${total}$ marbles, ${red}$ of them red. Two marbles are drawn without "
        f"replacement. What is the probability that both are red? {_FRACTION_HINT}"
    )
    solution = _frac_solution(answer)
    s = Steps()
    s.step("The first draw is red with probability", rf"\frac{{{red}}}{{{total}}}")
    s.step("Without replacement, one red marble is gone for the second draw.",
           rf"\frac{{{red - 1}}}{{{total - 1}}}")
    s.step("Multiply.",
           rf"\frac{{{red}}}{{{total}}} \times \frac{{{red - 1}}}{{{total - 1}}} = {_tex(answer)}")
    s.answer(solution)
    return problem, solution, s.done()


def _proper_fraction():
    d = random.randint(2, 6)
    return Fraction(random.randint(1, d - 1), d)


@pre.pre_compound_probability.variant("missing_probability")
def _probability_missing():
    """Reverse: P(A) and P(A and B) for independent events give P(B)."""
    pa, pb = _proper_fraction(), _proper_fraction()
    both = pa * pb
    problem = (
        f"Events $A$ and $B$ are independent. $P(A) = {frac_from(pa)}$ and "
        f"$P(A \\text{{ and }} B) = {frac_from(both)}$. What is $P(B)$? {_FRACTION_HINT}"
    )
    solution = _frac_solution(pb)
    s = Steps()
    s.step("For independent events, $P(A \\text{ and } B) = P(A) \\cdot P(B)$.",
           f"{_tex(both)} = {_tex(pa)} \\cdot P(B)")
    s.step(f"Divide by ${_tex(pa)}$.", f"P(B) = {_tex(pb)}")
    s.answer(solution)
    return problem, solution, s.done()


_EXPERIMENTS = [
    ("a coin is flipped", 2), ("a number cube is rolled", 6),
    ("a spinner with 4 equal sections is spun", 4), ("a letter is picked from A, B, and C", 3),
    ("a card is drawn from cards numbered 1 to 5", 5),
]


@pre.pre_compound_probability.variant("sample_space")
def _probability_sample_space():
    """Size of the sample space of a two-part experiment."""
    (first, n1), (second, n2) = random.sample(_EXPERIMENTS, 2)
    problem = f"First {first}, then {second}. How many outcomes are in the sample space?"
    solution = f"${n1 * n2}$"
    s = Steps()
    s.step("By the counting principle, multiply the number of outcomes of each part.",
           rf"{n1} \times {n2} = {n1 * n2}")
    s.answer(solution)
    return problem, solution, s.done()


@pre.pre_unit_rate.variant("table")
def _unit_rate_table():
    """A unit rate from a proportional table."""
    rate = random.randint(2, 15)
    xs = sorted(random.sample(range(1, 10), 3))
    ys = [rate * x for x in xs]
    table = _table(r"\text{Hours}", xs, r"\text{Miles}", ys)
    problem = (
        f"The table shows how far a cyclist rides. ${table}$ "
        "What is the cyclist's speed, in miles per hour?"
    )
    solution = f"${rate}$"
    s = Steps()
    s.step("Divide miles by hours for any column.", rf"\frac{{{ys[0]}}}{{{xs[0]}}} = {rate}")
    s.answer(solution)
    return problem, solution, s.done()
