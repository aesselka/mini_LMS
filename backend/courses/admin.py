from django.contrib import admin, messages
from .models import (
    Assignment,
    Course,
    Enrollment,
    Lesson,
    Notification,
    Submission,
    notify_deadline_approaching,
    notify_grade_and_threshold,
)


@admin.action(description="Проверить дедлайны и отправить напоминания")
def check_assignment_deadlines(modeladmin, request, queryset):
    for assignment in queryset.select_related("course", "course__teacher"):
        notify_deadline_approaching(assignment, days_left=1)
    modeladmin.message_user(
        request,
        f"Проверка дедлайнов выполнена для заданий: {queryset.count()}.",
        level=messages.SUCCESS,
    )


@admin.action(description="Отправить уведомления об оценках и пороге")
def send_grade_notifications(modeladmin, request, queryset):
    for enrollment in queryset.select_related("student", "course", "course__teacher"):
        notify_grade_and_threshold(enrollment)
    modeladmin.message_user(
        request,
        f"Уведомления по оценкам сформированы для записей: {queryset.count()}.",
        level=messages.SUCCESS,
    )


@admin.action(description="Отметить выбранные уведомления как прочитанные")
def mark_notifications_as_read(modeladmin, request, queryset):
    updated = queryset.update(is_read=True)
    modeladmin.message_user(
        request,
        f"Отмечено прочитанными: {updated}.",
        level=messages.SUCCESS,
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("recipient__username", "message")
    readonly_fields = ("created_at",)
    actions = [mark_notifications_as_read]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "title", "teacher", "midterm_weight", "final_weight", "created_at")
    search_fields = ("title", "code")
    list_filter = ("teacher",)
    # Поля, которые можно редактировать в админке
    fields = ("title", "code", "description", "credits", "max_students", "teacher", "midterm_weight", "final_weight")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "course", "midterm_score", "final_score", "total_score", "grade", "enroll_date")
    search_fields = ("student__username", "course__title", "course__code")
    list_filter = ("course", "grade")
    actions = [send_grade_notifications]

    # Делаем total_score доступным для просмотра в админке
    readonly_fields = ("total_score", "enroll_date")
    fields = ("student", "course", "midterm_score", "final_score", "total_score", "grade")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "title", "order", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "course__title")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "title", "due_date", "max_score", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    actions = [check_assignment_deadlines]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "assignment", "score", "submitted_at")
    list_filter = ("assignment__course",)
    search_fields = ("student__username", "assignment__title")