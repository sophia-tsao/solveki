# Solveki

Solveki is a math practice web app. It serves an endless deck of auto-generated
math problems organized into courses and topics, checks answers, and lets each
signed-in user pick which topics they want to practice. Everyone chooses a role
once at sign-up — **student** or **teacher** — which decides what they see.

Practice is scheduled with spaced repetition: each answer grades the underlying
topic on the SM-2 algorithm, and the daily deck surfaces topics in due order and
gives more of the deck to the topics that are due, so struggled-with topics come
back soon and take up more of your session while mastered ones resurface less
often.

A progress dashboard shows each selected topic's SM-2 state (ease, interval,
repetitions, due date), what's coming up in the next deck, and a per-day
practice calendar that marks each day as completed, partial, or unpracticed. New
students can skip manual topic-picking with a short **diagnostic**: a couple of
profile questions plus a few generated problems infer their level per math
category and pick starting topics with a pre-seeded review schedule.

Teachers get a separate side of the app: create **classes** that students join
with a code, author **assignments** (a set of topics plus how many cards a day
the practice deck should hold), and assign them to classes with due dates.
Opening an assignment adds its topics to the student's own practice and grows
their daily deck to the chosen size, so assignment work is graded and scheduled
by the same SM-2 engine as normal practice. Teachers track progress through a
familiarity-over-time view (the share of topics in each proficiency band, for
all students or a single class), a per-assignment report of proficiency on the
assigned topics and who has practiced by the due date, and a per-student view of
their SM-2 progress and assignment history.

Problems are produced by [mathgenerator](https://github.com/lukew3/mathgenerator),
a library of parameterized math-problem generators (a pip dependency), plus a
handful of first-party generators under `backend/myapp/generators/`.

## Repository structure

```
solveki/
├── backend/     Django JSON API (problem generation, decks, auth, settings)
│   ├── config/          Django project (settings, URLs, WSGI/ASGI)
│   └── myapp/           App: models, views, generators, migrations, seed commands
├── frontend/    React + Vite single-page app (unit tests + Playwright e2e)
├── bruno/       Bruno API collection for exercising the backend
└── .github/     CI workflows
```

See [DESIGN.md](DESIGN.md) for the architecture, including the generator system.

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
python manage.py seed_topics       # load topics
python manage.py seed_courses      # create courses and link the topics to them
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

Set the backend URL and Google OAuth client ID in `frontend/.env`:

```
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

The Vite dev server (`:5173`) talks to Django (`:8000`) with credentialed
requests, so the backend allows that origin via CORS.

## API

The backend exposes a small JSON API under the app's URLs, including:

- `GET /auth/me/`, `POST /auth/google/`, `POST /auth/logout/`,
  `DELETE /auth/delete/` — authentication and account deletion
- `GET /problem/` — generate a problem
- `GET /deck/`, `POST /deck/advance/` — the daily practice deck (advancing may
  report an answer outcome that updates the topic's spaced-repetition schedule)
- `GET /dashboard/` — selected/upcoming topics with their SM-2 state
- `GET /practice-calendar/` — per-day practice status for a calendar month
- `GET /courses/`, `GET /courses/<id>/topics`, `PATCH /courses/<id>/select`,
  `GET /topics/`, `PATCH /topics/<id>/select` — course/topic browsing and selection
- `GET|PATCH /settings/`, `POST /settings/role/` — user settings and the one-time
  role choice (student/teacher)
- `GET /diagnostic/config/`, `POST /diagnostic/start/`, `POST /diagnostic/submit/`
  — the onboarding diagnostic (infers level, then selects and seeds topics)
- **Teacher — classes:** `GET|POST /classes/`, `GET|PATCH|DELETE /classes/<id>/`,
  `GET /classes/<id>/students/`, `DELETE /classes/<id>/students/<sid>/`
- **Teacher — assignments:** `GET|POST /assignments/`,
  `GET|PATCH|DELETE /assignments/<id>/`, `POST /assignments/<id>/assign/`,
  `GET /assignments/<id>/results/`
- **Teacher — analytics:** `GET /teacher/overview/`,
  `GET /teacher/proficiency-history/`, `GET /teacher/students/<sid>/`
- **Student — classes & assignments:** `POST /classes/join/`, `GET /classes/mine/`,
  `GET /assignments/mine/`, `GET /assignments/<id>/play/` (adds the assignment's
  topics to the student's practice and routes them to their deck)

See [backend/myapp/urls.py](backend/myapp/urls.py) for the full list. The
[bruno/](bruno/) collection contains ready-to-run requests against these
endpoints.

## Testing

- **Backend unit tests:** `cd backend && python manage.py test`
- **Frontend unit tests (Vitest):** `cd frontend && npm test`
- **End-to-end tests (Playwright):** see below.

### End-to-end tests

Playwright specs in [frontend/e2e/](frontend/e2e/) drive a real browser through
the full stack — the built React SPA against a live Django API — covering the
login gate, course/topic selection, the daily deck flow, and settings.

Because sign-in is Google-OAuth-only (which can't run headless), the suite
authenticates through a **test-only** endpoint, `POST /auth/test-login/`. It
logs in a fixed test user and is gated behind the `ENABLE_TEST_LOGIN` setting:
it returns **404 unless `ENABLE_TEST_LOGIN=1`**, so it can never be reached in a
normal or production run. Each call also resets that user's practice state
(selections, deck, settings) so tests start from a clean slate.

Run locally:

```bash
# 1. Backend with the test-login endpoint enabled (after migrate + seed).
cd backend
ENABLE_TEST_LOGIN=1 python manage.py runserver 8000

# 2. In another terminal: run the E2E suite. Playwright builds and serves the
#    SPA on :5173 itself (the origin the backend's CORS allows).
cd frontend
npm run test:e2e            # headless
npm run test:e2e:ui         # interactive UI mode for debugging
npx playwright show-report  # open the HTML report after a run
```

The suite runs on every pull request via
[.github/workflows/e2e-tests.yml](.github/workflows/e2e-tests.yml).
