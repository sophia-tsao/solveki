"""Tests that topic "Learn more" links can be changed from the Django admin."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from myapp.models import Topic
from .factories import make_course, make_topic


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
