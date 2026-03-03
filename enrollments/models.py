from django.db import models
import uuid


class TrainingEnrollment(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    training_session = models.ForeignKey(
        "trainings.TrainingSession",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="training_enrollments",
    )
    request = models.ForeignKey(
        "training_requests.TrainingRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
    )

    created_at = models.DateTimeField(auto_now_add=True)

