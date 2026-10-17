"""Configuración aislada para pruebas locales: SQLite en memoria y hash rápido."""

from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "pruebas-clave-local-sin-valor-real"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
