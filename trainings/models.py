import uuid
from django.db import models


class Training(models.Model):
    class TrainingType(models.TextChoices):
        SEMINAR = "SEMINAR", "Семинар"
        TRAINING = "TRAINING", "Тренинг"
        CERTIFICATION = "CERTIFICATION", "Сертификация"

    class PricingType(models.TextChoices):
        PER_PERSON = "PER_PERSON", "За человека"
        PER_GROUP = "PER_GROUP", "За группу"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # СВЯЗЬ С ПОСТАВЩИКОМ
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.CASCADE,
        related_name="trainings",
        verbose_name="Поставщик",
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255, verbose_name="Название")
    type = models.CharField(max_length=20, choices=TrainingType.choices, verbose_name="Тип")
    trainer_name = models.CharField(max_length=255, verbose_name="Тренер")
    description = models.TextField(blank=True, verbose_name="Описание")

    pricing_type = models.CharField(max_length=20, choices=PricingType.choices, verbose_name="Тип цены")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Цена")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Обучение"
        verbose_name_plural = "Обучения"


class TrainingSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    training = models.ForeignKey(
        "trainings.Training", on_delete=models.CASCADE, related_name="sessions", verbose_name="Курс"
    )
    start_date = models.DateTimeField(verbose_name="Дата и время начала")
    end_date = models.DateTimeField(verbose_name="Дата и время окончания")
    location = models.CharField(max_length=255, verbose_name="Место")
    city = models.CharField(max_length=100, verbose_name="Город")
    capacity = models.IntegerField(verbose_name="Вместимость")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.training.title} ({self.start_date})"

    class Meta:
        verbose_name = "Сессия обучения"
        verbose_name_plural = "Сессии обучения"
