"""Cabeceras de seguridad que Django 5.2 no trae de serie (1.5)."""

from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Añade ``Content-Security-Policy`` si ``CONTENT_SECURITY_POLICY`` existe.

    La política se define en settings como dict directiva -> fuentes. Las
    plantillas no usan scripts ni estilos en línea, así que no hace falta
    ``'unsafe-inline'``.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        policy = getattr(settings, "CONTENT_SECURITY_POLICY", None) or {}
        self.header = "; ".join(
            f"{directive} {' '.join(sources)}".strip()
            for directive, sources in policy.items()
        )

    def __call__(self, request):
        response = self.get_response(request)
        if self.header and "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = self.header
        return response


class PermissionsPolicyMiddleware:
    """Añade ``Permissions-Policy`` si ``PERMISSIONS_POLICY`` existe.

    La cadena se copia tal cual en la cabecera. No pisa una cabecera que la
    vista ya haya puesto.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.header = getattr(settings, "PERMISSIONS_POLICY", "")

    def __call__(self, request):
        response = self.get_response(request)
        if self.header and "Permissions-Policy" not in response:
            response["Permissions-Policy"] = self.header
        return response
