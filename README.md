# Solveki

Solveki is a math practice web app. It serves an endless deck of auto-generated
math problems organized into courses and topics, checks answers, and lets each
signed-in user pick which topics they want to practice.

Problems are produced by [mathgenerator](https://github.com/lukew3/mathgenerator),
a library of parameterized math-problem generators, vendored under the backend.

## Repository structure

```
solveki/
├── backend/     Django REST API (problem generation, decks, auth, settings)
│   ├── config/          Django project (settings, URLs, WSGI/ASGI)
│   ├── myapp/           App: models, views, migrations, seed commands
│   └── mathgenerator/   Vendored problem-generator library
├── frontend/    React + Vite single-page app
└── bruno/       Bruno API collection for exercising the backend
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- A Google OAuth client ID (sign-in uses Google)

## Getting started

### Backend (Django, port 8000)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .                   # installs deps from pyproject.toml
python manage.py migrate
python manage.py seed_courses      # load courses
python manage.py seed_topics       # load topics
python manage.py runserver
```

Configuration is read from environment variables or a `backend/.env` file
(git-ignored). At minimum set the Google OAuth client ID:

```
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

### Frontend (React + Vite, port 5173)

```bash
cd frontend
npm install
npm run dev
```

Set the backend URL in `frontend/.env`:

```
VITE_API_URL=http://localhost:8000
```

The Vite dev server (`:5173`) talks to Django (`:8000`) with credentialed
requests, so the backend allows that origin via CORS.

## API

The backend exposes a small JSON API under the app's URLs, including:

- `POST /auth/google/`, `GET /auth/me/`, `POST /auth/logout/` — authentication
- `GET /problem/` — generate a problem
- `GET /deck/`, `POST /deck/advance/` — the daily practice deck
- `GET /courses/`, `GET /courses/<id>/topics`, `POST /topics/<id>/select` — course/topic selection
- `GET|POST /settings/` — user settings

See [backend/myapp/urls.py](backend/myapp/urls.py) for the full list. The
[bruno/](bruno/) collection contains ready-to-run requests against these
endpoints.
