import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Название")
    bin = models.CharField(max_length=20, verbose_name="БИН")
    address = models.CharField(max_length=255, verbose_name="Адрес")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Название")
    organization = models.ForeignKey(
        to="accounts.Organization", 
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name="Организация"
    )

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    class Meta:
        verbose_name = "Департамент"
        verbose_name_plural = "Департаменты"

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Администратор"
        MANAGER = "MANAGER", "Менеджер"
        EMPLOYEE = "EMPLOYEE", "Сотрудник"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=False, verbose_name="Email")
    patronymic = models.CharField(max_length=150, blank=True, verbose_name="Отчество")
    department = models.ForeignKey(
        to="accounts.Department", 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="users",
        verbose_name="Департамент"
    )
    role = models.CharField(max_length=20, choices=Role.choices, verbose_name="Роль")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.username})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
