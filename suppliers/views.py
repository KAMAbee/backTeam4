from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Contract, ContractAllocation, Supplier
from .serializers import ContractSerializer, SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by("-created_at")
    serializer_class = ContractSerializer


@api_view(["GET"])
def budget_summary(request):
    total_contract_amount = (
        Contract.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    )

    allocated_total = (
        ContractAllocation.objects.aggregate(total=Sum("allocated_amount"))["total"]
        or 0
    )

    remaining_budget = total_contract_amount - allocated_total

    return Response(
        {
            "total_contract_amount": total_contract_amount,
            "allocated_total": allocated_total,
            "remaining_budget": remaining_budget,
        }
    )