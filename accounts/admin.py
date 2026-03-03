from django.contrib import admin

from django.contrib.auth.admin import UserAdmin

from .models import Department, Organization, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "bin", "address")
    search_fields = ("name", "bin")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "organization_id")
    search_fields = ("name",)
