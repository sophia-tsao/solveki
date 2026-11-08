"""Shared formatters for typeable generator solutions.

Every Solveki-local generator returns a solution string the student types back
on their keyboard, so answers must avoid LaTeX that can't be typed: no
``\\frac``, ``\\sqrt``, ``\\langle``, ``\\geq``, matrices, or set notation.
These helpers are the single source of truth for rendering the typeable forms
(plain integers, decimals, ``a/b`` fractions, and ``(x, y)`` pairs).
"""
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction


def _exact_decimal(value):
    """`value` as a Decimal, without float binary-representation noise."""
    if isinstance(value, Fraction):
        return Decimal(value.numerator) / Decimal(value.denominator)
    if isinstance(value, float):
        # The shortest repr is the number as written: 0.0625, not 0.06249999...
        return Decimal(repr(value))
    return Decimal(value)


def num(value, places=3):
    """Format a number cleanly and typeably.

    Rounds to ``places`` decimals the way a student does — halves round up
    (away from zero), so 1/16 = 0.0625 is 0.063 — then drops trailing zeros so
    an integral result reads as ``8`` rather than ``8.0``. Normalises ``-0`` to
    ``0``. (Python's ``round`` would give 0.062: it rounds halves to even.)
    """
    rounded = _exact_decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    text = f"{rounded:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def frac(numerator, denominator):
    """Render a fraction typeably: ``'n'`` when whole, else reduced ``'p/q'``."""
    fr = Fraction(numerator, denominator)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def frac_from(value):
    """Render a ``Fraction`` (or int) typeably as ``'n'`` or reduced ``'p/q'``."""
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def pair(x, y):
    """Render an ordered pair ``(x, y)`` with each component via :func:`num`."""
    return f"({num(x)}, {num(y)})"
