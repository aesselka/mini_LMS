import csv
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from .models import User


@admin.action(description="Экспортировать выбранных пользователей в CSV")
def export_to_csv(modeladmin, request, queryset):
    if not queryset.exists():
        modeladmin.message_user(
            request,
            "Выберите хотя бы одного пользователя для экспорта.",
            level=messages.WARNING,
        )
        return

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="users_export.csv"'
    response.write("sep=;\n")

    writer = csv.writer(response, delimiter=";")
    writer.writerow(["ID", "Username", "Email", "Role", "Staff Status"])

    for user in queryset:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.role,
            user.is_staff,
        ])

    modeladmin.message_user(
        request,
        f"Экспортировано пользователей: {queryset.count()}.",
        level=messages.SUCCESS,
    )
    return response


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = UserAdmin.fieldsets + (
        ("Role Information", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role Information", {"fields": ("role",)}),
    )

    actions = [export_to_csv]