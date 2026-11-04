from rest_framework import permissions


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == "admin")


def is_teacher(user):
    return user.is_authenticated and user.role == "teacher"


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
