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


from drf_spectacular.utils import extend_schema, extend_schema_view

from rest_framework import viewsets, permissions, status, mixins

@extend_schema_view(
    list=extend_schema(summary="Список всех заявок", description="Позволяет получить список заявок. Админы видят все, менеджеры - только свои."),
    create=extend_schema(summary="Создание новой заявки", description="Менеджер создает заявку на обучение для списка сотрудников."),
    retrieve=extend_schema(summary="Детальная информация о заявке"),
)
class TrainingRequestViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    """
    Управление жизненным циклом заявок на обучение.
    Поддерживает создание, просмотр и специальные действия (одобрение/отклонение).
    Редактирование и удаление запрещены для сохранения целостности данных.
    """
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

    @extend_schema(
        summary="Одобрение заявки (HR)",
        description="Администратор одобряет заявку, выбирая контракт. Проверяется бюджет и вместимость сессии.",
        responses={200: TrainingRequestSerializer}
    )
    @action(detail=True, methods=["POST"], serializer_class=ApproveRequestSerializer)
    def approve(self, request, pk=None):
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "Только администраторы могут одобрять запросы."}, status=status.HTTP_403_FORBIDDEN)
        
        with transaction.atomic():
            # Захватываем блокировку на строку запроса, чтобы несколько людей подряд не могли использовать заявку
            try:
                training_request = TrainingRequest.objects.select_for_update(nowait=True).get(pk=pk)
            except TrainingRequest.DoesNotExist:
                return Response({"detail": "Запрос не найден."}, status=status.HTTP_404_NOT_FOUND)
            except transaction.TransactionManagementError:
                return Response({"detail": "Запрос обрабатывается другим пользователем."}, status=status.HTTP_409_CONFLICT)
            
            if training_request.status != TrainingRequest.Status.PENDING:
                return Response({"detail": "Запрос уже был обработан."}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Захватываем блокировку на строку контракта для безопасного расчета бюджета
            contract = Contract.objects.select_for_update().get(pk=serializer.validated_data["contract"].id)
            
            employees = training_request.employees.all()
            if not employees.exists():
                return Response({"detail": "Запрос не содержит сотрудников."}, status=status.HTTP_400_BAD_REQUEST)
            
            training_session = training_request.training_session
            training = training_session.training
            
            # Проверка вместимости сессии
            current_enrollments_count = TrainingEnrollment.objects.filter(training_session=training_session).count()
            if current_enrollments_count + employees.count() > training_session.capacity:
                return Response({
                    "detail": f"Недостаточно мест в сессии. Доступно: {training_session.capacity - current_enrollments_count}, Требуется: {employees.count()}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Проверка, не зачислены ли сотрудники уже
            already_enrolled = TrainingEnrollment.objects.filter(
                training_session=training_session,
                employee__in=[re.employee for re in employees]
            )
            if already_enrolled.exists():
                names = ", ".join([f"{e.employee.first_name} {e.employee.last_name}" for e in already_enrolled])
                return Response({
                    "detail": f"Следующие сотрудники уже зачислены на этот курс: {names}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Расчет стоимости
            if training.pricing_type == Training.PricingType.PER_PERSON:
                total_cost = training.price * employees.count()
            else:
                total_cost = training.price
                
            # Проверка бюджета
            allocated_sum = ContractAllocation.objects.filter(contract=contract).aggregate(total=Sum("allocated_amount"))["total"] or Decimal(0)
            remaining_budget = contract.total_amount - allocated_sum
            
            if remaining_budget < total_cost:
                return Response({
                    "detail": f"Недостаточно средств по контракту. Требуется: {total_cost}, Доступно: {remaining_budget}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Выделение бюджета
            ContractAllocation.objects.create(
                contract=contract,
                training_request=training_request,
                allocated_amount=total_cost
            )
            
            # Зачисление
            enrollments_to_create = [
                TrainingEnrollment(
                    training_session=training_session,
                    employee=req_employee.employee,
                    request=training_request
                ) for req_employee in employees
            ]
            TrainingEnrollment.objects.bulk_create(enrollments_to_create)
            
            # Обновление статуса
            training_request.status = TrainingRequest.Status.APPROVED
            training_request.save()
            
        return Response(TrainingRequestSerializer(training_request).data)

    @extend_schema(
        summary="Отмена заявки (Менеджер)",
        description="Менеджер отменяет свою заявку, пока она находится в статусе PENDING.",
        request=None,
        responses={200: TrainingRequestSerializer}
    )
    @action(detail=True, methods=["POST"])
    def cancel(self, request, pk=None):
        training_request = self.get_object()
        
        if training_request.manager != request.user:
            return Response({"detail": "Вы не можете отменить чужую заявку."}, status=status.HTTP_403_FORBIDDEN)
            
        if training_request.status != TrainingRequest.Status.PENDING:
            return Response({"detail": "Можно отменить только заявку в ожидании (PENDING)."}, status=status.HTTP_400_BAD_REQUEST)
            
        training_request.status = TrainingRequest.Status.CANCELLED
        training_request.save()
        
        return Response(TrainingRequestSerializer(training_request).data)

    @extend_schema(
        summary="Отклонение заявки (HR)",
        description="Администратор отклоняет заявку. Статус меняется на REJECTED.",
        request=None,
        responses={200: TrainingRequestSerializer}
    )
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
