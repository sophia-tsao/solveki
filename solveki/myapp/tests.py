import json
from django.test import TestCase, Client
from .models import Course, Topic


class ToggleTopicTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(course_name="Algebra", grade_level=8)
        self.topic = Topic.objects.create(topic_name="Linear Equations", course=self.course, is_selected=False)

    def test_select_topic(self):
        response = self.client.patch(
            f"/topics/{self.topic.id}/select",
            data=json.dumps({"is_selected": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_selected"])
        self.topic.refresh_from_db()
        self.assertTrue(self.topic.is_selected)

    def test_deselect_topic(self):
        self.topic.is_selected = True
        self.topic.save()
        response = self.client.patch(
            f"/topics/{self.topic.id}/select",
            data=json.dumps({"is_selected": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.topic.refresh_from_db()
        self.assertFalse(self.topic.is_selected)

    def test_toggle_nonexistent_topic(self):
        response = self.client.patch(
            "/topics/99999/select",
            data=json.dumps({"is_selected": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


class SetCourseTopicsSelectedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(course_name="Geometry", grade_level=9)
        self.t1 = Topic.objects.create(topic_name="Triangles", course=self.course, is_selected=False)
        self.t2 = Topic.objects.create(topic_name="Circles", course=self.course, is_selected=False)

    def test_select_all_course_topics(self):
        response = self.client.patch(
            f"/courses/{self.course.id}/select",
            data=json.dumps({"is_selected": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.t1.refresh_from_db()
        self.t2.refresh_from_db()
        self.assertTrue(self.t1.is_selected)
        self.assertTrue(self.t2.is_selected)

    def test_deselect_all_course_topics(self):
        self.t1.is_selected = True
        self.t1.save()
        self.t2.is_selected = True
        self.t2.save()
        response = self.client.patch(
            f"/courses/{self.course.id}/select",
            data=json.dumps({"is_selected": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.t1.refresh_from_db()
        self.t2.refresh_from_db()
        self.assertFalse(self.t1.is_selected)
        self.assertFalse(self.t2.is_selected)

    def test_set_course_selected_nonexistent_course(self):
        response = self.client.patch(
            "/courses/99999/select",
            data=json.dumps({"is_selected": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


class ViewCourseTopicsIncludesIsSelectedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(course_name="Calculus", grade_level=12)
        self.topic = Topic.objects.create(topic_name="Derivatives", course=self.course, is_selected=True)

    def test_topics_response_includes_is_selected(self):
        response = self.client.get(f"/courses/{self.course.id}/topics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("is_selected", data["topics"][0])
        self.assertTrue(data["topics"][0]["is_selected"])
