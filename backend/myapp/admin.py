from django.contrib import admin
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from .models import (
    Course, Topic, Settings, Classroom, ClassEnrollment, Assignment,
    AssignmentTopic, AssignmentClass, StudentAssignment, ProblemReport,
)


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [TopicInline]


# The "Learn more" link is edited here (seed_topics only fills blank links), so
# it's editable straight from the topic list.
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("topic_name", "course", "generator_name", "learn_more_url")
    list_editable = ("learn_more_url",)
    list_filter = ("course",)
    search_fields = ("topic_name", "generator_name")


# Roles are changed from the admin (the /settings/role/ endpoint only lets a
# user set their own role once), so expose it here.
@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "role_chosen", "questions_per_day")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")


class ClassEnrollmentInline(admin.TabularInline):
    model = ClassEnrollment
    extra = 0


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "join_code", "archived")
    list_filter = ("archived",)
    inlines = [ClassEnrollmentInline]


class AssignmentTopicInline(admin.TabularInline):
    model = AssignmentTopic
    extra = 0


class AssignmentClassInline(admin.TabularInline):
    model = AssignmentClass
    extra = 0


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "deck_size")
    inlines = [AssignmentTopicInline, AssignmentClassInline]


@admin.register(StudentAssignment)
class StudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("student", "assignment", "classroom", "status")
    list_filter = ("status",)


# Student reports of a wrong question/solution, filed from the practice card's
# "Report issue" button. Everything but `resolved` is a record of what the
# student saw and said, so it's read-only; admins tick `resolved` from the list.
@admin.register(ProblemReport)
class ProblemReportAdmin(admin.ModelAdmin):
    list_display = (
        "created_at", "reason", "topic", "course", "user",
        "problem_text", "solution_text", "student_answer", "resolved",
    )
    list_editable = ("resolved",)
    list_filter = ("resolved", "reason", "topic__course", "date")
    search_fields = (
        "details", "problem", "solution", "user_answer",
        "topic__topic_name", "user__username", "user__email",
    )
    date_hierarchy = "created_at"
    list_select_related = ("topic__course", "user")
    readonly_fields = (
        "user", "topic", "course", "reason", "details",
        "problem_text", "solution_text", "steps_text", "student_answer", "date", "created_at",
    )
    fields = readonly_fields + ("resolved",)

    @admin.display(description="Course", ordering="topic__course__course_name")
    def course(self, obj):
        return obj.topic.course if obj.topic else None

    # Problems and solutions are stored with the `$...$` math delimiters the
    # card renders with KaTeX; drop them so "$1+1=$" reads as "1+1=".
    @admin.display(description="Problem", ordering="problem")
    def problem_text(self, obj):
        return obj.problem.replace("$", "")

    @admin.display(description="Solveki's solution", ordering="solution")
    def solution_text(self, obj):
        return obj.solution.replace("$", "")

    @admin.display(description="Steps shown")
    def steps_text(self, obj):
        if not obj.steps:
            return "—"
        lines = []
        for i, step in enumerate(obj.steps, 1):
            line = f"{i}. {step.get('text', '').replace('$', '')}"
            if step.get("math"):
                line += f"  [{step['math']}]"
            lines.append(line)
        return format_html_join(mark_safe("<br>"), "{}", ((line,) for line in lines))

    @admin.display(description="Student's answer", ordering="user_answer")
    def student_answer(self, obj):
        return obj.user_answer or "—"

    def has_add_permission(self, request):
        return False
