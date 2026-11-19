import csv
from django.http import HttpResponse
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 1. Функция экспорта выбранных пользователей в CSV
@admin.action(description='Экспортировать выбранных пользователей в CSV')
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    # Записываем заголовки столбцов
    writer.writerow(['ID', 'Username', 'Email', 'Role', 'Staff Status'])
    
    # Записываем данные каждого выбранного пользователя
    for user in queryset:
        writer.writerow([user.id, user.username, user.email, user.role, user.is_staff])
        
    return response

# 2. Настройка админки пользователей
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    
    # Отображение поля role в интерфейсе админки
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
    # Добавляем действие экспорта в список доступных кнопок в админке
    actions = [export_to_csv]