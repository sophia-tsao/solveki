"""Simulated two weeks of practice, checked against the deck's design constraints.

Re-runs the simulation the deck sizing was tuned with (DESIGN.md, "Deck
sizing") on top of the real `practice` and `srs` functions, so a change to
either that breaks a constraint fails here. The day loop mirrors the deck view:
plan the required cards (`practice.plan_required`), fill the pool to the daily
setting, then answer card by card — regrading the topic from the day's answers
(`srs.grade_day`), counting assignment progress, and adding learning or
finishing cards — and graduate topics when an assignment is finished well.

Teacher scenarios are (assign day, topic, cards, days until due); students are
modelled by how fast they learn and forget. Constraints:

- C1: no day asks for more than 100 cards.
- C2: a student who gets everything right is "familiar" with the topic (6+
  days) when they finish the assignment, and isn't due back the next day.
- C3: a topic the student gets mostly wrong is due the next day, with at
  least 5 cards.
- C5: a single mistake in a day is never punished (no lapse, no ease drop).
"""
import math
import random
from collections import defaultdict

from django.test import SimpleTestCase

from myapp import practice, srs

F, S, X = "correct_first", "correct_second", "incorrect"
DAYS = 14
PER_DAY = 1  # the student's own setting: a single pool card, so assignments drive the deck

SCENARIOS = {
    "daily50": [(d, f"T{d}", 50, 1) for d in range(DAYS)],
    "every3_20": [(d, f"T{d}", 20, 3) for d in range(0, DAYS, 3)],
    "weekly10": [(0, "T0", 10, 7), (7, "T7", 10, 7)],
    "weekly10_reassign": [(0, "T0", 10, 7), (7, "T7", 10, 7), (9, "T0", 20, 3)],
    "every3_20_reassign": [(d, f"T{d}", 20, 3) for d in range(0, DAYS, 3)] + [(7, "T0", 20, 3)],
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


class Student:
    """Accuracy rises with practice and decays between practice days."""

    def __init__(self, kind, rng):
        self.kind, self.rng = kind, rng
        self.answers = defaultdict(int)
        self.last_day = {}
        self.first_day = {}
        self.good_days = defaultdict(int)

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


def simulate(scenario, kind, seed):
    """Run two weeks; returns per-day card counts, per topic-day records and finishes."""
    rng = random.Random(seed)
    student = Student(kind, rng)
    reviews = {}  # topic -> {ease, interval, reps, due, failed_on}
    assignments = [
        {"topic": t, "size": n, "start": s, "due": s + d, "answered": 0, "needed": n,
         "outcomes": [], "done": False}
        for s, t, n, d in SCENARIOS[scenario]
    ]
    log = {"cards": [], "days": {}, "finished": []}
    for day in range(DAYS):
        open_ = [a for a in assignments if a["start"] <= day < a["due"] and not a["done"]]
        assigned = {a["topic"] for a in assignments if a["start"] <= day}
        plan = defaultdict(int)
        for a in open_:
            share = practice.assignment_cards(a["needed"] - a["answered"], a["due"] - day, [a["topic"]])
            for topic, cards in share.items():
                plan[topic] = max(plan[topic], cards)
        due = {t: r for t, r in reviews.items() if r["due"] <= day}
        lapsed = {t: r["ease"] for t, r in due.items() if r["reps"] == 0 and r["failed_on"] == day - 1}
        due_reviews = {t: r["ease"] for t, r in due.items() if t in assigned}
        due_reviews.update(lapsed)
        plan = practice.plan_required(dict(plan), due_reviews, lapsed)

        queue = []
        left = dict(plan)
        while any(left.values()):
            for topic in left:
                if left[topic] > 0:
                    queue.append(topic)
                    left[topic] -= 1
        if len(queue) < PER_DAY:
            pool = sorted(assigned, key=lambda t: (reviews[t]["due"] if t in reviews else -1, t))
            queue += pool[:PER_DAY - len(queue)]

        snapshots = {}
        today = defaultdict(list)
        slip_at = rng.randrange(len(queue)) if kind == "one_mistake" and queue else -1
        floors = {}
        i = 0
        while i < len(queue):
            topic = queue[i]
            outcome = student.answer(topic, day, i == slip_at)
            today[topic].append(outcome)
            review = reviews.setdefault(
                topic, {"ease": srs.INITIAL_EASE, "interval": 0, "reps": 0, "due": None, "failed_on": None}
            )
            snap = snapshots.setdefault(topic, dict(review))
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

            finishing = False
            for a in open_:
                if a["topic"] != topic or a["done"]:
                    continue
                a["answered"] += 1
                a["outcomes"].append(outcome)
                by_topic = {topic: a["outcomes"]}
                a["needed"] = practice.cards_needed(a["size"], a["answered"], by_topic)
                done, _ = practice.is_complete(a["size"], a["answered"], by_topic)
                if done:
                    a["done"] = True
                    if srs.accuracy(a["outcomes"]) >= practice.GRADUATION_ACCURACY:
                        floors[topic] = practice.GRADUATION_INTERVAL
                        if review["interval"] < floors[topic]:
                            review.update(interval=floors[topic], reps=max(review["reps"], 2), due=day + floors[topic])
                    log["finished"].append((topic, day, dict(review)))
                elif a["due"] - day == 1 and a["needed"] > a["answered"]:
                    finishing = True
            learning = (
                snap["reps"] == 0 and not practice.is_enough_today(today[topic])
                and len(today[topic]) < practice.MAX_TOPIC_CARDS_PER_DAY
            )
            confirming = (
                snap["reps"] > 0 and quality <= srs.HARD_QUALITY
                and len(today[topic]) < practice.MIN_SESSION
            )
            wanted = learning or confirming or finishing
            if wanted and topic not in queue[i + 1:] and len(queue) < practice.DAILY_CAP:
                queue.insert(min(len(queue), i + 2), topic)
            i += 1

        log["cards"].append(len(queue))
        for topic, outcomes in today.items():
            if sum(o == F for o in outcomes) / len(outcomes) >= 0.8:
                student.good_days[topic] += 1
            log["days"][(topic, day)] = {
                "outcomes": outcomes, "before": snapshots[topic], "after": dict(reviews[topic]),
            }
    return log


def runs(kind):
    """Seeds to run: one for the deterministic students, several for the rest."""
    return range(1 if STUDENTS[kind] is None else 8)


class DeckSimulationTests(SimpleTestCase):
    def _each(self, kinds=STUDENTS):
        for scenario in SCENARIOS:
            for kind in kinds:
                for seed in runs(kind):
                    yield scenario, kind, simulate(scenario, kind, seed)

    def test_c1_no_day_asks_for_more_than_100_cards(self):
        for scenario, kind, log in self._each():
            self.assertLessEqual(max(log["cards"]), practice.HARD_CAP, (scenario, kind))

    def test_c2_perfect_student_is_familiar_after_finishing(self):
        for scenario, kind, log in self._each(["perfect"]):
            self.assertTrue(log["finished"], scenario)
            for topic, day, review in log["finished"]:
                self.assertGreaterEqual(review["interval"], 6, (scenario, topic, day))
                self.assertGreater(review["due"], day + 1, (scenario, topic, day))

    def test_c3_failed_topic_is_back_next_day_with_enough_cards(self):
        checked = 0
        for scenario, kind, log in self._each():
            for (topic, day), record in log["days"].items():
                outcomes = record["outcomes"]
                if day + 1 >= DAYS or len(outcomes) < 3 or srs.accuracy(outcomes) >= 0.3:
                    continue
                checked += 1
                self.assertEqual(record["after"]["due"], day + 1, (scenario, kind, topic, day))
                tomorrow = log["days"].get((topic, day + 1))
                self.assertIsNotNone(tomorrow, (scenario, kind, topic, day))
                self.assertGreaterEqual(len(tomorrow["outcomes"]), 5, (scenario, kind, topic, day))
        self.assertGreater(checked, 0)  # the struggling students do produce failed days

    def test_c5_single_mistake_is_not_punished(self):
        for scenario, kind, log in self._each(["one_mistake"]):
            for (topic, day), record in log["days"].items():
                if record["outcomes"].count(X) != 1:
                    continue
                before, after = record["before"], record["after"]
                self.assertNotEqual(after["reps"], 0, (scenario, topic, day))
                self.assertGreaterEqual(after["ease"], before["ease"] - 0.05, (scenario, topic, day))

    def test_struggling_students_practise_more(self):
        def mean_cards(kind):
            totals = [sum(log["cards"]) for _, _, log in self._each([kind])]
            return sum(totals) / len(totals)
        self.assertGreater(mean_cards("struggler"), mean_cards("strong"))
        self.assertGreater(mean_cards("strong"), mean_cards("perfect"))
