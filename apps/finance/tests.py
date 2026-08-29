from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from . import engine
from .models import (
    AssetClass,
    FinancialAccount,
    Goal,
    Income,
    Liability,
    LiabilityType,
    RiskProfile,
    Transaction,
    TransactionCategory,
    TransactionType,
)

User = get_user_model()


def make_user(email="user@example.com"):
    return User.objects.create_user(email=email, password="Str0ng-Passw0rd!")


class FinancialSummaryTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.other_user = make_user("other@example.com")
        now = timezone.now()

        FinancialAccount.objects.create(
            user=self.user, name="Cash", asset_class=AssetClass.CASH, current_balance=Decimal("280000000")
        )
        FinancialAccount.objects.create(
            user=self.user, name="Gold Vault", asset_class=AssetClass.GOLD, current_balance=Decimal("60000000")
        )
        FinancialAccount.objects.create(
            user=self.user, name="Silver Vault", asset_class=AssetClass.SILVER, current_balance=Decimal("12000000")
        )
        FinancialAccount.objects.create(
            user=self.user, name="Crypto Wallet", asset_class=AssetClass.CRYPTO, current_balance=Decimal("40000000")
        )
        FinancialAccount.objects.create(
            user=self.user, name="Brokerage", asset_class=AssetClass.STOCK, current_balance=Decimal("120000000")
        )
        Liability.objects.create(
            user=self.user,
            liability_type=LiabilityType.LOAN,
            label="Car Loan",
            outstanding_balance=Decimal("80000000"),
        )
        Income.objects.create(
            user=self.user, source="Salary", amount=Decimal("45000000"), received_at=now - timezone.timedelta(days=5)
        )
        Transaction.objects.create(
            user=self.user,
            account=FinancialAccount.objects.filter(user=self.user, asset_class=AssetClass.CASH).first(),
            transaction_type=TransactionType.EXPENSE,
            category=TransactionCategory.FOOD,
            amount=Decimal("18000000"),
            occurred_at=now - timezone.timedelta(days=3),
        )
        Transaction.objects.create(
            user=self.user,
            account=FinancialAccount.objects.filter(user=self.user, asset_class=AssetClass.CASH).first(),
            transaction_type=TransactionType.EXPENSE,
            category=TransactionCategory.HOUSING,
            amount=Decimal("10000000"),
            occurred_at=now - timezone.timedelta(days=10),
        )

        # A record belonging to a different user must never leak into totals.
        FinancialAccount.objects.create(
            user=self.other_user, name="Other Cash", asset_class=AssetClass.CASH, current_balance=Decimal("999999999")
        )

    def test_net_worth_equals_assets_minus_liabilities(self):
        summary = engine.build_financial_summary(self.user)
        expected_assets = Decimal("280000000") + Decimal("60000000") + Decimal("12000000") + Decimal(
            "40000000"
        ) + Decimal("120000000")
        self.assertEqual(summary.total_assets, expected_assets)
        self.assertEqual(summary.total_debt, Decimal("80000000"))
        self.assertEqual(summary.net_worth, expected_assets - Decimal("80000000"))

    def test_monthly_expenses_sum_within_window(self):
        expenses = engine.get_monthly_expenses(self.user)
        self.assertEqual(expenses, Decimal("28000000"))

    def test_savings_rate_calculation(self):
        summary = engine.build_financial_summary(self.user)
        # income 45M, expenses 28M -> savings 17M -> rate = 17/45*100
        expected_rate = (Decimal("17000000") / Decimal("45000000") * Decimal("100")).quantize(Decimal("0.1"))
        self.assertEqual(summary.savings_rate_pct, expected_rate)

    def test_savings_rate_is_zero_with_no_income(self):
        user2 = make_user("noincome@example.com")
        summary = engine.build_financial_summary(user2)
        self.assertEqual(summary.savings_rate_pct, Decimal("0"))

    def test_user_data_isolation(self):
        """A user's financial summary must never include another user's records."""
        summary = engine.build_financial_summary(self.user)
        self.assertNotEqual(summary.total_assets, Decimal("999999999"))
        other_summary = engine.build_financial_summary(self.other_user)
        self.assertEqual(other_summary.total_assets, Decimal("999999999"))

    def test_allocation_percentages_sum_close_to_100(self):
        summary = engine.build_financial_summary(self.user)
        total_pct = sum((slice_.pct for slice_ in summary.allocation), Decimal("0"))
        self.assertAlmostEqual(float(total_pct), 100.0, delta=0.5)

    def test_expense_breakdown_by_category(self):
        breakdown = engine.get_expense_breakdown(self.user)
        self.assertEqual(breakdown[TransactionCategory.FOOD], Decimal("18000000"))
        self.assertEqual(breakdown[TransactionCategory.HOUSING], Decimal("10000000"))


class InvestableCapitalTests(TestCase):
    def setUp(self):
        self.user = make_user()
        now = timezone.now()
        FinancialAccount.objects.create(
            user=self.user, name="Cash", asset_class=AssetClass.CASH, current_balance=Decimal("300000000")
        )
        Income.objects.create(
            user=self.user, source="Salary", amount=Decimal("50000000"), received_at=now - timezone.timedelta(days=5)
        )
        Transaction.objects.create(
            user=self.user,
            account=FinancialAccount.objects.filter(user=self.user).first(),
            transaction_type=TransactionType.EXPENSE,
            category=TransactionCategory.OTHER,
            amount=Decimal("30000000"),
            occurred_at=now - timezone.timedelta(days=5),
        )
        RiskProfile.objects.create(user=self.user, emergency_reserve_months=3)

    def test_investable_capital_subtracts_emergency_reserve(self):
        # emergency reserve = 3 * 30M = 90M ; no near-term goals; no debt
        investable = engine.calculate_investable_capital(self.user)
        self.assertEqual(investable, Decimal("300000000") - Decimal("90000000"))

    def test_investable_capital_never_negative(self):
        Liability.objects.create(
            user=self.user,
            liability_type=LiabilityType.LOAN,
            label="Big Loan",
            outstanding_balance=Decimal("500000000"),
        )
        investable = engine.calculate_investable_capital(self.user)
        self.assertEqual(investable, Decimal("0"))

    def test_investable_capital_reduced_by_near_term_goal(self):
        today = timezone.now().date()
        Goal.objects.create(
            user=self.user,
            title="Buy a car",
            target_amount=Decimal("100000000"),
            current_allocation=Decimal("20000000"),
            deadline=today + timezone.timedelta(days=30),
        )
        investable = engine.calculate_investable_capital(self.user)
        # 300M - 90M reserve - (100M-20M goal gap) = 130M
        self.assertEqual(investable, Decimal("130000000"))


class GoalTests(TestCase):
    def test_funding_gap_never_negative(self):
        user = make_user()
        goal = Goal.objects.create(
            user=user, title="Emergency Fund", target_amount=Decimal("10000000"), current_allocation=Decimal("15000000")
        )
        self.assertEqual(goal.funding_gap, Decimal("0"))
