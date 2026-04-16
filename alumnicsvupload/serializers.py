import csv
import codecs
from io import StringIO
import re

from django.db import transaction
from rest_framework import serializers

from alumnistudent.models import AlumniStudent, Category
from .models import AlumniStudentCSVUpload


REQUIRED_CSV_COLUMNS = [
    "Alumni-Id",
    "Name",
    "Gender",
    "Year-Graduate",
    "Course",
]

REQUIRED_COLUMN_ALIASES = {
    "Alumni-Id": ("Alumni-Id", "Alumni ID"),
    "Name": ("Name",),
    "Gender": ("Gender",),
    "Year-Graduate": ("Year-Graduate", "Year Graduated"),
    "Course": ("Course",),
}


def _normalize_csv_header(value):
    return "".join(ch for ch in str(value).strip().lower() if ch not in {" ", "-", "_"})


def _decode_csv_content(raw_content):
    encodings = ["utf-8-sig", "cp1252", "latin-1"]
    if raw_content.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)) or b"\x00" in raw_content[:256]:
        encodings = ["utf-16", "utf-16-le", "utf-16-be"] + encodings

    for encoding in encodings:
        try:
            decoded = raw_content.decode(encoding)
        except UnicodeDecodeError:
            continue

        # UTF-16 content can technically decode under UTF-8 because of embedded NULs.
        # If we see NULs here, keep searching for the real encoding.
        if "\x00" in decoded:
            continue

        return decoded

    raise serializers.ValidationError("CSV file must be encoded as UTF-8 or UTF-16.")


def _get_csv_dialect(text_content):
    sample = text_content[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except csv.Error:
        return csv.excel


def _split_full_name(full_name):
    parts = [part for part in re.split(r"\s+", str(full_name).strip()) if part]
    if not parts:
        return "", None, ""
    if len(parts) == 1:
        return parts[0], None, parts[0]
    if len(parts) == 2:
        return parts[0], None, parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]


def _normalize_gender(value):
    normalized = str(value).strip().capitalize()
    if normalized not in {"Male", "Female"}:
        raise serializers.ValidationError(f"Invalid gender: {value}")
    return normalized


class AlumniStudentCSVUploadSerializer(serializers.ModelSerializer):
    csv_file_url = serializers.SerializerMethodField()
    csv_file_name = serializers.SerializerMethodField()

    class Meta:
        model = AlumniStudentCSVUpload
        fields = ["id", "title", "csv_file", "csv_file_name", "csv_file_url", "uploaded_at"]
        extra_kwargs = {
            "csv_file": {"write_only": True},
        }

    def validate_csv_file(self, value):
        try:
            raw_content = value.read()
        finally:
            value.seek(0)

        text_content = _decode_csv_content(raw_content)

        try:
            reader = csv.reader(StringIO(text_content), dialect=_get_csv_dialect(text_content))
            headers = next(reader)
        except StopIteration as exc:
            raise serializers.ValidationError("CSV file is empty.") from exc

        normalized_headers = {_normalize_csv_header(header) for header in headers}
        missing_columns = [
            column
            for column in REQUIRED_CSV_COLUMNS
            if not any(
                _normalize_csv_header(candidate) in normalized_headers
                for candidate in REQUIRED_COLUMN_ALIASES[column]
            )
        ]

        if missing_columns:
            raise serializers.ValidationError(
                "CSV file is missing required column(s): " + ", ".join(missing_columns) + "."
            )

        return value

    def _import_csv_rows(self, csv_file):
        try:
            raw_content = csv_file.read()
        finally:
            csv_file.seek(0)

        text_content = _decode_csv_content(raw_content)
        reader = csv.DictReader(StringIO(text_content), dialect=_get_csv_dialect(text_content))

        if not reader.fieldnames:
            raise serializers.ValidationError("CSV file is empty.")

        header_map = {}
        for fieldname in reader.fieldnames:
            header_map.setdefault(_normalize_csv_header(fieldname), fieldname)

        alumni_id_header = next(
            (header_map.get(_normalize_csv_header(candidate)) for candidate in REQUIRED_COLUMN_ALIASES["Alumni-Id"]),
            None,
        )
        name_header = next(
            (header_map.get(_normalize_csv_header(candidate)) for candidate in REQUIRED_COLUMN_ALIASES["Name"]),
            None,
        )
        gender_header = next(
            (header_map.get(_normalize_csv_header(candidate)) for candidate in REQUIRED_COLUMN_ALIASES["Gender"]),
            None,
        )
        year_graduate_header = next(
            (
                header_map.get(_normalize_csv_header(candidate))
                for candidate in REQUIRED_COLUMN_ALIASES["Year-Graduate"]
            ),
            None,
        )
        course_header = next(
            (header_map.get(_normalize_csv_header(candidate)) for candidate in REQUIRED_COLUMN_ALIASES["Course"]),
            None,
        )

        if not all([alumni_id_header, name_header, gender_header, year_graduate_header, course_header]):
            raise serializers.ValidationError(
                "CSV file is missing required column(s): Alumni-Id, Name, Gender, Year-Graduate, Course."
            )

        imported = []
        for index, row in enumerate(reader, start=2):
            if not any(str(value).strip() for value in row.values()):
                continue

            alumni_id = str(row.get(alumni_id_header, "")).strip()
            name = str(row.get(name_header, "")).strip()
            gender = _normalize_gender(row.get(gender_header, ""))
            year_graduate_raw = str(row.get(year_graduate_header, "")).strip()
            course = str(row.get(course_header, "")).strip()

            if not alumni_id:
                raise serializers.ValidationError(f"Row {index}: Alumni-Id is required.")
            if not name:
                raise serializers.ValidationError(f"Row {index}: Name is required.")
            if not year_graduate_raw:
                raise serializers.ValidationError(f"Row {index}: Year-Graduate is required.")
            if not course:
                raise serializers.ValidationError(f"Row {index}: Course is required.")

            try:
                year_graduate = int(year_graduate_raw)
            except ValueError as exc:
                raise serializers.ValidationError(f"Row {index}: Year-Graduate must be a number.") from exc

            first_name, middle_name, last_name = _split_full_name(name)
            if not first_name or not last_name:
                raise serializers.ValidationError(f"Row {index}: Name must contain at least one name.")

            category, _ = Category.objects.get_or_create(name=course)
            alumni_student, _ = AlumniStudent.objects.update_or_create(
                alumni_id=alumni_id,
                defaults={
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "last_name": last_name,
                    "gender": gender,
                    "age": 0,
                    "year_graduate": year_graduate,
                    "category": category,
                },
            )
            imported.append(alumni_student)

        return imported

    @transaction.atomic
    def create(self, validated_data):
        csv_file = validated_data["csv_file"]
        self._import_csv_rows(csv_file)
        return super().create(validated_data)

    def get_csv_file_name(self, obj):
        if not obj.csv_file:
            return None
        return obj.csv_file.name.rsplit("/", 1)[-1]

    def get_csv_file_url(self, obj):
        request = self.context.get("request")
        if obj.csv_file and request:
            return request.build_absolute_uri(obj.csv_file.url)
        if obj.csv_file:
            return obj.csv_file.url
        return None
