"""URLs raíz de Voces Migra."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django_otp.admin import OTPAdminSite

# Falla al arrancar si alguien reemplaza el sitio y el admin queda sin 2FA.
assert isinstance(admin.site, OTPAdminSite), "admin.site debe exigir OTP"

urlpatterns = [
    # Ruta configurable con DJANGO_ADMIN_URL; /admin/ no existe (1.3).
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("publicaciones/", include("apps.posts.urls")),
    path("cuenta/", include("apps.accounts.urls")),
]
