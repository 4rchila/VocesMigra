"""Correos del registro sin enumeración (tarea 1.2).

Quien envía el formulario siempre ve la misma pantalla. La diferencia entre
"cuenta nueva" y "correo ya registrado" solo llega al buzón del dueño del
correo, que es el único que puede leerla.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import activation_token


def _send(template, subject, user, context):
    body = render_to_string(template, {"user": user, **context})
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])


def send_activation_email(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    path = reverse(
        "accounts:activate",
        kwargs={"uidb64": uidb64, "token": activation_token.make_token(user)},
    )
    _send(
        "accounts/email/activation.txt",
        "Activa tu cuenta en Voces Migra",
        user,
        {"activation_url": request.build_absolute_uri(path)},
    )


def send_existing_account_notice(request, user):
    _send(
        "accounts/email/existing_account.txt",
        "Intento de registro con tu correo en Voces Migra",
        user,
        {"login_url": request.build_absolute_uri(reverse("accounts:login"))},
    )
