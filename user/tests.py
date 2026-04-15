from django.test import TestCase
from rest_framework.test import APIClient

from alumnistudent.models import AlumniStudent, Category
from user.models import CustomUser
from user.serializers import StaffCreateSerializer


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
            alumni_id="A-001",
            course=" bscs ",
            year_graduate=2024,
        )

        response = self.client.post(f"/api/users/{user.id}/approve/")

        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.status, "approved")

    def test_approve_user_ignores_name_and_uses_alumni_id_course_year_only(self):
        category = Category.objects.create(name="BSIT")
        AlumniStudent.objects.create(
            alumni_id="A-900",
            first_name="Different",
            last_name="Person",
            gender="Female",
            age=25,
            year_graduate=2023,
            category=category,
        )
        user = CustomUser.objects.create_user(
            email="alumni2@example.com",
            password="testpass123",
            first_name="Mismatch",
            last_name="Name",
            gender="Female",
            age=25,
            role="user",
            alumni_id="A-900",
            course="BSIT",
            year_graduate=2023,
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


class StaffRoleTests(TestCase):
    def test_staff_create_serializer_accepts_id_staff(self):
        serializer = StaffCreateSerializer(
            data={
                "email": "idstaff@example.com",
                "first_name": "ID",
                "middle_name": "",
                "last_name": "Staff",
                "gender": "Male",
                "age": 30,
                "position": "Records Officer",
                "password": "testpass123",
                "role": "id-staff",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.role, "id-staff")
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_staff_api_includes_id_staff_records(self):
        CustomUser.objects.create_user(
            email="staff@example.com",
            password="testpass123",
            first_name="Regular",
            last_name="Staff",
            gender="Male",
            age=30,
            role="staff",
            position="Officer",
        )
        CustomUser.objects.create_user(
            email="idstaff@example.com",
            password="testpass123",
            first_name="ID",
            last_name="Staff",
            gender="Male",
            age=31,
            role="id-staff",
            position="Records Officer",
        )

        response = self.client.get("/api/staff/")

        self.assertEqual(response.status_code, 200)
        roles = {item["role"] for item in response.data}
        self.assertIn("staff", roles)
        self.assertIn("id-staff", roles)

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
