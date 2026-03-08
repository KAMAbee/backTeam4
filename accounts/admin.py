from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Department, Organization, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Добавляем поле email на форму СОЗДАНИЯ пользователя (ту, что на скриншоте)
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'first_name', 'last_name', 'department')}),
    )

    # Добавляем поля на форму РЕДАКТИРОВАНИЯ пользователя
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('patronymic', 'department', 'role')}),
    )

    list_display = ("username", "email", "first_name", "last_name", "role")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "bin", "address")
    search_fields = ("name", "bin")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "organization")
    search_fields = ("name",)