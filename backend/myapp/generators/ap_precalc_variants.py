"""Extra question types for the AP Precalculus topics.

Variants for the generators in ``ap_precalc_functions``, ``ap_precalc_matrices``
and ``ap_precalc_trig``. Each attaches to its topic's dispatcher (see
``_variants.with_variants``); the original question stays as the ``classic``
variant. Variants only use their own topic's skill. See
docs/generator-variations.md.
"""
import math
import random
from fractions import Fraction

from ._format import frac_from, num, pair
from ._steps import Steps, paren, tex_frac
from . import ap_precalc_functions as fn, ap_precalc_matrices as mx, ap_precalc_trig as tr
from .prealgebra_variants import _table

_FRACTION_HINT = "Express your answer as a fraction in the form a/b, or an integer."
_ROUND = "Round your answer to the nearest thousandth."
_ROUNDED = "Rounded to the nearest thousandth, the answer is"


def _nonzero(lo, hi):
    return random.choice([i for i in range(lo, hi + 1) if i != 0])


def _tex(value):
    v = Fraction(value)
    return str(v.numerator) if v.denominator == 1 else tex_frac(v.numerator, v.denominator)


def _poly(coeffs):
    from .algebra2_variants import _poly as poly
    return poly(coeffs)


def _matrix_tex(m):
    return r"\begin{bmatrix}" + r" \\ ".join(" & ".join(str(v) for v in row) for row in m) + r"\end{bmatrix}"


# --- Functions and their rates of change -----------------------------------------------------

@fn.pc_change_in_tandem.variant("from_rates")
def _tandem_from_rates():
    """Concavity read from a table of average rates of change."""
    up = random.random() < 0.5
    inc = random.random() < 0.5
    rates = sorted(random.sample(range(1, 30), 4), reverse=not up)
    if not inc:
        rates = [-r for r in sorted(random.sample(range(1, 30), 4), reverse=up)]
    intervals = [f"[{i}, {i + 1}]" for i in range(4)]
    from_text = ", ".join(f"${r}$ on ${iv}$" for r, iv in zip(rates, intervals))
    problem = (
        f"The average rates of change of $f$ on consecutive intervals are {from_text}. Is the graph of $f$ concave up or "
        "concave down? Answer concave up or concave down."
    )
    answer = "concave up" if rates[1] > rates[0] else "concave down"
    s = Steps()
    s.step("Concave up means the rate of change is increasing; concave down means it's decreasing.")
    s.step(f"The rates {'increase' if answer == 'concave up' else 'decrease'} from interval to interval.")
    s.answer(answer)
    return problem, answer, s.done()


@fn.pc_second_differences.variant("missing_entry")
def _second_differences_missing():
    """A missing table value of a quadratic, from constant second differences."""
    a, b, c = _nonzero(-4, 4), random.randint(-9, 9), random.randint(-9, 9)
    xs = list(range(0, 5))
    ys = [a * x * x + b * x + c for x in xs]
    hole = random.randint(1, 3)
    shown = [str(y) if i != hole else "?" for i, y in enumerate(ys)]
    problem = f"The table shows a quadratic function. ${_table('x', xs, 'f(x)', shown)}$ What number replaces the question mark?"
    solution = f"{ys[hole]}"
    s = Steps()
    s.step("A quadratic's second differences are constant.", f"2a = {2 * a}")
    s.step("Use the second difference with the known neighbors to fill the gap.", f"f({hole}) = {ys[hole]}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_second_differences.variant("leading_from_difference")
def _second_differences_leading():
    """For equally spaced x with step h, the second difference is 2ah^2."""
    a = Fraction(_nonzero(-6, 6), random.choice([1, 2]))
    h = random.choice([1, 2])
    d = 2 * a * h * h
    problem = (
        f"A quadratic $f(x) = ax^2 + bx + c$ is evaluated at $x$-values ${h}$ apart, and its second differences are all "
        f"${num(d)}$. What is $a$? {_FRACTION_HINT}"
    )
    solution = frac_from(a)
    s = Steps()
    s.step("For $x$-values $h$ apart, the second difference is $2ah^2$.", rf"2a({h})^2 = {num(d)} \Rightarrow a = {_tex(a)}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_degree_from_differences.variant("leading_coefficient")
def _differences_leading_coefficient():
    """The constant n-th difference of a degree-n polynomial (step 1) is n! times the leading coefficient."""
    n = random.choice([2, 3])
    a = _nonzero(-4, 4)
    coeffs = [a] + [random.randint(-5, 5) for _ in range(n)]
    ys = [sum(c * x ** (n - i) for i, c in enumerate(coeffs)) for x in range(0, 6)]
    problem = (
        f"The table shows a polynomial of degree ${n}$. ${_table('x', list(range(6)), 'p(x)', ys)}$ What is its leading coefficient?"
    )
    solution = f"{a}"
    diffs = ys
    for _ in range(n):
        diffs = [diffs[i + 1] - diffs[i] for i in range(len(diffs) - 1)]
    s = Steps()
    s.step(f"Take differences ${n}$ times; they become constant.", f"\\Delta^{n} = {diffs[0]}")
    s.step(f"For steps of $1$, that constant is ${n}!$ times the leading coefficient.", rf"\frac{{{diffs[0]}}}{{{math.factorial(n)}}} = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_complex_conjugate_zeros.variant("max_real_zeros")
def _conjugate_max_real():
    """Nonreal zeros come in pairs, which caps the real zeros."""
    degree = random.randint(3, 9)
    pairs = random.randint(1, degree // 2)
    nonreal = 2 * pairs
    problem = (
        f"A polynomial of degree ${degree}$ with real coefficients has exactly ${nonreal}$ nonreal zeros. How many real zeros "
        "does it have, counting multiplicity?"
    )
    solution = f"{degree - nonreal}"
    s = Steps()
    s.step("Counting multiplicity, a degree-$n$ polynomial has $n$ zeros in all.", f"{degree} - {nonreal} = {degree - nonreal}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_complex_conjugate_zeros.variant("minimum_degree")
def _conjugate_minimum_degree():
    """Minimum degree: every nonreal zero brings its conjugate."""
    real = random.sample(range(-6, 7), random.randint(0, 2))
    nonreal = [(random.randint(-5, 5), _nonzero(1, 6)) for _ in range(random.randint(1, 2))]
    shown = [f"${r}$" for r in real] + [f"${a} {'+' if b > 0 else '-'} {abs(b)}i$" if a else f"${b}i$" for a, b in nonreal]
    random.shuffle(shown)
    problem = (
        f"A polynomial with real coefficients has zeros {', '.join(shown)}. What is the smallest degree it can have?"
    )
    solution = f"{len(real) + 2 * len(nonreal)}"
    s = Steps()
    s.step("Each nonreal zero must come with its conjugate, so it counts twice.", f"{len(real)} + 2({len(nonreal)}) = {len(real) + 2 * len(nonreal)}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_even_odd_function.variant("value_from_symmetry")
def _even_odd_value():
    """Use the symmetry: f(-a) = f(a) for even f, -f(a) for odd f."""
    kind = random.choice(["even", "odd"])
    a, v = random.randint(1, 9), random.randint(-20, 20)
    problem = f"$f$ is an {kind} function and $f({a}) = {v}$. What is $f({-a})$?"
    solution = f"{v if kind == 'even' else -v}"
    s = Steps()
    s.step("Even means $f(-x) = f(x)$; odd means $f(-x) = -f(x)$.", f"f({-a}) = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_even_odd_function.variant("parameter_for_even")
def _even_odd_parameter():
    """For what k is the polynomial even (or odd)? The wrong-parity terms must vanish."""
    want = random.choice(["even", "odd"])
    k = 0
    a, c = _nonzero(-6, 6), _nonzero(-9, 9)
    if want == "even":
        poly = f"{a}x^4 + kx^3 {'+' if c > 0 else '-'} {abs(c)}x^2 + {random.randint(1, 9)}"
    else:
        poly = f"{a}x^5 + kx^2 {'+' if c > 0 else '-'} {abs(c)}x"
    problem = f"For what value of $k$ is $f(x) = {poly}$ an {want} function?"
    solution = f"{k}"
    s = Steps()
    s.step(f"An {want} polynomial has only {'even' if want == 'even' else 'odd'} powers of $x$, so the other term's coefficient "
           "must be $0$.", "k = 0")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_function_transformation.variant("preimage")
def _transformation_preimage():
    """Reverse: which point on f maps to a given point on g(x) = a f(b(x - h)) + k."""
    a, b = random.choice([2, 3, -1, -2]), random.choice([1, 2, -1])
    h, k = random.randint(-5, 5), random.randint(-5, 5)
    x0, y0 = random.randint(-6, 6) * b, random.randint(-6, 6)
    gx, gy = Fraction(x0, b) + h, a * y0 + k
    def lead(v):
        return "" if v == 1 else ("-" if v == -1 else str(v))
    inner = f"{lead(b)}(x {'-' if h > 0 else '+'} {abs(h)})" if h else f"{lead(b)}x"
    problem = (
        f"The point $({frac_from(gx)}, {gy})$ is on the graph of $g(x) = {lead(a)}f({inner}) {'+' if k >= 0 else '-'} {abs(k)}$. "
        "Which point on the graph of $f$ does it come from? Format your answer as (x, y), writing any non-integer as a fraction a/b."
    )
    solution = f"({frac_from(Fraction(x0))}, {frac_from(Fraction(y0))})"
    s = Steps()
    s.step("Undo the inside (horizontal) changes on $x$: subtract the shift, then multiply by $b$.",
           rf"x = {b}\left({_tex(gx)} - {paren(h)}\right) = {x0}")
    s.step("Undo the outside (vertical) changes on $y$: subtract $k$, then divide by $a$.", rf"y = \frac{{{gy} - {paren(k)}}}{{{a}}} = {y0}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_function_transformation.variant("new_maximum")
def _transformation_new_maximum():
    """A vertical stretch/shift moves a maximum (a negative stretch turns it into a minimum)."""
    M, m = random.randint(1, 20), random.randint(-20, 0)
    a, k = _nonzero(-4, 4), random.randint(-9, 9)
    new_max = a * M + k if a > 0 else a * m + k
    problem = (
        f"$f$ has a maximum value of ${M}$ and a minimum value of ${m}$. What is the maximum value of "
        f"$g(x) = {a}f(x) {'+' if k >= 0 else '-'} {abs(k)}$?"
    )
    solution = f"{new_max}"
    s = Steps()
    if a > 0:
        s.step("A positive stretch keeps the maximum on top.", f"{a}({M}) + {paren(k)} = {new_max}")
    else:
        s.step("A negative factor flips the graph, so the old minimum becomes the new maximum.", f"{a}({m}) + {paren(k)} = {new_max}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_identify_model.variant("model_constant")
def _identify_model_constant():
    """The defining constant of the model: the common difference or the common ratio."""
    if random.random() < 0.5:
        m, b = _nonzero(-9, 9), random.randint(-10, 10)
        ys = [m * x + b for x in range(5)]
        problem = f"The table shows a linear model. ${_table('x', list(range(5)), 'y', ys)}$ By how much does $y$ change each time $x$ increases by $1$?"
        solution = f"{m}"
        s = Steps()
        s.step("A linear model changes by a constant difference.", f"{ys[1]} - {paren(ys[0])} = {m}")
    else:
        a, r = random.randint(1, 6), Fraction(random.choice([2, 3, 4]), random.choice([1, 1, 2]))
        if r == 1:
            r = Fraction(3)
        scale = r.denominator ** 4
        ys = [a * scale * r ** x for x in range(5)]
        problem = (
            f"The table shows an exponential model. ${_table('x', list(range(5)), 'y', [num(y) for y in ys])}$ By what factor does $y$ "
            f"change each time $x$ increases by $1$? {_FRACTION_HINT}"
        )
        solution = frac_from(r)
        s = Steps()
        s.step("An exponential model changes by a constant ratio.", rf"\frac{{{num(ys[1])}}}{{{num(ys[0])}}} = {_tex(r)}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_quadratic_model_predict.variant("time_of_maximum")
def _quadratic_time_of_max():
    """The vertex time of a projectile model h(t) = -16t^2 + vt + h0."""
    v, h0 = random.choice(range(16, 129, 8)), random.randint(0, 200)
    tmax = Fraction(v, 32)
    ask_time = random.random() < 0.5
    hmax = h0 + Fraction(v * v, 64)
    problem = (
        f"A ball's height in feet is $h(t) = -16t^2 + {v}t + {h0}$. "
        f"{'When does it reach its highest point, in seconds?' if ask_time else 'What is its greatest height, in feet?'}"
    )
    solution = num(tmax if ask_time else hmax)
    s = Steps()
    s.step("The highest point is the vertex.", rf"t = -\frac{{b}}{{2a}} = \frac{{{v}}}{{32}} = {num(tmax)}")
    if not ask_time:
        s.step("Evaluate the height there.", f"h({num(tmax)}) = {num(hmax)}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_exponential_from_two_points.variant("half_life")
def _exponential_half_life():
    """A half-life from two measurements of a decaying amount."""
    half = random.randint(2, 20)
    t = random.randint(1, 15)
    a0 = random.choice(range(100, 1001, 50))
    later = a0 * 0.5 ** (t / half)
    later_shown = Fraction(round(later * 1000), 1000)
    hl = t * math.log(2) / math.log(a0 / float(later_shown))
    problem = (
        f"A sample has ${a0}$ grams, and ${t}$ hours later it has ${num(later_shown)}$ grams. Assuming exponential decay, what is "
        f"its half-life, in hours? {_ROUND}"
    )
    solution = num(hl)
    s = Steps()
    s.step("Exponential decay: the fraction left after $t$ hours is $(1/2)^{t/h}$.", rf"\left(\frac{{1}}{{2}}\right)^{{{t}/h}} = \frac{{{num(later_shown)}}}{{{a0}}}")
    s.step("Solve with logarithms.", rf"h = \frac{{{t}\ln 2}}{{\ln({a0}/{num(later_shown)})}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@fn.pc_rewrite_exponential.variant("monthly_factor")
def _rewrite_monthly_factor():
    """The monthly growth factor equivalent to an annual one."""
    pct = random.choice([3, 4, 5, 6, 8, 10, 12, 15, 20, 25])
    factor = (1 + pct / 100) ** (1 / 12)
    problem = (
        f"A quantity grows by ${pct}\\%$ per year, so $A = A_0({num(Fraction(100 + pct, 100))})^t$ with $t$ in years. Rewrite it with $t$ in "
        f"months: by what factor does it grow each month? {_ROUND}"
    )
    solution = num(factor)
    s = Steps()
    s.step("Twelve months make a year, so the monthly factor to the 12th power is the yearly factor.",
           rf"b^{{12}} = {num(Fraction(100 + pct, 100))} \Rightarrow b = {num(Fraction(100 + pct, 100))}^{{1/12}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@fn.pc_residual.variant("actual_from_residual")
def _residual_actual():
    """Reverse: the actual value from the prediction and the residual."""
    m, b = Fraction(random.randint(-40, 40), 10), Fraction(random.randint(-50, 100), 10)
    x = random.randint(0, 20)
    res = Fraction(random.randint(-90, 90), 10)
    actual = m * x + b + res
    problem = (
        f"A model predicts $\\hat y = {num(m)}x {'+' if b >= 0 else '-'} {num(abs(b))}$. The residual at $x = {x}$ is ${num(res)}$. "
        "What is the actual $y$-value there?"
    )
    solution = num(actual)
    s = Steps()
    s.step("Predict.", rf"\hat y = {num(m * x + b)}")
    s.step("Residual = actual minus predicted, so add.", f"{num(m * x + b)} + {paren(num(res))} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_inverse_exponential.variant("time_to_reach")
def _inverse_exponential_time():
    """When a growing amount reaches a target (whole-number answer)."""
    a, b = random.randint(1, 9), random.choice([2, 3, 4])
    t = random.randint(1, 6)
    target = a * b ** t
    problem = f"A population is modeled by $P(t) = {a} \\cdot {b}^t$. After how many years does it reach ${target}$?"
    solution = f"{t}"
    s = Steps()
    s.step(f"Divide by ${a}$.", f"{b}^t = {b ** t}")
    s.step("Write as a power of the base.", f"t = \\log_{{{b}}} {b ** t} = {t}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_log_function_features.variant("parameter_from_point")
def _log_features_parameter():
    """Find a so that f(x) = a log_b(x - h) passes through a point."""
    b = random.choice([2, 3, 5, 10])
    h = random.randint(-5, 5)
    e = random.randint(1, 3)
    a = _nonzero(-5, 5)
    x = h + b ** e
    y = a * e
    problem = (
        f"$f(x) = a\\log_{{{b}}}(x {'-' if h > 0 else '+'} {abs(h)})$ passes through $({x}, {y})$. What is $a$?" if h else
        f"$f(x) = a\\log_{{{b}}} x$ passes through $({x}, {y})$. What is $a$?"
    )
    solution = f"{a}"
    s = Steps()
    s.step("Substitute the point.", rf"{y} = a\log_{{{b}}} {b ** e} = {e}a")
    s.step("Solve.", f"a = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_solve_log_equation.variant("count_valid")
def _solve_log_count():
    """How many solutions of log(x^2 + b) = log(x + a) survive the domain check (0, 1 or 2)."""
    # x^2 + b = x + a has roots r and 1 - r when b - a = r(1 - r). At a root both sides are
    # equal, so x + a > 0 is the only check. (log(x + a) + log(x + b) = log c always has exactly
    # one valid root, so it can't make a counting question.)
    a = random.randint(-9, 9)
    if random.random() < 0.2:
        b = a + random.randint(1, 9)     # b - a >= 1 > 1/4: no real roots at all
        roots = []
    else:
        r = random.randint(-8, 8)
        b = a + r * (1 - r)
        roots = [r, 1 - r]
    valid = [x for x in roots if x + a > 0]

    def arg(k, var="x"):
        return var if k == 0 else f"{var} {'+' if k > 0 else '-'} {abs(k)}"
    left = arg(b, "x^2")
    problem = f"How many solutions does $\\log({left}) = \\log({arg(a)})$ have?"
    solution = f"{len(valid)}"
    s = Steps()
    if roots:
        s.step("Drop the logs and solve.", f"{left} = {arg(a)} \\Rightarrow x = {roots[0]} \\text{{ or }} x = {roots[1]}")
    else:
        s.step("Drop the logs: the quadratic has a negative discriminant, so no real solutions.",
               f"x^2 - x + {b - a} = 0, \\quad 1 - 4({b - a}) < 0")
    s.step("At a solution both sides are equal, so a candidate works exactly when $" + arg(a) + " > 0$.",
           ", ".join(map(str, valid)) if valid else r"\text{none}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_exp_log_inequality.variant("smallest_integer")
def _exp_inequality_smallest_integer():
    """The smallest integer with b^x > N."""
    b = random.choice([2, 3, 5, 10])
    N = random.randint(5, 5000)
    x = 0
    while b ** x <= N:
        x += 1
    problem = f"What is the smallest integer $x$ with ${b}^x > {N}$?"
    solution = f"{x}"
    s = Steps()
    s.step("Take logs (base " + str(b) + ").", rf"x > \log_{{{b}}} {N} \approx {num(math.log(N, b))}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_log_model_context.variant("magnitude_ratio")
def _log_magnitude_ratio():
    """Richter magnitudes: each unit is 10 times the amplitude."""
    m1 = Fraction(random.randint(30, 90), 10)
    diff = random.randint(1, 4)
    m2 = m1 - diff
    problem = (
        f"On the Richter scale, $M = \\log\\left(\\frac{{A}}{{A_0}}\\right)$. How many times larger is the amplitude of a magnitude "
        f"${num(m1)}$ earthquake than a magnitude ${num(m2)}$ earthquake?"
    )
    solution = f"{10 ** diff}"
    s = Steps()
    s.step("Subtracting the magnitudes gives the log of the amplitude ratio.", rf"\log\frac{{A_1}}{{A_2}} = {num(m1)} - {num(m2)} = {diff}")
    s.step("Undo the log.", f"10^{diff} = {10 ** diff}")
    s.answer(solution)
    return problem, solution, s.done()


@fn.pc_semilog_model.variant("predict")
def _semilog_predict():
    """Predict y from a line fitted to log10(y)."""
    m = Fraction(random.randint(1, 30), 100)
    b = Fraction(random.randint(0, 200), 100)
    x = random.randint(1, 12)
    y = 10 ** float(m * x + b)
    problem = (
        f"Data were fit by the line $\\log_{{10}} y = {num(m)}x + {num(b)}$. Predict $y$ when $x = {x}$. {_ROUND}"
    )
    solution = num(y)
    s = Steps()
    s.step("Find $\\log_{10} y$ first.", f"{num(m)}({x}) + {num(b)} = {num(m * x + b)}")
    s.step("Undo the log.", rf"y = 10^{{{num(m * x + b)}}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


# --- Periodic and trigonometric functions ---------------------------------------------------------

@tr.pc_periodic_values.variant("negative_input")
def _periodic_negative_input():
    """f at a negative input: add whole periods until it lands in one cycle."""
    p = random.randint(3, 7)
    vals = [random.randint(-9, 9) for _ in range(p)]
    x = -random.randint(1, 60)
    listing = ", ".join(f"$f({i}) = {v}$" for i, v in enumerate(vals))
    problem = f"$f$ is periodic with period ${p}$, and over one period {listing}. Find $f({x})$."
    solution = f"{vals[x % p]}"
    s = Steps()
    s.step(f"Add a multiple of ${p}$ to land in $0$ to ${p - 1}$.", f"{x} + {p * ((-x) // p + 1)} \\to {x % p}")
    s.answer(solution)
    return problem, solution, s.done()


@tr.pc_sinusoidal_model.variant("first_time_at_height")
def _sinusoidal_first_time():
    """A Ferris wheel rider boarding at the bottom: first time at height h."""
    d = random.randint(20, 80)
    low = random.randint(1, 6)
    T = random.randint(4, 20)
    r = d / 2
    mid = low + r
    h = random.randint(low + 1, low + d - 1)
    # h(t) = mid - r cos(2pi t / T); first t with h(t) = h
    t = T / (2 * math.pi) * math.acos((mid - h) / r)
    problem = (
        f"A Ferris wheel with diameter ${d}$ ft has its lowest point ${low}$ ft above the ground and turns once every ${T}$ minutes. "
        f"A rider boards at the bottom at $t = 0$. When does the rider first reach ${h}$ ft? {_ROUND}"
    )
    solution = num(t)
    s = Steps()
    s.step("Starting at the bottom, the height is a reflected cosine.", rf"h(t) = {num(mid)} - {num(r)}\cos\left(\frac{{2\pi t}}{{{T}}}\right)")
    s.step("Set it equal and solve for the first time.", rf"t = \frac{{{T}}}{{2\pi}}\cos^{{-1}}\left(\frac{{{num(mid)} - {h}}}{{{num(r)}}}\right) \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@tr.pc_sinusoid_transformations.variant("dilation_factor")
def _sinusoid_dilation_factor():
    """Reverse: the horizontal dilation factor from the new period."""
    old = random.choice([360, 180])
    factor = Fraction(random.choice([1, 2, 3, 4, 5, 6]), random.choice([1, 2, 3]))
    new = old * factor
    func = "\\sin" if old == 360 else "\\tan"
    problem = (
        f"The graph of $y = {func} x$ (in degrees, period ${old}^\\circ$) is dilated horizontally so its period becomes "
        f"${num(new)}^\\circ$. By what factor was it dilated? {_FRACTION_HINT}"
    )
    solution = frac_from(factor)
    s = Steps()
    s.step("A horizontal dilation multiplies the period by its factor.", rf"\frac{{{num(new)}}}{{{old}}} = {_tex(factor)}")
    s.answer(solution)
    return problem, solution, s.done()


@tr.pc_tangent_features.variant("count_asymptotes")
def _tangent_count_asymptotes():
    """Vertical asymptotes of tan(bx) in [0, 360)."""
    b = random.randint(1, 6)
    count = 2 * b
    problem = f"How many vertical asymptotes does $y = \\tan({b if b > 1 else ''}x)$ have for $0^\\circ \\leq x < 360^\\circ$?"
    solution = f"{count}"
    s = Steps()
    s.step(f"$\\tan u$ has an asymptote every $180^\\circ$, at $u = 90^\\circ, 270^\\circ, \\ldots$; here $u = {b}x$ sweeps "
           f"${360 * b}^\\circ$.", f"\\frac{{{360 * b}}}{{180}} = {count}")
    s.answer(solution)
    return problem, solution, s.done()


@tr.pc_trig_inequality.variant("solution_length")
def _trig_inequality_length():
    """The total length of the solution set in [0, 360)."""
    # (a, b): f(x) > v exactly on the arc running counterclockwise from a to b.
    func, v, (a, b) = random.choice([("sin", r"\frac{1}{2}", (30, 150)), ("cos", r"\frac{1}{2}", (300, 60)),
                                    ("sin", r"-\frac{1}{2}", (330, 210)), ("cos", r"-\frac{1}{2}", (240, 120)),
                                    ("sin", r"\frac{\sqrt{2}}{2}", (45, 135)), ("cos", r"\frac{\sqrt{3}}{2}", (330, 30))])
    greater = random.random() < 0.5
    inside = (b - a) % 360
    length = inside if greater else 360 - inside
    problem = (
        f"For $0^\\circ \\leq x < 360^\\circ$, the solutions of $\\{func} x {'>' if greater else '<'} {v}$ form one or two intervals. "
        "What is their total length, in degrees?"
    )
    solution = f"{length}"
    s = Steps()
    s.step(f"$\\{func} x = {v}$ at the boundary angles; the inequality holds on the arcs between them.")
    s.step("Add the lengths of the arcs where it holds.", f"{length}")
    s.answer(solution)
    return problem, solution, s.done()


@tr.pc_polar_graph_features.variant("max_angle")
def _polar_max_angle():
    """The smallest theta > 0 where r = a + b sin(theta) is largest."""
    a, b = random.randint(2, 6), random.randint(1, 6)
    func = random.choice(["sin", "cos"])
    sign = random.choice([1, -1])
    angle = {("sin", 1): 90, ("sin", -1): 270, ("cos", 1): 360, ("cos", -1): 180}[(func, sign)]
    problem = (
        f"For $r = {a} {'+' if sign > 0 else '-'} {b}\\{func}\\theta$ on $0^\\circ < \\theta \\leq 360^\\circ$, at what angle is $r$ "
        "greatest, in degrees?"
    )
    solution = f"{angle}"
    s = Steps()
    s.step(f"$r$ is greatest when ${'+' if sign > 0 else '-'}\\{func}\\theta$ is $1$.", f"\\theta = {angle}")
    s.answer(solution)
    return problem, solution, s.done()


@tr.pc_polar_rate_of_change.variant("faster_interval")
def _polar_faster_interval():
    """Compare average rates of r = a + b sin(theta) on [0, pi/6] and [pi/6, pi/2]."""
    a, b = random.randint(1, 6), _nonzero(-6, 6)
    r = lambda t: a + b * math.sin(t)  # noqa: E731
    rate1 = (r(math.pi / 6) - r(0)) / (math.pi / 6)
    rate2 = (r(math.pi / 2) - r(math.pi / 6)) / (math.pi / 3)
    bigger = rate1 if abs(rate1) > abs(rate2) else rate2
    problem = (
        f"For $r = {a} {'+' if b > 0 else '-'} {abs(b)}\\sin\\theta$, compare the average rates of change of $r$ on "
        "$[0, \\frac{\\pi}{6}]$ and $[\\frac{\\pi}{6}, \\frac{\\pi}{2}]$. Give the one with the larger absolute value. " + _ROUND
    )
    solution = num(bigger)
    s = Steps()
    s.step("Average rate = change in $r$ over change in $\\theta$.",
           rf"\frac{{r(\pi/6) - r(0)}}{{\pi/6}} \approx {num(rate1)}, \quad \frac{{r(\pi/2) - r(\pi/6)}}{{\pi/3}} \approx {num(rate2)}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


# --- Parametric, implicit and vector-valued functions -------------------------------------------

@mx.pc_parametric_position.variant("time_at_point")
def _parametric_time_at_point():
    """Reverse: the time when a linear particle is at a given point."""
    a, b, c, d = _nonzero(-5, 5), random.randint(-9, 9), _nonzero(-5, 5), random.randint(-9, 9)
    t = random.randint(0, 10)
    problem = (
        f"A particle moves along $x(t) = {a}t {'+' if b >= 0 else '-'} {abs(b)}$, $y(t) = {c}t {'+' if d >= 0 else '-'} {abs(d)}$. "
        f"At what time $t$ is it at $({a * t + b}, {c * t + d})$?"
    )
    solution = f"{t}"
    s = Steps()
    s.step("Solve either coordinate equation (both give the same $t$).", f"{a}t {'+' if b >= 0 else '-'} {abs(b)} = {a * t + b} \\Rightarrow t = {t}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_parametric_rate_of_change.variant("average_speed")
def _parametric_average_speed():
    """Average speed of straight-line motion: distance over time."""
    a, c = _nonzero(-6, 6), _nonzero(-6, 6)
    speed = math.hypot(a, c)
    t1, t2 = sorted(random.sample(range(0, 10), 2))
    problem = (
        f"A particle moves along $x(t) = {a}t$, $y(t) = {c}t$. What is its average speed from $t = {t1}$ to $t = {t2}$? {_ROUND}"
    )
    solution = num(speed)
    s = Steps()
    s.step("The path is a straight line, so distance traveled is the straight-line distance.",
           rf"d = \sqrt{{({a}({t2 - t1}))^2 + ({c}({t2 - t1}))^2}}")
    s.step("Divide by the elapsed time.", rf"\frac{{d}}{{{t2 - t1}}} = \sqrt{{{a}^2 + {c}^2}} \approx {solution}")
    s.answer(solution, lead=_ROUNDED)
    return problem, solution, s.done()


@mx.pc_parametric_circle_line.variant("radius_from_period")
def _parametric_radius():
    """x = r cos(kt), y = r sin(kt): the time for one revolution is 2pi/k."""
    r, k = random.randint(1, 9), random.randint(1, 6)
    problem = (
        f"A point moves by $x(t) = {r}\\cos({k}t)$, $y(t) = {r}\\sin({k}t)$. How many full revolutions does it make for "
        "$0 \\leq t \\leq 2\\pi$?"
    )
    solution = f"{k}"
    s = Steps()
    s.step("The angle is $kt$; as $t$ goes from $0$ to $2\\pi$, the angle goes from $0$ to $2k\\pi$.", f"\\frac{{2({k})\\pi}}{{2\\pi}} = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_implicit_curve_points.variant("count_points")
def _implicit_count_points():
    """How many points of a circle have a given x-value (0, 1 or 2)."""
    r = random.randint(2, 10)
    h, k = random.randint(-5, 5), random.randint(-5, 5)
    x = h + random.randint(-r - 2, r + 2)
    d = r * r - (x - h) ** 2
    count = 2 if d > 0 else (1 if d == 0 else 0)
    problem = (
        f"How many points on the curve $(x {'-' if h >= 0 else '+'} {abs(h)})^2 + (y {'-' if k >= 0 else '+'} {abs(k)})^2 = {r * r}$ "
        f"have $x = {x}$?"
    )
    solution = f"{count}"
    s = Steps()
    s.step(f"Substitute $x = {x}$.", f"(y - {paren(k)})^2 = {r * r} - {(x - h) ** 2} = {d}")
    s.step("A positive right side gives two $y$-values, zero gives one, negative gives none.")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_parametrize_ellipse.variant("semi_axis")
def _ellipse_semi_axis():
    """Reverse: the ellipse equation's denominator from a parametrization."""
    p, q = random.randint(1, 9), random.randint(1, 9)
    h, k = random.randint(-5, 5), random.randint(-5, 5)
    ask_x = random.random() < 0.5
    problem = (
        f"The parametrization $x(t) = {h} + {p}\\cos t$, $y(t) = {k} + {q}\\sin t$ traces an ellipse "
        f"$\\frac{{(x - {paren(h)})^2}}{{A}} + \\frac{{(y - {paren(k)})^2}}{{B}} = 1$. What is ${'A' if ask_x else 'B'}$?"
    )
    solution = f"{p * p if ask_x else q * q}"
    s = Steps()
    s.step("The cosine and sine coefficients are the semi-axes; the denominators are their squares.", f"{'A' if ask_x else 'B'} = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_classify_conic.variant("parameter_for_circle")
def _classify_parameter_circle():
    """For what k is kx^2 + cy^2 + ... = 0 a circle? The squared terms need equal coefficients."""
    c = random.randint(1, 9)
    D, E, F = random.randint(-12, 12), random.randint(-12, 12), random.randint(-20, -1)
    problem = (
        f"For what value of $k$ is $kx^2 + {c}y^2 {'+' if D >= 0 else '-'} {abs(D)}x {'+' if E >= 0 else '-'} {abs(E)}y "
        f"{'+' if F >= 0 else '-'} {abs(F)} = 0$ a circle?"
    )
    solution = f"{c}"
    s = Steps()
    s.step("A circle has equal coefficients on $x^2$ and $y^2$ (and no $xy$ term).", f"k = {c}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_vector_valued_function.variant("time_for_component")
def _vector_valued_time():
    """Reverse: when the x-component of p(t) = <at + b, ...> reaches a value."""
    a, b = _nonzero(-6, 6), random.randint(-9, 9)
    t = random.randint(0, 10)
    problem = (
        f"A particle's position is $p(t) = \\langle {a}t {'+' if b >= 0 else '-'} {abs(b)}, t^2 \\rangle$. At what time is its "
        f"$x$-coordinate ${a * t + b}$?"
    )
    solution = f"{t}"
    s = Steps()
    s.step("Set the first component equal and solve.", f"{a}t {'+' if b >= 0 else '-'} {abs(b)} = {a * t + b} \\Rightarrow t = {t}")
    s.answer(solution)
    return problem, solution, s.done()


# --- Matrices ------------------------------------------------------------------------------------

@mx.pc_inverse_matrix_entry.variant("singular_parameter")
def _inverse_singular():
    """For what k is the matrix not invertible?"""
    while True:
        a, b, c = _nonzero(-9, 9), _nonzero(-9, 9), _nonzero(-9, 9)
        if (b * c) % a == 0:
            break
    k = b * c // a
    problem = f"For what value of $k$ does ${_matrix_tex([[a, b], [c, 'k']])}$ have no inverse?"
    solution = f"{k}"
    s = Steps()
    s.step("No inverse when the determinant is $0$.", f"{a}k - ({b})({c}) = 0 \\Rightarrow k = {k}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_inverse_matrix_entry.variant("inverse_determinant")
def _inverse_determinant():
    """det(A^-1) = 1/det(A)."""
    while True:
        A = [[random.randint(-6, 6) for _ in range(2)] for _ in range(2)]
        d = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        if d:
            break
    problem = f"Let $A = {_matrix_tex(A)}$. What is $\\det(A^{{-1}})$? {_FRACTION_HINT}"
    solution = frac_from(Fraction(1, d))
    s = Steps()
    s.step("Find $\\det A$.", f"{A[0][0]}({A[1][1]}) - ({A[0][1]})({A[1][0]}) = {d}")
    s.step("The inverse's determinant is the reciprocal.", rf"\frac{{1}}{{{d}}}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_matrix_transform_point.variant("preimage")
def _matrix_preimage():
    """Reverse: which point does the matrix send to the given image?"""
    while True:
        A = [[random.randint(-4, 4) for _ in range(2)] for _ in range(2)]
        if A[0][0] * A[1][1] - A[0][1] * A[1][0] in (1, -1):
            break
    x, y = random.randint(-6, 6), random.randint(-6, 6)
    image = (A[0][0] * x + A[0][1] * y, A[1][0] * x + A[1][1] * y)
    problem = (
        f"The matrix $A = {_matrix_tex(A)}$ sends a point to $({image[0]}, {image[1]})$. What was the point? Format your answer as (x, y)."
    )
    solution = pair(x, y)
    s = Steps()
    s.step("Solve $A\\begin{bmatrix} x \\\\ y \\end{bmatrix}$ = the image (multiply by $A^{-1}$).", f"({x}, {y})")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_matrix_transform_point.variant("entry_from_mapping")
def _matrix_entry_from_mapping():
    """Reverse: a missing matrix entry from where it sends a point."""
    a, b, c, d = (random.randint(-5, 5) for _ in range(4))
    x, y = _nonzero(-5, 5), random.randint(-5, 5)
    image = (a * x + b * y, c * x + d * y)
    problem = (
        f"The matrix ${_matrix_tex([['k', b], [c, d]])}$ sends $({x}, {y})$ to $({image[0]}, {image[1]})$. What is $k$?"
    )
    solution = f"{a}"
    s = Steps()
    s.step("The first coordinate of the image is the first row times the point.", f"{x}k + {b}({y}) = {image[0]}")
    s.step("Solve for $k$.", f"k = {a}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_matrix_composition.variant("order_matters")
def _matrix_order_matters():
    """AB and BA usually send a point to different places."""
    A = [[random.randint(-3, 3) for _ in range(2)] for _ in range(2)]
    B = [[random.randint(-3, 3) for _ in range(2)] for _ in range(2)]
    mul = lambda P, v: (P[0][0] * v[0] + P[0][1] * v[1], P[1][0] * v[0] + P[1][1] * v[1])  # noqa: E731
    v = (random.randint(-4, 4), random.randint(-4, 4))
    ab = mul(A, mul(B, v))
    ba = mul(B, mul(A, v))
    problem = (
        f"Let $A = {_matrix_tex(A)}$ and $B = {_matrix_tex(B)}$, and $v = ({v[0]}, {v[1]})$. What is the x-coordinate of "
        "$ABv - BAv$?"
    )
    solution = f"{ab[0] - ba[0]}"
    s = Steps()
    s.step("Apply $B$ then $A$, and separately $A$ then $B$.", f"ABv = ({ab[0]}, {ab[1]}), \\quad BAv = ({ba[0]}, {ba[1]})")
    s.step("Subtract the x-coordinates.", f"{ab[0]} - {paren(ba[0])} = {ab[0] - ba[0]}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_markov_transition.variant("steady_state")
def _markov_steady_state():
    """The long-run count at A for a two-state Markov chain."""
    while True:
        p = random.choice(range(5, 50, 5))   # leave A
        q = random.choice(range(5, 50, 5))   # leave B
        total = random.choice(range(100, 2001, 100))
        at_a = Fraction(total * q, p + q)
        if at_a.denominator == 1:
            break
    problem = (
        f"Each week ${p}\\%$ of customers at Store A switch to Store B, and ${q}\\%$ of those at Store B switch to Store A. With "
        f"${total}$ customers in all, how many will be at Store A in the long run?"
    )
    solution = f"{at_a}"
    s = Steps()
    s.step("In the long run the flows balance: as many leave A as join it.", f"{num(Fraction(p, 100))}A = {num(Fraction(q, 100))}({total} - A)")
    s.step("Solve.", rf"A = \frac{{{total} \times {q}}}{{{p} + {q}}} = {at_a}")
    s.answer(solution)
    return problem, solution, s.done()


@mx.pc_markov_transition.variant("previous_week")
def _markov_previous_week():
    """Reverse: last week's count at A from this week's."""
    stay_a, stay_b = random.choice([60, 70, 80, 90]), random.choice([60, 70, 80, 90])
    a0, b0 = random.choice(range(100, 1001, 100)), random.choice(range(100, 1001, 100))
    a1 = (stay_a * a0 + (100 - stay_b) * b0) // 100
    total = a0 + b0
    problem = (
        f"Each week ${stay_a}\\%$ of customers at Store A stay and the rest switch to B; ${stay_b}\\%$ at B stay and the rest switch "
        f"to A. There are ${total}$ customers in all, and this week Store A has ${a1}$. How many did Store A have last week?"
    )
    solution = f"{a0}"
    s = Steps()
    s.step("Write this week's count in terms of last week's $a$.", f"{num(Fraction(stay_a, 100))}a + {num(Fraction(100 - stay_b, 100))}({total} - a) = {a1}")
    s.step("Solve.", f"a = {a0}")
    s.answer(solution)
    return problem, solution, s.done()
