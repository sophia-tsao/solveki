from django.http import JsonResponse

from ..models import Settings


def _require_auth(request):
    """Return a 401 JsonResponse if not authenticated, else None."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    return None


def _require_teacher(request):
    """Return a 401/403 JsonResponse unless the user is an authenticated teacher.

    Teacher-only endpoints (classes, assignment authoring, analytics) call this
    at the top the same way every view calls `_require_auth`. Returns the auth
    error first (401) so an anonymous request isn't told the resource requires a
    teacher, then 403 for a logged-in non-teacher.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    if Settings.load(request.user).role != Settings.TEACHER:
        return JsonResponse({"error": "Teacher access required"}, status=403)
    return None
