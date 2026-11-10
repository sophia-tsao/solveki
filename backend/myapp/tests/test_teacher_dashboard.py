"""Tests for the teacher dashboard read endpoints.

Covers the assignments list summaries (classes, due dates, status counts),
duplicating an assignment, the extra per-student fields on assignment results
(teacher status, cards needed, accuracy, topics solid, last active, counts),
the class roster's weekly stats, the class progress grid, the teacher home
summary (KPIs, needs attention, due soon), and the student page's classes,
benchmarks and per-topic accuracy.
"""
import datetime
import itertools

from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from myapp.models import (
    AnswerRecord, Assignment, AssignmentClass, AssignmentTopic, ClassEnrollment,
    Classroom, DailyPractice, Settings, StudentAssignment, TopicReview,
)
from .factories import make_course, make_topic, make_user, select
from .test_classes_assignments import log_answers, make_teacher

_codes = itertools.count(1)
TODAY = timezone.localdate()


def make_class(teacher, name="P1"):
    return Classroom.objects.create(teacher=teacher, name=name, join_code=f"T{next(_codes):05d}")


def enroll(classroom, *students):
    for s in students:
        ClassEnrollment.objects.create(classroom=classroom, student=s)


def make_assignment(teacher, topics, title="HW", deck_size=4, classes=(), due_at=None):
    a = Assignment.objects.create(teacher=teacher, title=title, deck_size=deck_size)
    for t in topics:
        AssignmentTopic.objects.create(assignment=a, topic=t)
    for c in classes:
        AssignmentClass.objects.create(assignment=a, classroom=c, due_at=due_at)
    return a


def start(assignment, classroom, student, started_at=None, **fields):
    return StudentAssignment.objects.create(
        assignment=assignment, classroom=classroom, student=student,
        status=fields.pop("status", StudentAssignment.IN_PROGRESS),
        started_at=started_at or timezone.now() - datetime.timedelta(days=1), **fields,
    )


def practiced(user, day, answered=10, total=10):
    DailyPractice.objects.update_or_create(
        user=user, date=day, defaults={"answered": answered, "total": total},
    )


class AssignmentListTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        course = make_course()
        self.t1 = make_topic(course, topic_name="One")
        self.t2 = make_topic(course, topic_name="Two")
        self.p1 = make_class(self.teacher, "P1")
        self.p2 = make_class(self.teacher, "P2")
        self.ada, self.ben, self.cy = make_user(), make_user(), make_user()
        enroll(self.p1, self.ada, self.ben)
        enroll(self.p2, self.cy)
        self.client.force_login(self.teacher)

    def test_rows_carry_classes_due_dates_and_status_counts(self):
        past = timezone.now() - datetime.timedelta(days=1)
        a = make_assignment(self.teacher, [self.t1, self.t2], classes=[self.p1], due_at=past)
        AssignmentClass.objects.create(assignment=a, classroom=self.p2, due_at=past + datetime.timedelta(days=5))
        start(a, self.p1, self.ada)  # reached, no cards: not started
        start(a, self.p1, self.ben, cards_answered=2)
        start(a, self.p2, self.cy, status=StudentAssignment.COMPLETED, cards_answered=6, max_reached=True)

        row = self.client.get("/assignments/").json()["assignments"][0]
        self.assertEqual(row["topic_count"], 2)
        self.assertEqual([c["class_name"] for c in row["classes"]], ["P1", "P2"])
        self.assertEqual(row["next_due_at"], past.isoformat())
        self.assertEqual(row["counts"], {
            "assigned": 3, "done": 1, "in_progress": 1, "not_started": 1,
            "overdue": 2, "needs_help": 1,
        })

    def test_class_filter_narrows_rows_and_counts(self):
        a = make_assignment(self.teacher, [self.t1], classes=[self.p1, self.p2])
        make_assignment(self.teacher, [self.t1], title="Other", classes=[self.p2])
        rows = self.client.get(f"/assignments/?class={self.p1.id}").json()["assignments"]
        self.assertEqual([r["id"] for r in rows], [a.id])
        self.assertEqual(rows[0]["counts"]["assigned"], 2)
        self.assertEqual([c["class_id"] for c in rows[0]["classes"]], [self.p1.id])

    def test_query_count_does_not_grow_with_assignments(self):
        make_assignment(self.teacher, [self.t1], classes=[self.p1])
        with CaptureQueriesContext(connection) as one:
            self.client.get("/assignments/")
        for i in range(4):
            make_assignment(self.teacher, [self.t1, self.t2], title=f"A{i}", classes=[self.p1, self.p2])
        with CaptureQueriesContext(connection) as five:
            self.client.get("/assignments/")
        self.assertEqual(len(one), len(five))

    def test_duplicate_copies_settings_and_topics_but_not_classes(self):
        a = make_assignment(self.teacher, [self.t1, self.t2], title="Unit 4", deck_size=7, classes=[self.p1])
        res = self.client.post(f"/assignments/{a.id}/duplicate/")
        self.assertEqual(res.status_code, 201)
        copy = Assignment.objects.get(id=res.json()["id"])
        self.assertEqual((copy.title, copy.deck_size), ("Unit 4 (copy)", 7))
        self.assertEqual(
            list(copy.assignment_topics.order_by("id").values_list("topic_id", flat=True)),
            [self.t1.id, self.t2.id],
        )
        self.assertFalse(copy.class_links.exists())

    def test_duplicate_rejects_another_teachers_assignment(self):
        a = make_assignment(make_teacher(), [self.t1])
        self.assertEqual(self.client.post(f"/assignments/{a.id}/duplicate/").status_code, 403)


class AssignmentResultsExtrasTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        course = make_course()
        self.t1 = make_topic(course, topic_name="One")
        self.t2 = make_topic(course, topic_name="Two")
        self.p1 = make_class(self.teacher)
        self.ada, self.ben = make_user(), make_user()
        enroll(self.p1, self.ada, self.ben)
        self.a = make_assignment(self.teacher, [self.t1, self.t2], deck_size=4, classes=[self.p1])
        self.client.force_login(self.teacher)

    def test_students_carry_status_cards_accuracy_solid_and_last_active(self):
        start(self.a, self.p1, self.ada, cards_answered=4, cards_needed=6)
        start(self.a, self.p1, self.ben)
        # Before the assignment reached Ada: ignored.
        old = AnswerRecord.objects.create(user=self.ada, topic=self.t1, date=TODAY, outcome="incorrect")
        AnswerRecord.objects.filter(id=old.id).update(created_at=timezone.now() - datetime.timedelta(days=3))
        log_answers(self.ada, self.t1, "correct_first", "correct_first")
        log_answers(self.ada, self.t2, "correct_second", "incorrect")
        practiced(self.ada, TODAY, answered=4)

        res = self.client.get(f"/assignments/{self.a.id}/results/?today={TODAY}").json()
        rows = {r["name"]: r for r in res["students"]}
        ada = rows[self.ada.username]
        self.assertEqual((ada["status"], ada["cards_answered"], ada["cards_needed"]), ("in_progress", 4, 6))
        self.assertEqual(ada["accuracy"], 50)
        self.assertEqual(ada["topics_solid"], 1)  # One: 2/2 right; Two: not solid
        self.assertEqual(ada["last_active"], TODAY.isoformat())
        ben = rows[self.ben.username]
        # Reached but nothing answered reads as not started, with the deck size as cards needed.
        self.assertEqual((ben["status"], ben["cards_needed"], ben["accuracy"]), ("not_started", 4, None))
        self.assertEqual(res["counts"]["not_started"], 1)
        self.assertEqual(res["counts"]["in_progress"], 1)


class ClassRosterAndProgressTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        course = make_course()
        self.t1 = make_topic(course, topic_name="One")
        self.t2 = make_topic(course, topic_name="Two")
        self.p1 = make_class(self.teacher)
        self.ada, self.ben = make_user(first_name="Ada"), make_user(first_name="Ben")
        enroll(self.p1, self.ben, self.ada)
        self.client.force_login(self.teacher)

    def test_roster_reports_the_week_and_overdue_work(self):
        past = timezone.now() - datetime.timedelta(hours=2)
        a = make_assignment(self.teacher, [self.t1], classes=[self.p1], due_at=past)
        start(a, self.p1, self.ada)
        start(a, self.p1, self.ben, status=StudentAssignment.COMPLETED, cards_answered=4)
        practiced(self.ada, TODAY - datetime.timedelta(days=2), answered=6)
        practiced(self.ada, TODAY - datetime.timedelta(days=9), answered=8)  # outside the week
        log_answers(self.ada, self.t1, "correct_first", "incorrect", date=TODAY - datetime.timedelta(days=2))

        rows = {r["id"]: r for r in self.client.get(
            f"/classes/{self.p1.id}/students/?today={TODAY}").json()["students"]}
        ada = rows[self.ada.id]
        self.assertEqual((ada["cards_7d"], ada["accuracy_7d"]), (6, 50))
        self.assertEqual(ada["last_active"], (TODAY - datetime.timedelta(days=2)).isoformat())
        self.assertEqual(ada["overdue_count"], 1)
        ben = rows[self.ben.id]
        self.assertEqual((ben["cards_7d"], ben["accuracy_7d"], ben["last_active"], ben["overdue_count"]),
                         (0, None, None, 0))

    def test_progress_grid_bands_each_student_on_the_latest_assignments_topics(self):
        older = make_assignment(self.teacher, [self.t2], title="Old", classes=[self.p1])
        latest = make_assignment(self.teacher, [self.t1, self.t2], title="New", classes=[self.p1])
        AssignmentClass.objects.filter(assignment=older).update(
            assigned_at=timezone.now() - datetime.timedelta(days=5))
        TopicReview.objects.create(user=self.ada, topic=self.t1, interval=10, repetitions=2, ease=2.5)
        log_answers(self.ada, self.t1, "correct_first")
        log_answers(self.ada, self.t2, "incorrect")

        res = self.client.get(f"/classes/{self.p1.id}/progress/?today={TODAY}").json()
        self.assertEqual(res["assignment_id"], latest.id)
        self.assertEqual([a["title"] for a in res["assignments"]], ["New", "Old"])
        self.assertEqual([t["topic_name"] for t in res["topics"]], ["One", "Two"])
        self.assertEqual([s["name"] for s in res["students"]], ["Ada", "Ben"])
        ada, ben = res["students"]
        self.assertEqual(ada["cells"][str(self.t1.id)], {"band": "familiar", "missed_recent": False})
        self.assertEqual(ada["cells"][str(self.t2.id)], {"band": "new", "missed_recent": True})
        self.assertIsNone(ben["cells"][str(self.t1.id)])
        self.assertEqual(res["topic_summary"], {str(self.t1.id): 50, str(self.t2.id): 0})

        picked = self.client.get(f"/classes/{self.p1.id}/progress/?assignment={older.id}").json()
        self.assertEqual([t["topic_name"] for t in picked["topics"]], ["Two"])

    def test_progress_grid_is_empty_without_assignments_and_owner_only(self):
        res = self.client.get(f"/classes/{self.p1.id}/progress/").json()
        self.assertEqual((res["topics"], res["assignment_id"]), ([], None))
        self.client.force_login(make_teacher())
        self.assertEqual(self.client.get(f"/classes/{self.p1.id}/progress/").status_code, 403)


class OverviewSummaryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        course = make_course()
        self.t1 = make_topic(course, topic_name="Factoring")
        self.p1 = make_class(self.teacher)
        self.ada, self.ben = make_user(first_name="Ada"), make_user(first_name="Ben")
        enroll(self.p1, self.ada, self.ben)
        for s in (self.ada, self.ben):
            settings = Settings.load(s)
            settings.questions_per_day = 5
            settings.save()
        self.client.force_login(self.teacher)

    def get(self, **params):
        return self.client.get("/teacher/overview/summary/", {"today": TODAY.isoformat(), **params}).json()

    def test_kpis_count_the_week_against_the_weekly_goal(self):
        practiced(self.ada, TODAY, answered=16)  # goal: 3 days x 5 cards = 15
        practiced(self.ben, TODAY - datetime.timedelta(days=1), answered=4)
        practiced(self.ben, TODAY - datetime.timedelta(days=8), answered=20)  # last week
        log_answers(self.ada, self.t1, "correct_first", "correct_first", "correct_first", "incorrect")
        log_answers(self.ben, self.t1, "correct_first", "incorrect", date=TODAY - datetime.timedelta(days=8))

        kpis = self.get()["kpis"]
        self.assertEqual((kpis["students"], kpis["on_track"], kpis["on_track_prev"]), (2, 1, 1))
        self.assertEqual((kpis["active"], kpis["cards_7d"], kpis["cards_per_active"]), (2, 20, 10))
        self.assertEqual((kpis["accuracy_7d"], kpis["accuracy_prev_7d"]), (75, 50))
        self.assertEqual(kpis["goal_cards"], 15)

    def test_needs_attention_ranks_overdue_quiet_students_first(self):
        past = timezone.now() - datetime.timedelta(days=1)
        a = make_assignment(self.teacher, [self.t1], title="Unit 4", classes=[self.p1], due_at=past)
        start(a, self.p1, self.ada)
        start(a, self.p1, self.ben, status=StudentAssignment.COMPLETED, cards_answered=6,
              max_reached=True, completed_at=timezone.now())
        practiced(self.ada, TODAY - datetime.timedelta(days=9))
        log_answers(self.ben, self.t1, "incorrect", "incorrect", "correct_first")

        data = self.get()
        items = data["needs_attention"]
        self.assertEqual(items[0]["type"], "student")
        self.assertEqual((items[0]["severity"], items[0]["name"]), ("crit", "Ada"))
        self.assertEqual(items[0]["overdue"], ["Unit 4"])
        self.assertEqual(items[0]["inactive_days"], 9)
        self.assertEqual(items[0]["class_id"], self.p1.id)
        kinds = [i["type"] for i in items]
        self.assertIn("needs_help", kinds)
        spot = next(i for i in items if i["type"] == "trouble_spot")
        self.assertEqual((spot["topic_name"], spot["accuracy"]), ("Factoring", 33))
        self.assertEqual([s["name"] for s in spot["students"]], ["Ben"])
        self.assertEqual(data["kpis"]["overdue"], 1)

    def test_due_soon_and_not_started_alerts(self):
        soon = timezone.now() + datetime.timedelta(hours=20)
        a = make_assignment(self.teacher, [self.t1], title="Quiz prep", classes=[self.p1], due_at=soon)
        start(a, self.p1, self.ada)
        start(a, self.p1, self.ben, cards_answered=1)
        make_assignment(self.teacher, [self.t1], title="Later", classes=[self.p1],
                        due_at=timezone.now() + datetime.timedelta(days=20))

        data = self.get()
        self.assertEqual([d["title"] for d in data["due_soon"]], ["Quiz prep"])
        self.assertEqual(data["due_soon"][0]["counts"]["assigned"], 2)
        alert = next(i for i in data["needs_attention"] if i["type"] == "not_started")
        self.assertEqual((alert["title"], alert["count"]), ("Quiz prep", 1))

    def test_class_scope_and_ownership(self):
        other = make_class(self.teacher, "P2")
        enroll(other, make_user())
        self.assertEqual(self.get(scope="class", class_id=other.id)["kpis"]["students"], 1)
        self.client.force_login(make_teacher())
        res = self.client.get("/teacher/overview/summary/", {"scope": "class", "class_id": self.p1.id})
        self.assertEqual(res.status_code, 403)


class StudentDetailExtrasTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = make_teacher()
        course = make_course()
        self.t1 = make_topic(course, topic_name="One")
        self.p1 = make_class(self.teacher, "P1")
        self.p2 = make_class(self.teacher, "P2")
        self.ada, self.ben, self.cy = make_user(), make_user(), make_user()
        enroll(self.p1, self.ada, self.ben, self.cy)
        enroll(self.p2, self.ada)
        select(self.ada, self.t1)
        self.client.force_login(self.teacher)

    def test_classes_benchmarks_and_topic_accuracy(self):
        practiced(self.ada, TODAY, answered=2)
        practiced(self.ben, TODAY, answered=10)
        practiced(self.cy, TODAY, answered=20)
        log_answers(self.ada, self.t1, "correct_first", "incorrect")
        log_answers(self.ben, self.t1, "correct_first", "correct_first")

        data = self.client.get(f"/teacher/students/{self.ada.id}/?today={TODAY}").json()
        self.assertEqual([c["name"] for c in data["classes"]], ["P1", "P2"])
        bench = data["benchmarks"]
        self.assertEqual((bench["class_name"], bench["cards_7d_median"]), ("P1", 10))
        self.assertEqual((bench["accuracy_30d"], bench["accuracy_30d_class"]), (50, 75))
        self.assertEqual(data["topics"][0]["accuracy_30d"], 50)

        other = self.client.get(f"/teacher/students/{self.ada.id}/?class={self.p2.id}").json()
        self.assertEqual(other["benchmarks"]["class_name"], "P2")

    def test_assignment_rows_use_teacher_status(self):
        a = make_assignment(self.teacher, [self.t1], classes=[self.p1])
        start(a, self.p1, self.ada)
        row = self.client.get(f"/teacher/students/{self.ada.id}/").json()["assignments"][0]
        self.assertEqual((row["status"], row["cards_needed"], row["class_id"]), ("not_started", 4, self.p1.id))
