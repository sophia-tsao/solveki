import json
import logging

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import (
    Assignment, AssignmentTopic, AssignmentClass, Classroom, ClassEnrollment,
    StudentAssignment, AssignmentAttempt, Topic, UserTopicSelection,
)
from ..diagnostic_config import unit_for_topic
from .common import _require_auth, _require_teacher
from .deck import _effective_due_dates, _weighted_slot_counts, _client_today, _apply_quality
from .problems import _make_problem_for_topic

logger = logging.getLogger(__name__)

# Same outcome->quality/correctness mapping the deck uses; an assignment card is
# answered with the same two-attempt UI.
_OUTCOME_CORRECT = {"correct_first": True, "correct_second": True, "incorrect": False}
_OUTCOME_ATTEMPTS = {"correct_first": 1, "correct_second": 2, "incorrect": 2}


# ---------------------------------------------------------------------------
# Problem generation for a student's instance of an assignment
# ---------------------------------------------------------------------------

def _ensure_selected(student, topics):
    """Add `topics` to `student`'s own selections (idempotent).

    Selecting a deck assignment's teacher-picked topics adds them to the
    student's selections, so they also show up in the student's daily practice.
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


def _scoped_deck_topics(assignment, student):
    """The student's selected, usable topics filtered to a deck assignment's scope."""
    topics = Topic.objects.filter(
        selections__user=student, generator_name__isnull=False
    )
    if assignment.deck_scope == Assignment.SCOPE_TOPICS:
        # Teacher-picked topics are included regardless of the student's prior
        # selections, and are added to those selections so they carry over into
        # the student's own daily practice.
        topic_ids = list(assignment.assignment_topics.values_list("topic_id", flat=True))
        picked = list(Topic.objects.filter(id__in=topic_ids, generator_name__isnull=False))
        _ensure_selected(student, picked)
        return picked
    if assignment.deck_scope == Assignment.SCOPE_COURSE and assignment.course_id:
        topics = topics.filter(course_id=assignment.course_id)
    elif assignment.deck_scope == Assignment.SCOPE_UNIT and assignment.unit_key:
        topics = topics.select_related("course")
        matched = []
        for t in topics:
            course_name = t.course.course_name if t.course else ""
            unit = unit_for_topic(course_name, t.topic_name)
            if unit and unit["key"] == assignment.unit_key:
                matched.append(t)
        return matched
    return list(topics)


def _emit_weighted(user, topics, count, today):
    """Generate up to `count` problems across `topics`, weighted by SM-2 due priority.

    Reuses the deck's due-weighting (`_effective_due_dates`/`_weighted_slot_counts`)
    so a deck-kind assignment mirrors normal practice: overdue topics get more of
    the questions. Returns a list of {problem, solution, topic_id}.
    """
    if count <= 0 or not topics:
        return []
    due = _effective_due_dates(user, topics, today)
    ordered = sorted(topics, key=lambda t: (due[t.id], t.id))
    counts = _weighted_slot_counts(ordered, due, count, today)
    sequence = []
    left = dict(counts)
    while len(sequence) < sum(counts.values()):
        for topic in ordered:
            if left.get(topic.id, 0) > 0:
                sequence.append(topic)
                left[topic.id] -= 1
    return _generate_for_sequence(sequence)


def _generate_for_sequence(sequence):
    """Generate one problem per topic in `sequence`, skipping broken generators."""
    problems = []
    broken = set()
    for topic in sequence:
        if topic.id in broken:
            continue
        made = _make_problem_for_topic(topic)
        if made is None:
            broken.add(topic.id)
            continue
        problems.append(made)
    return problems


def _generate_problems_for_student(assignment, student, today):
    """Build the concrete problem list for one student's instance of an assignment."""
    if assignment.is_deck:
        topics = _scoped_deck_topics(assignment, student)
        return _emit_weighted(student, topics, assignment.deck_size, today)
    # Topics kind: a fixed number of freshly generated problems per chosen topic.
    sequence = []
    for at in assignment.assignment_topics.select_related("topic").order_by("id"):
        sequence.extend([at.topic] * max(0, at.num_questions))
    return _generate_for_sequence(sequence)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _serialize_assignment(assignment, include_topics=True):
    data = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "mode": assignment.mode,
        "deck_scope": assignment.deck_scope,
        "course_id": assignment.course_id,
        "unit_key": assignment.unit_key,
        "deck_size": assignment.deck_size,
        "created_at": assignment.created_at.isoformat(),
    }
    if include_topics:
        data["topics"] = [
            {
                "topic_id": at.topic_id,
                "topic_name": at.topic.topic_name,
                "course_id": at.topic.course_id,
                "num_questions": at.num_questions,
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


def _accuracy(correct, total):
    return round(correct / total, 4) if total else None


# ---------------------------------------------------------------------------
# Teacher: assignment authoring
# ---------------------------------------------------------------------------

def _apply_assignment_body(assignment, body):
    """Set assignment fields from a create/update body. Returns None or an error response."""
    if "title" in body:
        title = (body.get("title") or "").strip()
        if not title:
            return JsonResponse({"error": "title is required"}, status=400)
        assignment.title = title
    if "description" in body:
        assignment.description = body.get("description") or ""
    if "mode" in body:
        if body["mode"] not in dict(Assignment.MODE_CHOICES):
            return JsonResponse({"error": "invalid mode"}, status=400)
        assignment.mode = body["mode"]
    if assignment.is_deck:
        assignment.deck_scope = body.get("deck_scope", assignment.deck_scope or Assignment.SCOPE_ALL)
        assignment.course_id = body.get("course_id", assignment.course_id)
        assignment.unit_key = body.get("unit_key", assignment.unit_key)
        if "deck_size" in body:
            try:
                assignment.deck_size = max(1, int(body["deck_size"]))
            except (ValueError, TypeError):
                return JsonResponse({"error": "deck_size must be an integer"}, status=400)
    return None


def _set_assignment_topics(assignment, topics_spec):
    """Replace an assignment's topic list from [{topic_id, num_questions}, ...]."""
    assignment.assignment_topics.all().delete()
    rows = []
    for spec in topics_spec or []:
        topic_id = spec.get("topic_id")
        try:
            num = max(1, int(spec.get("num_questions", 1)))
        except (ValueError, TypeError):
            num = 1
        if topic_id is None:
            continue
        if not Topic.objects.filter(id=topic_id).exists():
            continue
        rows.append(AssignmentTopic(assignment=assignment, topic_id=topic_id, num_questions=num))
    AssignmentTopic.objects.bulk_create(rows)


def _uses_topic_list(assignment):
    """Whether the assignment stores an explicit topic list (`AssignmentTopic`).

    True for the topics kind, and for a deck scoped to teacher-picked topics —
    both drive their topic set from the same `AssignmentTopic` rows.
    """
    return assignment.is_topics or (
        assignment.is_deck
        and assignment.deck_scope == Assignment.SCOPE_TOPICS
    )


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
            if _uses_topic_list(assignment):
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
            if _uses_topic_list(assignment) and "topics" in body:
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


@csrf_exempt
@require_http_methods(["GET"])
def assignment_preview(request, assignment_id):
    """A sample generation of the assignment's problems (teacher preview).

    For a topics-kind assignment this is a real generation of the spec. For a
    deck-kind assignment there's no fixed problem set (it draws from each
    student's own selected topics), so we describe the scope instead.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    assignment, err = _get_owned_assignment(request, assignment_id)
    if err:
        return err
    if assignment.is_deck:
        return JsonResponse({
            "kind": "deck",
            "deck_scope": assignment.deck_scope,
            "deck_size": assignment.deck_size,
            "note": "Deck assignments draw from each student's own selected topics; no fixed preview.",
        })
    problems = _generate_problems_for_student(assignment, request.user, _client_today(request))
    # Show the problem text only (hide solutions in the preview list is optional;
    # the teacher owns the assignment, so we include them for review).
    return JsonResponse({"kind": "topics", "problems": problems})


# ---------------------------------------------------------------------------
# Teacher: analytics
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["GET"])
def assignment_results(request, assignment_id):
    """Analytics for one assignment, optionally filtered to a single class.

    Reports: average accuracy across the assigned students, per-topic accuracy
    (worst first — "most struggled with"), and each student's accuracy plus when
    they began and how long they took.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    assignment, err = _get_owned_assignment(request, assignment_id)
    if err:
        return err
    class_id = request.GET.get("class")
    sa_qs = StudentAssignment.objects.filter(assignment=assignment).select_related("student", "classroom")
    if class_id:
        sa_qs = sa_qs.filter(classroom_id=class_id)

    students = []
    overall_correct = overall_total = 0
    # Per-topic tallies for the "most struggled with" list.
    topic_tally = {}  # topic_id -> [correct, total, name]
    for sa in sa_qs:
        attempts = list(sa.attempts.select_related("topic"))
        correct = sum(1 for a in attempts if a.is_correct)
        total = len(attempts)
        overall_correct += correct
        overall_total += total
        for a in attempts:
            key = a.topic_id
            name = a.topic.topic_name if a.topic else "(deleted topic)"
            tally = topic_tally.setdefault(key, [0, 0, name])
            tally[0] += 1 if a.is_correct else 0
            tally[1] += 1
        time_taken = None
        if sa.started_at and sa.completed_at:
            time_taken = int((sa.completed_at - sa.started_at).total_seconds())
        u = sa.student
        students.append({
            "student_id": u.id,
            "name": (u.get_full_name() or u.username or u.email),
            "class_id": sa.classroom_id,
            "status": sa.status,
            "accuracy": _accuracy(correct, total),
            "answered": total,
            "started_at": sa.started_at.isoformat() if sa.started_at else None,
            "completed_at": sa.completed_at.isoformat() if sa.completed_at else None,
            "time_taken_seconds": time_taken,
        })

    topics = sorted(
        (
            {"topic_id": tid, "topic_name": t[2], "accuracy": _accuracy(t[0], t[1]), "answered": t[1]}
            for tid, t in topic_tally.items()
        ),
        key=lambda d: (d["accuracy"] if d["accuracy"] is not None else 1),
    )
    return JsonResponse({
        "assignment": _serialize_assignment(assignment),
        "average_accuracy": _accuracy(overall_correct, overall_total),
        "num_submissions": len(students),
        "topics_struggled": topics,
        "students": students,
    })


# ---------------------------------------------------------------------------
# Student: viewing and taking assignments
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
    """The current student's assignments: upcoming (not completed) and completed."""
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
    existing = {
        sa.assignment_id: sa
        for sa in StudentAssignment.objects.filter(student=request.user)
    }
    seen = set()
    upcoming, completed = [], []
    for link in links:
        a = link.assignment
        if a.id in seen:
            continue
        seen.add(a.id)
        sa = existing.get(a.id)
        accuracy = None
        if sa and sa.status == StudentAssignment.COMPLETED:
            total = sa.attempts.count()
            correct = sa.attempts.filter(is_correct=True).count()
            accuracy = _accuracy(correct, total)
        row = {
            "assignment_id": a.id,
            "title": a.title,
            "mode": a.mode,
            "class_name": link.classroom.name,
            "due_at": link.due_at.isoformat() if link.due_at else None,
            "status": sa.status if sa else StudentAssignment.NOT_STARTED,
            "accuracy": accuracy,
        }
        if sa and sa.status == StudentAssignment.COMPLETED:
            completed.append(row)
        else:
            upcoming.append(row)
    return JsonResponse({"upcoming": upcoming, "completed": completed})


def _student_assignment_payload(sa):
    """Current-card payload for a student taking an assignment (mirrors the deck)."""
    total = len(sa.problems)
    if sa.current_index >= total:
        return {"completed": True, "total": total}
    current = sa.problems[sa.current_index]
    topic_id = current.get("topic_id")
    topic_name = Topic.objects.filter(id=topic_id).values_list("topic_name", flat=True).first() if topic_id else None
    return {
        "completed": False,
        "problem": current["problem"],
        "solution": current["solution"],
        "topic_name": topic_name,
        "current_number": sa.current_index + 1,
        "total": total,
    }


@csrf_exempt
@require_http_methods(["GET"])
def play_assignment(request, assignment_id):
    """Start or resume the current student's instance of an assignment.

    Creates the StudentAssignment (generating this student's problems) on first
    open, marks it in-progress, and returns the current card.
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

    sa = StudentAssignment.objects.filter(assignment=assignment, student=request.user).first()
    # (Re)generate when there's no instance yet, or when a prior open produced an
    # empty problem list (e.g. a deck assignment opened before the student had any
    # selected topics in scope). Regenerating lets a stuck empty instance recover
    # once the student has selected topics, instead of being frozen as "completed".
    needs_problems = sa is None or (
        not sa.problems and sa.status != StudentAssignment.COMPLETED
    )
    if needs_problems:
        problems = _generate_problems_for_student(assignment, request.user, _client_today(request))
        if not problems:
            # Nothing could be generated. Don't persist a zero-problem instance
            # (which would read as instantly "completed"); tell the client so it
            # can explain rather than congratulate.
            logger.info(
                "Student %s opened assignment %s but no problems could be generated",
                request.user.id, assignment_id,
            )
            return JsonResponse({
                "empty": True,
                "title": assignment.title,
                "reason": "no_topics_in_scope" if assignment.is_deck else "no_problems",
            })
        if sa is None:
            sa = StudentAssignment.objects.create(
                assignment=assignment, classroom=link.classroom, student=request.user,
                problems=problems, status=StudentAssignment.IN_PROGRESS,
                started_at=timezone.now(),
            )
            logger.info("Student %s started assignment %s (%d problems)", request.user.id, assignment_id, len(problems))
        else:
            sa.problems = problems
            sa.status = StudentAssignment.IN_PROGRESS
            sa.started_at = sa.started_at or timezone.now()
            sa.save(update_fields=["problems", "status", "started_at"])
    elif sa.status == StudentAssignment.NOT_STARTED:
        sa.status = StudentAssignment.IN_PROGRESS
        sa.started_at = sa.started_at or timezone.now()
        sa.save(update_fields=["status", "started_at"])

    payload = _student_assignment_payload(sa)
    payload["title"] = assignment.title
    return JsonResponse(payload)


@csrf_exempt
@require_http_methods(["POST"])
def advance_assignment(request, assignment_id):
    """Record the current card's outcome and step forward; finish on the last card.

    Body: {"outcome": "...", "from_number": N}. On completion, if the assignment
    has SM-2 enabled, applies one accuracy-derived SM-2 grade per topic.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    assignment = Assignment.objects.filter(id=assignment_id).first()
    if assignment is None:
        return JsonResponse({"error": "Assignment not found"}, status=404)
    sa = StudentAssignment.objects.filter(assignment=assignment, student=request.user).first()
    if sa is None:
        return JsonResponse({"error": "Assignment not started"}, status=400)

    try:
        body = json.loads(request.body) if request.body else {}
    except (ValueError, TypeError):
        body = {}
    outcome = body.get("outcome")
    from_number = body.get("from_number")

    total = len(sa.problems)
    position_ok = from_number is None or from_number == sa.current_index + 1
    if sa.current_index < total and position_ok:
        card = sa.problems[sa.current_index]
        if outcome in _OUTCOME_CORRECT:
            AssignmentAttempt.objects.update_or_create(
                student_assignment=sa, problem_index=sa.current_index,
                defaults={
                    "topic_id": card.get("topic_id"),
                    "is_correct": _OUTCOME_CORRECT[outcome],
                    "attempts": _OUTCOME_ATTEMPTS[outcome],
                    "outcome": outcome,
                },
            )
        sa.current_index += 1
        if sa.current_index >= total:
            sa.status = StudentAssignment.COMPLETED
            sa.completed_at = timezone.now()
            sa.save(update_fields=["current_index", "status", "completed_at"])
            if assignment.sm2_enabled:
                _apply_sm2_from_accuracy(sa, _client_today(request))
        else:
            sa.save(update_fields=["current_index"])

    return JsonResponse(_student_assignment_payload(sa))


def _apply_sm2_from_accuracy(sa, today):
    """On completion, apply one SM-2 grade per topic from the student's accuracy.

    Only called for SM-2-enabled assignments. Per topic, accuracy = correct/total
    across that topic's attempts in this assignment; it maps to an SM-2 quality
    which is applied once via the deck's shared scheduling path (`_apply_quality`),
    so it obeys the same once-per-day rule as normal practice.
    """
    tally = {}  # topic_id -> [correct, total]
    for a in sa.attempts.all():
        if a.topic_id is None:
            continue
        t = tally.setdefault(a.topic_id, [0, 0])
        t[0] += 1 if a.is_correct else 0
        t[1] += 1
    for topic_id, (correct, total) in tally.items():
        if total == 0:
            continue
        quality = _accuracy_to_quality(correct / total)
        _apply_quality(sa.student, topic_id, quality, today)
    logger.info("Applied SM-2 grades from accuracy for student assignment %s", sa.id)


def _accuracy_to_quality(acc):
    """Map an accuracy fraction (0..1) to an SM-2 quality grade (1..5)."""
    if acc >= 0.9:
        return 5
    if acc >= 0.75:
        return 4
    if acc >= 0.6:
        return 3
    if acc >= 0.4:
        return 2
    return 1
