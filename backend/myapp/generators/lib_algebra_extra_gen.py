"""Solveki-local overrides for stock ``mathgenerator`` algebra generators.

Each is named to *exactly* match a stock ``mathgenerator`` generator so
``_make_problem_for_topic`` (which resolves ``LOCAL_GENERATORS`` before the
library) picks up our version. The first two were caught by the
served-problem quality contract test in ``test_generators.py``, because the
stock versions fail on random draws the initial sweep missed:

* ``expanding`` (Expanding Factored Binomial) raises ``IndexError`` on some
  inputs — a 500 for the student — and even when it doesn't, it can emit a
  malformed product like ``-14x^2x+3``.
* ``power_rule_differentiation`` returns the derivative with LaTeX braces
  (``90x^{9} + 30x^{2}``) that can't be typed into the answer box, lists terms
  in the problem's arbitrary order, and shows ugly ``1x^{5}`` coefficients.

The rest (``basic_algebra`` through ``permutation``) replace stock versions
that seeded topics use, so every card gets a step-by-step explanation and a
typeable answer whose format the problem states (``a/b``, ``(x, y)``,
``a+bi``, ``>``/``<``/``=``), at review-level numbers.

Each generator takes no required arguments, is ``@register``-ed, and returns
``(problem, solution, steps)`` with a strictly keyboard-typeable solution.
"""
import math
import random
from fractions import Fraction

from ._format import frac, frac_from, pair
from ._registry import register
from ._steps import Steps, paren, tex_frac


def _term(coeff, power):
    """Render one polynomial term typeably (ASCII caret, drop unit coeff/^1).

    ``coeff`` may be negative; the caller joins terms with explicit signs, so
    this renders the magnitude's variable part and keeps the sign on the
    coefficient (e.g. ``-3x^2``). A zero coefficient yields ``"0"``.
    """
    if coeff == 0:
        return "0"
    if power == 0:
        return str(coeff)
    var = "x" if power == 1 else f"x^{power}"
    if coeff == 1:
        return var
    if coeff == -1:
        return f"-{var}"
    return f"{coeff}{var}"


def _poly_str(terms):
    """Render ``{power: coeff}`` as a descending-power polynomial string.

    Zero coefficients are dropped. The leading term keeps its own sign; each
    subsequent term is joined with `` + `` or `` - `` so the result reads like
    ``4x^3 - 2x^2 + x - 5``. Returns ``"0"`` if every coefficient is zero.
    """
    powers = [p for p in sorted(terms, reverse=True) if terms[p] != 0]
    if not powers:
        return "0"
    out = _term(terms[powers[0]], powers[0])
    for p in powers[1:]:
        coeff = terms[p]
        op = " + " if coeff > 0 else " - "
        out += op + _term(abs(coeff), p)
    return out


def _joined(terms):
    """Render ``(coeff, power)`` terms in the given order, without combining.

    Like :func:`_poly_str` but keeps like terms separate, for showing the
    products of a distribution before they are combined.
    """
    out = _term(*terms[0])
    for coeff, power in terms[1:]:
        out += (" + " if coeff >= 0 else " - ") + _term(abs(coeff), power)
    return out


@register
def expanding(max_coeff=9):
    r"""Expanding Factored Binomial

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Expand $(2x-1)(3x+4)$. | 6x^2 + 5x - 4 |

    ``(ax+b)(cx+d) = ac x^2 + (ad+bc) x + bd``. Overrides the stock
    ``expanding``, which raises ``IndexError`` on some draws and can emit a
    malformed product. The answer is a typeable quadratic in descending order.
    """
    nonzero = [n for n in range(-max_coeff, max_coeff + 1) if n != 0]
    a = random.choice(nonzero)
    c = random.choice(nonzero)
    b = random.randint(-max_coeff, max_coeff)
    d = random.randint(-max_coeff, max_coeff)

    def _factor(lead, const):
        # Render one factor like (2x-1); lead is nonzero.
        lead_str = "x" if lead == 1 else ("-x" if lead == -1 else f"{lead}x")
        if const == 0:
            return f"({lead_str})"
        return f"({lead_str}{'+' if const > 0 else '-'}{abs(const)})"

    coeffs = {2: a * c, 1: a * d + b * c, 0: b * d}
    problem = (
        f"Expand ${_factor(a, b)}{_factor(c, d)}$. "
        "Write your answer with terms in descending order of power, "
        "e.g. 6x^2 + 5x - 4."
    )
    solution = _poly_str(coeffs)

    # Each factor's nonzero terms as (coeff, power); a product of two terms
    # multiplies the coefficients and adds the powers.
    first = [(a, 1)] + ([(b, 0)] if b else [])
    second = [(c, 1)] + ([(d, 0)] if d else [])
    products = [(p1 * p2, e1 + e2) for p1, e1 in first for p2, e2 in second]
    pairs = " + ".join(
        rf"{paren(_term(p1, e1))} \cdot {paren(_term(p2, e2))}"
        for p1, e1 in first for p2, e2 in second
    )
    s = Steps()
    if len(products) == 4:
        s.step("Use FOIL: multiply the First, Outer, Inner and Last terms.", pairs)
    else:
        s.step("Distribute: multiply each term of one factor by each term of the other.", pairs)
    s.step(r"Multiply each pair: multiply the coefficients, and $x \cdot x = x^2$.",
           _joined(products))
    if len(products) == 4:
        middle = a * d + b * c
        if middle:
            s.step(f"Combine the like terms ${_term(a * d, 1)}$ and ${_term(b * c, 1)}$.",
                   f"{_joined([(a * d, 1), (b * c, 1)])} = {_term(middle, 1)}")
        else:
            s.step(f"The $x$-terms ${_term(a * d, 1)}$ and ${_term(b * c, 1)}$ cancel out.")
    s.answer(solution)
    return problem, solution, s.done()


@register
def power_rule_differentiation(min_power=1, max_power=8):
    r"""Power Rule Differentiation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Differentiate $3x^{5}+2x^{2}$. | 15x^4 + 4x |

    ``d/dx (c x^n) = c*n x^(n-1)``. Overrides the stock generator, which
    returned the derivative with untypeable LaTeX braces. Here the answer is a
    typeable polynomial in descending power order with an ASCII caret.
    """
    powers = random.sample(range(min_power, max_power + 1),
                           random.randint(2, 4))
    coeffs = {p: random.randint(1, 9) for p in powers}
    shown = " + ".join(f"{coeffs[p]}x^{{{p}}}" for p in sorted(powers, reverse=True))

    # Derivative: c x^n -> (c*n) x^(n-1). A power-1 term becomes a constant.
    deriv = {}
    for p, c in coeffs.items():
        deriv[p - 1] = deriv.get(p - 1, 0) + c * p

    problem = (
        f"Differentiate ${shown}$ with respect to $x$. "
        "Write your answer with terms in descending order of power, "
        "e.g. 15x^4 + 4x."
    )
    solution = _poly_str(deriv)

    s = Steps()
    s.formula("The power rule", r"\frac{d}{dx}\left(c x^{n}\right) = c \cdot n\, x^{n-1}")
    s.step("Differentiate each term separately: multiply the coefficient by the "
           "exponent, then lower the exponent by $1$.",
           r"\begin{aligned} " + r" \\ ".join(
               rf"{coeffs[p]}x^{{{p}}} &\to {coeffs[p]} \cdot {p}\, x^{{{p - 1}}} = {_term(coeffs[p] * p, p - 1)}"
               for p in sorted(powers, reverse=True)
           ) + r" \end{aligned}")
    if 1 in coeffs:
        s.step(f"Since $x^{{0}} = 1$, the term ${coeffs[1]}x^{{1}}$ becomes the constant ${coeffs[1]}$.")
    s.answer(solution, lead="Add the differentiated terms. The answer is")
    return problem, solution, s.done()


# ---------------------------------------------------------------------------
# Overrides of stock generators that seeded topics use. The library versions
# answer with LaTeX or Python reprs (``(3+4j)``), can emit singular systems or
# parallel lines, or use numbers too big to work by hand.
# ---------------------------------------------------------------------------

def _linear(coeffs, names):
    """Render ``3x - 2y`` style: ``coeffs`` pair up with variable ``names``.

    Zero coefficients are dropped (the caller guarantees one is nonzero).
    """
    out = ""
    for c, v in ((c, v) for c, v in zip(coeffs, names) if c):
        body = v if abs(c) == 1 else f"{abs(c)}{v}"
        if not out:
            out = f"-{body}" if c < 0 else body
        else:
            out += f" - {body}" if c < 0 else f" + {body}"
    return out


def _plus(n):
    """`` + n`` or `` - |n|``, for appending a constant to an expression."""
    return f" + {n}" if n >= 0 else f" - {-n}"


def _slope_line(m, b):
    """The right side of ``y = mx + b`` for integer slope and intercept."""
    if m == 0:
        return str(b)
    return _linear([m], ["x"]) + (_plus(b) if b else "")


def _tex_num(value):
    """A ``Fraction``/int as LaTeX: an integer, or a signed ``\\frac``."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return tex_frac(value.numerator, value.denominator)


def _complex(re_part, im_part):
    """Typeable ``a+bi`` text: ``3-2i``, ``4+i``, ``-i``, ``5``."""
    if im_part == 0:
        return str(re_part)
    mag = "" if abs(im_part) == 1 else str(abs(im_part))
    sign = "-" if im_part < 0 else ("+" if re_part else "")
    return f"{re_part if re_part else ''}{sign}{mag}i"


_COMPARE_WORD = {">": "greater than", "<": "less than", "=": "equal to"}


@register
def basic_algebra(max_coeff=9, max_const=10, max_rhs=20):
    r"""Solve a Two-Step Linear Equation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve for $x$: $3x + 4 = 10$. Express your answer as a fraction... | 2 |

    Overrides the stock ``basic_algebra``. Grade 7 review: ``ax + b = c`` with
    integer coefficients (negatives included). The answer ``(c - b) / a`` is
    reduced and may be a fraction, so the problem states the format.
    """
    a = random.choice([n for n in range(-max_coeff, max_coeff + 1) if n not in (0, 1)])
    b = random.choice([n for n in range(-max_const, max_const + 1) if n != 0])
    c = random.randint(-max_rhs, max_rhs)
    ax = _linear([a], "x")
    problem = (
        f"Solve for $x$: ${ax}{_plus(b)} = {c}$. Express your answer as a "
        "fraction in the form a/b, or an integer."
    )
    solution = frac(c - b, a)

    s = Steps()
    if b > 0:
        s.step(f"Undo the $+ {b}$: subtract ${b}$ from both sides.",
               f"{ax} = {c} - {b} = {c - b}")
    else:
        s.step(f"Undo the $- {-b}$: add ${-b}$ to both sides.",
               f"{ax} = {c} + {-b} = {c - b}")
    shown, simplified = tex_frac(c - b, a), _tex_num(Fraction(c - b, a))
    s.step(f"Undo the multiplication: divide both sides by ${a}$.",
           f"x = {shown}" + (f" = {simplified}" if simplified != shown else ""))
    s.answer(solution, lead="So $x =$")
    return problem, solution, s.done()


@register
def linear_equations(max_value=10, max_coeff=6):
    r"""Solve a System of Two Linear Equations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Solve the system of equations $2x + 3y = 7$ and $x - y = 1$. Format your answer as (x, y). | (2, 1) |

    Overrides the stock ``linear_equations``, which can emit a singular system
    and answers with two ``$x = ..$`` strings. Grade 8 review: nonzero
    coefficients and a nonzero determinant, so there is exactly one integer
    solution, explained by elimination.
    """
    nonzero = [n for n in range(-max_coeff, max_coeff + 1) if n != 0]
    x = random.randint(-max_value, max_value)
    y = random.randint(-max_value, max_value)
    while True:
        a1, b1, a2, b2 = (random.choice(nonzero) for _ in range(4))
        if a1 * b2 != a2 * b1:
            break
    c1, c2 = a1 * x + b1 * y, a2 * x + b2 * y
    problem = (
        f"Solve the system of equations ${_linear([a1, b1], 'xy')} = {c1}$ and "
        f"${_linear([a2, b2], 'xy')} = {c2}$. Format your answer as (x, y)."
    )
    solution = pair(x, y)

    # Scale each equation so the x-coefficients match, then subtract.
    target = abs(a1 * a2) // math.gcd(a1, a2)
    m1, m2 = target // a1, target // a2
    y_coeff, y_rhs = b1 * m1 - b2 * m2, c1 * m1 - c2 * m2
    tx = _linear([target], "x")
    s = Steps()
    if m1 == 1 and m2 == 1:
        s.step(f"Use elimination. Both equations already contain ${tx}$, "
               "so subtracting them removes $x$.")
    else:
        scaled = [f"the {which} equation by ${m}$"
                  for which, m in (("first", m1), ("second", m2)) if m != 1]
        s.step(f"Use elimination. Multiply {' and '.join(scaled)} so both contain ${tx}$.",
               rf"\begin{{aligned}} {_linear([a1 * m1, b1 * m1], 'xy')} &= {c1 * m1} \\ "
               rf"{_linear([a2 * m2, b2 * m2], 'xy')} &= {c2 * m2} \end{{aligned}}")
    s.step("Subtract the second equation from the first. The $x$-terms cancel.",
           f"{_linear([y_coeff], 'y')} = {y_rhs}")
    if y_coeff != 1:
        s.step(f"Divide both sides by ${y_coeff}$.", f"y = {y}")
    ax = _linear([a1], "x")
    lines = [f"{ax} {'+' if b1 > 0 else '-'} {abs(b1)}({y}) &= {c1}", f"{ax} &= {c1 - b1 * y}"]
    if a1 != 1:
        lines.append(f"x &= {x}")
    s.step(f"Substitute $y = {y}$ into the first equation and solve for $x$.",
           r"\begin{aligned} " + r" \\ ".join(lines) + r" \end{aligned}")
    s.answer(solution, lead="The solution is")
    return problem, solution, s.done()


@register
def intersection_of_two_lines(max_slope=5, max_intercept=10):
    r"""Intersection of Two Lines

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the point where the lines $y = 2x + 1$ and $y = -x + 4$ intersect... | (1, 3) |

    Overrides the stock ``intersection_of_two_lines``, which can draw
    parallel or identical lines and answers in LaTeX. Algebra I review:
    integer slopes that always differ, so there is exactly one intersection;
    its coordinates may be fractions, and the problem says how to type them.
    """
    m1, m2 = random.sample(range(-max_slope, max_slope + 1), 2)
    b1 = random.randint(-max_intercept, max_intercept)
    b2 = random.randint(-max_intercept, max_intercept)
    x = Fraction(b2 - b1, m1 - m2)
    y = m1 * x + b1
    rhs1, rhs2 = _slope_line(m1, b1), _slope_line(m2, b2)
    problem = (
        f"Find the point where the lines $y = {rhs1}$ and $y = {rhs2}$ intersect. "
        "Format your answer as (x, y), writing any coordinate that isn't an "
        "integer as a fraction a/b (e.g. (3/2, -1))."
    )
    solution = f"({frac_from(x)}, {frac_from(y)})"

    s = Steps()
    s.step("Where the lines cross they have the same $y$, so set the right sides equal.",
           f"{rhs1} = {rhs2}")
    s.step("Move the $x$-terms to the left side and the constants to the right.",
           f"{_linear([m1 - m2], 'x')} = {b2 - b1}")
    xs = _tex_num(x)
    if m1 - m2 != 1:
        shown = tex_frac(b2 - b1, m1 - m2)
        s.step(f"Divide both sides by ${m1 - m2}$.",
               f"x = {shown}" + (f" = {xs}" if xs != shown else ""))
    if m1 == 0:
        s.step(f"The first line is horizontal: $y = {b1}$ for every $x$.")
    else:
        sub = rf"\left({xs}\right)" if x < 0 or x.denominator != 1 else xs
        s.step(f"Substitute $x = {xs}$ into the first equation to find $y$.",
               rf"y = {m1} \cdot {sub}{_plus(b1)} = {_tex_num(y)}")
    s.answer(solution, lead="The lines intersect at")
    return problem, solution, s.done()


@register
def surds_comparison(max_square=30, max_cube=150):
    r"""Compare a Square Root and a Cube Root

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Which symbol makes $\sqrt{20} \;\square\; \sqrt[3]{90}$ true? Type >, < or =. | > |

    Overrides the stock ``surds_comparison``, whose roots of index up to 9
    can't be compared by hand. Algebra I review: a square root against a cube
    root, compared by raising both to the 6th power (the LCM of 2 and 3),
    which keeps their order.
    """
    sq = random.randint(2, max_square)
    cu = random.randint(2, max_cube)
    square_first = random.random() < 0.5
    sq6, cu6 = sq ** 3, cu ** 2
    sq_tex, cu_tex = rf"\sqrt{{{sq}}}", rf"\sqrt[3]{{{cu}}}"
    if square_first:
        (left, lv), (right, rv) = (sq_tex, sq6), (cu_tex, cu6)
    else:
        (left, lv), (right, rv) = (cu_tex, cu6), (sq_tex, sq6)
    symbol = ">" if lv > rv else ("<" if lv < rv else "=")
    problem = rf"Which symbol makes ${left} \;\square\; {right}$ true? Type >, < or =."
    solution = symbol

    s = Steps()
    s.step("The roots have different indices, $2$ and $3$. Raise both to the "
           "$6$th power, the least common multiple of $2$ and $3$. For positive "
           "numbers this keeps their order.")
    s.step(f"Square root: $({sq_tex})^6 = {sq}^3 = {sq6}$.")
    s.step(f"Cube root: $({cu_tex})^6 = {cu}^2 = {cu6}$.")
    s.step(f"${lv}$ is {_COMPARE_WORD[symbol]} ${rv}$.")
    s.answer(solution, lead=f"So ${left} {symbol} {right}$, and the symbol is")
    return problem, solution, s.done()


@register
def log(max_base=10, max_value=1000):
    r"""Evaluate a Logarithm

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\log_{2}(8)$. | 3 |

    Overrides the stock ``log`` (bases 2-3 only, rendered as plain ``log``).
    Algebra II review: ``log_b(b^k)`` for whole-number bases and exponents
    with ``b^k`` at most ``max_value``, including ``k = 0``.
    """
    base = random.randint(2, max_base)
    k = random.choice([e for e in range(20) if base ** e <= max_value])
    value = base ** k
    log_tex = rf"\log_{{{base}}}({value})"
    problem = f"Evaluate ${log_tex}$."
    solution = str(k)

    s = Steps()
    s.step(f"A logarithm asks for an exponent: ${log_tex} = x$ means ${base}^x = {value}$.")
    if k == 0:
        s.step(f"Any nonzero number to the power $0$ is $1$, so ${base}^0 = 1$.")
    elif k == 1:
        s.step(f"Any number to the power $1$ is itself: ${base}^1 = {base}$.")
    else:
        s.step(f"Write ${value}$ as a power of ${base}$.",
               r" \times ".join([str(base)] * k) + f" = {value} = {base}^{{{k}}}")
    s.answer(solution, lead=f"So ${log_tex} =$")
    return problem, solution, s.done()


@register
def multiply_complex_numbers(max_part=9):
    r"""Multiply Two Complex Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Multiply $(3+4i)(2-i)$. Write your answer as a+bi with no spaces... | 10+5i |

    Overrides the stock ``multiply_complex_numbers``, which answers with a
    Python repr like ``(-3+4j)``. Algebra II review: nonzero integer parts up
    to ``max_part``. The product is drawn so its real part is nonzero and its
    imaginary part isn't 0 or +-1, so the a+bi form to type is unambiguous.
    """
    nonzero = [n for n in range(-max_part, max_part + 1) if n != 0]
    while True:
        a, b, c, d = (random.choice(nonzero) for _ in range(4))
        re_part, im_part = a * c - b * d, a * d + b * c
        if re_part != 0 and abs(im_part) > 1:
            break
    problem = (
        f"Multiply $({_complex(a, b)})({_complex(c, d)})$. Write your answer as "
        "a+bi with no spaces, where a and b are integers (e.g. 7-4i)."
    )
    solution = _complex(re_part, im_part)

    def term(coeff, unit):
        return f"{coeff}{unit}"

    foil = term(a * c, "") + "".join(
        f" {'-' if t < 0 else '+'} {term(abs(t), unit)}"
        for t, unit in ((a * d, "i"), (b * c, "i"), (b * d, "i^2"))
    )
    s = Steps()
    s.step("Multiply like binomials: use FOIL to multiply each part of the first "
           "number by each part of the second.", foil)
    s.step(f"Replace $i^2$ with $-1$: ${b * d}i^2 = {-b * d}$.")
    s.step("Combine the real parts and the imaginary parts.",
           rf"({a * c}{_plus(-b * d)}) + ({a * d}{_plus(b * c)})i = {solution}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def int_matrix_22_determinant(max_entry=9):
    r"""Determinant of a 2x2 Matrix

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find $\det\begin{bmatrix} 3 & 1 \\ 4 & 2 \end{bmatrix}$. | 2 |

    Overrides the stock ``int_matrix_22_determinant`` (entries up to 100).
    Review: integer entries from ``-max_entry`` to ``max_entry``.
    """
    a, b, c, d = (random.randint(-max_entry, max_entry) for _ in range(4))
    det = a * d - b * c
    problem = rf"Find $\det\begin{{bmatrix}} {a} & {b} \\ {c} & {d} \end{{bmatrix}}$."
    solution = str(det)

    s = Steps()
    s.formula(r"The determinant of a $2 \times 2$ matrix",
              r"\det\begin{bmatrix} a & b \\ c & d \end{bmatrix} = ad - bc")
    s.substitute(f"({a})({d}) - ({b})({c})")
    s.step("Multiply, then subtract.", f"{a * d} - {paren(b * c)} = {det}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def vector_dot(max_entry=9):
    r"""Dot Product of Two Vectors

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the dot product $\langle 1, -2, 3 \rangle \cdot \langle 4, 0, -1 \rangle$. | 1 |

    Overrides the stock ``vector_dot``, which renders the vectors as Python
    lists. Pre-Calculus review: 3D vectors with small integer components.
    """
    u = [random.randint(-max_entry, max_entry) for _ in range(3)]
    v = [random.randint(-max_entry, max_entry) for _ in range(3)]
    products = [p * q for p, q in zip(u, v)]
    dot = sum(products)

    def vec(w):
        return rf"\langle {', '.join(map(str, w))} \rangle"

    problem = rf"Find the dot product ${vec(u)} \cdot {vec(v)}$."
    solution = str(dot)

    s = Steps()
    s.formula("The dot product multiplies matching components and adds them. It",
              r"\langle u_1, u_2, u_3 \rangle \cdot \langle v_1, v_2, v_3 \rangle"
              r" = u_1 v_1 + u_2 v_2 + u_3 v_3")
    s.substitute(" + ".join(f"({p})({q})" for p, q in zip(u, v)))
    s.step("Multiply each pair, then add.",
           " + ".join(paren(p) for p in products) + f" = {dot}")
    s.answer(solution)
    return problem, solution, s.done()


def _ordinal(n):
    """``1st``, ``2nd``, ``23rd``, ``11th``..."""
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@register
def arithmetic_progression_term(max_first=20, max_diff=10, min_n=5, max_n=30):
    r"""Term of an Arithmetic Sequence

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the 20th term of the arithmetic sequence $3, 7, 11, \dots$ | 79 |

    Overrides the stock ``arithmetic_progression_term`` (values up to 100,
    terms up to the 100th). Algebra I review: ``a_n = a_1 + (n - 1)d`` with a
    nonzero common difference.
    """
    a1 = random.randint(-max_first, max_first)
    d = random.choice([k for k in range(-max_diff, max_diff + 1) if k != 0])
    n = random.randint(min_n, max_n)
    term = a1 + (n - 1) * d
    problem = (
        f"Find the {_ordinal(n)} term of the arithmetic sequence "
        rf"${a1}, {a1 + d}, {a1 + 2 * d}, \dots$"
    )
    solution = str(term)

    s = Steps()
    s.step("Find the common difference by subtracting consecutive terms: "
           f"$d = {a1 + d} - {paren(a1)} = {d}$.")
    s.formula("The $n$th term of an arithmetic sequence", "a_n = a_1 + (n - 1)d")
    s.substitute(rf"a_{{{n}}} = {a1} + ({n} - 1)({d})",
                 text=f"Substitute $a_1 = {a1}$, $n = {n}$ and $d = {d}$.")
    s.step("Multiply, then add.", rf"a_{{{n}}} = {a1} + {paren((n - 1) * d)} = {term}")
    s.answer(solution)
    return problem, solution, s.done()


def _times(factors):
    return r" \times ".join(map(str, factors))


@register
def combinations(min_n=4, max_n=12):
    r"""Combinations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | In how many ways can you choose 3 objects from 8 distinct objects if order doesn't matter? | 56 |

    Overrides the stock ``combinations`` (answers up to 184756). Algebra II
    review: ``nCr = n! / (r!(n-r)!)`` with ``n`` up to ``max_n``, explained by
    cancelling the larger factorial in the denominator.
    """
    n = random.randint(min_n, max_n)
    r = random.randint(1, n - 1)
    count = math.comb(n, r)
    problem = (
        f"In how many ways can you choose ${r}$ objects from ${n}$ distinct "
        f"objects if order doesn't matter? (Find ${{}}_{{{n}}}C_{{{r}}}$.)"
    )
    solution = str(count)

    k = min(r, n - r)
    top = list(range(n, n - k, -1))
    s = Steps()
    s.formula("The number of combinations", r"{}_nC_r = \frac{n!}{r!\,(n-r)!}")
    s.substitute(rf"{{}}_{{{n}}}C_{{{r}}} = \frac{{{n}!}}{{{r}!\,{n - r}!}}")
    if k == 1:
        s.step(f"Cancel ${n - 1}!$ from the top and bottom. Since ${n}! = {n} \\times {n - 1}!$, "
               f"only ${n}$ is left.", rf"\frac{{{n} \times {n - 1}!}}{{1 \times {n - 1}!}} = {count}")
    else:
        s.step(f"Cancel ${n - k}!$ from the top and bottom. That leaves the largest "
               f"${k}$ factors of ${n}!$ over ${k}!$.",
               rf"\frac{{{_times(top)}}}{{{_times(range(k, 0, -1))}}}"
               rf" = \frac{{{math.prod(top)}}}{{{math.factorial(k)}}}")
        s.step("Divide.", rf"{math.prod(top)} \div {math.factorial(k)} = {count}")
    s.answer(solution)
    return problem, solution, s.done()


@register
def permutation(min_n=4, max_n=12, max_r=4):
    r"""Permutations

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | In how many ways can you arrange 3 objects chosen from 8 distinct objects if order matters? | 336 |

    Overrides the stock ``permutation`` (answers in the hundreds of millions).
    Algebra II review: ``nPr = n! / (n-r)!`` with ``r`` at most ``max_r``.
    """
    n = random.randint(min_n, max_n)
    r = random.randint(1, min(max_r, n))
    count = math.perm(n, r)
    problem = (
        f"In how many ways can you arrange ${r}$ objects chosen from ${n}$ "
        f"distinct objects if order matters? (Find ${{}}_{{{n}}}P_{{{r}}}$.)"
    )
    solution = str(count)

    top = list(range(n, n - r, -1))
    s = Steps()
    s.formula("The number of permutations", r"{}_nP_r = \frac{n!}{(n-r)!}")
    s.substitute(rf"{{}}_{{{n}}}P_{{{r}}} = \frac{{{n}!}}{{{n - r}!}}")
    if n == r:
        s.step("Since $0! = 1$, this is just the product of every number from "
               f"${n}$ down to $1$.", f"{_times(top)} = {count}")
    else:
        which = "largest factor" if r == 1 else f"largest ${r}$ factors"
        s.step(f"Cancel ${n - r}!$ from the top and bottom. That leaves the {which} "
               f"of ${n}!$.", f"{_times(top)} = {count}")
    s.answer(solution)
    return problem, solution, s.done()
