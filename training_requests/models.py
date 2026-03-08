import uuid
from django.db import models

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
        "training_requests.TrainingRequest",
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
