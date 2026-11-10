import json
import logging
import secrets

from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import Assignment, AssignmentClass, AssignmentTopic, Classroom, ClassEnrollment, Course, Topic
from .common import _require_auth, _require_teacher
from .assignments import _start_assignment_for, overdue_by_student
from .deck import _client_today
from .insights import activity_by_student, band_counts_by_student, band_matrix

logger = logging.getLogger(__name__)

# Join codes are short, human-typeable, and drawn from an unambiguous alphabet
# (no O/0/I/1) so a student reading one off a board doesn't mis-type it.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 6


def _generate_join_code():
    """A unique join code for a new classroom (retries on the rare collision)."""
    for _ in range(10):
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        if not Classroom.objects.filter(join_code=code).exists():
            return code
    # Extremely unlikely; widen the space rather than fail.
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH + 2))


def _get_owned_class(request, class_id):
    """Return (classroom, None) if the teacher owns it, else (None, error_response).

    The ownership guard for every teacher class endpoint: a teacher may only act
    on classes they created.
    """
    classroom = Classroom.objects.filter(id=class_id).first()
    if classroom is None:
        return None, JsonResponse({"error": "Class not found"}, status=404)
    if classroom.teacher_id != request.user.id:
        return None, JsonResponse({"error": "Not your class"}, status=403)
    return classroom, None


def _serialize_class(classroom, student_count=None):
    if student_count is None:
        student_count = classroom.enrollments.count()
    return {
        "id": classroom.id,
        "name": classroom.name,
        "join_code": classroom.join_code,
        "course_id": classroom.course_id,
        "archived": classroom.archived,
        "student_count": student_count,
        "created_at": classroom.created_at.isoformat(),
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def classes(request):
    """List the teacher's classes, or create one."""
    guard = _require_teacher(request)
    if guard:
        return guard
    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid request body"}, status=400)
        name = (body.get("name") or "").strip()
        if not name:
            return JsonResponse({"error": "name is required"}, status=400)
        course = None
        course_id = body.get("course_id")
        if course_id is not None:
            course = Course.objects.filter(id=course_id).first()
        classroom = Classroom.objects.create(
            teacher=request.user, name=name, course=course,
            join_code=_generate_join_code(),
        )
        logger.info("Teacher %s created class %s", request.user.id, classroom.id)
        return JsonResponse(_serialize_class(classroom, student_count=0), status=201)

    qs = (
        Classroom.objects.filter(teacher=request.user, archived=False)
        .annotate(n=Count("enrollments"))
        .order_by("-created_at")
    )
    return JsonResponse({"classes": [_serialize_class(c, c.n) for c in qs]})


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def class_detail(request, class_id):
    """Read, update (name/course/archived), or delete one class the teacher owns."""
    guard = _require_teacher(request)
    if guard:
        return guard
    classroom, err = _get_owned_class(request, class_id)
    if err:
        return err
    if request.method == "DELETE":
        classroom.delete()
        logger.info("Teacher %s deleted class %s", request.user.id, class_id)
        return JsonResponse({"ok": True})
    if request.method == "PATCH":
        try:
            body = json.loads(request.body)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid request body"}, status=400)
        if "name" in body:
            name = (body.get("name") or "").strip()
            if not name:
                return JsonResponse({"error": "name cannot be empty"}, status=400)
            classroom.name = name
        if "course_id" in body:
            classroom.course = Course.objects.filter(id=body["course_id"]).first()
        if "archived" in body:
            classroom.archived = bool(body["archived"])
        classroom.save()
    return JsonResponse(_serialize_class(classroom))


@csrf_exempt
@require_http_methods(["GET"])
def class_students(request, class_id):
    """Roster for one class the teacher owns, with each student's band mix and week.

    `proficiency` counts the student's selected topics per proficiency band, the
    same mix their own dashboard donut shows. `cards_7d` / `accuracy_7d` cover
    today (the client's `?today=`) and the six days before, `last_active` is
    the last day they practiced, and `overdue_count` how many of this class's
    assignments they're past due on.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    classroom, err = _get_owned_class(request, class_id)
    if err:
        return err
    enrollments = list(classroom.enrollments.select_related("student").order_by("joined_at"))
    ids = [e.student_id for e in enrollments]
    bands = band_counts_by_student(ids)
    activity = activity_by_student(ids, _client_today(request))
    class_assignments = list(Assignment.objects.filter(class_links__classroom=classroom).distinct())
    overdue = overdue_by_student(class_assignments, timezone.now(), class_id=classroom.id)
    students = []
    for e in enrollments:
        u = e.student
        act = activity[u.id]
        students.append({
            "id": u.id,
            "name": (u.get_full_name() or u.username or u.email),
            "email": u.email,
            "joined_at": e.joined_at.isoformat(),
            "proficiency": bands[u.id],
            "cards_7d": act["cards"],
            "accuracy_7d": act["accuracy"],
            "last_active": act["last_active"].isoformat() if act["last_active"] else None,
            "overdue_count": len(overdue.get(u.id, [])),
        })
    return JsonResponse({"students": students})


def _progress_topics(request, classroom):
    """The topics a class progress grid covers, plus the assignments to pick from.

    `?assignment=<id>` picks one of this class's assignments; by default it's
    the most recently assigned one still open (no due date, or due later),
    else the most recently assigned. Returns (topics, assignment id or None,
    the class's assignments as [{id, title}], newest first).
    """
    links = list(
        AssignmentClass.objects.filter(classroom=classroom)
        .select_related("assignment").order_by("-assigned_at", "-id")
    )
    now = timezone.now()
    choices, seen, first_open = [], set(), None
    for link in links:
        if link.assignment_id not in seen:
            seen.add(link.assignment_id)
            choices.append({"id": link.assignment_id, "title": link.assignment.title})
            if first_open is None and (link.due_at is None or link.due_at >= now):
                first_open = link.assignment_id
    picked = None
    if request.GET.get("assignment"):
        try:
            wanted = int(request.GET["assignment"])
        except (TypeError, ValueError):
            wanted = None
        picked = wanted if wanted in seen else None
    elif choices:
        picked = first_open or choices[0]["id"]
    if picked is None:
        return [], None, choices
    topic_ids = list(
        AssignmentTopic.objects.filter(assignment_id=picked).order_by("id").values_list("topic_id", flat=True)
    )
    by_id = {t.id: t for t in Topic.objects.filter(id__in=topic_ids, generator_name__isnull=False)}
    return [by_id[tid] for tid in topic_ids if tid in by_id], picked, choices


@csrf_exempt
@require_http_methods(["GET"])
def class_progress(request, class_id):
    """The class progress grid: every student's band on each of an assignment's topics.

    Rows are the class roster (alphabetical), columns the topics of the picked
    assignment (see `_progress_topics`). A cell is {"band", "missed_recent"}
    once the student has answered the topic (see `insights.band_matrix`), or
    null when they haven't started it. `topic_summary` gives, per topic, the
    share of the class at Familiar or above.
    """
    guard = _require_teacher(request)
    if guard:
        return guard
    classroom, err = _get_owned_class(request, class_id)
    if err:
        return err
    today = _client_today(request)
    topics, picked, choices = _progress_topics(request, classroom)
    enrollments = list(classroom.enrollments.select_related("student"))
    ids = [e.student_id for e in enrollments]
    cells = band_matrix(ids, [t.id for t in topics], today)
    activity = activity_by_student(ids, today)
    students = []
    for e in enrollments:
        u = e.student
        last = activity[u.id]["last_active"]
        students.append({
            "id": u.id,
            "name": (u.get_full_name() or u.username or u.email),
            "last_active": last.isoformat() if last else None,
            "cells": {str(t.id): cells.get((u.id, t.id)) for t in topics},
        })
    students.sort(key=lambda r: r["name"].lower())
    summary = {}
    for t in topics:
        strong = sum(
            1 for sid in ids if (cells.get((sid, t.id)) or {}).get("band") in ("familiar", "proficient")
        )
        summary[str(t.id)] = round(strong / len(ids) * 100) if ids else None
    return JsonResponse({
        "assignment_id": picked,
        "assignments": choices,
        "topics": [{"topic_id": t.id, "topic_name": t.topic_name} for t in topics],
        "students": students,
        "topic_summary": summary,
    })


@csrf_exempt
@require_http_methods(["DELETE"])
def remove_student(request, class_id, student_id):
    """Remove a student from a class the teacher owns."""
    guard = _require_teacher(request)
    if guard:
        return guard
    classroom, err = _get_owned_class(request, class_id)
    if err:
        return err
    ClassEnrollment.objects.filter(classroom=classroom, student_id=student_id).delete()
    logger.info("Teacher %s removed student %s from class %s", request.user.id, student_id, class_id)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["POST"])
def join_class(request):
    """Student joins a class by its join code."""
    auth = _require_auth(request)
    if auth:
        return auth
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)
    code = (body.get("code") or "").strip().upper()
    if not code:
        return JsonResponse({"error": "code is required"}, status=400)
    classroom = Classroom.objects.filter(join_code=code, archived=False).first()
    if classroom is None:
        return JsonResponse({"error": "No class found for that code"}, status=404)
    ClassEnrollment.objects.get_or_create(classroom=classroom, student=request.user)
    # Assignments already given to this class reach the new student right away.
    for link in AssignmentClass.objects.filter(classroom=classroom).select_related("assignment"):
        _start_assignment_for(link.assignment, classroom.id, [request.user.id])
    logger.info("Student %s joined class %s", request.user.id, classroom.id)
    return JsonResponse({
        "id": classroom.id,
        "name": classroom.name,
        "teacher": (classroom.teacher.get_full_name() or classroom.teacher.username),
    })


@csrf_exempt
@require_http_methods(["GET"])
def my_classes(request):
    """Classes the current student is enrolled in."""
    auth = _require_auth(request)
    if auth:
        return auth
    classes_out = []
    for e in (
        ClassEnrollment.objects.filter(student=request.user)
        .select_related("classroom", "classroom__teacher")
        .order_by("-joined_at")
    ):
        c = e.classroom
        classes_out.append({
            "id": c.id,
            "name": c.name,
            "teacher": (c.teacher.get_full_name() or c.teacher.username),
        })
    return JsonResponse({"classes": classes_out})
