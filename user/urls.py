from django.urls import path
from .views import register_api, login_api, create_staff_api, get_users_api, get_user_by_id_api, get_staff_api, approve_user_api, reject_user_api, update_user_api, update_staff_api, delete_staff_api, delete_user_api, get_staff_profile_api, change_password_api, get_user_profile_api, update_user_profile_api, toggle_privacy_api, stats_api, me_api, forgot_password_api, verify_code_api, reset_password_api, check_email_api, send_registration_otp_api, verify_registration_otp_api, notifications_api, user_notifications_api, upload_profile_image_api, directory_api
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("stats/", stats_api),
    path("register/", register_api),
    path("check-email/", check_email_api),
    path("send-registration-otp/", send_registration_otp_api),
    path("verify-registration-otp/", verify_registration_otp_api),
    path("login/", login_api),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("create-staff/", create_staff_api),
    path("users/", get_users_api),
    path("users/<int:user_id>/", get_user_by_id_api),
    path("staff/", get_staff_api),
    path("users/<int:user_id>/approve/", approve_user_api),
    path("users/<int:user_id>/reject/", reject_user_api),
    path("users/<int:user_id>/update/", update_user_api),
    path("users/<int:user_id>/delete/", delete_user_api),
    path("staff/<int:user_id>/update/", update_staff_api),
    path("staff/<int:user_id>/delete/", delete_staff_api),
    path("staff-profile/", get_staff_profile_api),
    path("change-password/", change_password_api),
    path("user-profile/", get_user_profile_api),
    path("update-profile/", update_user_profile_api),
    path("toggle-privacy/", toggle_privacy_api),
    path("me/", me_api),
    path("forgot-password/", forgot_password_api),
    path("verify-code/", verify_code_api),
    path("reset-password/", reset_password_api),
    path("notifications/", notifications_api),
    path("user-notifications/", user_notifications_api),
    path("upload-profile-image/", upload_profile_image_api),
    path("directory/", directory_api),
]