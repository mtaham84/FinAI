from django.contrib import admin

from .models import (
    Asset,
    FinancialAccount,
    Goal,
    Holding,
    Income,
    Installment,
    Liability,
    Portfolio,
    RiskProfile,
    Transaction,
)

admin.site.register(FinancialAccount)
admin.site.register(Transaction)
admin.site.register(Income)
admin.site.register(Asset)
admin.site.register(Liability)
admin.site.register(Installment)
admin.site.register(RiskProfile)
admin.site.register(Goal)
admin.site.register(Portfolio)
admin.site.register(Holding)
