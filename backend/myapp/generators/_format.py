"""Shared formatters for typeable generator solutions.

Every Solveki-local generator returns a solution string the student types back
on their keyboard, so answers must avoid LaTeX that can't be typed: no
``\\frac``, ``\\sqrt``, ``\\langle``, ``\\geq``, matrices, or set notation.
These helpers are the single source of truth for rendering the typeable forms
(plain integers, decimals, ``a/b`` fractions, and ``(x, y)`` pairs).

Rounding happens once, at the end: generators compute with exact (or full
float) values and only `num` rounds, for display. A student may round *or*
truncate to the stated place, so `num` can also report the truncated form of
everything it rounds (see `track_rounding`), which the grader accepts too.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from fractions import Fraction

# While `track_rounding` is active: unsigned rounded text -> set of the unsigned
# truncated texts of the values that actually needed rounding to produce it.
_rounding = ContextVar("rounding", default=None)

# Relative float error below this is noise, not a value to truncate.
_NOISE = Decimal("1e-9")


@contextmanager
def track_rounding():
    """Collect how every `num` call inside the block rounded.

    Yields a dict mapping each unsigned rounded text to the set of truncated
    texts it stands for; `truncations` turns that into the alternatives the
    grader accepts.
    """
    record = {}
    token = _rounding.set(record)
    try:
        yield record
    finally:
        _rounding.reset(token)


def truncations(record):
    """``{rounded: truncated}`` for each rounded text with one truncated form.

    A text rounded from two values that truncate differently (``2.667`` from
    2.6666... and from 2.6671) is ambiguous, so it's left out and only the
    rounded form is accepted. Exact values aren't recorded at all, so showing
    an already-rounded number again (``num(Fraction(num(x)))``) changes nothing.
    """
    return {
        rounded: next(iter(cut))
        for rounded, cut in record.items()
        if len(cut) == 1 and next(iter(cut)) != rounded
    }


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
    Inside `track_rounding`, also records the truncated form of a value whose
    rounding changed it.
    """
    exact = _exact_decimal(value)
    step = Decimal(1).scaleb(-places)
    rounded = exact.quantize(step, rounding=ROUND_HALF_UP)
    text = _clean(rounded)
    record = _rounding.get()
    # Float error isn't a value to truncate: 0.49999999999999994 is 0.5.
    if record is not None and abs(exact - rounded) > _NOISE * max(1, abs(exact)):
        cut = _clean(exact.quantize(step, rounding=ROUND_DOWN))
        record.setdefault(text.lstrip("-"), set()).add(cut.lstrip("-"))
    return text


def _clean(value):
    """A Decimal as text with trailing zeros (and ``-0``) dropped."""
    text = f"{value:f}"
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
