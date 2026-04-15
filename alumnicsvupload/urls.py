from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AlumniStudentCSVUploadViewSet


router = DefaultRouter()
router.register(r"alumni-csv-uploads", AlumniStudentCSVUploadViewSet)

urlpatterns = [
    path(
        "alumni-csv-uploads",
        AlumniStudentCSVUploadViewSet.as_view({"get": "list", "post": "create"}),
        name="alumni-csv-uploads-no-slash",
    ),
    path("", include(router.urls)),
]

