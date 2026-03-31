from rest_framework import viewsets, permissions
from .models import AlumniStudent, Category
from .serializers import AlumniStudentSerializer, CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class AlumniStudentViewSet(viewsets.ModelViewSet):
    queryset = AlumniStudent.objects.all()
    serializer_class = AlumniStudentSerializer
    permission_classes = [permissions.AllowAny]
