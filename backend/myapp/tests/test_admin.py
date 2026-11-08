"""Django admin tests: editable topic "Learn more" links and the problem-report views."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

import datetime

from myapp.models import Topic, ProblemReport
from .factories import make_course, make_topic, make_user


# Admin pages reference static files; the production manifest storage needs
# `collectstatic` to have run (the Dockerfile does it, CI doesn't), so serve
# them unhashed here.
@override_settings(STORAGES={
    **settings.STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class TopicAdminLearnMoreTests(TestCase):
    def setUp(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="pw"
        )
        self.client.force_login(admin_user)
        self.topic = make_topic(make_course())
        self.change_url = f"/admin/myapp/topic/{self.topic.id}/change/"

    def post_link(self, url):
        return self.client.post(self.change_url, {
            "topic_name": self.topic.topic_name,
            "course": self.topic.course_id,
            "generator_name": self.topic.generator_name,
            "learn_more_url": url,
        })

    def test_link_is_editable_in_the_topic_list(self):
        response = self.client.get("/admin/myapp/topic/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="form-0-learn_more_url"')

    def test_link_can_be_changed_from_the_change_form(self):
        response = self.post_link("https://www.khanacademy.org/math/new-lesson")
        self.assertEqual(response.status_code, 302)
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.learn_more_url, "https://www.khanacademy.org/math/new-lesson")

    def test_invalid_link_is_rejected(self):
        response = self.post_link("not a url")
        self.assertEqual(response.status_code, 200)  # form redisplayed with an error
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.learn_more_url, "")

    def test_link_can_be_cleared(self):
        Topic.objects.filter(id=self.topic.id).update(learn_more_url="https://example.com/x")
        self.post_link("")
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.learn_more_url, "")


@override_settings(STORAGES={
    **settings.STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class ProblemReportAdminTests(TestCase):
    def setUp(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="pw"
        )
        self.client.force_login(admin_user)
        self.topic = make_topic(make_course(), topic_name="Adding fractions")
        self.report = ProblemReport.objects.create(
            user=make_user(), topic=self.topic, reason=ProblemReport.OTHER,
            details="Typo in the question", problem="$1/2+1/4=$", solution="3/4",
            user_answer="0.75", date=datetime.date(2026, 7, 21),
        )

    def test_list_shows_reason_topic_and_resolved_toggle(self):
        response = self.client.get("/admin/myapp/problemreport/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adding fractions")
        self.assertContains(response, 'name="form-0-resolved"')

    def test_list_shows_problem_solution_and_student_answer(self):
        response = self.client.get("/admin/myapp/problemreport/")
        for heading in ("Problem", "Solveki&#x27;s solution", "Student&#x27;s answer"):
            self.assertContains(response, heading)
        # Math delimiters are stripped for readability.
        self.assertContains(response, "1/2+1/4=")
        self.assertNotContains(response, "$1/2+1/4=$")
        self.assertContains(response, "3/4")
        self.assertContains(response, "0.75")

    def test_change_page_shows_report_and_can_mark_resolved(self):
        url = f"/admin/myapp/problemreport/{self.report.id}/change/"
        response = self.client.get(url)
        self.assertContains(response, "Typo in the question")
        self.assertContains(response, "1/2+1/4=")
        self.assertContains(response, "3/4")
        self.assertContains(response, "0.75")
        self.client.post(url, {"resolved": "on"})
        self.report.refresh_from_db()
        self.assertTrue(self.report.resolved)
        self.assertEqual(self.report.details, "Typo in the question")  # read-only

    def test_change_page_lists_the_steps_shown(self):
        self.report.steps = [
            {"text": "Rewrite $1/2$ as $2/4$.", "math": "2/4+1/4"},
            {"text": "Add the numerators.", "math": None},
        ]
        self.report.save()
        response = self.client.get(f"/admin/myapp/problemreport/{self.report.id}/change/")
        self.assertContains(response, "Steps shown")
        self.assertContains(response, "1. Rewrite 1/2 as 2/4.  [2/4+1/4]")
        self.assertContains(response, "2. Add the numerators.")

    def test_reports_cannot_be_added_by_hand(self):
        response = self.client.get("/admin/myapp/problemreport/add/")
        self.assertEqual(response.status_code, 403)
