"""
Django settings for the FinAI project.

Security-sensitive values are read from environment variables --
see .env.example. Nothing secret is hardcoded or committed.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key, default=None, required=False):
    value = os.environ.get(key, default)
    if required and value is None:
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return value


def env_bool(key, default=False):
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def env_list(key, default=""):
    value = os.environ.get(key, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# --------------------------------------------------------------------
# Core / secrets
# --------------------------------------------------------------------

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="dev-only-insecure-key-change-me-before-any-real-deployment",
)

DEBUG = env_bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1")

# --------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ratelimit",
    # FinAI domain apps
    "apps.accounts",
    "apps.core",
    "apps.finance",
    "apps.expenses",
    "apps.goals",
    "apps.investments",
    "apps.personality",
    "apps.reports",
    "apps.ai",
    "apps.integrations",
    "apps.risk",
    "apps.quant",
]

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.brand_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------
# Database -- PostgreSQL is the only supported application database.
# --------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="finai"),
        "USER": env("POSTGRES_USER", default="finai"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="finai-dev-password"),
        "HOST": env("POSTGRES_HOST", default="127.0.0.1"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

# --------------------------------------------------------------------
# Password hashing & validation
# --------------------------------------------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------
# Internationalization -- English default, Persian/RTL architected in
# --------------------------------------------------------------------

LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("fa", "Persian"),
]

# --------------------------------------------------------------------
# Static / media
# --------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------
# Security -- FinTech product, treated as first-class throughout
# --------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

CSRF_COOKIE_HTTPONLY = False  # must be readable by JS if using fetch() with CSRF header
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = "same-origin"

# HTTPS-ready configuration -- only enforced when not in local DEBUG,
# since local dev typically runs over plain HTTP.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CORS is intentionally not opened here. When the API layer needs
# cross-origin access (e.g. a future mobile app), add
# django-cors-headers with an explicit, narrow ALLOWED_ORIGINS list --
# never "*".

# --------------------------------------------------------------------
# Rate limiting (django-ratelimit) -- backed by the cache framework
# --------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "apps.core.views.coming_soon_view"  # placeholder; see urls for a dedicated 429 view later

# LocMemCache is per-process, which is fine for single-process local dev
# and tests. In production, point CACHES/default at a shared backend
# (e.g. Redis) so rate limits are enforced across all app workers.
SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003"]

# --------------------------------------------------------------------
# Logging -- never expose stack traces to users; DEBUG=False shows
# Django's generic 500 page, and server-side logs capture detail.
# --------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
