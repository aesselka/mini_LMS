from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (AssignmentViewSet, CourseViewSet, EnrollmentViewSet, LessonViewSet,
                    SubmissionViewSet, my_courses, stats)

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register("lessons", LessonViewSet, basename="lesson")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("submissions", SubmissionViewSet, basename="submission")

urlpatterns = [
    path("my-courses/", my_courses, name="my-courses"),
    path("stats/", stats, name="stats"),
] + router.urls
