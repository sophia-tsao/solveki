"""
WSGI config for the solveki backend (config project).

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import logging
import os
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# --- Cold-start instrumentation -------------------------------------------
# Each gunicorn worker imports this module once. On Cloud Run (scale-to-zero,
# 1 throttled vCPU) that import is the dominant slice of the first request's
# latency, so we time each stage and log a single line the Cloud Run logs will
# show (myapp logger -> console at INFO in production). Costs nothing on the
# warm path; only runs once per worker at startup.
_t_start = time.perf_counter()

from django.core.wsgi import get_wsgi_application

_t_import = time.perf_counter()

# Loads settings and populates the app registry (equivalent to django.setup()).
application = get_wsgi_application()
_t_setup = time.perf_counter()

# The root URLconf (and therefore every view + problem generator) otherwise
# imports lazily on the first request, inflating its latency. Force it now so
# the cost is paid at worker startup and shows up as its own measured stage.
from django.urls import get_resolver

get_resolver().url_patterns
_t_urls = time.perf_counter()

logging.getLogger('myapp.startup').info(
    'cold start (pid %d): import django=%.3fs, get_wsgi_application=%.3fs, '
    'URLconf+views/generators import=%.3fs, total wsgi load=%.3fs',
    os.getpid(),
    _t_import - _t_start,
    _t_setup - _t_import,
    _t_urls - _t_setup,
    _t_urls - _t_start,
)
