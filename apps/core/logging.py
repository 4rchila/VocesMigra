"""Filtro de logs que oculta correos y recorta IP (1.7).

Los correos se sustituyen por ``[correo]``. Las IPv4 se recortan a /24
(``203.0.113.0``) y las IPv6 a /48, que sirve para ver patrones de abuso sin
guardar la dirección exacta de una persona.
"""

import ipaddress
import logging
import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b")


def _truncate_ip(match):
    text = match.group(0)
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return text
    prefix = 24 if ip.version == 4 else 48
    return str(ipaddress.ip_network(f"{ip}/{prefix}", strict=False).network_address)


def redact(text):
    text = EMAIL_RE.sub("[correo]", text)
    text = IPV4_RE.sub(_truncate_ip, text)
    return IPV6_RE.sub(_truncate_ip, text)


class RedactPersonalDataFilter(logging.Filter):
    def filter(self, record):
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - un log mal formado no debe romper nada
            return True
        record.msg = redact(message)
        record.args = ()
        return True
