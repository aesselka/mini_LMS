from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Course, Enrollment
from .permissions import is_admin

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
