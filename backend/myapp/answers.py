"""Whether a typed answer is the same as a card's solution.

Students type answers by hand, so an answer counts if it's *equivalent* to the
solution, not only character-for-character equal:

- Whitespace and letter case don't matter: "(1,2)" is "(1, 2)", "YES" is "yes".
- Numbers compare by value: "0.5" is "1/2", "42.0" is "42", and "(1/2, -3)" is
  "(0.5, -3)".
- A fraction also matches the rounded decimal it rounds to: "1/3" is "0.333"
  (rounded the platform's way, see `generators._format.num`).
- A typed fraction must be in lowest terms: "6/8" is never "3/4", and "4/1"
  isn't "4".
- A unit after a lone number is optional: "216" is "216 m^2".

Everything that isn't a number must match as text, so "2^8" isn't "256" and
list order matters. Pure functions; `frontend/src/answerMatch.js` mirrors this
for the in-browser diagnostic, and both are tested against the same cases in
`frontend/src/answerCases.json`.
"""
import math
import re
from fractions import Fraction
from math import gcd

from .generators._format import num

# A solution that is one number followed by a unit ("216 m^2", "4.5 cm").
_WITH_UNIT_RE = re.compile(r"^(-?(?:\d+(?:\.\d*)?|\.\d+)(?:/\d+)?)\s*[a-zA-Z]+(?:\^\d)?$")

# A number as typed: an integer or decimal (".5" and "2." included), optionally
# over an integer denominator. Signs stay in the surrounding text, so "-1/2" and
# "-0.5" both read as "-" followed by one number.
_NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:/\d+)?")


def _normalize(text):
    """`text` without whitespace or `$`, lowercased, with a Unicode minus as '-'."""
    return re.sub(r"\s+", "", str(text)).replace("$", "").replace("−", "-").lower()


def _value(token):
    """The exact value of a number token, or None for a zero denominator."""
    numerator, _, denominator = token.partition("/")
    if denominator and int(denominator) == 0:
        return None
    value = Fraction(numerator)
    return value / int(denominator) if denominator else value


def _is_reduced(token):
    """False for a typed fraction that isn't in lowest terms ("6/8", "4/1", "1.5/3")."""
    numerator, slash, denominator = token.partition("/")
    if not slash:
        return True
    if "." in numerator:
        return False
    p, q = int(numerator), int(denominator)
    return q > 1 and gcd(p, q) == 1


def _numbers_match(typed, expected):
    """True if the typed number token is the same number as the expected one."""
    if not _is_reduced(typed):
        return False
    value = _value(typed)
    if value is None:
        return False
    if value == _value(expected):
        return True
    # A fraction for an answer that was rounded: right if it rounds to it.
    return "/" in typed and "/" not in expected and num(value) == expected


def answer_matches(answer, solution):
    """True if `answer` is equivalent to `solution` (see the module docstring)."""
    with_unit = _WITH_UNIT_RE.match(_normalize(solution))
    if with_unit and _matches(answer, with_unit.group(1)):
        return True
    return _matches(answer, solution)


def _matches(answer, solution):
    if answer == solution:
        return True
    try:
        a, s = float(answer), float(solution)
    except ValueError:
        pass
    else:
        if math.isfinite(a) and a == s:
            return True
    typed, expected = _normalize(answer), _normalize(solution)
    if not typed:
        return False
    typed_numbers = _NUMBER_RE.findall(typed)
    expected_numbers = _NUMBER_RE.findall(expected)
    if len(typed_numbers) != len(expected_numbers):
        return False
    if _NUMBER_RE.split(typed) != _NUMBER_RE.split(expected):
        return False
    return all(_numbers_match(t, e) for t, e in zip(typed_numbers, expected_numbers))
