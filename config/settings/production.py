"""Configuración de producción: exige variables de entorno y PostgreSQL."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)  # noqa: F405
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")  # noqa: F405
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Define DJANGO_ALLOWED_HOSTS con los hosts de producción."
    )

DATABASES = {"default": postgres_database_from_env()}  # noqa: F405

EMAIL_BACKEND = env(  # noqa: F405
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")  # noqa: F405
EMAIL_PORT = int(env("EMAIL_PORT", default="25"))  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_USER", default="")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD", default="")  # noqa: F405
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)  # noqa: F405
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-responder@voces-migra.local")  # noqa: F405

# La ruta del admin es obligatoria en producción y no puede ser "admin/".
ADMIN_URL = admin_url(env("DJANGO_ADMIN_URL", required=True))  # noqa: F405

# Proxies de confianza delante de la app (Render = 1) para la IP del límite.
TRUSTED_PROXY_COUNT = int(env("TRUSTED_PROXY_COUNT", default="1"))  # noqa: F405

# Caché compartida entre procesos para que el límite de intentos sea global.
# Requiere una vez: python manage.py createcachetable
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

SECURE_SSL_REDIRECT = True
# El chequeo de salud de Render puede llegar por HTTP interno.
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
# Sin includeSubDomains ni preload mientras el dominio .tech no sea definitivo:
# salir de la lista de preload de los navegadores tarda meses (SENTINEL).
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
