from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import GRADE_POINTS, Assignment, Course, Enrollment, Lesson, Submission
from .permissions import can_manage_course, is_admin

User = get_user_model()


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class CourseSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    # admin sends teacher_id when creating a course
    teacher_id = serializers.PrimaryKeyRelatedField(
        source="teacher",
        queryset=User.objects.filter(role="teacher"),
        write_only=True,
        required=False,
    )
    students_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "code", "title", "description", "credits",
                  "teacher", "teacher_id", "students_count", "created_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        creating = self.instance is None
        if is_admin(user):
            if creating and "teacher" not in attrs:
                raise serializers.ValidationError({"teacher_id": "teacher is required"})
        else:
            # teacher creates course only for himself
            attrs["teacher"] = user if creating else self.instance.teacher
        return attrs


class EnrollmentSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField(read_only=True)
    # only admin can enroll another student
    student_id = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=User.objects.filter(role="student"),
        write_only=True,
        required=False,
    )
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_id", "course", "course_title", "enroll_date", "grade"]
        read_only_fields = ["enroll_date", "grade"]
        validators = []  # duplicate check is done below

    def validate(self, attrs):
        user = self.context["request"].user
        if user.role == "student":
            attrs["student"] = user
        elif not is_admin(user):
            raise serializers.ValidationError("only students can enroll")
        elif "student" not in attrs:
            raise serializers.ValidationError({"student_id": "student is required"})

        # check duplicate enrollment
        if Enrollment.objects.filter(student=attrs["student"], course=attrs["course"]).exists():
            raise serializers.ValidationError("student is already enrolled in this course")
        return attrs


class GradeSerializer(serializers.Serializer):
    grade = serializers.CharField(allow_blank=True, allow_null=True)

    def validate_grade(self, value):
        if not value:
            return None  # empty = remove grade
        value = value.upper()
        if value not in GRADE_POINTS:
            raise serializers.ValidationError("grade must be one of: " + ", ".join(GRADE_POINTS))
        return value


# student's course with grade (for my-courses page)
class MyCourseSerializer(serializers.ModelSerializer):
    enrollment_id = serializers.IntegerField(source="id")
    course_id = serializers.IntegerField(source="course.id")
    code = serializers.CharField(source="course.code")
    title = serializers.CharField(source="course.title")
    credits = serializers.IntegerField(source="course.credits")
    teacher = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ["enrollment_id", "course_id", "code", "title", "credits",
                  "teacher", "enroll_date", "grade"]

    def get_teacher(self, obj):
        t = obj.course.teacher
        return f"{t.first_name} {t.last_name}".strip() or t.username


# check that user can add lessons/assignments to this course
class CourseOwnedSerializer(serializers.ModelSerializer):
    def validate_course(self, course):
        if not can_manage_course(self.context["request"].user, course):
            raise serializers.ValidationError("you are not the teacher of this course")
        return course


class LessonSerializer(CourseOwnedSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "course", "title", "content", "order", "created_at"]


class AssignmentSerializer(CourseOwnedSerializer):
    class Meta:
        model = Assignment
        fields = ["id", "course", "title", "description", "due_date", "max_score", "created_at"]


class SubmissionSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField(read_only=True)
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)

    class Meta:
        model = Submission
        fields = ["id", "assignment", "assignment_title", "student", "answer", "submitted_at", "score"]
        read_only_fields = ["submitted_at", "score"]
        validators = []  # duplicate check is done below

    def validate(self, attrs):
        user = self.context["request"].user
        assignment = attrs["assignment"]
        if user.role != "student":
            raise serializers.ValidationError("only students can submit")
        # student must be enrolled in the course
        if not assignment.course.enrollments.filter(student=user).exists():
            raise serializers.ValidationError("you are not enrolled in this course")
        # check duplicate submission
        if Submission.objects.filter(assignment=assignment, student=user).exists():
            raise serializers.ValidationError("you already submitted this assignment")
        attrs["student"] = user
        return attrs


class ScoreSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0)
