import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import DailyQuote
from apps.finance.models import (
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
from apps.personality.models import AssessmentType, PersonalityAssessment

User = get_user_model()

DEMO_EMAIL = "demo@finai.app"
DEMO_PASSWORD = "DemoUser-2026!"

QUOTES = [
    ("تصمیم‌های کوچک مالی، نتایج بزرگی می‌سازند.", ""),
    ("بودجه یعنی به پولتان بگویید کجا برود، نه اینکه بعداً بپرسید کجا رفت.", "جان سی. مکسول"),
    ("آنچه پس از خرج‌کردن باقی می‌ماند پس‌انداز نکنید؛ آنچه پس از پس‌انداز باقی می‌ماند خرج کنید.", "وارن بافت"),
    ("بدانید چه چیزی دارید و چرا آن را دارید.", "پیتر لینچ"),
    ("بازار سهام پول را از افراد عجول به افراد صبور منتقل می‌کند.", "وارن بافت"),
    ("آزادی مالی برای کسانی در دسترس است که درباره آن یاد می‌گیرند و برایش تلاش می‌کنند.", "رابرت کیوساکی"),
    ("مراقب هزینه‌های کوچک باشید؛ یک نشتی کوچک می‌تواند کشتی بزرگی را غرق کند.", "بنجامین فرانکلین"),
]

CATEGORY_MERCHANTS = {
    TransactionCategory.HOUSING: ["پرداخت اجاره", "مدیریت ساختمان"],
    TransactionCategory.FOOD: ["اسنپ‌فود", "فروشگاه محلی", "کافه"],
    TransactionCategory.SHOPPING: ["دیجی‌کالا", "ترب"],
    TransactionCategory.TRANSPORTATION: ["اسنپ", "کارت مترو"],
    TransactionCategory.ENTERTAINMENT: ["سینما", "فیلیمو"],
    TransactionCategory.TRAVEL: ["پرواز", "رزرو هتل"],
    TransactionCategory.HEALTHCARE: ["داروخانه", "درمانگاه"],
    TransactionCategory.EDUCATION: ["دوره آنلاین", "کتاب‌فروشی"],
    TransactionCategory.BILLS: ["قبض برق", "اینترنت", "شارژ تلفن"],
    TransactionCategory.OTHER: ["سایر"],
}


class Command(BaseCommand):
    help = "Seed (or reset) realistic demo data for the FinAI dashboard."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo user's data before reseeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding daily quotes...")
        for text, author in QUOTES:
            DailyQuote.objects.get_or_create(text=text, defaults={"author": author})

        self.stdout.write("Seeding personality assessment catalog...")
        PersonalityAssessment.objects.get_or_create(
            assessment_type=AssessmentType.MBTI,
            title="ارزیابی شخصیت به سبک MBTI",
            defaults={
                "description": "یک ارزیابی کوتاه برای شناخت شخصیت بر اساس مدل چهارمحوری کلاسیک؛ "
                "این ارزیابی ابزار تصمیم‌گیری مالی نیست."
            },
        )
        PersonalityAssessment.objects.get_or_create(
            assessment_type=AssessmentType.FINANCIAL_RISK,
            title="شخصیت و ریسک مالی",
            defaults={
                "description": "برای تعیین نقطه شروع پروفایل ریسک دقیق شما استفاده می‌شود؛ "
                "این پروفایل شامل سطح ریسک، افق سرمایه‌گذاری و ترجیح نقدینگی است."
            },
        )

        user, created = User.objects.get_or_create(
            email=DEMO_EMAIL, defaults={"full_name": "Taha Demo", "email_verified": True}
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo user {DEMO_EMAIL} / {DEMO_PASSWORD}"))
        elif options["reset"]:
            self.stdout.write("Resetting existing demo user's data...")
            FinancialAccount.objects.filter(user=user).delete()
            Transaction.objects.filter(user=user).delete()
            Income.objects.filter(user=user).delete()
            Liability.objects.filter(user=user).delete()
            Goal.objects.filter(user=user).delete()
            RiskProfile.objects.filter(user=user).delete()

        if FinancialAccount.objects.filter(user=user).exists() and not options["reset"]:
            self.stdout.write(self.style.WARNING("Demo user already has data. Use --reset to reseed."))
            return

        now = timezone.now()

        accounts = {
            AssetClass.CASH: FinancialAccount.objects.create(
                user=user, name="پول نقد", asset_class=AssetClass.CASH,
                current_balance=Decimal("280000000"),
            ),
            AssetClass.GOLD: FinancialAccount.objects.create(
                user=user, name="دارایی طلا", asset_class=AssetClass.GOLD,
                current_balance=Decimal("60000000"),
            ),
            AssetClass.SILVER: FinancialAccount.objects.create(
                user=user, name="دارایی نقره", asset_class=AssetClass.SILVER,
                current_balance=Decimal("12000000"),
            ),
            AssetClass.CRYPTO: FinancialAccount.objects.create(
                user=user, name="کیف‌پول رمزارز", asset_class=AssetClass.CRYPTO,
                current_balance=Decimal("40000000"), institution_name="Demo Exchange",
            ),
            AssetClass.STOCK: FinancialAccount.objects.create(
                user=user, name="حساب کارگزاری", asset_class=AssetClass.STOCK,
                current_balance=Decimal("120000000"), institution_name="Demo Brokerage",
            ),
        }
        FinancialAccount.objects.create(
            user=user, name="بانک آزمایشی الف", asset_class=AssetClass.BANK,
            current_balance=Decimal("120000000"), institution_name="Bank A",
        )
        FinancialAccount.objects.create(
            user=user, name="بانک آزمایشی ب", asset_class=AssetClass.BANK,
            current_balance=Decimal("80000000"), institution_name="Bank B",
        )
        FinancialAccount.objects.create(
            user=user, name="بانک آزمایشی ج", asset_class=AssetClass.BANK,
            current_balance=Decimal("50000000"), institution_name="Bank C",
        )

        Liability.objects.create(
            user=user, liability_type=LiabilityType.LOAN, label="وام خودرو",
            outstanding_balance=Decimal("80000000"),
        )

        for months_ago in range(3):
            Income.objects.create(
                user=user, source="حقوق",
                amount=Decimal("45000000"),
                received_at=now - timedelta(days=30 * months_ago + 3),
            )

        # Realistic per-category monthly budgets (Toman) so totals land
        # close to the ~28M/month figure used elsewhere in the product spec.
        CATEGORY_MONTHLY_BUDGET = {
            TransactionCategory.HOUSING: Decimal("9000000"),
            TransactionCategory.FOOD: Decimal("6000000"),
            TransactionCategory.SHOPPING: Decimal("4000000"),
            TransactionCategory.TRANSPORTATION: Decimal("2500000"),
            TransactionCategory.ENTERTAINMENT: Decimal("1500000"),
            TransactionCategory.TRAVEL: Decimal("1200000"),
            TransactionCategory.HEALTHCARE: Decimal("1000000"),
            TransactionCategory.EDUCATION: Decimal("800000"),
            TransactionCategory.BILLS: Decimal("1500000"),
            TransactionCategory.OTHER: Decimal("500000"),
        }

        cash_account = accounts[AssetClass.CASH]
        for months_ago in range(2):
            window_start = now - timedelta(days=30 * (months_ago + 1))
            # Vary month-over-month slightly so the MoM comparison isn't flat.
            month_factor = Decimal("1.0") if months_ago == 0 else Decimal("0.87")
            for category, monthly_budget in CATEGORY_MONTHLY_BUDGET.items():
                merchant = random.choice(CATEGORY_MERCHANTS[category])
                num_transactions = random.randint(2, 4)
                remaining = monthly_budget * month_factor
                for i in range(num_transactions):
                    share = remaining / Decimal(num_transactions - i)
                    amount = (share * Decimal(str(random.uniform(0.7, 1.3)))).quantize(Decimal("1"))
                    amount = max(amount, Decimal("50000"))
                    remaining -= amount
                    occurred_at = window_start + timedelta(
                        days=random.randint(0, 29), hours=random.randint(0, 23)
                    )
                    Transaction.objects.create(
                        user=user, account=cash_account, transaction_type=TransactionType.EXPENSE,
                        category=category, amount=amount, merchant=merchant,
                        description=merchant, occurred_at=occurred_at,
                    )

        Goal.objects.create(
            user=user, title="خرید خودرو", target_amount=Decimal("500000000"),
            current_allocation=Decimal("300000000"), deadline=(now + timedelta(days=60)).date(),
        )

        RiskProfile.objects.create(
            user=user, emergency_reserve_months=3, max_crypto_allocation_pct=Decimal("10"),
            max_single_asset_concentration_pct=Decimal("25"),
        )

        self.stdout.write(self.style.SUCCESS(f"Demo data ready. Log in as {DEMO_EMAIL} / {DEMO_PASSWORD}"))
