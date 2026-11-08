"""Builder for the step-by-step explanation a generator can return.

A generator may return ``(problem, solution, steps)``; ``steps`` is what the
card shows (behind a "See step-by-step solution" toggle) once a student has
missed both attempts. Each step is a dict::

    {"text": "Subtract $3$ from both sides.", "math": "2x = 4"}

``text`` is a sentence with optional inline ``$...$`` LaTeX; ``math`` is an
optional display-mode LaTeX line (no ``$``), usually the equation that results
from the step. Unlike the solution, steps may use any LaTeX (``\\frac``,
``\\sqrt``, ...) — they're rendered, never typed.

Usage::

    s = Steps()
    s.formula("The area of a circle", r"A = \\pi r^2")
    s.substitute(r"A = \\pi (3)^2")
    s.step("Multiply.", r"A \\approx 28.274")
    s.answer(solution, lead="Rounded to the nearest thousandth, the answer is")
    return problem, solution, s.done()
"""
import re

# A word of two or more letters, as in "no solution" — but not "x" or "2x+3".
_WORD = re.compile(r"\b[a-zA-Z]{2,}\b")
# Typed notation that LaTeX would mangle: "%" starts a comment ("68%" shows as
# "68"), and "^(" superscripts only the "(" of "(x-3)^(1/3)".
_NOT_LATEX = re.compile(r"%|\^\(")


def paren(value):
    """`value` as a string, parenthesised if negative: ``-3`` -> ``(-3)``.

    For substituting into an expression, e.g. ``f"{a} - {paren(b)}"``.
    """
    text = str(value)
    return f"({text})" if text.startswith("-") else text


def tex_frac(numerator, denominator):
    """A LaTeX fraction, with any sign pulled out front: ``-\\frac{3}{4}``."""
    n, d = numerator, denominator
    sign = "-" if (str(n).startswith("-")) != (str(d).startswith("-")) else ""
    return f"{sign}\\frac{{{str(n).lstrip('-')}}}{{{str(d).lstrip('-')}}}"


class Steps:
    def __init__(self):
        self._steps = []

    def step(self, text, math=None):
        """Add one step: a sentence, plus an optional display-math line."""
        self._steps.append({"text": text, "math": math})
        return self

    def formula(self, name, latex):
        """Open with the rule being used, e.g. "The volume of a cone is ..."."""
        return self.step(f"{name} is:", latex)

    def substitute(self, latex, text="Substitute the values from the problem."):
        """Show the formula with the problem's numbers plugged in."""
        return self.step(text, latex)

    def answer(self, solution, lead="The answer is"):
        """Close on the solution exactly as the student must type it.

        ``solution`` is the generator's solution string. One that already
        carries ``$`` delimiters (``"$x = -5$ or $x = 2$"``) or is worded
        (``"no solution"``) is used as-is; anything else is wrapped in ``$`` so
        it renders as math. Every explanation ends here — the test suite checks
        the final step states the served answer.
        """
        text = str(solution).strip()
        if "$" not in text and not _WORD.search(text) and not _NOT_LATEX.search(text):
            text = f"${text}$"
        return self.step(f"{lead} {text}.")

    def done(self):
        return list(self._steps)
