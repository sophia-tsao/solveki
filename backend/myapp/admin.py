from django.contrib import admin
from .models import (
    Course, Topic, Settings, Classroom, ClassEnrollment, Assignment,
    AssignmentTopic, AssignmentClass, StudentAssignment,
)


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [TopicInline]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("topic_name", "course")
    list_filter = ("course",)


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