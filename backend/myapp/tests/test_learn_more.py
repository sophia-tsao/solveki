"""Tests for the default "Learn more" video links seeded into topics.

LEARN_MORE_VIDEOS is keyed by generator_name, which is a silent contract with
seed_topics: a seeded topic missing from the map is seeded with no "Learn more"
link, and a stale key (a renamed generator) points nowhere. The contract tests
catch both the moment they ship.
"""
import re

from django.test import SimpleTestCase

from myapp.learn_more import LEARN_MORE_VIDEOS, default_learn_more_url
from myapp.management.commands.seed_topics import TOPICS

YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class DefaultLearnMoreUrlTests(SimpleTestCase):
    def test_mapped_generator_defaults_to_its_youtube_video(self):
        video_id = LEARN_MORE_VIDEOS["addition"]
        self.assertEqual(
            default_learn_more_url("addition"), f"https://www.youtube.com/watch?v={video_id}"
        )

    def test_unmapped_generator_has_no_default(self):
        self.assertEqual(default_learn_more_url("not_a_real_generator"), "")

    def test_missing_generator_has_no_default(self):
        self.assertEqual(default_learn_more_url(None), "")
        self.assertEqual(default_learn_more_url(""), "")


class LearnMoreContractTests(SimpleTestCase):
    def test_every_seeded_topic_has_a_video(self):
        seeded = {generator for _name, generator in TOPICS}
        missing = sorted(seeded - LEARN_MORE_VIDEOS.keys())
        self.assertEqual(missing, [], f"Seeded topics with no Learn more video: {missing}")

    def test_no_video_is_keyed_by_an_unknown_generator(self):
        seeded = {generator for _name, generator in TOPICS}
        stale = sorted(LEARN_MORE_VIDEOS.keys() - seeded)
        self.assertEqual(stale, [], f"Learn more videos for unknown generators: {stale}")

    def test_every_video_id_is_a_well_formed_youtube_id(self):
        malformed = {g: v for g, v in LEARN_MORE_VIDEOS.items() if not YOUTUBE_ID.match(v)}
        self.assertEqual(malformed, {})
