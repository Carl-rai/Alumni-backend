from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.core.cache import cache
from django.db import models
from backend.email_utils import send_system_email, smtp_connection_diagnostics
from .serializers import RegisterSerializer, StaffCreateSerializer
from .models import CustomUser
from alumnistudent.models import AlumniStudent
import random
import string


def _normalize_match_value(value):
    if value is None:
        return ""
    return str(value).strip().casefold()


def _find_matching_alumni_record(user):
    user_first_name = _normalize_match_value(user.first_name)
    user_course = _normalize_match_value(user.course)
    user_year_graduate = user.year_graduate

    if not user_first_name or not user_course or user_year_graduate is None:
        return None

    alumni_records = AlumniStudent.objects.select_related("category").filter(
        year_graduate=user_year_graduate
    )

    for alumni in alumni_records:
        alumni_first_name = _normalize_match_value(alumni.first_name)
        alumni_category = _normalize_match_value(
            alumni.category.name if alumni.category else ""
        )

        if alumni_first_name == user_first_name and alumni_category == user_course:
            return alumni

    return None


def _resolve_login_email(login_value):
    login_value = (login_value or "").strip()
    if not login_value:
        return None

    user = CustomUser.objects.filter(email__iexact=login_value).first()
    if user:
        return user.email

    alumni_user = CustomUser.objects.filter(
        role="user",
        alumni_id__iexact=login_value,
    ).first()
    if alumni_user:
        return alumni_user.email

    return login_value


@api_view(["POST"])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login_api(request):
    login_value = request.data.get("email") or request.data.get("alumni_id")
    password = request.data.get("password")

    if not login_value or not password:
        return Response(
            {"error": "Email or alumni ID and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    resolved_email = _resolve_login_email(login_value)
    user = authenticate(email=resolved_email, password=password)

    if user is not None:
        if user.role == "user" and user.status != "approved":
            return Response(
                {"message": "Your account is for pending approval"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "email": user.email,
            "alumni_id": user.alumni_id if user.role == "user" else None,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }, status=status.HTTP_200_OK)

    return Response(
        {"error": "Invalid email/alumni ID or password"},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(["POST"])
def create_staff_api(request):
    """Admin endpoint to create staff accounts"""
    serializer = StaffCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Send email with password
        try:
            password = request.data.get('password')
            send_system_email(
                subject='Staff Account Created - Alumni System',
                message=f'Dear {user.first_name} {user.last_name},\n\nYour staff account has been created!\n\nEmail: {user.email}\nPassword: {password}\n\nPlease login and change your password immediately.\n\nBest regards,\nAlumni Management Team',
                recipient=user.email,
            )
        except Exception as e:
            return Response(
                {"error": f"Staff account created, but email sending failed: {str(e)}"},
                status=status.HTTP_201_CREATED,
            )
        
        return Response({"message": "Staff account created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def stats_api(request):
    """Public stats: approved alumni count, total events, and total jobs"""
    from addevent.models import Event
    from career.models import JobPost
    alumni_count = CustomUser.objects.filter(role="user", status="approved").count()
    events_count = Event.objects.count()
    jobs_count = JobPost.objects.filter(status="open").count()
    return Response({"alumni_count": alumni_count, "events_count": events_count, "jobs_count": jobs_count}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_user_by_id_api(request, user_id):
    """Get a single user by ID"""
    try:
        user = CustomUser.objects.get(id=user_id)
        if user.is_private:
            data = {
                "id": user.id,
                "full_name": f"{user.first_name} {user.middle_name + ' ' if user.middle_name else ''}{user.last_name}",
                "current_job": user.current_job,
                "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
                "is_private": True,
                "private_message": "This Profile is set to Private.",
            }
            return Response(data, status=status.HTTP_200_OK)

        data = {
            "id": user.id,
            "alumni_id": user.alumni_id,
            "email": user.email,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "gender": user.gender,
            "age": user.age,
            "course": user.course,
            "year_graduate": user.year_graduate,
            "status": user.status,
            "location": user.location,
            "contact_num": user.contact_num,
            "current_job": user.current_job,
            "company": user.company,
            "skills": user.skills,
            "bio": user.bio,
            "is_private": False,
            "private_message": None,
            "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
        }
        return Response(data, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def get_users_api(request):
    """Get all users with role 'user'"""
    users = CustomUser.objects.filter(role="user")
    data = [{
        "id": user.id,
        "alumni_id": user.alumni_id,
        "email": user.email,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "gender": user.gender,
        "age": user.age,
        "course": user.course,
        "year_graduate": user.year_graduate,
        "status": user.status,
        "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
    } for user in users]
    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_staff_api(request):
    """Get all users with role 'staff'"""
    staff = CustomUser.objects.filter(role="staff")
    data = [{
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "gender": user.gender,
        "age": user.age,
        "position": user.position,
        "status": user.status,
        "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
    } for user in staff]
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
def approve_user_api(request, user_id):
    """Approve a user"""
    try:
        user = CustomUser.objects.get(id=user_id, role="user")

        matched_alumni = _find_matching_alumni_record(user)
        if matched_alumni is None:
            return Response(
                {
                    "error": (
                        "User cannot be approved because no matching alumni student "
                        "record was found for first name, course, and year_graduate."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.status = "approved"
        user.save()
        
        # Send approval email
        try:
            send_system_email(
                subject='Account Approved - Alumni System',
                message=f'Dear {user.first_name} {user.last_name},\n\nYour alumni account has been approved! You can now login to the system.\n\nBest regards,\nAlumni Management Team',
                recipient=user.email,
            )
        except Exception as e:
            return Response(
                {"error": f"User approved, but email sending failed: {str(e)}"},
                status=status.HTTP_200_OK,
            )
        
        return Response({"message": "User approved successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def reject_user_api(request, user_id):
    """Reject a user"""
    try:
        user = CustomUser.objects.get(id=user_id)
        reason = request.data.get('reason', '')
        user.status = "rejected"
        user.save()

        try:
            send_system_email(
                subject='Account Rejected - Alumni System',
                message=f'Dear {user.first_name} {user.last_name},\n\nWe regret to inform you that your alumni account registration has been rejected.\n\nReason: {reason}\n\nIf you have any questions, please contact the administrator through this email or on system customer service.\n\nBest regards,\nAlumni Management Team',
                recipient=user.email,
            )
        except Exception as e:
            return Response(
                {"error": f"User rejected, but email sending failed: {str(e)}"},
                status=status.HTTP_200_OK,
            )

        return Response({"message": "User rejected successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
def update_user_api(request, user_id):
    """Update a user"""
    from alumnistudent.models import AlumniStudent
    try:
        user = CustomUser.objects.get(id=user_id)
        old_alumni_id = user.alumni_id
        new_alumni_id = request.data.get('alumni_id', user.alumni_id)

        if user.role == "user" and not AlumniStudent.objects.filter(alumni_id=new_alumni_id).exists():
            return Response(
                {"error": "Alumni ID does not match any record in the alumni student database."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.alumni_id = new_alumni_id
        user.email = request.data.get('email', user.email)
        user.first_name = request.data.get('first_name', user.first_name)
        user.middle_name = request.data.get('middle_name', user.middle_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.gender = request.data.get('gender', user.gender)
        user.age = request.data.get('age', user.age)
        user.course = request.data.get('course', user.course)
        user.year_graduate = request.data.get('year_graduate', user.year_graduate)
        user.save()
        
        # Send email only if alumni_id was updated
        if old_alumni_id != user.alumni_id:
            try:
                send_system_email(
                    subject='Alumni ID Updated - Alumni System',
                    message=f'Dear {user.first_name} {user.last_name},\n\nYour Alumni ID has been updated by an administrator.\n\nOld Alumni ID: {old_alumni_id}\nNew Alumni ID: {user.alumni_id}\n\nIf you did not request this change, please contact the administrator immediately.\n\nBest regards,\nAlumni Management Team',
                    recipient=user.email,
                )
            except Exception as e:
                return Response(
                    {"error": f"User updated, but email sending failed: {str(e)}"},
                    status=status.HTTP_200_OK,
                )
        
        return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["DELETE"])
def delete_user_api(request, user_id):
    """Delete a user"""
    try:
        user = CustomUser.objects.get(id=user_id, role="user")
        user.delete()
        return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["DELETE"])
def delete_staff_api(request, user_id):
    """Delete a staff member"""
    try:
        user = CustomUser.objects.get(id=user_id, role="staff")
        user.delete()
        return Response({"message": "Staff deleted successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
def update_staff_api(request, user_id):
    """Update a staff member"""
    try:
        user = CustomUser.objects.get(id=user_id)
        user.email = request.data.get('email', user.email)
        user.first_name = request.data.get('first_name', user.first_name)
        user.middle_name = request.data.get('middle_name', user.middle_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.gender = request.data.get('gender', user.gender)
        user.age = request.data.get('age', user.age)
        user.position = request.data.get('position', user.position)
        user.role = request.data.get('role', user.role)
        user.save()
        return Response({"message": "Staff updated successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def get_staff_profile_api(request):
    """Get staff profile by email"""
    email = request.GET.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email, role="staff")
        data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "gender": user.gender,
            "age": user.age,
            "position": user.position,
            "password_changed": user.password_changed,
            "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
        }
        return Response(data, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def change_password_api(request):
    """Change user password"""
    email = request.data.get('email')
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not all([email, current_password, new_password]):
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email)
        
        if user.role == "staff" and user.password_changed:
            return Response({"error": "You have already changed your password once. Contact admin for further changes."}, status=status.HTTP_403_FORBIDDEN)
        
        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        if user.role == "staff":
            user.password_changed = True
        user.save()
        
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_api(request):
    """Get current authenticated user's profile"""
    user = request.user
    return Response({
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "course": user.course,
        "year_graduate": user.year_graduate,
        "role": user.role,
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_user_profile_api(request):
    """Get user profile by email"""
    email = request.GET.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email, role="user")
        data = {
            "id": user.id,
            "alumni_id": user.alumni_id,
            "email": user.email,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "gender": user.gender,
            "age": user.age,
            "course": user.course,
            "year_graduate": user.year_graduate,
            "location": user.location,
            "contact_num": user.contact_num,
            "current_job": user.current_job,
            "company": user.company,
            "skills": user.skills,
            "bio": user.bio,
            "is_private": user.is_private,
            "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
        }
        return Response(data, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
def update_user_profile_api(request):
    """Update user's own profile"""
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email, role="user")
        user.first_name = request.data.get('first_name', user.first_name)
        user.middle_name = request.data.get('middle_name', user.middle_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.gender = request.data.get('gender', user.gender)
        user.age = request.data.get('age', user.age)
        user.course = request.data.get('course', user.course)
        user.year_graduate = request.data.get('year_graduate', user.year_graduate)
        user.location = request.data.get('location', user.location)
        user.contact_num = request.data.get('contact_num', user.contact_num)
        user.current_job = request.data.get('current_job', user.current_job)
        user.company = request.data.get('company', user.company)
        user.skills = request.data.get('skills', user.skills)
        user.bio = request.data.get('bio', user.bio)
        user.save()
        return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def toggle_privacy_api(request):
    """Toggle profile privacy for a user"""
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = CustomUser.objects.get(email=email, role="user")
        user.is_private = not user.is_private
        user.save()
        return Response({"is_private": user.is_private}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def send_registration_otp_api(request):
    """Send OTP to verify email during registration"""
    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    if CustomUser.objects.filter(email__iexact=email).exists():
        return Response({"error": "This email is already registered."}, status=status.HTTP_409_CONFLICT)
    code = ''.join(random.choices(string.digits, k=6))
    cache.set(f"reg_otp_{email}", code, timeout=600)
    try:
        send_system_email(
            subject='Email Verification Code - SCSIT Alumni',
            message=f'Your email verification code is: {code}\n\nThis code expires in 10 minutes.\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nSCSIT Alumni Management Team',
            recipient=email,
        )
    except Exception as e:
        return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({"message": "Verification code sent"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def verify_registration_otp_api(request):
    """Verify OTP for registration email"""
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code", "").strip()
    if not email or not code:
        return Response({"error": "Email and code are required"}, status=status.HTTP_400_BAD_REQUEST)
    cached_code = cache.get(f"reg_otp_{email}")
    if not cached_code or cached_code != code:
        return Response({"error": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)
    cache.delete(f"reg_otp_{email}")
    return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def check_email_api(request):
    """Check if email is already registered"""
    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    exists = CustomUser.objects.filter(email__iexact=email).exists()
    if exists:
        return Response({"error": "This email is already registered."}, status=status.HTTP_409_CONFLICT)
    return Response({"message": "Email is available"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def forgot_password_api(request):
    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({"error": "No account found with this email"}, status=status.HTTP_404_NOT_FOUND)

    code = ''.join(random.choices(string.digits, k=6))
    cache.set(f"reset_code_{email}", code, timeout=600)

    try:
        send_system_email(
            subject='Password Reset Code - Alumni System',
            message=f'Dear {user.first_name},\n\nYour password reset code is: {code}\n\nThis code expires in 10 minutes.\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nAlumni Management Team',
            recipient=email,
        )
    except Exception as e:
        return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Verification code sent to your email"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def verify_code_api(request):
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code")

    if not email or not code:
        return Response({"error": "Email and code are required"}, status=status.HTTP_400_BAD_REQUEST)

    cached_code = cache.get(f"reset_code_{email}")
    if not cached_code or cached_code != code:
        return Response({"error": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Code verified successfully"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def reset_password_api(request):
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if not all([email, code, new_password, confirm_password]):
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    cached_code = cache.get(f"reset_code_{email}")
    if not cached_code or cached_code != code:
        return Response({"error": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        cache.delete(f"reset_code_{email}")
        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def notifications_api(request):
    """Returns new pending user registrations, new event registrations, and new reports within last 24 hours"""
    from django.utils import timezone
    from datetime import timedelta
    from eventregister.models import EventRegistration
    from report.models import Report

    since = timezone.now() - timedelta(hours=24)

    new_users = CustomUser.objects.filter(
        role="user", status="pending"
    ).filter(
        models.Q(created_at__gte=since) | models.Q(created_at__isnull=True)
    ).order_by("-created_at").values(
        "id", "first_name", "last_name", "email", "created_at"
    )

    new_event_regs = EventRegistration.objects.filter(registration_date__gte=since).order_by("-registration_date").select_related("user", "event").values(
        "id", "user__first_name", "user__last_name", "user__email", "event__title", "registration_date"
    )

    new_reports = Report.objects.filter(created_at__gte=since).order_by("-created_at").values(
        "id", "name", "email", "message", "created_at", "user"
    )

    return Response({
        "new_users": list(new_users),
        "new_users_count": len(new_users),
        "new_event_regs": list(new_event_regs),
        "new_event_regs_count": len(new_event_regs),
        "new_reports": list(new_reports),
        "new_reports_count": len(new_reports),
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def user_notifications_api(request):
    """Returns new events, new jobs, and upcoming registered events (tomorrow) for logged-in users"""
    from django.utils import timezone
    from datetime import timedelta, date
    from addevent.models import Event
    from career.models import JobPost
    from eventregister.models import EventRegistration

    since = timezone.now() - timedelta(days=7)
    tomorrow = date.today() + timedelta(days=1)

    # New events posted in last 7 days
    new_events = list(Event.objects.filter(created_at__gte=since).order_by("-created_at").values(
        "id", "title", "date", "location", "created_at"
    ))

    # New jobs posted in last 7 days
    new_jobs = list(JobPost.objects.filter(date_posted__gte=since.date(), status="open").order_by("-date_posted").values(
        "id", "job_title", "company_name", "employment_type", "date_posted"
    ))

    # Upcoming registered events starting tomorrow (reminder)
    email = request.GET.get("email", "")
    upcoming_reminders = []
    if email:
        try:
            user = CustomUser.objects.get(email=email, role="user")
            regs = EventRegistration.objects.filter(user=user, event__date=tomorrow).select_related("event")
            upcoming_reminders = [
                {"id": r.id, "event_id": r.event.id, "title": r.event.title,
                 "date": str(r.event.date), "start_time": str(r.event.start_time), "location": r.event.location}
                for r in regs
            ]
        except CustomUser.DoesNotExist:
            pass

    return Response({
        "new_events": new_events,
        "new_jobs": new_jobs,
        "upcoming_reminders": upcoming_reminders,
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
def upload_profile_image_api(request):
    """Upload or update profile image for any user by email"""
    email = request.data.get("email", "").strip()
    image = request.FILES.get("profile_image")
    if not email or not image:
        return Response({"error": "Email and image are required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = CustomUser.objects.get(email=email)
        if user.profile_image:
            user.profile_image.delete(save=False)
        user.profile_image = image
        user.save()
        return Response({
            "message": "Profile image updated",
            "profile_image": request.build_absolute_uri(user.profile_image.url)
        }, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def directory_api(request):
    """Get all approved alumni for directory"""
    exclude_email = request.GET.get("email", "").strip()
    users = CustomUser.objects.filter(role="user", status="approved")
    if exclude_email:
        users = users.exclude(email__iexact=exclude_email)
    data = [{
        "id": user.id,
        "full_name": f"{user.first_name} {user.middle_name + ' ' if user.middle_name else ''}{user.last_name}",
        "course": user.course,
        "year_graduate": user.year_graduate,
        "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
        "current_job": user.current_job,
        "company": user.company,
        "location": user.location,
    } for user in users]
    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
def email_debug_api(request):
    diagnostics = smtp_connection_diagnostics()
    status_code = status.HTTP_200_OK if diagnostics["connect_ok"] else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(diagnostics, status=status_code)
