from rest_framework import permissions

from .models import Course


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == "admin")


def is_teacher(user):
    return user.is_authenticated and user.role == "teacher"


def can_manage_course(user, course):
    # admin or teacher of this course
    return is_admin(user) or course.teacher_id == user.id


def visible_courses(user):
    # admin - all, teacher - own, student - enrolled
    if is_admin(user):
        return Course.objects.all()
    if is_teacher(user):
        return Course.objects.filter(teacher=user)
    return Course.objects.filter(enrollments__student=user)


# everyone can view, only admin/teacher can change
class IsAdminOrTeacherOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_admin(request.user) or is_teacher(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # teacher can edit only own course
        return is_admin(request.user) or obj.teacher_id == request.user.id


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)
