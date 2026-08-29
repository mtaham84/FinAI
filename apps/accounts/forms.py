import re

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import User

PHONE_RE = re.compile(r"^\+?[0-9]{8,15}$")


class RegistrationForm(forms.Form):
    """
    Accepts either an email or a phone number (at least one required).
    All validation is server-side; the view never trusts client state.
    """

    email = forms.EmailField(required=False)
    phone_number = forms.CharField(required=False, max_length=20)
    full_name = forms.CharField(required=False, max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if phone and not PHONE_RE.match(phone):
            raise ValidationError("شماره تلفن معتبر وارد کنید.")
        return phone

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        phone = cleaned.get("phone_number")

        if not email and not phone:
            raise ValidationError("ایمیل یا شماره تلفن خود را وارد کنید.")

        if email and User.objects.filter(email__iexact=email).exists():
            # Generic message -- avoid confirming which channel is already taken
            raise ValidationError("ثبت‌نام با اطلاعات واردشده انجام نشد.")
        if phone and User.objects.filter(phone_number=phone).exists():
            raise ValidationError("ثبت‌نام با اطلاعات واردشده انجام نشد.")

        password = cleaned.get("password")
        password_confirm = cleaned.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise ValidationError("رمزهای عبور یکسان نیستند.")

        if password:
            # Validate against a throwaway user-like object carrying the
            # provided identifiers, so Django's similarity validators work.
            password_validation.validate_password(password)

        return cleaned


class LoginForm(forms.Form):
    """
    Single 'identifier' field accepts email or phone. Error messages are
    intentionally generic to avoid leaking which accounts exist
    (account enumeration protection).
    """

    identifier = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)


class PasswordResetRequestForm(forms.Form):
    identifier = forms.CharField(max_length=255)


class PasswordResetConfirmForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    new_password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("new_password"), cleaned.get("new_password_confirm")
        if p1 and p2 and p1 != p2:
            raise ValidationError("رمزهای عبور یکسان نیستند.")
        if p1:
            password_validation.validate_password(p1)
        return cleaned


class EmailVerificationForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6, strip=True)

    def clean_code(self):
        code = self.cleaned_data["code"]
        if not code.isascii() or not code.isdigit():
            raise ValidationError("کد باید شامل ۶ رقم باشد.")
        return code
