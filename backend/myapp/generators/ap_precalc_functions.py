"""Solveki-local generators filling gaps in AP Precalculus Units 1-2 (polynomial, rational, exponential and logarithmic functions).

Every generator here takes no required arguments, is decorated with
``@register``, and returns ``(problem, solution, steps)``: LaTeX strings plus a
step-by-step explanation built with ``_steps.Steps``. Never seed ``random``
inside a generator.

Answers are kept typeable: integers, values rounded to at most three decimal
places, reduced ``"a/b"`` fractions, ``(x, y)`` pairs, ``a+bi`` complex
numbers, ASCII inequalities (``0 < x <= 32``), or a word from a fixed list
named in the problem.
"""
import math
import random
from fractions import Fraction

from ._registry import register
from ._format import num as _num, frac_from as _frac_from
from ._steps import Steps, paren, tex_frac

_ROUND_HINT = "Round your answer to the nearest thousandth."
_ROUND_IF_HINT = "Round your answer to the nearest thousandth if necessary."
_FRAC_HINT = "Give your answer as an integer or a fraction (such as 3/4)."


# ------------------------------ shared helpers ------------------------------

def _tex(value):
    """A number as LaTeX: an integer or a signed ``\\frac`` for a fraction."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return tex_frac(fr.numerator, fr.denominator)


def _coef_tex(k):
    """LaTeX coefficient in front of a symbol: ``''``, ``'-'``, ``'2'``, ``'\\frac{1}{2}'``."""
    k = Fraction(k)
    if k == 1:
        return ""
    if k == -1:
        return "-"
    return _tex(k)


def _signed(value):
    """`` + 3`` / `` - 3`` / ``""`` for appending a constant term."""
    if value == 0:
        return ""
    return f" + {value}" if value > 0 else f" - {-value}"


def _minus(var, value):
    """``var - value`` with the sign folded: ``x - 3``, ``x + 2``, ``x``."""
    if value == 0:
        return var
    return f"{var} - {value}" if value > 0 else f"{var} + {-value}"


def _join(pieces):
    """Join ``(sign, body)`` pieces into ``a - b + c`` (leading ``+`` dropped)."""
    if not pieces:
        return "0"
    first_sign, first_body = pieces[0]
    out = first_body if first_sign == "+" else f"-{first_body}"
    for sign, body in pieces[1:]:
        out += f" {sign} {body}"
    return out


def _poly(terms, var="x"):
    """Render ``(coefficient, exponent)`` pairs (highest first): ``3x^4 - 2x^2 + 5``."""
    pieces = []
    for coeff, exp in terms:
        if coeff == 0:
            continue
        mag = abs(coeff)
        if exp == 0:
            body = str(mag)
        else:
            token = var if exp == 1 else f"{var}^{exp}"
            body = token if mag == 1 else f"{mag}{token}"
        pieces.append(("-" if coeff < 0 else "+", body))
    return _join(pieces)


def _table(xs, ys, x_label="x", y_label="f(x)"):
    """A two-row LaTeX table of inputs and outputs."""
    head = " & ".join(_num(v) for v in xs)
    body = " & ".join(_num(v) for v in ys)
    return (rf"\begin{{array}}{{c|{'c' * len(xs)}}} {x_label} & {head} \\ "
            rf"\hline {y_label} & {body} \end{{array}}")


def _diffs(values):
    """Consecutive differences of a list."""
    return [b - a for a, b in zip(values, values[1:])]


def _row(values):
    """A comma-separated row of numbers for display math."""
    return r",\ ".join(_tex(v) for v in values)


def _complex(a, b):
    """``a + bi`` typeably: ``3-4i``, ``2+i``, ``-5i``, ``7``."""
    if b == 0:
        return str(a)
    mag = "" if abs(b) == 1 else str(abs(b))
    if a == 0:
        return f"{'-' if b < 0 else ''}{mag}i"
    return f"{a}{'+' if b > 0 else '-'}{mag}i"


def _and_list(items):
    """``A``, ``A and B``, ``A, B, and C``."""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _nonzero(lo, hi):
    return random.choice([v for v in range(lo, hi + 1) if v != 0])


# --------------------------- AP 1.1-1.5: polynomials ---------------------------

@register
def pc_change_in_tandem(min_second=1, max_second=4, min_start=-10, max_start=10, points=5):
    r"""Change in Tandem: Increasing and Concavity

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $x$: 0, 1, 2, 3, 4; $f(x)$: 2, 3, 6, 10, 16. Increasing or decreasing? Concave up or down? | increasing, concave up |

    The first differences share a sign (direction); the second differences
    share a sign (concavity) but needn't be constant.
    """
    increasing = random.random() < 0.5
    concave_up = random.random() < 0.5
    sign = 1 if increasing else -1
    curve = 1 if concave_up else -1
    seconds = [curve * random.randint(min_second, max_second) for _ in range(points - 2)]
    offsets = [0]
    for d in seconds:
        offsets.append(offsets[-1] + d)
    # Shift the first differences so every one is strictly of the right sign.
    base = 1 - min(sign * o for o in offsets) + random.randint(0, 3)
    firsts = [sign * base + o for o in offsets]
    h = random.choice([1, 2])
    x0 = random.randint(-3, 3)
    xs = [x0 + i * h for i in range(points)]
    ys = [random.randint(min_start, max_start)]
    for d in firsts:
        ys.append(ys[-1] + d)

    direction = "increasing" if increasing else "decreasing"
    concavity = "concave up" if concave_up else "concave down"
    problem = (
        f"The table shows values of a function $f$ at equally spaced inputs. "
        f"${_table(xs, ys)}$ On this interval, is $f$ increasing or decreasing, "
        f"and is its graph concave up or concave down? Answer in the form: "
        f"increasing, concave up."
    )
    solution = f"{direction}, {concavity}"

    s = Steps()
    s.step(f"Find the first differences, the change in $f(x)$ over each step of "
           f"${h}$ in $x$. They are all {'positive' if increasing else 'negative'}, "
           f"so $f$ is {direction}.", rf"\Delta f:\ {_row(firsts)}")
    s.step(f"Find the second differences, the change in the first differences. They "
           f"are all {'positive' if concave_up else 'negative'}, so the rate of change "
           f"is {'increasing' if concave_up else 'decreasing'} and the graph is {concavity}.",
           rf"\Delta^2 f:\ {_row(_diffs(firsts))}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_second_differences(min_a=-4, max_a=4, min_b=-6, max_b=6, min_c=-9, max_c=9):
    r"""Second Differences of a Quadratic

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $x$: 0, 1, 2, 3; $f(x)$: 1, 4, 11, 22 (quadratic). Find $f(4)$. | $37$ |
    | Same table, $f(x) = ax^2 + bx + c$. Find $a$. | $2$ |

    For a quadratic with input step ``h`` the second differences are the
    constant ``2ah^2``.
    """
    a = _nonzero(min_a, max_a)
    b = random.randint(min_b, max_b)
    c = random.randint(min_c, max_c)
    h = random.choice([1, 2])
    x0 = random.randint(-2, 2)
    xs = [x0 + i * h for i in range(4)]
    ys = [a * x * x + b * x + c for x in xs]
    firsts = _diffs(ys)
    second = firsts[1] - firsts[0]
    table = _table(xs, ys)

    s = Steps()
    s.step("Find the first differences between consecutive outputs.",
           rf"\Delta f:\ {_row(firsts)}")
    s.step(f"Find the second differences. For a quadratic they are constant: ${second}$.",
           rf"\Delta^2 f:\ {_row(_diffs(firsts))}")
    if random.random() < 0.5:
        x_next = x0 + 4 * h
        next_first = firsts[-1] + second
        answer = ys[-1] + next_first
        problem = (f"The table shows values of a quadratic function $f$. ${table}$ "
                   f"Find $f({x_next})$.")
        s.step(f"The next first difference is the last one plus the second difference.",
               f"{firsts[-1]} + {paren(second)} = {next_first}")
        s.step(f"Add it to $f({xs[-1]})$.",
               f"f({x_next}) = {ys[-1]} + {paren(next_first)} = {answer}")
    else:
        answer = a
        problem = (f"The table shows values of the quadratic function "
                   f"$f(x) = ax^2 + bx + c$. ${table}$ Find $a$.")
        s.step(f"With inputs ${h}$ apart, the second difference of a quadratic is "
               f"$2ah^2$. Solve for $a$.",
               rf"a = \frac{{{second}}}{{2({h})^2}} = {answer}")
    solution = f"${answer}$"
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_degree_from_differences(min_degree=1, max_degree=3, max_coeff=5):
    r"""Polynomial Degree from Finite Differences

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $x$: 0..5; $p(x)$: 1, 2, 9, 28, 65, 126. What is the degree of $p$? | $3$ |

    The ``n``th differences of a degree-``n`` polynomial over consecutive
    integers are constant and nonzero.
    """
    degree = random.randint(min_degree, max_degree)
    coeffs = [_nonzero(-3, 3)] + [random.randint(-max_coeff, max_coeff) for _ in range(degree)]
    x0 = random.randint(-2, 1)
    xs = list(range(x0, x0 + 6))
    ys = [sum(c * x ** (degree - i) for i, c in enumerate(coeffs)) for x in xs]
    problem = (f"The table shows values of a polynomial function $p$ at consecutive "
               f"integers. ${_table(xs, ys, y_label='p(x)')}$ What is the degree of $p$?")
    solution = f"${degree}$"

    s = Steps()
    row = ys
    names = {1: "first", 2: "second", 3: "third"}
    for k in range(1, degree + 1):
        row = _diffs(row)
        text = f"Find the {names[k]} differences."
        if k == degree:
            text += (f" They are constant, and a polynomial of degree $n$ has constant "
                     f"$n$th differences, so the degree is ${degree}$.")
        else:
            text += " They are not constant yet."
        s.step(text, rf"\Delta^{{{k}}} p:\ {_row(row)}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_complex_conjugate_zeros(max_real=6, max_part=6):
    r"""Complex Conjugate Zeros

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Degree 3, real coefficients, zeros $2$ and $3-4i$. Remaining zero? | 3+4i |
    | Real coefficients, zeros $1$ and $2+i$. Minimum degree? | $3$ |

    Non-real zeros of a real-coefficient polynomial come in conjugate pairs.
    """
    reals_pool = list(range(-max_real, max_real + 1))
    theorem = ("By the Complex Conjugate Root Theorem, the non-real zeros of a "
               "polynomial with real coefficients come in conjugate pairs "
               "$a + bi$ and $a - bi$.")
    s = Steps()
    s.step(theorem)
    if random.random() < 0.5:
        degree = random.choice([3, 4])
        reals = sorted(random.sample(reals_pool, degree - 2))
        a = _nonzero(-max_part, max_part)
        b = random.choice([v for v in range(-max_part, max_part + 1) if abs(v) >= 2])
        given = [str(r) for r in reals] + [_complex(a, b)]
        listing = _and_list([f"$x = {z}$" for z in given])
        problem = (f"A polynomial $p(x)$ of degree ${degree}$ with real coefficients has "
                   f"zeros at {listing}. What is its remaining zero? Write it in the "
                   f"form a+bi (for example, 2-3i).")
        solution = _complex(a, -b)
        s.step(f"So the conjugate of ${_complex(a, b)}$ is also a zero.",
               rf"\overline{{{_complex(a, b)}}} = {solution}")
        s.step(f"That gives ${degree}$ zeros, as many as the degree, so there are no others.",
               ",\\ ".join(given + [solution]))
    else:
        reals = sorted(random.sample(reals_pool, random.randint(1, 2)))
        count = random.randint(1, 2)
        pairs = []
        while len(pairs) < count:
            z = (random.randint(-max_part, max_part), _nonzero(-max_part, max_part))
            if any(z[0] == w[0] and abs(z[1]) == abs(w[1]) for w in pairs):
                continue
            pairs.append(z)
        given_nonreal = list(pairs)
        if random.random() < 1 / 3:
            given_nonreal.append((pairs[0][0], -pairs[0][1]))
        answer = len(reals) + 2 * len(pairs)
        listing = _and_list([f"$x = {r}$" for r in reals]
                            + [f"$x = {_complex(a, b)}$" for a, b in given_nonreal])
        problem = (f"A polynomial $p(x)$ with real coefficients has zeros at {listing}. "
                   f"What is the smallest possible degree of $p$?")
        solution = f"${answer}$"
        pair_tex = r",\quad ".join(f"{_complex(a, b)},\\ {_complex(a, -b)}" for a, b in pairs)
        text = "So each non-real zero brings its conjugate along."
        if len(given_nonreal) > len(pairs):
            text += (f" (${_complex(*pairs[0])}$ and ${_complex(pairs[0][0], -pairs[0][1])}$ "
                     f"are already a pair.)")
        s.step(text, pair_tex)
        s.step(f"Count the zeros: ${len(reals)}$ real plus $2$ for each of the "
               f"${len(pairs)}$ conjugate pair{'s' if len(pairs) > 1 else ''}.",
               f"{len(reals)} + 2({len(pairs)}) = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


_EVENS, _ODDS = [0, 2, 4, 6], [1, 3, 5]


def _random_terms(kind, count, max_coeff):
    """Terms for an even / odd / neither polynomial with ``count`` terms."""
    if kind == "even":
        exps = random.sample(_EVENS, count)
    elif kind == "odd":
        exps = random.sample(_ODDS, count)
    else:
        exps = [random.choice(_EVENS), random.choice(_ODDS)]
        exps += random.sample([e for e in _EVENS + _ODDS if e not in exps], count - 2)
    return [(_nonzero(-max_coeff, max_coeff), e) for e in sorted(exps, reverse=True)]


def _sub_neg_x(terms):
    """The polynomial with ``(-x)`` substituted, before simplifying."""
    pieces = []
    for coeff, exp in terms:
        mag = abs(coeff)
        if exp == 0:
            body = str(mag)
        else:
            power = "(-x)" if exp == 1 else f"(-x)^{exp}"
            body = power if mag == 1 else f"{mag}{power}"
        pieces.append(("-" if coeff < 0 else "+", body))
    return _join(pieces)


def _flip(terms):
    """Terms of ``p(-x)``."""
    return [(c * (-1) ** e, e) for c, e in terms]


def _neg(terms):
    return [(-c, e) for c, e in terms]


@register
def pc_even_odd_function(max_coeff=6):
    r"""Even and Odd Functions (Symmetry)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Is $f(x) = 3x^4 - 2x^2 + 5$ even, odd, or neither? | even |
    | Is $f(x) = \frac{x^3}{x^2 + 1}$ even, odd, or neither? | odd |
    """
    kind = random.choice(["even", "odd", "neither"])
    if random.random() < 2 / 3:
        terms = _random_terms(kind, random.randint(2, 3), max_coeff)
        expr = _poly(terms)
        sub = _sub_neg_x(terms)
        flipped = _poly(_flip(terms))
        negated = _poly(_neg(terms))
    else:
        # Rational over an even denominator x^2 + c or x^4 + c (never zero,
        # never cancels), so the numerator alone sets the symmetry.
        bot = [(1, random.choice([2, 4])), (random.randint(1, 5), 0)]
        top = _random_terms(kind, 2 if kind == "neither" else random.randint(1, 2), max_coeff)
        den = _poly(bot)
        expr = rf"\frac{{{_poly(top)}}}{{{den}}}"
        sub = rf"\frac{{{_sub_neg_x(top)}}}{{{_sub_neg_x(bot)}}}"
        flipped = rf"\frac{{{_poly(_flip(top))}}}{{{den}}}"
        negated = rf"\frac{{{_poly(_neg(top))}}}{{{den}}}"
    problem = (f"Is the function $f(x) = {expr}$ even, odd, or neither? "
               f"Answer even, odd, or neither.")
    solution = kind

    s = Steps()
    s.step("A function is even if $f(-x) = f(x)$ for every $x$, and odd if "
           "$f(-x) = -f(x)$. Substitute $-x$ for $x$.", f"f(-x) = {sub}")
    s.step("Simplify: an even power of $-x$ is positive and an odd power is negative.",
           f"f(-x) = {flipped}")
    if kind == "even":
        s.step("This is exactly $f(x)$, so $f$ is even.", "f(-x) = f(x)")
    elif kind == "odd":
        s.step("Every term changed sign: this is the opposite of $f(x)$, so $f$ is odd.",
               rf"f(-x) = -\left({expr}\right) = -f(x)")
    else:
        s.step(f"This is neither $f(x)$ nor $-f(x) = {negated}$, so $f$ is neither "
               f"even nor odd.")
    s.answer(solution)
    return problem, solution, s.done()


# --------------------------- AP 1.12-1.14: modeling ---------------------------

_SCALES = [1, 2, 3, -1, -2, Fraction(1, 2), Fraction(-1, 2)]
_STRETCHES = [1, 2, 3, -1, -2, Fraction(1, 2), Fraction(1, 3)]


@register
def pc_function_transformation(min_shift=-5, max_shift=5, min_point=-6, max_point=6):
    r"""Transform a Point on a Function's Graph

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $(4, 3)$ is on $y = f(x)$. Find the point on $g(x) = 2f(2(x - 1)) + 5$. | (3, 11) |

    ``(x0, y0)`` maps to ``(x0/b + h, a*y0 + k)`` under ``a f(b(x - h)) + k``.
    """
    while True:
        a, b = random.choice(_SCALES), random.choice(_STRETCHES)
        h, k = random.randint(min_shift, max_shift), random.randint(min_shift, max_shift)
        if (a, b, h, k) != (1, 1, 0, 0):
            break
    x0, y0 = random.randint(min_point, max_point), random.randint(min_point, max_point)
    x_new = Fraction(x0) / b + h
    y_new = Fraction(a) * y0 + k

    shifted = _minus("x", h)
    if b == 1:
        inner = shifted
    elif h == 0:
        inner = f"{_coef_tex(b)}x"
    else:
        inner = f"{_coef_tex(b)}({shifted})"
    g = f"{_coef_tex(a)}f({inner}){_signed(k)}"
    problem = (f"The point $({x0}, {y0})$ is on the graph of $y = f(x)$. Find the "
               f"corresponding point on the graph of $g(x) = {g}$. Format your answer "
               f"as (x, y), writing any non-integer as a fraction a/b.")
    solution = f"({_frac_from(x_new)}, {_frac_from(y_new)})"

    s = Steps()
    how = []
    if b != 1:
        how.append(f"divide by ${_tex(b)}$")
    if h != 0:
        how.append(f"{'add' if h > 0 else 'subtract'} ${abs(h)}$")
    how_text = f" ({_and_list(how)})" if how else ""
    s.step(f"Since $f({x0}) = {y0}$, find the $x$ that makes the input of $f$ equal "
           f"${x0}${how_text}.", rf"{inner} = {x0} \implies x = {_tex(x_new)}")
    scaled = str(y0) if a == 1 else f"{_coef_tex(a)}({y0})"
    s.step(f"At that $x$, $f$ outputs ${y0}$, so $g$ multiplies it by ${_tex(a)}$"
           + (f" and adds ${k}$." if k > 0 else f" and subtracts ${-k}$." if k < 0 else "."),
           rf"g\left({_tex(x_new)}\right) = {scaled}{_signed(k)} = {_tex(y_new)}")
    s.answer(solution)
    return problem, solution, s.done()


def _model_values(kind):
    """Five outputs at x = 0..4 for a linear, quadratic or exponential model."""
    xs = list(range(5))
    if kind == "linear":
        m, b = _nonzero(-8, 8), random.randint(-10, 20)
        return [m * x + b for x in xs]
    if kind == "quadratic":
        a, b, c = _nonzero(-3, 3), random.randint(-6, 6), random.randint(-5, 15)
        return [a * x * x + b * x + c for x in xs]
    r = Fraction(random.choice([2, 3, Fraction(1, 2), Fraction(1, 3), Fraction(3, 2)]))
    if r.denominator == 1:
        start = random.randint(1, 6 if r == 2 else 4)
    else:
        # Scale by denominator^4 so all five outputs are integers.
        start = random.randint(1, 2 if r.denominator == 3 else 4) * r.denominator ** 4
    return [int(start * Fraction(r) ** x) for x in xs]


@register
def pc_identify_model():
    r"""Identify a Linear, Quadratic, or Exponential Model

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $x$: 0..4; $y$: 3, 6, 12, 24, 48. Linear, quadratic, or exponential? | exponential |

    Constant first differences: linear; constant second differences:
    quadratic; constant ratios: exponential.
    """
    kind = random.choice(["linear", "quadratic", "exponential"])
    ys = _model_values(kind)
    xs = list(range(5))
    problem = (f"The table shows data that fit one model exactly. "
               f"${_table(xs, ys, y_label='y')}$ Is the model linear, quadratic, or "
               f"exponential? Answer linear, quadratic, or exponential.")
    solution = kind
    firsts = _diffs(ys)
    seconds = _diffs(firsts)

    s = Steps()
    if kind == "linear":
        s.step(f"Find the first differences. They are all ${firsts[0]}$, a constant "
               f"rate of change, so the model is linear.", rf"\Delta y:\ {_row(firsts)}")
    else:
        s.step("Find the first differences. They are not constant, so the model is "
               "not linear.", rf"\Delta y:\ {_row(firsts)}")
        if kind == "quadratic":
            s.step(f"Find the second differences. They are all ${seconds[0]}$, so the "
                   f"model is quadratic.", rf"\Delta^2 y:\ {_row(seconds)}")
        else:
            s.step("Find the second differences. They are not constant either, so the "
                   "model is not quadratic.", rf"\Delta^2 y:\ {_row(seconds)}")
            ratios = [Fraction(b, a) for a, b in zip(ys, ys[1:])]
            s.step(f"Find the ratios of consecutive outputs. They are all "
                   f"${_tex(ratios[0])}$, a constant factor, so the model is exponential.",
                   rf"\frac{{y_{{n+1}}}}{{y_n}}:\ {_row(ratios)}")
    s.answer(solution)
    return problem, solution, s.done()


# (description, function letter, input letter, sign of a: -1 concave down, 0 any)
_QUAD_CONTEXTS = [
    ("The height of a ball, in feet, $t$ seconds after it is thrown upward", "h", "t", -1),
    ("The number of visitors to a museum exhibit, in hundreds, $t$ weeks after it opens",
     "V", "t", -1),
    ("A company's monthly profit, in thousands of dollars, $x$ months after a product "
     "launch", "P", "x", 0),
    ("The cost, in dollars, of producing $x$ hundred items", "C", "x", 1),
]


@register
def pc_quadratic_model_predict(max_input=8):
    r"""Predict with a Quadratic Model

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Height $h(t)$: $h(0) = 5$, $h(1) = 21$, $h(2) = 29$ (quadratic). Predict $h(3)$. | $29$ |

    Fit ``y = at^2 + bt + c`` through three data points, then evaluate it at
    a fourth input.
    """
    context, f, v, sign = random.choice(_QUAD_CONTEXTS)
    inputs = sorted(random.sample(range(0, max_input + 1), 3))
    target = random.choice([t for t in range(0, max_input + 2) if t not in inputs])
    while True:
        a = random.randint(1, 3) * (sign or random.choice([1, -1]))
        b = random.randint(-12, 12)
        c = random.randint(0, 40)
        values = [a * t * t + b * t + c for t in inputs + [target]]
        if min(values) >= 1:
            break
    ys, answer = values[:3], values[3]
    problem = (f"{context} is modeled by a quadratic function ${f}({v})$. The table "
               f"shows three data values. ${_table(inputs, ys, v, f'{f}({v})')}$ Use the "
               f"model to predict ${f}({target})$.")
    solution = f"${answer}$"

    model = _poly([(a, 2), (b, 1), (c, 0)], v)
    s = Steps()
    s.formula("A quadratic model", rf"{f}({v}) = a{v}^2 + b{v} + c")
    s.substitute(r",\quad ".join(f"{y} = a({t})^2 + b({t}) + c" for t, y in zip(inputs, ys)),
                 text="Substitute each data point to get three equations.")
    s.step("Subtract the equations in pairs to eliminate $c$, solve the two resulting "
           "equations for $a$ and $b$, then back-substitute for $c$.",
           rf"a = {a},\quad b = {b},\quad c = {c}")
    s.step(f"Evaluate the model at ${v} = {target}$.",
           rf"{f}({target}) = {a}({target})^2 + {paren(b)}({target}) + {c} = {answer}")
    s.answer(solution)
    return problem, solution, s.done()


# ------------------------ AP 2.2-2.6: exponential models ------------------------

_EXP_BASES = [2, 3, 4, 5, Fraction(1, 2), Fraction(1, 3), Fraction(3, 2)]


@register
def pc_exponential_from_two_points(max_coeff=9):
    r"""Exponential Function from Two Points

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $f(x) = ab^x$ passes through $(1, 6)$ and $(3, 54)$. Find $b$. | $3$ |

    Divide the two equations to eliminate ``a`` and find ``b``, then
    back-substitute.
    """
    b = Fraction(random.choice(_EXP_BASES))
    max_x = 3 if b >= 4 else 4
    if b.denominator == 1:
        a = random.randint(1, max_coeff)
    else:
        a = random.randint(1, 2 if b.denominator == 3 else 3) * b.denominator ** max_x
    x1, x2 = sorted(random.sample(range(0, max_x + 1), 2))
    y1, y2 = int(a * b ** x1), int(a * b ** x2)
    n = x2 - x1
    ratio = Fraction(y2, y1)
    mode = random.choice(["a", "b", "value"])
    intro = (f"The exponential function $f(x) = ab^x$ passes through the points "
             f"$({x1}, {y1})$ and $({x2}, {y2})$.")

    s = Steps()
    power = f"b^{{{n}}}" if n > 1 else "b"
    s.step("Divide the two equations to eliminate $a$.",
           rf"\frac{{{y2}}}{{{y1}}} = \frac{{ab^{{{x2}}}}}{{ab^{{{x1}}}}} \implies "
           rf"{power} = {_tex(ratio)}")
    if n > 1:
        root = "square" if n == 2 else "cube" if n == 3 else f"{n}th"
        index = "" if n == 2 else f"[{n}]"
        s.step(f"Take the {root} root of both sides.",
               rf"b = \sqrt{index}{{{_tex(ratio)}}} = {_tex(b)}")
    if mode == "b":
        problem = f"{intro} Find $b$. {_FRAC_HINT}"
        solution = _frac_from(b)
    else:
        s.step(f"Substitute $b$ into $f({x1}) = {y1}$ to find $a$.",
               rf"{y1} = a\left({_tex(b)}\right)^{{{x1}}} \implies a = {a}")
        if mode == "a":
            problem = f"{intro} Find $a$."
            solution = f"${a}$"
        else:
            x3 = random.choice([x for x in range(0, max_x + 1) if x not in (x1, x2)])
            value = int(a * b ** x3)
            problem = f"{intro} Find $f({x3})$."
            solution = f"${value}$"
            s.step(f"Evaluate $f({x3})$.",
                   rf"f({x3}) = {a}\left({_tex(b)}\right)^{{{x3}}} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


# (B, m, root): B^(x/m) = root^x
_ROOT_PAIRS = [(4, 2, 2), (9, 2, 3), (16, 2, 4), (25, 2, 5), (36, 2, 6), (49, 2, 7),
               (8, 3, 2), (27, 3, 3), (64, 3, 4), (16, 4, 2), (81, 4, 3)]


@register
def pc_rewrite_exponential(min_coeff=2, max_coeff=9):
    r"""Rewrite an Exponential Expression

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Rewrite $3 \cdot 2^{x+2}$ as $a \cdot 2^x$. What is $a$? | $12$ |
    | $5 \cdot 9^{x/2} = 5 \cdot b^x$. What is $b$? | $3$ |
    | Rewrite $2^{3x}$ as $c^x$. What is $c$? | $8$ |
    """
    mode = random.choice(["shift", "root", "power"])
    c = random.randint(min_coeff, max_coeff)
    s = Steps()
    if mode == "shift":
        b = random.choice([2, 3, 4, 5])
        n = random.choice([k for k in (-2, -1, 1, 2, 3) if b ** abs(k) <= 64])
        value = c * Fraction(b) ** n
        exponent = _minus("x", -n)
        problem = (rf"Rewrite ${c} \cdot {b}^{{{exponent}}}$ in the form "
                   rf"$a \cdot {b}^{{x}}$. What is $a$?")
        if n < 0:
            problem += f" {_FRAC_HINT}"
        s.formula("The product rule for exponents", r"b^{m + n} = b^m \cdot b^n")
        s.step(f"Split off the constant power ${b}^{{{n}}}$.",
               rf"{c} \cdot {b}^{{{exponent}}} = {c} \cdot {b}^{{{n}}} \cdot {b}^{{x}}")
        s.step("Multiply the constants to get $a$.",
               rf"a = {c} \cdot {_tex(Fraction(b) ** n)} = {_tex(value)}")
    elif mode == "root":
        big, m, value = random.choice(_ROOT_PAIRS)
        problem = (rf"The expression ${c} \cdot {big}^{{\frac{{x}}{{{m}}}}}$ can be "
                   rf"written as ${c} \cdot b^{{x}}$. What is $b$?")
        s.formula("The power rule for exponents", r"\left(b^m\right)^n = b^{mn}")
        s.step(rf"Write the exponent $\frac{{x}}{{{m}}}$ as $\frac{{1}}{{{m}}} \cdot x$.",
               rf"{big}^{{\frac{{x}}{{{m}}}}} = \left({big}^{{\frac{{1}}{{{m}}}}}\right)^{{x}}")
        s.step(f"Evaluate the {'square' if m == 2 else 'cube' if m == 3 else str(m) + 'th'} "
               f"root.", rf"{big}^{{\frac{{1}}{{{m}}}}} = \sqrt[{m}]{{{big}}} = {value}")
    else:
        b = random.choice([2, 3, 4, 5])
        k = random.choice([j for j in (-2, -1, 2, 3) if b ** abs(j) <= 125])
        value = Fraction(b) ** k
        problem = (rf"Rewrite ${b}^{{{_coef_tex(k)}x}}$ in the form $c^{{x}}$. "
                   rf"What is $c$?")
        if k < 0:
            problem += f" {_FRAC_HINT}"
        s.formula("The power rule for exponents", r"b^{mn} = \left(b^m\right)^n")
        s.step(f"Group ${k}$ with the base.",
               rf"{b}^{{{_coef_tex(k)}x}} = \left({b}^{{{k}}}\right)^{{x}}")
        s.step(f"Evaluate ${b}^{{{k}}}$.", f"{b}^{{{k}}} = {_tex(value)}")
    solution = _frac_from(value)
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_residual(min_x=1, max_x=10):
    r"""Residual of a Regression Model

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Model $\hat{y} = 2.5x + 12$; data point $(4, 25)$. Find the residual. | $3$ |

    ``residual = actual - predicted``.
    """
    s = Steps()
    s.step("The residual is the actual value minus the predicted value.",
           r"\text{residual} = y - \hat{y}")
    if random.random() < 0.5:
        m = Fraction(random.randint(5, 50) * random.choice([1, -1]), 10)
        b0 = random.randint(5, 40)
        x = random.randint(min_x, max_x)
        predicted = m * x + b0
        actual = predicted + Fraction(_nonzero(-50, 50), 10)
        m_tex = "" if m == 1 else "-" if m == -1 else _num(m)
        model = rf"\hat{{y}} = {m_tex}x + {b0}"
        hint = "If your answer is not an integer, write it as a decimal."
        s.substitute(rf"\hat{{y}} = {_num(m)}({x}) + {b0} = {_num(predicted)}",
                     text=f"Find the predicted value at $x = {x}$.")
    else:
        a = random.randint(50, 500)
        rate = Fraction(random.choice(list(range(102, 126)) + list(range(80, 96))), 100)
        x = random.randint(1, 6)
        predicted = a * rate ** x
        actual = int(predicted) + random.randint(-15, 15)
        model = rf"\hat{{y}} = {a}({_num(rate)})^{{x}}"
        hint = _ROUND_HINT
        s.substitute(rf"\hat{{y}} = {a}({_num(rate)})^{{{x}}} \approx {_num(predicted)}",
                     text=f"Find the predicted value at $x = {x}$.")
    residual = actual - predicted
    problem = (f"A model for a data set is ${model}$. The data set includes the point "
               f"$({x}, {_num(actual)})$. Find the residual for this point. {hint}")
    solution = f"${_num(residual)}$"
    if residual > 0:
        meaning = " It is positive, so the model underestimates this point."
    elif residual < 0:
        meaning = " It is negative, so the model overestimates this point."
    else:
        meaning = " The model predicts this point exactly."
    equals = "=" if (residual * 1000).denominator == 1 else r"\approx"
    s.step(f"Subtract the predicted value from the actual value ${_num(actual)}$.{meaning}",
           rf"{_num(actual)} - {paren(_num(predicted))} {equals} {_num(residual)}")
    s.answer(solution)
    return problem, solution, s.done()


# ------------------------ AP 2.10-2.15: logarithms ------------------------

def _max_power(base, limit=125):
    k = 0
    while base ** (k + 1) <= limit:
        k += 1
    return k


@register
def pc_inverse_exponential(max_coeff=5, min_shift=-10, max_shift=10):
    r"""Evaluate the Inverse of an Exponential Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Let $f(x) = 3 \cdot 2^x + 1$. Find $f^{-1}(25)$. | $3$ |

    The inverse of ``a*b^x + k`` is ``log_b((x - k)/a)``.
    """
    b = random.choice([2, 3, 4, 5, 10])
    a = random.randint(1, max_coeff)
    k = random.randint(min_shift, max_shift)
    t = random.randint(0, _max_power(b))
    v = a * b ** t + k
    a_part = "" if a == 1 else rf"{a} \cdot "
    problem = rf"Let $f(x) = {a_part}{b}^{{x}}{_signed(k)}$. Find $f^{{-1}}({v})$."
    solution = f"${t}$"

    s = Steps()
    s.step(f"$f^{{-1}}({v})$ is the input $x$ that gives $f(x) = {v}$.",
           f"{a_part}{b}^{{x}}{_signed(k)} = {v}")
    how = []
    if k:
        how.append(f"{'subtract' if k > 0 else 'add'} ${abs(k)}$")
    if a != 1:
        how.append(f"divide by ${a}$")
    s.step(f"Isolate the exponential{' (' + _and_list(how) + ')' if how else ''}.",
           f"{b}^{{x}} = {b ** t}")
    inside = _minus("x", k)
    inverse = (rf"\log_{{{b}}}\left(\frac{{{inside}}}{{{a}}}\right)" if a != 1
               else rf"\log_{{{b}}}({inside})")
    s.step(rf"An exponential is undone by a logarithm with the same base (in general "
           rf"$f^{{-1}}(x) = {inverse}$), so take $\log_{{{b}}}$ of both sides.",
           rf"x = \log_{{{b}}}({b ** t}) = {t}")
    s.answer(solution)
    return problem, solution, s.done()


def _log_tex(b, arg):
    return rf"\log_{{{b}}}({arg})"


@register
def pc_log_function_features(min_shift=-6, max_shift=6):
    r"""Features of a Logarithmic Function

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $f(x) = 2\log_{3}(x - 4) + 1$. Vertical asymptote? | x = 4 |
    | Same $f$. Domain? | x > 4 |
    | $f(x) = \log_{2}(x - 1) - 3$. $x$-intercept? | $9$ |
    """
    b = random.choice([2, 3, 5, 10])
    a = random.choice([1, 2, 3, -1, -2])
    h = random.randint(min_shift, max_shift)
    mode = random.choice(["asymptote", "domain", "intercept"])
    if mode == "intercept":
        n = random.choice([-1, 0, 1, 2])
        k = -a * n
    else:
        k = random.randint(-5, 5)
    arg = _minus("x", h)
    f = f"{_coef_tex(a)}{_log_tex(b, arg)}{_signed(k)}"
    intro = f"Let $f(x) = {f}$."

    s = Steps()
    if mode in ("asymptote", "domain"):
        s.step(rf"A logarithm is defined only for positive arguments, and "
               rf"$\log_{{{b}}}(u)$ falls without bound as $u$ approaches $0$ from the right.")
        if mode == "asymptote":
            problem = (f"{intro} Find the vertical asymptote of the graph of $f$. Answer "
                       f"in the form x = c.")
            solution = f"x = {h}"
            s.step("The vertical asymptote is where the argument equals $0$.",
                   rf"{arg} = 0 \implies x = {h}")
        else:
            problem = (f"{intro} Find the domain of $f$. Write it as an inequality, "
                       f"such as x > 2.")
            solution = f"x > {h}"
            s.step("Require the argument to be positive.", rf"{arg} > 0 \implies x > {h}")
    else:
        root = h + Fraction(b) ** n
        problem = (f"{intro} Find the $x$-coordinate of the $x$-intercept of the graph "
                   f"of $f$. {_FRAC_HINT}")
        solution = _frac_from(root)
        s.step("At the $x$-intercept, $f(x) = 0$.", f"{f} = 0")
        if a != 1 or k:
            s.step("Isolate the logarithm.", f"{_log_tex(b, arg)} = {n}")
        s.step(f"Rewrite in exponential form: $\\log_{{{b}}}(u) = {n}$ means "
               f"$u = {b}^{{{n}}}$.", f"{arg} = {b}^{{{n}}} = {_tex(Fraction(b) ** n)}")
        if h:
            s.step(f"{'Add' if h > 0 else 'Subtract'} ${abs(h)}$.", f"x = {_tex(root)}")
    s.answer(solution)
    return problem, solution, s.done()


# (base, exponent) with base^exponent at most 100.
_LOG_POWERS = [(2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 2), (3, 3), (3, 4),
               (5, 2), (10, 1), (10, 2), (4, 2), (4, 3)]


def _factor_pairs(n):
    return [(r, n // r) for r in range(1, n + 1) if n % r == 0 and r != n // r]


@register
def pc_solve_log_equation(max_shift=9):
    r"""Solve a Logarithmic Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $\log_{2}(x + 3) = 4$ for $x$. | $13$ |
    | Solve $\log_{2}(x) + \log_{2}(x + 2) = 3$ for $x$. | $2$ |
    | Solve $\log_{3}(x + 8) - \log_{3}(x) = 2$ for $x$. | $1$ |

    The product form produces an extraneous negative root, rejected in the
    steps.
    """
    mode = random.choice(["single", "product", "quotient"])
    s = Steps()
    if mode == "single":
        b, n = random.choice(_LOG_POWERS)
        big = b ** n
        c = _nonzero(-max_shift, max_shift)
        x = big - c
        arg = _minus("x", -c)
        problem = rf"Solve ${_log_tex(b, arg)} = {n}$ for $x$."
        s.step(rf"Rewrite in exponential form: $\log_{{{b}}}(u) = {n}$ means $u = {b}^{{{n}}}$.",
               f"{arg} = {b}^{{{n}}} = {big}")
        s.step(f"{'Subtract' if c > 0 else 'Add'} ${abs(c)}$, then check that the "
               f"argument ${big}$ is positive.", f"x = {x}")
    elif mode == "product":
        b, n = random.choice([(b, n) for b, n in _LOG_POWERS if _factor_pairs(b ** n)])
        big = b ** n
        r, other = random.choice(_factor_pairs(big))
        c = other - r  # x(x + c) = big has roots r and -other
        x = r
        arg = _minus("x", -c)
        problem = rf"Solve ${_log_tex(b, 'x')} + {_log_tex(b, arg)} = {n}$ for $x$."
        s.formula("The product rule for logarithms", r"\log_b M + \log_b N = \log_b (MN)")
        s.step("Combine the logs, then rewrite in exponential form.",
               rf"x({arg}) = {b}^{{{n}}} = {big}")
        s.step("Expand into a quadratic and factor.",
               rf"{_poly([(1, 2), (c, 1), (-big, 0)])} = 0 \implies "
               rf"(x - {r})(x + {other}) = 0")
        s.step(rf"So $x = {r}$ or $x = -{other}$. But $x = -{other}$ makes "
               rf"$\log_{{{b}}}(x)$ undefined, so it is extraneous.", f"x = {r}")
    else:
        b, n = random.choice([(b, n) for b, n in _LOG_POWERS if b ** n <= 25])
        big = b ** n
        x = random.randint(1, 6)
        c = x * (big - 1)
        problem = (rf"Solve ${_log_tex(b, _minus('x', -c))} - {_log_tex(b, 'x')} = {n}$ "
                   rf"for $x$.")
        s.formula("The quotient rule for logarithms",
                  r"\log_b M - \log_b N = \log_b \frac{M}{N}")
        s.step("Combine the logs, then rewrite in exponential form.",
               rf"\frac{{x + {c}}}{{x}} = {b}^{{{n}}} = {big}")
        s.step(f"Multiply by $x$ and solve; $x = {x}$ is positive, so both logs are defined.",
               rf"x + {c} = {big}x \implies {c} = {big - 1}x \implies x = {x}")
    solution = f"${x}$"
    s.answer(solution)
    return problem, solution, s.done()


_REL_TEX = {">": ">", ">=": r"\ge", "<": "<", "<=": r"\le"}
_FLIP = {">": "<", ">=": "<=", "<": ">", "<=": ">="}


@register
def pc_exp_log_inequality(max_shift=5):
    r"""Exponential and Logarithmic Inequalities

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve $3^{x - 1} > 27$. | x > 4 |
    | Solve $\log_{2}(x) \le 5$. | 0 < x <= 32 |

    Exponentials and logs with base above 1 are increasing, so the inequality
    keeps its direction; a log inequality also carries its domain.
    """
    rel = random.choice(list(_REL_TEX))
    fmt = ("Write your answer as an inequality in x using >, <, >=, or <=, such as "
           "x > 4 or 0 < x <= 32.")
    s = Steps()
    mode = random.choice(["exp", "exp", "log", "log", "recip"])
    if mode in ("exp", "recip"):
        b = random.choice([2, 3, 5])
        n = random.randint(1, _max_power(b))
        big = b ** n
        if mode == "exp":
            c = random.randint(-max_shift, max_shift)
            exponent = _minus("x", c)
            problem = rf"Solve ${b}^{{{exponent}}} {_REL_TEX[rel]} {big}$. {fmt}"
            s.step(f"Write ${big}$ as a power of ${b}$.",
                   rf"{b}^{{{exponent}}} {_REL_TEX[rel]} {b}^{{{n}}}")
            s.step(f"Since ${b} > 1$, ${b}^{{x}}$ is increasing, so the exponents compare "
                   f"the same way.", rf"{exponent} {_REL_TEX[rel]} {n}")
            solution = f"x {rel} {n + c}"
            if c:
                s.step(f"{'Add' if c > 0 else 'Subtract'} ${abs(c)}$.",
                       rf"x {_REL_TEX[rel]} {n + c}")
        else:
            problem = (rf"Solve $\left(\frac{{1}}{{{b}}}\right)^{{x}} {_REL_TEX[rel]} "
                       rf"{big}$. {fmt}")
            s.step(f"Write both sides as powers of ${b}$.",
                   rf"{b}^{{-x}} {_REL_TEX[rel]} {b}^{{{n}}}")
            s.step(f"Since ${b} > 1$, ${b}^{{x}}$ is increasing, so the exponents compare "
                   f"the same way.", rf"-x {_REL_TEX[rel]} {n}")
            solution = f"x {_FLIP[rel]} {-n}"
            s.step("Multiply by $-1$, which reverses the inequality.",
                   rf"x {_REL_TEX[_FLIP[rel]]} {-n}")
    else:
        b, n = random.choice(_LOG_POWERS)
        big = b ** n
        c = random.randint(-max_shift, max_shift)
        arg = _minus("x", c)
        problem = rf"Solve ${_log_tex(b, arg)} {_REL_TEX[rel]} {n}$. {fmt}"
        s.step("The argument of a logarithm must be positive.", rf"{arg} > 0 \implies x > {c}")
        s.step(rf"Since $\log_{{{b}}}$ is increasing, rewrite in exponential form "
               rf"keeping the direction.", rf"{arg} {_REL_TEX[rel]} {b}^{{{n}}} = {big}")
        if rel in (">", ">="):
            solution = f"x {rel} {c + big}"
            s.step(f"Solve for $x$. Every such $x$ is already greater than ${c}$.",
                   rf"x {_REL_TEX[rel]} {c + big}")
        else:
            solution = f"{c} < x {rel} {c + big}"
            s.step("Solve for $x$ and combine with the domain.",
                   rf"{c} < x {_REL_TEX[rel]} {c + big}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def pc_log_model_context(min_exp=2, max_exp=12):
    r"""Logarithmic Scales in Context (pH, Decibels, Richter)

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | $[\text{H}^+] = 3.2 \times 10^{-5}$. Find $\text{pH} = -\log[\text{H}^+]$. | $4.495$ |
    | Sound A is 20 dB louder than sound B. How many times as intense? | $100$ |
    | Magnitudes 6.5 and 5.2: how many times the amplitude? | $19.953$ |
    """
    mode = random.choice(["ph", "decibel", "db_ratio", "richter"])
    s = Steps()
    if mode == "ph":
        m = Fraction(random.choice([10] + list(range(11, 100))), 10)
        e = random.randint(min_exp, max_exp)
        value = e - math.log10(m)
        conc = f"{_num(m)} \\times 10^{{-{e}}}" if m != 1 else f"10^{{-{e}}}"
        problem = (rf"The pH of a solution is $\text{{pH}} = -\log[\text{{H}}^+]$, where "
                   rf"$[\text{{H}}^+]$ is the hydrogen-ion concentration in moles per liter. "
                   rf"Find the pH when $[\text{{H}}^+] = {conc}$. {_ROUND_IF_HINT}")
        s.substitute(rf"\text{{pH}} = -\log\left({conc}\right)")
        s.step("Use the product rule: the log of a product is the sum of the logs, and "
               r"$\log 10^{-n} = -n$.",
               rf"\text{{pH}} = -\left(\log {_num(m)} - {e}\right) = {e} - \log {_num(m)}")
        s.step("Evaluate with a calculator.", rf"\text{{pH}} \approx {_num(value)}")
    elif mode == "decibel":
        m = Fraction(random.choice([10] + list(range(11, 100))), 10)
        e = random.randint(2, 10)
        value = 10 * (math.log10(m) - e + 12)
        inten = f"{_num(m)} \\times 10^{{-{e}}}" if m != 1 else f"10^{{-{e}}}"
        problem = (rf"The loudness of a sound, in decibels, is "
                   rf"$L = 10\log\left(\frac{{I}}{{I_0}}\right)$, where $I$ is its intensity "
                   rf"in watts per square meter and $I_0 = 10^{{-12}}$. Find the loudness of "
                   rf"a sound with intensity $I = {inten}$. {_ROUND_IF_HINT}")
        s.substitute(rf"L = 10\log\left(\frac{{{inten}}}{{10^{{-12}}}}\right)")
        mant = rf"{_num(m)} \times " if m != 1 else ""
        s.step("Divide the powers of ten by subtracting exponents.",
               rf"L = 10\log\left({mant}10^{{{12 - e}}}\right)")
        s.step("Evaluate with a calculator.",
               rf"L = 10\left(\log {_num(m)} + {12 - e}\right) \approx {_num(value)}")
    elif mode == "db_ratio":
        d = random.randint(1, 40)
        value = 10 ** (d / 10)
        problem = (rf"Loudness in decibels is $L = 10\log\left(\frac{{I}}{{I_0}}\right)$. "
                   rf"Sound A is ${d}$ decibels louder than sound B. How many times as "
                   rf"intense as sound B is sound A? {_ROUND_IF_HINT}")
        s.step("Subtract the two loudness formulas; the quotient rule combines the logs.",
               rf"L_A - L_B = 10\log\left(\frac{{I_A}}{{I_B}}\right) = {d}")
        equals = "=" if d % 10 == 0 else r"\approx"
        s.step("Divide by $10$ and rewrite in exponential form.",
               rf"\frac{{I_A}}{{I_B}} = 10^{{{_num(Fraction(d, 10))}}} {equals} {_num(value)}")
    else:
        big_t = random.randint(40, 90)
        diff_t = random.randint(1, min(30, big_t - 10))
        small_t = big_t - diff_t
        diff = Fraction(diff_t, 10)
        value = 10 ** (diff_t / 10)
        problem = (rf"The Richter magnitude of an earthquake is "
                   rf"$M = \log\left(\frac{{A}}{{A_0}}\right)$, where $A$ is the amplitude "
                   rf"of its seismic waves. An earthquake of magnitude "
                   rf"${_num(Fraction(big_t, 10))}$ has how many times the amplitude of one "
                   rf"of magnitude ${_num(Fraction(small_t, 10))}$? {_ROUND_IF_HINT}")
        s.step("Subtract the magnitudes; the quotient rule combines the logs.",
               rf"\log\left(\frac{{A_1}}{{A_2}}\right) = {_num(Fraction(big_t, 10))} - "
               rf"{_num(Fraction(small_t, 10))} = {_num(diff)}")
        equals = "=" if diff.denominator == 1 else r"\approx"
        s.step("Rewrite in exponential form.",
               rf"\frac{{A_1}}{{A_2}} = 10^{{{_num(diff)}}} {equals} {_num(value)}")
    solution = f"${_num(value)}$"
    s.answer(solution, lead="Rounded to the nearest thousandth if necessary, the answer is")
    return problem, solution, s.done()


@register
def pc_semilog_model(min_slope=2, max_slope=30):
    r"""Exponential Model from a Semi-Log Plot

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Semi-log line $\log_{10} y = 0.05x + 1.3$; model $y = ab^x$. Find $a$. | $19.953$ |
    | Semi-log line $\ln y = -0.2x + 3$; model $y = ab^x$. Find $b$. | $0.819$ |

    A line ``log y = mx + c`` on a semi-log plot means ``y = B^c (B^m)^x``.
    """
    natural = random.random() < 0.5
    m = Fraction(random.randint(min_slope, max_slope) * random.choice([1, -1]), 100)
    c = Fraction(random.randint(5, 50 if natural else 30), 10)
    find_a = random.random() < 0.5
    base_tex, log_tex = ("e", r"\ln y") if natural else ("10", r"\log_{10} y")
    base = math.e if natural else 10
    value = base ** float(c) if find_a else base ** float(m)
    line = f"{log_tex} = {_num(m)}x + {_num(c)}"
    target = ("$a$, the initial value" if find_a
              else f"$b$, the {'growth' if m > 0 else 'decay'} factor")
    problem = (f"A semi-log plot of a data set, with ${log_tex}$ on the vertical axis and "
               f"$x$ on the horizontal axis, is a straight line with equation ${line}$. "
               f"The data are modeled by $y = ab^x$. Find {target}. {_ROUND_IF_HINT}")
    solution = f"${_num(value)}$"

    s = Steps()
    s.step(f"Undo the {'natural log' if natural else 'log'} by raising ${base_tex}$ to "
           f"each side.", rf"y = {base_tex}^{{{_num(m)}x + {_num(c)}}}")
    s.step("Split the exponent with the exponent rules.",
           rf"y = {base_tex}^{{{_num(c)}}}\left({base_tex}^{{{_num(m)}}}\right)^{{x}}")
    if find_a:
        s.step("Match with $y = ab^x$.", rf"a = {base_tex}^{{{_num(c)}}} \approx {_num(value)}")
    else:
        s.step("Match with $y = ab^x$.", rf"b = {base_tex}^{{{_num(m)}}} \approx {_num(value)}")
    s.answer(solution, lead="Rounded to the nearest thousandth if necessary, the answer is")
    return problem, solution, s.done()
