"""Django settings for StormRoute project.

Configured strictly from environment variables per ARCHITECTURE.md and CODING_RULES.md.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env if present
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

raw_secret_key = os.getenv("DJANGO_SECRET_KEY")
if not DEBUG:
    if not raw_secret_key or raw_secret_key.startswith("django-insecure"):
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set to a secure, non-default value when DEBUG is False."
        )
    SECRET_KEY = raw_secret_key
else:
    SECRET_KEY = raw_secret_key or "django-insecure-dev-only-placeholder-key-for-stormroute"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# Minimal INSTALLED_APPS (no django.contrib.admin, sessions, or messages)
INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

# Database: minimal SQLite configuration required by Django runtime
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Cache: LocMemCache backend
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "stormroute-cache",
    }
}
ROUTE_CACHE_TTL_SECONDS = int(os.getenv("ROUTE_CACHE_TTL_SECONDS", "1800"))
WEATHER_CACHE_TTL_SECONDS = int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "1800"))
GEOCODE_CACHE_TTL_SECONDS = int(os.getenv("GEOCODE_CACHE_TTL_SECONDS", "86400"))
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "8.0"))
ROUTING_PROVIDER = os.getenv("ROUTING_PROVIDER", "tomtom")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")

num_proxies_val = os.getenv("NUM_PROXIES")
NUM_PROXIES = int(num_proxies_val) if num_proxies_val is not None else None

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Django REST Framework configuration
REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "analyze": os.getenv("THROTTLE_ANALYZE", "20/min"),
        "heatmap": os.getenv("THROTTLE_HEATMAP", "30/min"),
        "geocode": os.getenv("THROTTLE_GEOCODE", "120/min"),
    },
    "NUM_PROXIES": NUM_PROXIES,
    "EXCEPTION_HANDLER": "api.errors.custom_exception_handler",
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

# Logging configuration: httpx and httpcore at WARNING
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "httpx": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "httpcore": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
