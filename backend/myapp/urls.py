from django.urls import path
from . import views
urlpatterns = [
    path('auth/me/', views.me, name="me"),
    path('auth/google/', views.google_login, name="google_login"),
    path('auth/test-login/', views.test_login, name="test_login"),
    path('auth/logout/', views.logout_view, name="logout"),
    path('auth/delete/', views.delete_account, name="delete_account"),
    path('problem/', views.generate_problem, name="generate_problem"),
    path('deck/', views.get_deck, name="get_deck"),
    path('deck/advance/', views.advance_deck, name="advance_deck"),
    path('dashboard/', views.view_dashboard, name="view_dashboard"),
    path('practice-calendar/', views.view_practice_calendar, name="view_practice_calendar"),
    path('settings/', views.settings_view, name="settings_view"),
    path('settings/role/', views.set_role, name="set_role"),
    path('courses/', views.view_courses, name="view_courses"),
    path('topics/', views.view_topics, name="view_topics"),
    path('courses/<int:courseID>/topics', views.view_course_topics, name="view_course_topics"),
    path('courses/<int:courseID>/select', views.set_course_topics_selected, name="set_course_topics_selected"),
    path('topics/<int:topicID>/select', views.toggle_topic, name="toggle_topic"),
    path('diagnostic/config/', views.diagnostic_config, name="diagnostic_config"),
    path('diagnostic/start/', views.diagnostic_start, name="diagnostic_start"),
    path('diagnostic/submit/', views.diagnostic_submit, name="diagnostic_submit"),

    # Classes (teacher-owned) and student membership.
    path('classes/', views.classes, name="classes"),
    path('classes/join/', views.join_class, name="join_class"),
    path('classes/mine/', views.my_classes, name="my_classes"),
    path('classes/<int:class_id>/', views.class_detail, name="class_detail"),
    path('classes/<int:class_id>/students/', views.class_students, name="class_students"),
    path('classes/<int:class_id>/students/<int:student_id>/', views.remove_student, name="remove_student"),

    # Assignments: teacher authoring + analytics.
    path('assignments/', views.assignments, name="assignments"),
    path('assignments/mine/', views.my_assignments, name="my_assignments"),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name="assignment_detail"),
    path('assignments/<int:assignment_id>/assign/', views.assign_to_classes, name="assign_to_classes"),
    path('assignments/<int:assignment_id>/results/', views.assignment_results, name="assignment_results"),
    # Student starting an assignment (routes them to their practice deck).
    path('assignments/<int:assignment_id>/play/', views.play_assignment, name="play_assignment"),

    # Teacher analytics.
    path('teacher/overview/', views.teacher_overview, name="teacher_overview"),
    path('teacher/proficiency-history/', views.proficiency_history, name="proficiency_history"),
    path('teacher/students/<int:student_id>/', views.student_detail, name="student_detail"),
]
