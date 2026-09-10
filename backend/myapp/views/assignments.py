import json
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import (
    Assignment, AssignmentTopic, AssignmentClass, Classroom, ClassEnrollment,
    StudentAssignment, Topic, UserTopicSelection, TopicReview, DailyTopicGrade,
)
from .common import _require_auth, _require_teacher
from .deck import _client_today, _get_or_create_today_deck, _grow_today_deck, _interval_band

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Assignment model, simplified
# ---------------------------------------------------------------------------
#
# An assignment is a single idea: the teacher picks topics to add to students'
# spaced-repetition decks, and how many cards the deck should hold. The
# teacher-picked topics (stored as `AssignmentTopic` rows) are added to each
# assigned student's own selections when they open the assignment — so the work
# flows through the student's normal daily practice, with SM-2 always scheduling
# it — and those same topics drive the progress report.


def _ensure_selected(student, topics):
    """Add `topics` to `student`'s own selections (idempotent).

    Opening an assignment adds its teacher-picked topics to the student's
    selections, so they show up in the student's normal daily practice deck.
    """
    if not topics:
        return
    existing = set(
        UserTopicSelection.objects.filter(
            user=student, topic__in=topics
        ).values_list("topic_id", flat=True)
    )
    to_create = [
        UserTopicSelection(user=student, topic=t)
        for t in topics if t.id not in existing
    ]
    if to_create:
        UserTopicSelection.objects.bulk_create(to_create, ignore_conflicts=True)


def _assignment_topics(assignment):
    """The assignment's teacher-picked topics that have a usable generator."""
    topic_ids = list(assignment.assignment_topics.values_list("topic_id", flat=True))
    return list(Topic.objects.filter(id__in=topic_ids, generator_name__isnull=False))


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _serialize_assignment(assignment, include_topics=True):
    data = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "deck_size": assignment.deck_size,
        "created_at": assignment.created_at.isoformat(),
    }
    if include_topics:
        data["topics"] = [
            {
                "topic_id": at.topic_id,
                "topic_name": at.topic.topic_name,
                "course_id": at.topic.course_id,
            }
            for at in assignment.assignment_topics.select_related("topic").order_by("id")
        ]
        data["classes"] = [
            {
                "class_id": link.classroom_id,
                "class_name": link.classroom.name,
                "due_at": link.due_at.isoformat() if link.due_at else None,
                "available_at": link.available_at.isoformat() if link.available_at else None,
            }
            for link in assignment.class_links.select_related("classroom")
        ]
    return data


# ---------------------------------------------------------------------------
# Teacher: assignment authoring
# ---------------------------------------------------------------------------

def _apply_assignment_body(assignment, body):
    """Set assignment fields from a create/update body. Returns None or an error response.

    Delivery is fixed: every assignment is a spaced-repetition deck scoped to all
    of each student's selected topics, with SM-2 on. Only the title, description,
    and deck size (the teacher's card count) are teacher-editable.
    """
    if "title" in body:
        title = (body.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "title is required"}, status=400)
        assignment.title = title
    if "description" in body:
        assignment.description = body.get("description") or ""
    if "deck_size" in body:
        try:
            assignment.deck_size = max(1, int(body["deck_size"]))
        except (ValueError, TypeError):
            return JsonResponse({"error": "deck_size must be an integer"}, status=400)
    return None


def _set_assignment_topics(assignment, topics_spec):
    """Replace an assignment's topic list from [{topic_id}, ...].

    These are the topics added to each assigned student's deck. Per-topic counts
    no longer apply (deck size governs the total), so only the topic id matters.
    """
    assignment.assignment_topics.all().delete()
    seen = set()
    rows = []
    for spec in topics_spec or []:
        topic_id = spec.get("topic_id")
        if topic_id is None or topic_id in seen:
            continue
        if not Topic.objects.filter(id=topic_id).exists():
            continue
        seen.add(topic_id)
        rows.append(AssignmentTopic(assignment=assignment, topic_id=topic_id))
    AssignmentTopic.objects.bulk_create(rows)


def _get_owned_assignment(request, assignment_id):
    assignment = Assignment.objects.filter(id=assignment_id).first()
    if assignment is None:
        return None, JsonResponse({"error": "Assignment not found"}, status=404)
    if assignment.teacher_id != request.user.id:
        return None, JsonResponse({"error": "Not your assignment"}, status=403)
    return assignment, None


@csrf_exempt
@require_http_methods(["GET", "POST"])
def assignments(request):
    """List the teacher's assignments, or create one."""
    guard = _require_teacher(request)
    if guard:
        return guard
    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid request body"}, status=400)
        with transaction.atomic():
            assignment = Assignment(teacher=request.user)
            err = _apply_assignment_body(assignment, body)
            if err:
                return err
            if not assignment.title:
                return JsonResponse({"error": "title is required"}, status=400)
            assignment.save()
            _set_assignment_topics(assignment, body.get("topics"))
        logger.info("Teacher %s created assignment %s", request.user.id, assignment.id)
        return JsonResponse(_serialize_assignment(assignment), status=201)

    qs = Assignment.objects.filter(teacher=request.user).order_by("-created_at")
    return JsonResponse({"assignments": [_serialize_assignment(a, include_topics=False) for a in qs]})


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def assignment_detail(request, assignment_id):
    guard = _require_teacher(request)
    if guard:
        return guard
    assignment, err = _get_owned_assignment(request, assignment_id)
    if err:
        return err
    if request.method == "DELETE":
        assignment.delete()
        logger.info("Teacher %s deleted assignment %s", request.user.id, assignment_id)
        return JsonResponse({"ok": True})
    if request.method == "PATCH":
        try:
            body = json.loads(request.body)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid request body"}, status=400)
        with transaction.atomic():
            err = _apply_assignment_body(assignment, body)
            if err:
                return err
            assignment.save()
            if "topics" in body:
                _set_assignment_topics(assignment, body.get("topics"))
    return JsonResponse(_serialize_assignment(assignment))


@csrf_exempt
@require_http_methods(["POST"])
def assign_to_classes(request, assignment_id):
    """Assign (or re-assign) an assignment to a set of classes with due dates.

    Body: {"classes": [{"class_id": 1, "due_at": "...", "available_at": "..."}, ...]}.
    Replaces the assignment's class links with the given set, so the same call
    both assigns to new classes and edits/removes existing ones. Only classes the
    teacher owns are accepted.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    assignment, err = _get_owned_assignment(request, assignment_id)
    if err:
        return err
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)
    specs = body.get("classes") or []
    owned = set(
        Classroom.objects.filter(teacher=request.user).values_list("id", flat=True)
    )
    with transaction.atomic():
        assignment.class_links.all().delete()
        links = []
        for spec in specs:
            cid = spec.get("class_id")
            if cid not in owned:
                continue
            links.append(AssignmentClass(
                assignment=assignment, classroom_id=cid,
                due_at=parse_datetime(spec["due_at"]) if spec.get("due_at") else None,
                available_at=parse_datetime(spec["available_at"]) if spec.get("available_at") else None,
            ))
        AssignmentClass.objects.bulk_create(links)
    logger.info("Teacher %s assigned assignment %s to %d classes", request.user.id, assignment_id, len(links))
    return JsonResponse(_serialize_assignment(assignment))


# ---------------------------------------------------------------------------
# Teacher: analytics
# ---------------------------------------------------------------------------

_BANDS = ("new", "learning", "familiar", "proficient")


def _empty_bands():
    return {b: 0 for b in _BANDS}


def _student_due_map(assignment):
    """Map each assigned student's id -> (class_id, due_at), earliest due wins.

    A student reaches an assignment through a class they're enrolled in that the
    assignment was assigned to; if several match, the earliest-due link wins (the
    same rule as `_assignment_link_for_student`), giving one due date per student.
    """
    out = {}  # student_id -> (class_id, due_at)
    links = (
        AssignmentClass.objects.filter(assignment=assignment)
        .select_related("classroom")
        .order_by("due_at", "id")
    )
    for link in links:
        for student_id in ClassEnrollment.objects.filter(
            classroom_id=link.classroom_id
        ).values_list("student_id", flat=True):
            # First link wins because links are already ordered earliest-due.
            out.setdefault(student_id, (link.classroom_id, link.due_at))
    return out


@csrf_exempt
@require_http_methods(["GET"])
def assignment_results(request, assignment_id):
    """Familiarity report for one assignment, optionally filtered to a class.

    Reports, over the assignment's topics: each student's proficiency-band mix on
    those topics (from their SM-2 state), whether they've practiced the topics,
    and whether they're overdue (past due date without practicing). Assignments
    are now practiced through the student's normal deck, so progress is measured
    by the SM-2 schedule the practice builds — not a one-off quiz score.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    assignment, err = _get_owned_assignment(request, assignment_id)
    if err:
        return err

    topics = _assignment_topics(assignment)
    topic_ids = [t.id for t in topics]

    due_map = _student_due_map(assignment)
    class_filter = request.GET.get("class")
    if class_filter:
        try:
            cid = int(class_filter)
            due_map = {sid: v for sid, v in due_map.items() if v[0] == cid}
        except (ValueError, TypeError):
            pass
    student_ids = list(due_map.keys())

    # Bulk-fetch the SM-2 state and practice signal for every (student, topic).
    intervals = {}  # (student_id, topic_id) -> interval
    for uid, tid, interval in TopicReview.objects.filter(
        user_id__in=student_ids, topic_id__in=topic_ids
    ).values_list("user_id", "topic_id", "interval"):
        intervals[(uid, tid)] = interval
    graded = set(  # (student_id, topic_id) that has been practiced at least once
        DailyTopicGrade.objects.filter(
            user_id__in=student_ids, topic_id__in=topic_ids
        ).values_list("user_id", "topic_id")
    )

    User = get_user_model()
    names = {
        u.id: (u.get_full_name() or u.username or u.email)
        for u in User.objects.filter(id__in=student_ids)
    }

    now = timezone.now()
    students_out = []
    totals = _empty_bands()
    num_practiced = 0
    for sid in student_ids:
        class_id, due_at = due_map[sid]
        bands = _empty_bands()
        for tid in topic_ids:
            bands[_interval_band(intervals.get((sid, tid), 0))] += 1
        practiced_any = any((sid, tid) in graded for tid in topic_ids)
        if practiced_any:
            num_practiced += 1
        for b in _BANDS:
            totals[b] += bands[b]
        students_out.append({
            "student_id": sid,
            "name": names.get(sid, "(unknown)"),
            "class_id": class_id,
            "due_at": due_at.isoformat() if due_at else None,
            "practiced": practiced_any,
            "overdue": bool(due_at and due_at < now and not practiced_any),
            "proficiency": bands,
        })
    students_out.sort(key=lambda s: s["name"].lower())

    return JsonResponse({
        "assignment": _serialize_assignment(assignment),
        "topics": [{"topic_id": t.id, "topic_name": t.topic_name} for t in topics],
        "num_students": len(student_ids),
        "num_practiced": num_practiced,
        "band_totals": totals,
        "students": students_out,
    })


# ---------------------------------------------------------------------------
# Student: viewing and starting assignments
# ---------------------------------------------------------------------------

def _assignment_link_for_student(assignment, student):
    """The AssignmentClass through which `student` receives `assignment`, or None.

    A student reaches an assignment via a class they're enrolled in that the
    assignment was assigned to. If several match (rare), the earliest-due wins so
    there's a single deterministic instance per (assignment, student).
    """
    class_ids = ClassEnrollment.objects.filter(student=student).values_list("classroom_id", flat=True)
    return (
        AssignmentClass.objects.filter(assignment=assignment, classroom_id__in=class_ids)
        .order_by("due_at", "id")
        .first()
    )


@csrf_exempt
@require_http_methods(["GET"])
def my_assignments(request):
    """The current student's assignments: to-do and done.

    An assignment is "done" once the student has practiced all of its topics at
    least once; otherwise it's outstanding. Progress is tracked through the
    student's normal deck, so there's no separate assignment quiz to complete.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    class_ids = list(
        ClassEnrollment.objects.filter(student=request.user).values_list("classroom_id", flat=True)
    )
    links = (
        AssignmentClass.objects.filter(classroom_id__in=class_ids)
        .select_related("assignment", "classroom")
        .order_by("due_at", "id")
    )
    now = timezone.now()
    seen = set()
    upcoming, completed = [], []
    for link in links:
        a = link.assignment
        if a.id in seen:
            continue
        seen.add(a.id)
        topic_ids = set(a.assignment_topics.values_list("topic_id", flat=True))
        practiced = set(
            DailyTopicGrade.objects.filter(
                user=request.user, topic_id__in=topic_ids
            ).values_list("topic_id", flat=True)
        ) if topic_ids else set()
        done = bool(topic_ids) and topic_ids.issubset(practiced)
        started = bool(practiced)
        row = {
            "assignment_id": a.id,
            "title": a.title,
            "class_name": link.classroom.name,
            "due_at": link.due_at.isoformat() if link.due_at else None,
            "num_topics": len(topic_ids),
            "num_practiced": len(topic_ids & practiced),
            "status": "done" if done else ("in_progress" if started else "not_started"),
            "overdue": bool(link.due_at and link.due_at < now and not done),
        }
        (completed if done else upcoming).append(row)
    return JsonResponse({"upcoming": upcoming, "completed": completed})


@csrf_exempt
@require_http_methods(["POST"])
def play_assignment(request, assignment_id):
    """Start an assignment for the current student, then send them to practice.

    Adds the assignment's topics to the student's own selections and grows
    today's practice deck to the teacher's chosen card count, so opening an
    assignment simply routes the student to their normal practice page with the
    assigned topics in scope. Returns {"goto": "practice"} for the client to
    navigate; the actual practice happens through the deck endpoints.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    assignment = Assignment.objects.filter(id=assignment_id).first()
    if assignment is None:
        return JsonResponse({"error": "Assignment not found"}, status=404)
    link = _assignment_link_for_student(assignment, request.user)
    if link is None:
        return JsonResponse({"error": "This assignment is not assigned to you"}, status=403)

    today = _client_today(request)
    topics = _assignment_topics(assignment)
    _ensure_selected(request.user, topics)
    # Ensure today's deck exists (built from the now-selected topics), then grow
    # it — never shrink — to the teacher's card count so the student's practice
    # session covers the assigned work. Creating first matters when the student
    # opens the assignment before practicing today: `_grow_today_deck` alone is a
    # no-op with no deck yet.
    _get_or_create_today_deck(request.user, today)
    _grow_today_deck(request.user, assignment.deck_size, today)

    sa = StudentAssignment.objects.filter(assignment=assignment, student=request.user).first()
    if sa is None:
        StudentAssignment.objects.create(
            assignment=assignment, classroom=link.classroom, student=request.user,
            status=StudentAssignment.IN_PROGRESS, started_at=timezone.now(),
        )
    elif sa.status == StudentAssignment.NOT_STARTED:
        sa.status = StudentAssignment.IN_PROGRESS
        sa.started_at = sa.started_at or timezone.now()
        sa.save(update_fields=["status", "started_at"])

    logger.info("Student %s started assignment %s", request.user.id, assignment_id)
    return JsonResponse({"goto": "practice", "title": assignment.title, "deck_size": assignment.deck_size})
