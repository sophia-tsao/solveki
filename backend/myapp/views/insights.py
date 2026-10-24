"""Read-side helpers behind the teacher views' practice insights.

Shared by the assignment report, class roster and student detail: per-student
proficiency-band counts, the "struggled with most" topic ranking, and a
student's recent practice activity (consistency, volume, time, accuracy).
"""
import datetime

from django.db.models import Count, Q, Sum

from ..models import AnswerRecord, DailyPractice, Topic, TopicReview
from .deck import _interval_band

_BANDS = ("new", "learning", "familiar", "proficient")

# How many days of practice the student detail's consistency strip covers.
ACTIVITY_DAYS = 28
# How far back the student detail looks when ranking struggled topics.
STRUGGLE_DAYS = 30


def _empty_bands():
    return {b: 0 for b in _BANDS}


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
        records.values("topic_id", "topic__topic_name")
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
