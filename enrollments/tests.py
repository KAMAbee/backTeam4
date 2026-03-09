import json
from datetime import datetime, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from enrollments.models import TrainingEnrollment
from trainings.models import Training, TrainingSession


def dt(y, m, d, h=9, minute=0):
    return timezone.make_aware(datetime(y, m, d, h, minute))


class SessionParticipantsAdminEndpointsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="password123",
            first_name="Manager",
            last_name="User",
            role=User.Role.MANAGER,
        )
        self.employee = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="password123",
            first_name="Employee",
            last_name="User",
            role=User.Role.EMPLOYEE,
        )

        training = Training.objects.create(
            title="DRF Basics",
            type=Training.TrainingType.TRAINING,
            trainer_name="Trainer",
            pricing_type=Training.PricingType.PER_PERSON,
            price="1000.00",
        )
        self.session = TrainingSession.objects.create(
            training=training,
            start_date=dt(2026, 1, 10, 9, 0),
            end_date=dt(2026, 1, 12, 18, 0),
            location="Office",
            city="Almaty",
            capacity=20,
        )
        self.enrollment = TrainingEnrollment.objects.create(
            training_session=self.session,
            employee=self.employee,
        )

        self.url = f"/api/enrollments/session/{self.session.id}/participants/"

    def _auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_get_participants_unauthorized_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_participants_unauthorized_returns_401(self):
        response = self.client.patch(self.url, data=[], format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_participants_manager_forbidden(self):
        response = self._auth_client(self.manager).get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_participants_employee_forbidden(self):
        response = self._auth_client(self.employee).get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_participants_admin_ok(self):
        response = self._auth_client(self.admin).get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item["enrollment_id"], str(self.enrollment.id))
        self.assertEqual(item["employee"]["id"], str(self.employee.id))
        self.assertEqual(item["employee"]["email"], self.employee.email)
        self.assertEqual(item["training_title"], "DRF Basics")

    def test_patch_participants_manager_forbidden(self):
        payload = [{"enrollment_id": str(self.enrollment.id), "is_attended": True, "certificate_number": "ABC-1"}]
        response = self._auth_client(self.manager).patch(self.url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_participants_employee_forbidden(self):
        payload = [{"enrollment_id": str(self.enrollment.id), "is_attended": True, "certificate_number": "ABC-1"}]
        response = self._auth_client(self.employee).patch(self.url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_participants_admin_ok_json(self):
        payload = [{"enrollment_id": str(self.enrollment.id), "is_attended": True, "certificate_number": "ABC-1"}]
        response = self._auth_client(self.admin).patch(self.url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.enrollment.refresh_from_db()
        self.assertTrue(self.enrollment.is_attended)
        self.assertEqual(self.enrollment.certificate_number, "ABC-1")

    def test_patch_participants_admin_ok_multipart_with_file(self):
        uploaded_file = SimpleUploadedFile("cert.txt", b"dummy certificate", content_type="text/plain")
        payload = {
            "items": json.dumps(
                [
                    {
                        "enrollment_id": str(self.enrollment.id),
                        "is_attended": True,
                        "certificate_number": "ABC-2",
                    }
                ]
            ),
            f"files.{self.enrollment.id}": uploaded_file,
        }
        response = self._auth_client(self.admin).patch(self.url, data=payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.enrollment.refresh_from_db()
        self.assertTrue(self.enrollment.is_attended)
        self.assertEqual(self.enrollment.certificate_number, "ABC-2")
        self.assertTrue(bool(self.enrollment.certificate_file))

    def test_patch_participants_fails_for_not_finished_session(self):
        future_training = Training.objects.create(
            title="Future Session",
            type=Training.TrainingType.TRAINING,
            trainer_name="Future Trainer",
            pricing_type=Training.PricingType.PER_PERSON,
            price="1000.00",
        )
        future_session = TrainingSession.objects.create(
            training=future_training,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            location="Office",
            city="Almaty",
            capacity=20,
        )
        future_enrollment = TrainingEnrollment.objects.create(
            training_session=future_session,
            employee=self.employee,
        )

        payload = [{"enrollment_id": str(future_enrollment.id), "is_attended": True, "certificate_number": "FUT-1"}]
        future_url = f"/api/enrollments/session/{future_session.id}/participants/"
        response = self._auth_client(self.admin).patch(future_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("только для прошедших мероприятий", str(response.data))


class MyEnrollmentsViewTests(APITestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="my_employee",
            email="my_employee@example.com",
            password="password123",
            first_name="My",
            last_name="Employee",
            role=User.Role.EMPLOYEE,
        )
        training = Training.objects.create(
            title="Security Basics",
            type=Training.TrainingType.TRAINING,
            trainer_name="Trainer",
            pricing_type=Training.PricingType.PER_PERSON,
            price="1000.00",
        )
        session = TrainingSession.objects.create(
            training=training,
            start_date=dt(2026, 1, 1, 9, 0),
            end_date=dt(2026, 1, 2, 18, 0),
            location="Plant A, Room 11",
            city="Karaganda",
            capacity=20,
        )
        TrainingEnrollment.objects.create(training_session=session, employee=self.employee, is_attended=True)

    def test_my_enrollments_contains_location_and_city(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get("/api/enrollments/my/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["location"], "Plant A, Room 11")
        self.assertEqual(response.data[0]["city"], "Karaganda")
