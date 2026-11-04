from django.conf import settings
from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название курса")
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    credits = models.PositiveSmallIntegerField(default=3)
    # one teacher - many courses
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses_taught",
        limit_choices_to={"role": "teacher"},
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"


# bridge table between students and courses
class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "student"},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enroll_date = models.DateField(auto_now_add=True)
    grade = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        # student can't join the same course twice
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_student_course"),
        ]

    def __str__(self):
        return f"{self.student} -> {self.course.code}"
