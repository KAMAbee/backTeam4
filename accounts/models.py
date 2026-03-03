from django.db import models

# Create your models here.
import uuid
from django.contrib.auth.models import AbstractUser


class Organization(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    bin = models.CharField(max_length=20)
    address = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()
        return super().save(*args, **kwargs)


class Department(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        to="accounts.Organization", null=False, on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()
        return super().save(*args, **kwargs)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN"
        MANAGER = "MANAGER"
        EMPLOYEE = "EMPLOYEE"

    id = models.UUIDField(primary_key=True)
    username = models.CharField(max_length=150, null=False, unique=True)
    password = models.CharField(max_length=255, null=False)
    email = models.CharField(max_length=255, unique=True, null=False)
    first_name = models.CharField(max_length=150, null=False)
    last_name = models.CharField(max_length=150, null=False)
    patronymic = models.CharField(max_length=150, blank=True)
    department = models.ForeignKey(
        to="accounts.Department", on_delete=models.SET_NULL, null=True
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()
        return super().save(*args, **kwargs)
