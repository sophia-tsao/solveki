"""How much practice a day's deck asks for, and when an assignment is done.

Pure functions with no database, request, or clock access, like `srs`: callers
(the deck and assignment views) gather the state and persist the results. The
rules were tuned with a day-by-day simulation of teacher assignment patterns and
student types (see DESIGN.md, "Deck sizing").

- Assignment cards: each open assignment spreads its remaining cards over the
  days left until it's due, at least `MIN_SESSION` per topic practised.
- Review cards: a due assignment topic gets `REVIEW_CONSTANT / ease` cards, so
  a topic the student struggles with (low ease) gets more practice.
- A topic that lapsed yesterday is guaranteed a review today.
- The required total is capped at `DAILY_CAP` (the guarantee may go to
  `HARD_CAP`); reviews that don't fit stay due until tomorrow.
- An assignment needs at least its card count `N`, then more while any of its
  topics isn't solid, up to `MAX_CARDS_MULTIPLIER * N`.
- An open assignment's decks hold at most `MAX_CARDS_MULTIPLIER * N` cards over
  its life, on any topic. Its own topics come first; reviews of the student's
  other due topics, most at risk of being forgotten first, use what's left, up
  to `1 - REVIEW_RESERVE` of the extra `N / 2` (`plan_assignment_deck`).
"""
import math

# Fewest cards worth scheduling for a topic in one sitting: with one or two
# cards, a single slip is half the day's evidence.
MIN_SESSION = 4
# Cards for a due review are REVIEW_CONSTANT / ease (8 at the starting ease,
# 15 at the floor).
REVIEW_CONSTANT = 20
# A topic that lapsed yesterday gets at least this many cards today, even when
# the day is otherwise full.
LAPSE_REVIEW_CARDS = 5
# Soft and hard caps on the cards a day's required work may add up to.
DAILY_CAP = 80
HARD_CAP = 100
# A topic still being learned today gets extra cards until it's solid, up to
# this many cards on it in one day.
MAX_TOPIC_CARDS_PER_DAY = 15
# An assignment never asks for more than this multiple of its card count.
MAX_CARDS_MULTIPLIER = 1.5
# Share of an assignment's extra cards (beyond its count) kept for its own
# topics; reviews of the student's other topics may use the rest.
REVIEW_RESERVE = 0.25
# Assignments with no due date are spread over this many days.
DEFAULT_ASSIGNMENT_DAYS = 7
# Finishing an assignment at this accuracy on a topic lifts the topic to at
# least GRADUATION_INTERVAL days ("familiar"), so a student who gets it right
# isn't sent straight back to it the next day.
GRADUATION_ACCURACY = 0.85
GRADUATION_INTERVAL = 6

# Enough practice means at least SOLID_CORRECT right answers (either try) among
# the last SOLID_WINDOW.
SOLID_WINDOW = 4
SOLID_CORRECT = 3


def is_correct(outcome):
    """True for an answer that was right on either try."""
    return outcome in ("correct_first", "correct_second")


def is_enough_today(outcomes):
    """True once a topic being learned has had enough practice for the day.

    At least 3 of the last 4 of today's `outcomes` (oldest first) right — so a
    single right answer is never enough on a new topic.
    """
    return sum(1 for o in outcomes[-SOLID_WINDOW:] if is_correct(o)) >= SOLID_CORRECT


def is_solid(outcomes):
    """True if an assignment topic's answers since it started show it's secure.

    With 4 or more answers, 3 of the last 4 right. With fewer, every one right:
    an assignment spread over many topics may give each only a card or two,
    and a student who gets them all right shouldn't need more than the
    assignment's card count. A topic with no answers yet isn't solid.
    """
    if not outcomes:
        return False
    if len(outcomes) < SOLID_WINDOW:
        return all(is_correct(o) for o in outcomes)
    return is_enough_today(outcomes)


def cards_to_solid(outcomes):
    """The fewest more answers, all right, that would make `outcomes` solid."""
    trial = list(outcomes)
    added = 0
    while not is_solid(trial):
        trial.append("correct_first")
        added += 1
    return added


def max_cards(deck_size):
    """The most cards an assignment of `deck_size` can ask for."""
    return math.ceil(MAX_CARDS_MULTIPLIER * deck_size)


def review_limit(deck_size):
    """Most cards an assignment's decks give to reviews of other topics over its life."""
    return int((max_cards(deck_size) - deck_size) * (1 - REVIEW_RESERVE))


def review_room(deck_size, deck_cards, review_cards_so_far, still_needed):
    """Cards reviews of other topics may still take in an assignment's decks.

    `deck_cards` is the cards its decks hold so far (answered, plus reviews
    planned but not answered yet), `review_cards_so_far` the reviews among them,
    and `still_needed` the cards on its own topics it still needs. Those come
    first: reviews get what's left of `max_cards` after them, and no more than
    `review_limit` in all, so a struggling student keeps room to practise.
    """
    flex = max_cards(deck_size) - deck_cards - still_needed
    return max(0, min(flex, review_limit(deck_size) - review_cards_so_far))


def extra_fits(deck_size, deck_cards, review_cards_so_far, still_needed, review):
    """True if an assignment's decks can take one more extra card.

    Never past `max_cards`; a card reviewing another topic (`review`) also
    needs `review_room`. Arguments as for `review_room`, counting every card
    in the decks, answered or not.
    """
    if deck_cards >= max_cards(deck_size):
        return False
    return not review or review_room(deck_size, deck_cards, review_cards_so_far, still_needed) > 0


def budget_spent(deck_size, deck_cards):
    """True once an assignment's decks have no room left for a whole session."""
    return max_cards(deck_size) - deck_cards < MIN_SESSION


def review_urgency(ease, interval, days_overdue, lapsed):
    """Sort key putting the reviews most at risk of being forgotten first.

    A topic that lapsed yesterday leads (it's being relearned), then the most
    overdue relative to its interval (3 days late on a 2-day interval is
    riskier than on a 30-day one), then the lowest ease.
    """
    return (not lapsed, -days_overdue / max(1, interval), ease)


def plan_assignment_deck(share, due, own, cap, room, still_needed):
    """Cards an open assignment's deck needs today: `(own_plan, review_plan)`.

    - `share`: `{topic_id: cards}` of today's share (`assignment_cards`), in
      priority order, less what's already answered today.
    - `due`: `{topic_id: (cards, urgency)}` for the due topics the deck may
      review, `cards` being a review's worth less what's answered today
      (`LAPSE_REVIEW_CARDS` for a lapse, else `MIN_SESSION`).
    - `own`: the assignment's topic ids.
    - `cap`: cards the deck may still hold (`max_cards` less what its decks
      already held); `room`: `review_room`; `still_needed` as there.

    An own topic that's due gets up to a review's worth, which counts toward
    the assignment, so only cards beyond `still_needed` come out of `room`.
    The plan is trimmed to `cap` from its lowest-priority end. Other due
    topics follow, most urgent first, while they fit `room` and `cap`; the
    rest stay due until another day. A topic that doesn't get its full
    count still gets at least `MIN_SESSION` cards, or none (one slip on two
    cards would be half the evidence), unless the deck can't hold a session
    at all.
    """
    plan = {tid: cards for tid, cards in share.items() if cards > 0}
    ordered = sorted(due, key=lambda t: (due[t][1], t))
    floor = min(MIN_SESSION, cap)

    def flex(on_topic):
        return max(0, on_topic - still_needed)

    for tid in ordered:
        want = due[tid][0] - plan.get(tid, 0)
        if tid not in own or want <= 0:
            continue
        total = sum(plan.values())
        extra = min(want, cap - total)
        if extra <= 0 or plan.get(tid, 0) + extra < min(floor, due[tid][0]):
            continue
        room = max(0, room - (flex(total + extra) - flex(total)))
        plan[tid] = plan.get(tid, 0) + extra
    while sum(plan.values()) > cap:
        last = next(reversed(plan))
        cut = plan[last] - (sum(plan.values()) - cap)
        if cut >= floor:
            plan[last] = cut
        else:
            del plan[last]
    reviews = {}
    for tid in ordered:
        if tid in own:
            continue
        cards = min(due[tid][0], room, cap - sum(plan.values()) - sum(reviews.values()))
        if cards <= 0 or cards < min(floor, due[tid][0]):
            continue
        reviews[tid] = cards
        room -= cards
    return plan, reviews


def cards_needed(deck_size, answered, outcomes_by_topic):
    """How many cards an assignment needs in total, given progress so far.

    `outcomes_by_topic` maps each assigned topic to its answers since the
    assignment started (oldest first). Before `deck_size` cards it's just
    `deck_size`; after that it's the answers so far plus what the shakiest topic
    still needs to become solid, never above `max_cards`.
    """
    if answered < deck_size:
        return deck_size
    extra = max((cards_to_solid(o) for o in outcomes_by_topic.values()), default=0)
    return min(max_cards(deck_size), answered + extra)


def is_complete(deck_size, answered, outcomes_by_topic):
    """`(done, max_reached)` for an assignment's progress.

    Done once `deck_size` cards are answered and every topic is solid, or once
    `max_cards` are answered regardless; `max_reached` marks the second case.
    """
    if answered >= max_cards(deck_size):
        all_solid = all(is_solid(o) for o in outcomes_by_topic.values())
        return True, not all_solid
    if answered >= deck_size and all(is_solid(o) for o in outcomes_by_topic.values()):
        return True, False
    return False, False


def completion_pct(answered, needed, previous=0):
    """Whole-number percent done, never lower than `previous`.

    The cards needed can rise when a student misses, so the raw ratio could
    drop; the shown percentage pauses instead.
    """
    if needed <= 0:
        return max(previous, 100)
    return max(previous, min(100, (100 * answered) // needed))


def review_cards(ease):
    """Cards for one due review of a topic at `ease`."""
    return max(MIN_SESSION, round(REVIEW_CONSTANT / ease))


def assignment_cards(remaining, days_left, topic_ids):
    """Split one assignment's share of today's cards across its topics.

    `remaining` is the cards it still needed at the start of today, `days_left`
    the days until it's due counting today (at least 1), and `topic_ids` its
    topics in priority order. Today's share is spread evenly over as few topics
    as keep every one at `MIN_SESSION` or more; the rest wait for another day.
    Returns `{topic_id: cards}`.
    """
    if remaining <= 0 or not topic_ids:
        return {}
    share = max(MIN_SESSION, math.ceil(remaining / max(1, days_left)))
    count = max(1, min(len(topic_ids), share // MIN_SESSION))
    base, extra = divmod(share, count)
    return {tid: base + (1 if i < extra else 0) for i, tid in enumerate(topic_ids[:count])}


def plan_required(assignment_plans, due_reviews, lapsed, cap=DAILY_CAP, hard_cap=HARD_CAP):
    """Cards each topic needs today for assignments, reviews and lapses.

    - `assignment_plans`: `{topic_id: cards}` from `assignment_cards`, summed
      over the student's open assignments. Always scheduled.
    - `due_reviews`: `{topic_id: ease}` for due topics that get `review_cards`.
    - `lapsed`: `{topic_id: ease}` for topics that lapsed yesterday, a subset of
      the due ones that's scheduled ahead of the rest.

    A topic both assigned and due gets the larger count, not the sum. Lapsed
    topics get their full review if it fits under `cap`, otherwise
    `LAPSE_REVIEW_CARDS`, and never push the total past `hard_cap`. Other
    reviews fill what's left of `cap`, lowest ease first, scaled down when they
    don't all fit (at least `MIN_SESSION` each); any that still don't fit are
    left out. Returns `{topic_id: cards}`.
    """
    plan = dict(assignment_plans)
    for tid, ease in due_reviews.items():
        if tid in plan:
            plan[tid] = max(plan[tid], review_cards(ease))
    others = {
        tid: review_cards(ease) for tid, ease in due_reviews.items()
        if tid not in plan and tid not in lapsed
    }
    for tid in sorted((t for t in lapsed if t not in plan), key=lambda t: (lapsed[t], t)):
        used = sum(plan.values())
        want = review_cards(lapsed[tid])
        cards = want if used + want <= cap else LAPSE_REVIEW_CARDS
        if used + cards <= hard_cap:
            plan[tid] = cards
    budget = cap - sum(plan.values())
    wanted = sum(others.values())
    if not others or wanted <= budget:
        plan.update(others)
        return plan
    scale = max(budget, 0) / wanted
    for tid in sorted(others, key=lambda t: (due_reviews[t], t)):
        cards = max(MIN_SESSION, int(others[tid] * scale))
        if cards <= budget:
            plan[tid] = cards
            budget -= cards
    return plan
