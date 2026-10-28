"""Configuración del admin propio (1.3)."""

from django.contrib.admin.apps import AdminConfig


class VocesAdminConfig(AdminConfig):
    """Sustituye ``django.contrib.admin`` para que ``admin.site`` sea el nuestro."""

    default_site = "config.admin_site.VocesAdminSite"
