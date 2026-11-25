from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (GRADE_POINTS, Assignment, Course, Enrollment, Lesson, Notification, Submission,
                     Waitlist, has_passed)
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
    seats_left = serializers.SerializerMethodField()
    # send list of course ids: {"prerequisites": [1, 3]}
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all(), required=False
    )
    prerequisite_codes = serializers.SerializerMethodField()
    waitlist_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "code", "title", "description", "credits", "max_students",
                  "seats_left", "waitlist_count", "prerequisites", "prerequisite_codes",
                  "teacher", "teacher_id", "students_count", "created_at"]

    def get_prerequisite_codes(self, course):
        return [c.code for c in course.prerequisites.all()]

    def get_waitlist_count(self, course):
        return course.waitlist.count()

    def validate_prerequisites(self, value):
        # course can't require itself
        if self.instance and self.instance in value:
            raise serializers.ValidationError("course can't be its own prerequisite")
        return value

    def get_seats_left(self, course):
        count = getattr(course, "students_count", None)
        if count is None:
            count = course.enrollments.count()
        return max(course.max_students - count, 0)

    def validate_max_students(self, value):
        # can't make limit smaller than students already enrolled
        if self.instance and value < self.instance.enrollments.count():
            raise serializers.ValidationError("limit is less than enrolled students")
        return value

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

        course = attrs["course"]
        check_prerequisites(attrs["student"], course)

        # check free seats
        if course.enrollments.count() >= course.max_students:
            raise serializers.ValidationError("course is full")
        return attrs


def check_prerequisites(student, course):
    # all required courses must be passed with C or higher
    missing = [c.code for c in course.prerequisites.all() if not has_passed(student, c)]
    if missing:
        raise serializers.ValidationError(
            f"you need to pass {', '.join(missing)} first (grade C or higher)"
        )


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


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]
        read_only_fields = fields



class WaitlistSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField(read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    position = serializers.IntegerField(read_only=True)

    class Meta:
        model = Waitlist
        fields = ["id", "student", "course", "course_code", "position", "joined_at"]
        read_only_fields = ["joined_at"]
        validators = []  # checks are done below

    def validate(self, attrs):
        user = self.context["request"].user
        course = attrs["course"]
        if user.role != "student":
            raise serializers.ValidationError("only students can join the waitlist")
        if course.enrollments.filter(student=user).exists():
            raise serializers.ValidationError("you are already enrolled in this course")
        if Waitlist.objects.filter(student=user, course=course).exists():
            raise serializers.ValidationError("you are already in the waitlist")
        # waitlist only for a full course
        if course.enrollments.count() < course.max_students:
            raise serializers.ValidationError("course has free seats, just enroll")
        check_prerequisites(user, course)
        attrs["student"] = user
        return attrs
