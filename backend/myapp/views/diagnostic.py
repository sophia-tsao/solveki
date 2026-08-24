"""Diagnostic-test endpoints: onboarding "cold start" solver.

Three views back the short diagnostic (two questions + three problems):
  - GET  /diagnostic/config/  the course list, and the Georgia-curriculum units
                              per course for the "which unit" question.
  - POST /diagnostic/start/   three generated problems from the units the student
                              has already learned in their current course.
  - POST /diagnostic/submit/  current course + unit -> selections + SM-2 seed.

The unit taxonomy and seeding rules are pure and live in
``myapp.diagnostic_config``; this module resolves them against the database,
reuses the existing problem generator, and writes the user's selections/schedule.
"""

import datetime
import json
import logging
import random

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import Course, UserTopicSelection, TopicReview
from ..diagnostic_config import (
    aggregate_learned_band,
    category_of_course_name,
    course_sort_key,
    current_unit_topic_names,
    learned_unit_topic_names,
    seed_state_for_band,
    units_for_course,
)
from .common import _require_auth
from .problems import _make_problem_for_topic
from .deck import _regenerate_deck_tail, _client_today

logger = logging.getLogger(__name__)

# The diagnostic is a fixed five questions: two profile questions (current course,
# current unit) then this many calibration problems, all drawn from units the
# student has already learned in their current course.
NUM_CALIBRATION_PROBLEMS = 3


def _prior_course(current_course):
    """The single course the student most likely took the year before, or None.

    "The year before" = the course with the greatest grade level strictly below
    the current course's. Ties (multiple courses at that grade) are broken toward
    the one in the same curriculum track (category), then by curriculum order, so
    e.g. Algebra I picks the grade below it rather than a same-grade elective.
    """
    below = [c for c in Course.objects.all() if c.grade_level < current_course.grade_level]
    if not below:
        return None
    top_grade = max(c.grade_level for c in below)
    candidates = [c for c in below if c.grade_level == top_grade]
    current_category = category_of_course_name(current_course.course_name)
    candidates.sort(
        key=lambda c: (
            category_of_course_name(c.course_name) != current_category,
            course_sort_key(c.course_name, c.grade_level),
        )
    )
    return candidates[0]


def _usable_topics(course):
    """Topics in a course that have a resolvable problem generator."""
    return list(
        course.topics.exclude(generator_name__isnull=True).exclude(generator_name="")
    )


@csrf_exempt
@require_http_methods(["GET"])
def diagnostic_config(request):
    """Course list (for the "current course" dropdown) plus, keyed by course id,
    the ordered Georgia-curriculum units that have at least one usable topic (for
    the "which unit are you learning" dropdown)."""
    auth = _require_auth(request)
    if auth:
        return auth

    courses_qs = sorted(
        Course.objects.all(),
        key=lambda c: course_sort_key(c.course_name, c.grade_level),
    )
    units_by_course = {}
    for course in courses_qs:
        usable = {t.topic_name for t in _usable_topics(course)}
        units = [
            {"key": u["key"], "name": u["name"]}
            for u in units_for_course(course.course_name)
            if any(name in usable for name in u["topics"])
        ]
        units_by_course[course.id] = units

    courses = [
        {"id": c.id, "course_name": c.course_name, "grade_level": c.grade_level}
        for c in courses_qs
    ]
    return JsonResponse({"courses": courses, "units_by_course": units_by_course})


def _learned_topics(course, unit_key):
    """Usable topics of ``course`` in the units up to and including ``unit_key``.

    Ordered by id (curriculum order) so any downstream slicing is deterministic.
    """
    learned_names = learned_unit_topic_names(course.course_name, unit_key)
    topics = [t for t in _usable_topics(course) if t.topic_name in learned_names]
    topics.sort(key=lambda t: t.id)
    return topics


@csrf_exempt
@require_http_methods(["POST"])
def diagnostic_start(request):
    """Generate the calibration problems for the student's current course.

    Problems are drawn only from the units the student has already learned (the
    reported current unit and the units before it), capped at
    NUM_CALIBRATION_PROBLEMS. Ships the solution (matching the deck/problem
    contract: grading is client-side).
    """
    auth = _require_auth(request)
    if auth:
        return auth
    body = json.loads(request.body)
    course_id = body.get("current_course_id")
    unit_key = body.get("current_unit_key")

    problems = []
    course = Course.objects.filter(id=course_id).first() if course_id else None
    if course is not None:
        topics = _learned_topics(course, unit_key)
        random.shuffle(topics)
        for topic in topics:
            if len(problems) >= NUM_CALIBRATION_PROBLEMS:
                break
            made = _make_problem_for_topic(topic)
            if made is None:
                continue
            problems.append({
                "topic_id": made["topic_id"],
                "problem": made["problem"],
                "solution": made["solution"],
            })
    return JsonResponse({"problems": problems})


def _seed_reviews(user, seeds):
    """Create TopicReview rows for the seed plan, never clobbering existing state.

    `seeds` is a list of ``(topic_id, ease, interval, repetitions, due_date)``.
    A topic the user already has a review for (e.g. from a prior diagnostic or
    real practice) is left untouched, so re-running the diagnostic can't erase
    genuine history — it only fills in schedules for newly seeded topics.
    """
    topic_ids = [s[0] for s in seeds]
    existing = set(
        TopicReview.objects.filter(user=user, topic_id__in=topic_ids)
        .values_list("topic_id", flat=True)
    )
    to_create = [
        TopicReview(
            user=user, topic_id=topic_id,
            ease=ease, interval=interval, repetitions=reps, due_date=due,
        )
        for (topic_id, ease, interval, reps, due) in seeds
        if topic_id not in existing
    ]
    TopicReview.objects.bulk_create(to_create, ignore_conflicts=True)


@csrf_exempt
@require_http_methods(["POST"])
def diagnostic_submit(request):
    """Turn the current course + unit + problem results into selections + SM-2 seeds.

    Three seeding bands, matching the dashboard's mastery buckets:
      - Current unit (the one the student is learning now): "new", due today.
      - Earlier learned units of the current course (everything before the current
        unit): one aggregate band from the calibration results — aced them ->
        "familiar", bombed them -> "new", otherwise the default "learning".
      - The prior-year course (one grade below): fully selected as "proficient".
    Units the student hasn't reached yet are left unselected.

    The diagnostic owns the whole selection set: the user's existing selections
    are cleared first, so retaking with different answers resets to a clean slate
    rather than accumulating. SM-2 review *history* is preserved (see
    ``_seed_reviews``), matching manual deselect/reselect. Rebuilds today's deck
    once at the end.
    """
    auth = _require_auth(request)
    if auth:
        return auth
    today = _client_today(request)
    body = json.loads(request.body)
    course_id = body.get("current_course_id")
    unit_key = body.get("current_unit_key")
    results = body.get("results") or []
    user = request.user

    current_course = Course.objects.filter(id=course_id).first() if course_id else None
    selections = []
    seeds = []
    summary = {}  # course_name -> selected topic count

    def _seed(course, topics, band):
        """Select ``topics`` of ``course`` and seed them into SM-2 band ``band``."""
        if not topics:
            return
        ease, interval, reps = seed_state_for_band(band)
        due = today if interval == 0 else today + datetime.timedelta(days=interval)
        for topic in topics:
            selections.append(UserTopicSelection(user=user, topic=topic))
            seeds.append((topic.id, ease, interval, reps, due))
        summary[course.course_name] = summary.get(course.course_name, 0) + len(topics)

    if current_course is not None:
        topics = sorted(_usable_topics(current_course), key=lambda t: t.id)
        learned_names = learned_unit_topic_names(current_course.course_name, unit_key)
        current_names = current_unit_topic_names(current_course.course_name, unit_key)
        # Earlier learned units = everything learned except the current unit.
        earlier_names = learned_names - current_names

        current_topics = [t for t in topics if t.topic_name in current_names]
        earlier_topics = [t for t in topics if t.topic_name in earlier_names]

        # The current unit is freshly being learned: due today, unseen.
        _seed(current_course, current_topics, "new")
        # Earlier units get one aggregate band from how the calibration went.
        outcomes = [r.get("outcome") for r in results if isinstance(r, dict)]
        _seed(current_course, earlier_topics, aggregate_learned_band(outcomes))

        # The prior-year course is assumed mastered: select it all as proficient.
        prior = _prior_course(current_course)
        if prior is not None:
            _seed(prior, sorted(_usable_topics(prior), key=lambda t: t.id), "proficient")

    # Reset to a clean slate so a retake reflects only the new results (any topics
    # selected before — by a prior diagnostic or by hand — are cleared). Review
    # history is left untouched: _seed_reviews skips topics that already have a
    # schedule, so genuine practice progress survives a retake.
    UserTopicSelection.objects.filter(user=user).delete()
    UserTopicSelection.objects.bulk_create(selections, ignore_conflicts=True)
    _seed_reviews(user, seeds)

    # Apply the new selections to today's deck immediately (one batched rebuild
    # rather than the per-toggle rebuild the courses endpoints do).
    _regenerate_deck_tail(user, today)

    selected_count = sum(summary.values())
    logger.info(
        "Diagnostic for user %s selected %d topics across %s",
        user.id, selected_count, sorted(summary),
    )
    return JsonResponse({"selected_count": selected_count, "by_course": summary})
