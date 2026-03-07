from django.db import models
import uuid


class TrainingRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"
        CANCELLED = "CANCELLED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    manager = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="managed_training_requests",
    )
    training_session = models.ForeignKey(
        "trainings.TrainingSession",
        on_delete=models.CASCADE,
        related_name="training_requests",
    )

    status = models.CharField(max_length=20, choices=Status.choices)
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class TrainingRequestEmployee(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    training_request = models.ForeignKey(
        "training_requests.TrainingRequest",
        on_delete=models.CASCADE,
        related_name="employees",
    )
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="training_request_participations",
    )

    class Meta:
        # Один и тот же сотрудник не должен дублироваться в одном запросе.
        unique_together = ("training_request", "employee")

