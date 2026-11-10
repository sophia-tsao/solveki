import datetime
import json
import logging
from collections import Counter, defaultdict

from django.conf import settings as django_settings
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from ..models import (
    Topic, Settings, DailyDeck, TopicReview, DailyTopicGrade, DailyPractice,
    ProficiencySnapshot, StudentAssignment, AssignmentTopic, AssignmentClass,
    AnswerRecord, ProblemReport,
)
from .common import _require_auth
from .problems import _make_problem_for_topic
from .. import practice, srs
from ..answers import answer_matches

logger = logging.getLogger(__name__)

# The answer outcomes the client reports when it advances past a card; each
# earns credit toward the topic's day grade (see `srs.CREDIT`).
_OUTCOMES = frozenset(srs.CREDIT)

# Every stored card has a kind (see `_visible_total`):
#   required - assignment work and due assignment-topic or lapsed reviews,
#              planned at the start of the day (`_required_plan`)
#   pool     - the student's own practice, filling up to `questions_per_day`
#   extra    - added during the day: a topic still being learned, or an
#              assignment that needs more on its last day (`_add_practice`)
# Cards stored before kinds existed read as pool.
_REQUIRED, _POOL, _EXTRA = "required", "pool", "extra"

# Longest time one card can count toward a student's review time. The client
# times each card from when it appears, so a tab left open on a card would
# otherwise log hours of "review"; a generous cap keeps genuine slow work.
_MAX_CARD_SECONDS = 10 * 60

# Wrong answers allowed per card before its solution is revealed. Mirrors the
# client's MAX_ATTEMPTS (MathProblem.jsx).
_MAX_ATTEMPTS = 2


class DeckScope:
    """Which of a student's decks for the day a request is about (see `_request_scope`).

    - the default deck (`assignment_id` None): the student's own practice,
      shown while no assignment is open;
    - an open assignment's deck: that assignment's share of today, plus the
      usual reviews and pool practice up to `questions_per_day`;
    - a closed assignment's deck (`topic_ids` set): pool practice on just its
      topics, to practice it again after it's done.

    Each deck fills up to the student's setting on its own. Answers count the
    same whichever deck they're in: toward the topic's day grade and every
    open assignment on the topic.
    """

    def __init__(self, assignment_id=None, topic_ids=None):
        self.assignment_id = assignment_id
        self.topic_ids = topic_ids


_DEFAULT_SCOPE = DeckScope()


def _scope_for(user, assignment_id, open_rows=None):
    """The `DeckScope` of `assignment_id`'s deck (the default deck for None)."""
    if assignment_id is None:
        return _DEFAULT_SCOPE
    if open_rows is None:
        open_rows = _open_assignments(user)
    if any(row.assignment_id == assignment_id for row, _, _ in open_rows):
        return DeckScope(assignment_id)
    topic_ids = set(
        AssignmentTopic.objects.filter(assignment_id=assignment_id, topic__generator_name__isnull=False)
        .values_list("topic_id", flat=True)
    )
    return DeckScope(assignment_id, topic_ids)


def _request_scope(request):
    """The deck a deck request is for: `(scope, None)`, or `(None, response)` to send instead.

    `?assignment=<id>` picks that assignment's deck, open or closed; it's a 404
    unless the assignment has reached the student. Without it, the deck is the
    one open assignment's, or the default deck when none is open. With several
    open the student has to pick one, so the response lists them (`choose`).
    """
    user = request.user
    raw = request.GET.get("assignment")
    if raw:
        try:
            assignment_id = int(raw)
        except ValueError:
            return None, JsonResponse({"error": "Bad assignment id"}, status=400)
        if not StudentAssignment.objects.filter(student=user, assignment_id=assignment_id).exists():
            return None, JsonResponse({"error": "Assignment not found"}, status=404)
        return _scope_for(user, assignment_id), None
    open_rows = _open_assignments(user)
    if not open_rows:
        return _DEFAULT_SCOPE, None
    if len(open_rows) == 1:
        return _scope_for(user, open_rows[0][0].assignment_id, open_rows), None
    return None, JsonResponse({"choose": _assignment_choices(open_rows)})


def _assignment_choices(open_rows):
    """The open assignments a student picks between, soonest due first (no due date last)."""
    choices = [
        {
            "assignment_id": row.assignment_id,
            "title": row.assignment.title,
            "due_at": due_at.isoformat() if due_at else None,
            "completion_pct": row.completion_pct,
            "cards_answered": row.cards_answered,
        }
        for row, _, due_at in open_rows
    ]
    choices.sort(key=lambda c: (c["due_at"] is None, c["due_at"] or "", c["assignment_id"]))
    return choices


def _scope_assignments(user, scope):
    """The open assignments whose cards `scope`'s deck carries (see `_open_assignments`).

    The default deck carries any that are open (normally none: it's only shown
    while none are); an assignment's deck carries just its own, if it's open.
    """
    rows = _open_assignments(user)
    if scope.assignment_id is None:
        return rows
    return [r for r in rows if r[0].assignment_id == scope.assignment_id]


def _pool_topics(user, scope):
    """The usable topics `scope`'s deck draws pool practice from.

    The student's selected topics, or a closed assignment's own topics.
    """
    if scope.topic_ids is not None:
        return Topic.objects.filter(id__in=scope.topic_ids, generator_name__isnull=False)
    return Topic.objects.filter(selections__user=user, generator_name__isnull=False)

# Cap on a submitted answer's length; nothing typeable is longer than this.
_MAX_ANSWER = 500

# Caps on a problem report's free text, so a client can't store arbitrarily
# large blobs. Generous next to any genuine description or typed answer.
_MAX_REPORT_DETAILS = 2000
_MAX_REPORT_ANSWER = 500


def _client_today(request):
    """The calendar day to treat as "today" for the requesting client.

    The deck resets at the start of each day, but "the day" means the user's
    local day — not the server's. The server clock runs in UTC (see
    settings.TIME_ZONE), so relying on `timezone.localdate()` would only roll
    the deck over at UTC midnight; a user ahead of UTC would keep seeing
    yesterday's (often finished) deck through their whole morning.

    The client sends its local date as `?today=YYYY-MM-DD`. We trust it: the
    only thing a user can affect by lying is when their own practice deck
    resets, which is harmless. If it's missing or malformed we fall back to the
    server's date so the endpoint still works (and existing callers/tests that
    don't send it keep their behaviour).
    """
    raw = request.GET.get("today")
    if raw:
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            logger.warning("Ignoring malformed 'today' param: %r", raw)
    return timezone.localdate()


def _has_topics(user, scope=_DEFAULT_SCOPE):
    """True if `scope`'s deck has at least one usable topic (see `_pool_topics`)."""
    return _pool_topics(user, scope).exists()


def _kind(problem):
    return problem.get("kind", _POOL)


def _deck_size_target(deck, per_day):
    """How many cards the deck should show at `per_day` (before capping to what's stored).

    Everything up to the last required or extra card, and at least `per_day`
    cards plus one per extra card (extras come on top of the student's
    setting). Pool cards are always stored after the required ones they were
    built with, so only unanswered pool cards at the end fall outside this.
    """
    extra = 0
    last = 0
    for i, problem in enumerate(deck.problems):
        kind = _kind(problem)
        if kind != _POOL:
            last = i + 1
        if kind == _EXTRA:
            extra += 1
    return max(per_day + extra, last)


def _visible_total(user, deck):
    """How many of the deck's stored cards today's practice shows.

    All required and extra cards, plus pool cards up to `questions_per_day`
    (see `_deck_size_target`). Lowering the setting mid-day hides only
    unanswered pool cards at the end, and reads as finished if the student has
    already answered that many. Hiding is display-only; raising the setting
    again shows the stored cards without regenerating them.
    """
    per_day = Settings.load(user).questions_per_day
    return min(len(deck.problems), _deck_size_target(deck, per_day))


def _open_assignments(user, now=None):
    """The user's unfinished assignments that still take cards, with their topics.

    Returns `[(student_assignment, topic_ids, due_at)]`: the assignment's topics
    that have a generator, in the order the teacher added them, and its due date
    for the student's class (or None). An assignment past its due date that
    doesn't allow late work is left out: its progress is frozen. One that
    reached the student but is still marked not started (assigning normally
    starts it) counts as open too, so it can be begun from the practice page.
    """
    now = now or timezone.now()
    rows = list(
        StudentAssignment.objects.filter(student=user)
        .exclude(status=StudentAssignment.COMPLETED)
        .select_related("assignment")
    )
    if not rows:
        return []
    ids = [r.assignment_id for r in rows]
    topics = defaultdict(list)
    for aid, tid in (
        AssignmentTopic.objects.filter(assignment_id__in=ids, topic__generator_name__isnull=False)
        .order_by("id").values_list("assignment_id", "topic_id")
    ):
        topics[aid].append(tid)
    dues = {
        (aid, cid): due
        for aid, cid, due in AssignmentClass.objects.filter(assignment_id__in=ids)
        .values_list("assignment_id", "classroom_id", "due_at")
    }
    out = []
    for row in rows:
        due_at = dues.get((row.assignment_id, row.classroom_id))
        if due_at and due_at < now and not row.assignment.allow_late:
            continue
        out.append((row, topics[row.assignment_id], due_at))
    return out


def _outcomes_since(user, topic_ids, since):
    """Map each of `topic_ids` to the user's answer outcomes on it since `since`, oldest first."""
    out = {tid: [] for tid in topic_ids}
    rows = AnswerRecord.objects.filter(user=user, topic_id__in=topic_ids)
    if since is not None:
        rows = rows.filter(created_at__gte=since)
    for tid, outcome in rows.order_by("created_at", "id").values_list("topic_id", "outcome"):
        out[tid].append(outcome)
    return out


def _days_left(row, due_at, today):
    """Days the assignment's remaining cards are spread over, counting today (at least 1).

    Just today once the student chose to finish it today (`finish_on`).
    """
    if row.finish_on is not None and row.finish_on >= today:
        return 1
    if due_at is not None:
        return max(1, (timezone.localdate(due_at) - today).days + 1)
    started = timezone.localdate(row.started_at) if row.started_at else today
    return max(1, practice.DEFAULT_ASSIGNMENT_DAYS - (today - started).days)


def _count_assignment_card(user, topic_id, today):
    """Count an answered card on `topic_id` toward the user's open assignments that include it.

    Called after the card's `AnswerRecord` is written. Updates each matching
    assignment's cards needed and completion percentage, and completes it once
    the student is solid after its card count, or at its maximum (see
    `practice.is_complete`). Completing it lifts each topic answered well
    enough to "familiar" (`_graduate_topic`).
    """
    now = timezone.now()
    for row, topic_ids, due_at in _open_assignments(user, now):
        if topic_id not in topic_ids:
            continue
        outcomes = _outcomes_since(user, topic_ids, row.started_at)
        size = row.assignment.deck_size
        row.cards_answered += 1
        row.cards_needed = practice.cards_needed(size, row.cards_answered, outcomes)
        done, max_reached = practice.is_complete(size, row.cards_answered, outcomes)
        if done:
            row.status = StudentAssignment.COMPLETED
            row.completed_at = now
            row.completion_pct = 100
            row.max_reached = max_reached
            row.late = bool(due_at and due_at < now)
        else:
            row.completion_pct = practice.completion_pct(
                row.cards_answered, row.cards_needed, row.completion_pct
            )
        row.save(update_fields=[
            "cards_answered", "cards_needed", "completion_pct", "status",
            "completed_at", "max_reached", "late",
        ])
        if done:
            for tid, topic_outcomes in outcomes.items():
                if topic_outcomes and srs.accuracy(topic_outcomes) >= practice.GRADUATION_ACCURACY:
                    _graduate_topic(user, tid, today)
            logger.info(
                "User %s completed assignment %s after %d cards%s",
                user.id, row.assignment_id, row.cards_answered,
                " (max reached)" if max_reached else "",
            )


def _graduate_topic(user, topic_id, today):
    """Lift a topic to at least `practice.GRADUATION_INTERVAL` days after a good assignment.

    If the topic was answered today, the lift is stored on today's grade so
    regrading from later answers keeps it; otherwise it's applied to the
    schedule directly.
    """
    grade = DailyTopicGrade.objects.filter(user=user, topic_id=topic_id, date=today).first()
    if grade is not None:
        grade.floor_interval = practice.GRADUATION_INTERVAL
        grade.save(update_fields=["floor_interval"])
        _grade_topic(user, topic_id, today)
        return
    review = TopicReview.objects.filter(user=user, topic_id=topic_id).first()
    if review is None or review.interval >= practice.GRADUATION_INTERVAL:
        return
    review.interval = practice.GRADUATION_INTERVAL
    review.repetitions = max(review.repetitions, 2)
    review.due_date = today + datetime.timedelta(days=practice.GRADUATION_INTERVAL)
    review.save(update_fields=["interval", "repetitions", "due_date"])


# Proficiency bands, keyed off a topic's SM-2 `interval` (days until next review).
# These thresholds mirror the frontend's `intervalLevel` (TopicProgress.jsx) so
# the donut, the teacher views, and the historical snapshots all bucket topics
# the same way. A never-reviewed topic has interval 0 and lands in "new".
def _interval_band(interval):
    if interval <= 1:
        return "new"
    if interval < 6:
        return "learning"
    if interval < 21:
        return "familiar"
    return "proficient"


def _snapshot_proficiency(user, today):
    """Upsert today's `ProficiencySnapshot` for `user` from current SM-2 state.

    Counts the user's currently-selected, usable topics by proficiency band so
    the teacher's familiarity-over-time charts have a per-day data point. Cheap:
    one query for the selected topics, one for their reviews, then a single
    upsert. Called on active days (deck load and after grading); days the student
    isn't active simply have no row and are forward-filled by readers.
    """
    topics = list(
        Topic.objects.filter(
            selections__user=user, generator_name__isnull=False
        ).values_list("id", flat=True)
    )
    if not topics:
        # No usable selection: record an empty snapshot so a day the student
        # cleared their topics still reads as "0 topics" rather than carrying
        # forward a stale mix.
        ProficiencySnapshot.objects.update_or_create(
            user=user, date=today,
            defaults={"new": 0, "learning": 0, "familiar": 0, "proficient": 0, "total": 0},
        )
        return
    intervals = dict(
        TopicReview.objects.filter(user=user, topic_id__in=topics)
        .values_list("topic_id", "interval")
    )
    counts = {"new": 0, "learning": 0, "familiar": 0, "proficient": 0}
    for topic_id in topics:
        counts[_interval_band(intervals.get(topic_id, 0))] += 1
    ProficiencySnapshot.objects.update_or_create(
        user=user, date=today,
        defaults={**counts, "total": len(topics)},
    )


def _effective_due_dates(user, topics, today):
    """Map each topic id to its effective SM-2 due date.

    Reads each topic's `TopicReview.due_date` (written by the grading step) but
    never computes it — scheduling math lives in myapp.srs. A topic never
    practiced has no `TopicReview` row (or a null `due_date`); it's treated as
    due *today*, so new topics enter the rotation promptly rather than being
    deferred. Shared by `_ordered_topics` (ordering) and `_weighted_topic_plan`
    (how many slots a topic gets), so both read one consistent notion of "due".
    """
    reviews = {
        r.topic_id: r
        for r in TopicReview.objects.filter(user=user, topic__in=topics)
    }
    due = {}
    for topic in topics:
        review = reviews.get(topic.id)
        if review is None or review.due_date is None:
            due[topic.id] = today
        else:
            due[topic.id] = review.due_date
    return due


def _ordered_topics(user, today, scope=_DEFAULT_SCOPE):
    """The user's selected, usable topics ordered by spaced-repetition priority.

    This is the one place that decides the *order* topics are reviewed in; the
    deck helpers route through it so the ordering rule lives in a single,
    testable spot.

    A single sort on each topic's effective due date yields the whole policy:

    - Due first, most overdue first (Option A). A topic never reviewed is
      treated as due today (see `_effective_due_dates`), so new topics enter the
      rotation promptly rather than being deferred.
    - Next-soonest after that (Option 2). Not-yet-due topics have a future
      `due_date`, so they sort after everything already due — they're only
      reached once the due topics run out.

    Ties break by topic id for a stable, deterministic order (no reliance on DB
    row order). Returns every usable selected topic (a Topic list, possibly
    empty); callers slice or cycle it to the size they need. A closed
    assignment's deck orders its own topics instead (see `_pool_topics`).
    """
    topics = list(_pool_topics(user, scope))
    due = _effective_due_dates(user, topics, today)
    topics.sort(key=lambda t: (due[t.id], t.id))
    return topics


def _select_deck_topics(user, today, count, exclude=()):
    """The next `count` distinct topics to review, in due order, skipping `exclude`.

    A thin slice over `_ordered_topics`. `exclude` is a set/iterable of topic
    ids already in the deck, so callers topping up a deck get *fresh* topics
    first (variety before repeats). Returns 0..count Topic objects; empty only
    when the user has no usable topic selected outside `exclude`.
    """
    if count <= 0:
        return []
    exclude = set(exclude)
    return [t for t in _ordered_topics(user, today) if t.id not in exclude][:count]


def _deck_topic_ids(deck):
    """Source topic ids of a deck's stored problems, skipping any that lack one.

    Problems stored before topic attribution was added (or by a client that
    predates it) have no `topic_id`; they're simply omitted rather than crashing
    a top-up. The result is used only to prefer fresh topics when topping up, so
    a missing id degrades to "might repeat this topic", never an error.
    """
    return _deck_topic_ids_of(deck.problems)


def _deck_topic_ids_of(problems):
    return [p["topic_id"] for p in problems if "topic_id" in p]


def _due_weight(due_date, today):
    """How many deck slots a topic should compete for, by how overdue it is.

    This is the SM-2 signal expressed as *dose within a day* rather than only as
    ordering: a topic that's due (or overdue) should occupy more of today's deck
    than one whose next review is still days away. The weight rises with
    overdueness and falls as the due date recedes into the future, and is
    continuous at "due today" (both branches give 1):

    - due today or overdue by N days -> weight N + 1 (1, 2, 3, ...)
    - due in N days                  -> weight 1/(N + 1) (1/2, 1/3, ...)

    Weights are relative; only their ratios matter to the allocation below.
    """
    days_overdue = (today - due_date).days
    if days_overdue >= 0:
        return float(days_overdue + 1)
    return 1.0 / (1 - days_overdue)


def _weighted_slot_counts(rotation, due, count, today):
    """Split `count` deck slots across `rotation` topics, weighted by due priority.

    Every topic gets one slot first (a variety floor: every selected topic still
    appears in the deck), then the *remaining* slots are handed out in proportion
    to each topic's `_due_weight`, so an overdue topic takes a larger share than
    one that isn't due yet. The leftover from integer rounding goes to the
    largest fractional remainders (the standard largest-remainder method), which
    keeps the allocation deterministic and summing to exactly `count`.

    When there are at least `count` topics no repeats are needed, so the first
    `count` (already in due order) simply get one slot each and weighting is moot.
    Returns {topic_id: slot_count} summing to min(count, len(rotation)*...) —
    exactly `count` whenever any topic is present.
    """
    n = len(rotation)
    if n >= count:
        return {t.id: 1 for t in rotation[:count]}

    remaining = count - n  # slots left after the one-each variety floor
    weights = {t.id: _due_weight(due[t.id], today) for t in rotation}
    total = sum(weights.values())
    exact = {t.id: remaining * weights[t.id] / total for t in rotation}
    floors = {tid: int(v) for tid, v in exact.items()}
    leftover = remaining - sum(floors.values())
    # Hand the rounding leftover to the largest remainders; stable sort keeps
    # ties in due order (rotation order), so the allocation is deterministic.
    by_remainder = sorted(
        rotation, key=lambda t: exact[t.id] - floors[t.id], reverse=True
    )
    for t in by_remainder[:leftover]:
        floors[t.id] += 1
    return {t.id: 1 + floors[t.id] for t in rotation}


def _generate_problems(user, count, today, existing=(), scope=_DEFAULT_SCOPE):
    """Generate exactly `count` problems for the deck, weighted by due priority.

    Distinct topics come first, most-due first (so a fresh or topped-up deck has
    as much variety as the user's topic set allows). When there are fewer usable
    topics than `count`, topics repeat to fill the deck — but not evenly: slots
    are allocated by `_weighted_slot_counts`, so a topic that's due or overdue
    occupies more of the deck than one whose next review is still days out. This
    keeps the deck full (SM-2 alone would leave a 2-topic user with one due card)
    while still reflecting SM-2's core signal: practice the due thing more.
    `existing` is the topic ids already in the deck; those topics are placed last
    within the rotation, so a top-up adds new topics before repeating any.

    Each problem records its source topic id (see `_make_problem_for_topic`), so
    a repeated topic yields a different generated problem but is still
    attributable for scheduling. Returns a list of up to `count` problems; fewer
    only if no topics are usable (empty) or every candidate topic's generator is
    broken.
    """
    if count <= 0:
        return []
    ordered = _ordered_topics(user, today, scope)
    if not ordered:
        return []
    # Prefer topics not already in the deck, preserving due order within each
    # group, so top-ups add variety before repeating.
    existing = set(existing)
    fresh = [t for t in ordered if t.id not in existing]
    repeats = [t for t in ordered if t.id in existing]
    rotation = fresh + repeats

    due = _effective_due_dates(user, rotation, today)
    counts = _weighted_slot_counts(rotation, due, count, today)
    # Emit the planned slots in due order, one topic per pass, so a topic's
    # repeats are spread through the deck and the most-due topic leads.
    sequence = []
    left = dict(counts)
    while len(sequence) < sum(counts.values()):
        for topic in rotation:
            if left.get(topic.id, 0) > 0:
                sequence.append(topic)
                left[topic.id] -= 1

    problems = []
    broken = set()
    for planned in sequence:
        # Try the planned topic; if its generator is broken, fall back to any
        # other working topic so one dud skews toward the rest rather than
        # short-decking. `broken` caches duds (a missing generator is a stable
        # property of a topic) so we never re-attempt them.
        problem = None
        for topic in [planned] + [t for t in rotation if t.id != planned.id]:
            if topic.id in broken:
                continue
            made = _make_problem_for_topic(topic)
            if made is None:
                broken.add(topic.id)
                continue
            problem = made
            break
        if problem is None:
            break  # every topic's generator is broken; return what we have
        problems.append(problem)
    return problems


def _required_plan(user, today, scope=_DEFAULT_SCOPE):
    """Cards each topic still needs today for assignments, reviews and lapses.

    Gathers the inputs for `practice.plan_required`:

    - each open assignment's share of today (`practice.assignment_cards`), its
      topics ordered shakiest first (not solid, then lowest ease);
    - due reviews of the student's assignment topics, from any assignment;
    - selected topics that lapsed yesterday.

    Cards already answered on a topic today are subtracted, so rebuilding the
    deck mid-day doesn't ask for them again. Returns `{topic_id: cards}` in
    priority order: assignment topics first, then lapses, then reviews. Topics
    outside assignments otherwise come only from the pool (`questions_per_day`).

    Only the assignments `scope`'s deck carries count (`_scope_assignments`).
    A closed assignment's deck has no required work: it's all pool practice on
    the assignment's topics.
    """
    if scope.topic_ids is not None:
        return {}
    answered_today = Counter(
        AnswerRecord.objects.filter(user=user, date=today).values_list("topic_id", flat=True)
    )
    open_rows = _scope_assignments(user, scope)
    all_topic_ids = {tid for _, tids, _ in open_rows for tid in tids}
    eases = dict(
        TopicReview.objects.filter(user=user, topic_id__in=all_topic_ids).values_list("topic_id", "ease")
    )
    assignment_plans = Counter()
    for row, topic_ids, due_at in open_rows:
        if not topic_ids:
            continue
        outcomes = _outcomes_since(user, topic_ids, row.started_at)
        needed = row.cards_needed or row.assignment.deck_size
        today_rows = AnswerRecord.objects.filter(user=user, date=today, topic_id__in=topic_ids)
        if row.started_at is not None:
            today_rows = today_rows.filter(created_at__gte=row.started_at)
        remaining = max(0, needed - row.cards_answered) + today_rows.count()
        ordered = sorted(
            topic_ids,
            key=lambda t: (practice.is_solid(outcomes[t]), eases.get(t, srs.INITIAL_EASE), t),
        )
        # A card counts toward every open assignment on its topic, so two
        # assignments sharing a topic need the larger share, not both.
        for tid, cards in practice.assignment_cards(remaining, _days_left(row, due_at, today), ordered).items():
            assignment_plans[tid] = max(assignment_plans[tid], cards)

    selected = set(
        Topic.objects.filter(selections__user=user, generator_name__isnull=False)
        .values_list("id", flat=True)
    )
    assigned = set(
        AssignmentTopic.objects.filter(assignment__student_assignments__student=user)
        .values_list("topic_id", flat=True)
    )
    due = {
        tid: (ease, reps)
        for tid, ease, reps in TopicReview.objects.filter(
            user=user, topic_id__in=selected | set(assignment_plans), due_date__lte=today
        ).values_list("topic_id", "ease", "repetitions")
    }
    failed_yesterday = set(
        DailyTopicGrade.objects.filter(
            user=user, date=today - datetime.timedelta(days=1),
            applied_quality__lt=srs.PASSING_GRADE,
        ).values_list("topic_id", flat=True)
    )
    lapsed = {
        tid: ease for tid, (ease, reps) in due.items()
        if tid in failed_yesterday and tid in selected and reps == 0
    }
    due_reviews = {tid: ease for tid, (ease, _) in due.items() if tid in assigned}
    due_reviews.update(lapsed)
    plan = practice.plan_required(dict(assignment_plans), due_reviews, lapsed)
    return {
        tid: cards - answered_today[tid]
        for tid, cards in plan.items() if cards > answered_today[tid]
    }


def _required_problems(plan):
    """Generate the cards for a `_required_plan`, one topic per pass so repeats spread out.

    A topic whose generator is broken is skipped rather than replaced: these
    cards are tied to specific topics.
    """
    topics = {
        t.id: t for t in Topic.objects.filter(id__in=plan, generator_name__isnull=False)
    }
    left = {tid: cards for tid, cards in plan.items() if tid in topics}
    problems = []
    while any(left.values()):
        for tid in list(left):
            if left[tid] <= 0:
                continue
            left[tid] -= 1
            problem = _make_problem_for_topic(topics[tid])
            if problem is None:
                left[tid] = 0
                continue
            problem["kind"] = _REQUIRED
            problems.append(problem)
    return problems


def _build_cards(user, today, kept, scope=_DEFAULT_SCOPE):
    """The cards that follow `kept` (already answered) in today's deck.

    The required work comes first, then pool practice filling the deck up to
    `questions_per_day`, preferring topics not already in it.
    """
    required = _required_problems(_required_plan(user, today, scope))
    # Extra cards come on top of the setting (see `_deck_size_target`).
    kept_extra = sum(1 for p in kept if _kind(p) == _EXTRA)
    pool_count = Settings.load(user).questions_per_day + kept_extra - len(kept) - len(required)
    existing = _deck_topic_ids_of(kept + required)
    pool = _generate_problems(user, pool_count, today, existing=existing, scope=scope)
    for problem in pool:
        problem["kind"] = _POOL
    return required + pool


def _record_practice(user, today):
    """Update the durable per-day practice record after a deck advance.

    Stores how many problems the student has stepped past today (`answered`) and
    the display size (`total`, matching `_deck_payload`) summed over the decks
    they've opened today, so the dashboard calendar can later report completed /
    partial for the day even after the `DailyDeck` rows are pruned. A row is
    created on the first advance of the day, so a day with no row means the
    student never practiced.
    """
    total = answered = 0
    for deck in DailyDeck.objects.filter(user=user, date=today):
        deck_total = _visible_total(user, deck)
        total += deck_total
        answered += min(deck.current_index, deck_total)
    DailyPractice.objects.update_or_create(
        user=user, date=today,
        defaults={"answered": answered, "total": total},
    )


def _grade_topic(user, topic_id, today):
    """Regrade a topic's SM-2 schedule from all of today's answers on it.

    Called after each answer's `AnswerRecord` is written. The first answer of
    the day snapshots the topic's state (and whether it was early, i.e. not due
    yet); every answer then recomputes the schedule from that snapshot and the
    day's answers so far with `srs.grade_day`, so the day counts as exactly one
    review however many cards the topic had. An early pass leaves the schedule,
    due date included, as it was that morning. A lift from finishing an
    assignment (`floor_interval`) is kept.
    """
    outcomes = list(
        AnswerRecord.objects.filter(user=user, topic_id=topic_id, date=today)
        .order_by("created_at", "id").values_list("outcome", flat=True)
    )
    if not outcomes:
        return
    review, _ = TopicReview.objects.get_or_create(user=user, topic_id=topic_id)
    grade = DailyTopicGrade.objects.filter(user=user, topic_id=topic_id, date=today).first()
    if grade is None:
        grade = DailyTopicGrade.objects.create(
            user=user, topic_id=topic_id, date=today, applied_quality=0,
            snapshot_ease=review.ease, snapshot_interval=review.interval,
            snapshot_repetitions=review.repetitions, snapshot_due_date=review.due_date,
            early=review.due_date is not None and review.due_date > today,
        )
    ease, interval, repetitions, quality = srs.grade_day(
        grade.snapshot_ease, grade.snapshot_interval, grade.snapshot_repetitions,
        outcomes, early=grade.early,
    )
    if grade.early and quality >= srs.PASSING_GRADE:
        due_date = grade.snapshot_due_date
    else:
        due_date = today + datetime.timedelta(days=interval)
    if grade.floor_interval and interval < grade.floor_interval:
        interval = grade.floor_interval
        repetitions = max(repetitions, 2)
        due_date = today + datetime.timedelta(days=interval)
    if grade.applied_quality != quality:
        grade.applied_quality = quality
        grade.save(update_fields=["applied_quality"])
    review.ease = ease
    review.interval = interval
    review.repetitions = repetitions
    review.due_date = due_date
    review.save(update_fields=["ease", "interval", "repetitions", "due_date"])
    logger.info(
        "Graded topic %s for user %s: %d answers, q=%d -> interval=%d, due %s",
        topic_id, user.id, len(outcomes), quality, interval, review.due_date,
    )


def _add_practice(user, deck, topic_id, today, scope=_DEFAULT_SCOPE):
    """Add one more card on `topic_id` after an answer, if today's practice on it isn't enough.

    Three cases call for one:

    - the topic started today new or lapsed and hasn't had enough practice yet
      (`practice.is_enough_today`: 3 of its last 4 answers today right), with
      fewer than `MAX_TOPIC_CARDS_PER_DAY` cards on it today;
    - today's answers on a known topic grade below a normal pass (a lapse or a
      hard pass) on fewer than `practice.MIN_SESSION` cards: one slip on a
      lone card shouldn't reset a topic or cost it ease, so the student gets
      more cards to show it was a slip (more misses still count);
    - it's in the deck's open assignment (`_scope_assignments`), due today, and
      that still needs more cards than the student has answered.

    Only when no unanswered card on the topic is left, and the deck is under
    `practice.DAILY_CAP`. The card goes one place after the next card, so the
    student doesn't see the topic twice in a row unless nothing else is left.
    """
    if any(p.get("topic_id") == topic_id for p in deck.problems[deck.current_index:]):
        return
    if _visible_total(user, deck) >= practice.DAILY_CAP:
        return
    outcomes = list(
        AnswerRecord.objects.filter(user=user, topic_id=topic_id, date=today)
        .order_by("created_at", "id").values_list("outcome", flat=True)
    )
    grade = DailyTopicGrade.objects.filter(user=user, topic_id=topic_id, date=today).first()
    learning = (
        grade is not None and grade.snapshot_repetitions == 0
        and not practice.is_enough_today(outcomes)
        and len(outcomes) < practice.MAX_TOPIC_CARDS_PER_DAY
    )
    confirming = (
        grade is not None and grade.snapshot_repetitions > 0
        and grade.applied_quality <= srs.HARD_QUALITY
        and len(outcomes) < practice.MIN_SESSION
    )
    finishing = any(
        topic_id in topic_ids and _days_left(row, due_at, today) == 1
        and row.cards_needed > row.cards_answered
        for row, topic_ids, due_at in _scope_assignments(user, scope)
    )
    if not (learning or confirming or finishing):
        return
    topic = Topic.objects.filter(id=topic_id, generator_name__isnull=False).first()
    problem = _make_problem_for_topic(topic) if topic else None
    if problem is None:
        return
    problem["kind"] = _EXTRA
    deck.problems.insert(min(len(deck.problems), deck.current_index + 1), problem)
    deck.save(update_fields=["problems"])


def _get_or_create_today_deck(user, today, scope=_DEFAULT_SCOPE):
    """Return the user's deck for today in `scope`, creating a fresh one if none exists.

    `today` is the client's local calendar day (see `_client_today`), so the
    deck resets at the user's midnight rather than the server's UTC midnight.

    Any deck from a previous day (for this user) is discarded so a new day
    yields new problems: the day's required work (`_required_plan`) followed by
    pool practice up to `questions_per_day` (`_build_cards`). An existing deck
    whose pool falls short of the setting is topped up with pool cards
    (appending only, so progress is preserved). This heals a deck that was built
    before any topics were selected (empty) as well as one left short by a topic
    change earlier in the day — the latter is why the deck must never be
    reported as "finished" at a smaller size than the user's setting.
    """
    deck = DailyDeck.objects.filter(user=user, date=today, assignment_id=scope.assignment_id).first()
    if deck is None:
        # The first deck of a new day, or another of today's decks opened for
        # the first time: clear out this user's stale decks and build it.
        DailyDeck.objects.filter(user=user).exclude(date=today).delete()
        problems = _build_cards(user, today, [], scope)
        logger.info(
            "Built new deck for user %s (assignment %s) with %d problems",
            user.id, scope.assignment_id, len(problems),
        )
        return DailyDeck.objects.create(
            user=user, date=today, assignment_id=scope.assignment_id,
            problems=problems, current_index=0,
        )
    # A topic toggle or a new assignment since this deck was last loaded only
    # flagged it stale (see _mark_deck_stale); reconcile the unanswered tail now,
    # on the practice-page load, rather than on every toggle.
    if deck.needs_regen:
        _regenerate_deck(user, deck, today, scope)
    _top_up_pool(user, deck, Settings.load(user).questions_per_day, today, scope)
    return deck


def _top_up_pool(user, deck, per_day, today, scope=_DEFAULT_SCOPE):
    """Append pool cards until the deck can show what `per_day` calls for.

    Missing cards are the `_deck_size_target` beyond what's stored, i.e. the
    pool's shortfall; required and extra cards never need topping up here.
    """
    missing = _deck_size_target(deck, per_day) - len(deck.problems)
    if missing <= 0:
        return
    extra = _generate_problems(user, missing, today, existing=_deck_topic_ids(deck), scope=scope)
    if extra:
        for problem in extra:
            problem["kind"] = _POOL
        deck.problems = deck.problems + extra
        deck.save(update_fields=["problems"])
        logger.info(
            "Topped up deck for user %s by %d problems (now %d)",
            user.id, len(extra), len(deck.problems),
        )


def _today_decks_with_scopes(user, today):
    """Today's stored decks for `user`, each with its current `DeckScope`."""
    decks = list(DailyDeck.objects.filter(user=user, date=today))
    open_rows = _open_assignments(user) if decks else []
    return [(deck, _scope_for(user, deck.assignment_id, open_rows)) for deck in decks]


def _grow_today_deck(user, count, today):
    """Grow today's decks so each shows `count` pool-filled cards, if currently smaller.

    Appends freshly generated pool problems to the end so the student's
    progress (already-answered problems and `current_index`) is preserved.
    Never shrinks a stored deck: a smaller `count` only hides unanswered pool
    cards (see `_visible_total`). Does nothing for decks not built yet today —
    those will be built at the new count on first access.
    """
    for deck, scope in _today_decks_with_scopes(user, today):
        _top_up_pool(user, deck, count, today, scope)


def _mark_deck_stale(user, today):
    """Flag today's decks so their tails are rebuilt when next loaded.

    Called when the user's topic selection changes. This is deliberately cheap
    — a single boolean UPDATE, no problem generation — so a topic/course toggle
    returns immediately instead of rebuilding the deck on the request path. The
    actual regeneration is deferred to the next `GET /deck` (see
    `_get_or_create_today_deck`), which is exactly when the student returns to
    the practice page and would first see the new problems anyway.

    Does nothing if there's no deck for today yet: that deck is built fresh from
    the current selection on first access, so it's never stale. Deferring also
    coalesces a burst of toggles (deselect-old-then-select-new, rapid clicks)
    into a single regeneration at load time rather than one per toggle.
    """
    DailyDeck.objects.filter(user=user, date=today).update(needs_regen=True)


def _clear_needs_regen(deck):
    """Clear a deck's stale flag if set, without touching its problems."""
    if deck.needs_regen:
        deck.needs_regen = False
        deck.save(update_fields=["needs_regen"])


def _regenerate_deck_tail(user, today):
    """Rebuild the not-yet-answered problems of each of today's decks (see `_regenerate_deck`)."""
    for deck, scope in _today_decks_with_scopes(user, today):
        _regenerate_deck(user, deck, today, scope)


def _regenerate_deck(user, deck, today, scope):
    """Rebuild a deck's not-yet-answered problems from the current topics and assignments.

    Problems the student has already worked through (everything before
    `current_index`) are kept; the rest are rebuilt by `_build_cards` — the
    day's remaining required work (less what's already answered today) and pool
    practice back up to `questions_per_day` — preserving the student's position.
    Clears the `needs_regen` flag once the deck has been reconciled (this is the
    lazy handler for `_mark_deck_stale`, and for a new assignment).

    Does nothing if the deck has no usable topics. That matters: swapping topic
    sets is two steps (deselect the old, select the new), and in between
    nothing is selected. Regenerating then would produce an empty tail; writing
    it back would truncate the deck down to just the answered cards and strand
    the student on an already-"finished" deck. Leaving the deck untouched lets
    the following selection rebuild the tail properly.
    """
    answered = deck.current_index
    kept = deck.problems[:answered]
    new_tail = _build_cards(user, today, kept, scope) if _has_topics(user, scope) else []
    if not new_tail and len(deck.problems) > answered:
        # Nothing to rebuild from (no topics selected mid topic-swap, or the
        # day's practice is already answered). Preserve the deck rather than
        # truncating away its unanswered tail. Clear the flag so the state
        # isn't retried forever; the next selection marks the deck stale again.
        logger.debug(
            "Skipped deck tail regeneration for user %s: no problems generated",
            user.id,
        )
        _clear_needs_regen(deck)
        return
    deck.problems = deck.problems[:answered] + new_tail
    deck.needs_regen = False
    # The current card was replaced, so its attempts start over.
    deck.attempts = 0
    deck.save(update_fields=["problems", "needs_regen", "attempts"])
    logger.info(
        "Regenerated deck tail for user %s: kept %d answered, %d new",
        user.id, answered, len(new_tail),
    )


def _deck_payload(user, deck, scope=_DEFAULT_SCOPE):
    """The deck's current card (or its finished / no-topics state), and which deck it is.

    An assignment's deck also carries `assignment` (`{"id", "title", "open"}`,
    `open` false when it's done, for practicing again), so the client keeps
    sending it while it stays on this deck, and `open_assignments`, the
    student's open assignment count, so the client knows where leaving the
    deck goes: the list to pick another when there's more than one.

    A finished deck whose open assignment still needs cards on a later day
    carries `cards_left`, so the client can offer to finish it now
    (`finish_assignment_now`).
    """
    payload = _deck_state(user, deck, scope)
    if deck.assignment_id is not None:
        payload["assignment"] = {
            "id": deck.assignment_id, "title": deck.assignment.title,
            "open": scope.topic_ids is None,
        }
        payload["open_assignments"] = len(_open_assignments(user))
        if payload.get("completed"):
            cards_left = _cards_left_after_today(user, scope, deck.date)
            if cards_left:
                payload["cards_left"] = cards_left
    return payload


def _cards_left_after_today(user, scope, today):
    """Cards the deck's open assignment still needs beyond today, or 0.

    0 when the deck carries no open assignment, or today is already its last
    day (`_days_left`), since then today's deck holds everything left.
    """
    for row, topic_ids, due_at in _scope_assignments(user, scope):
        if topic_ids and _days_left(row, due_at, today) > 1:
            return max(0, (row.cards_needed or row.assignment.deck_size) - row.cards_answered)
    return 0


def _deck_state(user, deck, scope):
    # "No topics" is driven by the live selection, not the deck contents, so
    # deselecting every topic shows the "pick a topic" screen immediately even
    # if the deck still holds problems from before the change.
    if not _has_topics(user, scope):
        return {"no_topics": True}
    # Present the deck capped to what today's practice shows (`_visible_total`):
    # all required and extra cards, and pool cards up to the setting. Growing
    # the count is handled when the deck is loaded (pool cards are appended);
    # shrinking it is applied here at display time, so a smaller
    # `questions_per_day` takes effect immediately rather than next day. We
    # only cap the view — the pool cards stay stored, so raising the count back
    # up restores them. Without this cap, reducing the count after answering
    # more than the new total would keep showing the old (larger) deck instead
    # of "finished".
    total = _visible_total(user, deck)
    if total == 0:
        return {"no_topics": True}
    if deck.current_index >= total:
        return {"completed": True, "total": total}
    current = deck.problems[deck.current_index]
    topic = _topic_meta(current.get("topic_id"))
    # The solution is deliberately left out: anything here is readable in the
    # browser's dev tools. Answers are graded by `check_answer` instead, which
    # reveals the solution only once the card's attempts are used up.
    return {
        "problem": current["problem"],
        "topic_name": topic["topic_name"] if topic else None,
        "learn_more_url": (topic["learn_more_url"] or None) if topic else None,
        "current_number": deck.current_index + 1,
        "total": total,
        # 1-based attempt the student is on, so a reload resumes it rather than
        # handing out fresh attempts.
        "attempt": min(deck.attempts + 1, _MAX_ATTEMPTS),
    }


def _topic_meta(topic_id):
    """Resolve a stored problem's topic id to its display name and "Learn more" link, or None.

    Problems store only `topic_id`, so the card's topic label and its "Learn
    more" video link are looked up here at display time — which also keeps both
    current if a topic is renamed or an admin changes its link. Returns None when the
    id is missing (problems stored before topic attribution) or the topic no
    longer exists, so the client simply omits the label and link rather than
    showing stale or broken ones.
    """
    if topic_id is None:
        return None
    return Topic.objects.filter(id=topic_id).values("topic_name", "learn_more_url").first()


@csrf_exempt
@require_http_methods(["GET"])
def get_deck(request):
    auth = _require_auth(request)
    if auth:
        return auth
    scope, response = _request_scope(request)
    if response:
        return response
    today = _client_today(request)
    deck = _get_or_create_today_deck(request.user, today, scope)
    _snapshot_proficiency(request.user, today)
    return JsonResponse(_deck_payload(request.user, deck, scope))


@csrf_exempt
@require_http_methods(["POST"])
def advance_deck(request):
    """Move to the next problem in today's deck.

    Advancing only ever steps an *existing* deck forward — it must never build
    one. If we created-then-advanced here, a new day's deck (fresh at index 0)
    would be pushed to index 1 without the student answering anything, leaving
    them stranded on "2 of N" instead of card 1. This happens for real: the
    "correct answer" handler advances on a 900ms timer, so finishing a problem
    right before midnight fires the advance after the day has rolled over,
    making the day's first backend call an advance rather than a load.

    When there's no deck for today yet, treat the advance as a no-op and just
    report the freshly-built deck (get_or_create at index 0), so that stray
    advance lands the student on card 1.

    The optional JSON body `{"outcome": "correct_first"|"correct_second"|
    "incorrect"}` reports how the card being left was answered. It's logged as
    an `AnswerRecord` (with the optional `seconds` the student spent on the
    card), regrades the card's topic from today's answers (`_grade_topic`),
    counts toward any open assignment on that topic (`_count_assignment_card`),
    and may add another card on the topic (`_add_practice`). It's optional so a
    stray advance with no answer (the midnight-rollover case) simply doesn't
    grade or count.

    An optional `report` (`{"reason", "details", "user_answer"}`) files a
    `ProblemReport` against the card being left (see `_record_report`). The
    client sends it alongside `outcome: "correct_first"`, so reporting a faulty
    card grades it as correct rather than as a miss.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    scope, response = _request_scope(request)
    if response:
        return response
    today = _client_today(request)
    existing = DailyDeck.objects.filter(
        user=request.user, date=today, assignment_id=scope.assignment_id
    ).first()
    deck = _get_or_create_today_deck(request.user, today, scope)

    # An advance may only step the deck when it's a genuine "I finished the card
    # I'm looking at" — never a stray leftover timer. Two things must hold:
    #
    #  1. The deck already existed before this request. If this advance is what
    #     built today's deck (a stray advance as the day's first call), there was
    #     nothing to answer, so it must land the student on card 1, not card 2.
    #  2. The card the client says it's leaving (`from_number`, 1-based) is the
    #     one the server currently shows. This is the fix for the real
    #     new-day bug: the SPA mounts and GETs a fresh deck (card 1), and *then*
    #     a leftover advance timer from finishing yesterday's last card fires.
    #     That stray advance still names yesterday's card, which no longer
    #     matches, so it's ignored and the student stays on card 1. When the
    #     client sends no position (legacy callers), we don't gate on it.
    from_number = _advance_from_number(request)
    position_ok = from_number is None or from_number == deck.current_index + 1
    if existing is not None and deck.current_index < len(deck.problems) and position_ok:
        # Grade the card being left before stepping past it.
        outcome = _advance_outcome(request)
        card = deck.problems[deck.current_index]
        topic_id = card.get("topic_id")
        graded = (
            outcome in _OUTCOMES and topic_id is not None
            and Topic.objects.filter(id=topic_id).exists()
        )
        if graded:
            AnswerRecord.objects.create(
                user=request.user, topic_id=topic_id, date=today, outcome=outcome,
                seconds=_advance_seconds(request),
            )
            _grade_topic(request.user, topic_id, today)
        _record_report(request, card, today)
        deck.current_index += 1
        deck.attempts = 0
        deck.save(update_fields=["current_index", "attempts"])
        if graded:
            _count_assignment_card(request.user, topic_id, today)
            _add_practice(request.user, deck, topic_id, today, scope)
        _record_practice(request.user, today)
        # Grading may have moved a topic between bands; recapture today's mix.
        _snapshot_proficiency(request.user, today)
        logger.debug(
            "User %s advanced deck to %d/%d",
            request.user.id, deck.current_index, len(deck.problems),
        )
    elif not position_ok:
        logger.info(
            "Ignoring stale advance for user %s: client left card %s but deck is on %d",
            request.user.id, from_number, deck.current_index + 1,
        )
    return JsonResponse(_deck_payload(request.user, deck, scope))


@csrf_exempt
@require_http_methods(["POST"])
def finish_assignment_now(request):
    """Add the rest of the deck's assignment to today's deck ("Finish it now").

    Offered once the student has finished today's share of an assignment that
    isn't due yet (`cards_left` in the deck payload). Marks today as the
    assignment's last day (`finish_on`), so `_required_plan` schedules every
    remaining card today and `_add_practice` keeps adding cards while it still
    needs more, then rebuilds the deck's unanswered tail. Needs an open
    assignment's deck (`?assignment=<id>`). Returns the deck payload.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    scope, response = _request_scope(request)
    if response:
        return response
    rows = _scope_assignments(request.user, scope) if scope.assignment_id is not None else []
    if not rows:
        return JsonResponse({"error": "No open assignment to finish"}, status=400)
    today = _client_today(request)
    row = rows[0][0]
    row.finish_on = today
    row.save(update_fields=["finish_on"])
    deck = _get_or_create_today_deck(request.user, today, scope)
    _regenerate_deck(request.user, deck, today, scope)
    _record_practice(request.user, today)
    logger.info("User %s chose to finish assignment %s today", request.user.id, scope.assignment_id)
    return JsonResponse(_deck_payload(request.user, deck, scope))


def _normalize_solution(solution):
    """A stored solution as the student is expected to type it (no LaTeX '$')."""
    return str(solution).replace("$", "").strip()


def _answer_matches(answer, solution):
    """True if `answer` is equivalent to `solution` (see `myapp.answers`)."""
    return answer_matches(answer, solution)


@csrf_exempt
@require_http_methods(["POST"])
def check_answer(request):
    """Grade an answer to the current card of today's deck.

    Body: `{"answer": str, "from_number": int}`, where `from_number` is the
    1-based card the client is answering. Responds with `{"correct",
    "attempts_left"}`. Once a wrong answer uses up the card's last attempt, the
    response also carries `solution` and `steps` (the step-by-step explanation,
    possibly empty), for the incorrect face. Grading happens
    here, not in the client, so the deck payload never has to carry the
    solution (see `_deck_payload`).

    This only checks the answer. Stepping past the card and grading its topic
    is still `advance_deck`'s job. A card with no attempts left can't be
    re-checked: it reports incorrect with the solution, so there's no guessing
    after the reveal. Returns 409 if `from_number` isn't the card the server is
    showing (e.g. another tab moved on); the client then reloads the deck.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    scope, response = _request_scope(request)
    if response:
        if response.status_code != 200:
            return response
        # Several assignments are open and none was named: there's no card.
        return JsonResponse({"error": "stale card"}, status=409)
    today = _client_today(request)
    deck = DailyDeck.objects.filter(
        user=request.user, date=today, assignment_id=scope.assignment_id
    ).first()
    body = _advance_body(request)
    answer = body.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        return JsonResponse({"error": "answer is required"}, status=400)
    total = _visible_total(request.user, deck) if deck else 0
    if deck is None or deck.current_index >= total or body.get("from_number") != deck.current_index + 1:
        return JsonResponse({"error": "stale card"}, status=409)

    card = deck.problems[deck.current_index]
    solution = _normalize_solution(card["solution"])
    # Decks built before explanations existed have no "steps" key.
    reveal = {"solution": solution, "steps": card.get("steps", [])}
    if deck.attempts >= _MAX_ATTEMPTS:
        return JsonResponse({"correct": False, "attempts_left": 0, **reveal})
    # A rounded answer may also be typed truncated (see `_make_problem_for_topic`);
    # decks built before that have no "alternatives" key.
    accepted = [solution, *card.get("alternatives", [])]
    if any(_answer_matches(answer.strip()[:_MAX_ANSWER], s) for s in accepted):
        return JsonResponse({"correct": True, "attempts_left": _MAX_ATTEMPTS - deck.attempts})

    deck.attempts += 1
    deck.save(update_fields=["attempts"])
    left = _MAX_ATTEMPTS - deck.attempts
    payload = {"correct": False, "attempts_left": left}
    if left == 0:
        payload.update(reveal)
    return JsonResponse(payload)


@csrf_exempt
@require_http_methods(["GET"])
def test_solution(request):
    """The current card's solution, for the E2E suite only.

    The deck payload no longer carries solutions, so Playwright has no other way
    to type a correct answer. Guarded by ENABLE_TEST_LOGIN like `test_login`:
    it's a 404 everywhere else, including production.
    """
    if not getattr(django_settings, "ENABLE_TEST_LOGIN", False):
        raise Http404()
    auth = _require_auth(request)
    if auth:
        return auth
    scope, response = _request_scope(request)
    if response:
        raise Http404()
    deck = DailyDeck.objects.filter(
        user=request.user, date=_client_today(request), assignment_id=scope.assignment_id
    ).first()
    if deck is None or deck.current_index >= len(deck.problems):
        raise Http404()
    return JsonResponse({"solution": _normalize_solution(deck.problems[deck.current_index]["solution"])})


def _advance_body(request):
    """Parse the advance request's JSON body into a dict, or {} if absent/bad.

    Tolerant by design: a missing/empty/malformed body yields {} so callers get
    default (None) values and the advance still proceeds.
    """
    if not request.body:
        return {}
    try:
        data = json.loads(request.body)
        return data if isinstance(data, dict) else {}
    except ValueError:
        logger.warning("Ignoring malformed advance body for user %s", request.user.id)
        return {}


def _record_report(request, card, today):
    """File a `ProblemReport` for `card` from the advance body's `report`, if any.

    The problem, solution, and steps come from the server's stored card, not the
    client, so the report shows exactly what was served. An unknown reason, or
    "other" with no description, is dropped with a warning rather than failing
    the advance — the client validates before sending, so this only guards
    against malformed callers.
    """
    report = _advance_body(request).get("report")
    if not isinstance(report, dict):
        return
    reason = report.get("reason")
    details = report.get("details")
    details = details.strip()[:_MAX_REPORT_DETAILS] if isinstance(details, str) else ""
    answer = report.get("user_answer")
    answer = answer.strip()[:_MAX_REPORT_ANSWER] if isinstance(answer, str) else ""
    valid_reasons = {key for key, _ in ProblemReport.REASON_CHOICES}
    if reason not in valid_reasons or (reason == ProblemReport.OTHER and not details):
        logger.warning("Ignoring invalid problem report from user %s: %r", request.user.id, reason)
        return
    topic_id = card.get("topic_id")
    if topic_id is not None and not Topic.objects.filter(id=topic_id).exists():
        topic_id = None
    ProblemReport.objects.create(
        user=request.user, topic_id=topic_id, reason=reason, details=details,
        problem=card.get("problem", ""), solution=card.get("solution", ""),
        steps=card.get("steps", []), user_answer=answer, date=today,
    )
    logger.info("User %s reported a problem on topic %s: %s", request.user.id, topic_id, reason)


def _advance_outcome(request):
    """The reported answer outcome from an advance request body, or None.

    A missing/empty/malformed body (or missing key) yields None so the advance
    still proceeds ungraded. `advance_deck` ignores values outside `_OUTCOMES`.
    """
    return _advance_body(request).get("outcome")


def _advance_from_number(request):
    """The 1-based card number the client says it's advancing away from, or None.

    Lets `advance_deck` reject a stale/stray advance whose position no longer
    matches the server's current card (see the new-day rollover case there).
    Returns None when the client sends no position, so legacy callers that omit
    it keep advancing unconditionally.
    """
    value = _advance_body(request).get("from_number")
    return value if isinstance(value, int) else None


def _advance_seconds(request):
    """Seconds the client says the student spent on the card, clamped to a sane range.

    Missing or non-numeric values count as 0; anything longer than
    `_MAX_CARD_SECONDS` is capped (see there).
    """
    value = _advance_body(request).get("seconds")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return int(max(0, min(_MAX_CARD_SECONDS, value)))
