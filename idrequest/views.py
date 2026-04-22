import csv
from io import StringIO

from django.db import transaction

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .models import IDRequest
from .serializers import IDRequestStaffSerializer
from user.audit import log_audit_event
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_id_request(request):
    user = request.user
    if user.role != "user":
        return Response({"error": "Only alumni users can request an ID."}, status=status.HTTP_403_FORBIDDEN)

    note = request.data.get("note", "").strip()

    if IDRequest.objects.filter(user=user, status="pending").exists():
        return Response({"error": "You already have a pending ID request."}, status=status.HTTP_400_BAD_REQUEST)

    IDRequest.objects.update_or_create(
        user=user,
        defaults={"status": "pending", "note": note},
    )
    return Response({"message": "ID request submitted successfully."}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_id_request(request):
    user = request.user
    try:
        req = IDRequest.objects.get(user=user)
        return Response({
            "id": req.id,
            "status": req.status,
            "note": req.note,
            "created_at": req.created_at,
        })
    except IDRequest.DoesNotExist:
        return Response({"status": None})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cancel_id_request(request):
    user = request.user
    try:
        req = IDRequest.objects.get(user=user, status="pending")
        req.delete()
        return Response({"message": "ID request cancelled."})
    except IDRequest.DoesNotExist:
        return Response({"error": "No pending request found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_id_requests(request):
    if request.user.role not in ("admin", "staff", "id-staff"):
        return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

    status_filter = request.query_params.get("status", "pending")
    qs = IDRequest.objects.select_related("user").filter(status=status_filter).order_by("-created_at")
    return Response(IDRequestStaffSerializer(qs, many=True).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_id_request_status(request, request_id):
    if request.user.role not in ("admin", "staff", "id-staff"):
        return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

    new_status = request.data.get("status")
    if new_status not in ("pending", "exported", "done"):
        return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        req = IDRequest.objects.get(id=request_id)
        previous_status = req.status
        req.status = new_status
        req.save()

        if previous_status != new_status:
            if new_status == "exported":
                send_id_request_export_email(req)
            elif new_status == "done":
                send_id_request_ready_email(req)

        return Response({"message": "Status updated."})
    except IDRequest.DoesNotExist:
        return Response({"error": "Request not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_id_requests_csv(request):
    if request.user.role not in ("admin", "staff", "id-staff"):
        return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

    status_filter = request.query_params.get("status", "pending")
    qs = IDRequest.objects.select_related("user").filter(status=status_filter).order_by("-created_at")
    id_requests = list(qs)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="id_requests_{status_filter}.csv"'

    writer = csv.writer(response)
    writer.writerow(["#", "Alumni ID", "First Name", "Middle Name", "Last Name", "Email", "Course", "Year Graduated", "Gender", "Note", "Status", "Requested At"])

    for i, r in enumerate(id_requests, start=1):
        writer.writerow([
            i,
            r.user.alumni_id or "",
            r.user.first_name,
            r.user.middle_name or "",
            r.user.last_name,
            r.user.email,
            r.user.course or "",
            r.user.year_graduate or "",
            r.user.gender or "",
            r.note or "",
            r.status,
            r.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    # Mark exported ones as "exported"
    if status_filter == "pending":
        exported_count = qs.update(status="exported")
    else:
        exported_count = 0

    try:
        setattr(request, "_audit_logged", True)
        log_audit_event(
            request,
            response=response,
            action="export_id_requests",
            details={
                "status_filter": status_filter,
                "exported_count": exported_count,
                "row_count": len(id_requests),
            },
        )
    except Exception:
        pass

    return response


def _normalize_csv_header(value):
    return "".join(ch for ch in str(value).strip().lower() if ch not in {" ", "-", "_"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def import_id_requests_csv(request):
    if request.user.role not in ("admin", "staff", "id-staff"):
        return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

    csv_file = request.FILES.get("csv_file") or request.data.get("csv_file")
    if not csv_file:
        return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        raw_content = csv_file.read()
    finally:
        try:
            csv_file.seek(0)
        except Exception:
            pass

    try:
        text_content = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return Response({"error": "CSV file must be encoded as UTF-8."}, status=status.HTTP_400_BAD_REQUEST)

    reader = csv.DictReader(StringIO(text_content))
    if not reader.fieldnames:
        return Response({"error": "CSV file is empty."}, status=status.HTTP_400_BAD_REQUEST)

    header_map = {}
    for fieldname in reader.fieldnames:
        header_map.setdefault(_normalize_csv_header(fieldname), fieldname)

    alumni_id_header = header_map.get(_normalize_csv_header("Alumni ID")) or header_map.get(_normalize_csv_header("Alumni-Id"))
    first_name_header = header_map.get(_normalize_csv_header("First Name"))
    course_header = header_map.get(_normalize_csv_header("Course"))
    year_graduate_header = header_map.get(_normalize_csv_header("Year Graduated")) or header_map.get(_normalize_csv_header("Year-Graduate"))
    status_header = header_map.get(_normalize_csv_header("Status"))

    missing_required_columns = []
    if not alumni_id_header:
        missing_required_columns.append("Alumni ID")
    if not first_name_header:
        missing_required_columns.append("First Name")
    if not course_header:
        missing_required_columns.append("Course")
    if not year_graduate_header:
        missing_required_columns.append("Year Graduated")
    if not status_header:
        missing_required_columns.append("Status")

    if missing_required_columns:
        return Response(
            {"error": "CSV file is missing required column(s): " + ", ".join(missing_required_columns) + "."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rows = []
    invalid_rows = []
    missing_rows = []

    for index, row in enumerate(reader, start=2):
        alumni_id = str(row.get(alumni_id_header, "")).strip() if alumni_id_header else ""
        first_name = str(row.get(first_name_header, "")).strip() if first_name_header else ""
        course = str(row.get(course_header, "")).strip() if course_header else ""
        year_graduate_raw = str(row.get(year_graduate_header, "")).strip() if year_graduate_header else ""
        row_status = str(row.get(status_header, "")).strip().lower()

        row_missing = []
        if not alumni_id:
            row_missing.append("Alumni ID")
        if not first_name:
            row_missing.append("First Name")
        if not course:
            row_missing.append("Course")
        if not year_graduate_raw:
            row_missing.append("Year Graduated")
        if row_status != "done":
            row_missing.append("Status")

        if row_missing:
            invalid_rows.append({
                "row": index,
                "missing_or_invalid": row_missing,
                "alumni_id": alumni_id or None,
                "first_name": first_name or None,
                "course": course or None,
                "year_graduate": year_graduate_raw or None,
                "status": row_status or None,
            })
            continue

        rows.append({
            "row": index,
            "alumni_id": alumni_id,
            "first_name": first_name,
            "course": course,
            "year_graduate": year_graduate_raw,
            "status": row_status,
        })

    if invalid_rows:
        return Response(
            {
                "error": "CSV import aborted because one or more rows are missing required data or are not marked done.",
                "invalid_rows": invalid_rows,
                "missing_rows": missing_rows,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_requests = []
    validation_errors = []
    for row in rows:
        req = IDRequest.objects.select_related("user").filter(user__alumni_id__iexact=row["alumni_id"]).first()
        if req is None:
            validation_errors.append({"row": row["row"], "alumni_id": row["alumni_id"], "reason": "No matching ID request found."})
            continue

        user = req.user
        required_mismatches = []
        if str(user.first_name or "").strip().casefold() != row["first_name"].casefold():
            required_mismatches.append("First Name")
        if str(user.course or "").strip().casefold() != row["course"].casefold():
            required_mismatches.append("Course")
        if str(user.year_graduate or "").strip() != row["year_graduate"].strip():
            required_mismatches.append("Year Graduated")

        if required_mismatches:
            validation_errors.append({
                "row": row["row"],
                "alumni_id": row["alumni_id"],
                "mismatched_fields": required_mismatches,
            })
            continue

        validated_requests.append({"row": row["row"], "request": req})

    if validation_errors or missing_rows:
        return Response(
            {
                "error": "CSV import aborted because one or more rows do not match the alumni request data.",
                "validation_errors": validation_errors,
                "missing_rows": missing_rows,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        updated_requests = []
        skipped_rows = []
        for item in validated_requests:
            req = item["request"]
            if req.status == "done":
                skipped_rows.append({"row": item["row"], "reason": "Already marked done.", "request_id": req.id})
            else:
                req.status = "done"
                req.save(update_fields=["status", "updated_at"])
            updated_requests.append(req)

    return Response(
        {
            "message": "ID requests imported successfully.",
            "updated_count": len(updated_requests),
            "skipped_count": len(skipped_rows),
            "missing_count": len(missing_rows),
            "invalid_count": len(invalid_rows),
            "updated_requests": [
                IDRequestStaffSerializer(req).data
                for req in updated_requests
            ],
            "skipped_rows": skipped_rows,
            "missing_rows": missing_rows,
            "invalid_rows": invalid_rows,
        },
        status=status.HTTP_200_OK,
    )
