from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "bin", "phone", "email")
    search_fields = ("name", "bin")