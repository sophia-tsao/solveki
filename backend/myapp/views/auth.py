import json
import logging

from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings as django_settings
from django.contrib.auth import login, logout, get_user_model

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from google.auth.exceptions import GoogleAuthError

from ..models import Settings

logger = logging.getLogger(__name__)

# Google signs tokens against its own clock. A small drift on the server clock
# is enough to make verify_oauth2_token reject every token with "Token used too
# early/late". Allow a modest tolerance so ordinary clock skew doesn't lock all
# users out.
GOOGLE_CLOCK_SKEW_SECONDS = 10


def _serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "name": (user.get_full_name() or user.username or user.email),
    }


@csrf_exempt
@require_http_methods(["GET"])
def me(request):
    """Return the current user, or authenticated=False if not logged in."""
    if request.user.is_authenticated:
        return JsonResponse({"authenticated": True, "user": _serialize_user(request.user)})
    return JsonResponse({"authenticated": False})


@csrf_exempt
@require_http_methods(["POST"])
def google_login(request):
    """Verify a Google ID token and log the user in, creating them if needed."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request body"}, status=400)

    token = body.get("credential")
    if not token:
        return JsonResponse({"error": "Missing credential"}, status=400)

    client_id = getattr(django_settings, "GOOGLE_OAUTH_CLIENT_ID", None)
    if not client_id:
        return JsonResponse({"error": "Google login is not configured on the server"}, status=500)

    try:
        idinfo = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=GOOGLE_CLOCK_SKEW_SECONDS,
        )
    except ValueError as exc:
        # Surface the underlying reason (bad audience, expiry, clock skew, ...)
        # to the logs; the client only gets a generic message.
        logger.warning("Google token verification failed: %s", exc)
        return JsonResponse({"error": "Invalid Google token"}, status=401)
    except GoogleAuthError as exc:
        # verify_oauth2_token first fetches Google's signing certs over HTTPS.
        # A transport/SSL failure there raises GoogleAuthError (not ValueError),
        # which is a server-side problem, not a bad token. Return JSON 502 so the
        # client shows a real message instead of choking on an HTML 500 page.
        logger.error("Could not verify Google token (transport error): %s", exc)
        return JsonResponse(
            {"error": "Could not reach Google to verify sign-in. Please try again."},
            status=502,
        )

    email = idinfo.get("email")
    if not email or not idinfo.get("email_verified", False):
        logger.warning("Rejected Google login: email missing or unverified")
        return JsonResponse({"error": "Google account email is not verified"}, status=401)

    User = get_user_model()
    # Use the Google subject as the stable username; fall back to email.
    google_sub = idinfo.get("sub")
    user, created = User.objects.get_or_create(
        username=google_sub or email,
        defaults={
            "email": email,
            "first_name": idinfo.get("given_name", ""),
            "last_name": idinfo.get("family_name", ""),
        },
    )
    # Keep email/name fresh on returning users.
    if not created and user.email != email:
        user.email = email
        user.save(update_fields=["email"])

    login(request, user)
    logger.info(
        "Google login succeeded for user %s (%s account)",
        user.id, "new" if created else "existing",
    )
    return JsonResponse({"authenticated": True, "user": _serialize_user(user)})


@csrf_exempt
@require_http_methods(["POST"])
def test_login(request):
    """Log in a fixed test user with a clean slate, for the E2E suite.

    Guarded by ENABLE_TEST_LOGIN: when the flag is off (the default, and always
    in production) this returns 404 so the route is invisible. The end-to-end
    run sets ENABLE_TEST_LOGIN=1 so Playwright can obtain a real session cookie.

    Each call resets the test user's practice state — topic selections, daily
    decks, and settings — so a test can call it (e.g. in beforeEach) to start
    from a known-clean state regardless of what earlier tests did. The single
    shared user means tests can't rely on the database for isolation otherwise.
    """
    if not getattr(django_settings, "ENABLE_TEST_LOGIN", False):
        raise Http404()
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="e2e-user",
        defaults={
            "email": "e2e@example.com",
            "first_name": "E2E",
            "last_name": "User",
        },
    )
    # Reset to a clean slate: no selected topics, no deck, default settings.
    user.topic_selections.all().delete()
    user.decks.all().delete()
    Settings.objects.filter(user=user).delete()
    login(request, user)
    logger.info("Test login for user %s (ENABLE_TEST_LOGIN is on)", user.id)
    return JsonResponse({"authenticated": True, "user": _serialize_user(user)})


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    user_id = request.user.id if request.user.is_authenticated else None
    logout(request)
    logger.info("User %s logged out", user_id)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_account(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)
    user = request.user
    user_id = user.id
    logout(request)
    user.delete()  # Cascades to selections, settings, and decks.
    logger.info("Deleted account for user %s and all associated data", user_id)
    return JsonResponse({"ok": True})
