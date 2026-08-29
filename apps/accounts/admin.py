from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "phone_number", "full_name", "is_active", "date_joined"]
    search_fields = ["email", "phone_number", "full_name"]
    readonly_fields = ["id", "date_joined", "last_login_ip"]

    fieldsets = (
        (None, {"fields": ("email", "phone_number", "password")}),
        ("Personal info", {"fields": ("full_name",)}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Verification", {"fields": ("email_verified", "phone_verified")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "last_login_ip")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "phone_number", "password1", "password2")}),
    )
