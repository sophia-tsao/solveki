"""Day-by-day deck simulation with pluggable deck-planning policies.

Models what the deck view does over two weeks — one deck per open assignment
(the default deck only while none is open), required cards planned when a deck
is opened, then answered card by card with the topic regraded from the day's
answers (`srs.grade_day`), assignment progress counted, and extra cards added —
on top of the real `practice` and `srs` functions. A *policy* decides how a
deck is planned and when an extra card fits, so several candidates can be run
over the same teachers, students and seeds and compared.

Run `python -m myapp.tests.deck_sim` from backend/ for the comparison table.
"""
import math
import random
from collections import defaultdict

from myapp import practice, srs

F, S, X = "correct_first", "correct_second", "incorrect"
DAYS = 14
PER_DAY = 1  # the student's own setting: a single pool card, so assignments drive the deck

# Teacher scenarios: (assign day, topics, cards, days until due).
TEACHERS = {
    "daily50": [(d, [f"T{d}"], 50, 1) for d in range(DAYS)],
    "every3_20": [(d, [f"T{d}"], 20, 3) for d in range(0, DAYS, 3)],
    "weekly10": [(0, ["T0"], 10, 7), (7, ["T7"], 10, 7)],
    "weekly10_reassign": [(0, ["T0"], 10, 7), (7, ["T7"], 10, 7), (9, ["T0"], 20, 3)],
    "every3_20_reassign": [(d, [f"T{d}"], 20, 3) for d in range(0, DAYS, 3)] + [(7, ["T0"], 20, 3)],
    "weekly25x5": [(d, [f"T{d}_{k}" for k in range(5)], 25, 7) for d in (0, 7)],
    "overlap": [(0, ["T0"], 10, 7), (2, ["T2"], 20, 3), (5, ["T5"], 20, 3), (7, ["T7"], 10, 7), (9, ["T9"], 20, 3)],
}
# (starting accuracy, answers to grasp a topic); None answers perfectly.
STUDENTS = {
    "perfect": None,
    "one_mistake": None,
    "strong": (0.3, 10),
    "average": (0.15, 30),
    "struggler": (0.02, 100),
    "all_wrong": (0.0, 100),
}
BACKLOG_SIZE = 20


def backlog_reviews():
    """Previously learned topics from earlier assignments, shaped like a real student's backlog.

    Eases 1.3-2.6, 1-7 repetitions, due from 6 days ago to 5 days ahead, so
    some are overdue on day 0 and the rest come due during the two weeks.
    """
    out = {}
    for i in range(BACKLOG_SIZE):
        reps = 1 + i % 7
        ease = round(1.3 + 0.065 * i, 2)
        interval = max(1, round(ease ** reps))
        out[f"B{i}"] = {"ease": ease, "interval": interval, "reps": reps, "due": i % 12 - 6, "failed_on": None}
    return out


class Student:
    """Accuracy rises with practice and decays between practice days."""

    def __init__(self, kind, rng):
        self.kind, self.rng = kind, rng
        self.answers = defaultdict(int)
        self.last_day = {}
        self.first_day = {}
        self.good_days = defaultdict(int)

    def know(self, topic, review):
        """Start with `topic` learned before the simulation, last practised when it was scheduled."""
        grasp = STUDENTS[self.kind][1] if STUDENTS[self.kind] else 1
        self.answers[topic] = int(1.5 * grasp)
        self.last_day[topic] = review["due"] - review["interval"]
        self.first_day[topic] = -100
        self.good_days[topic] = review["reps"]

    def skill(self, topic, day):
        start, grasp = STUDENTS[self.kind]
        if self.kind == "all_wrong" and self.first_day.get(topic, day) == day:
            return 0.0
        learned = start + (0.95 - start) * (1 - math.exp(-3 * self.answers[topic] / grasp))
        if topic in self.last_day:
            gap = day - self.last_day[topic]
            learned = start + (learned - start) * math.exp(-gap / (3 * (1 + self.good_days[topic])))
        return learned

    def answer(self, topic, day, slip):
        self.first_day.setdefault(topic, day)
        if STUDENTS[self.kind] is None:
            outcome = X if slip else F
        else:
            p = self.skill(topic, day)
            if self.rng.random() < p:
                outcome = F
            elif p > 0 and self.rng.random() < min(1, p + 0.15):
                outcome = S
            else:
                outcome = X
        self.answers[topic] += 1
        self.last_day[topic] = day
        return outcome


# Policies: P0 is the deck before assignment budgets (every due review and
# pool practice in every deck, extras up to DAILY_CAP); P2 is the current one
# (an open assignment's decks hold at most max_cards cards over its life, see
# `practice.plan_assignment_deck`). DESIGN.md ("Deck sizing") records how P2
# was chosen over the other candidates.
P0 = {"name": "P0 no budget", "budget": False}
P2 = {"name": "P2 budget", "budget": True}
POLICIES = [P0, P2]


def _interleave(plan):
    """One card per topic per pass, so a topic's cards spread through the deck."""
    queue, left = [], dict(plan)
    while any(left.values()):
        for topic in left:
            if left[topic] > 0:
                queue.append(topic)
                left[topic] -= 1
    return queue


def _share(a, day, reviews):
    ordered = sorted(
        a["topics"],
        key=lambda t: (
            bool(a["outcomes"][t]), practice.is_solid(a["outcomes"][t]),
            reviews.get(t, {}).get("ease", srs.INITIAL_EASE), t,
        ),
    )
    return practice.assignment_cards(max(0, a["needed"] - a["answered"]), a["due"] - day, ordered)


def build_deck(pol, a, day, reviews, assigned, today, planned_today):
    """Plan a deck when it's opened: `(queue, review_topics)`.

    `a` is the deck's assignment, or None for the default deck.
    """
    due = {t: r for t, r in reviews.items() if r["due"] is not None and r["due"] <= day}
    lapsed = {t: r["ease"] for t, r in due.items() if r["reps"] == 0 and r["failed_on"] == day - 1}
    answered = {t: len(o) for t, o in today.items()}

    def minus_answered(plan):
        return {t: c - answered.get(t, 0) for t, c in plan.items() if c > answered.get(t, 0)}

    if a is None or not pol["budget"]:
        # The assignment's share, then lapses and every due assignment-topic
        # review, capped at DAILY_CAP; pool up to the setting.
        core = _share(a, day, reviews) if a else {}
        due_reviews = {t: r["ease"] for t, r in due.items() if t in assigned}
        due_reviews.update(lapsed)
        plan = minus_answered(practice.plan_required(core, due_reviews, lapsed))
        queue = _interleave(plan)
        if len(queue) < PER_DAY:
            pool = sorted(assigned, key=lambda t: (reviews[t]["due"] if t in reviews and reviews[t]["due"] is not None else -1, t))
            queue += pool[:PER_DAY - len(queue)]
        return queue, set(plan) - set(core)

    own = set(a["topics"])
    candidates = {}
    for t, r in due.items():
        if t not in own and t in planned_today:
            continue
        size = practice.LAPSE_REVIEW_CARDS if t in lapsed else practice.MIN_SESSION
        urgency = practice.review_urgency(r["ease"], r["interval"], day - r["due"], t in lapsed)
        candidates[t] = (size - answered.get(t, 0), urgency)
    still = max(0, a["needed"] - a["answered"])
    plan, review_plan = practice.plan_assignment_deck(
        minus_answered(_share(a, day, reviews)), candidates, own,
        cap=practice.max_cards(a["size"]) - a["deck_used"],
        room=practice.review_room(a["size"], a["deck_used"], a["review_used"], still),
        still_needed=still,
    )
    return _interleave(plan) + _interleave(review_plan), set(review_plan)


def _extra_fits(pol, a, queue, i, reviews_in_deck, topic):
    """True if one more card on `topic` fits the deck being answered."""
    if a is None or not pol["budget"]:
        return len(queue) < practice.DAILY_CAP
    tail = queue[i + 1:]
    tail_reviews = sum(1 for t in tail if t not in a["topics"])
    still = 0 if a["done"] else max(0, a["needed"] - a["answered"] - (len(tail) - tail_reviews))
    return practice.extra_fits(
        a["size"], a["deck_used"] + len(tail), a["review_used"] + tail_reviews, still,
        review=topic not in a["topics"],
    )


def simulate(teacher, kind, seed, pol=P0, backlog=False):
    """Run two weeks; returns per-day cards, per topic-day records, finishes and review lateness."""
    rng = random.Random(seed)
    student = Student(kind, rng)
    reviews = {}  # topic -> {ease, interval, reps, due, failed_on}
    prior = set()
    if backlog:
        for topic, review in backlog_reviews().items():
            reviews[topic] = review
            prior.add(topic)
            student.know(topic, review)
    assignments = [
        {"topics": list(ts), "size": n, "start": s, "due": s + d, "answered": 0, "needed": n,
         "outcomes": {t: [] for t in ts}, "done": False, "max_reached": False,
         "deck_used": 0, "review_used": 0, "deck_max": 0, "done_day": None}
        for s, ts, n, d in TEACHERS[teacher]
    ]
    log = {"cards": [], "days": {}, "finished": [], "late": [], "forgot": 0, "assignments": assignments}
    for day in range(DAYS):
        open_ = sorted(
            (a for a in assignments if a["start"] <= day < a["due"] and not a["done"]),
            key=lambda a: (a["due"], a["start"]),
        )
        assigned = prior | {t for a in assignments if a["start"] <= day for t in a["topics"]}
        snapshots, today, floors = {}, defaultdict(list), {}
        planned_today = set()
        day_cards = 0
        slip_at = None
        for a in open_ or [None]:
            if a is not None and a["done"]:
                continue  # finished in an earlier deck today
            queue, deck_reviews = build_deck(pol, a, day, reviews, assigned, today, planned_today)
            planned_today |= set(queue)
            if slip_at is None:
                slip_at = rng.randrange(len(queue)) if kind == "one_mistake" and queue else -1
            i = 0
            while i < len(queue):
                topic = queue[i]
                outcome = student.answer(topic, day, day_cards == slip_at)
                day_cards += 1
                today[topic].append(outcome)
                review = reviews.setdefault(
                    topic, {"ease": srs.INITIAL_EASE, "interval": 0, "reps": 0, "due": None, "failed_on": None}
                )
                if topic not in snapshots:
                    snapshots[topic] = dict(review)
                    if review["due"] is not None and review["due"] <= day and review["interval"] > 0:
                        log["late"].append(day - review["due"])
                snap = snapshots[topic]
                early = snap["due"] is not None and snap["due"] > day
                ease, interval, reps, quality = srs.grade_day(
                    snap["ease"], snap["interval"], snap["reps"], today[topic], early=early
                )
                due_day = snap["due"] if early and quality >= srs.PASSING_GRADE else day + interval
                if floors.get(topic) and interval < floors[topic]:
                    interval, reps, due_day = floors[topic], max(reps, 2), day + floors[topic]
                review.update(
                    ease=ease, interval=interval, reps=reps, due=due_day,
                    failed_on=day if quality < srs.PASSING_GRADE else None,
                )
                if a is not None:
                    a["deck_used"] += 1
                    if pol["budget"] and topic not in a["topics"]:
                        a["review_used"] += 1

                finishing = False
                for b in open_:
                    if topic not in b["topics"] or b["done"]:
                        continue
                    b["answered"] += 1
                    b["outcomes"][topic].append(outcome)
                    b["needed"] = practice.cards_needed(b["size"], b["answered"], b["outcomes"])
                    done, max_reached = practice.is_complete(b["size"], b["answered"], b["outcomes"])
                    if done:
                        _finish(b, max_reached, day, reviews, floors, log)
                        if pol["budget"]:
                            _drop_finished(b, queue, i, open_)
                    elif b["due"] - day == 1 and b["needed"] > b["answered"]:
                        finishing = True
                learning = (
                    snap["reps"] == 0 and not practice.is_enough_today(today[topic])
                    and len(today[topic]) < practice.MAX_TOPIC_CARDS_PER_DAY
                )
                confirming = (
                    snap["reps"] > 0 and quality <= srs.HARD_QUALITY
                    and len(today[topic]) < practice.MIN_SESSION
                )
                if pol["budget"] and a is not None and topic not in a["topics"]:
                    # A review of another topic starts at MIN_SESSION cards and
                    # gets more, up to a full review, while it grades below a
                    # normal pass.
                    confirming = (
                        snap["reps"] > 0 and quality <= srs.HARD_QUALITY
                        and len(today[topic]) < practice.review_cards(snap["ease"])
                    )
                if (learning or confirming or finishing) and topic not in queue[i + 1:]:
                    if _extra_fits(pol, a, queue, i, deck_reviews, topic):
                        queue.insert(min(len(queue), i + 2), topic)
                if (
                    pol["budget"] and a is not None and not a["done"]
                    and practice.budget_spent(a["size"], a["deck_used"])
                    and not any(t in a["topics"] for t in queue[i + 1:])
                ):
                    _finish(a, not all(practice.is_solid(o) for o in a["outcomes"].values()), day, reviews, floors, log)
                i += 1
            if a is not None:
                a["deck_max"] = max(a["deck_max"], len(queue))
        log["cards"].append(day_cards)
        for topic, outcomes in today.items():
            if sum(o == F for o in outcomes) / len(outcomes) >= 0.8:
                student.good_days[topic] += 1
            before = snapshots[topic]
            after = dict(reviews[topic])
            if before["reps"] > 0 and before["due"] is not None and before["due"] <= day and after["reps"] == 0:
                log["forgot"] += 1
            log["days"][(topic, day)] = {"outcomes": outcomes, "before": before, "after": after}
    if STUDENTS[kind] is not None:
        log["recall"] = [student.skill(t, DAYS) for t in reviews]
    log["backlog"] = [t for t, r in reviews.items() if r["due"] is not None and r["due"] < DAYS]
    log["late"] += [DAYS - reviews[t]["due"] for t in log["backlog"] if reviews[t]["interval"] > 0]
    return log


def _finish(a, max_reached, day, reviews, floors, log):
    """Complete assignment `a`, lifting topics answered well enough to "familiar"."""
    a["done"], a["max_reached"], a["done_day"] = True, max_reached, day
    flat = [o for t in a["topics"] for o in a["outcomes"][t]]
    for t in a["topics"]:
        if a["outcomes"][t] and srs.accuracy(a["outcomes"][t]) >= practice.GRADUATION_ACCURACY:
            floors[t] = practice.GRADUATION_INTERVAL
            r = reviews[t]
            if r["interval"] < floors[t]:
                r.update(interval=floors[t], reps=max(r["reps"], 2), due=day + floors[t])
    log["finished"].append((a["topics"], day, {t: dict(reviews[t]) for t in a["topics"] if t in reviews}, srs.accuracy(flat)))


def _drop_finished(a, queue, i, open_):
    """Drop a finished assignment's unanswered cards, unless another open one shares the topic."""
    still = {t for b in open_ if not b["done"] for t in b["topics"]}
    queue[i + 1:] = [t for t in queue[i + 1:] if t not in a["topics"] or t in still]


def runs(kind):
    """Seeds to run: one for the deterministic students, several for the rest."""
    return range(1 if STUDENTS[kind] is None else 8)


def each(pol, teachers=TEACHERS, kinds=STUDENTS, backlogs=(False, True)):
    for teacher in teachers:
        for kind in kinds:
            for backlog in backlogs:
                for seed in runs(kind):
                    yield teacher, kind, backlog, simulate(teacher, kind, seed, pol, backlog)


def violations(pol):
    """Counts of constraint violations for `pol` across every run."""
    out = defaultdict(int)
    for teacher, kind, backlog, log in each(pol):
        out["runs"] += 1
        out["C1 max/day"] = max(out["C1 max/day"], max(log["cards"]))
        if kind == "perfect":
            for topics, day, after, _ in log["finished"]:
                for t in after:
                    if after[t]["interval"] < 6 or after[t]["due"] <= day + 1:
                        out["C2"] += 1
        for (topic, day), rec in log["days"].items():
            outcomes = rec["outcomes"]
            if day + 1 >= DAYS or len(outcomes) < 3 or srs.accuracy(outcomes) >= 0.3:
                continue
            out["C3 checked"] += 1
            tomorrow = log["days"].get((topic, day + 1))
            if rec["after"]["due"] != day + 1 or tomorrow is None or len(tomorrow["outcomes"]) < 5:
                out["C3"] += 1
        if kind == "one_mistake":
            for rec in log["days"].values():
                if rec["outcomes"].count(X) == 1 and (
                    rec["after"]["reps"] == 0 or rec["after"]["ease"] < rec["before"]["ease"] - 0.05
                ):
                    out["C5"] += 1
        for a in log["assignments"]:
            limit = practice.max_cards(a["size"])
            if a["deck_used"] > limit:
                out["C6"] += 1
            out["C6 worst"] = max(out["C6 worst"], a["deck_used"] / limit)
    return out


def goals(pol, backlog):
    """Goal metrics for `pol`, with or without a starting backlog."""
    late, backlog_left, forgot, cards, days, recall = [], [], 0, 0, 0, []
    per_kind = defaultdict(list)
    struggle = {"on_topic": [], "max_reached": 0, "unfinished": 0, "n": 0}
    for teacher, kind, _, log in each(pol, backlogs=(backlog,)):
        late += log["late"]
        backlog_left.append(len(log["backlog"]))
        forgot += log["forgot"]
        recall += log.get("recall", [])
        cards += sum(log["cards"])
        days += DAYS
        per_kind[kind].append(sum(log["cards"]))
        if kind == "struggler":
            for a in log["assignments"]:
                if a["start"] + (a["due"] - a["start"]) > DAYS:
                    continue  # still running at the end
                struggle["n"] += 1
                struggle["on_topic"].append(a["answered"] / a["size"])
                struggle["max_reached"] += a["max_reached"]
                struggle["unfinished"] += not a["done"]
    mean = lambda xs: sum(xs) / len(xs) if xs else 0
    return {
        "backlog": mean(backlog_left),
        "late": mean(late),
        "late max": max(late) if late else 0,
        "<=1d": mean([x <= 1 for x in late]),
        "forgot": forgot,
        "recall": mean(recall),
        "cards/day": cards / days,
        "strug on-topic/N": mean(struggle["on_topic"]),
        "strug max%": struggle["max_reached"] / max(1, struggle["n"]),
        "strug unfin%": struggle["unfinished"] / max(1, struggle["n"]),
        "kind cards": {k: mean(v) for k, v in per_kind.items()},
    }


def main():
    print(f"{'policy':<22} {'C1':>4} {'C2':>3} {'C3':>9} {'C5':>3} {'C6':>4} {'C6w':>5} | "
          f"{'bl':>5} {'late':>5} {'lmax':>4} {'<=1d':>5} {'recl':>5} {'c/d':>5} {'s/N':>5} {'smax':>5} {'sunf':>5}")
    for pol in POLICIES:
        v = violations(pol)
        for backlog in (False, True):
            g = goals(pol, backlog)
            head = (
                f"{pol['name']:<22} {v['C1 max/day']:>4} {v['C2']:>3} {v['C3']:>4}/{v['C3 checked']:<4} "
                f"{v['C5']:>3} {v['C6']:>4} {v['C6 worst']:>5.2f}" if not backlog else f"{'  + backlog':<22} {'':>34}"
            )
            print(
                f"{head} | {g['backlog']:>5.1f} {g['late']:>5.2f} {g['late max']:>4} {g['<=1d']:>5.0%} "
                f"{g['recall']:>5.2f} {g['cards/day']:>5.1f} {g['strug on-topic/N']:>5.2f} {g['strug max%']:>5.0%} "
                f"{g['strug unfin%']:>5.0%}"
            )


if __name__ == "__main__":
    main()
