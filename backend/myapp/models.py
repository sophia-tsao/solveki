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
    # The practice card's "Learn more" link: a video or resource that teaches the
    # topic. Admin-editable; seed_topics only fills it while blank (defaults in
    # learn_more.py), so an admin's choice survives reseeding. Blank = no link.
    learn_more_url = models.URLField(max_length=500, blank=True, default="")

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

    A topic usually appears several times in a day's deck. Its SM-2 schedule
    moves once per day, by the grade for all of that day's answers on it (see
    `srs.grade_day`).

    To apply that without compounding, this stores a snapshot of the topic's
    SM-2 state *before* the day's first answer (`snapshot_*`). Every answer
    recomputes the TopicReview from the snapshot and the day's answers so far,
    so the day's net effect is always one review from a single fixed base.
    `applied_quality` is the quality that recompute last gave; `early` records
    whether the topic wasn't due yet when the day started (an early pass leaves
    the schedule alone); `floor_interval` is set when finishing an assignment
    today lifted the topic to "familiar" (see `practice.GRADUATION_INTERVAL`),
    so later recomputes keep that lift.
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_topic_grades")
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="daily_grades")
    date = models.DateField()
    applied_quality = models.IntegerField()  # SM-2 quality from today's answers so far
    snapshot_ease = models.FloatField()
    snapshot_interval = models.IntegerField()
    snapshot_repetitions = models.IntegerField()
    snapshot_due_date = models.DateField(blank=True, null=True)
    early = models.BooleanField(default=False)
    floor_interval = models.IntegerField(default=0)

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
    deck size at that moment (`min(len(problems), questions_per_day)`, or more
    while an assignment is open — matching what the deck view reports). The day counts as completed when
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

class AnswerRecord(models.Model):
    """One answered practice card: its topic, how it went, and how long it took.

    `DailyTopicGrade` keeps only the worst grade per topic per day (for the SM-2
    once-per-day rule) and `DailyPractice` only counts cards, so neither can say
    how often a student got cards right or how long they spent. This
    append-only log, written on each graded deck advance, backs the teacher
    views' accuracy, time-spent and "struggled with most" figures.

    `outcome` is the advance's reported outcome (see `srs.CREDIT`).
    `seconds` is the client-measured time from the card appearing to the
    student answering it, capped server-side so a tab left open doesn't count
    as hours of review; 0 when the client didn't report it.
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answer_records")
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name="answer_records")
    date = models.DateField()
    outcome = models.CharField(max_length=20)
    seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "date"])]

    def __str__(self):
        return f"Answer({self.user} -> {self.topic} on {self.date}: {self.outcome})"

class ProblemReport(models.Model):
    """A student's report that a practice card's question or solution was wrong.

    Filed from the incorrect back face of a card ("Report issue"), which also
    grades the card as correct (`correct_first`) so a faulty problem doesn't
    drag the topic's schedule down. The card's problem and solution are
    snapshotted here from the server-side deck — decks are pruned daily, and
    generated problems aren't stored anywhere else — so an admin can see
    exactly what was shown. Reviewed from the Django admin; `resolved` lets
    them tick reports off.

    `topic` is SET_NULL so a report outlives its topic being deleted.
    `user_answer` is the student's last answer to the card, when the client sent it.
    """
    ANSWER_MARKED_WRONG = "answer_marked_wrong"
    SOLUTION_INCORRECT = "solution_incorrect"
    OTHER = "other"
    REASON_CHOICES = [
        (ANSWER_MARKED_WRONG, "My answer was correct/equivalent but marked incorrect"),
        (SOLUTION_INCORRECT, "Solveki's solution is incorrect"),
        (OTHER, "Other"),
    ]

    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="problem_reports")
    topic = models.ForeignKey('Topic', blank=True, null=True, on_delete=models.SET_NULL, related_name="problem_reports")
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True, default="")
    problem = models.TextField()
    solution = models.TextField()
    # The step-by-step explanation the student was shown, so a "solution is
    # incorrect" report can be checked against it too.
    steps = models.JSONField(default=list, blank=True)
    user_answer = models.CharField(max_length=500, blank=True, default="")
    date = models.DateField()  # the student's local day the card was from
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report({self.user} -> {self.topic} on {self.date}: {self.reason})"

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
    students' spaced-repetition decks (stored as `AssignmentTopic` rows) and the
    fewest cards the student must answer on them (`deck_size`). Assigning it to a
    class (or a student joining a class that has it) adds its topics to the
    student's own selections and spreads its cards over their daily decks until
    it's due; the student practices through their normal deck, so SM-2 always
    schedules the work. A student who isn't solid on the topics after
    `deck_size` cards gets more, up to `practice.MAX_CARDS_MULTIPLIER` times as
    many — see `StudentAssignment`. `allow_late` decides whether cards answered
    after the due date still count. The assignment's topics also drive its
    familiarity report.

    An assignment is authored once and handed to classes through
    `AssignmentClass`, so editing/deleting it affects every class it reached.
    """
    teacher = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_assignments")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    deck_size = models.IntegerField(default=10)
    allow_late = models.BooleanField(default=True)
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
    """A student's progress on one assignment, created when it reaches them.

    The row is created, in progress, when the assignment is assigned to the
    student's class or they join a class that has it (its topics are added to
    their selections and their deck grows to cover the assignment's remaining
    cards). Opening it just routes the student to their normal practice page, so
    there's no separate assignment quiz to store. Every card the student answers
    in their deck while the assignment is in progress bumps `cards_answered`,
    if it's on one of the assignment's topics (cards
    after the due date only count if the assignment allows late work).
    `cards_needed` starts at the assignment's `deck_size` and grows while a
    topic isn't solid (see `practice.cards_needed`); the row is completed when
    the student is solid after `deck_size` cards, or at the maximum
    (`max_reached`, shown to the teacher as "needs help"). `completion_pct` is
    the teacher-facing progress and never goes down; `late` marks completion
    after the due date. Familiarity on the assignment's topics is still read
    from the SM-2 state for the teacher's report.
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
    cards_answered = models.IntegerField(default=0)
    cards_needed = models.IntegerField(default=0)  # 0 until the first card: read as deck_size
    completion_pct = models.IntegerField(default=0)
    max_reached = models.BooleanField(default=False)
    late = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    # The day the student chose "Finish it now": it counts as the assignment's
    # last day, so all its remaining cards are due then (see `deck._days_left`).
    finish_on = models.DateField(blank=True, null=True)
    # Cards the student has stepped past in this assignment's own decks, on any
    # topic, and the reviews of other topics among them: the assignment's
    # decks hold at most `practice.max_cards` cards over its life.
    deck_answered = models.IntegerField(default=0)
    review_answered = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_assignment_student"),
        ]

    def __str__(self):
        return f"StudentAssignment({self.student} :: {self.assignment}, {self.status})"


class DailyDeck(models.Model):
    """A set of problems generated for a single day, for a single user.

    A student has a default deck (`assignment` null), used while no assignment
    is open, and one deck per assignment they open that day (see
    `deck.DeckScope`).
    """
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="decks")
    date = models.DateField()
    assignment = models.ForeignKey(
        "Assignment", null=True, blank=True, on_delete=models.CASCADE, related_name="decks"
    )
    problems = models.JSONField(default=list)
    current_index = models.IntegerField(default=0)
    # Wrong answers submitted for the current card (see check_answer). Kept
    # server-side so the solution is only revealed once attempts run out, and
    # reset whenever the current card changes.
    attempts = models.IntegerField(default=0)
    # Set when the user's topic selection changes so the unanswered tail is
    # rebuilt lazily on the next practice-page load (see _mark_deck_stale /
    # _get_or_create_today_deck) rather than synchronously on every toggle.
    needs_regen = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"], condition=models.Q(assignment__isnull=True),
                name="unique_user_date_deck",
            ),
            models.UniqueConstraint(
                fields=["user", "date", "assignment"], condition=models.Q(assignment__isnull=False),
                name="unique_user_date_assignment_deck",
            ),
        ]

    def __str__(self):
        return f"Deck {self.user} {self.date} ({self.current_index}/{len(self.problems)})"
