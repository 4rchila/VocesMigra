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
# 587 con STARTTLS por defecto (1.6). Brevo: smtp-relay.brevo.com:587.
EMAIL_PORT = int(env("EMAIL_PORT", default="587"))  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_USER", default="")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD", default="")  # noqa: F405
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)  # noqa: F405
EMAIL_TIMEOUT = 10
if not EMAIL_USE_TLS and EMAIL_BACKEND.endswith("smtp.EmailBackend"):
    raise ImproperlyConfigured("En producción el SMTP debe usar TLS (EMAIL_USE_TLS).")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-responder@voces-migra.local")  # noqa: F405

# La ruta del admin es obligatoria en producción y no puede ser "admin/".
ADMIN_URL = admin_url(env("DJANGO_ADMIN_URL", required=True))  # noqa: F405

# Orígenes que pueden enviar formularios con CSRF, p. ej. https://vocesmigra.tech
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")  # noqa: F405
if any(not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("DJANGO_CSRF_TRUSTED_ORIGINS solo admite https://.")

# Vercel (D5) termina TLS y escribe X-Forwarded-Proto. Para la IP real usa
# X-Vercel-Forwarded-For, que Vercel reescribe siempre para evitar suplantación
# (docs: vercel.com/docs/headers/request-headers). Otro host: revisar esto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CLIENT_IP_HEADER = env("CLIENT_IP_HEADER", default="HTTP_X_VERCEL_FORWARDED_FOR")  # noqa: F405
TRUSTED_PROXY_COUNT = int(env("TRUSTED_PROXY_COUNT", default="1"))  # noqa: F405

# Vercel corre collectstatic en el build porque STATIC_ROOT está definido. WhiteNoise
# sirve los estáticos desde Django; si el CDN de Vercel los atiende antes, WhiteNoise queda de respaldo (confirmar en el primer despliegue).
MIDDLEWARE = [  # noqa: F405
    *MIDDLEWARE[:1],  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Caché compartida entre procesos para que el límite de intentos sea global.
# Requiere una vez: python manage.py createcachetable
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

SECURE_SSL_REDIRECT = True
# El chequeo de salud puede llegar por HTTP interno.
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
