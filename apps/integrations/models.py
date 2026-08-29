import uuid

from django.conf import settings
from django.db import models


class ProviderConnection(models.Model):
    """
    Foundation for future real integrations. Stores only an opaque,
    encrypted-at-rest authorization token reference -- never a raw
    bank password, CVV2, card PIN, or dynamic password. No
    connections exist in the two-week MVP; this table is created so
    the schema doesn't need to change later.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONNECTED = "connected", "Connected"
        REVOKED = "revoked", "Revoked"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="provider_connections")
    provider_key = models.CharField(max_length=40)  # matches BaseProvider.provider_key
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    external_account_ref = models.CharField(max_length=255, blank=True)
    # Encrypted token reference only -- actual secret lives in a secrets
    # manager / vault in production, never in this column as plaintext.
    token_reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user", "provider_key"])]
