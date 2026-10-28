"""Token de activación de cuenta (tarea 1.2).

Incluye ``is_active`` en el hash: al activar la cuenta el enlace deja de
servir, así que cada enlace es de un solo uso. Caduca según
``PASSWORD_RESET_TIMEOUT`` (3 días por defecto).
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ActivationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "apps.accounts.tokens.ActivationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_active}{user.password}{timestamp}{user.email}"


activation_token = ActivationTokenGenerator()
