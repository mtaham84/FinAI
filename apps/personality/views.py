from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.finance.models import RiskProfile

from .models import PersonalityAssessment, PersonalityResult


@login_required
def personality_home_view(request):
    assessments = PersonalityAssessment.objects.filter(is_active=True)
    latest_results = PersonalityResult.objects.filter(user=request.user).select_related("assessment")[:5]
    risk_profile = RiskProfile.objects.filter(user=request.user).first()

    context = {
        "assessments": assessments,
        "latest_results": latest_results,
        "risk_profile": risk_profile,
    }
    return render(request, "personality/index.html", context)
