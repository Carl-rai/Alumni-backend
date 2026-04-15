from django.urls import path
from .views import submit_id_request, my_id_request, cancel_id_request, list_id_requests, update_id_request_status, export_id_requests_csv, import_id_requests_csv

urlpatterns = [
    path("id-requests/submit/", submit_id_request),
    path("id-requests/my/", my_id_request),
    path("id-requests/cancel/", cancel_id_request),
    path("id-requests/", list_id_requests),
    path("id-requests/<int:request_id>/status/", update_id_request_status),
    path("id-requests/export/", export_id_requests_csv),
    path("id-requests/import/", import_id_requests_csv),
]
