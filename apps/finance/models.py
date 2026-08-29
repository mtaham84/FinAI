import uuid

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserOwnedModel(TimeStampedModel):
    """
    Base class enforcing object-level ownership. Every finance query
    in views/services MUST filter by user -- see apps.finance.engine
    for the pattern all read paths should follow.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True


class AssetClass(models.TextChoices):
    CASH = "cash", "پول نقد"
    BANK = "bank", "سپرده بانکی"
    GOLD = "gold", "طلا"
    SILVER = "silver", "نقره"
    CRYPTO = "crypto", "رمزارز"
    STOCK = "stock", "سهام"
    OTHER = "other", "سایر"


class FinancialAccount(UserOwnedModel):
    """
    A holding location for money or assets: a bank account, a crypto
    wallet, a brokerage account, or a manually-tracked cash balance.
    Real provider connectivity is added later via
    apps.integrations.providers -- for now `provider_connection` is
    always null and `is_mock` marks demo data.
    """

    name = models.CharField(max_length=120)
    asset_class = models.CharField(max_length=20, choices=AssetClass.choices)
    institution_name = models.CharField(max_length=120, blank=True)
    current_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="IRT")  # Toman
    is_mock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["user", "asset_class"])]

    def __str__(self):
        return f"{self.name} ({self.get_asset_class_display()})"


class TransactionCategory(models.TextChoices):
    HOUSING = "housing", "مسکن"
    FOOD = "food", "خوراک"
    SHOPPING = "shopping", "خرید"
    TRANSPORTATION = "transportation", "حمل‌ونقل"
    ENTERTAINMENT = "entertainment", "سرگرمی"
    TRAVEL = "travel", "سفر"
    HEALTHCARE = "healthcare", "سلامت"
    EDUCATION = "education", "آموزش"
    BILLS = "bills", "قبوض"
    OTHER = "other", "سایر"


class TransactionType(models.TextChoices):
    EXPENSE = "expense", "هزینه"
    INCOME = "income", "درآمد"
    TRANSFER = "transfer", "انتقال"


class Transaction(UserOwnedModel):
    account = models.ForeignKey(
        FinancialAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    category = models.CharField(
        max_length=20, choices=TransactionCategory.choices, default=TransactionCategory.OTHER
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    merchant = models.CharField(max_length=120, blank=True)
    occurred_at = models.DateTimeField(db_index=True)
    is_mock = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "occurred_at"]),
            models.Index(fields=["user", "category", "occurred_at"]),
        ]
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount} ({self.category})"


class Income(UserOwnedModel):
    """Recurring or one-off income records used for savings-rate and liquidity calculations."""

    source = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    is_recurring = models.BooleanField(default=True)
    received_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["user", "received_at"])]


class Asset(UserOwnedModel):
    """Non-cash assets: gold, silver, crypto holdings valued in aggregate (see Holding for per-symbol detail)."""

    asset_class = models.CharField(max_length=20, choices=AssetClass.choices)
    label = models.CharField(max_length=120)
    quantity = models.DecimalField(max_digits=24, decimal_places=8, default=1)
    unit_value = models.DecimalField(max_digits=18, decimal_places=2)
    is_mock = models.BooleanField(default=True)

    @property
    def total_value(self):
        return self.quantity * self.unit_value


class LiabilityType(models.TextChoices):
    LOAN = "loan", "وام"
    CREDIT_CARD = "credit_card", "کارت اعتباری"
    BNPL = "bnpl", "خرید اقساطی"
    OTHER = "other", "سایر"


class Liability(UserOwnedModel):
    liability_type = models.CharField(max_length=20, choices=LiabilityType.choices)
    label = models.CharField(max_length=120)
    outstanding_balance = models.DecimalField(max_digits=18, decimal_places=2)
    is_mock = models.BooleanField(default=True)


class Installment(UserOwnedModel):
    """BNPL / credit obligations with a due schedule -- foundation for Digipay/SnappPay/TorobPay integrations."""

    liability = models.ForeignKey(
        Liability, on_delete=models.CASCADE, related_name="installments"
    )
    amount_due = models.DecimalField(max_digits=18, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)


class RiskLevel(models.TextChoices):
    LOW = "low", "کم"
    MEDIUM = "medium", "متوسط"
    HIGH = "high", "زیاد"


class InvestmentHorizon(models.TextChoices):
    SHORT = "short", "کوتاه‌مدت"
    MEDIUM = "medium", "میان‌مدت"
    LONG = "long", "بلندمدت"


class RiskProfile(UserOwnedModel):
    """
    Deterministic risk boundaries used to guard any future AI
    recommendation. This is intentionally independent of the
    MBTI-style PersonalityResult -- see apps.personality.
    """

    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    investment_horizon = models.CharField(
        max_length=10, choices=InvestmentHorizon.choices, default=InvestmentHorizon.MEDIUM
    )
    liquidity_preference = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    max_crypto_allocation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    max_single_asset_concentration_pct = models.DecimalField(max_digits=5, decimal_places=2, default=25)
    emergency_reserve_months = models.PositiveSmallIntegerField(default=3)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user"], name="one_risk_profile_per_user")]


class Goal(UserOwnedModel):
    """Foundation for the future deterministic Goal Engine (see apps.goals)."""

    title = models.CharField(max_length=150)
    target_amount = models.DecimalField(max_digits=18, decimal_places=2)
    current_allocation = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    is_achieved = models.BooleanField(default=False)

    @property
    def funding_gap(self):
        return max(self.target_amount - self.current_allocation, 0)


class Portfolio(UserOwnedModel):
    name = models.CharField(max_length=120, default="سبد اصلی")
    is_mock = models.BooleanField(default=True)


class Holding(UserOwnedModel):
    """Per-symbol position within a Portfolio (stocks, crypto, etc.)."""

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    asset_class = models.CharField(max_length=20, choices=AssetClass.choices)
    symbol = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    average_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    current_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    @property
    def market_value(self):
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self):
        return (self.current_price - self.average_cost) * self.quantity
