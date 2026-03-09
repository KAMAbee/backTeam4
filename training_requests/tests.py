from datetime import date

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from suppliers.models import Contract, Supplier
from training_requests.models import TrainingRequest, TrainingRequestEmployee
from trainings.models import Training, TrainingSession


class TrainingRequestContractSupplierValidationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_tr",
            email="admin_tr@example.com",
            password="password123",
            first_name="Admin",
            last_name="TR",
            role=User.Role.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager_tr",
            email="manager_tr@example.com",
            password="password123",
            first_name="Manager",
            last_name="TR",
            role=User.Role.MANAGER,
        )
        self.employee = User.objects.create_user(
            username="employee_tr",
            email="employee_tr@example.com",
            password="password123",
            first_name="Employee",
            last_name="TR",
            role=User.Role.EMPLOYEE,
        )

        self.supplier_a = Supplier.objects.create(name="Supplier A", bin="222222222222")
        self.supplier_b = Supplier.objects.create(name="Supplier B", bin="333333333333")

        self.contract_a = Contract.objects.create(
            supplier=self.supplier_a,
            contract_number="CTR-A-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            total_amount="500000.00",
        )
        self.contract_b = Contract.objects.create(
            supplier=self.supplier_b,
            contract_number="CTR-B-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            total_amount="500000.00",
        )

        training_b = Training.objects.create(
            supplier=self.supplier_b,
            title="Data Analysis",
            type=Training.TrainingType.TRAINING,
            trainer_name="Trainer B",
            pricing_type=Training.PricingType.PER_PERSON,
            price="50000.00",
        )
        self.session_b = TrainingSession.objects.create(
            training=training_b,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 2),
            location="Campus",
            city="Astana",
            capacity=10,
        )

    def _auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_contract_supplier_mismatch_on_create(self):
        payload = {
            "training_session": str(self.session_b.id),
            "employee_ids": [str(self.employee.id)],
            "comment": "Need approval",
            "contract": str(self.contract_a.id),
        }

        response = self._auth_client(self.manager).post(
            "/api/training-requests/",
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Selected contract does not belong to training supplier", str(response.data))

    def test_contract_supplier_match_on_approve(self):
        training_request = TrainingRequest.objects.create(
            manager=self.manager,
            training_session=self.session_b,
            status=TrainingRequest.Status.PENDING,
            comment="Pending request",
        )
        TrainingRequestEmployee.objects.create(
            training_request=training_request,
            employee=self.employee,
        )

        response = self._auth_client(self.admin).post(
            f"/api/training-requests/{training_request.id}/approve/",
            data={"contract": str(self.contract_b.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("Selected contract does not belong to training supplier", str(response.data))

    def test_contract_supplier_mismatch_on_approve(self):
        training_request = TrainingRequest.objects.create(
            manager=self.manager,
            training_session=self.session_b,
            status=TrainingRequest.Status.PENDING,
            comment="Pending request",
        )
        TrainingRequestEmployee.objects.create(
            training_request=training_request,
            employee=self.employee,
        )

        response = self._auth_client(self.admin).post(
            f"/api/training-requests/{training_request.id}/approve/",
            data={"contract": str(self.contract_a.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Selected contract does not belong to training supplier", str(response.data))
