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

# Gather static files (Django admin, etc.) into STATIC_ROOT for WhiteNoise.
# Needs no DB. DEBUG must be off so manifest storage behaves; DATABASE_URL is
# unset here so it falls back to SQLite, which collectstatic never touches.
RUN DEBUG=0 SECRET_KEY=build-only python manage.py collectstatic --noinput

# Cloud Run injects $PORT (usually 8080). Shell form so $PORT expands at runtime.
CMD gunicorn --bind :$PORT --workers 3 --timeout 60 config.wsgi:application
