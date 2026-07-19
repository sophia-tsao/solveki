from django.urls import path
from . import views
urlpatterns = [
    path('auth/me/', views.me, name="me"),
    path('auth/google/', views.google_login, name="google_login"),
    path('auth/logout/', views.logout_view, name="logout"),
    path('auth/delete/', views.delete_account, name="delete_account"),
    path('problem/', views.generate_problem, name="generate_problem"),
    path('deck/', views.get_deck, name="get_deck"),
    path('deck/advance/', views.advance_deck, name="advance_deck"),
    path('settings/', views.settings_view, name="settings_view"),
    path('courses/', views.view_courses, name="view_courses"),
    path('courses/<int:courseID>/topics', views.view_course_topics, name="view_course_topics"),
    path('courses/<int:courseID>/select', views.set_course_topics_selected, name="set_course_topics_selected"),
    path('topics/<int:topicID>/select', views.toggle_topic, name="toggle_topic"),
]
