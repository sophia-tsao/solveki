"""Solveki-local overrides for stock ``mathgenerator`` arithmetic & number-theory generators.

Each generator here is named to *exactly* match a stock ``mathgenerator``
generator so ``_make_problem_for_topic`` (which resolves ``LOCAL_GENERATORS``
before the library) overrides the library version. They ask the same kind of
question as the library, but return a typeable answer *and* a step-by-step
explanation (which the library can't provide).

Number ranges are pitched at the lowest grade each topic is seeded in (e.g.
addition and subtraction in Grade 1, multiplication and division facts in
Grade 3), since these cards review a concept rather than drill big
calculations. Worded answers (``yes``/``no``) and comparison symbols are
spelled out in the problem, because grading is an exact match.
"""
import math
import random

from ._registry import register
from ._steps import Steps, paren, tex_frac
from ._variants import with_variants

_PLACES = ["ones", "tens", "hundreds", "thousands", "ten-thousands"]


def _digits(n):
    """Digits of ``n`` (n >= 0), ones place first: ``427 -> [7, 2, 4]``."""
    return [int(d) for d in reversed(str(n))]


def _column(top, bottom, op):
    """A right-aligned written column, ``27`` over ``+ 15`` with a rule."""
    return rf"\begin{{array}}{{r}} {top} \\ {op}\,{bottom} \\ \hline \end{{array}}"


def _running_product(factors):
    """Multiply ``factors`` left to right as an aligned list of partial products.

    Returns ``(latex, product)``; the latex is ``None`` for fewer than two
    factors.
    """
    total = factors[0]
    lines = []
    for f in factors[1:]:
        lines.append(rf"{total} \times {f} &= {total * f}")
        total *= f
    if not lines:
        return None, total
    return r"\begin{aligned} " + r" \\ ".join(lines) + r" \end{aligned}", total


def _smallest_factor(n):
    """The smallest prime factor of ``n`` (n >= 2)."""
    p = 2
    while p * p <= n:
        if n % p == 0:
            return p
        p += 1
    return n


def _primes_through(limit):
    return [p for p in range(2, limit + 1) if _smallest_factor(p) == p]


def _primality_steps(s, n):
    """Add the steps deciding whether ``n`` (n >= 2) is prime; return that."""
    p = _smallest_factor(n)
    if p < n:
        s.step(
            f"Try dividing by the primes $2, 3, 5, 7, \\dots$ in order. The first one "
            f"that divides ${n}$ evenly is ${p}$: ${n} \\div {p} = {n // p}$."
        )
        s.step(
            f"So ${n} = {p} \\times {n // p}$. "
            f"Besides $1$ and ${n}$, it also has the factor ${p}$, "
            f"so ${n}$ is composite, not prime."
        )
        return False
    tests = _primes_through(math.isqrt(n))
    if not tests:
        s.step(f"The only whole numbers that divide ${n}$ are $1$ and ${n}$.")
    else:
        nxt = tests[-1] + 1
        while _smallest_factor(nxt) != nxt:
            nxt += 1
        listed = ", ".join(f"${t}$" for t in tests)
        s.step(
            f"You only need to test primes whose square is at most ${n}$. "
            f"The next prime, ${nxt}$, has ${nxt} \\times {nxt} = {nxt * nxt} > {n}$, "
            f"so test {listed}.",
            r",\quad ".join(rf"{n} \div {t} = {n // t} \text{{ R }} {n % t}" for t in tests),
        )
        s.step(f"None of them divides ${n}$ evenly, so its only factors are $1$ and ${n}$.")
    s.step(f"So ${n}$ is prime, not composite.")
    return True


@register
@with_variants
def addition(max_sum=99, max_addend=50):
    r"""Addition of Two Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is $27 + 15$? | 42 |

    Grade 1 review: sums up to 99. Single-digit pairs are explained by
    counting on; anything bigger with column addition and carrying.
    """
    max_addend = min(max_addend, max_sum)
    a = random.randint(0, max_addend)
    b = random.randint(0, min(max_sum - a, max_addend))
    total = a + b
    problem = f"What is ${a} + {b}$?"
    solution = str(total)

    s = Steps()
    if a < 10 and b < 10:
        start, count = max(a, b), min(a, b)
        if count == 0:
            s.step(f"Adding $0$ doesn't change a number, so the sum is ${start}$.")
        else:
            s.step(f"Start at the bigger number, ${start}$, and count on ${count}$ more.")
            s.step(
                "Count up: " + ", ".join(f"${k}$" for k in range(start + 1, total + 1)) + "."
            )
    else:
        s.step("Write the numbers in a column, lining up the ones and the tens.",
               _column(a, b, "+"))
        da, db = _digits(a), _digits(b)
        carry = 0
        for i in range(max(len(da), len(db))):
            place = _PLACES[i]
            parts = [d[i] for d in (da, db) if i < len(d)]
            col = sum(parts) + carry
            shown = " + ".join(str(p) for p in parts)
            if carry:
                shown += f" + {carry}"
            if len(parts) == 1 and not carry:
                s.step(f"Bring down the ${parts[0]}$ in the {place} place.")
                continue
            label = " (including the carried 1)" if carry else ""
            last = i == max(len(da), len(db)) - 1
            if col >= 10 and not last:
                s.step(f"Add the {place}{label}: ${shown} = {col}$. "
                       f"Write ${col % 10}$ and carry $1$ to the {_PLACES[i + 1]}.")
                carry = 1
            else:
                s.step(f"Add the {place}{label}: ${shown} = {col}$. Write ${col}$.")
                carry = 0
    s.answer(solution, lead=f"So ${a} + {b} =$")
    return problem, solution, s.done()


@register
@with_variants
def subtraction(max_minuend=99, max_diff=99):
    r"""Subtraction of Two Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is $42 - 18$? | 24 |

    Grade 1 review: whole numbers up to 99 with a non-negative difference.
    Single-digit problems are explained by counting back; bigger ones with
    column subtraction and regrouping (borrowing). The written method assumes
    two-digit numbers (no regrouping across a zero), so keep ``max_minuend``
    at 99 or below.
    """
    a = random.randint(0, max_minuend)
    b = random.randint(max(0, a - max_diff), a)
    diff = a - b
    problem = f"What is ${a} - {b}$?"
    solution = str(diff)

    s = Steps()
    if a < 10:
        if b == 0:
            s.step(f"Taking away $0$ leaves the number unchanged, so the difference is ${a}$.")
        else:
            s.step(f"Start at ${a}$ and count back ${b}$.")
            s.step("Count back: " + ", ".join(f"${k}$" for k in range(a - 1, diff - 1, -1)) + ".")
    else:
        s.step("Write the numbers in a column, lining up the ones and the tens.",
               _column(a, b, "-"))
        top, bot = _digits(a), _digits(b)
        for i in range(len(top)):
            place = _PLACES[i]
            if i >= len(bot):
                if top[i] or i < len(_digits(diff)):
                    s.step(f"Bring down the ${top[i]}$ in the {place} place.")
                continue
            if top[i] < bot[i]:
                s.step(
                    f"In the {place}, you can't take ${bot[i]}$ from ${top[i]}$. "
                    f"Regroup: borrow $1$ from the {_PLACES[i + 1]}, so ${top[i + 1]}$ "
                    f"becomes ${top[i + 1] - 1}$ and the {place} become ${top[i] + 10}$. "
                    f"Then ${top[i] + 10} - {bot[i]} = {top[i] + 10 - bot[i]}$."
                )
                top[i + 1] -= 1
            else:
                left = top[i] - bot[i]
                none = f", so there are no {place} left" if left == 0 and i == len(top) - 1 else ""
                s.step(f"Subtract the {place}: ${top[i]} - {bot[i]} = {left}${none}.")
    s.answer(solution, lead=f"So ${a} - {b} =$")
    return problem, solution, s.done()


@register
@with_variants
def multiplication(max_factor=12):
    r"""Multiplication Facts

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is $7 \times 4$? | 28 |

    Grade 3 review: times-table facts from 0 to ``max_factor``. Explained by
    skip counting (equal groups).
    """
    a = random.randint(0, max_factor)
    b = random.randint(0, max_factor)
    product = a * b
    problem = f"What is ${a} \\times {b}$?"
    solution = str(product)

    s = Steps()
    if a == 0 or b == 0:
        s.step("Any number times $0$ is $0$: zero groups, or groups of nothing, add up to nothing.")
    elif a == 1 or b == 1:
        other = b if a == 1 else a
        s.step(f"Any number times $1$ is itself: one group of ${other}$ is just ${other}$.")
    else:
        big, small = max(a, b), min(a, b)
        s.step(f"${a} \\times {b}$ means ${small}$ equal groups of ${big}$. "
               "The order of the factors doesn't change the product.")
        s.step(f"Skip count by ${big}$, ${small}$ times: "
               + ", ".join(f"${big * k}$" for k in range(1, small + 1)) + ".")
    s.answer(solution, lead=f"So ${a} \\times {b} =$")
    return problem, solution, s.done()


@register
@with_variants
def division(max_divisor=10, max_quotient=10):
    r"""Division Facts

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | What is $42 \div 6$? | 7 |

    Grade 3 review: dividends within 100 that divide evenly. Explained with
    the related multiplication fact, found by skip counting.
    """
    divisor = random.randint(1, max_divisor)
    quotient = random.randint(0, max_quotient)
    dividend = divisor * quotient
    problem = f"What is ${dividend} \\div {divisor}$?"
    solution = str(quotient)

    s = Steps()
    s.step(f"${dividend} \\div {divisor}$ asks: how many groups of ${divisor}$ make ${dividend}$? "
           f"Think of the multiplication fact ${divisor} \\times ? = {dividend}$.")
    if quotient == 0:
        s.step(f"$0$ split into groups of ${divisor}$ makes no groups, since ${divisor} \\times 0 = 0$.")
    elif divisor == 1:
        s.step(f"Dividing by $1$ leaves a number unchanged: ${dividend}$ groups of $1$ make ${dividend}$.")
    else:
        s.step(f"Skip count by ${divisor}$ until you reach ${dividend}$: "
               + ", ".join(f"${divisor * k}$" for k in range(1, quotient + 1))
               + f". That is ${quotient}$ jumps, so ${divisor} \\times {quotient} = {dividend}$.")
    s.answer(solution, lead=f"So ${dividend} \\div {divisor} =$")
    return problem, solution, s.done()


@register
@with_variants
def absolute_difference(max_val=25):
    r"""Absolute Difference Between Two Numbers

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\lvert 6 - (-9) \rvert$. | 15 |

    Grade 6 review: integers from ``-max_val`` to ``max_val``.
    """
    a = random.randint(-max_val, max_val)
    b = random.randint(-max_val, max_val)
    diff = a - b
    problem = f"Evaluate $\\lvert {a} - {paren(b)} \\rvert$."
    solution = str(abs(diff))

    s = Steps()
    if b < 0:
        s.step("Work inside the absolute value bars first. Subtracting a negative "
               "number is the same as adding its opposite.",
               rf"{a} - ({b}) = {a} + {-b} = {diff}")
    else:
        s.step("Work inside the absolute value bars first.", rf"{a} - {b} = {diff}")
    if diff < 0:
        s.step(f"The absolute value is the distance from $0$, which is never negative, "
               f"so drop the minus sign: $\\lvert {diff} \\rvert = {-diff}$.")
    else:
        s.step(f"The absolute value is the distance from $0$. ${diff}$ is not negative, "
               f"so it stays the same: $\\lvert {diff} \\rvert = {diff}$.")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def exponentiation(min_base=2, max_base=10, min_exp=2, max_exp=5, max_value=10000):
    r"""Exponentiation

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $3^{4}$. | 81 |

    Grade 6 review: whole-number powers no bigger than ``max_value``.
    """
    base = random.randint(min_base, max_base)
    exps = [e for e in range(min_exp, max_exp + 1) if base ** e <= max_value] or [min_exp]
    exp = random.choice(exps)
    value = base ** exp
    problem = f"Evaluate ${base}^{{{exp}}}$."
    solution = str(value)

    s = Steps()
    factors = [base] * exp
    expanded = rf"{base}^{{{exp}}} = " + r" \times ".join(map(str, factors))
    lead = f"The exponent ${exp}$ tells you to use the base ${base}$ as a factor ${exp}$ times."
    if exp == 2:
        s.step(lead, f"{expanded} = {value}")
    else:
        s.step(lead, expanded)
        work, _ = _running_product(factors)
        s.step("Multiply from left to right.", work)
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def square(min_val=1, max_val=20):
    r"""Square of a Number

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $17^2$. | 289 |

    Grade 6 review: squares of whole numbers up to ``max_val``.
    """
    a = random.randint(min_val, max_val)
    value = a * a
    problem = f"Evaluate ${a}^2$."
    solution = str(value)

    s = Steps()
    s.step("Squaring a number means multiplying it by itself.", rf"{a}^2 = {a} \times {a}")
    if a > 12 and a % 10:
        tens, ones = a - a % 10, a % 10
        s.step(f"Break the second ${a}$ into ${tens} + {ones}$ and multiply each part.",
               rf"{a} \times {tens} + {a} \times {ones} = {a * tens} + {a * ones} = {value}")
    else:
        s.step("Multiply.", rf"{a} \times {a} = {value}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def square_root(min_root=1, max_root=15):
    r"""Square Root of a Perfect Square

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $\sqrt{144}$. | 12 |

    Grade 8 review: principal square roots of perfect squares.
    """
    root = random.randint(min_root, max_root)
    n = root * root
    problem = f"Evaluate $\\sqrt{{{n}}}$."
    solution = str(root)

    s = Steps()
    s.step(f"$\\sqrt{{{n}}}$ is the non-negative number that, multiplied by itself, gives ${n}$.")
    if root > 1:
        s.step(f"Check the perfect squares near ${n}$: "
               f"${root - 1} \\times {root - 1} = {(root - 1) ** 2}$ is too small, "
               f"and ${root} \\times {root} = {n}$ is exactly right.")
    else:
        s.step("$1 \\times 1 = 1$.")
    s.answer(solution, lead=f"So $\\sqrt{{{n}}} =$")
    return problem, solution, s.done()


@register
@with_variants
def lcm(min_val=2, max_val=12):
    r"""Least Common Multiple

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the least common multiple of $8$ and $12$. | 24 |

    Grade 6 review: two different whole numbers up to ``max_val``. Explained
    by listing multiples of the larger number.
    """
    a, b = random.sample(range(min_val, max_val + 1), 2)
    answer = a * b // math.gcd(a, b)
    problem = f"Find the least common multiple (LCM) of ${a}$ and ${b}$."
    solution = str(answer)

    big, small = max(a, b), min(a, b)
    multiples = list(range(big, answer + 1, big))
    s = Steps()
    s.step(f"The least common multiple is the smallest number that both ${a}$ and ${b}$ divide into evenly.")
    s.step(f"List the multiples of the larger number, ${big}$, until you reach one "
           f"that ${small}$ also divides into.",
           ",\\ ".join(map(str, multiples)))
    earlier = f" None of the earlier multiples of ${big}$ is." if len(multiples) > 1 else ""
    s.step(f"${answer} \\div {small} = {answer // small}$ with no remainder, so ${answer}$ "
           f"is a multiple of both.{earlier}")
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def prime_factors(min_val=4, max_val=100):
    r"""Prime Factorization

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Find the prime factorization of $60$... | 2,2,3,5 |

    Grade 6 review: composite numbers up to ``max_val``, found by repeated
    division by the smallest prime.
    """
    composites = [k for k in range(max(min_val, 4), max_val + 1) if _smallest_factor(k) < k]
    n = random.choice(composites)
    factors = []
    m = n
    while m > 1:
        p = _smallest_factor(m)
        factors.append(p)
        m //= p
    problem = (
        f"Find the prime factorization of ${n}$. List the prime factors from least "
        "to greatest, repeating any that appear more than once, separated by "
        "commas with no spaces (e.g. 2,2,3 for 12)."
    )
    solution = ",".join(map(str, factors))

    s = Steps()
    s.step("Divide by the smallest prime that goes in evenly, and keep going until you reach $1$.")
    m = n
    for p in sorted(set(factors)):
        start = m
        chain = []
        while m % p == 0:
            chain.append(rf"{m} \div {p} = {m // p}")
            m //= p
        times = factors.count(p)
        how = "once" if times == 1 else ("twice" if times == 2 else f"{times} times")
        s.step(f"The smallest prime that divides ${start}$ is ${p}$. "
               f"It goes in {how}.", r",\quad ".join(chain))
    s.step("Every factor is prime, so the factorization is complete.",
           rf"{n} = " + r" \times ".join(map(str, factors)))
    s.answer(solution, lead="Listed from least to greatest, the answer is")
    return problem, solution, s.done()


@register
@with_variants
def is_prime(min_val=2, max_val=100):
    r"""Is the Number Prime?

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Is $91$ a prime number? Answer yes or no. | no |

    Grade 4 review. A prime has exactly two factors, 1 and itself; the steps
    show a factor, or the divisibility checks up to the square root.
    """
    n = random.randint(min_val, max_val)
    problem = f"Is ${n}$ a prime number? Answer yes or no."
    s = Steps()
    s.step(f"A prime number has exactly two factors: $1$ and itself. "
           f"To decide, look for any other number that divides ${n}$ evenly.")
    solution = "yes" if _primality_steps(s, n) else "no"
    s.answer(solution)
    return problem, solution, s.done()


@register
@with_variants
def is_composite(min_val=2, max_val=100):
    r"""Is the Number Composite?

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Is $91$ a composite number? Answer yes or no. | yes |

    Grade 4 review. A composite number has a factor other than 1 and itself;
    the steps show one, or the divisibility checks up to the square root.
    """
    n = random.randint(min_val, max_val)
    problem = f"Is ${n}$ a composite number? Answer yes or no."
    s = Steps()
    s.step("A composite number has at least one factor other than $1$ and itself. "
           f"Look for a number that divides ${n}$ evenly.")
    solution = "no" if _primality_steps(s, n) else "yes"
    s.answer(solution)
    return problem, solution, s.done()


def _scale(n, d, k):
    """``n/d`` rewritten over ``d*k`` as LaTeX, showing the multiplication."""
    if k == 1:
        return rf"{tex_frac(n, d)} \text{{ (already over }} {d} \text{{)}}"
    return (rf"{tex_frac(n, d)} = \frac{{{n} \times {k}}}{{{d} \times {k}}}"
            rf" = {tex_frac(n * k, d * k)}")


@register
@with_variants
def compare_fractions(min_den=2, max_den=12):
    r"""Compare Two Fractions

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Which symbol makes $\frac{3}{4} \;\square\; \frac{2}{3}$ true? Type >, < or =. | > |

    Grade 4 review: proper fractions with denominators up to ``max_den``,
    compared by rewriting over a common denominator.
    """
    b = random.randint(min_den, max_den)
    d = random.randint(min_den, max_den)
    a = random.randint(1, b - 1)
    c = random.randint(1, d - 1)
    left, right = a * d, c * b
    symbol = ">" if left > right else ("<" if left < right else "=")
    fa, fc = tex_frac(a, b), tex_frac(c, d)
    problem = (
        f"Which symbol makes ${fa} \\;\\square\\; {fc}$ true? "
        "Type >, < or =."
    )
    solution = symbol

    s = Steps()
    if b == d:
        s.step(f"Both fractions have denominator ${b}$, so the one with the "
               "bigger numerator is bigger.")
        na, nc = a, c
    else:
        den = b * d // math.gcd(b, d)
        na, nc = a * (den // b), c * (den // d)
        s.step(f"Rewrite both fractions with a common denominator. "
               f"The least common multiple of ${b}$ and ${d}$ is ${den}$.")
        s.step("Multiply the top and bottom of each fraction by the same number.",
               _scale(a, b, den // b) + r",\qquad " + _scale(c, d, den // d))
    word = {">": "greater than", "<": "less than", "=": "equal to"}[symbol]
    s.step(f"Compare the numerators: ${na}$ is {word} ${nc}$.")
    s.answer(solution, lead=f"So ${fa} {symbol} {fc}$, and the symbol is")
    return problem, solution, s.done()


@register
@with_variants
def factorial(min_n=0, max_n=8):
    r"""Factorial

    | Ex. Problem | Ex. Solution |
    | --- | --- |
    | Evaluate $5!$. | 120 |

    Algebra II review: ``n!`` for small ``n``, including the ``0! = 1``
    convention.
    """
    n = random.randint(min_n, max_n)
    value = math.factorial(n)
    problem = f"Evaluate ${n}!$."
    solution = str(value)

    s = Steps()
    s.step("$n!$ (read \"$n$ factorial\") is the product of every whole number from $n$ down to $1$.")
    if n == 0:
        s.step("By definition $0! = 1$: it is the product of no numbers at all, which is $1$.")
    elif n == 1:
        s.step("The only number from $1$ down to $1$ is $1$, so $1! = 1$.")
    else:
        factors = list(range(n, 0, -1))
        s.step("Write out the product.", rf"{n}! = " + r" \times ".join(map(str, factors)))
        if n > 2:
            work, _ = _running_product(factors[:-1])
            s.step("Multiply from left to right. (The final $\\times 1$ changes nothing.)", work)
        else:
            s.step("Multiply.", r"2 \times 1 = 2")
    s.answer(solution, lead=f"So ${n}! =$")
    return problem, solution, s.done()
