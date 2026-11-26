from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название курса")
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    credits = models.PositiveSmallIntegerField(default=3)

    # Максимальное количество студентов на курсе
    max_students = models.PositiveSmallIntegerField(default=30)

    # courses you must pass before this one (course - course, many to many)
    prerequisites = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="required_for"
    )

    # Настройка весов оценивания (по умолчанию 0.6 и 0.4)
    midterm_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.60"),  # Decimal, а не float: 0.60 как float не проходит full_clean()
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Вес Midterm",
    )
    final_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.40"),
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Вес Final",
    )

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

    def clean(self):
        super().clean()
        # Валидация: сумма весов должна быть строго равна 1.0 (или 100%)
        if (
            self.midterm_weight is not None
            and self.final_weight is not None
            and float(self.midterm_weight + self.final_weight) != 1.0
        ):
            raise ValidationError(
                "Сумма midterm_weight и final_weight должна быть строго равна 1.0 (например, 0.6 и 0.4)"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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

    # Оценки студента с валидацией диапазона от 0 до 100
    midterm_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Балл за Midterm (0-100)",
    )
    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Балл за Final (0-100)",
    )

    grade = models.CharField(max_length=2, blank=True, null=True, verbose_name="Итоговая оценка")

    class Meta:
        # student can't join the same course twice
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_student_course"),
        ]

    @property
    def total_score(self):
        """Автоматический расчет итогового балла на основе весов курса."""
        return (
            self.midterm_score * self.course.midterm_weight
            + self.final_score * self.course.final_weight
        )

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

# grade C (2.0) or higher = course is passed
PASS_POINTS = 2.0


def has_passed(student, course):
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return False
    return GRADE_POINTS.get(enrollment.grade, 0) >= PASS_POINTS


# queue for a full course
class Waitlist(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="waitlist",
        limit_choices_to={"role": "student"},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="waitlist")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at", "id"]  # first come - first served
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_waitlist_student_course"),
        ]

    @property
    def position(self):
        # place in the queue: 1, 2, 3...
        return Waitlist.objects.filter(course=self.course, id__lte=self.id).count()

    def __str__(self):
        return f"{self.student} waits for {self.course.code}"


def promote_from_waitlist(course):
    """when a seat is free, first student in the queue is enrolled automatically"""
    promoted = []
    with transaction.atomic():
        while course.enrollments.count() < course.max_students:
            first = course.waitlist.select_related("student").first()
            if first is None:
                break
            Enrollment.objects.create(student=first.student, course=course)
            first.delete()
            Notification.objects.create(
                recipient=first.student,
                message=f"Место освободилось: вы записаны на курс {course.code} из листа ожидания.",
            )
            promoted.append(first.student)
    return promoted


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


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Получатель",
    )
    message = models.CharField(max_length=255, verbose_name="Текст уведомления")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"{self.recipient}: {self.message}"


def notify_deadline_approaching(assignment, days_left=1):
    """Напоминает студентам (без сдачи) и преподавателю о скором due_date."""
    if not assignment.due_date:
        return

    diff_days = (assignment.due_date - timezone.localdate()).days
    if 0 <= diff_days <= days_left:
        submitted_student_ids = set(
            assignment.submissions.values_list("student_id", flat=True)
        )
        enrollments = assignment.course.enrollments.select_related("student")

        for enrollment in enrollments:
            if enrollment.student_id not in submitted_student_ids:
                Notification.objects.get_or_create(
                    recipient=enrollment.student,
                    message=(
                        f"Скоро дедлайн ({assignment.due_date}) по заданию "
                        f"«{assignment.title}» ({assignment.course.code})."
                    ),
                )

        if assignment.course.teacher:
            Notification.objects.get_or_create(
                recipient=assignment.course.teacher,
                message=(
                    f"Дедлайн {assignment.due_date} по заданию «{assignment.title}» "
                    f"({assignment.course.code})."
                ),
            )


def notify_grade_and_threshold(enrollment, passing_score=Decimal("50.00")):
    """Уведомляет об оценке и предупреждает при нехватке баллов до проходного порога."""
    total = Decimal(str(enrollment.total_score)).quantize(Decimal("0.01"))

    Notification.objects.create(
        recipient=enrollment.student,
        message=(
            f"Обновлены баллы по курсу {enrollment.course.code}: "
            f"Midterm {enrollment.midterm_score}, Final {enrollment.final_score}, "
            f"итоговый балл {total}."
        ),
    )

    if total < passing_score:
        missing = (passing_score - total).quantize(Decimal("0.01"))
        Notification.objects.create(
            recipient=enrollment.student,
            message=(
                f"Не хватает {missing} балл(ов) до проходного порога ({passing_score}) "
                f"по курсу {enrollment.course.code}."
            ),
        )
        if enrollment.course.teacher:
            Notification.objects.create(
                recipient=enrollment.course.teacher,
                message=(
                    f"Студенту {enrollment.student} не хватает {missing} балл(ов) "
                    f"до проходного порога ({passing_score}) по курсу {enrollment.course.code}."
                ),
            )