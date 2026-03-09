from datetime import date, datetime
from decimal import Decimal
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from suppliers.models import Contract, Supplier, ContractAllocation
from training_requests.models import TrainingRequest, TrainingRequestEmployee
from trainings.models import Training, TrainingSession
from enrollments.models import TrainingEnrollment

def dt(y, m, d, h=9, minute=0):
    return timezone.make_aware(datetime(y, m, d, h, minute))

class TrainingRequestWorkflowTests(APITestCase):
    def setUp(self):
        # Пользователи с уникальными email
        self.admin = User.objects.create_user(
            username="admin_tr", email="admin_tr@test.com", role=User.Role.ADMIN, password="password123"
        )
        self.manager = User.objects.create_user(
            username="manager_tr", email="manager_tr@test.com", role=User.Role.MANAGER, password="password123"
        )
        self.employee = User.objects.create_user(
            username="employee_tr", email="employee_tr@test.com", role=User.Role.EMPLOYEE, password="password123"
        )

        # Поставщики
        self.supplier_a = Supplier.objects.create(name="Supplier A", bin="111111111111")
        self.supplier_b = Supplier.objects.create(name="Supplier B", bin="222222222222")

        # Контракты
        self.contract_a = Contract.objects.create(
            supplier=self.supplier_a,
            contract_number="CTR-A-2026",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            total_amount=Decimal("1000000.00")
        )
        self.contract_b_short = Contract.objects.create(
            supplier=self.supplier_b,
            contract_number="CTR-B-SHORT",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1), # Короткий срок
            total_amount=Decimal("500000.00")
        )
        self.contract_b_valid = Contract.objects.create(
            supplier=self.supplier_b,
            contract_number="CTR-B-VALID",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            total_amount=Decimal("500000.00")
        )

        # Тренинг и Сессия (Поставщик B)
        self.training_b = Training.objects.create(
            supplier=self.supplier_b,
            title="Advanced Data Science",
            type=Training.TrainingType.TRAINING,
            trainer_name="Dr. Smith",
            pricing_type=Training.PricingType.PER_PERSON,
            price=Decimal("50000.00")
        )
        self.session_b = TrainingSession.objects.create(
            training=self.training_b,
            start_date=dt(2026, 3, 10),
            end_date=dt(2026, 3, 12),
            location="Room 101",
            city="Almaty",
            capacity=10
        )

    def _auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_manager_creates_request_successfully(self):
        """Менеджер успешно создает заявку (без контракта)."""
        payload = {
            "training_session": str(self.session_b.id),
            "employee_ids": [str(self.employee.id)],
            "comment": "Team needs this"
        }
        response = self._auth_client(self.manager).post(
            "/api/training-requests/", data=payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrainingRequest.objects.count(), 1)
        self.assertEqual(TrainingRequest.objects.first().status, TrainingRequest.Status.PENDING)

    def test_admin_approves_with_correct_contract(self):
        """Админ успешно одобряет заявку с подходящим контрактом."""
        # Создаем заявку
        request_obj = TrainingRequest.objects.create(
            manager=self.manager, training_session=self.session_b, status=TrainingRequest.Status.PENDING
        )
        TrainingRequestEmployee.objects.create(training_request=request_obj, employee=self.employee)

        payload = {"contract": str(self.contract_b_valid.id)}
        response = self._auth_client(self.admin).post(
            f"/api/training-requests/{request_obj.id}/approve/", data=payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверка 1: Статус изменился
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, TrainingRequest.Status.APPROVED)

        # Проверка 2: Деньги списались (ContractAllocation)
        allocation = ContractAllocation.objects.get(training_request=request_obj)
        self.assertEqual(allocation.contract, self.contract_b_valid)
        self.assertEqual(allocation.allocated_amount, Decimal("50000.00"))

        # Проверка 3: Сотрудник зачислен
        self.assertTrue(TrainingEnrollment.objects.filter(employee=self.employee, training_session=self.session_b).exists())

    def test_admin_cannot_approve_with_mismatched_supplier(self):
        """Админ НЕ может одобрить заявку контрактом ДРУГОГО поставщика."""
        request_obj = TrainingRequest.objects.create(
            manager=self.manager, training_session=self.session_b, status=TrainingRequest.Status.PENDING
        )
        TrainingRequestEmployee.objects.create(training_request=request_obj, employee=self.employee)

        # Пытаемся привязать Контракт А (Поставщик А) к Тренингу Б (Поставщик Б)
        payload = {"contract": str(self.contract_a.id)}
        response = self._auth_client(self.admin).post(
            f"/api/training-requests/{request_obj.id}/approve/", data=payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("принадлежит поставщику", response.data["detail"])

    def test_admin_cannot_approve_with_expired_contract(self):
        """Админ НЕ может одобрить заявку, если срок контракта не покрывает сессию."""
        request_obj = TrainingRequest.objects.create(
            manager=self.manager, training_session=self.session_b, status=TrainingRequest.Status.PENDING
        )
        TrainingRequestEmployee.objects.create(training_request=request_obj, employee=self.employee)

        # Сессия в марте, контракт только до февраля
        payload = {"contract": str(self.contract_b_short.id)}
        response = self._auth_client(self.admin).post(
            f"/api/training-requests/{request_obj.id}/approve/", data=payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("не покрывает даты проведения", response.data["detail"])
