from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailOrPhoneBackend(ModelBackend):
    """
    Authenticates against either the email or phone_number field.
    Always runs password hashing even on a miss (via a dummy hasher
    check) to keep response timing similar for existing vs.
    non-existing identifiers -- a mitigation against user enumeration
    via timing side channels.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("identifier")
        if not identifier or not password:
            return None

        try:
            if "@" in identifier:
                user = User.objects.get(email__iexact=identifier)
            else:
                user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            User().set_password(password)  # constant-time-ish dummy hash
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
