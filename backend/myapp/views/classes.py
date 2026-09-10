import json
import logging
import secrets

from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import Classroom, ClassEnrollment, Course
from .common import _require_auth, _require_teacher

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
    """Roster for one class the teacher owns."""
    guard = _require_teacher(request)
    if guard:
        return guard
    classroom, err = _get_owned_class(request, class_id)
    if err:
        return err
    students = []
    for e in classroom.enrollments.select_related("student").order_by("joined_at"):
        u = e.student
        students.append({
            "id": u.id,
            "name": (u.get_full_name() or u.username or u.email),
            "email": u.email,
            "joined_at": e.joined_at.isoformat(),
        })
    return JsonResponse({"students": students})


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
