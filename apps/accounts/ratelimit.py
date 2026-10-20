"""Límite de intentos para acceso y registro (tarea 1.1).

Usa la caché de Django para contar intentos por ventana de tiempo. Las claves
se guardan como hash SHA-256: la caché nunca contiene correos ni IP en claro.
"""

import hashlib

from django.conf import settings
from django.core.cache import cache

# (límite, ventana en segundos). Se pueden ajustar con settings.RATELIMITS.
DEFAULT_RATELIMITS = {
    "login-ip": (20, 15 * 60),
    "login-account-ip": (5, 15 * 60),
    # Tope por cuenta desde cualquier IP: frena ataques repartidos entre IP.
    "login-account": (50, 60 * 60),
    "register-ip": (5, 60 * 60),
    "admin-login-ip": (5, 15 * 60),
}


def _rule(scope):
    return getattr(settings, "RATELIMITS", {}).get(scope, DEFAULT_RATELIMITS[scope])


def client_ip(request):
    """IP del cliente; detrás de N proxies de confianza usa X-Forwarded-For.

    Solo se lee X-Forwarded-For cuando ``TRUSTED_PROXY_COUNT`` es mayor que 0,
    porque esa cabecera la puede escribir cualquier cliente. Se toma la entrada
    añadida por el último proxy de confianza, no la primera de la lista.
    """
    header = getattr(settings, "CLIENT_IP_HEADER", "")
    if header:
        # Cabecera que el proveedor siempre reescribe (Vercel:
        # X-Vercel-Forwarded-For); un cliente no la puede falsificar.
        value = request.META.get(header, "").split(",")[0].strip()
        if value:
            return value
    count = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    if count:
        parts = [
            part.strip()
            for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
            if part.strip()
        ]
        if len(parts) >= count:
            return parts[-count]
    return request.META.get("REMOTE_ADDR", "")


def _key(scope, *identity):
    raw = "\x1f".join([scope, *[str(part).lower() for part in identity]])
    return "rl:" + hashlib.sha256(raw.encode()).hexdigest()


def is_limited(scope, *identity):
    limit, _window = _rule(scope)
    return cache.get(_key(scope, *identity), 0) >= limit


def hit(scope, *identity):
    """Suma un intento; la ventana empieza con el primer intento."""
    _limit, window = _rule(scope)
    key = _key(scope, *identity)
    if not cache.add(key, 1, window):
        try:
            cache.incr(key)
        except ValueError:
            cache.add(key, 1, window)


def reset(scope, *identity):
    cache.delete(_key(scope, *identity))
