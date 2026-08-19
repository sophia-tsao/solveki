import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from ..models import Course, Topic, UserTopicSelection
from .common import _require_auth
from .deck import _regenerate_deck_tail, _client_today

logger = logging.getLogger(__name__)


def _course_selection(course, selected_ids):
    # Read topic ids from the prefetched objects (see view_courses) rather than a
    # fresh .values_list() query: .values_list() ignores the prefetch cache and
    # issues one query per course (an N+1 against the DB), whereas .all() returns
    # the already-in-memory topics, keeping the whole view at 2 queries total.
    #
    # is_selected: every topic selected. is_partial: some but not all selected.
    topic_ids = [topic.id for topic in course.topics.all()]
    selected_count = sum(1 for tid in topic_ids if tid in selected_ids)
    is_selected = bool(topic_ids) and selected_count == len(topic_ids)
    is_partial = selected_count > 0 and not is_selected
    return is_selected, is_partial


def view_courses(request):
    auth = _require_auth(request)
    if auth:
        return auth
    selected_ids = set(
        UserTopicSelection.objects.filter(user=request.user).values_list("topic_id", flat=True)
    )
    courses = []
    for course in Course.objects.all().prefetch_related("topics"):
        is_selected, is_partial = _course_selection(course, selected_ids)
        courses.append({
            "id": course.id,
            "course_name": course.course_name,
            "grade_level": course.grade_level,
            "is_selected": is_selected,
            "is_partial": is_partial,
        })
    return JsonResponse({"courses": courses})


def view_topics(request):
    auth = _require_auth(request)
    if auth:
        return auth
    # Every topic across every course, with this user's selection state. Backs
    # the course-search box, which matches on topic names for courses the user
    # hasn't expanded (and so hasn't lazily loaded topics for) yet.
    selected_ids = set(
        UserTopicSelection.objects.filter(user=request.user).values_list("topic_id", flat=True)
    )
    topics = [
        {
            "id": topic.id,
            "topic_name": topic.topic_name,
            "course_id": topic.course_id,
            "is_selected": topic.id in selected_ids,
        }
        for topic in Topic.objects.order_by("course_id", "id")
    ]
    return JsonResponse({"topics": topics})


def view_course_topics(request, courseID):
    auth = _require_auth(request)
    if auth:
        return auth
    # Returns topics for specific course, with this user's selection state.
    selected_ids = set(
        UserTopicSelection.objects.filter(user=request.user).values_list("topic_id", flat=True)
    )
    topics = []
    for topic in Course.objects.get(id=courseID).topics.all():
        topics.append({
            "id": topic.id,
            "topic_name": topic.topic_name,
            "course_id": topic.course_id,
            "generator_name": topic.generator_name,
            "is_selected": topic.id in selected_ids,
        })
    return JsonResponse({"topics": topics})


@csrf_exempt
@require_http_methods(["PATCH"])
def toggle_topic(request, topicID):
    auth = _require_auth(request)
    if auth:
        return auth
    try:
        topic = Topic.objects.get(id=topicID)
    except Topic.DoesNotExist:
        return JsonResponse({"error": "Topic not found"}, status=404)
    body = json.loads(request.body)
    is_selected = body["is_selected"]
    if is_selected:
        UserTopicSelection.objects.get_or_create(user=request.user, topic=topic)
    else:
        UserTopicSelection.objects.filter(user=request.user, topic=topic).delete()
    logger.info(
        "User %s %s topic %s", request.user.id,
        "selected" if is_selected else "deselected", topic.id,
    )
    # Apply the topic change to today's deck immediately (see helper docstring).
    _regenerate_deck_tail(request.user, _client_today(request))
    return JsonResponse({"id": topic.id, "is_selected": is_selected})


@csrf_exempt
@require_http_methods(["PATCH"])
def set_course_topics_selected(request, courseID):
    auth = _require_auth(request)
    if auth:
        return auth
    try:
        course = Course.objects.get(id=courseID)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)
    body = json.loads(request.body)
    new_value = body["is_selected"]
    topics = course.topics.all()
    if new_value:
        UserTopicSelection.objects.bulk_create(
            [UserTopicSelection(user=request.user, topic=t) for t in topics],
            ignore_conflicts=True,
        )
    else:
        UserTopicSelection.objects.filter(user=request.user, topic__in=topics).delete()
    logger.info(
        "User %s %s all %d topics in course %s", request.user.id,
        "selected" if new_value else "deselected", len(topics), courseID,
    )
    # Apply the topic change to today's deck immediately (see helper docstring).
    _regenerate_deck_tail(request.user, _client_today(request))
    return JsonResponse({"course_id": courseID, "is_selected": new_value})
