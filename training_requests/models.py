import uuid
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction, models as django_models
from django.utils import timezone

class TrainingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Ожидание"
        APPROVED = "APPROVED", "Одобрено"
        REJECTED = "REJECTED", "Отклонено"
        CANCELLED = "CANCELLED", "Отменено"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manager = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="managed_training_requests",
        verbose_name="Менеджер"
    )
    training_session = models.ForeignKey(
        "trainings.TrainingSession",
        on_delete=models.CASCADE,
        related_name="training_requests",
        verbose_name="Сессия обучения"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Заявка {self.id} ({self.status})"

    class Meta:
        verbose_name = "Заявка на обучение"
        verbose_name_plural = "Заявки на обучение"


class TrainingRequestEmployee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training_request = models.ForeignKey(
        TrainingRequest,
        on_delete=models.CASCADE,
        related_name="employees",
        verbose_name="Заявка"
    )
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="training_request_participations",
        verbose_name="Сотрудник"
    )

    class Meta:
        unique_together = ("training_request", "employee")
        verbose_name = "Сотрудник в заявке"
        verbose_name_plural = "Сотрудники в заявке"


@receiver(post_save, sender=TrainingRequest)
def handle_training_request_status_change(sender, instance, **kwargs):
    if instance.status == TrainingRequest.Status.APPROVED:
        from enrollments.models import TrainingEnrollment
        from suppliers.models import Contract, ContractAllocation
        from django.db.models import Sum

        with transaction.atomic():
            employees = instance.employees.all()
            employee_count = employees.count()

            if employee_count == 0:
                return

            total_cost = instance.training_session.training.price * employee_count
            target_supplier = instance.training_session.training.supplier

            if not target_supplier:
                return

            now = timezone.now()
            # Ищем активный контракт
            contract = Contract.objects.filter(
                supplier=target_supplier,
                start_date__lte=now,
                end_date__gte=now
            ).first()

            if contract:
                # Считаем сколько уже потрачено по этому контракту (сумма всех Allocation)
                spent = ContractAllocation.objects.filter(contract=contract).aggregate(Sum('allocated_amount'))['allocated_amount__sum'] or 0
                available = contract.total_amount - spent

                if available >= total_cost:
                    # Денег хватает — списываем
                    ContractAllocation.objects.update_or_create(
                        training_request=instance,
                        defaults={'contract': contract, 'allocated_amount': total_cost}
                    )
                    # Создаем зачисления (Enrollments)
                    for req_emp in employees:
                        TrainingEnrollment.objects.get_or_create(
                            employee=req_emp.employee,
                            training_session=instance.training_session
                        )
                    print(f"Успех: Списано {total_cost}. Остаток: {available - total_cost}")
                else:
                    print(f"Ошибка: Недостаточно средств. Нужно {total_cost}, осталось {available}")