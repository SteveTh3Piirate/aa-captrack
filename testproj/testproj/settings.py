"""
Django settings for testproj project.
"""

SILENCED_SYSTEM_CHECKS = ["admin.E039"]

from pathlib import Path
import os
import sys

# ------------------------------------------------------------
# Base directory
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Add mock dependencies to Python path
sys.path.insert(0, str(BASE_DIR / "mockdeps"))

# ------------------------------------------------------------
# Quick-start development settings
# ------------------------------------------------------------
SECRET_KEY = "django-insecure-a6mh1o2cliuy(cju6scc2l=wlwzs4534&$jc%d*jo-*%2mh^6n"
DEBUG = True
ALLOWED_HOSTS = []

# ------------------------------------------------------------
# Application definition
# ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Mock deps
    "authentication",
    "eveuniverse.apps.EveUniverseConfig",

    # Plugin under test
    "captrack",
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

# ------------------------------------------------------------
# URLs / WSGI
# ------------------------------------------------------------
ROOT_URLCONF = "testproj.testproj.urls"
WSGI_APPLICATION = "testproj.testproj.wsgi.application"

# ------------------------------------------------------------
# Templates
# ------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ------------------------------------------------------------
# Database
# ------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ------------------------------------------------------------
# Password validation
# ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------
# Static files
# ------------------------------------------------------------
STATIC_URL = "static/"

# ------------------------------------------------------------
# Defaults
# ------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
