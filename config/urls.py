"""URLs raíz de Voces Migra."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("publicaciones/", include("apps.posts.urls")),
    path("cuenta/", include("apps.accounts.urls")),
]
