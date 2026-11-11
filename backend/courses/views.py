from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count, Q
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import GRADE_POINTS, Assignment, Course, Enrollment, Lesson, Submission
from .permissions import (IsAdmin, IsAdminOrTeacherOrReadOnly, can_manage_course,
                          is_admin, is_teacher, visible_courses)
from .serializers import (AssignmentSerializer, CourseSerializer, EnrollmentSerializer,
                          GradeSerializer, LessonSerializer, MyCourseSerializer,
                          ScoreSerializer, SubmissionSerializer)

User = get_user_model()


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

    # PATCH /api/enrollments/<id>/grade/
    @action(detail=True, methods=["patch"])
    def grade(self, request, pk=None):
        enrollment = self.get_object()
        if not can_manage_course(request.user, enrollment.course):
            raise PermissionDenied("only the teacher of this course can set grades")
        data = GradeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        enrollment.grade = data.validated_data["grade"]
        enrollment.save()
        return Response(EnrollmentSerializer(enrollment).data)


# GET /api/my-courses/
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_courses(request):
    enrollments = (Enrollment.objects.filter(student=request.user)
                   .select_related("course", "course__teacher"))
    return Response(MyCourseSerializer(enrollments, many=True).data)


# base for lessons and assignments: same access rules
class CourseContentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    model = None

    def get_queryset(self):
        items = self.model.objects.filter(course__in=visible_courses(self.request.user))
        # filter by course: ?course=1
        course = self.request.query_params.get("course")
        if course:
            items = items.filter(course_id=course)
        return items

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        # only admin or teacher of the course can change
        if request.method not in permissions.SAFE_METHODS and not can_manage_course(request.user, obj.course):
            raise PermissionDenied("only the teacher of this course can change it")

    def create(self, request, *args, **kwargs):
        if not (is_admin(request.user) or is_teacher(request.user)):
            raise PermissionDenied("only teachers can add this")
        return super().create(request, *args, **kwargs)


# /api/lessons/
class LessonViewSet(CourseContentViewSet):
    serializer_class = LessonSerializer
    model = Lesson


# /api/assignments/
class AssignmentViewSet(CourseContentViewSet):
    serializer_class = AssignmentSerializer
    model = Assignment


# /api/submissions/
class SubmissionViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        items = Submission.objects.select_related("student", "assignment", "assignment__course")
        if is_admin(user):
            pass
        elif is_teacher(user):
            items = items.filter(assignment__course__teacher=user)
        else:
            items = items.filter(student=user)
        # filter by assignment: ?assignment=1
        assignment = self.request.query_params.get("assignment")
        if assignment:
            items = items.filter(assignment_id=assignment)
        return items

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError("you already submitted this assignment")

    # PATCH /api/submissions/<id>/score/
    @action(detail=True, methods=["patch"])
    def score(self, request, pk=None):
        submission = self.get_object()
        if not can_manage_course(request.user, submission.assignment.course):
            raise PermissionDenied("only the teacher of this course can set score")
        data = ScoreSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        if data.validated_data["score"] > submission.assignment.max_score:
            raise ValidationError(f"max score is {submission.assignment.max_score}")
        submission.score = data.validated_data["score"]
        submission.save()
        return Response(SubmissionSerializer(submission).data)


def average_grade(grades):
    # letters -> points -> average
    points = [GRADE_POINTS[g] for g in grades if g in GRADE_POINTS]
    if not points:
        return None
    return round(sum(points) / len(points), 2)


# GET /api/stats/  (admin only)
@api_view(["GET"])
@permission_classes([IsAdmin])
def stats(request):
    courses = []
    for course in Course.objects.annotate(students_count=Count("enrollments")):
        grades = course.enrollments.values_list("grade", flat=True)
        courses.append({
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "students_count": course.students_count,
            "average_grade": average_grade(grades),
        })

    popular = sorted(courses, key=lambda c: c["students_count"], reverse=True)[:3]

    return Response({
        "total_courses": Course.objects.count(),
        "total_students": User.objects.filter(role="student").count(),
        "total_teachers": User.objects.filter(role="teacher").count(),
        "total_enrollments": Enrollment.objects.count(),
        "average_grade": average_grade(Enrollment.objects.values_list("grade", flat=True)),
        "popular_courses": popular,
        "courses": courses,
    })
