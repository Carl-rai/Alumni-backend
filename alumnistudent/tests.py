from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from alumnistudent.models import AlumniStudent, Category
from alumnicsvupload.serializers import AlumniStudentCSVUploadSerializer


class AlumniStudentCSVUploadSerializerTests(TestCase):
    def test_rejects_csv_missing_required_columns(self):
        csv_file = SimpleUploadedFile(
            "students.csv",
            b"Alumni-Id,Name,Gender,Year-Graduate\n1,Jane Doe,Female,2024\n",
            content_type="text/csv",
        )

        serializer = AlumniStudentCSVUploadSerializer(
            data={"title": "Missing course column", "csv_file": csv_file}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("csv_file", serializer.errors)
        self.assertIn("Course", str(serializer.errors["csv_file"][0]))

    def test_accepts_csv_with_required_columns(self):
        csv_file = SimpleUploadedFile(
            "students.csv",
            b"Alumni-Id,Name,Gender,Year-Graduate,Course\n1,Jane Doe,Female,2024,BSIT\n",
            content_type="text/csv",
        )

        serializer = AlumniStudentCSVUploadSerializer(
            data={"title": "Valid upload", "csv_file": csv_file}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_csv_upload_imports_or_updates_alumni_records(self):
        csv_file = SimpleUploadedFile(
            "students.csv",
            b"Alumni-Id,Name,Gender,Year-Graduate,Course\nA-001,Jane Marie Doe,Female,2024,BSIT\n",
            content_type="text/csv",
        )

        serializer = AlumniStudentCSVUploadSerializer(
            data={"title": "Import upload", "csv_file": csv_file}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer._import_csv_rows(serializer.validated_data["csv_file"])

        record = AlumniStudent.objects.get(alumni_id="A-001")
        self.assertEqual(record.first_name, "Jane")
        self.assertEqual(record.middle_name, "Marie")
        self.assertEqual(record.last_name, "Doe")
        self.assertEqual(record.gender, "Female")
        self.assertEqual(record.year_graduate, 2024)
        self.assertEqual(record.category.name, "BSIT")

        update_file = SimpleUploadedFile(
            "students.csv",
            b"Alumni-Id,Name,Gender,Year-Graduate,Course\nA-001,Jane Q Doe,Female,2024,BSIT\n",
            content_type="text/csv",
        )

        update_serializer = AlumniStudentCSVUploadSerializer(
            data={"title": "Import update", "csv_file": update_file}
        )

        self.assertTrue(update_serializer.is_valid(), update_serializer.errors)
        update_serializer._import_csv_rows(update_serializer.validated_data["csv_file"])

        self.assertEqual(AlumniStudent.objects.filter(alumni_id="A-001").count(), 1)
        record.refresh_from_db()
        self.assertEqual(record.first_name, "Jane")
        self.assertEqual(record.middle_name, "Q")
        self.assertEqual(record.last_name, "Doe")
