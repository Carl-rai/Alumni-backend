from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not password:
            raise ValueError("Password is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    
    def create_superuser(self, email, password=None, **extra_fields):
        if not password:
            raise ValueError("Superuser must have a password.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)



class CustomUser(AbstractBaseUser, PermissionsMixin):

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
    ]

    ROLE_CHOICES = [
        ("user", "User"),
        ("staff", "Staff"),
        ("id-staff", "ID Staff"),
        ("admin", "Admin"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # Common fields
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    # User (alumni) specific fields
    alumni_id = models.CharField(unique=True, max_length=30, null=True, blank=True)
    course = models.CharField(max_length=100, null=True, blank=True)
    year_graduate = models.PositiveIntegerField(null=True, blank=True)
    location = models.CharField(max_length=150, null=True, blank=True)
    contact_num = models.CharField(max_length=20, null=True, blank=True)
    current_job = models.CharField(max_length=150, null=True, blank=True)
    company = models.CharField(max_length=150, null=True, blank=True)
    skills = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    # Staff/Admin specific fields
    position = models.CharField(max_length=100, null=True, blank=True)
    password_changed = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "gender",
        "age",
    ]

    def __str__(self):
        if self.role == "user":
            return f"{self.alumni_id} - {self.email}"
        return f"{self.email} - {self.role}"


class AuditLog(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("id-staff", "ID Staff"),
        ("user", "User"),
        ("anonymous", "Anonymous"),
        ("system", "System"),
    ]

    actor_email = models.EmailField(null=True, blank=True)
    actor_name = models.CharField(max_length=150, null=True, blank=True)
    actor_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="anonymous")
    action = models.CharField(max_length=120)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    resource = models.CharField(max_length=100, null=True, blank=True)
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    success = models.BooleanField(default=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["actor_role", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} - {self.actor_role} - {self.action}"
