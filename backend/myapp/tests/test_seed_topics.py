"""Tests for the seed_topics management command and the link data migration.

seed_topics owns each topic's generator (kept in sync on every run) but not its
"Learn more" link, which admins edit: the seed fills a blank link with the
curated default and must never overwrite a link someone chose.
"""
import importlib
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from myapp.learn_more import default_learn_more_url
from myapp.management.commands.seed_topics import TOPICS
from myapp.models import Topic

NAME, GENERATOR = TOPICS[0]
CUSTOM_URL = "https://www.khanacademy.org/math/custom"


def seed():
    out = StringIO()
    call_command("seed_topics", stdout=out)
    return out.getvalue()


class SeedTopicsLearnMoreTests(TestCase):
    def test_new_topics_get_their_default_link(self):
        seed()
        topic = Topic.objects.get(topic_name=NAME)
        self.assertEqual(topic.learn_more_url, default_learn_more_url(GENERATOR))
        self.assertFalse(Topic.objects.filter(learn_more_url="").exists())

    def test_existing_topic_with_blank_link_is_filled(self):
        Topic.objects.create(topic_name=NAME, generator_name=GENERATOR)
        seed()
        self.assertEqual(
            Topic.objects.get(topic_name=NAME).learn_more_url,
            default_learn_more_url(GENERATOR),
        )

    def test_admin_chosen_link_survives_reseeding(self):
        seed()
        Topic.objects.filter(topic_name=NAME).update(learn_more_url=CUSTOM_URL)
        seed()
        self.assertEqual(Topic.objects.get(topic_name=NAME).learn_more_url, CUSTOM_URL)

    def test_generator_is_still_synced_without_touching_the_link(self):
        Topic.objects.create(
            topic_name=NAME, generator_name="stale_generator", learn_more_url=CUSTOM_URL
        )
        seed()
        topic = Topic.objects.get(topic_name=NAME)
        self.assertEqual(topic.generator_name, GENERATOR)
        self.assertEqual(topic.learn_more_url, CUSTOM_URL)

    def test_is_idempotent(self):
        seed()
        self.assertIn("0 topic(s) created, 0 topic(s) updated", seed())


class FillLearnMoreMigrationTests(TestCase):
    """The 0019 data migration fills links on databases seeded before the field existed."""

    def setUp(self):
        self.migration = importlib.import_module(
            "myapp.migrations.0019_fill_topic_learn_more_url"
        )

    def test_fills_blank_links_and_keeps_existing_ones(self):
        blank = Topic.objects.create(topic_name="Blank", generator_name="addition")
        chosen = Topic.objects.create(
            topic_name="Chosen", generator_name="addition", learn_more_url=CUSTOM_URL
        )
        unknown = Topic.objects.create(topic_name="Unknown", generator_name="not_a_generator")

        self.migration.fill_learn_more_urls(apps, None)

        for topic in (blank, chosen, unknown):
            topic.refresh_from_db()
        self.assertEqual(
            blank.learn_more_url,
            f"https://www.youtube.com/watch?v={self.migration.VIDEOS['addition']}",
        )
        self.assertEqual(chosen.learn_more_url, CUSTOM_URL)
        self.assertEqual(unknown.learn_more_url, "")

    def test_frozen_videos_cover_every_seeded_topic(self):
        seeded = {generator for _name, generator in TOPICS}
        self.assertEqual(sorted(seeded - self.migration.VIDEOS.keys()), [])
