from django.contrib import admin
from django.db.models import Sum
from .models import Supplier, Contract, ContractAllocation


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "bin", "phone", "email")
    search_fields = ("name", "bin")


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("contract_number", "supplier", "total_amount", "get_remaining_money", "start_date", "end_date")
    list_filter = ("supplier", "start_date")
    search_fields = ("contract_number",)

    def get_remaining_money(self, obj):
        # Вместо obj.allocations используем прямой запрос к модели списаний
        spent = ContractAllocation.objects.filter(contract=obj).aggregate(Sum('allocated_amount'))[
                    'allocated_amount__sum'] or 0
        remaining = obj.total_amount - spent
        return f"{remaining:,.2f} / {obj.total_amount:,.2f}"

    get_remaining_money.short_description = "Остаток / Лимит"


@admin.register(ContractAllocation)
class ContractAllocationAdmin(admin.ModelAdmin):
    list_display = ("contract", "allocated_amount", "created_at")

    # Запрещаем редактировать вручную для чистоты данных
    def has_add_permission(self, request):
        return False