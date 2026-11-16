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


# grade letters and their points (for average grade)
GRADE_POINTS = {
    "A": 4.0, "A-": 3.67,
    "B+": 3.33, "B": 3.0, "B-": 2.67,
    "C+": 2.33, "C": 2.0, "C-": 1.67,
    "D+": 1.33, "D": 1.0,
    "F": 0.0,
}


# one course - many lessons
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course", "order"]

    def __str__(self):
        return f"{self.course.code}: {self.title}"


# one course - many assignments
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(blank=True, null=True)
    max_score = models.PositiveSmallIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course", "due_date"]

    def __str__(self):
        return f"{self.course.code}: {self.title}"


# student's answer to an assignment
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        limit_choices_to={"role": "student"},
    )
    answer = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        # student can submit one assignment only once
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_assignment_student"),
        ]

    def __str__(self):
        return f"{self.student} -> {self.assignment.title}"
