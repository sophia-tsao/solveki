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

    Two kinds:
      - `topics`: the teacher picks specific topics and how many questions of
        each (see `AssignmentTopic`).
      - `deck`: the student completes their own spaced-repetition deck of size
        `deck_size`, either across all their selected topics (`deck_scope='all'`)
        or limited to a teacher-picked set of topics (`deck_scope='topics'`, the
        set stored as `AssignmentTopic` rows). The legacy `course`/`unit` scopes
        remain for older assignments.

    When SM-2 is enabled (a `*_sm2` mode), completing the assignment applies one
    SM-2 grade per topic derived from the student's accuracy; otherwise assignment
    answers never touch the student's `TopicReview` schedule. An assignment is
    authored once and handed to classes through `AssignmentClass`, so
    editing/deleting it affects every class it was assigned to.

    The delivery kind (topics vs deck) and whether SM-2 is applied are stored
    together in a single `mode` field. Use the `is_topics`/`is_deck`/`sm2_enabled`
    properties to read either dimension, and `Assignment.make_mode` to compose a
    mode from the two.
    """
    TOPICS = "topics"
    TOPICS_SM2 = "topics_sm2"
    DECK = "deck"
    DECK_SM2 = "deck_sm2"
    MODE_CHOICES = [
        (TOPICS, "Topics"),
        (TOPICS_SM2, "Topics + SM-2"),
        (DECK, "Deck"),
        (DECK_SM2, "Deck + SM-2"),
    ]
    _DECK_MODES = frozenset({DECK, DECK_SM2})
    _SM2_MODES = frozenset({TOPICS_SM2, DECK_SM2})

    SCOPE_ALL = "all"
    SCOPE_TOPICS = "topics"
    SCOPE_COURSE = "course"  # legacy
    SCOPE_UNIT = "unit"  # legacy
    SCOPE_CHOICES = [
        (SCOPE_ALL, "All selected"),
        (SCOPE_TOPICS, "Teacher-picked topics"),
        (SCOPE_COURSE, "Course"),
        (SCOPE_UNIT, "Unit"),
    ]

    teacher = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_assignments")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    mode = models.CharField(max_length=16, choices=MODE_CHOICES, default=TOPICS)
    created_at = models.DateTimeField(auto_now_add=True)

    # Deck-kind scoping (ignored for topics-kind assignments).
    deck_scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, blank=True, null=True)
    course = models.ForeignKey('Course', blank=True, null=True, on_delete=models.SET_NULL, related_name="deck_assignments")
    unit_key = models.CharField(max_length=64, blank=True, null=True)
    deck_size = models.IntegerField(default=10)

    def __str__(self):
        return f"Assignment({self.title} by {self.teacher})"

    @property
    def is_deck(self):
        return self.mode in self._DECK_MODES

    @property
    def is_topics(self):
        return not self.is_deck

    @property
    def sm2_enabled(self):
        return self.mode in self._SM2_MODES

    @classmethod
    def make_mode(cls, kind, sm2_enabled):
        """Compose a `mode` value from a base kind (topics/deck) and an SM-2 flag."""
        if kind == cls.DECK:
            return cls.DECK_SM2 if sm2_enabled else cls.DECK
        return cls.TOPICS_SM2 if sm2_enabled else cls.TOPICS


class AssignmentTopic(models.Model):
    """One topic in a topics-kind `Assignment`, with its question count."""
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name="assignment_topics")
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="assignment_topics")
    num_questions = models.IntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "topic"], name="unique_assignment_topic"),
        ]

    def __str__(self):
        return f"{self.assignment} :: {self.topic} x{self.num_questions}"


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
    """One student's instance of an assignment: their generated problems + progress.

    Problems are generated per-student on first open (same topics/counts as the
    assignment spec, freshly generated numbers) and stored inline as JSON in the
    same shape as `DailyDeck.problems` (a list of {problem, solution, topic_id}).
    Per-problem results are recorded in `AssignmentAttempt`. `classroom` records
    which class context the student took it under (an assignment may reach a
    student through exactly one of their classes).
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STATUS_CHOICES = [(NOT_STARTED, "Not started"), (IN_PROGRESS, "In progress"), (COMPLETED, "Completed")]

    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name="student_assignments")
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, related_name="student_assignments")
    student = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_assignments")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=NOT_STARTED)
    problems = models.JSONField(default=list)
    current_index = models.IntegerField(default=0)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_assignment_student"),
        ]

    def __str__(self):
        return f"StudentAssignment({self.student} :: {self.assignment}, {self.status})"


class AssignmentAttempt(models.Model):
    """A single answered problem within a `StudentAssignment`.

    Normalized (one row per answered problem) so teacher analytics aggregate with
    the ORM: per-topic accuracy ("most struggled with"), per-student accuracy, and
    overall averages. `outcome` mirrors the deck's outcome strings; `attempts` is
    1 or 2 (the practice UI allows two tries).
    """
    student_assignment = models.ForeignKey('StudentAssignment', on_delete=models.CASCADE, related_name="attempts")
    topic = models.ForeignKey('Topic', on_delete=models.SET_NULL, blank=True, null=True, related_name="assignment_attempts")
    problem_index = models.IntegerField()
    is_correct = models.BooleanField()
    attempts = models.IntegerField(default=1)
    outcome = models.CharField(max_length=20)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student_assignment", "problem_index"], name="unique_studentassignment_problem"),
        ]

    def __str__(self):
        return f"Attempt(sa={self.student_assignment_id} #{self.problem_index}, correct={self.is_correct})"


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
