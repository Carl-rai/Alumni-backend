from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventRegistrationViewSet

router = DefaultRouter()
router.register(r'event-registrations', EventRegistrationViewSet, basename='event-registration')

urlpatterns = [
    path('', include(router.urls)),
]
