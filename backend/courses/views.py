from django.db import IntegrityError
from django.db.models import Count, Q
from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Course, Enrollment
from .permissions import IsAdminOrTeacherOrReadOnly, is_admin, is_teacher
from .serializers import CourseSerializer, EnrollmentSerializer


# /api/courses/
class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrTeacherOrReadOnly]

    def get_queryset(self):
        courses = Course.objects.select_related("teacher").annotate(
            students_count=Count("enrollments")
        )

        # search by title, code or teacher
        search = self.request.query_params.get("search")
        if search:
            courses = courses.filter(
                Q(title__icontains=search)
                | Q(code__icontains=search)
                | Q(teacher__first_name__icontains=search)
                | Q(teacher__last_name__icontains=search)
            )
        return courses


# /api/enrollments/
class EnrollmentViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        enrollments = Enrollment.objects.select_related("student", "course")
        if is_admin(user):
            return enrollments
        if is_teacher(user):
            return enrollments.filter(course__teacher=user)
        return enrollments.filter(student=user)

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            # db unique constraint as a backup
            raise ValidationError("student is already enrolled in this course")

    def perform_destroy(self, instance):
        # student can delete only own enrollment
        if not (is_admin(self.request.user) or instance.student == self.request.user):
            raise PermissionDenied("you can't delete this enrollment")
        instance.delete()
