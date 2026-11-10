"""Read-side helpers behind the teacher views' practice insights.

Shared by the assignment report, class roster, student detail and the
teacher home: per-student proficiency-band counts, the "struggled with most"
topic ranking, a student's recent practice activity (consistency, volume,
time, accuracy), the same activity in bulk for a group, and the weekly goal.
"""
import datetime

from django.db.models import Count, Max, Q, Sum

from ..models import AnswerRecord, DailyPractice, Settings, Topic, TopicReview
from .deck import _interval_band

BANDS = ("new", "learning", "familiar", "proficient")
_BANDS = BANDS

# The weekly goal a student is "on track" against: this many days' worth of
# their daily card setting over the last 7 days.
WEEKLY_GOAL_DAYS = 3
DEFAULT_QUESTIONS_PER_DAY = 10

# How many days of practice the student detail's consistency strip covers.
ACTIVITY_DAYS = 28
# How far back the student detail looks when ranking struggled topics.
STRUGGLE_DAYS = 30


def empty_bands():
    return {b: 0 for b in BANDS}


_empty_bands = empty_bands


def is_overdue(due_at, status, now):
    """Past its due date without being done (`status` as in `_progress_row`)."""
    return bool(due_at and due_at < now and status != "done")


def band_counts_by_student(student_ids):
    """Map student id -> band counts over that student's selected, usable topics.

    The same population the dashboard donut and `ProficiencySnapshot` count, so
    a student's bar here matches their own progress view. Students with no
    topics get all-zero counts.
    """
    out = {sid: _empty_bands() for sid in student_ids}
    selected = list(
        Topic.objects.filter(
            selections__user_id__in=student_ids, generator_name__isnull=False
        ).values_list("selections__user_id", "id")
    )
    intervals = {
        (uid, tid): interval
        for uid, tid, interval in TopicReview.objects.filter(
            user_id__in=student_ids
        ).values_list("user_id", "topic_id", "interval")
    }
    for uid, tid in selected:
        out[uid][_interval_band(intervals.get((uid, tid), 0))] += 1
    return out


def struggled_topics(student_ids, topic_ids=None, since=None, limit=3):
    """The topics these students got wrong most often, worst first.

    Ranks topics by first-try accuracy over the students' answered cards (a
    second-attempt correct counts as a struggle, like an outright miss), ties
    broken by more answers. Topics every answer got right first time aren't
    struggles and are left out, so the list may be shorter than `limit` — or
    empty when there's nothing to flag. Optionally restricted to `topic_ids`
    and to answers on or after the date `since`.
    """
    if not student_ids:
        return []
    records = AnswerRecord.objects.filter(user_id__in=student_ids)
    if topic_ids is not None:
        records = records.filter(topic_id__in=topic_ids)
    if since is not None:
        records = records.filter(date__gte=since)
    missed = ~Q(outcome="correct_first")
    rows = (
        records.values("topic_id", "topic__topic_name", "topic__course__course_name")
        .annotate(
            answers=Count("id"),
            misses=Count("id", filter=missed),
            students=Count("user_id", distinct=True, filter=missed),
        )
        .filter(misses__gt=0)
    )
    ranked = sorted(rows, key=lambda r: (-r["misses"] / r["answers"], -r["answers"], r["topic_id"]))
    return [
        {
            "topic_id": r["topic_id"],
            "topic_name": r["topic__topic_name"],
            "course_name": r["topic__course__course_name"] or "",
            "answers": r["answers"],
            "accuracy": round((r["answers"] - r["misses"]) / r["answers"] * 100),
            "students": r["students"],
        }
        for r in ranked[:limit]
    ]


def practice_activity(student, today):
    """A student's recent practice: consistency over 4 weeks, and the last 7 days.

    `days` is one entry per day of the last `ACTIVITY_DAYS` (oldest first),
    tagged "completed" / "partial" / "none" like the dashboard calendar.
    `streak` counts consecutive practiced days ending today — or yesterday, so
    a student who hasn't practiced *yet* today doesn't read as having broken
    it (capped at the window's length). The week figures cover today and the six days before: cards answered
    (from `DailyPractice`, so it includes days before answers were logged),
    seconds spent and first-try accuracy (from `AnswerRecord`; accuracy is
    None when nothing was answered).
    """
    start = today - datetime.timedelta(days=ACTIVITY_DAYS - 1)
    practice = {
        rec.date: rec
        for rec in DailyPractice.objects.filter(user=student, date__gte=start, date__lte=today)
    }

    def status(day):
        rec = practice.get(day)
        if rec is None or rec.answered <= 0:
            return "none"
        return "completed" if rec.total > 0 and rec.answered >= rec.total else "partial"

    days = []
    for i in range(ACTIVITY_DAYS):
        day = start + datetime.timedelta(days=i)
        days.append({"date": day.isoformat(), "status": status(day)})

    streak = 0
    day = today if status(today) != "none" else today - datetime.timedelta(days=1)
    while day >= start and status(day) != "none":
        streak += 1
        day -= datetime.timedelta(days=1)

    week_start = today - datetime.timedelta(days=6)
    week = AnswerRecord.objects.filter(
        user=student, date__gte=week_start, date__lte=today
    ).aggregate(
        answers=Count("id"),
        first_try=Count("id", filter=Q(outcome="correct_first")),
        seconds=Sum("seconds"),
    )
    return {
        "days": days,
        "days_practiced": sum(1 for d in days if d["status"] != "none"),
        "streak": streak,
        "week": {
            "cards_answered": sum(
                rec.answered for d, rec in practice.items() if d >= week_start
            ),
            "seconds": week["seconds"] or 0,
            "accuracy": (
                round(week["first_try"] / week["answers"] * 100) if week["answers"] else None
            ),
        },
    }


def activity_by_student(student_ids, today, days=7):
    """Each student's practice over the `days` days ending `today`, in bulk.

    Maps student id -> {"cards", "answers", "first_try", "seconds",
    "accuracy", "last_active"}: cards counted like `practice_activity`'s
    week (from `DailyPractice`), answers / first-try / seconds / accuracy
    from `AnswerRecord` (accuracy None when nothing was answered), and
    `last_active` the latest day on or before `today` they practiced at all
    (None if never). Three grouped queries, whatever the group size.
    """
    start = today - datetime.timedelta(days=days - 1)
    out = {
        sid: {"cards": 0, "answers": 0, "first_try": 0, "seconds": 0, "accuracy": None, "last_active": None}
        for sid in student_ids
    }
    if not out:
        return out
    for row in (
        DailyPractice.objects.filter(user_id__in=student_ids, date__gte=start, date__lte=today)
        .values("user_id").annotate(cards=Sum("answered"))
    ):
        out[row["user_id"]]["cards"] = row["cards"] or 0
    for row in (
        AnswerRecord.objects.filter(user_id__in=student_ids, date__gte=start, date__lte=today)
        .values("user_id")
        .annotate(
            answers=Count("id"),
            first_try=Count("id", filter=Q(outcome="correct_first")),
            seconds=Sum("seconds"),
        )
    ):
        rec = out[row["user_id"]]
        rec["answers"] = row["answers"]
        rec["first_try"] = row["first_try"]
        rec["seconds"] = row["seconds"] or 0
        rec["accuracy"] = round(row["first_try"] / row["answers"] * 100) if row["answers"] else None
    for row in (
        DailyPractice.objects.filter(user_id__in=student_ids, answered__gt=0, date__lte=today)
        .values("user_id").annotate(last=Max("date"))
    ):
        out[row["user_id"]]["last_active"] = row["last"]
    return out


def pooled_accuracy(activity):
    """First-try accuracy (0-100) over every answer in an `activity_by_student` map."""
    answers = sum(a["answers"] for a in activity.values())
    first = sum(a["first_try"] for a in activity.values())
    return round(first / answers * 100) if answers else None


def weekly_goals(student_ids):
    """Map student id -> cards per week they need to be "on track"."""
    per_day = dict(
        Settings.objects.filter(user_id__in=student_ids).values_list("user_id", "questions_per_day")
    )
    return {
        sid: WEEKLY_GOAL_DAYS * (per_day.get(sid) or DEFAULT_QUESTIONS_PER_DAY)
        for sid in student_ids
    }


def band_matrix(student_ids, topic_ids, today, missed_days=14):
    """Each student's standing on each topic, for the class progress grid.

    Maps (student id, topic id) -> {"band", "missed_recent"} for pairs the
    student has answered at least once: `band` from their SM-2 interval, and
    `missed_recent` whether they got one of its cards wrong first try in the
    last `missed_days` days. Pairs never practiced are absent ("not started").
    """
    if not student_ids or not topic_ids:
        return {}
    since = today - datetime.timedelta(days=missed_days - 1)
    intervals = {
        (uid, tid): interval
        for uid, tid, interval in TopicReview.objects.filter(
            user_id__in=student_ids, topic_id__in=topic_ids
        ).values_list("user_id", "topic_id", "interval")
    }
    out = {}
    for row in (
        AnswerRecord.objects.filter(user_id__in=student_ids, topic_id__in=topic_ids, date__lte=today)
        .values("user_id", "topic_id")
        .annotate(missed=Count("id", filter=~Q(outcome="correct_first") & Q(date__gte=since)))
    ):
        key = (row["user_id"], row["topic_id"])
        out[key] = {
            "band": _interval_band(intervals.get(key, 0)),
            "missed_recent": row["missed"] > 0,
        }
    return out
