import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ..models import Topic, Settings, TopicReview
from .common import _require_auth
from .deck import _client_today, _effective_due_dates, _ordered_topics
from .. import srs

logger = logging.getLogger(__name__)


def _topic_stats(topic, review, due_date):
    """Serialize one topic's SM-2 state for the dashboard.

    A topic never reviewed has no `TopicReview` row, so its stats fall back to
    the SM-2 starting state (see `myapp.srs`): ease 2.5, and interval/repetitions
    0. `due_date` is the effective due date (today for never-practiced topics),
    already resolved by the caller via `_effective_due_dates`.
    """
    if review is None:
        ease = srs.INITIAL_EASE
        interval = 0
        repetitions = 0
    else:
        ease = review.ease
        interval = review.interval
        repetitions = review.repetitions
    return {
        "id": topic.id,
        "topic_name": topic.topic_name,
        "course_name": topic.course.course_name if topic.course else None,
        "repetitions": repetitions,
        "ease": round(ease, 2),
        "interval": interval,
        "due_date": due_date.isoformat(),
    }


@require_http_methods(["GET"])
def view_dashboard(request):
    """Spaced-repetition dashboard: the user's selected topics and what's next.

    Returns two views over the same SM-2 state, both with each topic's
    repetitions / ease / interval:

    - ``selected``: every topic the user has selected (usable or not), ordered
      by effective due date so the most-due sit at the top.
    - ``upcoming``: the topics that will make up the next practice deck — the
      selected, *usable* topics in the exact due order the deck draws from
      (`_ordered_topics`), sliced to `questions_per_day`. This is "what will be
      shown soon".
    """
    auth = _require_auth(request)
    if auth:
        return auth

    today = _client_today(request)

    selected_topics = list(
        Topic.objects.filter(selections__user=request.user)
        .select_related("course")
        .distinct()
    )
    due = _effective_due_dates(request.user, selected_topics, today)
    reviews = {
        r.topic_id: r
        for r in TopicReview.objects.filter(user=request.user, topic__in=selected_topics)
    }
    selected_topics.sort(key=lambda t: (due[t.id], t.id))
    selected = [
        _topic_stats(t, reviews.get(t.id), due[t.id]) for t in selected_topics
    ]

    # "Shown soon" is the head of the deck's own draw order, so the dashboard
    # agrees with what the practice page will actually serve.
    limit = Settings.load(request.user).questions_per_day
    ordered = _ordered_topics(request.user, today)[:limit]
    up_due = _effective_due_dates(request.user, ordered, today)
    up_reviews = {
        r.topic_id: r
        for r in TopicReview.objects.filter(user=request.user, topic__in=ordered)
    }
    upcoming = [
        _topic_stats(t, up_reviews.get(t.id), up_due[t.id]) for t in ordered
    ]

    return JsonResponse({"selected": selected, "upcoming": upcoming})
