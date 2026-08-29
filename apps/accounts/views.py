import hashlib
import secrets

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from .forms import (
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    RegistrationForm,
)
from .models import LoginAttempt, PasswordResetToken, User

GENERIC_LOGIN_ERROR = "اطلاعات ورود نادرست است. دوباره تلاش کنید."
GENERIC_RESET_MESSAGE = (
    "اگر حسابی با این مشخصات وجود داشته باشد، دستورالعمل بازیابی رمز عبور ارسال شده است."
)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@never_cache
@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="10/h", method="POST", block=True)
def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        user = User.objects.create_user(
            email=data.get("email") or None,
            phone_number=data.get("phone_number") or None,
            password=data["password"],
            full_name=data.get("full_name", ""),
        )
        login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
        request.session.cycle_key()  # rotate session id on privilege change
        return redirect("core:dashboard")

    return render(request, "accounts/register.html", {"form": form})


@never_cache
@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="20/h", method="POST", block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = LoginForm(request.POST or None)
    error = None

    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["identifier"]
        password = form.cleaned_data["password"]
        ip = _client_ip(request)

        recent_failures = LoginAttempt.objects.filter(
            identifier=identifier,
            was_successful=False,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=15),
        ).count()

        if recent_failures >= 8:
            error = GENERIC_LOGIN_ERROR  # locked out, but message stays generic
        else:
            user = authenticate(request, username=identifier, password=password)
            LoginAttempt.objects.create(
                identifier=identifier, ip_address=ip, was_successful=bool(user)
            )
            if user is not None and user.is_active:
                login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
                request.session.cycle_key()
                user.last_login_ip = ip
                user.save(update_fields=["last_login_ip"])
                return redirect("core:dashboard")
            error = GENERIC_LOGIN_ERROR

    return render(request, "accounts/login.html", {"form": form, "error": error})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return redirect("core:landing")


@never_cache
@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="5/h", method="POST", block=True)
def password_reset_request_view(request):
    """
    Always returns the same generic message regardless of whether the
    identifier matches a real account (enumeration protection). Token
    delivery (email/SMS) is architecture-only for now -- no provider
    is wired up.
    """
    form = PasswordResetRequestForm(request.POST or None)
    message = None

    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["identifier"]
        user = (
            User.objects.filter(email__iexact=identifier).first()
            or User.objects.filter(phone_number=identifier).first()
        )
        if user:
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            PasswordResetToken.objects.create(
                user=user,
                token_hash=token_hash,
                expires_at=timezone.now() + timezone.timedelta(hours=1),
                requested_ip=_client_ip(request),
            )
            # TODO(future): dispatch raw_token via email/SMS provider.
            # Never log or render raw_token in a response.
        message = GENERIC_RESET_MESSAGE

    return render(request, "accounts/password_reset_request.html", {"form": form, "message": message})


@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_confirm_view(request, token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    reset_token = PasswordResetToken.objects.filter(token_hash=token_hash).first()

    if not reset_token or not reset_token.is_valid():
        return render(request, "accounts/password_reset_invalid.html", status=400)

    form = PasswordResetConfirmForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = reset_token.user
            user.set_password(form.cleaned_data["new_password"])
            user.save(update_fields=["password"])
            reset_token.used_at = timezone.now()
            reset_token.save(update_fields=["used_at"])
            return redirect("accounts:login")
        except ValidationError:
            pass

    return render(request, "accounts/password_reset_confirm.html", {"form": form})
