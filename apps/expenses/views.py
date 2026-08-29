from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.finance import engine
from apps.finance.models import Transaction, TransactionType


@login_required
def expenses_view(request):
    user = request.user
    now = timezone.now()

    breakdown = engine.get_expense_breakdown(user, as_of=now)
    total_this_month = sum(breakdown.values(), Decimal("0"))

    prev_as_of = now - timedelta(days=30)
    total_last_month = engine.get_monthly_expenses(user, as_of=prev_as_of)

    mom_change_pct = None
    if total_last_month > 0:
        mom_change_pct = ((total_this_month - total_last_month) / total_last_month * Decimal("100")).quantize(
            Decimal("0.1")
        )

    largest_category = max(breakdown.items(), key=lambda kv: kv[1], default=(None, Decimal("0")))

    recent_transactions = Transaction.objects.filter(
        user=user, transaction_type=TransactionType.EXPENSE
    ).order_by("-occurred_at")[:15]
    trend = []
    for days_ago in range(6, -1, -1):
        day = (now - timedelta(days=days_ago)).date()
        amount = Transaction.objects.filter(
            user=user, transaction_type=TransactionType.EXPENSE,
            occurred_at__date=day,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        trend.append({"label": day.strftime("%m/%d"), "amount": amount})
    trend_max = max((item["amount"] for item in trend), default=Decimal("0")) or Decimal("1")
    for item in trend:
        item["height"] = (item["amount"] / trend_max * Decimal("100")).quantize(Decimal("0.1"))

    context = {
        "breakdown": breakdown,
        "total_this_month": total_this_month,
        "total_last_month": total_last_month,
        "mom_change_pct": mom_change_pct,
        "largest_category": largest_category,
        "recent_transactions": recent_transactions,
        "trend": trend,
    }
    return render(request, "expenses/index.html", context)
