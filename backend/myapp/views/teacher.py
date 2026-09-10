import logging

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import (
    Classroom, ClassEnrollment, Topic, TopicReview, StudentAssignment, Settings,
)
from .common import _require_teacher
from .deck import _client_today, _effective_due_dates, _ordered_topics
from .dashboard import _topic_stats

logger = logging.getLogger(__name__)


def _accuracy(correct, total):
    return round(correct / total, 4) if total else None


def _class_accuracy(classroom):
    """(correct, total, completed_count) across all student assignments in a class."""
    correct = total = completed = 0
    sas = StudentAssignment.objects.filter(classroom=classroom).prefetch_related("attempts")
    for sa in sas:
        attempts = list(sa.attempts.all())
        correct += sum(1 for a in attempts if a.is_correct)
        total += len(attempts)
        if sa.status == StudentAssignment.COMPLETED:
            completed += 1
    return correct, total, completed


@csrf_exempt
@require_http_methods(["GET"])
def teacher_overview(request):
    """Summary across all of the teacher's classes: size, activity, accuracy."""
    guard = _require_teacher(request)
    if guard:
        return guard
    classes_out = []
    total_students = 0
    all_correct = all_total = 0
    for c in (
        Classroom.objects.filter(teacher=request.user, archived=False)
        .annotate(n=Count("enrollments", distinct=True))
        .order_by("-created_at")
    ):
        correct, total, completed = _class_accuracy(c)
        all_correct += correct
        all_total += total
        total_students += c.n
        classes_out.append({
            "id": c.id,
            "name": c.name,
            "student_count": c.n,
            "average_accuracy": _accuracy(correct, total),
            "completed_assignments": completed,
        })
    return JsonResponse({
        "classes": classes_out,
        "total_students": total_students,
        "average_accuracy": _accuracy(all_correct, all_total),
    })


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
    their assignment history and accuracy.
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

    assignments_out = []
    for sa in (
        StudentAssignment.objects.filter(student=student, classroom__teacher=request.user)
        .select_related("assignment", "classroom")
        .prefetch_related("attempts")
        .order_by("-started_at")
    ):
        attempts = list(sa.attempts.all())
        correct = sum(1 for a in attempts if a.is_correct)
        assignments_out.append({
            "assignment_id": sa.assignment_id,
            "title": sa.assignment.title,
            "class_name": sa.classroom.name,
            "status": sa.status,
            "accuracy": _accuracy(correct, len(attempts)),
            "answered": len(attempts),
            "started_at": sa.started_at.isoformat() if sa.started_at else None,
            "completed_at": sa.completed_at.isoformat() if sa.completed_at else None,
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
