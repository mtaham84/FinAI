from django.contrib import admin

from .models import DailyQuote


@admin.register(DailyQuote)
class DailyQuoteAdmin(admin.ModelAdmin):
    list_display = ["text", "author", "is_active"]
    list_filter = ["is_active"]
