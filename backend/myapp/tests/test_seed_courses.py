"""Tests for the seed_courses management command.

seed_courses creates Course rows and links each already-seeded Topic to its
course by matching on topic_name. That match is a silent contract: if a name in
seed_courses' CURRICULUM drifts from the name seed_topics writes, the topic is
simply never linked (it lands in the command's "not found" list) and disappears
from every course listing. The contract test below catches that drift the moment
it ships; the behaviour tests exercise the command's create/link/idempotency
logic against the real models.
"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from myapp.management.commands.seed_courses import CURRICULUM
from myapp.management.commands.seed_topics import TOPICS
from myapp.models import Course, Topic


class CurriculumContractTests(TestCase):
    def test_every_curriculum_topic_is_seeded_by_seed_topics(self):
        # A course topic name that seed_topics never creates would be silently
        # dropped by seed_courses, so guard the two lists against drifting apart.
        seeded_names = {name for name, _generator in TOPICS}
        curriculum_names = {
            name for _course, _grade, names in CURRICULUM for name in names
        }
        orphaned = sorted(curriculum_names - seeded_names)
        self.assertEqual(orphaned, [], f"Curriculum topics not seeded: {orphaned}")

    def test_curriculum_has_no_duplicate_topic_names(self):
        # A topic listed under two grades would be linked to whichever course
        # seed_courses processed last, quietly moving it off the earlier one.
        all_names = [name for _c, _g, names in CURRICULUM for name in names]
        duplicates = sorted({n for n in all_names if all_names.count(n) > 1})
        self.assertEqual(duplicates, [], f"Duplicate curriculum topics: {duplicates}")

    def test_curriculum_course_names_are_unique(self):
        course_names = [name for name, _grade, _topics in CURRICULUM]
        self.assertEqual(len(course_names), len(set(course_names)))


class SeedCoursesBehaviourTests(TestCase):
    def _run(self):
        out = StringIO()
        call_command("seed_courses", stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_seeding_after_topics_creates_courses_and_links_every_topic(self):
        call_command("seed_topics", stdout=StringIO())
        output = self._run()

        self.assertEqual(Course.objects.count(), len(CURRICULUM))
        # With topics seeded first, nothing should be reported as missing.
        self.assertNotIn("Topics not found", output)
        # Every topic named in the curriculum is now attached to a course.
        linked = Topic.objects.filter(course__isnull=False).count()
        expected = sum(len(names) for _c, _g, names in CURRICULUM)
        self.assertEqual(linked, expected)

    def test_links_topic_to_the_course_for_its_grade(self):
        call_command("seed_topics", stdout=StringIO())
        self._run()

        grade1 = Course.objects.get(course_name="Grade 1")
        topic = Topic.objects.get(topic_name="Addition of two numbers")
        self.assertEqual(topic.course_id, grade1.id)
        self.assertEqual(grade1.grade_level, 1)

    def test_missing_topics_are_reported_not_fatal(self):
        # Run seed_courses with no topics seeded: it must not raise, and it must
        # surface the names it could not link rather than failing silently.
        output = self._run()
        self.assertEqual(Course.objects.count(), len(CURRICULUM))
        self.assertIn("Topics not found", output)
        self.assertFalse(Topic.objects.exclude(course__isnull=True).exists())

    def test_is_idempotent(self):
        call_command("seed_topics", stdout=StringIO())
        self._run()
        self._run()
        # Re-running must not duplicate courses (get_or_create keyed on name).
        self.assertEqual(Course.objects.count(), len(CURRICULUM))
        self.assertEqual(
            Course.objects.filter(course_name="Grade 1").count(), 1
        )
