"""Configuración común de Voces Migra.

Contiene valores compartidos sin secretos. Cada módulo de entorno importa esta
base y cambia solo lo necesario. Los valores sensibles se leen de variables de
entorno y fallan de forma temprana cuando son obligatorios.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(name, default=None, required=False):
    """Devuelve una variable de entorno normalizada, opcional u obligatoria."""
    value = os.environ.get(name, default)
    if isinstance(value, str):
        value = value.strip()
    if required and not value:
        raise ImproperlyConfigured(
            "Falta la variable de entorno obligatoria %s." % name
        )
    return value


def env_bool(name, default=False):
    """Interpreta una variable de entorno como booleano."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=()):
    """Divide una variable de entorno separada por comas en una lista limpia."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def sqlite_database(path=None):
    """Base de datos SQLite para desarrollo y pruebas locales."""
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(path) if path else BASE_DIR / "db.sqlite3",
    }


def postgres_database_from_env():
    """Base de datos PostgreSQL construida solo con variables de entorno."""
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", required=True),
        "USER": env("POSTGRES_USER", required=True),
        "PASSWORD": env("POSTGRES_PASSWORD", required=True),
        "HOST": env("POSTGRES_HOST", required=True),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "OPTIONS": {"sslmode": env("POSTGRES_SSLMODE") or "require"},
    }


SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
DEBUG = env_bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "config.apps.VocesAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "apps.core",
    "apps.accounts",
    "apps.posts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.ContentSecurityPolicyMiddleware",
    "apps.core.middleware.PermissionsPolicyMiddleware",
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
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": sqlite_database(env("SQLITE_PATH"))}

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/cuenta/entrar/"
LOGIN_REDIRECT_URL = "accounts:profile"
LOGOUT_REDIRECT_URL = "core:home"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").is_dir() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DEFAULT_FROM_EMAIL = "no-responder@voces-migra.local"

# --- Seguridad (Fase 1) ----------------------------------------------------


def admin_url(value):
    """Normaliza la ruta del admin y rechaza ``admin/`` (1.3)."""
    value = (value or "").strip().strip("/")
    if not value or value.lower() == "admin":
        raise ImproperlyConfigured(
            "DJANGO_ADMIN_URL no puede estar vacía ni ser 'admin'."
        )
    return value + "/"


# En desarrollo y pruebas hay un valor por defecto; producción lo exige.
ADMIN_URL = admin_url(env("DJANGO_ADMIN_URL", default="gestion-interna"))
OTP_TOTP_ISSUER = "Voces Migra"

# Proxies de confianza delante de la app (ver docs/operations/DESPLIEGUE-VERCEL.md). Con 0 se ignora
# X-Forwarded-For porque cualquier cliente puede escribirla.
TRUSTED_PROXY_COUNT = int(env("TRUSTED_PROXY_COUNT", default="0"))
# Cabecera de IP del cliente que el proveedor reescribe siempre ("" = ninguna).
CLIENT_IP_HEADER = env("CLIENT_IP_HEADER", default="")

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
CONTENT_SECURITY_POLICY = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
}
# La app no usa cámara, micrófono ni ubicación; se niegan para todo el sitio.
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=()"

# Logs sin correos, contraseñas ni IP completas (1.7). Django no registra
# cuerpos de petición; el filtro recorta IP y correos que aparezcan en mensajes.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"redact": {"()": "apps.core.logging.RedactPersonalDataFilter"}},
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["redact"],
            "formatter": "plain",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Las alertas por correo de Django mandarían datos de la petición.
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
