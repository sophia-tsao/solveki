"""Small helpers for building test fixtures.

Kept dependency-free (no factory_boy): the models are simple enough that plain
helper functions read clearly and avoid another dev dependency.
"""
from django.contrib.auth import get_user_model

from myapp.models import Course, Topic, UserTopicSelection

User = get_user_model()

_user_seq = 0


def make_user(**kwargs):
    """Create a user with a unique username. Extra kwargs override defaults."""
    global _user_seq
    _user_seq += 1
    defaults = {
        "username": f"user{_user_seq}",
        "email": f"user{_user_seq}@example.com",
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_course(course_name="Algebra", grade_level=8):
    return Course.objects.create(course_name=course_name, grade_level=grade_level)


def make_topic(course, topic_name="Linear Equations", generator_name="addition"):
    return Topic.objects.create(
        topic_name=topic_name, course=course, generator_name=generator_name
    )


def select(user, topic):
    """Record that `user` has selected `topic`."""
    return UserTopicSelection.objects.create(user=user, topic=topic)
