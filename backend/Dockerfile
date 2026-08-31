# Python 3.13 slim — satisfies requires-python >=3.12; slim keeps the image small.
FROM python:3.13-slim

# Cleaner Python in containers: no .pyc files, unbuffered stdout so Cloud Run
# shows logs live.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for better layer caching: copy only the manifest,
# install, THEN copy code — so code edits don't re-run pip. psycopg[binary]
# ships prebuilt wheels, so no system build tools are needed.
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy the application source.
COPY . .

# Precompile all bytecode into the image so cold starts read baked .pyc instead
# of recompiling every module from source on a throttled vCPU (recompilation is
# a large slice of Cloud Run cold-start import time). Covers both our code and
# the heavy deps (sympy, mathgenerator). --invalidation-mode unchecked-hash makes
# imports trust the baked .pyc unconditionally, so COPY mtime shifts can't force
# a recompile; safe because the image is rebuilt fresh on every deploy, keeping
# .py and .pyc in lockstep. PYTHONDONTWRITEBYTECODE only blocks *writing* .pyc,
# not *reading* them, so the baked cache is still used at runtime.
#   - Our own code must compile cleanly (a failure is a real bug).
#   - Dependencies are best-effort: some packages ship files that intentionally
#     don't parse on this Python, and compileall returns non-zero on any such
#     file, so `|| true` keeps those from failing the build while still baking
#     the .pyc for everything that does compile (sympy, mathgenerator, Django).
RUN python -m compileall -q --invalidation-mode unchecked-hash /app
RUN python -m compileall -q --invalidation-mode unchecked-hash /usr/local/lib/python3.13/site-packages || true

# Gather static files (Django admin, etc.) into STATIC_ROOT for WhiteNoise.
# Needs no DB. DEBUG must be off so manifest storage behaves; DATABASE_URL is
# unset here so it falls back to SQLite, which collectstatic never touches.
RUN DEBUG=0 SECRET_KEY=build-only python manage.py collectstatic --noinput

# Cloud Run injects $PORT (usually 8080). Shell form so $PORT expands at runtime.
#
# Tuned for a 1-vCPU, I/O-bound (DB-waiting) Django app on Cloud Run:
#   --workers 1 --threads 8 --worker-class gthread
#     One process keeps memory low and the app imported exactly once. On a
#     single vCPU, extra sync worker *processes* add no CPU throughput (one core
#     runs one thread at a time) but multiply memory and import cost. Threads
#     instead give cheap concurrency for the part that actually blocks — waiting
#     on the Neon socket, during which Python releases the GIL so another thread
#     serves. Cloud Run absorbs real load by scaling out instances, not workers.
#   --preload
#     Imports the app in the master BEFORE it binds the port, so the heavy import
#     runs inside Cloud Run's startup CPU-boost window (which ends once the TCP
#     startup probe sees the port open) at full CPU, not afterwards under the
#     idle CPU throttle.
CMD gunicorn --bind :$PORT --workers 1 --threads 8 --worker-class gthread --preload --timeout 60 config.wsgi:application
