"""Tests for course/topic listing and per-user topic selection."""
import json

from django.test import TestCase, Client

from myapp.models import UserTopicSelection
from .factories import make_user, make_course, make_topic, select


class ViewCoursesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.course = make_course()
        self.t1 = make_topic(self.course, topic_name="Linear")
        self.t2 = make_topic(self.course, topic_name="Quadratic")

    def test_course_selected_only_when_all_topics_selected(self):
        select(self.user, self.t1)
        courses = self.client.get("/courses/").json()["courses"]
        self.assertFalse(courses[0]["is_selected"])

        select(self.user, self.t2)
        courses = self.client.get("/courses/").json()["courses"]
        self.assertTrue(courses[0]["is_selected"])

    def test_course_with_no_topics_is_not_selected(self):
        empty = make_course(course_name="Empty", grade_level=5)
        courses = {c["id"]: c for c in self.client.get("/courses/").json()["courses"]}
        self.assertFalse(courses[empty.id]["is_selected"])


class ViewCourseTopicsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.course = make_course()
        self.topic = make_topic(self.course, topic_name="Derivatives")

    def test_topics_include_selection_state(self):
        select(self.user, self.topic)
        data = self.client.get(f"/courses/{self.course.id}/topics").json()
        self.assertIn("is_selected", data["topics"][0])
        self.assertTrue(data["topics"][0]["is_selected"])

    def test_selection_is_per_user(self):
        other = make_user()
        select(other, self.topic)
        # Current user has not selected it, so it reads as unselected.
        data = self.client.get(f"/courses/{self.course.id}/topics").json()
        self.assertFalse(data["topics"][0]["is_selected"])


class ToggleTopicTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.course = make_course()
        self.topic = make_topic(self.course)

    def _toggle(self, topic_id, is_selected):
        return self.client.patch(
            f"/topics/{topic_id}/select",
            data=json.dumps({"is_selected": is_selected}),
            content_type="application/json",
        )

    def test_select_topic(self):
        response = self._toggle(self.topic.id, True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_selected"])
        self.assertTrue(
            UserTopicSelection.objects.filter(user=self.user, topic=self.topic).exists()
        )

    def test_select_is_idempotent(self):
        self._toggle(self.topic.id, True)
        self._toggle(self.topic.id, True)
        self.assertEqual(
            UserTopicSelection.objects.filter(user=self.user, topic=self.topic).count(), 1
        )

    def test_deselect_topic(self):
        select(self.user, self.topic)
        response = self._toggle(self.topic.id, False)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            UserTopicSelection.objects.filter(user=self.user, topic=self.topic).exists()
        )

    def test_toggle_nonexistent_topic(self):
        response = self._toggle(99999, True)
        self.assertEqual(response.status_code, 404)


class SetCourseTopicsSelectedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.course = make_course(course_name="Geometry", grade_level=9)
        self.t1 = make_topic(self.course, topic_name="Triangles")
        self.t2 = make_topic(self.course, topic_name="Circles")

    def _set(self, course_id, is_selected):
        return self.client.patch(
            f"/courses/{course_id}/select",
            data=json.dumps({"is_selected": is_selected}),
            content_type="application/json",
        )

    def test_select_all(self):
        response = self._set(self.course.id, True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserTopicSelection.objects.filter(user=self.user).count(), 2
        )

    def test_select_all_is_idempotent(self):
        select(self.user, self.t1)
        response = self._set(self.course.id, True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserTopicSelection.objects.filter(user=self.user).count(), 2
        )

    def test_deselect_all(self):
        select(self.user, self.t1)
        select(self.user, self.t2)
        response = self._set(self.course.id, False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserTopicSelection.objects.filter(user=self.user).count(), 0
        )

    def test_nonexistent_course(self):
        response = self._set(99999, True)
        self.assertEqual(response.status_code, 404)
