"""Configuración de desarrollo local: SQLite y correo por consola."""

from .base import *  # noqa: F401,F403

DEBUG = env_bool("DJANGO_DEBUG", default=True)  # noqa: F405
SECRET_KEY = env("DJANGO_SECRET_KEY", default="desarrollo-inseguro-no-usar-en-produccion")  # noqa: F405
ALLOWED_HOSTS = env_list(  # noqa: F405
    "DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"]
)

DATABASES = {"default": sqlite_database(env("SQLITE_PATH"))}  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]
