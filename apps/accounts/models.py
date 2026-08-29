import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Users can register with email OR phone number, so neither field is
    globally required at the DB level -- but at least one must be set
    (enforced in forms / serializers, not here, to keep the model simple).
    """

    use_in_migrations = True

    def _create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError("A user must have an email or a phone number.")
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, phone_number, password, **extra_fields)

    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Core identity record only. NEVER add banking credentials, card
    numbers, CVV2, PINs, or dynamic passwords to this model or any
    related model. Future provider integrations must use tokenized
    authorization (see apps.integrations.providers) rather than
    storing raw secrets.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    full_name = models.CharField(max_length=150, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(email__isnull=False) | models.Q(phone_number__isnull=False),
                name="user_has_email_or_phone",
            )
        ]

    def __str__(self):
        return self.email or self.phone_number or str(self.id)

    @property
    def display_identifier(self):
        return self.email or self.phone_number


class EmailVerificationToken(models.Model):
    """Architecture for future email verification. Tokens are single-use and hashed."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_tokens")
    token_hash = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at


class PhoneOTP(models.Model):
    """
    Architecture placeholder for future SMS-based OTP verification.
    No SMS provider is wired up yet -- code delivery is intentionally
    unimplemented. Only the hashed code and expiry are stored.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phone_otps")
    phone_number = models.CharField(max_length=20)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)

    def is_valid(self):
        return self.consumed_at is None and timezone.now() < self.expires_at


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token_hash = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    requested_ip = models.GenericIPAddressField(null=True, blank=True)

    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at


class LoginAttempt(models.Model):
    """Audit trail used for throttling and account-enumeration-resistant lockout logic."""

    identifier = models.CharField(max_length=255, db_index=True)  # email or phone, not raw password
    ip_address = models.GenericIPAddressField()
    was_successful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["identifier", "created_at"])]
