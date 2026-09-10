import datetime
import logging

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import (
    Classroom, ClassEnrollment, Topic, TopicReview, StudentAssignment, Settings,
    ProficiencySnapshot, AssignmentClass, DailyTopicGrade,
)
from .common import _require_teacher
from .deck import _client_today, _effective_due_dates, _ordered_topics
from .dashboard import _topic_stats

logger = logging.getLogger(__name__)

_BANDS = ("new", "learning", "familiar", "proficient")


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


@csrf_exempt
@require_http_methods(["GET"])
def proficiency_history(request):
    """Familiarity-over-time series: % of topics in each proficiency band per day.

    Averages each student's per-band percentage across the resolved student set,
    for each day in the window. Each student's mix is forward-filled from their
    most recent `ProficiencySnapshot` on or before the day (snapshots are written
    only on active days), and students with no topics selected yet don't
    contribute to that day's average. Values are percentages (0-100).
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
        return JsonResponse({"series": [], "student_count": 0})

    # Per-student ascending list of (date, band-percentages). Includes snapshots
    # before the window so the first in-window day forward-fills correctly.
    per_student = {sid: [] for sid in student_ids}
    for snap in (
        ProficiencySnapshot.objects.filter(user_id__in=student_ids, date__lte=end)
        .order_by("user_id", "date")
    ):
        if snap.total <= 0:
            per_student[snap.user_id].append((snap.date, None))
            continue
        pct = {b: getattr(snap, b) / snap.total * 100 for b in _BANDS}
        per_student[snap.user_id].append((snap.date, pct))

    pointers = {sid: 0 for sid in student_ids}
    latest = {sid: None for sid in student_ids}  # last-known pct dict (or None)
    series = []
    day = start
    while day <= end:
        # Advance each student's pointer to the latest snapshot on/before `day`.
        for sid in student_ids:
            snaps = per_student[sid]
            i = pointers[sid]
            while i < len(snaps) and snaps[i][0] <= day:
                latest[sid] = snaps[i][1]
                i += 1
            pointers[sid] = i
        contributors = [latest[sid] for sid in student_ids if latest[sid] is not None]
        if contributors:
            point = {"date": day.isoformat()}
            for b in _BANDS:
                point[b] = round(sum(c[b] for c in contributors) / len(contributors), 1)
            point["students"] = len(contributors)
            series.append(point)
        day += datetime.timedelta(days=1)

    return JsonResponse({"series": series, "student_count": len(student_ids)})


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
    of its topics they've practiced and whether they're overdue.
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
    # much of each they've practiced (progress lives in the SM-2 schedule, not a
    # per-assignment quiz). Earliest-due link per assignment wins the due date.
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
    started = set(
        StudentAssignment.objects.filter(student=student).values_list("assignment_id", flat=True)
    )
    assignments_out = []
    seen = set()
    for link in links:
        a = link.assignment
        if a.id in seen:
            continue
        seen.add(a.id)
        topic_ids = set(a.assignment_topics.values_list("topic_id", flat=True))
        practiced = set(
            DailyTopicGrade.objects.filter(
                user=student, topic_id__in=topic_ids
            ).values_list("topic_id", flat=True)
        ) if topic_ids else set()
        num_practiced = len(topic_ids & practiced)
        done = bool(topic_ids) and topic_ids.issubset(practiced)
        assignments_out.append({
            "assignment_id": a.id,
            "title": a.title,
            "class_name": link.classroom.name,
            "status": "done" if done else ("in_progress" if a.id in started or num_practiced else "not_started"),
            "num_topics": len(topic_ids),
            "num_practiced": num_practiced,
            "due_at": link.due_at.isoformat() if link.due_at else None,
            "overdue": bool(link.due_at and link.due_at < now and not done),
        })

    return JsonResponse({
        "student": {
            "id": student.id,
            "name": (student.get_full_name() or student.username or student.email),
            "email": student.email,
        },
        "topics": topics,
        "upcoming": upcoming,
        "assignments": assignments_out,
    })
