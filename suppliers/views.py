from django.db.models import Sum
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from accounts.permissions import IsAdminRole
from training_requests.models import TrainingRequest
from .models import Contract, ContractAllocation, Supplier
from .serializers import ContractSerializer, SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by("-created_at")
    serializer_class = ContractSerializer

    @extend_schema(
        summary="Детальная аналитика по договору",
        description="Показывает лимит договора, факт списания по одобренным заявкам и остаток.",
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="ContractAnalyticsResponse",
                    fields={
                        "contract_id": serializers.UUIDField(),
                        "contract_number": serializers.CharField(),
                        "supplier": inline_serializer(
                            name="ContractAnalyticsSupplier",
                            fields={
                                "id": serializers.UUIDField(),
                                "name": serializers.CharField(),
                                "bin": serializers.CharField(),
                            },
                        ),
                        "total_amount": serializers.FloatField(),
                        "spent_amount": serializers.FloatField(),
                        "remaining_amount": serializers.FloatField(),
                        "spent_percent": serializers.IntegerField(),
                        "remaining_percent": serializers.IntegerField(),
                    },
                ),
                description="Аналитика по договору",
            ),
        },
        examples=[
            OpenApiExample(
                "ContractAnalyticsExample",
                value={
                    "contract_id": "f4b2d58e-e3d4-4d64-b73b-ecbcf7f9387a",
                    "contract_number": "CTR-2026-001",
                    "supplier": {
                        "id": "58bf81ed-b0f0-4e64-9fb4-46947689b322",
                        "name": "Tech Academy",
                        "bin": "123456789012",
                    },
                    "total_amount": 1000000.0,
                    "spent_amount": 400000.0,
                    "remaining_amount": 600000.0,
                    "spent_percent": 40,
                    "remaining_percent": 60,
                },
            )
        ],
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="analytics",
        permission_classes=[permissions.IsAuthenticated, IsAdminRole],
    )
    def analytics(self, request, pk=None):
        contract = self.get_object()
        spent_amount = (
            ContractAllocation.objects.filter(
                contract=contract,
                training_request__status=TrainingRequest.Status.APPROVED,
            ).aggregate(total=Sum("allocated_amount"))["total"]
            or 0
        )
        total_amount = contract.total_amount or 0
        remaining_amount = max(total_amount - spent_amount, 0)

        if total_amount > 0:
            spent_percent = round(float(spent_amount * 100 / total_amount))
        else:
            spent_percent = 0
        remaining_percent = 100 - spent_percent

        return Response(
            {
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "supplier": {
                    "id": contract.supplier_id,
                    "name": contract.supplier.name,
                    "bin": contract.supplier.bin,
                },
                "total_amount": float(total_amount),
                "spent_amount": float(spent_amount),
                "remaining_amount": float(remaining_amount),
                "spent_percent": spent_percent,
                "remaining_percent": remaining_percent,
            }
        )


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
