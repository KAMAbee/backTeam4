from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import TrainingRequest, TrainingRequestEmployee
from .serializers import TrainingRequestSerializer, ApproveRequestSerializer
from trainings.models import Training
from suppliers.models import Contract, ContractAllocation
from enrollments.models import TrainingEnrollment
from accounts.models import User


class TrainingRequestViewSet(viewsets.ModelViewSet):
    queryset = TrainingRequest.objects.all().prefetch_related("employees__employee", "training_session__training")
    serializer_class = TrainingRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return TrainingRequest.objects.all().prefetch_related("employees__employee", "training_session__training")
        return TrainingRequest.objects.filter(manager=user).prefetch_related("employees__employee", "training_session__training")

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.MANAGER and self.request.user.role != User.Role.ADMIN:
            raise ValidationError("Только менеджеры могут создавать запросы на обучение.")
        serializer.save()

    @action(detail=True, methods=["POST"], serializer_class=ApproveRequestSerializer)
    def approve(self, request, pk=None):
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "Только администраторы могут одобрять запросы."}, status=status.HTTP_403_FORBIDDEN)
        
        training_request = self.get_object()
        
        if training_request.status != TrainingRequest.Status.PENDING:
            return Response({"detail": "Запрос уже был обработан."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = serializer.validated_data["contract"]
        
        employees = training_request.employees.all()
        if not employees.exists():
            return Response({"detail": "Запрос не содержит сотрудников."}, status=status.HTTP_400_BAD_REQUEST)
        
        training_session = training_request.training_session
        training = training_session.training
        
        # Calculate cost
        if training.pricing_type == Training.PricingType.PER_PERSON:
            total_cost = training.price * employees.count()
        else:
            total_cost = training.price
            
        # Check budget
        allocated_sum = ContractAllocation.objects.filter(contract=contract).aggregate(total=Sum("allocated_amount"))["total"] or Decimal(0)
        remaining_budget = contract.total_amount - allocated_sum
        
        if remaining_budget < total_cost:
            return Response({
                "detail": f"Недостаточно средств по контракту. Требуется: {total_cost}, Доступно: {remaining_budget}"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            # Allocate budget
            ContractAllocation.objects.create(
                contract=contract,
                training_request=training_request,
                allocated_amount=total_cost
            )
            
            # Create enrollments, avoid duplicates
            enrollments_to_create = []
            for req_employee in employees:
                if not TrainingEnrollment.objects.filter(
                    training_session=training_session,
                    employee=req_employee.employee
                ).exists():
                    enrollments_to_create.append(
                        TrainingEnrollment(
                            training_session=training_session,
                            employee=req_employee.employee,
                            request=training_request
                        )
                    )
            
            TrainingEnrollment.objects.bulk_create(enrollments_to_create)
            
            # Update status
            training_request.status = TrainingRequest.Status.APPROVED
            training_request.save()
            
        return Response(TrainingRequestSerializer(training_request).data)

    @action(detail=True, methods=["POST"])
    def reject(self, request, pk=None):
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "Только администраторы могут отклонять запросы."}, status=status.HTTP_403_FORBIDDEN)
            
        training_request = self.get_object()
        
        if training_request.status != TrainingRequest.Status.PENDING:
            return Response({"detail": "Запрос уже был обработан."}, status=status.HTTP_400_BAD_REQUEST)
            
        training_request.status = TrainingRequest.Status.REJECTED
        training_request.save()
        
        return Response(TrainingRequestSerializer(training_request).data)
