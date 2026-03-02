from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.

# This is a stub
class Organization(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    bin = models.CharField(max_length=20)
    address = models.CharField(max_length=255)

#This is a stub
class Department(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    organization_id = models.ForeignKey(to=Organization, null=False, on_delete=models.CASCADE)

class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'ADMIN'
        MANAGER = 'MANAGER'
        EMPLOYEE = 'EMPLOYEE'

    id = models.UUIDField(primary_key=True)
    username = models.CharField(max_length=150, null=False, unique=True)
    password = models.CharField(max_length=255, null=False)
    email = models.CharField(max_length=255, unique=True, null=False)
    first_name = models.CharField(max_length=150, null=False)
    last_name = models.CharField(max_length=150, null=False)
    patronymic = models.CharField(max_length=150, blank=True)
    department_id = models.ForeignKey(to=Department, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=20, choices=Role.choices)

    def save(self, *args, **kwargs):
        if not self.id :
            self.id = uuid.uuid4()
        return super(User, self).save(*args, **kwargs)
    pass

#training modelka eto snizu

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
    type = models.CharField(
        max_length=20,
        choices=TrainingType.choices
    )
    trainer_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    pricing_type = models.CharField(
        max_length=20,
        choices=PricingType.choices
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trainings"

    def __str__(self):
        return self.title

#eto training sessiya uje
class TrainingSession(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    training = models.ForeignKey(
        Training,
        on_delete=models.CASCADE,
        related_name="sessions"
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

class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_name = models.CharField(max_length=255)
    supplier_id = models.UUIDField(null=True, blank=True)
    contract_number = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contracts"

    def __str__(self):
        return self.contract_number


class ContractAllocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    training_request_id = models.UUIDField(null=True, blank=True)
    allocated_amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contract_allocations"

    def __str__(self):
        return f"{self.contract_id} | {self.allocated_amount}"