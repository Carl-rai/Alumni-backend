from django.urls import path
from . import views

urlpatterns = [
    path("apply-job/", views.apply_job_api, name="apply_job"),
    path("job-applications/", views.get_all_applications_api, name="get_all_applications"),
    path("job-applications/<int:app_id>/", views.get_application_api, name="get_application"),
    path("job-applications/<int:app_id>/update/", views.update_application_api, name="update_application"),
    path("job-applications/<int:app_id>/delete/", views.delete_application_api, name="delete_application"),
    path("job-applications/user/<int:user_id>/", views.get_user_applications_api, name="get_user_applications"),
]
