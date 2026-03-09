from datetime import date, datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from suppliers.models import Contract, ContractAllocation, Supplier
from training_requests.models import TrainingRequest, TrainingRequestEmployee
from trainings.models import Training, TrainingSession


def dt(y, m, d, h=9, minute=0):
    return timezone.make_aware(datetime(y, m, d, h, minute))


class ContractAnalyticsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_contracts",
            email="admin_contracts@example.com",
            password="password123",
            first_name="Admin",
            last_name="Contracts",
            role=User.Role.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager_contracts",
            email="manager_contracts@example.com",
            password="password123",
            first_name="Manager",
            last_name="Contracts",
            role=User.Role.MANAGER,
        )
        self.employee = User.objects.create_user(
            username="employee_contracts",
            email="employee_contracts@example.com",
            password="password123",
            first_name="Employee",
            last_name="Contracts",
            role=User.Role.EMPLOYEE,
        )

    def _auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_contract_analytics_auth(self):
        supplier = Supplier.objects.create(name="Supplier A", bin="111111111111")
        contract = Contract.objects.create(
            supplier=supplier,
            contract_number="CTR-AUTH-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            total_amount="1000000.00",
        )
        url = f"/api/suppliers/contracts/{contract.id}/analytics/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        manager_response = self._auth_client(self.manager).get(url)
        self.assertEqual(manager_response.status_code, status.HTTP_403_FORBIDDEN)

        employee_response = self._auth_client(self.employee).get(url)
        self.assertEqual(employee_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_contract_analytics_values(self):
        supplier = Supplier.objects.create(name="Supplier Analytics", bin="123456789012")
        contract = Contract.objects.create(
            supplier=supplier,
            contract_number="CTR-AN-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            total_amount="1000000.00",
        )
        training = Training.objects.create(
            supplier=supplier,
            title="Python Backend",
            type=Training.TrainingType.TRAINING,
            trainer_name="Trainer 1",
            pricing_type=Training.PricingType.PER_PERSON,
            price="100000.00",
        )
        session = TrainingSession.objects.create(
            training=training,
            start_date=dt(2026, 2, 10, 9, 0),
            end_date=dt(2026, 2, 12, 18, 0),
            location="Office",
            city="Almaty",
            capacity=20,
        )
        employee1 = User.objects.create_user(
            username="employee_contract_1",
            email="employee_contract_1@example.com",
            password="password123",
            first_name="Emp",
            last_name="One",
            role=User.Role.EMPLOYEE,
        )
        employee2 = User.objects.create_user(
            username="employee_contract_2",
            email="employee_contract_2@example.com",
            password="password123",
            first_name="Emp",
            last_name="Two",
            role=User.Role.EMPLOYEE,
        )

        request1 = TrainingRequest.objects.create(
            manager=self.manager,
            training_session=session,
            status=TrainingRequest.Status.APPROVED,
            comment="Approved 1",
        )
        request2 = TrainingRequest.objects.create(
            manager=self.manager,
            training_session=session,
            status=TrainingRequest.Status.APPROVED,
            comment="Approved 2",
        )
        request3 = TrainingRequest.objects.create(
            manager=self.manager,
            training_session=session,
            status=TrainingRequest.Status.PENDING,
            comment="Pending",
        )

        TrainingRequestEmployee.objects.create(training_request=request1, employee=employee1)
        TrainingRequestEmployee.objects.create(training_request=request2, employee=employee2)

        ContractAllocation.objects.create(
            contract=contract,
            training_request=request1,
            allocated_amount="100000.00",
        )
        ContractAllocation.objects.create(
            contract=contract,
            training_request=request2,
            allocated_amount="300000.00",
        )
        ContractAllocation.objects.create(
            contract=contract,
            training_request=request3,
            allocated_amount="250000.00",
        )

        url = f"/api/suppliers/contracts/{contract.id}/analytics/"
        response = self._auth_client(self.admin).get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["contract_id"]), str(contract.id))
        self.assertEqual(response.data["contract_number"], contract.contract_number)
        self.assertEqual(str(response.data["supplier"]["id"]), str(supplier.id))
        self.assertEqual(response.data["supplier"]["name"], supplier.name)
        self.assertEqual(response.data["supplier"]["bin"], supplier.bin)
        self.assertEqual(response.data["total_amount"], 1000000.0)
        self.assertEqual(response.data["spent_amount"], 400000.0)
        self.assertEqual(response.data["remaining_amount"], 600000.0)
        self.assertEqual(response.data["spent_percent"], 40)
        self.assertEqual(response.data["remaining_percent"], 60)
