"""Validadores de identidad pública y perfil mínimo."""

import re

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

