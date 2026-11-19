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

# total = 0.6 * midterm + 0.4 * final
MIDTERM_WEIGHT = 0.6
FINAL_WEIGHT = 0.4


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

    # GET /api/courses/my-standing/
    @action(detail=False, methods=["get"], url_path="my-standing",
            permission_classes=[permissions.IsAuthenticated])
    def my_standing(self, request):
        enrollments = (Enrollment.objects.filter(student=request.user)
                       .select_related("course", "course__teacher"))
        courses = [course_standing(e.course, request.user) for e in enrollments]
        return Response({
            "student": request.user.get_full_name() or request.user.username,
            "midterm_weight": MIDTERM_WEIGHT,
            "final_weight": FINAL_WEIGHT,
            "courses": courses,
        })


def final_needed(midterm_avg, target):
    # what final score gives this total
    needed = (target - MIDTERM_WEIGHT * midterm_avg) / FINAL_WEIGHT
    if needed > 100:
        return None  # not possible
    return max(round(needed, 1), 0)


def course_standing(course, student):
    assignments_total = course.assignments.count()
    submissions = Submission.objects.filter(assignment__course=course, student=student)
    graded = submissions.filter(score__isnull=False).select_related("assignment")

    # each work in percent: score / max_score * 100
    percents = [s.score / s.assignment.max_score * 100 for s in graded if s.assignment.max_score]
    avg = round(sum(percents) / len(percents), 1) if percents else None

    teacher = course.teacher
    return {
        "course_id": course.id,
        "code": course.code,
        "title": course.title,
        "credits": course.credits,
        "teacher": f"{teacher.first_name} {teacher.last_name}".strip() or teacher.username,
        "assignments_total": assignments_total,
        "submitted": submissions.count(),
        "graded": len(percents),
        "current_midterm_avg": avg,
        # how much midterm already gives to the total (max 60)
        "midterm_points": round(avg * MIDTERM_WEIGHT, 1) if avg is not None else None,
        # final score needed for scholarship (70) and high scholarship (90)
        "final_needed_for_70": final_needed(avg, 70) if avg is not None else None,
        "final_needed_for_90": final_needed(avg, 90) if avg is not None else None,
    }


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


# GET /api/transcript/
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def transcript(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related("course")

    courses = []
    total_points = 0
    graded_credits = 0
    for e in enrollments:
        credits = e.course.credits
        points = GRADE_POINTS.get(e.grade)  # None if no grade yet
        courses.append({
            "code": e.course.code,
            "title": e.course.title,
            "credits": credits,
            "grade": e.grade,
            "points": points,
        })
        # only graded courses count in gpa
        if points is not None:
            total_points += points * credits
            graded_credits += credits

    # gpa = sum(points * credits) / sum(credits)
    gpa = round(total_points / graded_credits, 2) if graded_credits else None

    return Response({
        "student": request.user.get_full_name() or request.user.username,
        "courses": courses,
        "total_credits": sum(c["credits"] for c in courses),
        "graded_credits": graded_credits,
        "gpa": gpa,
    })


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
