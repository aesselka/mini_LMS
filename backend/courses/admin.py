from django.contrib import admin
from .models import Course, Enrollment, Lesson, Assignment, Submission

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title', 'teacher', 'midterm_weight', 'final_weight', 'created_at')
    search_fields = ('title', 'code')
    list_filter = ('teacher',)
    # Поля, которые можно редактировать в админке
    fields = ('title', 'code', 'description', 'credits', 'teacher', 'midterm_weight', 'final_weight')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'midterm_score', 'final_score', 'total_score', 'grade', 'enroll_date')
    search_fields = ('student__username', 'course__title', 'course__code')
    list_filter = ('course', 'grade')
    
    # Делаем total_score доступным для просмотра в админке
    readonly_fields = ('total_score', 'enroll_date')
    fields = ('student', 'course', 'midterm_score', 'final_score', 'total_score', 'grade')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'title', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'title', 'due_date', 'max_score', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'assignment', 'score', 'submitted_at')
    list_filter = ('assignment__course',)
    search_fields = ('student__username', 'assignment__title')