from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.finance import engine
from apps.finance.models import AssetClass, FinancialAccount, Goal, RiskProfile

from .models import DailyQuote


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    return render(request, "landing/index.html")


@login_required
def dashboard_view(request):
    user = request.user
    now = timezone.now()

    summary = engine.build_financial_summary(user, as_of=now)
    quote = DailyQuote.get_quote_for_date(now.date())
    risk_profile = RiskProfile.objects.filter(user=user).first()
    bank_accounts = FinancialAccount.objects.filter(
        user=user, asset_class=AssetClass.BANK, is_active=True
    ).order_by("name")
    goals = Goal.objects.filter(user=user, is_achieved=False).order_by("deadline", "-target_amount")[:3]

    context = {
        "summary": summary,
        "quote": quote,
        "now": now,
        "risk_profile": risk_profile,
        "investable_capital": engine.calculate_investable_capital(user, as_of=now),
        "bank_accounts": bank_accounts,
        "goals": goals,
    }
    return render(request, "dashboard/index.html", context)


def coming_soon_view(request, section="This section"):
    return render(request, "core/coming_soon.html", {"section": section})


def _info_page(request, page, title, intro, cards):
    return render(request, "core/info_page.html", {
        "page": page, "title": title, "intro": intro, "cards": cards,
    })


def about_view(request):
    return _info_page(request, "about", "درباره فین‌ای",
        "فین‌ای در حال ساخت یک لایه هوشمندی مالی شفاف و قابل‌اعتماد برای تصمیم‌های روزمره شماست.", [
            ("تصمیم‌گیری روشن", "اطلاعات مالی پراکنده را در یک تصویر ساده و قابل‌فهم کنار هم می‌آوریم."),
            ("دقت در اعداد", "محاسبات مالی از داده و منطق قطعی می‌آیند، نه از حدس یا وعده‌های غیرواقعی."),
            ("ساخت مسئولانه", "امنیت، حریم خصوصی و کنترل کاربر از ابتدا در معماری محصول در نظر گرفته شده‌اند."),
        ])


def services_view(request):
    return _info_page(request, "services", "خدمات فین‌ای",
        "ابزارهایی برای اینکه پولتان را بهتر بفهمید و با آرامش بیشتری برای آینده تصمیم بگیرید.", [
            ("مدیریت مالی شخصی", "نمایش یکپارچه پول نقد، حساب‌ها، دارایی‌ها و بدهی‌ها."),
            ("تحلیل درآمد و هزینه", "دسته‌بندی هزینه‌ها، روند مخارج و مقایسه ماه‌به‌ماه."),
            ("هدف‌گذاری مالی", "تعریف هدف، مبلغ، مهلت و فاصله مالی موردنیاز."),
            ("مدیریت سرمایه‌گذاری", "نمایی از طلا، نقره، رمزارز و سهام با مرزبندی ریسک."),
            ("دستیار مالی هوشمند", "قابلیت آینده برای پاسخ‌گویی مبتنی بر داده‌های واقعی شما."),
            ("تحلیل رفتار مالی", "شناخت الگوهای مالی و ارائه بینش‌های کاربردی و قابل‌توضیح."),
        ])


def support_view(request):
    return _info_page(request, "support", "پشتیبانی",
        "پاسخ‌گویی شفاف و امن، بخشی از تجربه فین‌ای است.", [
            ("راهنمای شروع", "حساب بسازید، اطلاعات آزمایشی را ببینید و تصویر مالی خود را بررسی کنید."),
            ("امنیت حساب", "رمز عبور، نشست‌ها و دسترسی به اطلاعات مالی با اصول امنیتی مدیریت می‌شوند."),
            ("نیاز به کمک دارید؟", "این بخش به‌زودی با راهنمای کامل و مسیر ارتباطی اختصاصی فعال می‌شود."),
        ])


def contact_view(request):
    return _info_page(request, "contact", "تماس با ما",
        "برای پیشنهاد، بازخورد یا پرسش درباره مسیر محصول با ما در ارتباط باشید.", [
            ("بازخورد محصول", "نظر شما به اولویت‌بندی قابلیت‌های آینده فین‌ای کمک می‌کند."),
            ("همکاری", "اتصال به بانک‌ها، کارگزاری‌ها و ارائه‌دهندگان رسمی فقط از مسیرهای مجاز انجام خواهد شد."),
            ("وضعیت فعلی", "این قابلیت در نسخه پایه به‌صورت «به‌زودی» ارائه می‌شود."),
        ])
