from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from .models import AlumniStudent, AlumniStudentCSVUpload, Category
from .serializers import (
    AlumniStudentCSVUploadSerializer,
    AlumniStudentSerializer,
    CategorySerializer,
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class AlumniStudentViewSet(viewsets.ModelViewSet):
    queryset = AlumniStudent.objects.all()
    serializer_class = AlumniStudentSerializer
    permission_classes = [permissions.AllowAny]


class AlumniStudentCSVUploadViewSet(viewsets.ModelViewSet):
    queryset = AlumniStudentCSVUpload.objects.all()
    serializer_class = AlumniStudentCSVUploadSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_destroy(self, instance):
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated or getattr(user, "role", None) != "admin":
            raise PermissionDenied("Only admin users can delete CSV uploads.")
        return super().perform_destroy(instance)

    @action(detail=True, methods=["get"], url_path="open")
    def open_csv(self, request, pk=None):
        upload = self.get_object()
        if not upload.csv_file:
            raise Http404("CSV file not found")

        try:
            file_handle = upload.csv_file.open("rb")
        except Exception as exc:  # pragma: no cover - storage/backend specific
            raise Http404("Unable to open CSV file") from exc

        filename = upload.csv_file.name.rsplit("/", 1)[-1]
        return FileResponse(file_handle, as_attachment=False, filename=filename)
