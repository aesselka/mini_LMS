from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (AssignmentViewSet, CourseViewSet, EnrollmentViewSet, LessonViewSet, NotificationViewSet,
                    SubmissionViewSet, WaitlistViewSet, my_courses, stats, transcript)

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register("lessons", LessonViewSet, basename="lesson")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("submissions", SubmissionViewSet, basename="submission")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("waitlist", WaitlistViewSet, basename="waitlist")

urlpatterns = [
    path("my-courses/", my_courses, name="my-courses"),
    path("stats/", stats, name="stats"),
    path("transcript/", transcript, name="transcript"),
] + router.urls
