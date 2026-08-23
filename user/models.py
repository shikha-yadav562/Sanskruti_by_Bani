
#====================================================================================
#-------------------------LOGIN AND SIGNUP------------------------------------------
#====================================================================================
import uuid
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.utils import timezone

class AccountManager(BaseUserManager):
    def create_user(self, email: str, username: str, password: Optional[str] = None, **extra_fields) -> "Account":
        if not email:
            raise ValueError("Email is required.")
        if not username:
            raise ValueError("Username is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", Account.Role.USER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_admin(self, email: str, username: str, password: str, first_name: str = "", last_name: str = "") -> "Account":
        """
        Used only by the post_migrate signal in apps.py to seed the one
        predefined admin account. Never exposed through any public view.
        """
        return self.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=Account.Role.ADMIN,
            is_staff=True,
            is_superuser=False,
            is_active=True,
            email_verified=True,
        )

class Account(AbstractBaseUser):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # always False -- no permission framework used

    date_joined = models.DateTimeField(auto_now_add=True)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def is_locked(self) -> bool:
        return bool(self.locked_until and timezone.now() < self.locked_until)

    def register_failed_login(self) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.locked_until = timezone.now() + timedelta(minutes=self.LOCKOUT_MINUTES)
        self.save(update_fields=["failed_login_attempts", "locked_until"])

    def reset_failed_logins(self) -> None:
        if self.failed_login_attempts or self.locked_until:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_attempts", "locked_until"])

class OTPMixin(models.Model):
    """Shared OTP fields/logic -- hashed storage, expiry, attempt + resend limits."""
    EXPIRY_MINUTES = 5
    MAX_VERIFY_ATTEMPTS = 5
    MAX_RESEND_ATTEMPTS = 5
    RESEND_COOLDOWN_SECONDS = 60

    otp_hash = models.CharField(max_length=128)
    otp_created_at = models.DateTimeField(auto_now_add=True)
    verify_attempts = models.PositiveSmallIntegerField(default=0)
    resend_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        abstract = True

    def set_otp(self, raw_otp: str) -> None:
        self.otp_hash = make_password(raw_otp)
        self.otp_created_at = timezone.now()
        self.verify_attempts = 0

    def is_expired(self) -> bool:
        return timezone.now() > self.otp_created_at + timedelta(minutes=self.EXPIRY_MINUTES)

    def seconds_until_resend_allowed(self) -> int:
        elapsed = (timezone.now() - self.otp_created_at).total_seconds()
        remaining = self.RESEND_COOLDOWN_SECONDS - elapsed
        return max(0, int(remaining))

    def can_resend(self) -> bool:
        return self.resend_count < self.MAX_RESEND_ATTEMPTS and self.seconds_until_resend_allowed() == 0

    def check_otp(self, raw_otp: str) -> bool:
        if self.verify_attempts >= self.MAX_VERIFY_ATTEMPTS:
            return False
        matched = check_password(raw_otp, self.otp_hash)
        if not matched:
            self.verify_attempts += 1
            self.save(update_fields=['verify_attempts'])
        return matched

class PendingSignup(OTPMixin):
    """Holds a signup attempt until its OTP is confirmed. No Account row exists until then."""
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    password_hash = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"Pending signup: {self.email}"

class PasswordResetOTP(OTPMixin):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="password_reset")

    def __str__(self) -> str:
        return f"Password reset OTP for {self.account.email}"

class UsernameRecoveryOTP(OTPMixin):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="username_recovery")

    def __str__(self) -> str:
        return f"Username recovery OTP for {self.account.email}"

class LoginHistory(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="login_history",
        null=True, blank=True,
    )
    attempted_identifier = models.CharField(max_length=255)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Detailed User-Agent parsed fields
    user_agent = models.CharField(max_length=500, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=10, choices=Status.choices)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-login_time"]
        verbose_name_plural = "Login history"

class SecurityAuditLog(models.Model):
    """Minimal audit trail for security-relevant events."""
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    event = models.CharField(max_length=100)
    detail = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

#====================================================================================
#-------------------------END OF LOGIN AND SIGNUP------------------------------------------
#====================================================================================

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    address_type = models.CharField(max_length=20, choices=[('home', 'Home'), ('office', 'Office')], default='home')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.city} ({self.pincode})"


class ProductReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    product_slug = models.CharField(max_length=200, default='anuradha-paithani-saree')
    product_name = models.CharField(max_length=200, default='Anuradha Paithani Soft Peacock Design Saree')
    rating = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    image_1 = models.ImageField(upload_to='reviews/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='reviews/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='reviews/', blank=True, null=True)
    is_approved = models.BooleanField(default=True)
    is_verified_buyer = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.rating}★ by {self.user.full_name if self.user else 'Guest'}"


class ReviewHelpful(models.Model):
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('review', 'user'), ('review', 'session_key')]
