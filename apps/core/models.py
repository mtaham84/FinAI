from django.db import models


class DailyQuote(models.Model):
    """
    A pool of financial quotes. `get_quote_for_date` deterministically
    picks one per calendar day (stable across refreshes, changes at
    midnight) without needing a cron job -- selection is a pure
    function of the date, so it works even before any quote has been
    explicitly "assigned" to today.
    """

    text = models.CharField(max_length=280)
    author = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text[:60]

    @classmethod
    def get_quote_for_date(cls, date):
        quotes = list(cls.objects.filter(is_active=True).order_by("id"))
        if not quotes:
            return None
        index = date.toordinal() % len(quotes)
        return quotes[index]
