"""SuperMemo-2 (SM-2) spaced-repetition scheduling.

This module is the whole SM-2 algorithm and nothing else: pure functions with no
database, request, or clock access, so the scheduling math can be reasoned about
and unit-tested in isolation. Callers (the deck layer) own persistence and dates;
this module only maps (current state, grade) -> (next state) and (state) -> (days
until next review).

State is the SM-2 triple:
  - ease        the ease factor, a multiplier on the interval (starts 2.5)
  - interval    days until the next review
  - repetitions consecutive successful reviews (resets to 0 on a lapse)

Grades follow SM-2's 0-5 quality scale, where q >= 3 is a successful recall and
q < 3 is a lapse. A topic is graded once per day, from all of that day's answers
on it (`grade_day`): the day's accuracy picks the quality, like Anki's answer
buttons, so one slip among several right answers isn't treated as forgetting.
"""

# SM-2 constants.
MIN_EASE = 1.3   # ease floor: below this, intervals stop growing ("ease hell")
INITIAL_EASE = 2.5
PASSING_GRADE = 3  # quality >= this counts as a successful recall

# Maximum interval, in days. SM-2 itself has no cap; this borrows Anki's notion
# of a maximum interval, but not its value: Anki defaults to ~100 years, which
# for a math-practice app would let a mastered topic vanish for good. A 1-year
# cap keeps even well-known topics resurfacing at least annually so the skill is
# refreshed rather than forgotten. Tunable in one place.
MAX_INTERVAL = 365

# Day grading (`grade_day`). Each answer earns credit toward the day's accuracy:
# right first try counts fully, right on the second try half.
CREDIT = {"correct_first": 1.0, "correct_second": 0.5, "incorrect": 0.0}
# Lowest day accuracy for each quality, best first; below the last is quality 0.
# 90%+ is a clean pass (ease up), 75%+ a normal pass (one slip in four cards
# lands here), 60%+ a hard pass, anything lower a lapse.
QUALITY_TIERS = ((0.9, 5), (0.75, 4), (0.6, 3), (0.4, 2), (0.2, 1))
HARD_QUALITY = 3
# A hard pass still counts, but the interval only stretches by this much (and
# at least a day) instead of by the ease factor.
HARD_MULTIPLIER = 1.2
# On a learning day (a new or lapsed topic) only the session's last answers are
# judged, so the misses made while first working it out don't count against it.
LEARNING_TAIL = 5
# On a day that raises ease, the gain is multiplied by first-try-correct answers
# / RECOVERY_DIVISOR, up to MAX_RECOVERY: practising more and getting it right
# recovers a struggling topic's ease faster. Losses are never scaled.
RECOVERY_DIVISOR = 4
MAX_RECOVERY = 3


def update_ease(ease, quality):
    """Return the new ease factor after a review graded `quality` (0-5).

    This is SM-2's ease update, applied on *every* review (pass or lapse) and
    then clamped to the 1.3 floor. Higher quality nudges ease up; lower quality
    pulls it down, so hard-but-correct answers make future intervals grow more
    slowly.
    """
    ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return max(ease, MIN_EASE)


def update(ease, interval, repetitions, quality, early=False):
    """Advance SM-2 state by one review.

    Returns a new `(ease, interval, repetitions)` triple; does not mutate inputs.

    On a successful recall (`quality >= 3`) the interval grows: the first success
    schedules 1 day out, and every later one multiplies the previous interval by
    the ease factor (rounded, and at least one day longer), capped at
    `MAX_INTERVAL` so a mastered topic still resurfaces. That's Anki's ladder
    (graduate at 1 day, then `interval * ease`: 1 -> 3 -> 8 -> 23 days at the
    starting ease) rather than SM-2's fixed 6-day second step, which jumps too far
    for a topic just learned. On a lapse (`quality < 3`) the item is reset to be
    relearned — repetitions to 0 and interval to 1 day (due tomorrow) — so a topic
    answered wrong resurfaces quickly. The ease factor is updated in both cases.

    `early` marks a review of an item that isn't due yet (the deck fills with
    not-yet-due topics). SM-2 assumes items are reviewed only when due, so an
    early success leaves the state unchanged rather than growing the interval —
    otherwise daily practice would stack the ladder a rung per day. An early
    lapse still resets: a miss is evidence of forgetting whenever it happens.
    """
    if early and quality >= PASSING_GRADE:
        return ease, interval, repetitions
    new_ease = update_ease(ease, quality)
    if quality >= PASSING_GRADE:
        if repetitions == 0:
            new_interval = 1
        else:
            new_interval = max(interval + 1, round(interval * new_ease))
        new_interval = min(new_interval, MAX_INTERVAL)
        new_repetitions = repetitions + 1
    else:
        new_interval = 1
        new_repetitions = 0
    return new_ease, new_interval, new_repetitions


def accuracy(outcomes):
    """Share of credit earned by `outcomes` (answer outcome strings), 0.0 if none."""
    if not outcomes:
        return 0.0
    return sum(CREDIT.get(o, 0.0) for o in outcomes) / len(outcomes)


def day_quality(day_accuracy):
    """Map a day's accuracy (0-1) to an SM-2 quality via `QUALITY_TIERS`."""
    for floor, quality in QUALITY_TIERS:
        if day_accuracy >= floor:
            return quality
    return 0


def grade_day(ease, interval, repetitions, outcomes, early=False):
    """Advance SM-2 state by one day's answers on a topic.

    `outcomes` is the day's answer outcomes on the topic, oldest first. Returns
    `(ease, interval, repetitions, quality)`; the caller recomputes from the
    day's starting state after every answer, so the day only ever counts as one
    review.

    - The day's accuracy picks the quality (`QUALITY_TIERS`). On a learning day
      (`repetitions == 0`) only the last `LEARNING_TAIL` answers are judged.
    - A hard pass (quality 3) keeps the streak but stretches the interval by
      `HARD_MULTIPLIER` rather than the ease factor.
    - Otherwise this is `update`: Anki's ladder on a pass, a reset on a lapse,
      and an early pass leaves the state unchanged.
    - An ease gain is scaled by the day's first-try-correct volume (see
      `RECOVERY_DIVISOR`).
    """
    judged = outcomes[-LEARNING_TAIL:] if repetitions == 0 else outcomes
    quality = day_quality(accuracy(judged))
    if early and quality >= PASSING_GRADE:
        return ease, interval, repetitions, quality
    new_ease, new_interval, new_repetitions = update(ease, interval, repetitions, quality)
    if new_ease > ease:
        first_correct = sum(1 for o in outcomes if o == "correct_first")
        scale = min(MAX_RECOVERY, max(1.0, first_correct / RECOVERY_DIVISOR))
        new_ease = ease + (new_ease - ease) * scale
    if quality == HARD_QUALITY and repetitions > 0:
        new_interval = min(MAX_INTERVAL, max(interval + 1, round(interval * HARD_MULTIPLIER)))
    return new_ease, new_interval, new_repetitions, quality
