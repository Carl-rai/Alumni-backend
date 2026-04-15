from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlumniStudentCSVUploadViewSet, AlumniStudentViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'alumni-students', AlumniStudentViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'alumni-csv-uploads', AlumniStudentCSVUploadViewSet)

urlpatterns = [
    path(
        "alumni-csv-uploads",
        AlumniStudentCSVUploadViewSet.as_view({"get": "list", "post": "create"}),
        name="alumni-csv-uploads-no-slash",
    ),
    path('', include(router.urls)),
]
