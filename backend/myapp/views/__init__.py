"""HTTP views for myapp, split by concern.

This package used to be a single ``views.py``. It's kept importable as
``myapp.views`` with the same public surface, so ``urls.py`` and the test
suite need no changes. New code should import from the specific submodule
(e.g. ``from myapp.views.deck import _generate_problems``); the re-exports below
exist for backwards compatibility.
"""

# Re-exported so tests can patch ``myapp.views.mathgenerator`` and
# ``myapp.views.google_id_token`` (mock.patch resolves the module object here,
# and the submodules reference the same object). ``google_id_token`` is imported
# eagerly because ``.auth`` (imported just below) pulls in google-auth anyway;
# ``mathgenerator`` is deferred via ``__getattr__`` — see the note there.
from google.oauth2 import id_token as google_id_token  # noqa: F401

from .auth import (
    me,
    google_login,
    test_login,
    logout_view,
    delete_account,
)
from .courses import (
    view_courses,
    view_topics,
    view_course_topics,
    toggle_topic,
    set_course_topics_selected,
)
from .problems import generate_problem, _make_problem
from .settings import settings_view, set_role
from .deck import get_deck, advance_deck
from .dashboard import view_dashboard, view_practice_calendar
from .diagnostic import diagnostic_config, diagnostic_start, diagnostic_submit
from .classes import (
    classes,
    class_detail,
    class_students,
    remove_student,
    join_class,
    my_classes,
)
from .assignments import (
    assignments,
    assignment_detail,
    assign_to_classes,
    assignment_preview,
    assignment_results,
    my_assignments,
    play_assignment,
    advance_assignment,
)
from .teacher import teacher_overview, student_detail

def __getattr__(name):
    """Lazily expose ``mathgenerator`` as ``myapp.views.mathgenerator``.

    Importing mathgenerator costs ~1s and, inflated by Cloud Run's throttled
    single vCPU during a cold start, is the largest slice of cold-start latency
    — yet only problem generation needs it, not the URLconf load that every
    request (including the trivial /auth/me/) pays for. Keeping it out of module
    top level defers the cost to the first /problem/ (or /deck/) request. The
    attribute still resolves on access, so the test suite's
    ``mock.patch("myapp.views.mathgenerator.addition")`` keeps working.
    """
    if name == "mathgenerator":
        import mathgenerator
        return mathgenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "me",
    "google_login",
    "test_login",
    "logout_view",
    "delete_account",
    "view_courses",
    "view_topics",
    "view_course_topics",
    "toggle_topic",
    "set_course_topics_selected",
    "generate_problem",
    "settings_view",
    "set_role",
    "get_deck",
    "advance_deck",
    "view_dashboard",
    "view_practice_calendar",
    "diagnostic_config",
    "diagnostic_start",
    "diagnostic_submit",
    "classes",
    "class_detail",
    "class_students",
    "remove_student",
    "join_class",
    "my_classes",
    "assignments",
    "assignment_detail",
    "assign_to_classes",
    "assignment_preview",
    "assignment_results",
    "my_assignments",
    "play_assignment",
    "advance_assignment",
    "teacher_overview",
    "student_detail",
]
