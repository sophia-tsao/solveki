"""Custom middleware for the solveki backend."""

import logging
import time

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
