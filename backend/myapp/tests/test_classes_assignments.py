"""Tests for the teacher/student roles, classes, and assignments feature.

Covers role gating, class create/join/roster, assignment authoring and
assign-to-multiple-classes, and the simplified student flow: assigning an
assignment to a class (or joining a class that has one) adds its topics to the
student's selections and stretches today's practice deck to fit the teacher's
card count; opening it just sends the student to normal practice. An assignment
is done once the student has answered its card count (any topic) since it
reached them; the teacher report adds familiarity on the assignment's topics
from the student's SM-2 state.

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
    UserTopicSelection, DailyDeck, AnswerRecord, DailyPractice,
)
from .factories import make_user, make_course, make_topic, select


def make_teacher(**kwargs):
    user = make_user(**kwargs)
    settings = Settings.load(user)
    settings.role = Settings.TEACHER
    settings.role_chosen = True
    settings.save()
    return user


def log_answers(user, topic, *outcomes, seconds=30, date=None):
    """Record answered cards for `user` on `topic`, one per outcome."""
    for outcome in outcomes:
        AnswerRecord.objects.create(
            user=user, topic=topic, date=date or timezone.localdate(),
            outcome=outcome, seconds=seconds,
        )


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
    """Assigning adds topics and starts the count; opening grows the deck and routes."""

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
        # The deck view shows all 8, not just the student's daily 5.
        self.assertEqual(self.client.get("/deck/").json()["total"], 8)
        # The opened assignment is in progress with no cards counted yet.
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual(sa.status, StudentAssignment.IN_PROGRESS)
        self.assertEqual(sa.cards_answered, 0)

    def test_answering_card_count_completes_assignment(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 2
        settings.save(update_fields=["questions_per_day"])

        a, _ = self._setup_assignment(deck_size=3)
        self.client.post(f"/assignments/{a['id']}/play/")
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        for n in range(1, 3):
            data = self.client.post("/deck/advance/").json()
            self.assertEqual(data["total"], 3)
            sa.refresh_from_db()
            self.assertEqual(sa.cards_answered, n)
            self.assertEqual(sa.status, StudentAssignment.IN_PROGRESS)

        data = self.client.post("/deck/advance/").json()
        self.assertEqual(data, {"completed": True, "total": 3})
        sa.refresh_from_db()
        self.assertEqual(sa.cards_answered, 3)
        self.assertEqual(sa.status, StudentAssignment.COMPLETED)
        self.assertIsNotNone(sa.completed_at)
        mine = self.client.get("/assignments/mine/").json()
        self.assertEqual([r["status"] for r in mine["completed"]], ["done"])

    def _class_with_student(self):
        """A teacher's class the student has joined, with nothing assigned yet."""
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        return cls

    def _assign(self, assignment, cls):
        self.client.force_login(self.teacher)
        self.client.post(
            f"/assignments/{assignment['id']}/assign/",
            data=json.dumps({"classes": [{"class_id": cls["id"]}]}),
            content_type="application/json",
        )
        self.client.force_login(self.student)

    def _create_and_assign(self, cls, deck_size=3):
        self.client.force_login(self.teacher)
        a = self.client.post(
            "/assignments/",
            data=json.dumps({
                "title": "HW", "deck_size": deck_size,
                "topics": [{"topic_id": self.picked.id}],
            }),
            content_type="application/json",
        ).json()
        self._assign(a, cls)
        return a

    def test_assigning_adds_topics_to_enrolled_students(self, _gen):
        cls = self._class_with_student()
        a = self._create_and_assign(cls)
        # Without the student opening anything, the topic is selected and the
        # assignment is already counting.
        self.assertTrue(
            UserTopicSelection.objects.filter(user=self.student, topic=self.picked).exists()
        )
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual((sa.status, sa.cards_answered), (StudentAssignment.IN_PROGRESS, 0))
        self.assertIsNotNone(sa.started_at)

    def test_joining_later_adds_topics(self, _gen):
        # _setup_assignment assigns first, then the student joins.
        a, _ = self._setup_assignment()
        self.assertTrue(
            UserTopicSelection.objects.filter(user=self.student, topic=self.picked).exists()
        )
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual(sa.status, StudentAssignment.IN_PROGRESS)

    def test_assigning_flags_existing_deck_for_rebuild(self, _gen):
        cls = self._class_with_student()
        own = make_topic(self.course, topic_name="Own", generator_name="addition")
        select(self.student, own)
        self.client.get("/deck/")
        self._create_and_assign(cls)
        # Today's deck is rebuilt with the new topic on the next practice load.
        self.assertTrue(DailyDeck.objects.get(user=self.student).needs_regen)
        self.client.get("/deck/")
        self.assertFalse(DailyDeck.objects.get(user=self.student).needs_regen)

    def test_editing_topics_reaches_assigned_students(self, _gen):
        cls = self._class_with_student()
        a = self._create_and_assign(cls)
        extra = make_topic(self.course, topic_name="Extra", generator_name="addition")
        self.client.force_login(self.teacher)
        self.client.patch(
            f"/assignments/{a['id']}/",
            data=json.dumps({"topics": [{"topic_id": self.picked.id}, {"topic_id": extra.id}]}),
            content_type="application/json",
        )
        self.assertTrue(
            UserTopicSelection.objects.filter(user=self.student, topic=extra).exists()
        )

    def test_reassigning_keeps_progress(self, _gen):
        cls = self._class_with_student()
        a = self._create_and_assign(cls)
        self.client.get("/deck/")
        self.client.post("/deck/advance/")
        self._assign(a, cls)
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual((sa.status, sa.cards_answered), (StudentAssignment.IN_PROGRESS, 1))

    def test_cards_answered_before_assigning_do_not_count(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 3
        settings.save(update_fields=["questions_per_day"])

        cls = self._class_with_student()
        # The student practices two cards before the teacher assigns anything.
        select(self.student, self.picked)
        self.client.get("/deck/")
        self.client.post("/deck/advance/")
        self.client.post("/deck/advance/")

        a = self._create_and_assign(cls, deck_size=3)
        sa = StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)
        self.assertEqual(sa.cards_answered, 0)
        # The deck stretches past the daily 3 so all 3 assignment cards fit.
        data = self.client.get("/deck/").json()
        self.assertEqual((data["current_number"], data["total"]), (3, 5))

    def test_open_assignments_count_the_same_cards(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 1
        settings.save(update_fields=["questions_per_day"])

        small, _ = self._setup_assignment(deck_size=2)
        big, _ = self._setup_assignment(deck_size=4)
        self.client.post(f"/assignments/{small['id']}/play/")
        self.client.post(f"/assignments/{big['id']}/play/")
        # One deck covers both: the largest remainder, not the sum.
        self.assertEqual(self.client.get("/deck/").json()["total"], 4)
        for _ in range(2):
            self.client.post("/deck/advance/")
        statuses = dict(
            StudentAssignment.objects.filter(student=self.student)
            .values_list("assignment_id", "status")
        )
        self.assertEqual(statuses[small["id"]], StudentAssignment.COMPLETED)
        self.assertEqual(statuses[big["id"]], StudentAssignment.IN_PROGRESS)
        self.assertEqual(self.client.get("/deck/").json()["total"], 4)

    def test_unassigned_student_cannot_start(self, _gen):
        a, _ = self._setup_assignment()
        other = make_user()
        self.client.force_login(other)
        self.assertEqual(
            self.client.post(f"/assignments/{a['id']}/play/").status_code, 403
        )


class AssignmentResultsTests(TestCase):
    """The report: who finished their cards, band mix on the assigned topics."""

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

    def test_report_counts_bands_and_completion(self):
        student = make_user()
        a = self._assign_to_student(student)
        # Practiced Easy (interval 10 -> familiar); never practiced Hard (-> new).
        mark_practiced(student, self.easy, interval=10)
        # Joining created the in-progress row; finish it.
        StudentAssignment.objects.filter(assignment_id=a["id"], student=student).update(
            status=StudentAssignment.COMPLETED, cards_answered=10,
        )

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        self.assertEqual(res["num_students"], 1)
        self.assertEqual(res["num_completed"], 1)
        self.assertEqual(res["band_totals"]["familiar"], 1)
        self.assertEqual(res["band_totals"]["new"], 1)
        row = res["students"][0]
        self.assertEqual((row["status"], row["cards_answered"]), ("done", 10))
        self.assertEqual(row["proficiency"]["familiar"], 1)
        self.assertEqual(row["proficiency"]["new"], 1)

    def test_overdue_when_unfinished_past_due(self):
        student = make_user()
        past = (timezone.now() - timezone.timedelta(days=1)).isoformat()
        a = self._assign_to_student(student, due_at=past)
        # Practicing the topics isn't enough; the card count decides.
        mark_practiced(student, self.easy)
        mark_practiced(student, self.hard)

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        row = res["students"][0]
        self.assertEqual(row["status"], "in_progress")
        self.assertTrue(row["overdue"])

    def test_report_breaks_bands_down_per_topic(self):
        first, second = make_user(), make_user()
        a = self._assign_to_student(first)
        self._join_existing(second, a)
        mark_practiced(first, self.easy, interval=30)  # proficient
        mark_practiced(second, self.easy, interval=3)  # learning

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        by_name = {t["topic_name"]: t["proficiency"] for t in res["topics"]}
        self.assertEqual(by_name["Easy"], {"new": 0, "learning": 1, "familiar": 0, "proficient": 1})
        self.assertEqual(by_name["Hard"], {"new": 2, "learning": 0, "familiar": 0, "proficient": 0})

    def test_struggled_ranks_assigned_topics_by_misses(self):
        student = make_user()
        a = self._assign_to_student(student)
        log_answers(student, self.easy, "correct_first", "correct_first", "incorrect")
        log_answers(student, self.hard, "incorrect", "correct_second", "correct_first")
        # Unassigned topics never show, however badly they went.
        other = make_topic(self.course, topic_name="Other")
        log_answers(student, other, "incorrect", "incorrect")

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        self.assertEqual(
            [(t["topic_name"], t["accuracy"], t["students"]) for t in res["struggled"]],
            [("Hard", 33, 1), ("Easy", 67, 1)],
        )

    def test_struggled_omits_topics_never_missed(self):
        student = make_user()
        a = self._assign_to_student(student)
        log_answers(student, self.easy, "correct_first")

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        self.assertEqual(res["struggled"], [])

    def _join_existing(self, student, assignment):
        """Enroll another student in the class `assignment` was assigned to."""
        link = AssignmentClass.objects.get(assignment_id=assignment["id"])
        self.client.force_login(student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": link.classroom.join_code}),
            content_type="application/json",
        )


class TeacherInsightTests(TestCase):
    """Roster familiarity bars and the student detail's practice activity."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        self.course = make_course()
        self.topic = make_topic(self.course, topic_name="Fractions")
        self.other = make_topic(self.course, topic_name="Decimals")
        select(self.student, self.topic)
        select(self.student, self.other)
        self.classroom = Classroom.objects.create(
            teacher=self.teacher, name="P1", join_code="ABC234",
        )
        ClassEnrollment.objects.create(classroom=self.classroom, student=self.student)
        self.client.force_login(self.teacher)

    def test_roster_has_band_counts_over_selected_topics(self):
        mark_practiced(self.student, self.topic, interval=10)
        roster = self.client.get(f"/classes/{self.classroom.id}/students/").json()
        self.assertEqual(
            roster["students"][0]["proficiency"],
            {"new": 1, "learning": 0, "familiar": 1, "proficient": 0},
        )

    def test_activity_week_and_consistency(self):
        today = timezone.localdate()
        day = timezone.timedelta(days=1)
        # Practiced today (partial), yesterday (finished), then a gap, and once
        # 10 days ago: outside the week but inside the consistency window.
        DailyPractice.objects.create(user=self.student, date=today, answered=3, total=10)
        DailyPractice.objects.create(user=self.student, date=today - day, answered=10, total=10)
        DailyPractice.objects.create(user=self.student, date=today - 10 * day, answered=5, total=5)
        log_answers(self.student, self.topic, "correct_first", "correct_first", "incorrect", seconds=40)
        log_answers(self.student, self.other, "correct_second", seconds=20, date=today - day)
        log_answers(self.student, self.other, "incorrect", date=today - 10 * day)

        detail = self.client.get(
            f"/teacher/students/{self.student.id}/?today={today.isoformat()}"
        ).json()
        activity = detail["activity"]
        self.assertEqual(len(activity["days"]), 28)
        self.assertEqual(activity["days"][-1], {"date": today.isoformat(), "status": "partial"})
        self.assertEqual(activity["days"][-2]["status"], "completed")
        self.assertEqual(activity["days_practiced"], 3)
        self.assertEqual(activity["streak"], 2)
        self.assertEqual(activity["week"], {"cards_answered": 13, "seconds": 140, "accuracy": 50})
        # Decimals: 0/2 first-try; Fractions: 2/3.
        self.assertEqual(
            [(t["topic_name"], t["accuracy"]) for t in detail["struggled"]],
            [("Decimals", 0), ("Fractions", 67)],
        )

    def test_streak_holds_until_today_is_practiced(self):
        today = timezone.localdate()
        day = timezone.timedelta(days=1)
        for n in (1, 2):
            DailyPractice.objects.create(user=self.student, date=today - n * day, answered=1, total=10)
        detail = self.client.get(
            f"/teacher/students/{self.student.id}/?today={today.isoformat()}"
        ).json()
        self.assertEqual(detail["activity"]["streak"], 2)

    def test_activity_empty_for_new_student(self):
        detail = self.client.get(f"/teacher/students/{self.student.id}/").json()
        self.assertEqual(detail["activity"]["streak"], 0)
        self.assertEqual(
            detail["activity"]["week"], {"cards_answered": 0, "seconds": 0, "accuracy": None}
        )
        self.assertEqual(detail["struggled"], [])


@mock.patch("myapp.views.mathgenerator.addition", return_value=("Q", "4"))
class MyAssignmentsTests(TestCase):
    """A student's to-do / done split, driven by cards answered since assigning."""

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
            data=json.dumps({
                "title": "HW", "deck_size": 2, "topics": [{"topic_id": self.topic.id}],
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
        return a

    def test_upcoming_until_card_count_answered(self, _gen):
        a = self._assign()
        data = self.client.get("/assignments/mine/").json()
        self.assertEqual(len(data["upcoming"]), 1)
        self.assertEqual(len(data["completed"]), 0)
        row = data["upcoming"][0]
        # Joining a class that already has the assignment starts it.
        self.assertEqual((row["status"], row["cards_answered"], row["deck_size"]), ("in_progress", 0, 2))

        self.client.post(f"/assignments/{a['id']}/play/")
        self.client.post("/deck/advance/")
        row = self.client.get("/assignments/mine/").json()["upcoming"][0]
        self.assertEqual((row["status"], row["cards_answered"]), ("in_progress", 1))

        # The second card reaches the count and moves it to done.
        self.client.post("/deck/advance/")
        data = self.client.get("/assignments/mine/").json()
        self.assertEqual(len(data["upcoming"]), 0)
        self.assertEqual(len(data["completed"]), 1)
