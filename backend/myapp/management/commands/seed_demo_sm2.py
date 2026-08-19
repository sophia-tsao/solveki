"""Seed demonstration SM-2 data for the two non-admin demo accounts.

Each student ends up with 34 selected topics spread across every proficiency
bucket the dashboard shows, plus a realistic practice calendar. The SM-2 state
per topic is computed by feeding a chosen quality sequence through the real
scheduler (`myapp.srs.update`) — the ease/interval/repetitions are authentic
algorithm output, not hand-typed numbers. A topic's `due_date` is then placed
consistently (due = last review + interval) to tell its story: struggling
topics are overdue, proficient ones rest weeks out.

The dashboard buckets topics by *interval* (see frontend Dashboard.jsx):

    New (<=1)  Learning (2-5)  Familiar (6-20)  Proficient (>=21)

Note on the Learning band: SM-2's interval jumps 1 -> 6 on the second success,
so an interval of 2-5 never arises naturally — the band is a dead zone in the
real algorithm. So the demo can show it populated, a few topics are seeded
directly into it: their ease/reps come from a real update sequence, only the
interval is nudged into 2-5. Those rows are flagged in the run summary.

One account studies mostly middle-school topics (grades 5-8), the other high
school (grades 9-12); both span several grades. Idempotent: re-running wipes
each demo account's selections / reviews / grades / practice / decks and
rebuilds them.

    python manage.py seed_demo_sm2
    python manage.py seed_demo_sm2 --today 2026-08-18
"""

import datetime
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from myapp import srs
from myapp.models import (
    DailyDeck,
    DailyPractice,
    DailyTopicGrade,
    Settings,
    Topic,
    TopicReview,
    UserTopicSelection,
)

QUESTIONS_PER_DAY = 10
HORIZON_DAYS = 42  # how far back the practice calendar runs

# A proficiency bucket for a demo topic: the SM-2 answer-quality sequence to
# replay (5 = correct first try, 3 = second try, 1 = lapse), an optional
# interval override (only for "learning", which SM-2 can't reach on its own),
# and the window (relative to today, in days) its next review is placed in.
# Negative offsets are overdue.
#   quality scale: 5 correct-first, 3 correct-second, 1 wrong
BUCKETS = {
    # Well retained: several clean successes -> long interval, weeks out.
    "proficient": {
        "sequences": [[5, 5, 5, 4], [5, 5, 5, 3], [5, 5, 4, 5], [5, 5, 5, 5]],
        "interval": None,
        "due_offset": (6, 34),
    },
    # Settling in: two or three successes -> interval 6-16.
    "familiar": {
        "sequences": [[5, 5], [5, 5, 3], [5, 5, 4], [5, 3, 5]],
        "interval": None,
        "due_offset": (1, 12),
    },
    # Actively being learned. SM-2 skips intervals 2-5, so the interval is set
    # explicitly here (ease/reps still come from the sequence).
    "learning": {
        "sequences": [[5, 5], [5, 3], [3, 5]],
        "interval": [2, 3, 4, 5],
        "due_offset": (-2, 3),
    },
    # Just started: one success -> interval 1, seen almost daily.
    "new": {
        "sequences": [[5], [3]],
        "interval": None,
        "due_offset": (0, 1),
    },
    # Struggles the most: repeated lapses drive ease toward the 1.3 floor and
    # pin the interval at 1 day; overdue, so these lead the deck.
    "struggling": {
        "sequences": [[5, 1, 1, 1, 1], [5, 3, 1, 1], [3, 1, 1], [5, 1, 1, 1]],
        "interval": None,
        "due_offset": (-7, 0),
    },
}

# How many of the 34 topics land in each bucket. "new" + "struggling" both sit
# in the red New band (interval <= 1); struggling ones are set apart by a
# rock-bottom ease and an overdue date.
BUCKET_COUNTS = {
    "proficient": 12,
    "familiar": 8,
    "learning": 5,
    "new": 3,
    "struggling": 6,
}

# Topics to pull per grade level (deterministic, by id). Sums to 34 each.
MIDDLE_SCHOOL_GRADES = {5: 4, 6: 11, 7: 10, 8: 9}   # mostly middle school
HIGH_SCHOOL_GRADES = {9: 10, 10: 8, 11: 9, 12: 7}   # high school

DEMO_ACCOUNTS = [
    ("stsao@student.fsaps.org", "middle school", MIDDLE_SCHOOL_GRADES),
    ("sophiayutsao@gmail.com", "high school", HIGH_SCHOOL_GRADES),
]


def _apply_sequence(qualities):
    """Return the SM-2 (ease, interval, repetitions) after replaying qualities."""
    ease, interval, reps = srs.INITIAL_EASE, 0, 0
    for q in qualities:
        ease, interval, reps = srs.update(ease, interval, reps, q)
    return ease, interval, reps


class Command(BaseCommand):
    help = "Seed demonstration SM-2 review histories for the two non-admin accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--today",
            help="Date to treat as today (YYYY-MM-DD); defaults to the server date.",
        )

    def handle(self, *args, **options):
        if options.get("today"):
            try:
                today = datetime.date.fromisoformat(options["today"])
            except ValueError:
                raise CommandError(f"Invalid --today: {options['today']!r}")
        else:
            today = timezone.localdate()

        total = sum(BUCKET_COUNTS.values())
        User = get_user_model()
        for email, band, grade_plan in DEMO_ACCOUNTS:
            if sum(grade_plan.values()) != total:
                raise CommandError(
                    f"{email}: grade plan sums to {sum(grade_plan.values())}, "
                    f"expected {total}"
                )
            # Non-admin accounts can share an email (Google vs student login),
            # so match the non-staff row explicitly.
            user = (
                User.objects.filter(email=email, is_staff=False)
                .order_by("id")
                .first()
            )
            if user is None:
                raise CommandError(f"No non-admin user with email {email!r}")
            with transaction.atomic():
                summary = self._seed_user(user, grade_plan, today)
            self._report(user, email, band, summary, today)

    def _seed_user(self, user, grade_plan, today):
        rng = random.Random(f"seed:{user.id}")

        # Pull topics per grade (deterministic order), preserving grade order.
        topics = []
        for grade in sorted(grade_plan):
            picks = list(
                Topic.objects.filter(
                    course__grade_level=grade, generator_name__isnull=False
                )
                .select_related("course")
                .order_by("id")[: grade_plan[grade]]
            )
            if len(picks) < grade_plan[grade]:
                raise CommandError(
                    f"Only {len(picks)} usable topics in grade {grade}, "
                    f"need {grade_plan[grade]}"
                )
            topics.extend(picks)

        # Build the bucket assignment and shuffle so buckets spread across
        # grades (weak/strong topics aren't clustered in one subject).
        buckets = []
        for name, count in BUCKET_COUNTS.items():
            buckets += [name] * count
        rng.shuffle(buckets)

        # Clean slate for this account.
        UserTopicSelection.objects.filter(user=user).delete()
        TopicReview.objects.filter(user=user).delete()
        DailyTopicGrade.objects.filter(user=user).delete()
        DailyPractice.objects.filter(user=user).delete()
        DailyDeck.objects.filter(user=user).delete()

        settings = Settings.load(user)
        settings.questions_per_day = QUESTIONS_PER_DAY
        settings.save(update_fields=["questions_per_day"])

        selections = []
        reviews = []
        rows = []  # for the report
        seq_pick = {name: 0 for name in BUCKETS}
        for topic, bucket in zip(topics, buckets):
            selections.append(UserTopicSelection(user=user, topic=topic))
            spec = BUCKETS[bucket]
            seq = spec["sequences"][seq_pick[bucket] % len(spec["sequences"])]
            seq_pick[bucket] += 1
            ease, interval, reps = _apply_sequence(seq)
            forced = spec["interval"]
            if forced is not None:
                interval = forced[(seq_pick[bucket] - 1) % len(forced)]
            lo, hi = spec["due_offset"]
            due_date = today + datetime.timedelta(days=rng.randint(lo, hi))
            reviews.append(TopicReview(
                user=user, topic=topic,
                ease=ease, interval=interval, repetitions=reps, due_date=due_date,
            ))
            rows.append((bucket, topic, ease, interval, reps, due_date))

        UserTopicSelection.objects.bulk_create(selections)
        TopicReview.objects.bulk_create(reviews)

        practice_days = self._build_calendar(user, today, rng)

        return {"rows": rows, "practice_days": practice_days}

    def _build_calendar(self, user, today, rng):
        """Practice on most days in the window, with a couple of clear gaps."""
        start = today - datetime.timedelta(days=HORIZON_DAYS)
        all_days = [
            start + datetime.timedelta(days=n)
            for n in range((today - start).days)  # through yesterday
        ]
        # A couple of missed days, spread out and away from the recent tail so
        # they read as "skipped a few days here and there".
        gaps = set(rng.sample(all_days[: len(all_days) - 3], k=3))
        rows = []
        for day in all_days:
            if day in gaps:
                continue
            total = QUESTIONS_PER_DAY
            # Occasionally the student only got partway through the deck.
            answered = (
                rng.randint(3, total - 1) if rng.random() < 0.15 else total
            )
            rows.append(DailyPractice(
                user=user, date=day, answered=answered, total=total,
            ))
        DailyPractice.objects.bulk_create(rows)
        return {"count": len(rows), "gaps": sorted(gaps), "start": start}

    def _report(self, user, email, band, summary, today):
        rows = summary["rows"]
        self.stdout.write(self.style.SUCCESS(
            f"\n{email} (id {user.id}) - mostly {band}"
        ))
        # Bucket distribution.
        by_bucket = {}
        for bucket, *_ in rows:
            by_bucket[bucket] = by_bucket.get(bucket, 0) + 1
        dist = "  ".join(f"{b}:{by_bucket.get(b, 0)}" for b in BUCKETS)
        # Grade distribution.
        by_grade = {}
        for _, topic, *_ in rows:
            g = topic.course.grade_level if topic.course else "?"
            by_grade[g] = by_grade.get(g, 0) + 1
        grades = "  ".join(f"g{g}:{by_grade[g]}" for g in sorted(by_grade))
        cal = summary["practice_days"]
        self.stdout.write(f"  {len(rows)} topics | buckets  {dist}")
        self.stdout.write(f"  grades  {grades}")
        self.stdout.write(
            f"  {cal['count']} practice days ({cal['start']}..{today - datetime.timedelta(days=1)}), "
            f"missed: {', '.join(d.isoformat() for d in cal['gaps'])}"
        )
        # Show the topics that lead the deck (most overdue first).
        overdue = sorted(rows, key=lambda r: r[5])[:8]
        self.stdout.write("  leading the deck (most due first):")
        for bucket, topic, ease, interval, reps, due in overdue:
            g = topic.course.grade_level if topic.course else "?"
            over = (today - due).days
            when = "due today" if over == 0 else (
                f"{over}d overdue" if over > 0 else f"in {-over}d"
            )
            self.stdout.write(
                f"    g{str(g):<3}{topic.topic_name[:34]:<36}"
                f"{bucket:<11}ease {ease:.2f}  intvl {interval:<3}  {when}"
            )
