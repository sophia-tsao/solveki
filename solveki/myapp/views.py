from django.shortcuts import render
from django.http import HttpResponse
from .models import Course, Topic
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from mathgenerator import gen_by_name
import random
import json

def index(request):
    return render(request, "myapp/index.html")
def view_courses(request):
    courses=list(Course.objects.all().values())
    return JsonResponse({"courses":courses})
def view_course_topics(request, courseID):
    # Returns topics for specific course
    topics = list(Course.objects.get(id=courseID).topics.all().values())
    return JsonResponse({"topics":topics})
@csrf_exempt
@require_http_methods(["PATCH"])
def toggle_topic(request, topicID):
    try:
        topic = Topic.objects.get(id=topicID)
    except Topic.DoesNotExist:
        return JsonResponse({"error": "Topic not found"}, status=404)
    body = json.loads(request.body)
    topic.is_selected = body["is_selected"]
    topic.save(update_fields=["is_selected"])
    if topic.course:
        all_selected = not topic.course.topics.filter(is_selected=False).exists()
        topic.course.is_selected = all_selected
        topic.course.save(update_fields=["is_selected"])
    return JsonResponse({"id": topic.id, "is_selected": topic.is_selected})

@csrf_exempt
@require_http_methods(["PATCH"])
def set_course_topics_selected(request, courseID):
    try:
        course = Course.objects.get(id=courseID)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)
    body = json.loads(request.body)
    new_value = body["is_selected"]
    course.topics.all().update(is_selected=new_value)
    course.is_selected = new_value
    course.save(update_fields=["is_selected"])
    return JsonResponse({"course_id": courseID, "is_selected": new_value})

def generate_problem(request):
    generators = list(
        Topic.objects.filter(is_selected=True)
        .exclude(generator_name__isnull=True)
        .values_list("generator_name", flat=True)
    )
    if not generators:
        return JsonResponse({"no_topics": True})
    name = random.choice(generators)
    problem, solution = gen_by_name(name)

    sol_str = str(solution).strip().replace('$', '').strip()
    try:
        sol_float = float(sol_str)
        if '.' in sol_str:
            rounded = round(sol_float, 3)
            rounded_str = str(rounded)
            if rounded_str != sol_str:
                problem = problem.rstrip() + " Round to the nearest thousandth if necessary."
            solution = rounded_str
    except (ValueError, TypeError):
        pass

    return JsonResponse({"problem": problem, "solution": str(solution)})
