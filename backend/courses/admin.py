from django.contrib import admin
from .models import Course, Enrollment  # Добавили Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'code', 'teacher', 'created_at')  # Добавили code и teacher[cite: 13]
    search_fields = ('title', 'code')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'enrolled_at')