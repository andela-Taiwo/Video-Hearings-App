from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from courts.models import Court


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError("Email address is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create a regular user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_email_verified", True)
        extra_fields.setdefault("is_admin_approved", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def get_verified_users(self):
        """Get all verified users."""
        return self.filter(is_verified=True)

    def get_pending_approval(self):
        """Get users pending admin approval."""
        return self.filter(is_admin_approved=False, is_email_verified=True)

    def get_active_users(self):
        """Get active users (who have logged in within last 30 days)."""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return self.filter(last_login__gte=thirty_days_ago)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email as username."""

    username = None
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, db_index=True, validators=[EmailValidator()])

    # Verification fields
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    # Token fields for email verification
    verification_token = models.CharField(max_length=255, null=True, blank=True)
    verification_token_created = models.DateTimeField(null=True, blank=True)

    # Phone number (optional)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message=_("Phone number must be in international format"),
            )
        ],
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=["email", "is_verified"]),
            models.Index(fields=["is_admin_approved", "is_email_verified"]),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        elif self.first_name:
            return self.first_name
        return self.email

    def verify_email(self, token):
        """Verify email with token."""
        if self.verification_token == token:
            self.is_email_verified = True
            self.verification_token = None
            self.verification_token_created = None
            self._update_verification_status()
            self.save(
                update_fields=[
                    "is_email_verified",
                    "verification_token",
                    "verification_token_created",
                    "is_verified",
                ]
            )
            return True
        return False

    def _update_verification_status(self):
        """Update overall verification status."""
        self.is_verified = self.is_email_verified and self.is_admin_approved

    def admin_approve(self):
        """Approve user by admin."""
        self.is_admin_approved = True
        self._update_verification_status()
        self.save(update_fields=["is_admin_approved", "is_verified"])

    def admin_reject(self):
        """Reject user by admin."""
        self.is_admin_approved = False
        self._update_verification_status()
        self.save(update_fields=["is_admin_approved", "is_verified"])

    def has_permission(self, resource, action):
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True

        try:
            profile = self.profile
            return profile.roles.filter(
                permissions__resource=resource, permissions__action=action
            ).exists()
        except UserProfile.DoesNotExist:
            return False

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()

        super().save(*args, **kwargs)


class UserProfileManager(models.Manager):
    """Manager for UserProfile model with role-specific queries."""

    def get_by_role(self, role):
        """Get profiles by role."""
        return self.filter(role=role)

    def get_lawyers(self):
        """Get all lawyer profiles."""
        return self.filter(role=UserProfile.Role.LAWYER)

    def get_judges(self):
        """Get all judge profiles."""
        return self.filter(role=UserProfile.Role.JUDGE)


class UserProfile(models.Model):
    """Extended user profile with role-specific fields."""

    class Role(models.TextChoices):
        JUDGE = "judge", _("Judge")
        LAWYER = "lawyer", _("Lawyer")
        CLERK = "clerk", _("Clerk")
        DEFENDANT = "defendant", _("Defendant")
        WITNESS = "witness", _("Witness")
        PROSECUTOR = "prosecutor", _("Prosecutor")
        PUBLIC = "public", _("Public")
        ADMIN = "admin", _("Administrator")

    id = models.UUIDField(default=uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", primary_key=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, db_index=True)

    # Professional fields
    bar_number = models.CharField(max_length=50, blank=True)  # For lawyers
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name="user_court",
        blank=True,
        null=True,
    )
    specialization = models.CharField(max_length=100, blank=True)  # Area of expertise

    # Profile metadata
    profile_picture = models.ImageField(
        upload_to="profile_pics/%Y/%m/%d/", blank=True, null=True
    )
    bio = models.TextField(blank=True)
    office_address = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserProfileManager()

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["bar_number"]),
            models.Index(fields=["court_id"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.role}"

    def clean(self):
        """Validate model fields."""
        super().clean()

        if self.role == self.Role.LAWYER and not self.bar_number:
            raise ValidationError(
                {"bar_number": _("Bar number is required for lawyers")}
            )

        if self.role in [self.Role.JUDGE, self.Role.CLERK] and not self.court_id:
            raise ValidationError(
                {"court_id": _(f"Court ID is required for {self.role}s")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def has_role(self, role):
        """Check if user has a specific role."""
        return self.role == role
