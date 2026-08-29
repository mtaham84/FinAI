import uuid

from django.conf import settings
from django.db import models


class AIConversation(models.Model):
    """Placeholder for future chat-with-your-finances sessions. No LLM is wired up yet."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_conversations")
    created_at = models.DateTimeField(auto_now_add=True)


class AIRecommendation(models.Model):
    """
    Any future AI-generated suggestion must be stored here with the
    deterministic inputs it was based on, and must pass through the
    RiskProfile boundaries in apps.finance before ever being shown
    as actionable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_recommendations")
    conversation = models.ForeignKey(AIConversation, on_delete=models.SET_NULL, null=True, blank=True)
    summary = models.TextField()
    based_on = models.JSONField(default=dict, blank=True)
    was_shown = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    """Foundation for tracking sensitive actions (logins, financial edits, AI recommendations shown)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
