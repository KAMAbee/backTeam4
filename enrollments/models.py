import uuid
from django.db import models

class TrainingEnrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    training_session = models.ForeignKey(
        "trainings.TrainingSession",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Сессия обучения"
    )
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="training_enrollments",
        verbose_name="Сотрудник"
    )
    request = models.ForeignKey(
        "training_requests.TrainingRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
        verbose_name="Заявка"
    )

    # Сценарий Г: Результаты обучения
    is_attended = models.BooleanField(
        default=False,
        verbose_name="Присутствовал"
    )
    certificate_file = models.FileField(
        upload_to='certificates/',
        null=True,
        blank=True,
        verbose_name="Скан сертификата"
    )
    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Номер удостоверения"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата записи")

    class Meta:
        verbose_name = "Зачисление"
        verbose_name_plural = "Зачисления"
        unique_together = ('training_session', 'employee') # Чтобы нельзя было записать одного человека дважды на одну сессию

    def __str__(self):
        status = "✅" if self.is_attended else "❌"
        return f"{self.employee.username} | {self.training_session} | {status}"