from django.db import models
from django.conf import settings as django_settings

# Create your models here.

class Course(models.Model):
    course_name = models.CharField()
    grade_level = models.IntegerField()

    def __str__(self):
        return self.course_name

class Topic(models.Model):
    topic_name = models.CharField()
    course = models.ForeignKey('Course', blank=True, null=True, on_delete=models.SET_NULL, related_name="topics")
    generator_name = models.CharField(blank=True, null=True)

    def __str__(self):
        return self.topic_name

class UserTopicSelection(models.Model):
    """Records that a given user has selected a given topic.

    Topic selection is per-user, so it lives here rather than as a flag on the
    shared Topic catalog. A row's existence means "selected"; no row means
    "not selected".
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_selections")
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="selections")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "topic"], name="unique_user_topic"),
        ]

    def __str__(self):
        return f"{self.user} -> {self.topic}"

class TopicReview(models.Model):
    """Spaced-repetition (SM-2) scheduling state for one user's practice of one topic.

    Solveki schedules *topics*, not individual problems: every problem is freshly
    generated, so the schedulable unit is the user's mastery of a topic. One row
    per (user, topic) holds the SM-2 state used to decide when the topic is next
    due for review.

    Separate from `UserTopicSelection` on purpose: selection and learning history
    have independent lifecycles, so deselecting a topic (dropping the selection
    row) preserves its review state for when it's selected again.

    `due_date` is null until the topic has been reviewed at least once; a null
    `due_date` means "due now" (never practiced yet).
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_reviews")
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="reviews")
    ease = models.FloatField(default=2.5)
    interval = models.IntegerField(default=0)  # days until next review
    repetitions = models.IntegerField(default=0)  # consecutive successful reviews
    due_date = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "topic"], name="unique_user_topic_review"),
        ]

    def __str__(self):
        return f"Review({self.user} -> {self.topic}, due {self.due_date})"

class DailyTopicGrade(models.Model):
    """Records that a topic has been graded on a given day, for the once-per-day rule.

    A topic can appear more than once in a day's deck (the deck fills to
    `questions_per_day`, repeating topics when few are selected). Only the first
    answer for a topic each day sets its SM-2 schedule; later repeats may only
    pull it *down* (a miss re-grades as a lapse; a success does nothing). See the
    grading module for the rule.

    To apply that without compounding — repeated misses must not drop ease over
    and over — this stores a snapshot of the topic's SM-2 state *before* the
    day's first grade (`snapshot_*`) plus the worst quality seen so far today
    (`applied_quality`). Each occurrence recomputes the TopicReview from the
    snapshot using min(applied_quality, this_quality), so the day's net effect is
    always "first grade, then only downward", computed from a single fixed base.
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_topic_grades")
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="daily_grades")
    date = models.DateField()
    applied_quality = models.IntegerField()  # worst SM-2 quality applied so far today
    snapshot_ease = models.FloatField()
    snapshot_interval = models.IntegerField()
    snapshot_repetitions = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "topic", "date"], name="unique_user_topic_date_grade"),
        ]

    def __str__(self):
        return f"Grade({self.user} -> {self.topic} on {self.date}, q={self.applied_quality})"

class DailyPractice(models.Model):
    """Durable record of how much of a day's deck a user got through.

    `DailyDeck` rows are pruned when a new day starts (see
    ``_get_or_create_today_deck``), and `DailyTopicGrade` counts distinct topics,
    not problems answered — so neither can tell, after the fact, whether a past
    day's deck was finished. This one-row-per-(user, date) record is updated as
    the student advances through the deck, giving the dashboard calendar a
    stable "completed / partial / none" signal per day.

    `answered` is the number of problems stepped past that day; `total` is the
    deck size at that moment (`min(len(problems), questions_per_day)`, matching
    what the deck view reports). The day counts as completed when
    ``answered >= total`` (with ``total > 0``); a row only exists once at least
    one problem has been answered, so a day with no row means "did not practice".
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_practice")
    date = models.DateField()
    answered = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_user_date_practice"),
        ]

    def __str__(self):
        return f"Practice({self.user} on {self.date}: {self.answered}/{self.total})"

class ProficiencySnapshot(models.Model):
    """A daily count of how many of a user's selected topics sit in each proficiency band.

    The dashboard/teacher views bucket a topic's SM-2 `interval` into four
    proficiency bands (New / Learning / Familiar / Proficient). That's a *current*
    view; to chart familiarity over time we persist one row per (user, date)
    holding the band counts as of that day. Written on active days (deck load and
    after grading — see ``_snapshot_proficiency``); a day with no row means the
    student wasn't active, and readers forward-fill the last known snapshot.

    Counts are over the user's currently-selected, usable topics (matching the
    dashboard donut's "topics selected" total), so `total` == new + learning +
    familiar + proficient.
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="proficiency_snapshots")
    date = models.DateField()
    new = models.IntegerField(default=0)
    learning = models.IntegerField(default=0)
    familiar = models.IntegerField(default=0)
    proficient = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_user_date_proficiency"),
        ]

    def __str__(self):
        return f"Proficiency({self.user} on {self.date}: {self.total} topics)"

class Settings(models.Model):
    """Per-user settings.

    Also carries the user's `role` (student or teacher). Role lives here rather
    than on a separate profile so it rides along with the per-user config that
    `Settings.load(user)` already provisions on demand. New users default to
    student; the role is chosen once at signup (see the role endpoint) and gates
    the teacher-only class/assignment features.
    """
    STUDENT = "student"
    TEACHER = "teacher"
    ROLE_CHOICES = [(STUDENT, "Student"), (TEACHER, "Teacher")]

    user = models.OneToOneField(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="settings")
    language = models.CharField(default='en', max_length=10)
    questions_per_day = models.IntegerField(default=10)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    # True once the user has explicitly chosen their role at signup. The role
    # endpoint refuses to change a locked role, so a student can't later promote
    # themselves to teacher to read other students' data.
    role_chosen = models.BooleanField(default=False)

    @classmethod
    def load(cls, user):
        obj, _ = cls.objects.get_or_create(user=user)
        return obj

    def __str__(self):
        return f"Settings({self.user})"

class Classroom(models.Model):
    """A teacher's class that students join with a code.

    Owned by one teacher (`teacher`). Students join via `join_code` (or are added
    by the teacher); membership lives in `ClassEnrollment`. `course` is an
    optional default subject for the class, used to pre-scope the assignment
    builder. Archived classes are hidden from the default lists but retained so
    past assignment analytics still resolve their class.
    """
    teacher = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="taught_classes")
    name = models.CharField(max_length=200)
    join_code = models.CharField(max_length=12, unique=True)
    course = models.ForeignKey('Course', blank=True, null=True, on_delete=models.SET_NULL, related_name="classrooms")
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Classroom({self.name} by {self.teacher})"


class ClassEnrollment(models.Model):
    """A student's membership in a `Classroom`. One row per (classroom, student)."""
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["classroom", "student"], name="unique_classroom_student"),
        ]

    def __str__(self):
        return f"Enrollment({self.student} in {self.classroom})"


class Assignment(models.Model):
    """A teacher-authored task, assignable to one or more classes.

    An assignment is a single idea: the teacher picks a set of topics to add to
    students' spaced-repetition decks (stored as `AssignmentTopic` rows) and how
    many cards the daily practice deck should hold (`deck_size`). Opening an
    assignment adds its topics to the student's own selections and grows today's
    practice deck to `deck_size`; the student then practices through their normal
    deck, so SM-2 always schedules the work. The assignment's topics also drive
    its progress report (proficiency on those topics by the due date).

    An assignment is authored once and handed to classes through
    `AssignmentClass`, so editing/deleting it affects every class it reached.
    """
    teacher = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_assignments")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    deck_size = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment({self.title} by {self.teacher})"


class AssignmentTopic(models.Model):
    """One topic an `Assignment` adds to each assigned student's practice deck."""
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name="assignment_topics")
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="assignment_topics")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "topic"], name="unique_assignment_topic"),
        ]

    def __str__(self):
        return f"{self.assignment} :: {self.topic}"


class AssignmentClass(models.Model):
    """Assigns an `Assignment` to a `Classroom`, with scheduling.

    The same assignment can be handed to multiple classes (one row each), so a
    teacher authors once and assigns widely. `available_at`/`due_at` bound when
    students in that class can start and when it's due.
    """
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name="class_links")
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, related_name="assignment_links")
    assigned_at = models.DateTimeField(auto_now_add=True)
    available_at = models.DateTimeField(blank=True, null=True)
    due_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "classroom"], name="unique_assignment_classroom"),
        ]

    def __str__(self):
        return f"{self.assignment} -> {self.classroom}"


class StudentAssignment(models.Model):
    """A lightweight record that a student has opened an assignment.

    Opening an assignment routes the student to their normal practice page (its
    topics are added to their selections and today's deck is grown to the
    assignment's `deck_size`), so there's no separate assignment quiz to store.
    This row just marks that the student started, and through which class, for
    the teacher's report. Progress itself is read from the student's SM-2 state
    on the assignment's topics (`TopicReview` / `DailyTopicGrade`).
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STATUS_CHOICES = [(NOT_STARTED, "Not started"), (IN_PROGRESS, "In progress"), (COMPLETED, "Completed")]

    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name="student_assignments")
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, related_name="student_assignments")
    student = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_assignments")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=NOT_STARTED)
    started_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_assignment_student"),
        ]

    def __str__(self):
        return f"StudentAssignment({self.student} :: {self.assignment}, {self.status})"


class DailyDeck(models.Model):
    """A set of problems generated for a single day, for a single user."""
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="decks")
    date = models.DateField()
    problems = models.JSONField(default=list)
    current_index = models.IntegerField(default=0)
    # Set when the user's topic selection changes so the unanswered tail is
    # rebuilt lazily on the next practice-page load (see _mark_deck_stale /
    # _get_or_create_today_deck) rather than synchronously on every toggle.
    needs_regen = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_user_date_deck"),
        ]

    def __str__(self):
        return f"Deck {self.user} {self.date} ({self.current_index}/{len(self.problems)})"
