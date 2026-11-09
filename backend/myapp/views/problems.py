import itertools
import logging
import re

logger = logging.getLogger(__name__)

# NOTE: ``mathgenerator`` and the local ``..generators`` package are imported
# lazily inside the functions below, not at module top level. Importing them
# costs ~1s+, and — inflated by Cloud Run's throttled single vCPU during a cold
# start — that import is the single largest slice of cold-start latency. Only
# problem generation needs them; the URLconf load that every request (including
# the trivial /auth/me/) pays for does not. Deferring the import moves that cost
# off the cold-start path and onto the first /deck/ request.

# Matches an *over-precise* decimal (4+ fractional digits) anywhere in a string,
# e.g. the ``523.5987755982989`` inside ``"523.5987755982989 m^3"``. Decimals
# already at three or fewer places are left exactly as written, so a generator's
# intentional formatting (``5.0*10^4``, ``46.7``) is never disturbed — only the
# long floats some library generators emit get normalised. A leading sign is
# captured so negatives round correctly.
_LONG_DECIMAL_RE = re.compile(r"-?\d+\.\d{4,}")

# An unsigned number in a solution, such as the 2.667 in "(1.5, -2.667)".
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

# Most truncated variants kept for one solution (each rounded number in it can
# be typed rounded or truncated, so a list of n numbers has up to 2^n - 1).
_MAX_ALTERNATIVES = 63


def _round_decimals(text):
    """Round every over-precise decimal in `text` to the nearest thousandth.

    Operates per-number rather than requiring the whole string to be a single
    float, so answers carrying units or extra words (``"523.5987755982989
    m^3"``) are rounded too — the previous logic ran ``float()`` on the whole
    string and left any unit-suffixed answer at full precision. Only decimals
    with four or more fractional digits are touched (see `_LONG_DECIMAL_RE`);
    each is reformatted via the shared `num` helper (round to 3 places, drop a
    trailing ``.0``). Integers and already-short decimals pass through unchanged.
    """
    from ..generators._format import num as _num  # lazy; see module-top note
    return _LONG_DECIMAL_RE.sub(lambda m: _num(m.group()), text)


def _truncated_alternatives(solution, cuts):
    """Every other way to type `solution` with some rounded numbers truncated.

    `cuts` maps a rounded number's text to its truncated text (see
    `generators._format.truncations`): a student who truncates 2.6666... to
    2.666 instead of rounding to 2.667 is also right. Each rounded number in
    the solution may independently be typed either way.
    """
    parts = _NUMBER_RE.split(solution)
    numbers = _NUMBER_RE.findall(solution)
    choices = [[n, cuts[n]] if n in cuts else [n] for n in numbers]
    alternatives = []
    for combo in itertools.product(*choices):
        if list(combo) == numbers:
            continue
        alternatives.append("".join(
            part + (combo[i] if i < len(combo) else "") for i, part in enumerate(parts)
        ))
        if len(alternatives) >= _MAX_ALTERNATIVES:
            break
    return alternatives


def _make_problem_for_topic(topic):
    """Generate a single problem for one specific topic.

    Returns a dict with 'problem', 'solution', 'alternatives', 'steps', and
    'topic_id', or None if the topic has no usable generator. `alternatives`
    lists other accepted answers: the solution with rounded numbers truncated
    instead (see `_truncated_alternatives`). The `topic_id` ties the stored problem
    back to the topic it came from, so an answer can be attributed to that topic
    for spaced-repetition scheduling (see myapp.srs); it isn't sent to the
    client. `steps` is the generator's step-by-step explanation (see
    generators._steps), or [] for a generator that doesn't provide one; it's
    only sent once the student has used up their attempts.
    """
    name = topic.generator_name
    if not name:
        return None
    import mathgenerator  # lazy; see module-top note
    from ..generators import LOCAL_GENERATORS  # lazy; see module-top note
    from ..generators._format import track_rounding, truncations  # lazy
    # Prefer our own generators, then fall back to the mathgenerator library.
    generator = LOCAL_GENERATORS.get(name) or getattr(mathgenerator, name, None)
    if generator is None:
        # The stored generator name isn't a real generator (e.g. renamed or
        # removed by a library upgrade). Treat it as "no problem available"
        # rather than 500-ing the student. The contract test in
        # test_generators.py exists to catch this before it ships.
        logger.warning("No generator found for name %r; skipping problem", name)
        return None
    # Library generators (and local ones not yet given explanations) return
    # just (problem, solution); ours return (problem, solution, steps).
    with track_rounding() as rounding:
        problem, solution, *rest = generator()
        steps = rest[0] if rest else []
        made = _finish_problem(problem, solution, steps)
    made["alternatives"] = _truncated_alternatives(made["solution"], truncations(rounding))
    made["topic_id"] = topic.id
    return made


def _finish_problem(problem, solution, steps):
    """Normalise a generator's output into the card's problem/solution/steps."""
    # Strip the surrounding LaTeX '$' delimiters so every solution is returned
    # consistently, whether it's an integer, a decimal, or a symbolic answer.
    sol_str = str(solution).strip().replace('$', '').strip()

    # Round every decimal in the solution to the nearest thousandth. This runs
    # per-number, so it also handles answers that carry units or extra text
    # (e.g. "523.5987755982989 m^3"), which a whole-string float() cannot. If
    # rounding actually changed the answer, tell the student to round too, so
    # their typed answer can match the (now-rounded) solution.
    rounded_sol = _round_decimals(sol_str)
    if rounded_sol != sol_str:
        problem = problem.rstrip() + " Round to the nearest thousandth if necessary."
    sol_str = rounded_sol

    # The problem text can also contain unrounded decimals (some library
    # generators embed computed values in the prompt). Round those too so a
    # student never sees a 16-digit decimal anywhere on the card. LaTeX in the
    # problem uses no bare decimal tokens that this would corrupt.
    problem = _round_decimals(problem)
    # The explanation is left as the generator wrote it: its intermediate
    # values are exact (rounding happens only at the end), so rounding them
    # here would be the mid-calculation rounding the steps avoid.
    steps = [{"text": step["text"], "math": step.get("math") or None} for step in steps]

    return {"problem": problem, "solution": sol_str, "steps": steps}
