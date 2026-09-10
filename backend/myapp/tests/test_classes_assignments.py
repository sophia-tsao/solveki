"""Tests for the teacher/student roles, classes, and assignments feature.

Covers role gating, class create/join/roster, assignment authoring and
assign-to-multiple-classes, per-student problem generation, attempt recording,
teacher analytics (accuracy + "most struggled with"), and the SM-2
accuracy->quality integration (applied once when enabled; untouched when off).

The `addition` generator the test topics use is mocked so generated problems are
deterministic, mirroring test_deck.py.
"""
import json
from unittest import mock

from django.test import TestCase, Client

from myapp.models import (
    Settings, Classroom, ClassEnrollment, Assignment, AssignmentTopic,
    AssignmentClass, StudentAssignment, AssignmentAttempt, TopicReview,
    UserTopicSelection,
)
from myapp.views.assignments import _accuracy_to_quality
from .factories import make_user, make_course, make_topic, select


def make_teacher(**kwargs):
    user = make_user(**kwargs)
    settings = Settings.load(user)
    settings.role = Settings.TEACHER
    settings.role_chosen = True
    settings.save()
    return user


class RoleGatingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = make_user()
        self.teacher = make_teacher()

    def test_student_cannot_list_classes(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get("/classes/").status_code, 403)

    def test_teacher_can_list_classes(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get("/classes/").status_code, 200)

    def test_anonymous_is_401(self):
        self.assertEqual(self.client.get("/classes/").status_code, 401)


class SetRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def test_set_role_once(self):
        res = self.client.post(
            "/settings/role/", data=json.dumps({"role": "teacher"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Settings.load(self.user).role, Settings.TEACHER)

    def test_cannot_change_role_after_chosen(self):
        self.client.post(
            "/settings/role/", data=json.dumps({"role": "teacher"}),
            content_type="application/json",
        )
        res = self.client.post(
            "/settings/role/", data=json.dumps({"role": "student"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(Settings.load(self.user).role, Settings.TEACHER)

    def test_invalid_role_rejected(self):
        res = self.client.post(
            "/settings/role/", data=json.dumps({"role": "wizard"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_student_name_saved_and_returned(self):
        res = self.client.post(
            "/settings/role/",
            data=json.dumps({"role": "student", "first_name": "Ada", "last_name": "Lovelace"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "Ada Lovelace")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ada")
        self.assertEqual(self.user.last_name, "Lovelace")


class StudentNameDisplayTests(TestCase):
    """A student's chosen name shows on the roster and their detail page."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()

    def test_name_shows_on_roster_and_detail(self):
        # Student registers with a name.
        self.client.force_login(self.student)
        self.client.post(
            "/settings/role/",
            data=json.dumps({"role": "student", "first_name": "Grace", "last_name": "Hopper"}),
            content_type="application/json",
        )
        # Teacher makes a class the student joins.
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "Period 1"}),
            content_type="application/json",
        ).json()
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )

        self.client.force_login(self.teacher)
        roster = self.client.get(f"/classes/{cls['id']}/students/").json()
        self.assertEqual(roster["students"][0]["name"], "Grace Hopper")

        detail = self.client.get(f"/teacher/students/{self.student.id}/").json()
        self.assertEqual(detail["student"]["name"], "Grace Hopper")
        self.assertIn("upcoming", detail)


class ClassLifecycleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()

    def _create_class(self, name="Period 1"):
        self.client.force_login(self.teacher)
        res = self.client.post(
            "/classes/", data=json.dumps({"name": name}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        return res.json()

    def test_create_join_roster_remove(self):
        cls = self._create_class()
        code = cls["join_code"]

        # Student joins with the code.
        self.client.force_login(self.student)
        join = self.client.post(
            "/classes/join/", data=json.dumps({"code": code}),
            content_type="application/json",
        )
        self.assertEqual(join.status_code, 200)
        self.assertTrue(
            ClassEnrollment.objects.filter(classroom_id=cls["id"], student=self.student).exists()
        )

        # Teacher sees the student on the roster.
        self.client.force_login(self.teacher)
        roster = self.client.get(f"/classes/{cls['id']}/students/").json()
        self.assertEqual(len(roster["students"]), 1)

        # Teacher removes the student.
        rm = self.client.delete(f"/classes/{cls['id']}/students/{self.student.id}/")
        self.assertEqual(rm.status_code, 200)
        self.assertFalse(
            ClassEnrollment.objects.filter(classroom_id=cls["id"], student=self.student).exists()
        )

    def test_join_bad_code_404(self):
        self.client.force_login(self.student)
        res = self.client.post(
            "/classes/join/", data=json.dumps({"code": "ZZZZZZ"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 404)

    def test_teacher_cannot_access_others_class(self):
        cls = self._create_class()
        other = make_teacher()
        self.client.force_login(other)
        self.assertEqual(self.client.get(f"/classes/{cls['id']}/students/").status_code, 403)


class AssignmentAuthoringTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.course = make_course()
        self.topic = make_topic(self.course, generator_name="addition")
        self.client.force_login(self.teacher)
        # Two classes to assign the same assignment to.
        self.class_a = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        self.class_b = self.client.post(
            "/classes/", data=json.dumps({"name": "B"}), content_type="application/json"
        ).json()

    def _create_assignment(self, **overrides):
        body = {
            "title": "Homework 1",
            "mode": "topics",
            "topics": [{"topic_id": self.topic.id, "num_questions": 3}],
        }
        body.update(overrides)
        res = self.client.post(
            "/assignments/", data=json.dumps(body), content_type="application/json"
        )
        self.assertEqual(res.status_code, 201, res.content)
        return res.json()

    def test_create_assignment_with_topics(self):
        a = self._create_assignment()
        self.assertEqual(a["mode"], "topics")
        self.assertEqual(len(a["topics"]), 1)
        self.assertEqual(a["topics"][0]["num_questions"], 3)

    def test_assign_to_multiple_classes(self):
        a = self._create_assignment()
        res = self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [
                {"class_id": self.class_a["id"]},
                {"class_id": self.class_b["id"]},
            ]}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(
            AssignmentClass.objects.filter(assignment_id=a["id"]).count(), 2
        )

    def test_reassign_replaces_links(self):
        a = self._create_assignment()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": self.class_a["id"]}, {"class_id": self.class_b["id"]}]}),
            content_type="application/json",
        )
        # Re-assign to only one class -> the other link is dropped.
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": self.class_a["id"]}]}),
            content_type="application/json",
        )
        links = AssignmentClass.objects.filter(assignment_id=a["id"]).values_list("classroom_id", flat=True)
        self.assertEqual(set(links), {self.class_a["id"]})

    def test_delete_assignment(self):
        a = self._create_assignment()
        res = self.client.delete(f"/assignments/{a['id']}/")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Assignment.objects.filter(id=a["id"]).exists())

    def test_cannot_edit_others_assignment(self):
        a = self._create_assignment()
        other = make_teacher()
        self.client.force_login(other)
        res = self.client.patch(
            f"/assignments/{a['id']}/",
            data=json.dumps({"title": "hijacked"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)


@mock.patch("myapp.views.mathgenerator.addition", return_value=("Q", "4"))
class TakingAssignmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        self.course = make_course()
        self.topic = make_topic(self.course, generator_name="addition")

    def _setup_assignment(self, num_questions=2, sm2_enabled=False):
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        a = self.client.post(
            "/assignments/",
            data=json.dumps({
                "title": "HW", "mode": "topics_sm2" if sm2_enabled else "topics",
                "topics": [{"topic_id": self.topic.id, "num_questions": num_questions}],
            }),
            content_type="application/json",
        ).json()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": cls["id"]}]}),
            content_type="application/json",
        )
        # Student joins.
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        return a, cls

    def test_play_generates_problems_and_marks_in_progress(self, _gen):
        a, _ = self._setup_assignment(num_questions=2)
        res = self.client.get(f"/assignments/{a['id']}/play/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["current_number"], 1)
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual(sa.status, StudentAssignment.IN_PROGRESS)
        self.assertEqual(len(sa.problems), 2)

    def test_unassigned_student_cannot_play(self, _gen):
        a, _ = self._setup_assignment()
        other = make_user()
        self.client.force_login(other)
        self.assertEqual(self.client.get(f"/assignments/{a['id']}/play/").status_code, 403)

    def test_advance_records_attempts_and_completes(self, _gen):
        a, _ = self._setup_assignment(num_questions=2)
        self.client.get(f"/assignments/{a['id']}/play/")
        self.client.post(
            f"/assignments/{a['id']}/advance/",
            data=json.dumps({"outcome": "correct_first", "from_number": 1}),
            content_type="application/json",
        )
        last = self.client.post(
            f"/assignments/{a['id']}/advance/",
            data=json.dumps({"outcome": "incorrect", "from_number": 2}),
            content_type="application/json",
        ).json()
        self.assertTrue(last["completed"])
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual(sa.status, StudentAssignment.COMPLETED)
        self.assertIsNotNone(sa.completed_at)
        self.assertEqual(AssignmentAttempt.objects.filter(student_assignment=sa).count(), 2)

    def test_sm2_disabled_does_not_touch_topic_review(self, _gen):
        a, _ = self._setup_assignment(num_questions=1, sm2_enabled=False)
        self.client.get(f"/assignments/{a['id']}/play/")
        self.client.post(
            f"/assignments/{a['id']}/advance/",
            data=json.dumps({"outcome": "correct_first", "from_number": 1}),
            content_type="application/json",
        )
        self.assertFalse(TopicReview.objects.filter(user=self.student, topic=self.topic).exists())

    def test_sm2_enabled_applies_one_grade(self, _gen):
        a, _ = self._setup_assignment(num_questions=2, sm2_enabled=True)
        self.client.get(f"/assignments/{a['id']}/play/?today=2026-01-15")
        self.client.post(
            f"/assignments/{a['id']}/advance/?today=2026-01-15",
            data=json.dumps({"outcome": "correct_first", "from_number": 1}),
            content_type="application/json",
        )
        self.client.post(
            f"/assignments/{a['id']}/advance/?today=2026-01-15",
            data=json.dumps({"outcome": "correct_first", "from_number": 2}),
            content_type="application/json",
        )
        review = TopicReview.objects.filter(user=self.student, topic=self.topic)
        self.assertEqual(review.count(), 1)


@mock.patch("myapp.views.mathgenerator.addition", return_value=("Q", "4"))
class DeckAssignmentTests(TestCase):
    """Deck-kind assignments: 'all' vs teacher-picked 'topics' scope."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        self.course = make_course()
        self.picked = make_topic(self.course, topic_name="Picked", generator_name="addition")
        self.other = make_topic(self.course, topic_name="Other", generator_name="addition")
        # The student has both topics selected; scope decides which the deck draws.
        select(self.student, self.picked)
        select(self.student, self.other)

    def _deck_assignment(self, scope, topics=None, size=6):
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        body = {"title": "Deck HW", "mode": "deck", "deck_scope": scope, "deck_size": size}
        if topics is not None:
            body["topics"] = [{"topic_id": t.id, "num_questions": 1} for t in topics]
        a = self.client.post(
            "/assignments/", data=json.dumps(body), content_type="application/json"
        ).json()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": cls["id"]}]}),
            content_type="application/json",
        )
        self._last_join_code = cls["join_code"]
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        return a

    def test_topics_scope_draws_only_picked_topics(self, _gen):
        a = self._deck_assignment("topics", topics=[self.picked])
        self.assertEqual(
            AssignmentTopic.objects.filter(assignment_id=a["id"]).count(), 1
        )
        self.client.get(f"/assignments/{a['id']}/play/")
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertTrue(sa.problems)
        self.assertTrue(all(p["topic_id"] == self.picked.id for p in sa.problems))

    def test_all_scope_draws_from_all_selected(self, _gen):
        a = self._deck_assignment("all")
        self.client.get(f"/assignments/{a['id']}/play/")
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        topic_ids = {p["topic_id"] for p in sa.problems}
        self.assertEqual(topic_ids, {self.picked.id, self.other.id})

    def test_picked_topics_included_and_auto_selected_when_not_selected(self, _gen):
        # A teacher picks a topic the student has NOT selected: it must still be
        # included in the deck, and it should become one of the student's own
        # selections (so it carries into daily practice).
        unpicked_course = make_course(course_name="Geometry")
        fresh = make_topic(unpicked_course, topic_name="Fresh", generator_name="addition")
        newbie = make_user()  # no selections at all
        a = self._deck_assignment("topics", topics=[fresh])
        # _deck_assignment logs the default student in; join as the newbie instead.
        self.client.force_login(newbie)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": self._last_join_code}),
            content_type="application/json",
        )
        res = self.client.get(f"/assignments/{a['id']}/play/")
        data = res.json()
        self.assertNotIn("empty", data)
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=newbie)
        self.assertTrue(sa.problems)
        self.assertTrue(all(p["topic_id"] == fresh.id for p in sa.problems))
        self.assertTrue(
            UserTopicSelection.objects.filter(user=newbie, topic=fresh).exists()
        )

    def test_no_selected_topics_reports_empty_without_completing(self, _gen):
        # A student with no selected topics opens a deck assignment: nothing can be
        # generated, so it must report empty rather than persist an instantly
        # "completed" zero-problem instance.
        a = self._deck_assignment("all")
        loner = make_user()
        self.client.force_login(loner)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": self._last_join_code}),
            content_type="application/json",
        )
        res = self.client.get(f"/assignments/{a['id']}/play/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["empty"])
        self.assertEqual(data["reason"], "no_topics_in_scope")
        self.assertNotIn("completed", data)
        self.assertFalse(
            StudentAssignment.objects.filter(assignment_id=a["id"], student=loner).exists()
        )

    def test_empty_instance_recovers_after_selecting_topics(self, _gen):
        # Opening empty (no selections) then selecting a topic and reopening should
        # generate problems, not stay frozen on the completion/empty screen.
        a = self._deck_assignment("all")
        loner = make_user()
        self.client.force_login(loner)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": self._last_join_code}),
            content_type="application/json",
        )
        self.assertTrue(self.client.get(f"/assignments/{a['id']}/play/").json()["empty"])

        select(loner, self.picked)
        res = self.client.get(f"/assignments/{a['id']}/play/")
        data = res.json()
        self.assertNotIn("empty", data)
        self.assertEqual(data["current_number"], 1)
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=loner)
        self.assertTrue(sa.problems)
        self.assertEqual(sa.status, StudentAssignment.IN_PROGRESS)


@mock.patch("myapp.views.mathgenerator.addition", return_value=("Q", "4"))
class AssignmentResultsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.course = make_course()
        self.easy = make_topic(self.course, topic_name="Easy", generator_name="addition")
        self.hard = make_topic(self.course, topic_name="Hard", generator_name="addition")

    def test_results_aggregate_accuracy_and_struggle(self, _gen):
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        a = self.client.post(
            "/assignments/",
            data=json.dumps({
                "title": "HW", "mode": "topics",
                "topics": [
                    {"topic_id": self.easy.id, "num_questions": 1},
                    {"topic_id": self.hard.id, "num_questions": 1},
                ],
            }),
            content_type="application/json",
        ).json()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": cls["id"]}]}),
            content_type="application/json",
        )

        student = make_user()
        self.client.force_login(student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        self.client.get(f"/assignments/{a['id']}/play/")
        # First problem (Easy) correct, second (Hard) incorrect.
        self.client.post(
            f"/assignments/{a['id']}/advance/",
            data=json.dumps({"outcome": "correct_first", "from_number": 1}),
            content_type="application/json",
        )
        self.client.post(
            f"/assignments/{a['id']}/advance/",
            data=json.dumps({"outcome": "incorrect", "from_number": 2}),
            content_type="application/json",
        )

        self.client.force_login(self.teacher)
        results = self.client.get(f"/assignments/{a['id']}/results/").json()
        self.assertEqual(results["average_accuracy"], 0.5)
        self.assertEqual(results["num_submissions"], 1)
        # "Most struggled with" is sorted worst-first: Hard (0.0) before Easy (1.0).
        self.assertEqual(results["topics_struggled"][0]["topic_name"], "Hard")
        self.assertEqual(results["topics_struggled"][0]["accuracy"], 0.0)
        self.assertEqual(results["students"][0]["accuracy"], 0.5)


class AccuracyToQualityTests(TestCase):
    def test_mapping(self):
        self.assertEqual(_accuracy_to_quality(1.0), 5)
        self.assertEqual(_accuracy_to_quality(0.9), 5)
        self.assertEqual(_accuracy_to_quality(0.8), 4)
        self.assertEqual(_accuracy_to_quality(0.7), 3)
        self.assertEqual(_accuracy_to_quality(0.5), 2)
        self.assertEqual(_accuracy_to_quality(0.3), 1)
        self.assertEqual(_accuracy_to_quality(0.0), 1)
