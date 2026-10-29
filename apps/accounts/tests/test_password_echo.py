"""Pruebas de que ningún formulario de acceso o registro devuelve la contraseña.

Al fallar un envío, la plantilla no debe repetir la contraseña escrita en el
atributo ``value`` del campo. Estas pruebas renderizan las plantillas reales y
buscan una contraseña distintiva en el HTML de la respuesta.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import User
from apps.accounts.tokens import activation_token

# Cadena poco común para que cualquier aparición en el HTML sea inequívoca.
PASSWORD_ECO = "ClaveEco-7Q2x-no-repetir"
PASSWORD_BUENA = "Clave-correcta-Zz9k"


class PasswordNotEchoedTests(TestCase):
    """La contraseña tecleada nunca vuelve al HTML tras un error."""

    def setUp(self):
        self.user = User.objects.create_user(
            "cuenta@example.com", "CuentaUno", PASSWORD_BUENA
        )

    def assertPasswordInputWithoutValue(self, response):
        # El campo sigue en la página, pero sin atributo value.
        self.assertContains(response, 'id="id_password"', status_code=200)
        self.assertNotContains(response, PASSWORD_ECO)

    def test_failed_login_does_not_echo_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "cuenta@example.com", "password": PASSWORD_ECO},
        )
        self.assertPasswordInputWithoutValue(response)

    def test_failed_login_for_unknown_email_does_not_echo_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "nadie@example.com", "password": PASSWORD_ECO},
        )
        self.assertPasswordInputWithoutValue(response)

    def test_registration_with_mismatched_passwords_does_not_echo_password(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "nueva@example.com",
                "alias": "NuevaCuenta",
                "password1": PASSWORD_ECO,
                "password2": "Otra-distinta-Yy8m",
            },
        )
        self.assertContains(response, 'id="id_password1"', status_code=200)
        self.assertNotContains(response, PASSWORD_ECO)
        self.assertFalse(User.objects.filter(email="nueva@example.com").exists())

    def test_activation_with_mismatched_passwords_does_not_echo_password(self):
        # Cuenta pendiente de activar con un enlace válido.
        self.user.is_active = False
        self.user.save()
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = activation_token.make_token(self.user)
        url = reverse("accounts:activate", kwargs={"uidb64": uidb64, "token": token})

        response = self.client.post(
            url,
            {"new_password1": PASSWORD_ECO, "new_password2": "Otra-distinta-Yy8m"},
        )
        self.assertContains(response, 'id="id_new_password1"', status_code=200)
        self.assertNotContains(response, PASSWORD_ECO)
