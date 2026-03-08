from django.db.models import Sum
from rest_framework import viewsets, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer

from .models import Contract, ContractAllocation, Supplier
from .serializers import ContractSerializer, SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by("-created_at")
    serializer_class = ContractSerializer


@extend_schema(
    summary="Общая сводка по бюджету",
    description="Возвращает общую сумму всех контрактов, сумму потраченных средств и остаток бюджета.",
    responses={
        200: inline_serializer(
            name='BudgetSummaryResponse',
            fields={
                'total_contract_amount': serializers.FloatField(),
                'allocated_total': serializers.FloatField(),
                'remaining_budget': serializers.FloatField(),
            }
        )
    }
)
@api_view(["GET"])
def budget_summary(request):
    # Считаем общую сумму всех заключенных контрактов
    total_contract_amount = (
        Contract.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    )

    # Считаем, сколько денег уже заблокировано/списано под заявки
    allocated_total = (
        ContractAllocation.objects.aggregate(total=Sum("allocated_amount"))["total"]
        or 0
    )

    remaining_budget = total_contract_amount - allocated_total

    return Response(
        {
            "total_contract_amount": float(total_contract_amount),
            "allocated_total": float(allocated_total),
            "remaining_budget": float(remaining_budget),
        }
    )