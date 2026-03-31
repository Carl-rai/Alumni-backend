from django.test import TestCase
from rest_framework.test import APIClient

from alumnistudent.models import AlumniStudent, Category
from user.models import CustomUser


class ApproveUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_approve_user_requires_matching_alumni_record(self):
        user = CustomUser.objects.create_user(
            email="alumni@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Doe",
            gender="Female",
            age=24,
            role="user",
            course="BSCS",
            year_graduate=2024,
        )

        response = self.client.post(f"/api/users/{user.id}/approve/")

        user.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(user.status, "pending")
        self.assertIn("no matching alumni student record", response.data["error"].lower())

    def test_approve_user_succeeds_when_alumni_record_matches(self):
        category = Category.objects.create(name="BSCS")
        AlumniStudent.objects.create(
            alumni_id="A-001",
            first_name="Jane",
            last_name="Doe",
            gender="Female",
            age=24,
            year_graduate=2024,
            category=category,
        )
        user = CustomUser.objects.create_user(
            email="alumni@example.com",
            password="testpass123",
            first_name=" Jane ",
            last_name="Doe",
            gender="Female",
            age=24,
            role="user",
            course=" bscs ",
            year_graduate=2024,
        )

        response = self.client.post(f"/api/users/{user.id}/approve/")

        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.status, "approved")


class LoginApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_alumni_user_can_login_with_email(self):
        user = CustomUser.objects.create_user(
            email="alumni@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Doe",
            gender="Female",
            age=24,
            role="user",
            status="approved",
            alumni_id="2024-001",
        )

        response = self.client.post(
            "/api/login/",
            {"email": user.email, "password": "testpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], user.email)
        self.assertEqual(response.data["alumni_id"], user.alumni_id)

    def test_alumni_user_can_login_with_alumni_id(self):
        user = CustomUser.objects.create_user(
            email="alumni@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Doe",
            gender="Female",
            age=24,
            role="user",
            status="approved",
            alumni_id="2024-001",
        )

        response = self.client.post(
            "/api/login/",
            {"email": user.alumni_id, "password": "testpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], user.email)
        self.assertEqual(response.data["alumni_id"], user.alumni_id)
