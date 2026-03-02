from django.db import models

# Create your models here.
import uuid


class Training(models.Model):
    class TrainingType(models.TextChoices):
        ONLINE = "ONLINE"
        OFFLINE = "OFFLINE"
        HYBRID = "HYBRID"

    class PricingType(models.TextChoices):
        PER_PERSON = "PER_PERSON"
        PER_GROUP = "PER_GROUP"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TrainingType.choices)
    trainer_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    pricing_type = models.CharField(max_length=20, choices=PricingType.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trainings"

    def __str__(self):
        return self.title


class TrainingSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    training = models.ForeignKey(
        "trainings.Training", on_delete=models.CASCADE, related_name="sessions"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)

    capacity = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "training_sessions"

    def __str__(self):
        return f"{self.training.title} ({self.start_date})"
