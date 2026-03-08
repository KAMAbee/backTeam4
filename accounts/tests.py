from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Department, Organization, User
from enrollments.models import TrainingEnrollment
from trainings.models import Training, TrainingSession


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
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 2),
            location="HQ",
            city="Almaty",
            capacity=10,
        )
        session_not_attended = TrainingSession.objects.create(
            training=training,
            start_date=date(2026, 2, 3),
            end_date=date(2026, 2, 4),
            location="HQ",
            city="Almaty",
            capacity=10,
        )
        session_without_certificate = TrainingSession.objects.create(
            training=training,
            start_date=date(2026, 2, 5),
            end_date=date(2026, 2, 6),
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

    def test_legacy_profile_endpoint_still_works(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user.id))
