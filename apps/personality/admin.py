from django.contrib import admin

from .models import PersonalityAssessment, PersonalityResult

admin.site.register(PersonalityAssessment)
admin.site.register(PersonalityResult)
