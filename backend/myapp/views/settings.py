import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import Settings
from .common import _require_auth
from .deck import _grow_today_deck, _client_today

logger = logging.getLogger(__name__)


def _serialize_settings(settings):
    return {
        "language": settings.language,
        "questions_per_day": settings.questions_per_day,
        "role": settings.role,
        "role_chosen": settings.role_chosen,
    }


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def settings_view(request):
    auth = _require_auth(request)
    if auth:
        return auth
    settings = Settings.load(request.user)
    if request.method == "PATCH":
        body = json.loads(request.body)
        if "language" in body:
            settings.language = body["language"]
        if "questions_per_day" in body:
            try:
                count = int(body["questions_per_day"])
            except (ValueError, TypeError):
                return JsonResponse({"error": "questions_per_day must be an integer"}, status=400)
            if count < 1:
                return JsonResponse({"error": "questions_per_day must be at least 1"}, status=400)
            settings.questions_per_day = count
        settings.save()
        logger.info(
            "User %s updated settings (language=%s, questions_per_day=%d)",
            request.user.id, settings.language, settings.questions_per_day,
        )
        # Apply a larger card count to today's deck immediately so the change
        # takes effect on save, not just tomorrow. We only ever grow the deck:
        # problems the student has already worked through stay put, and a
        # smaller count leaves today's deck untouched (it applies next day).
        _grow_today_deck(request.user, settings.questions_per_day, _client_today(request))
    return JsonResponse(_serialize_settings(settings))


@csrf_exempt
@require_http_methods(["POST"])
def set_role(request):
    """Set the user's role once, at signup.

    The frontend shows a student/teacher picker only to brand-new users, but the
    endpoint is the real guard: it refuses to change a role that's already been
    chosen (`role_chosen`), so a student can't later promote themselves to
    teacher and read other students' data. Changing a role afterwards is an
    admin action.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    try:
        body = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)
    role = body.get("role")
    if role not in (Settings.STUDENT, Settings.TEACHER):
        return JsonResponse({"error": "role must be 'student' or 'teacher'"}, status=400)
    settings = Settings.load(request.user)
    if settings.role_chosen:
        return JsonResponse({"error": "Role has already been set"}, status=403)
    settings.role = role
    settings.role_chosen = True
    settings.save(update_fields=["role", "role_chosen"])

    # Students supply their own first/last name at signup (teachers only ever see
    # a student by name, so this is the name teachers will see). Django's
    # first_name/last_name are capped at 150 chars.
    first = body.get("first_name")
    last = body.get("last_name")
    if first is not None or last is not None:
        if first is not None:
            request.user.first_name = str(first).strip()[:150]
        if last is not None:
            request.user.last_name = str(last).strip()[:150]
        request.user.save(update_fields=["first_name", "last_name"])

    logger.info("User %s chose role %s", request.user.id, role)
    data = _serialize_settings(settings)
    data["name"] = (request.user.get_full_name() or request.user.username or request.user.email)
    return JsonResponse(data)
