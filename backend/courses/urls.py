from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = router.urls
