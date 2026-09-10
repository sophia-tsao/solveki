# Solveki — Design

Solveki is a math-practice web app. A Django JSON API backend serves generated
math problems to a React single-page frontend. Users sign in with Google, pick
course topics, and work through a daily deck of problems. A Bruno collection
documents the API for manual QA.

Every user chooses a **role** once at sign-up — *student* or *teacher* — which
decides which half of the app they see. Students practice, take a diagnostic to
onboard, and complete teacher assignments; teachers create classes, author
assignments, and track student progress. See [Roles, classes, and
assignments](#roles-classes-and-assignments).

## Repo layout

```
solveki/
├── backend/          Django project — JSON API, problem generators, DB (SQLite dev / Postgres prod)
│   ├── config/       project package (settings, urls, asgi/wsgi)
│   └── myapp/        the single app (models, views, generators, tests, commands)
├── frontend/         React 19 SPA built with Vite (unit tests + Playwright e2e)
├── bruno/            Bruno API client collection (one request per endpoint)
├── README.md
└── .github/          CI
```

## Backend (Django 6.0.4)

Plain Django with function-based views returning `JsonResponse` — no DRF.
Dependencies (`backend/pyproject.toml`): `django==6.0.4`,
`django-cors-headers`, `google-auth`, `mathgenerator==1.5.0`, plus deployment
deps (`gunicorn`, `psycopg`, `dj-database-url`, `whitenoise`). Python ≥ 3.12.
The database is SQLite in local development and Postgres in production (see
[Deployment](#deployment)).

### Authentication

Google ID tokens are verified server-side
(`google.oauth2.id_token.verify_oauth2_token`) and mapped to a Django session
login. The SPA sends the session cookie cross-origin, so
`CORS_ALLOW_CREDENTIALS = True`; the allowed origins and cookie flags are
environment-driven — the Vite dev origin (`http://localhost:5173`) with `Lax`
cookies locally, the Vercel origin with `SameSite=None; Secure` cookies in
production (see [Deployment](#deployment)). `settings.py` uses a small
dependency-free `_load_dotenv()` to read `backend/.env`.

**Roles.** Each user's role (`student` / `teacher`) lives on their `Settings`
row and is chosen once at first sign-in via `POST /settings/role/`. The endpoint
refuses to change a role already marked `role_chosen`, so a student can't later
promote themselves to teacher to read other students' data — the frontend's
role picker is a convenience, this check is the real guard. Teacher-only
endpoints call `_require_teacher` (401 if anonymous, else 403 for a non-teacher)
the same way every view calls `_require_auth`.

### Data model (`backend/myapp/models.py`)

- **Course** — `course_name`, `grade_level`.
- **Topic** — `topic_name`, FK `course`, and `generator_name` (the string that
  maps a topic to a generator callable). This field is the linchpin of the
  generator system.
- **UserTopicSelection** — per-user selection row (user, topic), unique
  together; row existence means "selected".
- **TopicReview** — per (user, topic) SM-2 scheduling state: `ease`, `interval`,
  `repetitions`, `due_date`. Solveki schedules *topics*, not individual problems
  (every problem is freshly generated), so the schedulable unit is the user's
  mastery of a topic. Kept separate from `UserTopicSelection` on purpose:
  deselecting a topic drops the selection row but preserves its review state for
  when it's selected again. A null `due_date` means "never practiced → due now".
- **DailyTopicGrade** — per (user, topic, date), supports the once-per-day
  grading rule (see below). Stores a snapshot of the topic's SM-2 state *before*
  the day's first grade plus the worst quality seen so far today, so repeated
  answers recompute from a fixed base instead of compounding.
- **DailyPractice** — one row per (user, date), tracking `answered`/`total` for a
  day's deck. `DailyDeck` rows are pruned when a new day starts and
  `DailyTopicGrade` counts topics rather than problems, so neither can say after
  the fact whether a past day was finished; this durable record gives the
  dashboard calendar a stable "completed / partial / none" signal.
- **Settings** — one-to-one per user; `language`, `questions_per_day`, and the
  user's `role` (`student`/`teacher`) plus `role_chosen`. Role rides along with
  the per-user config that `Settings.load(user)` provisions on demand rather than
  living on a separate profile.
- **DailyDeck** — per user + date; `problems` (JSON list of `{problem, solution,
  topic_id}`), `current_index`, and `needs_regen`. `topic_id` attributes each
  stored problem back to its source topic so an answer can be graded against that
  topic. `needs_regen` is a dirty flag: a topic/course selection change sets it
  (a tiny write) instead of rebuilding the deck inline, and the unanswered tail
  is regenerated lazily on the next `GET /deck` (see "Filling the deck" below).

The teacher/student class-and-assignment feature adds a further cluster of
models (detailed in [Roles, classes, and assignments](#roles-classes-and-assignments)):

- **Classroom** / **ClassEnrollment** — a teacher-owned class with a unique
  `join_code`, and one enrollment row per (class, student).
- **Assignment** / **AssignmentTopic** / **AssignmentClass** — a teacher-authored
  task (its `mode` encodes both *topics vs deck* and *whether SM-2 is applied*),
  its optional explicit topic list with per-topic question counts, and the links
  handing it to classes with per-class `available_at`/`due_at`.
- **StudentAssignment** / **AssignmentAttempt** — one student's instance of an
  assignment (their generated `problems` + progress, same JSON shape as
  `DailyDeck`), and one normalized row per answered problem for analytics.

### Endpoints (`backend/myapp/urls.py`)

| Method | Path | View |
| --- | --- | --- |
| GET | `auth/me/` | `me` |
| POST | `auth/google/` | `google_login` |
| POST | `auth/test-login/` | `test_login` (E2E only; 404 unless `ENABLE_TEST_LOGIN`) |
| POST | `auth/logout/` | `logout_view` |
| DELETE | `auth/delete/` | `delete_account` |
| GET | `problem/` | `generate_problem` |
| GET | `deck/` | `get_deck` |
| POST | `deck/advance/` | `advance_deck` |
| GET | `dashboard/` | `view_dashboard` |
| GET | `practice-calendar/` | `view_practice_calendar` |
| GET/PATCH | `settings/` | `settings_view` |
| POST | `settings/role/` | `set_role` (one-time role choice) |
| GET | `courses/` | `view_courses` |
| GET | `topics/` | `view_topics` |
| GET | `courses/<id>/topics` | `view_course_topics` |
| PATCH | `courses/<id>/select` | `set_course_topics_selected` |
| PATCH | `topics/<id>/select` | `toggle_topic` |
| GET | `diagnostic/config/` | `diagnostic_config` |
| POST | `diagnostic/start/` | `diagnostic_start` |
| POST | `diagnostic/submit/` | `diagnostic_submit` |
| GET/POST | `classes/` | `classes` (teacher: list/create) |
| GET/PATCH/DELETE | `classes/<id>/` | `class_detail` (teacher) |
| GET | `classes/<id>/students/` | `class_students` (teacher) |
| DELETE | `classes/<id>/students/<sid>/` | `remove_student` (teacher) |
| POST | `classes/join/` | `join_class` (student) |
| GET | `classes/mine/` | `my_classes` (student) |
| GET/POST | `assignments/` | `assignments` (teacher: list/create) |
| GET/PATCH/DELETE | `assignments/<id>/` | `assignment_detail` (teacher) |
| POST | `assignments/<id>/assign/` | `assign_to_classes` (teacher) |
| GET | `assignments/<id>/preview/` | `assignment_preview` (teacher) |
| GET | `assignments/<id>/results/` | `assignment_results` (teacher analytics) |
| GET | `assignments/mine/` | `my_assignments` (student) |
| GET | `assignments/<id>/play/` | `play_assignment` (student) |
| POST | `assignments/<id>/advance/` | `advance_assignment` (student) |
| GET | `teacher/overview/` | `teacher_overview` (teacher analytics) |
| GET | `teacher/students/<sid>/` | `student_detail` (teacher analytics) |

Selection is exposed as strings, not booleans. Each topic in `view_topics` /
`view_course_topics` carries a `selection_status` of `"selected"` |
`"unselected"`, and each course in `view_courses` a `topic_selection_status` of
`"all"` | `"partial"` | `"none"` derived from its topics (`_course_selection`).
The `PATCH .../select` endpoints are the exception: they still take a boolean
`is_selected` body because they express a select/deselect *command*, distinct
from the displayed state. The frontend applies these optimistically (flip the
checkbox before the request, roll back on failure) so a slow round-trip doesn't
read as a dead click.

Deck logic (`_get_or_create_today_deck`, `_generate_problems`, `_deck_payload`)
builds a per-day deck of `questions_per_day` problems and discards stale
prior-day decks. Problems are chosen by spaced-repetition due order
(`_ordered_topics`): most-overdue topics first, never-practiced topics treated
as due today, not-yet-due topics only once the due ones run out (ties break by
topic id for a deterministic order). Distinct topics fill the deck first for
variety; when fewer topics are selected than `questions_per_day`, topics repeat
by cycling the same due order. `advance_deck` only ever steps an *existing* deck
forward — it never builds one. Otherwise a new day's deck (fresh at index 0)
could be advanced to index 1 without the student answering, stranding them on
"2 of N"; this bites because the correct-answer handler advances on a timer, so
finishing a problem just before midnight fires the advance after the day rolls
over.

When the student advances past a card, the client reports how it was answered
(`correct_first` / `correct_second` / `incorrect`) in the advance body; the
deck layer maps that outcome to an SM-2 quality grade and updates the card's
topic schedule (`_grade_topic`). The outcome is optional, so a stray advance
with no answer (the midnight-rollover case) simply doesn't grade.

"The day" is the *user's* local day, not the server's. The server clock is UTC
(`TIME_ZONE`), so every deck-touching request carries the client's local date
as `?today=YYYY-MM-DD` (`_client_today`); the deck then resets at the user's
midnight rather than UTC's. Requests without the param fall back to the server
date. The SPA also re-fetches the deck when the tab is refocused on a new local
day, so a page left open overnight rolls over instead of stranding the student
on yesterday's finished deck.

## Spaced repetition (SM-2)

Solveki schedules practice with SuperMemo-2. The design splits cleanly into
*pure scheduling math* and *stateful application*:

- **`backend/myapp/srs.py`** is the whole SM-2 algorithm and nothing else: pure
  functions with no database, request, or clock access. It maps
  `(ease, interval, repetitions, quality) -> (ease, interval, repetitions)` and
  can be reasoned about and unit-tested in isolation. State is the SM-2 triple:
  `ease` (interval multiplier, starts 2.5, floored at 1.3), `interval` (days to
  the next review), and `repetitions` (consecutive successful recalls, reset on
  a lapse). A successful recall (`quality >= 3`) grows the interval — 1 day, then
  6, then `interval * ease` — capped at `MAX_INTERVAL` (365 days, borrowed from
  Anki's notion of a max interval but tuned so a mastered topic still resurfaces
  at least yearly). A lapse resets `repetitions` to 0 and `interval` to 1 day.
- **The deck layer owns persistence, dates, and grade derivation.**
  `_grade_topic` (in `views/deck.py`) turns an answer outcome into a quality
  grade (`correct_first` → 5, `correct_second` → 3, `incorrect` → 1), calls
  `srs.update`, and writes the topic's `TopicReview` (including its new
  `due_date = today + interval`). `_ordered_topics` reads those `due_date`s to
  order the deck but never computes them.

### Filling the deck: due-weighted dose

SM-2 schedules one review per item on its due date, but Solveki always fills the
day to `questions_per_day` so a student with few selected topics still gets a
full practice session. Rather than repeat topics evenly, `_generate_problems`
weights how much of the deck each topic gets by *how overdue* it is
(`_due_weight`): a topic due today or overdue takes a larger share than one whose
next review is days out. Every selected topic keeps at least one slot (a variety
floor), and the remaining slots are split by weight using the largest-remainder
method so the counts stay deterministic and sum to exactly `questions_per_day`.
This carries SM-2's core signal — practice the due thing more — into the *within-
day dose*, not just the ordering: after a lapse, that topic both leads the deck
and occupies more of it the next day, while a mastered topic recedes to its floor
slot. Equal-priority topics reduce to an even split.

### Regenerating on selection changes: the dirty flag

When a student changes their topic selection mid-day, the deck's *unanswered
tail* has to be rebuilt against the new set (answered cards are kept). Doing that
inline on every `PATCH .../select` was the wrong place for it: regeneration runs
the problem generators, whose first call per process warms up the (sympy-backed)
generator library — a one-off cost that made the first toggle after a cold start
take ~12s while later ones were sub-second, and rapid clicks piled up. So a
toggle now only sets `DailyDeck.needs_regen` (`_mark_deck_stale`, a boolean
`UPDATE`), and the next `GET /deck` — the practice-page load — sees the flag,
rebuilds the tail once (`_regenerate_deck_tail`), and clears it. This keeps
toggles cheap regardless of deck size or click speed, and moves the heavy work to
a page load where a brief spinner is expected. (The diagnostic still regenerates
eagerly: it's a one-shot after onboarding, not a hot path.)

### The once-per-day grading rule

A topic can appear more than once in a day's deck (the deck repeats topics when
few are selected). The rule: **the first answer for a topic each day sets its
schedule; later repeats may only pull it down** — a second miss re-grades as a
lapse, but a later success can't raise a schedule the student already got wrong.

To apply that without compounding (repeated misses must not drop ease over and
over), `DailyTopicGrade` snapshots the topic's SM-2 state *before* the day's
first grade and records the worst quality applied so far today. Each occurrence
recomputes the `TopicReview` from that fixed snapshot using
`min(applied_quality, this_quality)`, so the day's net effect is always "one
SM-2 update from a single base", never a chain of them.

### Tests

`tests/test_srs.py` unit-tests the pure algorithm (including grade boundaries);
`tests/test_srs_integration.py` covers the deck-layer wiring (due ordering,
grading, the once-per-day rule) end to end.

## The onboarding diagnostic

A new user faces 300-plus topics with no idea which to pick — a cold-start problem.
The diagnostic (`backend/myapp/diagnostic_config.py` + `views/diagnostic.py`)
solves it: a couple of profile questions (current course, unit reached) plus a
handful of freshly generated calibration problems infer the user's level **per
math category** (elementary, middle, algebra, geometry, statistics, precalculus,
calculus), and that inference drives (a) which courses of each category to select
and (b) how to seed each selected topic's SM-2 schedule so already-mastered
material starts further out.

The split mirrors `srs.py`: `diagnostic_config.py` holds the category taxonomy
and the pure level-inference/seeding rules (no Django, no HTTP), so they can be
unit-tested in isolation; `views/diagnostic.py` resolves category course names to
`Topic` rows, generates the calibration problems, and writes the resulting
`UserTopicSelection` / `TopicReview`. The categories list course names verbatim
from `seed_courses.CURRICULUM`, so the feature needs no schema change.

## Roles, classes, and assignments

The teacher side of the app is built on top of the same problem-generation and
SM-2 machinery students use, so a teacher's assignment is graded and (optionally)
scheduled exactly the way normal practice is.

### Roles

Every user has a role on their `Settings` row, chosen once at first sign-in
(`POST /settings/role/`). The endpoint is the authority — it refuses to change a
role already marked `role_chosen`, so the choice can't be escalated later; the
frontend's role picker just makes the choice. `_require_teacher` gates every
teacher-only endpoint (401 anonymous → 403 non-teacher), and the SPA restricts
navigation to the pages of the current role. Students supply a first/last name at
sign-up (the name teachers see); it's stored on the Django user.

### Classes

A **Classroom** is teacher-owned and carries a short, unique `join_code` drawn
from an unambiguous alphabet (no `O/0/I/1`) so it's safe to read off a board. A
student joins by posting the code (`POST /classes/join/`), creating a
**ClassEnrollment**. Every teacher class endpoint runs an ownership guard
(`_get_owned_class`, 404/403) so a teacher can only act on classes they created;
a student can only see the classes they're enrolled in. Classes can be archived
(hidden from the default lists but retained so past analytics still resolve
them).

### Assignments: one authoring, many classes

An **Assignment** is authored once and handed to any number of classes through
**AssignmentClass** links (each carrying that class's `available_at`/`due_at`),
so editing or deleting the assignment affects every class it reached. It has two
orthogonal dimensions, packed into a single `mode` field (read via the
`is_topics`/`is_deck`/`sm2_enabled` properties, composed via `make_mode`):

- **Delivery kind.** *Topics* — the teacher picks specific topics and a question
  count each (`AssignmentTopic` rows). *Deck* — the student gets a
  spaced-repetition deck of `deck_size` problems, either across all their
  selected topics (`deck_scope='all'`) or limited to a teacher-picked topic set
  (`deck_scope='topics'`, which is also added to the student's own selections so
  it carries into their daily practice). Legacy `course`/`unit` scopes remain for
  older assignments.
- **SM-2 or not.** A `*_sm2` mode feeds the result back into the student's
  `TopicReview` schedule on completion; otherwise assignment answers never touch
  their schedule.

### Taking an assignment

Problems are generated **per student on first open** (`play_assignment`) and
stored inline on a **StudentAssignment** in the same JSON shape as `DailyDeck`
(`{problem, solution, topic_id}`), so each student gets fresh numbers. A deck-kind
assignment reuses the deck layer's due-weighting (`_effective_due_dates` /
`_weighted_slot_counts`) so overdue topics get more of the questions — exactly
like normal practice. The student answers card-by-card with the same two-attempt
UI; `advance_assignment` records one **AssignmentAttempt** per problem (outcome +
correctness, mirroring the deck's outcome strings) and, on the final card, marks
the instance completed.

If SM-2 is enabled, completion applies **one grade per topic derived from
accuracy** (`_apply_sm2_from_accuracy` → `_accuracy_to_quality`), routed through
the deck's shared `_apply_quality` so it obeys the same once-per-day rule as
normal practice. A student who opens a deck assignment with no topics in scope
yet isn't persisted as an instantly-"completed" zero-problem instance; the view
returns an `empty` marker so the client can explain rather than congratulate.

### Teacher analytics

`AssignmentAttempt` is normalized (one row per answered problem) so analytics are
ORM aggregations rather than JSON scans. `assignment_results` reports average
accuracy, per-topic accuracy sorted worst-first ("most struggled with"), and each
student's accuracy and time taken. `teacher_overview` rolls those up across all
of a teacher's classes; `student_detail` combines a student's SM-2 topic stats —
the *same* view their own dashboard shows — with their assignment history, and is
gated so a teacher can only open a student enrolled in one of their classes.

## Frontend (React 19 + Vite 8)

Located at `frontend/` (top-level, a sibling of `backend/`). Uses KaTeX for
math rendering and oxlint for linting. `App.jsx` is a top-level hash router
(`#/page` or `#/page/42` for the detail pages, parsed without a router library).
`LoginPage` shows when unauthenticated; a brand-new user then hits `RolePicker`
before entering the app. The set of reachable pages is **keyed by role**
(`STUDENT_PAGES` / `TEACHER_PAGES`), so a student can't navigate to a teacher
page by editing the URL — and the backend enforces the same on every endpoint.

- **Student pages.** Practice UI in `MathProblem.jsx` /
  `MathProblemDisplay.jsx` / `MathProblemResponse.jsx` (problem rendering, answer
  box, two-attempt flow); course selection in `CourseList.jsx` / `CourseBar.jsx`;
  `Dashboard.jsx`; the onboarding `Diagnostic.jsx`; `Assignments.jsx` /
  `AssignmentPlayer.jsx`; `StudentClasses.jsx`.
- **Teacher pages.** `TeacherOverview.jsx`, `ClassList.jsx` / `ClassDetail.jsx`,
  `StudentDetail.jsx`, `TeacherAssignments.jsx` / `AssignmentBuilder.jsx` /
  `AssignmentDetail.jsx`, and a `TeacherGuide.jsx` new teachers land on first.

Auth helpers (including the `apiFetch` credentialed wrapper) live in `auth.js`.

## Testing

Three layers. Backend unit tests (`backend/myapp/tests/`) and frontend unit
tests (Vitest, colocated `*.test.jsx`) cover units in isolation. A Playwright
end-to-end suite (`frontend/e2e/`) drives a real browser through the built SPA
against a live Django API, covering the login gate, topic selection, the daily
deck flow, and settings. Since Google OAuth can't run headless, E2E auth goes
through `POST /auth/test-login/`, gated behind `ENABLE_TEST_LOGIN` (404 when
off) and resetting the shared test user's state on each call. The suite runs
serially (one shared backend user → no DB isolation between tests) and has its
own CI workflow (`.github/workflows/e2e-tests.yml`). See the README for how to
run it.

## Deployment

The app runs entirely on free tiers, split across three services chosen so that
nothing has to stay always-on:

```
   Browser
      │
      ▼
┌──────────────┐   HTTPS + cookies    ┌──────────────────┐   TLS    ┌──────────────┐
│  Frontend    │ ───────────────────► │  Backend         │ ───────► │  Database    │
│  (Vercel)    │                      │  (Cloud Run)     │          │  (Neon PG)   │
│  Vite SPA    │ ◄─────────────────── │  Django+Gunicorn │ ◄─────── │  Postgres    │
└──────────────┘                      └──────────────────┘          └──────────────┘
```

- **Frontend → Vercel.** The Vite SPA builds to static assets (`npm run build`
  → `dist/`), which Vercel serves from its CDN.
- **Backend → Google Cloud Run.** Cloud Run runs a container that listens for
  HTTP on `$PORT`; it scales to zero when idle (so an unused app costs nothing)
  and its always-free quota does not expire. It was chosen over the two
  serverless options that first come to mind: **Firebase** can't run a Django
  WSGI app at all (its functions are Node/Flask-shaped and event-triggered), and
  **AWS Lambda** can only via an adapter (Mangum) plus VPC networking and
  native-dependency packaging. Cloud Run runs our existing Gunicorn/WSGI app
  *unchanged* — the same `config.wsgi:application` a normal server would use — so
  no serverless-specific code enters the project.
- **Database → Neon Postgres.** Neon is managed, serverless Postgres on a
  free-forever tier that also scales to zero, matching Cloud Run. It replaces the
  dev SQLite file (see below for why SQLite can't follow us to production).

### The environment-variable principle

Every production behavior is gated behind an environment variable with a
development-friendly fallback. **With no env vars set the app behaves exactly as
it does on a developer's machine** (SQLite, `DEBUG` on, `Lax` cookies over
HTTP); Cloud Run supplies the env vars that flip each setting into its production
form. This keeps `python manage.py runserver` working with zero configuration
while the same `settings.py` serves production.

| Env var | Unset (local dev) | Set (Cloud Run) |
| --- | --- | --- |
| `SECRET_KEY` | insecure `django-insecure-…` fallback | strong per-deploy secret |
| `DEBUG` | `True` | `0` (off) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | the `*.run.app` host |
| `DATABASE_URL` | local `db.sqlite3` | Neon Postgres URL |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | the Vercel origin |
| `CSRF_TRUSTED_ORIGINS` | (empty) | the Vercel origin |
| `GOOGLE_OAUTH_CLIENT_ID` | from `.env` | set directly |

### `SECRET_KEY`

`SECRET_KEY` is Django's cryptographic signing key. Django uses it to sign
anything a user shouldn't be able to forge — session cookies, CSRF tokens,
password-reset tokens, and other signed values. If the key leaks, an attacker
can mint valid session cookies and impersonate any user, so it must be secret
and unpredictable. The project ships a `django-insecure-…` placeholder (fine for
local dev, and it's in git), but production reads a real key from the
environment: `SECRET_KEY = os.environ.get('SECRET_KEY', <local fallback>)`. The
deploy generates a fresh one with `python -c 'import secrets;
print(secrets.token_urlsafe(50))'` and passes it as a Cloud Run env var, so the
real key never lives in the repo.

### Database: `dj-database-url` (SQLite stays the local default)

SQLite is a single file on local disk. Cloud Run's filesystem is **ephemeral and
per-instance** — wiped when an instance recycles, and not shared between the
parallel instances Cloud Run spins up under load — so a `db.sqlite3` there would
silently lose writes. Production therefore needs a networked database (Neon),
which every instance connects to over TLS.

Rather than branch on the environment by hand, the `DATABASES` setting delegates
to `dj-database-url`:

```python
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
        ssl_require=os.environ.get('DATABASE_URL', '').startswith('postgres'),
    )
}
```

`dj_database_url.config()` reads the `DATABASE_URL` env var and parses that one
connection string into the verbose dict Django expects (engine, name, host,
user, …). The `default=` argument is used **only when `DATABASE_URL` is unset**,
and it points at the local SQLite file — so a developer's `runserver` is
unchanged, while Cloud Run's `DATABASE_URL` switches the app to Postgres with no
code edit. `conn_max_age=600` keeps a connection alive up to ten minutes so
requests reuse it instead of paying network-connection latency every time;
`ssl_require` forces TLS, but only for Postgres (the local SQLite file has no
network to encrypt).

### Static files: WhiteNoise + `STATIC_ROOT`

Django does not serve static files (the Django admin's CSS/JS, etc.) in
production — in development `runserver` does it as a convenience, but the real
WSGI app expects a separate web server or CDN in front. Cloud Run has no nginx,
so the app serves its own static files via **WhiteNoise**:

- `python manage.py collectstatic` copies every app's static files into one
  directory, `STATIC_ROOT` (`backend/staticfiles/`). This runs at image-build
  time in the Dockerfile, so the files are baked into the container.
- `whitenoise.middleware.WhiteNoiseMiddleware` (placed immediately after
  `SecurityMiddleware`) serves files from `STATIC_ROOT` on matching requests.
- The `CompressedManifestStaticFilesStorage` backend gzip-compresses each file
  and adds a content hash to its name (e.g. `admin.abc123.css`) so browsers can
  cache aggressively yet still pick up changes.

### CSRF and cross-site cookies

In production the SPA (`*.vercel.app`) and the API (`*.run.app`) are on
different sites, which changes how the session cookie and CSRF protection must
be configured versus local dev (where both sit on `localhost`):

- **Session cookie.** Locally it's `SameSite=Lax` over HTTP. In production it
  must be `SameSite=None; Secure` — `None` so the browser sends it on cross-site
  requests, `Secure` because browsers require that pairing (and only send it over
  HTTPS). These flip on automatically when `DEBUG` is off.
- **CORS.** `CORS_ALLOWED_ORIGINS` lists the Vercel origin and
  `CORS_ALLOW_CREDENTIALS = True` lets the browser include the session cookie on
  cross-origin calls — the counterpart to the frontend's `credentials: 'include'`
  in `apiFetch` (`frontend/src/auth.js`).
- **CSRF.** For state-changing requests Django checks the request's origin
  against `CSRF_TRUSTED_ORIGINS`, so the Vercel URL must be listed there or those
  requests are rejected.
- **Proxy scheme.** Cloud Run terminates TLS at its proxy and forwards the
  original scheme in `X-Forwarded-Proto`. `SECURE_PROXY_SSL_HEADER` tells Django
  to trust that header so it knows the request was HTTPS — without it Django
  thinks the request is plain HTTP and refuses to set `Secure` cookies.

### Build and deploy mechanics

- **Backend.** A `Dockerfile` (`python:3.13-slim` → `pip install .` →
  `collectstatic` → `gunicorn --bind :$PORT config.wsgi:application`) defines the
  image. Deploy from the `backend/` directory with the service named explicitly:
  `gcloud run deploy solveki-backend --project solveki --region us-central1
  --source .`. Naming it matters — a bare `gcloud run deploy` defaults the service
  name to the current folder, which creates a *new* service (new URL) instead of
  redeploying. Production config (secret, database URL, allowed hosts, origins) is
  passed as Cloud Run env vars.
- **Database.** A Neon project provides the Postgres instance; use its **pooled**
  connection string (host contains `-pooler`) for serverless compute. Migrations
  are a **separate step from the code deploy** and must be run against Neon
  whenever a deploy includes a new migration (`DATABASE_URL=… python manage.py
  migrate`). The deployed image does *not* run `migrate` on boot, so shipping code
  that references a new column without applying its migration first 500s every
  request that touches that table (`UndefinedColumn`) until the migration is run.
- **Frontend.** Vercel builds with root directory `frontend`, framework preset
  Vite. `VITE_API_URL` (the Cloud Run URL) and `VITE_GOOGLE_CLIENT_ID` are set as
  build-time env vars — Vite inlines `VITE_*` values at build time.
- **Google OAuth.** The deployed Vercel (and Cloud Run) URLs must be added to the
  OAuth client's *Authorized JavaScript origins* in the Google Cloud Console, or
  Google sign-in is rejected.

## The math generator system

This is the core design decision, reshaped by commit *"De-vendor
mathgenerator, add generator contract tests"*.

### Background: why de-vendored

The repo previously vendored a **fork** of `mathgenerator` under
`backend/mathgenerator/`. The fork added three custom generators not present in
PyPI's `mathgenerator==1.5.0`: `vertex_form`, `angle_sum`, and
`aroc_over_interval`. Maintaining a whole forked library to carry three
functions is expensive. The commit deleted the vendored copy, switched to the
pip dependency, and preserved just the three custom generators in a new
first-party package, `backend/myapp/generators/`.

### The generator contract

A generator is a **zero-required-arg callable that returns `(problem,
solution)`**. This is deliberately identical to a `mathgenerator` generator, so
the app's own generators and library generators are interchangeable at the call
site.

### Importing the library

The pip package is imported directly where problems are made:

```python
import mathgenerator
```

Its generators are resolved by name via `getattr(mathgenerator, name)`.

### The local registry (`backend/myapp/generators/_registry.py`)

Local generators register themselves with a decorator at import time:

```python
# name -> generator callable. Populated by @register at import time.
LOCAL_GENERATORS = {}

def register(fn):
    """Register `fn` under its own name. Raises on a duplicate name."""
    name = fn.__name__
    if name in LOCAL_GENERATORS:
        raise ValueError(f"Duplicate local generator name: {name!r}")
    LOCAL_GENERATORS[name] = fn
    return fn
```

### Package init — the import side-effect trick (`generators/__init__.py`)

Registration only happens when a category module is imported, so the package
`__init__.py` imports each category module for its side effects:

```python
from ._registry import LOCAL_GENERATORS, register  # noqa: F401

# Import each category module for its @register side effects. Add new modules
# here as you create them (e.g. calculus, geometry).
from . import algebra, geometry  # noqa: F401,E402

__all__ = ["LOCAL_GENERATORS", "register"]
```

### An example generator (`generators/algebra.py`)

```python
from ._registry import register

@register
def vertex_form(min_val=-10, max_val=10, min_a=-5, max_a=5):
    r"""Vertex of a Quadratic in Vertex Form ..."""
    a = random.choice([i for i in range(min_a, max_a + 1) if i != 0])
    h = random.randint(min_val, max_val)
    k = random.randint(min_val, max_val)
    h_str = f"x{'+' if -h >= 0 else '-'}{abs(h)}" if h != 0 else "x"
    a_str = "" if a == 1 else ("-" if a == -1 else str(a))
    problem = f"Find the coordinates of the vertex of $y={a_str}({h_str})^2{'+' if k >= 0 else '-'}{abs(k)}$"
    solution = f"$({h}, {k})$"
    return problem, solution
```

Generators may declare default kwargs but must be callable with zero args.
`algebra.py` holds `vertex_form` and `aroc_over_interval`; `geometry.py` holds
`angle_sum`.

### Resolving a name to a generator (`views/problems.py`, `_make_problem`)

The local registry and the library are fused here — local generators win, then
the library is the fallback:

```python
from .generators import LOCAL_GENERATORS
import mathgenerator

# Prefer our own generators, then fall back to the mathgenerator library.
generator = LOCAL_GENERATORS.get(name) or getattr(mathgenerator, name, None)
if generator is None:
    # Unknown name (renamed/removed by a library upgrade) -> no problem,
    # rather than 500-ing the student.
    return None
problem, solution = generator()
```

`_make_problem` picks a random `generator_name` among the user's selected
topics, resolves it, invokes it, then normalizes the solution (strips LaTeX
`$`, rounds decimals, appends a rounding instruction when rounding changes the
value).

### Wiring topics to generators (`management/commands/seed_topics.py`)

`Topic.generator_name` is the only link. The `TOPICS` seed list maps each topic
to a generator name — the three custom locals plus ~60 stock library names:

```python
("Average Rate of Change over Interval", "aroc_over_interval"),
("Angle Sum", "angle_sum"),
("Vertex of a Quadratic in Vertex Form", "vertex_form"),
("Addition", "addition"),          # stock mathgenerator
("Area of Triangle", "area_of_triangle"),
```

### Contract tests (`myapp/tests/test_generators.py`)

- **`SeedGeneratorContractTests`**
  - `test_names_exist` — every seeded `generator_name` is in
    `mathgenerator.get_gen_list()` ∪ `LOCAL_GENERATORS`. Guards against library
    upgrades or typos silently breaking a topic.
  - `test_names_produce_output` — resolves each name the way `_make_problem`
    does and calls it (retries up to 5 times under a fixed seed so a degenerate
    random draw can't flake CI).
- **`LocalGeneratorTests`** (stronger checks for owned code)
  - `test_all_local_generators_return_well_formed_pairs` — non-empty string
    problem and solution.
  - `test_vertex_form_is_deterministic_under_seed` — stable output under a
    fixed seed.

## How generators are exposed via the API

There is **no endpoint that lists generators**. They are exposed indirectly
through topics: `view_courses` / `view_course_topics` return topics (including
`generator_name`) with per-user selection state; the frontend lets the user
select topics; `generate_problem` and the deck endpoints call `_make_problem`,
which randomly chooses among the selected topics' generators and returns
`{problem, solution}`. Unknown names degrade gracefully to "no problem."

## Adding a new custom generator

1. Write `@register def foo(): return problem, solution` in the appropriate
   category module under `backend/myapp/generators/` (or add a new category
   module).
2. If it's a new module, import it in `generators/__init__.py` so its
   `@register` runs.
3. Add a `("Some Topic", "foo")` entry to `TOPICS` in `seed_topics.py`.

The contract tests then automatically verify it resolves and produces output.
```

