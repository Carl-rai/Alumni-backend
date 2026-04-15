from django.urls import path

from .views import audit_logs_api


urlpatterns = [
    path("audit-logs", audit_logs_api, name="audit-logs-no-slash"),
    path("audit-logs/", audit_logs_api),
]

