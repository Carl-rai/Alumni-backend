from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from alumnistudent.models import AlumniStudent
from .serializers import AlumniStudentCSVUploadSerializer


class AlumniStudentCSVUploadSerializerTests(TestCase):
    def test_accepts_year_graduated_header_alias(self):
        csv_file = SimpleUploadedFile(
            "students.csv",
            b"Alumni ID,Name,Gender,Year Graduated,Course\n1,Jane Doe,Female,2024,BSIT\n",
            content_type="text/csv",
        )

        serializer = AlumniStudentCSVUploadSerializer(data={"csv_file": csv_file})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_accepts_utf16_encoded_csv(self):
        csv_file = SimpleUploadedFile(
            "students.csv",
            "Alumni-Id,Name,Gender,Year-Graduate,Course\n1,Jane Doe,Female,2024,BSIT\n".encode("utf-16"),
            content_type="text/csv",
        )

        serializer = AlumniStudentCSVUploadSerializer(data={"csv_file": csv_file})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_imports_semicolon_delimited_csv(self):
        csv_file = SimpleUploadedFile(
            "students.csv",
            b"Alumni-Id;Name;Gender;Year-Graduate;Course\nA-001;Jane Marie Doe;Female;2024;BSIT\n",
            content_type="text/csv",
        )

        serializer = AlumniStudentCSVUploadSerializer(data={"csv_file": csv_file})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer._import_csv_rows(serializer.validated_data["csv_file"])

        record = AlumniStudent.objects.get(alumni_id="A-001")
        self.assertEqual(record.first_name, "Jane")
        self.assertEqual(record.middle_name, "Marie")
        self.assertEqual(record.last_name, "Doe")
        self.assertEqual(record.gender, "Female")
        self.assertEqual(record.year_graduate, 2024)
        self.assertEqual(record.category.name, "BSIT")
