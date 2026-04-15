from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlumniStudentViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'alumni-students', AlumniStudentViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
