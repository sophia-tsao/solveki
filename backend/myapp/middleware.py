"""Custom middleware for the solveki backend."""

import logging
import time

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger('myapp.request')


class RequestLoggingMiddleware:
    """Log one line per request: method, path, status, and server-side latency.

    Cloud Run already records an httpRequest entry per request, but this logs
    the time spent *inside* Django (excludes cold-start container/import time),
    which is what you compare against the ``myapp.startup`` cold-start line to
    see whether a slow request was cold start or real work. Logged at INFO on
    the ``myapp.request`` logger, so it appears wherever ``myapp`` logs go.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            '%s %s -> %s in %.1fms',
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )
        return response


class OriginCheckMiddleware:
    """Reject state-changing requests sent from a site we don't trust (CSRF).

    The SPA (Vercel) and API (Cloud Run) are on different sites, so the session
    cookie is SameSite=None and the API views are ``csrf_exempt`` (the SPA can't
    read a CSRF cookie set on the API's domain). Without another check, any
    website could make a logged-in user's browser POST to the API. Browsers
    always attach an ``Origin`` header to cross-site POST/PUT/PATCH/DELETE and
    pages can't forge it, so we only allow unsafe requests whose Origin is the
    API itself, an allowed frontend (``CORS_ALLOWED_ORIGINS``), or a
    ``CSRF_TRUSTED_ORIGINS`` entry.

    Requests with no Origin at all (curl, Bruno, Django's test client) are let
    through: they don't come from a browser, so they can't carry a victim's
    cookies.
    """

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS', 'TRACE')

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed = {
            o.rstrip('/')
            for o in [*settings.CORS_ALLOWED_ORIGINS, *settings.CSRF_TRUSTED_ORIGINS]
        }

    def __call__(self, request):
        origin = request.headers.get('Origin')
        if (
            request.method not in self.SAFE_METHODS
            and origin is not None
            and origin.rstrip('/') not in self.allowed
            and origin != f'{request.scheme}://{request.get_host()}'
        ):
            logger.warning(
                'Blocked %s %s from untrusted origin %s',
                request.method, request.path, origin,
            )
            return JsonResponse({'error': 'Untrusted origin'}, status=403)
        return self.get_response(request)
