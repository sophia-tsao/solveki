"""Tests for the teacher/student roles, classes, and assignments feature.

Covers role gating, class create/join/roster, assignment authoring and
assign-to-multiple-classes, and the simplified student flow: opening an
assignment adds its topics to the student's selections, grows today's practice
deck to the teacher's card count, and sends the student to normal practice.
Progress is read from the student's SM-2 state, so the teacher report and the
student's to-do/done split are proficiency/practiced based, not quiz scores.

The `addition` generator the test topics use is mocked so deck generation is
deterministic, mirroring test_deck.py.
"""
import json
from unittest import mock

from django.test import TestCase, Client
from django.utils import timezone

from myapp.models import (
    Settings, Classroom, ClassEnrollment, Assignment, AssignmentTopic,
    AssignmentClass, StudentAssignment, TopicReview, DailyTopicGrade,
    UserTopicSelection, DailyDeck,
)
from .factories import make_user, make_course, make_topic, select


def make_teacher(**kwargs):
    user = make_user(**kwargs)
    settings = Settings.load(user)
    settings.role = Settings.TEACHER
    settings.role_chosen = True
    settings.save()
    return user


def mark_practiced(user, topic, interval=10, quality=5):
    """Simulate the student having practiced `topic`: an SM-2 review + a graded day.

    The report reads practice from `DailyTopicGrade` and proficiency from
    `TopicReview.interval`, so seeding both mirrors what real practice would
    leave behind without stepping through the deck.
    """
    TopicReview.objects.update_or_create(
        user=user, topic=topic,
        defaults={"interval": interval, "repetitions": 1, "ease": 2.5},
    )
    DailyTopicGrade.objects.update_or_create(
        user=user, topic=topic, date=timezone.localdate(),
        defaults={
            "applied_quality": quality, "snapshot_ease": 2.5,
            "snapshot_interval": 0, "snapshot_repetitions": 0,
        },
    )


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
            "topics": [{"topic_id": self.topic.id}],
        }
        body.update(overrides)
        res = self.client.post(
            "/assignments/", data=json.dumps(body), content_type="application/json"
        )
        self.assertEqual(res.status_code, 201, res.content)
        return res.json()

    def test_create_assignment_with_topics(self):
        a = self._create_assignment(deck_size=15)
        self.assertEqual(a["deck_size"], 15)
        self.assertEqual(len(a["topics"]), 1)
        self.assertEqual(a["topics"][0]["topic_id"], self.topic.id)

    def test_deck_size_defaults(self):
        a = self._create_assignment()
        self.assertEqual(a["deck_size"], 10)

    def test_title_required(self):
        res = self.client.post(
            "/assignments/", data=json.dumps({"topics": [{"topic_id": self.topic.id}]}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

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

    def test_edit_topics_replaces_set(self):
        other = make_topic(self.course, topic_name="Other", generator_name="addition")
        a = self._create_assignment()
        res = self.client.patch(
            f"/assignments/{a['id']}/",
            data=json.dumps({"topics": [{"topic_id": other.id}]}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        topic_ids = set(
            AssignmentTopic.objects.filter(assignment_id=a["id"]).values_list("topic_id", flat=True)
        )
        self.assertEqual(topic_ids, {other.id})

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
class StartAssignmentTests(TestCase):
    """Opening an assignment adds its topics, grows the deck, and routes to practice."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        self.course = make_course()
        self.picked = make_topic(self.course, topic_name="Picked", generator_name="addition")

    def _setup_assignment(self, deck_size=6, topics=None):
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        a = self.client.post(
            "/assignments/",
            data=json.dumps({
                "title": "HW", "deck_size": deck_size,
                "topics": [{"topic_id": t.id} for t in (topics or [self.picked])],
            }),
            content_type="application/json",
        ).json()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": cls["id"]}]}),
            content_type="application/json",
        )
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        return a, cls

    def test_start_selects_topics_grows_deck_and_routes(self, _gen):
        # Pin the student's daily size below the assignment's card count so the
        # grow (never shrink) is actually exercised.
        settings = Settings.load(self.student)
        settings.questions_per_day = 5
        settings.save(update_fields=["questions_per_day"])

        a, _ = self._setup_assignment(deck_size=8)
        res = self.client.post(f"/assignments/{a['id']}/play/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["goto"], "practice")
        self.assertEqual(data["deck_size"], 8)
        # The picked topic is now one of the student's own selections.
        self.assertTrue(
            UserTopicSelection.objects.filter(user=self.student, topic=self.picked).exists()
        )
        # Today's deck grew to the teacher's card count.
        deck = DailyDeck.objects.get(user=self.student)
        self.assertEqual(len(deck.problems), 8)
        # A lightweight opened marker is recorded.
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual(sa.status, StudentAssignment.IN_PROGRESS)

    def test_unassigned_student_cannot_start(self, _gen):
        a, _ = self._setup_assignment()
        other = make_user()
        self.client.force_login(other)
        self.assertEqual(
            self.client.post(f"/assignments/{a['id']}/play/").status_code, 403
        )


class AssignmentResultsTests(TestCase):
    """The proficiency report: who practiced, band mix on the assigned topics."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.course = make_course()
        self.easy = make_topic(self.course, topic_name="Easy", generator_name="addition")
        self.hard = make_topic(self.course, topic_name="Hard", generator_name="addition")

    def _assign_to_student(self, student, due_at=None):
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        a = self.client.post(
            "/assignments/",
            data=json.dumps({
                "title": "HW",
                "topics": [{"topic_id": self.easy.id}, {"topic_id": self.hard.id}],
            }),
            content_type="application/json",
        ).json()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": cls["id"], "due_at": due_at}]}),
            content_type="application/json",
        )
        self.client.force_login(student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        return a

    def test_report_counts_bands_and_practice(self):
        student = make_user()
        a = self._assign_to_student(student)
        # Practiced Easy (interval 10 -> familiar); never practiced Hard (-> new).
        mark_practiced(student, self.easy, interval=10)

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        self.assertEqual(res["num_students"], 1)
        self.assertEqual(res["num_practiced"], 1)
        self.assertEqual(res["band_totals"]["familiar"], 1)
        self.assertEqual(res["band_totals"]["new"], 1)
        row = res["students"][0]
        self.assertTrue(row["practiced"])
        self.assertEqual(row["proficiency"]["familiar"], 1)
        self.assertEqual(row["proficiency"]["new"], 1)

    def test_overdue_when_unpracticed_past_due(self):
        student = make_user()
        past = (timezone.now() - timezone.timedelta(days=1)).isoformat()
        a = self._assign_to_student(student, due_at=past)

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        row = res["students"][0]
        self.assertFalse(row["practiced"])
        self.assertTrue(row["overdue"])


class MyAssignmentsTests(TestCase):
    """A student's to-do / done split, driven by whether topics were practiced."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        self.course = make_course()
        self.topic = make_topic(self.course, generator_name="addition")

    def _assign(self):
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        a = self.client.post(
            "/assignments/",
            data=json.dumps({"title": "HW", "topics": [{"topic_id": self.topic.id}]}),
            content_type="application/json",
        ).json()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": cls["id"]}]}),
            content_type="application/json",
        )
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        return a

    def test_unpracticed_is_upcoming_then_moves_to_done(self):
        a = self._assign()
        data = self.client.get("/assignments/mine/").json()
        self.assertEqual(len(data["upcoming"]), 1)
        self.assertEqual(len(data["completed"]), 0)
        self.assertEqual(data["upcoming"][0]["num_topics"], 1)

        # Practicing the only topic moves it to done.
        mark_practiced(self.student, self.topic)
        data = self.client.get("/assignments/mine/").json()
        self.assertEqual(len(data["upcoming"]), 0)
        self.assertEqual(len(data["completed"]), 1)
