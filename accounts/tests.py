from datetime import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Department, Organization, User
from enrollments.models import TrainingEnrollment
from trainings.models import Training, TrainingSession


def dt(y, m, d, h=9, minute=0):
    return timezone.make_aware(datetime(y, m, d, h, minute))


class MeProfileTests(APITestCase):
    def setUp(self):
        organization = Organization.objects.create(name="Org A", bin="123456789012", address="Address 1")
        department = Department.objects.create(name="HR", organization=organization)
        self.user = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="password123",
            first_name="Ivan",
            last_name="Ivanov",
            patronymic="Ivanovich",
            role=User.Role.EMPLOYEE,
            department=department,
        )

        training = Training.objects.create(
            title="Advanced DRF",
            type=Training.TrainingType.TRAINING,
            trainer_name="Trainer",
            pricing_type=Training.PricingType.PER_PERSON,
            price="1200.00",
        )
        session = TrainingSession.objects.create(
            training=training,
            start_date=dt(2026, 2, 1, 9, 0),
            end_date=dt(2026, 2, 2, 18, 0),
            location="HQ",
            city="Almaty",
            capacity=10,
        )
        session_not_attended = TrainingSession.objects.create(
            training=training,
            start_date=dt(2026, 2, 3, 9, 0),
            end_date=dt(2026, 2, 4, 18, 0),
            location="HQ",
            city="Almaty",
            capacity=10,
        )
        session_without_certificate = TrainingSession.objects.create(
            training=training,
            start_date=dt(2026, 2, 5, 9, 0),
            end_date=dt(2026, 2, 6, 18, 0),
            location="HQ",
            city="Almaty",
            capacity=10,
        )

        TrainingEnrollment.objects.create(
            training_session=session,
            employee=self.user,
            is_attended=True,
            certificate_number="CERT-100",
        )
        TrainingEnrollment.objects.create(
            training_session=session,
            employee=User.objects.create_user(
                username="other",
                email="other@example.com",
                password="password123",
                first_name="Other",
                last_name="User",
                role=User.Role.EMPLOYEE,
            ),
            is_attended=True,
            certificate_number="CERT-OTHER",
        )
        TrainingEnrollment.objects.create(
            training_session=session_not_attended,
            employee=self.user,
            is_attended=False,
            certificate_number="CERT-NOT-ATTENDED",
        )
        TrainingEnrollment.objects.create(
            training_session=session_without_certificate,
            employee=self.user,
            is_attended=True,
            certificate_number="",
        )

    def test_me_profile_unauthorized_returns_401(self):
        response = self.client.get("/api/accounts/me/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_profile_returns_user_and_filtered_certificates(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/accounts/me/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("user", response.data)
        self.assertIn("certificates", response.data)
        self.assertEqual(response.data["user"]["id"], str(self.user.id))
        self.assertEqual(response.data["user"]["fio"], "Ivanov Ivan Ivanovich")
        self.assertEqual(response.data["user"]["email"], "employee@example.com")
        self.assertEqual(response.data["user"]["department"], "HR")
        self.assertEqual(response.data["user"]["organization"], "Org A")

        self.assertEqual(len(response.data["certificates"]), 1)
        self.assertEqual(response.data["certificates"][0]["certificate_number"], "CERT-100")
        self.assertEqual(response.data["certificates"][0]["location"], "HQ")
        self.assertEqual(response.data["certificates"][0]["city"], "Almaty")

    def test_legacy_profile_endpoint_still_works(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user.id))

    def test_profile_patch_updates_only_first_and_last_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            "/api/accounts/profile/",
            {"first_name": "Petr", "last_name": "Petrov"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Petr")
        self.assertEqual(self.user.last_name, "Petrov")

    def test_profile_patch_rejects_fields_other_than_first_and_last_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            "/api/accounts/profile/",
            {"first_name": "Petr", "role": User.Role.ADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.EMPLOYEE)


class EmployeeDirectoryTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_dir",
            email="admin_dir@example.com",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager_dir",
            email="manager_dir@example.com",
            password="password123",
            role=User.Role.MANAGER,
        )
        self.employee = User.objects.create_user(
            username="employee_dir",
            email="employee_dir@example.com",
            password="password123",
            role=User.Role.EMPLOYEE,
        )
        self.employee_two = User.objects.create_user(
            username="employee_dir_2",
            email="employee_dir_2@example.com",
            password="password123",
            role=User.Role.EMPLOYEE,
        )

    def test_manager_can_get_employee_directory(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get("/api/accounts/users/employees/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertTrue(all(item["role"] == User.Role.EMPLOYEE for item in response.data))
        self.assertIn(str(self.employee.id), [item["id"] for item in response.data])

    def test_employee_cannot_get_employee_directory(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get("/api/accounts/users/employees/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_can_get_users_directory_route(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get("/api/accounts/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)
        self.assertTrue(all(item["role"] == User.Role.EMPLOYEE for item in response.data))
        self.assertNotIn(str(self.admin.id), [item["id"] for item in response.data])
