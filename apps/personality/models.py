import uuid

from django.conf import settings
from django.db import models


class AssessmentType(models.TextChoices):
    MBTI = "mbti", "شخصیت به سبک MBTI"
    GENERAL = "general", "شخصیت عمومی"
    FINANCIAL_RISK = "financial_risk", "شخصیت و ریسک مالی"


class PersonalityAssessment(models.Model):
    """
    A template for a questionnaire. IMPORTANT: assessment results here
    are informational personality insight only -- they are NEVER used
    directly as a financial decision engine. Actual investment
    boundaries always come from apps.finance.models.RiskProfile.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment_type = models.CharField(max_length=20, choices=AssessmentType.choices)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class PersonalityResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personality_results")
    assessment = models.ForeignKey(PersonalityAssessment, on_delete=models.CASCADE, related_name="results")
    result_label = models.CharField(max_length=50)  # e.g. "ENTJ"
    raw_scores = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.result_label}"
