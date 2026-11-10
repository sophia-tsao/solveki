"""Tests for the teacher/student roles, classes, and assignments feature.

Covers role gating, class create/join/roster, assignment authoring and
assign-to-multiple-classes, and the simplified student flow: assigning an
assignment to a class (or joining a class that has one) adds its topics to the
student's selections, and each open assignment gets its own deck for the day
carrying its share of the teacher's card count (with several open, the
practice page lists them to pick from). An assignment
is done once the student has answered its card count (any topic) since it
reached them; the teacher report adds familiarity on the assignment's topics
from the student's SM-2 state.

The `gcd` generator the test topics use is mocked so deck generation is
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
        self.topic = make_topic(self.course, generator_name="gcd")
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

    def test_late_work_allowed_by_default_and_editable(self):
        a = self._create_assignment()
        self.assertTrue(a["allow_late"])
        res = self.client.patch(
            f"/assignments/{a['id']}/", data=json.dumps({"allow_late": False}),
            content_type="application/json",
        )
        self.assertFalse(res.json()["allow_late"])
        self.assertFalse(Assignment.objects.get(id=a["id"]).allow_late)
        bad = self.client.patch(
            f"/assignments/{a['id']}/", data=json.dumps({"allow_late": "no"}),
            content_type="application/json",
        )
        self.assertEqual(bad.status_code, 400)

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
        other = make_topic(self.course, topic_name="Other", generator_name="gcd")
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


@mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "4"))
class StartAssignmentTests(TestCase):
    """Assigning adds topics and starts the count; opening grows the deck and routes."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        self.course = make_course()
        self.picked = make_topic(self.course, topic_name="Picked", generator_name="gcd")

    def _setup_assignment(self, deck_size=6, topics=None, due_at=None, allow_late=True):
        self.client.force_login(self.teacher)
        cls = self.client.post(
            "/classes/", data=json.dumps({"name": "A"}), content_type="application/json"
        ).json()
        a = self.client.post(
            "/assignments/",
            data=json.dumps({
                "title": "HW", "deck_size": deck_size, "allow_late": allow_late,
                "topics": [{"topic_id": t.id} for t in (topics or [self.picked])],
            }),
            content_type="application/json",
        ).json()
        spec = {"class_id": cls["id"]}
        if due_at is not None:
            spec["due_at"] = due_at.isoformat()
        self.client.post(
            f"/assignments/{a['id']}/assign/",
            data=json.dumps({"classes": [spec]}),
            content_type="application/json",
        )
        self.client.force_login(self.student)
        self.client.post(
            "/classes/join/", data=json.dumps({"code": cls["join_code"]}),
            content_type="application/json",
        )
        return a, cls

    def _due_today(self):
        return timezone.localtime().replace(hour=23, minute=59, second=0, microsecond=0)

    def _advance(self, outcome="correct_first", assignment=None):
        url = "/deck/advance/" + (f"?assignment={assignment['id']}" if assignment else "")
        return self.client.post(
            url, data=json.dumps({"outcome": outcome}), content_type="application/json",
        ).json()

    def _deck(self, assignment=None):
        url = "/deck/" + (f"?assignment={assignment['id']}" if assignment else "")
        return self.client.get(url).json()

    def _deck_topics(self, assignment):
        deck = DailyDeck.objects.get(user=self.student, assignment_id=assignment["id"])
        return {p["topic_id"] for p in deck.problems}

    def _row(self, a):
        return StudentAssignment.objects.get(assignment_id=a["id"], student=self.student)

    def test_start_selects_topics_grows_deck_and_routes(self, _gen):
        # Pin the student's daily size below the assignment's card count, and
        # make it due today, so the whole count lands in today's deck on top
        # of the setting.
        settings = Settings.load(self.student)
        settings.questions_per_day = 5
        settings.save(update_fields=["questions_per_day"])

        a, _ = self._setup_assignment(deck_size=8, due_at=self._due_today())
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

    def test_answering_card_count_right_completes_assignment(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 2
        settings.save(update_fields=["questions_per_day"])

        a, _ = self._setup_assignment(deck_size=3, due_at=self._due_today())
        self.client.post(f"/assignments/{a['id']}/play/")
        for n in range(1, 3):
            data = self._advance()
            # A sitting is at least 4 cards, so a single slip can't sink it.
            self.assertEqual(data["total"], 4)
            sa = self._row(a)
            self.assertEqual((sa.cards_answered, sa.status), (n, StudentAssignment.IN_PROGRESS))
            self.assertEqual(sa.completion_pct, 100 * n // 3)

        self._advance()
        sa = self._row(a)
        self.assertEqual(sa.cards_answered, 3)
        self.assertEqual(sa.status, StudentAssignment.COMPLETED)
        self.assertEqual(sa.completion_pct, 100)
        self.assertFalse(sa.max_reached)
        self.assertIsNotNone(sa.completed_at)
        mine = self.client.get("/assignments/mine/").json()
        self.assertEqual([r["status"] for r in mine["completed"]], ["done"])
        # Getting it all right lifts the topic to "familiar", not back tomorrow.
        review = TopicReview.objects.get(user=self.student, topic=self.picked)
        self.assertGreaterEqual(review.interval, 6)

    def test_struggling_student_gets_more_cards_up_to_the_maximum(self, _gen):
        # A daily setting of 1 so every card past the first 4 is extra practice.
        settings = Settings.load(self.student)
        settings.questions_per_day = 1
        settings.save(update_fields=["questions_per_day"])
        a, _ = self._setup_assignment(deck_size=4, due_at=self._due_today())
        self.client.post(f"/assignments/{a['id']}/play/")
        last_pct = 0
        for _ in range(6):  # 1.5 x 4
            self._advance("incorrect")
            sa = self._row(a)
            # The percentage pauses rather than dropping as cards needed grow.
            self.assertGreaterEqual(sa.completion_pct, last_pct)
            last_pct = sa.completion_pct
        sa = self._row(a)
        self.assertEqual(sa.cards_answered, 6)
        self.assertEqual(sa.status, StudentAssignment.COMPLETED)
        self.assertTrue(sa.max_reached)
        # The deck kept going past the teacher's 4 to give the extra practice.
        self.assertGreaterEqual(DailyDeck.objects.get(user=self.student).current_index, 6)

    def test_student_who_recovers_finishes_before_the_maximum(self, _gen):
        a, _ = self._setup_assignment(deck_size=4, due_at=self._due_today())
        self.client.post(f"/assignments/{a['id']}/play/")
        for outcome in ("incorrect", "correct_first", "correct_first", "correct_first"):
            self._advance(outcome)
        sa = self._row(a)
        # 3 of the last 4 right after the 4 cards: done, at exactly the count.
        self.assertEqual((sa.cards_answered, sa.status), (4, StudentAssignment.COMPLETED))
        self.assertFalse(sa.max_reached)

    def test_only_cards_on_the_assignments_topics_count(self, _gen):
        own = make_topic(self.course, topic_name="Own", generator_name="gcd")
        select(self.student, own)
        a, _ = self._setup_assignment(deck_size=4)
        from myapp.views.deck import _count_assignment_card
        log_answers(self.student, own, "correct_first")
        _count_assignment_card(self.student, own.id, timezone.localdate())
        self.assertEqual(self._row(a).cards_answered, 0)
        log_answers(self.student, self.picked, "correct_first")
        _count_assignment_card(self.student, self.picked.id, timezone.localdate())
        self.assertEqual(self._row(a).cards_answered, 1)

    def test_late_work_counts_only_when_allowed(self, _gen):
        from myapp.views.deck import _count_assignment_card
        past = timezone.now() - timezone.timedelta(days=1)
        strict, _ = self._setup_assignment(deck_size=1, due_at=past, allow_late=False)
        lenient, _ = self._setup_assignment(deck_size=1, due_at=past, allow_late=True)
        log_answers(self.student, self.picked, "correct_first")
        _count_assignment_card(self.student, self.picked.id, timezone.localdate())
        # Past due without late work: frozen.
        self.assertEqual(self._row(strict).cards_answered, 0)
        self.assertEqual(self._row(strict).status, StudentAssignment.IN_PROGRESS)
        # Late work allowed: it counts, and the completion is marked late.
        sa = self._row(lenient)
        self.assertEqual((sa.cards_answered, sa.status, sa.late), (1, StudentAssignment.COMPLETED, True))

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
        own = make_topic(self.course, topic_name="Own", generator_name="gcd")
        select(self.student, own)
        self.client.get("/deck/")
        a = self._create_and_assign(cls)
        # Today's default deck is rebuilt with the new topic when next loaded.
        default = DailyDeck.objects.get(user=self.student, assignment__isnull=True)
        self.assertTrue(default.needs_regen)
        # With one assignment open, the practice page opens its deck instead.
        data = self.client.get("/deck/").json()
        self.assertEqual(data["assignment"], {"id": a["id"], "title": "HW", "open": True})
        self.assertEqual(data["open_assignments"], 1)
        self.assertFalse(
            DailyDeck.objects.get(user=self.student, assignment_id=a["id"]).needs_regen
        )

    def test_editing_topics_reaches_assigned_students(self, _gen):
        cls = self._class_with_student()
        a = self._create_and_assign(cls)
        extra = make_topic(self.course, topic_name="Extra", generator_name="gcd")
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
        self._advance()
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
        # The assignment's own deck holds today's sitting of it (at least 4
        # cards), past the daily 3.
        data = self.client.get("/deck/").json()
        self.assertEqual((data["current_number"], data["total"]), (1, 4))

    def test_open_assignments_count_the_same_cards(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 1
        settings.save(update_fields=["questions_per_day"])

        small, _ = self._setup_assignment(deck_size=2)
        big, _ = self._setup_assignment(deck_size=4)
        self.assertEqual(self._deck(small)["total"], 4)
        for _ in range(2):
            self._advance(assignment=small)
        statuses = dict(
            StudentAssignment.objects.filter(student=self.student)
            .values_list("assignment_id", "status")
        )
        # The cards on the shared topic counted toward both.
        self.assertEqual(statuses[small["id"]], StudentAssignment.COMPLETED)
        self.assertEqual(statuses[big["id"]], StudentAssignment.IN_PROGRESS)
        self.assertEqual(self._row(big).cards_answered, 2)
        # Now the only one open, the big one opens directly, with the rest of
        # today's sitting on the topic.
        data = self._deck()
        self.assertEqual((data["assignment"]["id"], data["total"]), (big["id"], 2))

    def test_several_open_assignments_are_listed_to_choose_from(self, _gen):
        soon = timezone.now() + timezone.timedelta(days=1)
        later, _ = self._setup_assignment(due_at=soon + timezone.timedelta(days=1))
        undated, _ = self._setup_assignment()
        first, _ = self._setup_assignment(due_at=soon)
        data = self._deck()
        self.assertEqual(
            [c["assignment_id"] for c in data["choose"]],
            [first["id"], later["id"], undated["id"]],
        )
        self.assertFalse(DailyDeck.objects.filter(user=self.student).exists())
        # Without picking one there's no card to answer or advance past.
        res = self.client.post(
            "/deck/check/", data=json.dumps({"answer": "4", "from_number": 1}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 409)
        self.assertIn("choose", self._advance())

    def test_an_assignments_deck_carries_only_its_own_cards(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 1
        settings.save(update_fields=["questions_per_day"])
        other = make_topic(self.course, topic_name="Other", generator_name="gcd")
        a, _ = self._setup_assignment(deck_size=4)
        b, _ = self._setup_assignment(deck_size=4, topics=[other])

        data = self._deck(a)
        self.assertEqual((data["assignment"]["id"], data["open_assignments"]), (a["id"], 2))
        self.assertEqual(self._deck_topics(a), {self.picked.id})
        self._deck(b)
        self.assertEqual(self._deck_topics(b), {other.id})
        # Answering in one deck leaves the other where it was.
        self._advance(assignment=a)
        self.assertEqual(self._deck(a)["current_number"], 2)
        self.assertEqual(self._deck(b)["current_number"], 1)

    def test_each_deck_fills_up_to_the_daily_setting(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 10
        settings.save(update_fields=["questions_per_day"])
        a, _ = self._setup_assignment(deck_size=2)
        b, _ = self._setup_assignment(deck_size=2)
        self.assertEqual(self._deck(a)["total"], 10)
        self.assertEqual(self._deck(b)["total"], 10)

    def test_finished_assignment_practices_again_on_its_topics(self, _gen):
        settings = Settings.load(self.student)
        settings.questions_per_day = 3
        settings.save(update_fields=["questions_per_day"])
        own = make_topic(self.course, topic_name="Own", generator_name="gcd")
        select(self.student, own)
        a, _ = self._setup_assignment(deck_size=4, due_at=self._due_today())
        self._deck(a)
        for _ in range(4):
            self._advance(assignment=a)
        self.assertEqual(self._row(a).status, StudentAssignment.COMPLETED)
        DailyDeck.objects.filter(user=self.student).delete()

        # Practicing it again builds a deck on just its topics, without
        # counting toward anything further.
        res = self.client.post(f"/assignments/{a['id']}/play/")
        self.assertEqual(res.json()["assignment_id"], a["id"])
        data = self._deck(a)
        self.assertEqual(
            (data["assignment"]["id"], data["assignment"]["open"], data["total"]), (a["id"], False, 3)
        )
        self.assertEqual(self._deck_topics(a), {self.picked.id})
        # With nothing open, the practice page is the default deck again.
        self.assertNotIn("assignment", self._deck())

    def test_deck_for_an_assignment_not_given_to_the_student_is_404(self, _gen):
        a, _ = self._setup_assignment()
        self.client.force_login(make_user())
        self.assertEqual(self.client.get(f"/deck/?assignment={a['id']}").status_code, 404)

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
        self.easy = make_topic(self.course, topic_name="Easy", generator_name="gcd")
        self.hard = make_topic(self.course, topic_name="Hard", generator_name="gcd")

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

    def test_report_shows_completion_and_needs_help(self):
        helped = make_user()
        a = self._assign_to_student(helped)
        StudentAssignment.objects.filter(assignment_id=a["id"], student=helped).update(
            status=StudentAssignment.COMPLETED, completion_pct=100, max_reached=True,
        )

        self.client.force_login(self.teacher)
        res = self.client.get(f"/assignments/{a['id']}/results/").json()
        row = res["students"][0]
        self.assertEqual(
            (row["completion_pct"], row["max_reached"], row["late"]), (100, True, False)
        )
        self.assertEqual(res["assignment"]["max_cards"], 15)  # 1.5 x the default 10

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


@mock.patch("myapp.views.mathgenerator.gcd", return_value=("Q", "4"))
class MyAssignmentsTests(TestCase):
    """A student's to-do / done split, driven by cards answered since assigning."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.student = make_user()
        self.course = make_course()
        self.topic = make_topic(self.course, generator_name="gcd")

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
        advance = lambda: self.client.post(  # noqa: E731
            "/deck/advance/", data=json.dumps({"outcome": "correct_first"}),
            content_type="application/json",
        )
        advance()
        row = self.client.get("/assignments/mine/").json()["upcoming"][0]
        self.assertEqual(
            (row["status"], row["cards_answered"], row["completion_pct"]), ("in_progress", 1, 50)
        )
        self.assertNotIn("max_reached", row)  # extra practice isn't flagged to students

        # The second card right reaches the count and moves it to done.
        advance()
        data = self.client.get("/assignments/mine/").json()
        self.assertEqual(len(data["upcoming"]), 0)
        self.assertEqual(len(data["completed"]), 1)


class OverviewFocusTests(TestCase):
    """The overview's newly taught / weak spots columns."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.course = make_course()
        self.taught = make_topic(self.course, topic_name="Taught")
        self.older = make_topic(self.course, topic_name="Older")
        self.p1 = Classroom.objects.create(teacher=self.teacher, name="P1", join_code="FOC001")
        self.p2 = Classroom.objects.create(teacher=self.teacher, name="P2", join_code="FOC002")
        self.a, self.b = make_user(), make_user()
        ClassEnrollment.objects.create(classroom=self.p1, student=self.a)
        ClassEnrollment.objects.create(classroom=self.p2, student=self.b)
        self.client.force_login(self.teacher)

    def _assign(self, classroom, topic, students, days_ago=0):
        """Hand `topic` to `students` through an assignment started `days_ago` days back."""
        a = Assignment.objects.create(teacher=self.teacher, title=f"HW {topic.topic_name}")
        AssignmentTopic.objects.create(assignment=a, topic=topic)
        AssignmentClass.objects.create(assignment=a, classroom=classroom)
        started = timezone.now() - timezone.timedelta(days=days_ago)
        for s in students:
            select(s, topic)
            StudentAssignment.objects.create(
                assignment=a, classroom=classroom, student=s,
                status=StudentAssignment.IN_PROGRESS, started_at=started,
            )

    def _focus(self, **params):
        return self.client.get("/teacher/overview/focus/", params).json()

    def test_newly_taught_has_first_assigned_accuracy_and_bands(self):
        self._assign(self.p1, self.taught, [self.a], days_ago=3)
        self._assign(self.p2, self.taught, [self.b])
        mark_practiced(self.a, self.taught, interval=3)
        # a: 1 of 3 right first try; b: 1 of 1. Each student counts once: 67%.
        log_answers(self.a, self.taught, "incorrect", "correct_second", "correct_first")
        log_answers(self.b, self.taught, "correct_first")

        row, = self._focus()["newly_taught"]
        self.assertEqual(row, {
            "topic_id": self.taught.id, "topic_name": "Taught",
            "first_assigned": (timezone.localdate() - timezone.timedelta(days=3)).isoformat(),
            "accuracy": 67,
            "proficiency": {"new": 1, "learning": 1, "familiar": 0, "proficient": 0},
        })

    def test_newly_taught_ignores_old_assignments_and_answers_before_it(self):
        self._assign(self.p1, self.older, [self.a], days_ago=30)
        # Answers from before the assignment reached the student don't count.
        log_answers(
            self.b, self.taught, "incorrect",
            date=timezone.localdate() - timezone.timedelta(days=3),
        )
        self._assign(self.p2, self.taught, [self.b])

        row, = self._focus()["newly_taught"]
        self.assertEqual(row["topic_name"], "Taught")
        self.assertIsNone(row["accuracy"])

    def test_class_scope_narrows_every_column(self):
        self._assign(self.p1, self.taught, [self.a])
        self._assign(self.p2, self.older, [self.b])
        log_answers(self.a, self.taught, "incorrect")
        log_answers(self.b, self.older, "incorrect")

        data = self._focus(scope="class", class_id=self.p1.id)
        self.assertEqual([t["topic_name"] for t in data["newly_taught"]], ["Taught"])
        self.assertEqual([t["topic_name"] for t in data["weak_spots"]], ["Taught"])

    def test_weak_spots_average_accuracy_per_student(self):
        # a: 0% on one answer; b: 90% on ten. Pooled would be 9/11 = 82%, but
        # each student counts once, so the topic averages 45%.
        log_answers(self.a, self.taught, "incorrect")
        log_answers(self.b, self.taught, *["correct_first"] * 9, "incorrect")
        log_answers(self.a, self.older, "correct_first", "correct_second")

        data = self._focus()
        self.assertEqual(
            data["weak_spots"],
            [
                {"topic_id": self.taught.id, "topic_name": "Taught", "accuracy": 45, "missed_recent": 2},
                {"topic_id": self.older.id, "topic_name": "Older", "accuracy": 50, "missed_recent": 1},
            ],
        )

    def test_weak_spots_count_students_missing_in_the_last_two_weeks(self):
        old = timezone.localdate() - timezone.timedelta(days=20)
        log_answers(self.a, self.taught, "incorrect", date=old)
        log_answers(self.b, self.taught, "incorrect")
        # Only missed before the last two weeks: not a weak spot any more.
        log_answers(self.a, self.older, "incorrect", date=old)
        log_answers(self.b, self.older, "correct_first")

        spot, = self._focus()["weak_spots"]
        self.assertEqual((spot["topic_name"], spot["missed_recent"]), ("Taught", 1))

    def test_weak_spots_leave_out_topics_nobody_got_wrong(self):
        log_answers(self.a, self.taught, "correct_first", "correct_first")
        self.assertEqual(self._focus()["weak_spots"], [])

    def test_newly_taught_sorts_newest_then_lowest_accuracy(self):
        third = make_topic(self.course, topic_name="Third")
        self._assign(self.p1, self.older, [self.a], days_ago=5)
        self._assign(self.p1, self.taught, [self.a])
        self._assign(self.p1, third, [self.a])
        log_answers(self.a, self.taught, "correct_first")
        log_answers(self.a, third, "incorrect")
        log_answers(self.a, self.older, "incorrect")

        names = [t["topic_name"] for t in self._focus()["newly_taught"]]
        self.assertEqual(names, ["Third", "Taught", "Older"])

    def test_students_and_other_teachers_are_refused(self):
        self.client.force_login(self.a)
        self.assertEqual(self.client.get("/teacher/overview/focus/").status_code, 403)
        self.client.force_login(make_teacher())
        res = self.client.get("/teacher/overview/focus/", {"scope": "class", "class_id": self.p1.id})
        self.assertEqual(res.status_code, 403)


class ProficiencyHistoryTests(TestCase):
    """Familiarity over time: topics per band, banded by average familiarity."""

    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        self.course = make_course()
        self.classroom = Classroom.objects.create(teacher=self.teacher, name="P1", join_code="HIS001")
        self.a, self.b = make_user(), make_user()
        for s in (self.a, self.b):
            ClassEnrollment.objects.create(classroom=self.classroom, student=s)
        self.today = timezone.localdate()
        self.client.force_login(self.teacher)

    def _ago(self, days):
        return self.today - timezone.timedelta(days=days)

    def _grade(self, user, topic, days_ago, before):
        """A graded day for `user` on `topic`, with the interval it had before."""
        DailyTopicGrade.objects.create(
            user=user, topic=topic, date=self._ago(days_ago), applied_quality=5,
            snapshot_ease=2.5, snapshot_interval=before, snapshot_repetitions=0,
        )

    def _review(self, user, topic, interval):
        TopicReview.objects.create(user=user, topic=topic, interval=interval, repetitions=1, ease=2.5)

    def _series(self, **params):
        params = {"days": 7, "today": self.today.isoformat(), **params}
        res = self.client.get("/teacher/proficiency-history/", params).json()["series"]
        return {p["date"]: (p["new"], p["learning"], p["familiar"], p["proficient"]) for p in res}

    def test_topics_are_banded_by_average_interval_across_students(self):
        fractions = make_topic(self.course, topic_name="Fractions")
        select(self.a, fractions)
        select(self.b, fractions)
        # a: 0 -> 1 (graded 3 days ago) -> 30 (graded yesterday); b: 0 -> 4 (graded 3 days ago).
        self._grade(self.a, fractions, 3, before=0)
        self._grade(self.a, fractions, 1, before=1)
        self._review(self.a, fractions, 30)
        self._grade(self.b, fractions, 3, before=0)
        self._review(self.b, fractions, 4)

        series = self._series()
        # Average 2.5 (learning) after the first grades, then 17 (familiar).
        self.assertEqual(series[self._ago(3).isoformat()], (0, 1, 0, 0))
        self.assertEqual(series[self._ago(2).isoformat()], (0, 1, 0, 0))
        self.assertEqual(series[self._ago(1).isoformat()], (0, 0, 1, 0))
        self.assertEqual(series[self.today.isoformat()], (0, 0, 1, 0))
        self.assertNotIn(self._ago(4).isoformat(), series)

    def test_topic_count_grows_as_topics_are_added(self):
        early = make_topic(self.course, topic_name="Early")
        late = make_topic(self.course, topic_name="Late")
        select(self.a, early)
        select(self.a, late)
        self._grade(self.a, early, 5, before=0)
        self._review(self.a, early, 25)
        # Late reached the student through an assignment two days ago, unpracticed.
        assignment = Assignment.objects.create(teacher=self.teacher, title="HW")
        AssignmentTopic.objects.create(assignment=assignment, topic=late)
        StudentAssignment.objects.create(
            assignment=assignment, classroom=self.classroom, student=self.a,
            status=StudentAssignment.IN_PROGRESS,
            started_at=timezone.now() - timezone.timedelta(days=2),
        )

        series = self._series()
        self.assertEqual(series[self._ago(5).isoformat()], (0, 0, 0, 1))
        self.assertEqual(series[self._ago(3).isoformat()], (0, 0, 0, 1))
        self.assertEqual(series[self._ago(2).isoformat()], (1, 0, 0, 1))
        self.assertEqual(series[self.today.isoformat()], (1, 0, 0, 1))

    def test_selected_but_untouched_topic_counts_from_today(self):
        select(self.a, make_topic(self.course, topic_name="Fresh"))
        self.assertEqual(self._series(), {self.today.isoformat(): (1, 0, 0, 0)})
