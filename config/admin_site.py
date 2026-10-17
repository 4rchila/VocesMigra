"""Sitio de administración con segundo factor y límite de intentos (1.3).

Hereda de ``OTPAdminSite`` (django-otp): solo entra al admin quien está
autenticado con contraseña y con un código TOTP o de respaldo verificado.
Además limita los intentos fallidos de acceso por IP.
"""

from django.http import HttpResponse
from django_otp.admin import OTPAdminSite

from apps.accounts import ratelimit


class VocesAdminSite(OTPAdminSite):
    site_header = "Voces Migra · Administración"
    site_title = "Voces Migra"

    def login(self, request, extra_context=None):
        if request.method == "POST":
            ip = ratelimit.client_ip(request)
            if ratelimit.is_limited("admin-login-ip", ip):
                return HttpResponse(
                    "Demasiados intentos. Espera unos minutos.",
                    status=429,
                    content_type="text/plain; charset=utf-8",
                )
            response = super().login(request, extra_context)
            if response.status_code != 302:
                ratelimit.hit("admin-login-ip", ip)
            return response
        return super().login(request, extra_context)

