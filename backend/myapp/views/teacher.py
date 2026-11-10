import datetime
import logging
import statistics

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import (
    Assignment, Classroom, ClassEnrollment, Topic, TopicReview, Settings,
    AssignmentClass, AssignmentTopic, StudentAssignment, AnswerRecord,
    DailyTopicGrade, UserTopicSelection,
)
from .common import _require_teacher
from .deck import _client_today, _effective_due_dates, _interval_band, _ordered_topics
from .dashboard import _topic_stats
from .assignments import (
    _NO_PROGRESS, _progress_by_assignment, _teacher_progress, assignment_summaries, overdue_by_student,
)
from .insights import (
    BANDS, STRUGGLE_DAYS, activity_by_student, is_overdue, pooled_accuracy, practice_activity,
    struggled_topics, weekly_goals,
)

logger = logging.getLogger(__name__)

_BANDS = BANDS

# Overview focus columns: how far back an assignment counts as newly taught,
# how far back weak spots look (and how far back their "missed it" count
# looks), and how many topics each column lists.
NEW_DAYS = 14
WEAK_DAYS = 30
MISSED_DAYS = 14
FOCUS_LIMIT = 5

# Home "needs attention": at most this many items; a student counts as
# inactive after this many days without practice; "not started" alerts cover
# assignments due within this many hours; "needs help" looks back this far;
# trouble spots are topics under this first-try accuracy.
ATTENTION_LIMIT = 6
INACTIVE_DAYS = 7
NOT_STARTED_HOURS = 48
NEEDS_HELP_DAYS = 14
TROUBLE_ACCURACY = 70
TROUBLE_LIMIT = 2
DUE_SOON_DAYS = 7
DUE_SOON_LIMIT = 5
_SEVERITY_ORDER = {"crit": 0, "warn": 1, "info": 2}


@csrf_exempt
@require_http_methods(["GET"])
def teacher_overview(request):
    """Summary across all of the teacher's classes: how many classes and students.

    Familiarity-over-time (the proficiency trend) is served separately by
    `proficiency_history`; this endpoint just sizes the classes for the overview
    cards.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    classes_out = []
    total_students = 0
    for c in (
        Classroom.objects.filter(teacher=request.user, archived=False)
        .annotate(n=Count("enrollments", distinct=True))
        .order_by("-created_at")
    ):
        total_students += c.n
        classes_out.append({
            "id": c.id,
            "name": c.name,
            "student_count": c.n,
        })
    return JsonResponse({
        "classes": classes_out,
        "total_students": total_students,
    })


def _focus_assignments(teacher, student_ids, class_id):
    """These students' started `StudentAssignment` rows for the teacher's assignments.

    `class_id` narrows to assignments reaching them through that class.
    """
    rows = StudentAssignment.objects.filter(
        student_id__in=student_ids, assignment__teacher=teacher,
        started_at__isnull=False,
    )
    if class_id is not None:
        rows = rows.filter(classroom_id=class_id)
    return rows


def _first_assigned(teacher, student_ids, class_id, topic_ids):
    """Map topic id -> the local date the teacher's assignments first brought
    it to any of these students. Topics never assigned to them are absent.
    """
    started = {}  # assignment id -> earliest start among these students
    for aid, at in _focus_assignments(teacher, student_ids, class_id).values_list(
        "assignment_id", "started_at"
    ):
        day = timezone.localdate(at)
        started[aid] = min(day, started.get(aid, day))
    first = {}
    for aid, tid in AssignmentTopic.objects.filter(
        assignment_id__in=started, topic_id__in=topic_ids
    ).values_list("assignment_id", "topic_id"):
        first[tid] = min(started[aid], first.get(tid, started[aid]))
    return first


def _mean_rate(rates):
    """The mean of per-student first-try rates (0-1) as a 0-100 percentage."""
    return round(sum(rates) / len(rates) * 100) if rates else None


def _student_rates(student_ids, topic_ids=None, since=None):
    """Per topic, each student's first-try accuracy rate on it (0-1).

    Returns topic id -> {"topic_name", "rates": [one per student who
    answered], "missed": whether any answer wasn't right first try}, over
    answers on or after `since` (all time when None).
    """
    records = AnswerRecord.objects.filter(user_id__in=student_ids)
    if topic_ids is not None:
        records = records.filter(topic_id__in=topic_ids)
    if since is not None:
        records = records.filter(date__gte=since)
    out = {}
    for row in (
        records.values("topic_id", "topic__topic_name", "user_id")
        .annotate(answers=Count("id"), right=Count("id", filter=Q(outcome="correct_first")))
    ):
        topic = out.setdefault(row["topic_id"], {
            "topic_name": row["topic__topic_name"], "rates": [], "missed": False,
        })
        topic["rates"].append(row["right"] / row["answers"])
        topic["missed"] |= row["right"] < row["answers"]
    return out


def _newly_taught(teacher, student_ids, class_id, today):
    """Topics the teacher's assignments added to these students' decks lately.

    A topic is newly taught for a student when an assignment of this teacher
    carrying it reached them (`StudentAssignment.started_at`) in the last
    `NEW_DAYS` days; `class_id` narrows to assignments reaching them through
    that class. Per topic, newest first assignment first and then lowest
    accuracy: when it was first assigned to these students, their average first-try accuracy since it
    reached them (each student counts once; None until someone practices),
    and the current band mix across those students.
    """
    since = timezone.now() - datetime.timedelta(days=NEW_DAYS)
    rows = _focus_assignments(teacher, student_ids, class_id).filter(started_at__gte=since)
    # assignment id -> {student id: local date it reached them}
    started = {}
    for sid, aid, at in rows.values_list("student_id", "assignment_id", "started_at"):
        started.setdefault(aid, {})[sid] = timezone.localdate(at)
    if not started:
        return []

    # topic id -> {student id: earliest date the topic reached them}
    reached = {}
    names = {}
    for aid, tid, name in AssignmentTopic.objects.filter(
        assignment_id__in=started
    ).values_list("assignment_id", "topic_id", "topic__topic_name"):
        names[tid] = name
        per = reached.setdefault(tid, {})
        for sid, day in started[aid].items():
            per[sid] = min(day, per.get(sid, day))
    if not reached:
        return []

    sids = {sid for per in reached.values() for sid in per}
    intervals = {
        (uid, tid): interval
        for uid, tid, interval in TopicReview.objects.filter(
            user_id__in=sids, topic_id__in=reached
        ).values_list("user_id", "topic_id", "interval")
    }
    # Each student's (answers, right first try) per topic since it reached them.
    tallies = {}
    for uid, tid, day, outcome in AnswerRecord.objects.filter(
        user_id__in=sids, topic_id__in=reached
    ).values_list("user_id", "topic_id", "date", "outcome"):
        if uid in reached[tid] and day >= reached[tid][uid]:
            n, right = tallies.get((uid, tid), (0, 0))
            tallies[(uid, tid)] = (n + 1, right + (outcome == "correct_first"))
    first = _first_assigned(teacher, student_ids, class_id, reached)

    out = []
    for tid in reached:
        bands = {b: 0 for b in _BANDS}
        rates = []
        for sid in reached[tid]:
            bands[_interval_band(intervals.get((sid, tid), 0))] += 1
            if (sid, tid) in tallies:
                n, right = tallies[(sid, tid)]
                rates.append(right / n)
        out.append({
            "topic_id": tid,
            "topic_name": names[tid],
            "first_assigned": first[tid].isoformat(),
            "accuracy": _mean_rate(rates),
            "proficiency": bands,
        })
    # Most recently first assigned first; on the same day, lowest accuracy
    # first, with topics nobody has practiced yet after those.
    out.sort(key=lambda t: (
        -datetime.date.fromisoformat(t["first_assigned"]).toordinal(),
        t["accuracy"] is None, t["accuracy"] or 0, t["topic_id"],
    ))
    return out[:FOCUS_LIMIT]


def _weak_spots(student_ids, since, today):
    """Topics with the lowest average first-try accuracy per student, worst first.

    Each student's first-try accuracy on a topic (answers on or after `since`)
    counts once, so a student who answered a topic many times doesn't outweigh
    classmates who answered it a few times; `accuracy` is the mean of those.
    Ties go to the topic more students answered. `missed_recent` counts the
    students who got one of the topic's cards wrong first try in the last
    `MISSED_DAYS` days; topics nobody got wrong in that time aren't weak spots
    and are left out.
    """
    missed = dict(
        AnswerRecord.objects.filter(
            user_id__in=student_ids,
            date__gte=today - datetime.timedelta(days=MISSED_DAYS - 1),
        )
        .exclude(outcome="correct_first")
        .values("topic_id")
        .annotate(n=Count("user_id", distinct=True))
        .values_list("topic_id", "n")
    )
    rates = _student_rates(student_ids, topic_ids=missed, since=since)
    worst = sorted(
        rates, key=lambda tid: (_mean_rate(rates[tid]["rates"]), -len(rates[tid]["rates"]), tid),
    )[:FOCUS_LIMIT]
    return [
        {
            "topic_id": tid,
            "topic_name": rates[tid]["topic_name"],
            "accuracy": _mean_rate(rates[tid]["rates"]),
            "missed_recent": missed[tid],
        }
        for tid in worst
    ]


@csrf_exempt
@require_http_methods(["GET"])
def overview_focus(request):
    """The overview's two focus columns for a group of students.

    Scoped like `proficiency_history` (``scope=all``, or ``scope=class`` with
    ``class_id``):

    - ``newly_taught``: topics recent assignments added to their decks, with
      how well the students are doing on them (see `_newly_taught`);
    - ``weak_spots``: the topics with the lowest average first-try accuracy
      per student over the last `WEAK_DAYS` days, i.e. what to reteach (see
      `_weak_spots`).
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    student_ids, err = _resolve_history_students(request)
    if err:
        return err
    today = _client_today(request)
    class_id = (
        int(request.GET["class_id"]) if request.GET.get("scope") == "class" else None
    )
    return JsonResponse({
        "newly_taught": _newly_taught(request.user, student_ids, class_id, today),
        "weak_spots": _weak_spots(
            student_ids, since=today - datetime.timedelta(days=WEAK_DAYS - 1), today=today,
        ),
        "windows": {"new_days": NEW_DAYS, "missed_days": MISSED_DAYS},
    })


def _display_name(user):
    return user.get_full_name() or user.username or user.email


def _home_class_of(teacher, student_ids):
    """Map student id -> the first (oldest) of the teacher's classes they're in."""
    out = {}
    for sid, cid in (
        ClassEnrollment.objects.filter(student_id__in=student_ids, classroom__teacher=teacher)
        .order_by("classroom__created_at", "classroom_id")
        .values_list("student_id", "classroom_id")
    ):
        out.setdefault(sid, cid)
    return out


def _attention_items(teacher, student_ids, class_id, today, now, week, assignments, summaries):
    """The ranked "needs attention" list for the teacher home (see `overview_summary`)."""
    User = get_user_model()
    names = {u.id: _display_name(u) for u in User.objects.filter(id__in=student_ids)}
    home = {sid: class_id for sid in student_ids} if class_id else _home_class_of(teacher, student_ids)
    ids = set(student_ids)
    items = []

    overdue = overdue_by_student(assignments, now, class_id=class_id)
    for sid in student_ids:
        late = overdue.get(sid, [])
        last = week[sid]["last_active"]
        idle = (today - last).days if last else None
        # Only students who practiced before and stopped count as inactive, so
        # a brand-new roster isn't all alerts.
        inactive = idle is not None and idle >= INACTIVE_DAYS
        if not late and not inactive:
            continue
        severity = "crit" if late and (inactive or len(late) > 1) else "warn"
        items.append({
            "type": "student", "severity": severity, "student_id": sid,
            "name": names.get(sid, "(unknown)"), "class_id": home.get(sid),
            "overdue": [a["title"] for a in late], "inactive_days": idle if inactive else None,
            "_rank": (-len(late), -(idle or 0)),
        })

    for row in (
        StudentAssignment.objects.filter(
            assignment__in=assignments, student_id__in=ids, max_reached=True,
            completed_at__gte=now - datetime.timedelta(days=NEEDS_HELP_DAYS),
        ).select_related("assignment").order_by("-completed_at")
    ):
        if class_id and row.classroom_id != class_id:
            continue
        items.append({
            "type": "needs_help", "severity": "warn", "student_id": row.student_id,
            "name": names.get(row.student_id, "(unknown)"), "class_id": row.classroom_id,
            "assignment_id": row.assignment_id, "title": row.assignment.title,
            "_rank": (0, 0),
        })

    since = today - datetime.timedelta(days=WEAK_DAYS - 1)
    spots = [w for w in _weak_spots(student_ids, since, today) if w["accuracy"] < TROUBLE_ACCURACY]
    for spot in spots[:TROUBLE_LIMIT]:
        missed_ids = (
            AnswerRecord.objects.filter(
                user_id__in=student_ids, topic_id=spot["topic_id"],
                date__gte=today - datetime.timedelta(days=MISSED_DAYS - 1),
            ).exclude(outcome="correct_first").values_list("user_id", flat=True).distinct()
        )
        students = sorted(
            ({"id": sid, "name": names.get(sid, "(unknown)")} for sid in set(missed_ids)),
            key=lambda st: st["name"].lower(),
        )
        items.append({
            "type": "trouble_spot", "severity": "info", "topic_id": spot["topic_id"],
            "topic_name": spot["topic_name"], "accuracy": spot["accuracy"], "students": students,
            "_rank": (spot["accuracy"], 0),
        })

    soon = now + datetime.timedelta(hours=NOT_STARTED_HOURS)
    for a in assignments:
        info = summaries[a.id]
        for link in info["classes"]:
            due = link["due_at"] and datetime.datetime.fromisoformat(link["due_at"])
            if not due or not (now <= due <= soon):
                continue
            waiting = info["counts"]["not_started"]
            if waiting:
                items.append({
                    "type": "not_started", "severity": "warn", "assignment_id": a.id,
                    "title": a.title, "count": waiting, "due_at": link["due_at"],
                    "class_name": link["class_name"], "class_id": link["class_id"],
                    "_rank": (-waiting, 0),
                })
            break

    items.sort(key=lambda i: (_SEVERITY_ORDER[i["severity"]], i["_rank"]))
    for item in items:
        del item["_rank"]
    return items[:ATTENTION_LIMIT]


@csrf_exempt
@require_http_methods(["GET"])
def overview_summary(request):
    """The teacher home: headline numbers, what needs attention, and what's due soon.

    Scoped like `proficiency_history` (``scope=all``, or ``scope=class`` with
    ``class_id``), over the 7 days ending the client's ``today``:

    - ``kpis``: students on track for their weekly goal (`insights.weekly_goals`)
      and how many were last week, cards answered, cards per active student,
      first-try accuracy this week and last, and overdue student-assignments;
    - ``needs_attention``: up to `ATTENTION_LIMIT` items, most urgent first —
      students overdue and/or gone quiet, students who finished at the card cap
      without getting solid ("needs help"), trouble-spot topics with who
      missed them, and assignments due soon that students haven't started;
    - ``due_soon``: open assignments due in the next `DUE_SOON_DAYS` days.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    student_ids, err = _resolve_history_students(request)
    if err:
        return err
    today = _client_today(request)
    now = timezone.now()
    class_id = int(request.GET["class_id"]) if request.GET.get("scope") == "class" else None

    week = activity_by_student(student_ids, today)
    last_week = activity_by_student(student_ids, today - datetime.timedelta(days=7))
    goals = weekly_goals(student_ids)
    active = [sid for sid in student_ids if week[sid]["cards"] > 0]
    cards = sum(week[sid]["cards"] for sid in student_ids)

    assignments = Assignment.objects.filter(teacher=request.user)
    if class_id:
        assignments = assignments.filter(class_links__classroom_id=class_id)
    assignments = list(assignments.distinct().order_by("-created_at"))
    summaries = assignment_summaries(assignments, now, class_id=class_id)
    ids = set(student_ids)
    overdue = overdue_by_student(assignments, now, class_id=class_id)

    due_soon = []
    horizon = now + datetime.timedelta(days=DUE_SOON_DAYS)
    for a in assignments:
        info = summaries[a.id]
        due = info["next_due_at"] and datetime.datetime.fromisoformat(info["next_due_at"])
        if due and now <= due <= horizon and info["counts"]["assigned"]:
            due_soon.append({"id": a.id, "title": a.title, **info})
    due_soon.sort(key=lambda d: d["next_due_at"])

    return JsonResponse({
        "kpis": {
            "students": len(student_ids),
            "on_track": sum(1 for sid in student_ids if week[sid]["cards"] >= goals[sid]),
            "on_track_prev": sum(1 for sid in student_ids if last_week[sid]["cards"] >= goals[sid]),
            "goal_cards": statistics.median(goals.values()) if goals else None,
            "active": len(active),
            "cards_7d": cards,
            "cards_per_active": round(cards / len(active)) if active else None,
            "accuracy_7d": pooled_accuracy(week),
            "accuracy_prev_7d": pooled_accuracy(last_week),
            "overdue": sum(len(v) for sid, v in overdue.items() if sid in ids),
        },
        "needs_attention": _attention_items(
            request.user, student_ids, class_id, today, now, week, assignments, summaries,
        ),
        "due_soon": due_soon[:DUE_SOON_LIMIT],
    })


def _resolve_history_students(request):
    """Resolve the student id set for a proficiency-history request, or an error.

    Returns (student_ids, error_response). Scope is one of:
      - ``all`` (default): every student enrolled in one of the teacher's classes;
      - ``class`` (needs ``class_id``): the roster of one of the teacher's classes;
      - ``student`` (needs ``student_id``): a single student the teacher can view.
    """
    scope = request.GET.get("scope", "all")
    if scope == "student":
        try:
            sid = int(request.GET.get("student_id"))
        except (TypeError, ValueError):
            return None, JsonResponse({"error": "student_id required"}, status=400)
        if not _teacher_can_view_student(request.user, sid):
            return None, JsonResponse({"error": "Not your student"}, status=403)
        return [sid], None
    if scope == "class":
        try:
            cid = int(request.GET.get("class_id"))
        except (TypeError, ValueError):
            return None, JsonResponse({"error": "class_id required"}, status=400)
        if not Classroom.objects.filter(id=cid, teacher=request.user).exists():
            return None, JsonResponse({"error": "Not your class"}, status=403)
        ids = list(
            ClassEnrollment.objects.filter(classroom_id=cid).values_list("student_id", flat=True)
        )
        return ids, None
    # Default: all students across the teacher's classes (distinct).
    ids = list(
        ClassEnrollment.objects.filter(classroom__teacher=request.user)
        .values_list("student_id", flat=True)
        .distinct()
    )
    return ids, None


def _topic_band_history(student_ids, start, end):
    """Per day from `start` to `end`: how many of the group's topics sit in each band.

    The group's topics are the usable topics its students have selected. A
    topic joins the count on the first day it reached any of them: the
    earliest of an assignment bringing it to them and their first graded day
    on it (a topic selected but never assigned or practiced counts from
    `end`). Each day, a topic's band is that of its *average* SM-2 interval
    across the students who had it by then (0 until a student practices it),
    so for one student it's simply their own band.

    Past intervals are rebuilt from `DailyTopicGrade`, which snapshots a
    topic's state before each graded day: the interval at the end of day `d`
    is the snapshot of the first graded day after `d`, or the current
    `TopicReview.interval` when there is none. Days with no topics are left
    out. Deselected topics drop out entirely (selections keep no history).
    """
    pairs = set(
        UserTopicSelection.objects.filter(
            user_id__in=student_ids, topic__generator_name__isnull=False
        ).values_list("user_id", "topic_id")
    )
    if not pairs:
        return []
    topic_ids = {tid for _, tid in pairs}
    current = {
        (uid, tid): interval
        for uid, tid, interval in TopicReview.objects.filter(
            user_id__in=student_ids, topic_id__in=topic_ids
        ).values_list("user_id", "topic_id", "interval")
    }
    grades = {}  # (user, topic) -> [(date, interval before that day's grade)], oldest first
    for uid, tid, day, interval in (
        DailyTopicGrade.objects.filter(user_id__in=student_ids, topic_id__in=topic_ids)
        .order_by("date")
        .values_list("user_id", "topic_id", "date", "snapshot_interval")
    ):
        if (uid, tid) in pairs:
            grades.setdefault((uid, tid), []).append((day, interval))
    added = {}  # (user, topic) -> first day the topic reached the student
    for uid, tid, at in StudentAssignment.objects.filter(
        student_id__in=student_ids, started_at__isnull=False
    ).values_list("student_id", "assignment__assignment_topics__topic_id", "started_at"):
        if (uid, tid) in pairs:
            day = timezone.localdate(at)
            added[(uid, tid)] = min(day, added.get((uid, tid), day))

    # Sweep events: on its added day a pair joins its topic with the interval
    # it ended that day on; each later graded day shifts the topic's sum.
    events = {}  # date -> [(topic, interval delta, student delta)]
    for pair in pairs:
        gs = grades.get(pair, [])
        first = min(filter(None, [added.get(pair), gs[0][0] if gs else None]), default=end)

        def after(i):
            return gs[i + 1][1] if i + 1 < len(gs) else current.get(pair, 0)

        later = [i for i, (day, _) in enumerate(gs) if day > first]
        value = gs[later[0]][1] if later else current.get(pair, 0)
        events.setdefault(first, []).append((pair[1], value, 1))
        for i in later:
            events.setdefault(gs[i][0], []).append((pair[1], after(i) - value, 0))
            value = after(i)

    sums, counts = {}, {}

    def apply(day):
        for tid, d_sum, d_count in events.get(day, ()):
            sums[tid] = sums.get(tid, 0) + d_sum
            counts[tid] = counts.get(tid, 0) + d_count

    for day in sorted(d for d in events if d < start):
        apply(day)
    series = []
    day = start
    while day <= end:
        apply(day)
        point = {b: 0 for b in _BANDS}
        for tid, n in counts.items():
            if n:
                point[_interval_band(sums[tid] / n)] += 1
        if any(point.values()):
            series.append({"date": day.isoformat(), **point})
        day += datetime.timedelta(days=1)
    return series


@csrf_exempt
@require_http_methods(["GET"])
def proficiency_history(request):
    """Familiarity-over-time series: number of topics in each proficiency band per day.

    For a group, each topic is banded by the students' average familiarity
    with it, so the bars count topics, not students (see
    `_topic_band_history`). The count grows as topics are added through the
    year.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    student_ids, err = _resolve_history_students(request)
    if err:
        return err

    try:
        days = max(7, min(365, int(request.GET.get("days", 90))))
    except (TypeError, ValueError):
        days = 90
    end = _client_today(request)
    start = end - datetime.timedelta(days=days - 1)
    if not student_ids:
        return JsonResponse({"series": []})
    return JsonResponse({"series": _topic_band_history(student_ids, start, end)})


def _teacher_can_view_student(teacher, student_id):
    """True if the student is enrolled in at least one of the teacher's classes."""
    return ClassEnrollment.objects.filter(
        student_id=student_id, classroom__teacher=teacher
    ).exists()


@csrf_exempt
@require_http_methods(["GET"])
def student_detail(request, student_id):
    """One student's progress, for a teacher who has them in a class.

    Combines the same SM-2 topic stats the student's own dashboard shows with
    their assignment history: for each assignment reaching the student, how many
    of its cards they've answered and whether they're overdue. `activity` is
    their recent practice (consistency, this week's cards, time and accuracy;
    see `practice_activity`) and `struggled` the topics they've missed most
    over the last `STRUGGLE_DAYS` days.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    if not _teacher_can_view_student(request.user, student_id):
        return JsonResponse({"error": "Not your student"}, status=403)
    User = get_user_model()
    student = User.objects.filter(id=student_id).first()
    if student is None:
        return JsonResponse({"error": "Student not found"}, status=404)

    today = _client_today(request)
    selected_topics = list(
        Topic.objects.filter(selections__user=student).select_related("course").distinct()
    )
    due = _effective_due_dates(student, selected_topics, today)
    reviews = {
        r.topic_id: r
        for r in TopicReview.objects.filter(user=student, topic__in=selected_topics)
    }
    selected_topics.sort(key=lambda t: (due[t.id], t.id))
    topics = [_topic_stats(t, reviews.get(t.id), due[t.id]) for t in selected_topics]

    # "Shown soon" — the head of the student's own next practice deck, mirroring
    # the dashboard exactly so the teacher sees the same progress view.
    limit = Settings.load(student).questions_per_day
    ordered = _ordered_topics(student, today)[:limit]
    up_due = _effective_due_dates(student, ordered, today)
    up_reviews = {
        r.topic_id: r
        for r in TopicReview.objects.filter(user=student, topic__in=ordered)
    }
    upcoming = [_topic_stats(t, up_reviews.get(t.id), up_due[t.id]) for t in ordered]

    # Assignments reaching this student through the teacher's classes, with how
    # many of each one's cards they've answered. Earliest-due link per
    # assignment wins the due date.
    now = timezone.now()
    student_class_ids = list(
        ClassEnrollment.objects.filter(student=student).values_list("classroom_id", flat=True)
    )
    links = (
        AssignmentClass.objects.filter(
            classroom_id__in=student_class_ids, classroom__teacher=request.user
        )
        .select_related("assignment", "classroom")
        .order_by("due_at", "id")
    )
    progress = _progress_by_assignment(student)
    assignments_out = []
    seen = set()
    for link in links:
        a = link.assignment
        if a.id in seen:
            continue
        seen.add(a.id)
        row = _teacher_progress(progress.get(a.id, _NO_PROGRESS), a.deck_size)
        assignments_out.append({
            "assignment_id": a.id,
            "title": a.title,
            "class_id": link.classroom_id,
            "class_name": link.classroom.name,
            **row,
            "deck_size": a.deck_size,
            "assigned_at": link.assigned_at.isoformat(),
            "due_at": link.due_at.isoformat() if link.due_at else None,
            "overdue": is_overdue(link.due_at, row["status"], now),
        })

    # The teacher's classes the student is in (oldest first), and how the
    # student compares with one of them: `?class=` if given, else the first.
    classes = list(
        Classroom.objects.filter(teacher=request.user, enrollments__student=student)
        .order_by("created_at", "id").distinct()
    )
    try:
        wanted = int(request.GET.get("class", ""))
    except ValueError:
        wanted = None
    bench_class = next((c for c in classes if c.id == wanted), classes[0] if classes else None)
    benchmarks = None
    if bench_class is not None:
        roster = list(
            ClassEnrollment.objects.filter(classroom=bench_class).values_list("student_id", flat=True)
        )
        week = activity_by_student(roster, today)
        month = activity_by_student(roster, today, days=STRUGGLE_DAYS)
        benchmarks = {
            "class_id": bench_class.id,
            "class_name": bench_class.name,
            "cards_7d_median": statistics.median(w["cards"] for w in week.values()),
            "seconds_7d_median": statistics.median(w["seconds"] for w in week.values()),
            "accuracy_30d_class": pooled_accuracy(month),
            "accuracy_30d": month[student.id]["accuracy"] if student.id in month else None,
        }

    # Per-topic first-try accuracy over the same window as `struggled`.
    month_start = today - datetime.timedelta(days=STRUGGLE_DAYS - 1)
    topic_acc = {
        row["topic_id"]: round(row["right"] / row["answers"] * 100)
        for row in AnswerRecord.objects.filter(user=student, date__gte=month_start, date__lte=today)
        .values("topic_id")
        .annotate(answers=Count("id"), right=Count("id", filter=Q(outcome="correct_first")))
    }
    for t in topics:
        t["accuracy_30d"] = topic_acc.get(t["id"])

    return JsonResponse({
        "student": {
            "id": student.id,
            "name": (student.get_full_name() or student.username or student.email),
            "email": student.email,
        },
        "classes": [{"id": c.id, "name": c.name} for c in classes],
        "benchmarks": benchmarks,
        "topics": topics,
        "upcoming": upcoming,
        "assignments": assignments_out,
        "activity": practice_activity(student, today),
        "struggled": struggled_topics(
            [student.id], since=today - datetime.timedelta(days=STRUGGLE_DAYS - 1),
        ),
    })
