from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.

# This is a stub
class Organization(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField()
    bin = models.CharField()
    address = models.CharField()

#This is a stub
class Department(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField()
    organization_id = models.ForeignKey(to=Organization, null=False, on_delete=models.CASCADE)

class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'ADMIN'
        MANAGER = 'MANAGER'
        EMPLOYEE = 'EMPLOYEE'

    id = models.UUIDField(primary_key=True)
    username = models.CharField(null=False, unique=True)
    password = models.CharField(null=False)
    email = models.CharField(unique=True, null=False)
    first_name = models.CharField(null=False)
    last_name = models.CharField(null=False)
    patronymic = models.CharField()
    department_id = models.ForeignKey(to=Department, on_delete=models.SET_NULL, null=True)
    role = models.CharField(choices=Role.choices)

    def save(self, *args, **kwargs):
        if not self.id :
            self.id = uuid.uuid4()
        return super(User, self).save(*args, **kwargs)
    pass