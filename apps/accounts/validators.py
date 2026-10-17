"""Validadores de identidad pública y perfil mínimo."""

import re

import pycountry

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

ALIAS_MIN_LENGTH = 3
ALIAS_MAX_LENGTH = 30
ALIAS_PATTERN = r"^[\w.-]+$"
COUNTRY_PATTERN = r"^[A-Z]{2}$"
LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2}$")

alias_validator = RegexValidator(
    re.compile(ALIAS_PATTERN),
    message=_(
        "El alias solo admite letras Unicode, números, punto, guion y guion bajo."
    ),
)

country_validator = RegexValidator(
    re.compile(COUNTRY_PATTERN),
    message=_("Usa un código ISO 3166-1 de dos letras mayúsculas."),
)


def validate_language_codes(value):
    """Exige una lista sin repeticiones de códigos ISO 639-1 en minúsculas."""
    if not isinstance(value, (list, tuple)):
        raise ValidationError(_("Los idiomas deben ser una lista de códigos."))
    seen = set()
    for code in value:
        if not isinstance(code, str) or not LANGUAGE_CODE_PATTERN.match(code):
            raise ValidationError(
                _("Cada idioma debe ser un código ISO 639-1 de dos letras.")
            )
        if code in seen:
            raise ValidationError(_("No repitas el mismo idioma."))
        seen.add(code)


def region_choices():
    """Lista cerrada de regiones: subdivisiones ISO 3166-2 de todos los países."""
    return sorted(
        ((sub.code, f"{sub.name} ({sub.country_code})") for sub in pycountry.subdivisions),
        key=lambda item: item[1],
    )


def validate_region_for_country(region, country):
    """La región debe ser un código ISO 3166-2 del país elegido (1.8)."""
    if not region:
        return
    sub = pycountry.subdivisions.get(code=region)
    if sub is None:
        raise ValidationError(
            {"region": _("Elige una región de la lista.")}, code="invalid_region"
        )
    if country and sub.country_code != country:
        raise ValidationError(
            {"region": _("La región no pertenece al país elegido.")},
            code="region_country_mismatch",
        )


def region_name(code):
    sub = pycountry.subdivisions.get(code=code) if code else None
    return sub.name if sub else ""
