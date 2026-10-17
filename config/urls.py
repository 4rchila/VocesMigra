"""URLs raíz de Voces Migra."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Ruta configurable con DJANGO_ADMIN_URL; /admin/ no existe (1.3).
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
    path("publicaciones/", include("apps.posts.urls")),
    path("cuenta/", include("apps.accounts.urls")),
]
