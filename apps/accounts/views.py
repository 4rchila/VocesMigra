"""Vistas de cuenta: registro, activación, acceso, cierre y página propia.

El registro no revela si un correo ya tiene cuenta: siempre responde con la
misma pantalla y la diferencia solo llega por correo al dueño (1.2). Acceso y
registro tienen límite de intentos (1.1). El cierre de sesión solo acepta POST
con CSRF. La página de cuenta solo la ve su propietaria.
"""

import logging
import smtplib

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import NON_FIELD_ERRORS
from django.db import IntegrityError, transaction
from django.forms.utils import ErrorDict
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import ratelimit
from .emails import send_activation_email, send_existing_account_notice
from .forms import AliasChangeForm, LoginForm, RegistrationForm
from .models import User
from .tokens import activation_token

logger = logging.getLogger(__name__)

FORM_METHODS = ["GET", "POST"]
TOO_MANY_ATTEMPTS = "Demasiados intentos. Espera unos minutos e inténtalo de nuevo."
# Mismo texto y estado para los tres caminos: no delata si el correo existe.
SEND_FAILED = "No pudimos enviar el correo de confirmación. Inténtalo de nuevo más tarde."


def _with_limit_error(form):
    """Marca un formulario vacío con el aviso de límite sin validarlo.

    No se valida para no gastar un intento de autenticación ni revelar nada.
    """
    form._errors = ErrorDict(
        {NON_FIELD_ERRORS: form.error_class([_(TOO_MANY_ATTEMPTS)], error_class="nonfield")}
    )
    return form


def _safe_next_url(request):
    """Devuelve el destino ``next`` solo si pertenece a este sitio."""
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ""


def _register_new_or_notify(request, form):
    """Crea la cuenta inactiva o avisa al dueño del correo ya registrado.

    Devuelve ``False`` si el correo no se pudo enviar. En el caso nuevo, el
    usuario y el correo van en la misma transacción: si falla el envío, no
    queda una cuenta inactiva huérfana que nadie puede activar.
    """
    email = form.cleaned_data["email"]
    try:
        existing = User.objects.filter(email__iexact=email).first()
        if existing is None:
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False
                    user.save()
                    send_activation_email(request, user)
                return True
            except IntegrityError:
                # Dos registros simultáneos con el mismo correo o alias.
                existing = User.objects.filter(email__iexact=email).first()
                if existing is None:
                    raise
        # Iguala el coste de hash para que el tiempo de respuesta no delate el caso.
        make_password(form.cleaned_data["password1"])
        if existing.is_active:
            send_existing_account_notice(request, existing)
        else:
            send_activation_email(request, existing)
    except (smtplib.SMTPException, OSError):
        # Sin el correo en el registro: el dato personal no debe llegar a los logs.
        logger.exception("Fallo al enviar correo de registro")
        return False
    return True


@sensitive_post_parameters("password1", "password2")
@csrf_protect
@never_cache
@require_http_methods(FORM_METHODS)
def register(request):
    """Registro con correo y contraseña; la cuenta se activa desde el correo."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if request.method == "POST":
        ip = ratelimit.client_ip(request)
        if ratelimit.is_limited("register-ip", ip):
            form = _with_limit_error(RegistrationForm())
            return render(request, "accounts/register.html", {"form": form}, status=429)
        ratelimit.hit("register-ip", ip)
        form = RegistrationForm(request.POST)
        if form.is_valid():
            if _register_new_or_notify(request, form):
                return redirect("accounts:register_done")
            form.add_error(None, _(SEND_FAILED))
            return render(request, "accounts/register.html", {"form": form}, status=503)
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@never_cache
@require_GET
def register_done(request):
    """Pantalla única tras registrarse, exista o no el correo."""
    return render(request, "accounts/register_done.html")


def _user_from_uid(uidb64):
    try:
        return User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


@sensitive_post_parameters("new_password1", "new_password2")
@csrf_protect
@never_cache
@require_http_methods(FORM_METHODS)
def activate(request, uidb64, token):
    """GET muestra el formulario; POST fija la contraseña, activa e inicia sesión.

    La contraseña se define aquí, no en el registro: así, si alguien registra
    el correo de otra persona con una contraseña suya, esa contraseña deja de
    servir cuando la dueña real del correo activa la cuenta. Va por POST para
    que los antivirus que abren enlaces de correo no activen cuentas solos.
    """
    user = _user_from_uid(uidb64)
    valid = user is not None and not user.is_active and activation_token.check_token(
        user, token
    )
    if not valid:
        return render(request, "accounts/activate.html", {"valid": False}, status=400)
    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save(update_fields=["password", "is_active"])
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = SetPasswordForm(user)
    return render(
        request, "accounts/activate.html", {"valid": True, "form": form, "account": user}
    )


@sensitive_post_parameters("password")
@csrf_protect
@never_cache
@require_http_methods(FORM_METHODS)
def login_view(request):
    """Inicia sesión con correo y contraseña; rota la sesión al acceder."""
    next_url = _safe_next_url(request)
    if request.user.is_authenticated:
        return redirect(next_url or settings.LOGIN_REDIRECT_URL)
    if request.method == "POST":
        ip = ratelimit.client_ip(request)
        account = User.objects.normalize_email(request.POST.get("username", "")).lower()
        if (
            ratelimit.is_limited("login-ip", ip)
            or ratelimit.is_limited("login-account-ip", account, ip)
            or ratelimit.is_limited("login-account", account)
        ):
            form = _with_limit_error(LoginForm(request))
            return render(
                request,
                "accounts/login.html",
                {"form": form, "next": next_url},
                status=429,
            )
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            ratelimit.reset("login-account-ip", account, ip)
            login(request, form.get_user())
            return redirect(next_url or settings.LOGIN_REDIRECT_URL)
        ratelimit.hit("login-ip", ip)
        ratelimit.hit("login-account-ip", account, ip)
        ratelimit.hit("login-account", account)
    else:
        form = LoginForm(request)
    return render(request, "accounts/login.html", {"form": form, "next": next_url})


@csrf_protect
@require_POST
def logout_view(request):
    """Cierra la sesión solo mediante POST protegido por CSRF."""
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
@never_cache
@require_GET
def profile(request):
    """Página de cuenta visible únicamente para quien inició sesión."""
    return render(request, "accounts/profile.html", {"account": request.user})


@login_required
@csrf_protect
@never_cache
@require_http_methods(FORM_METHODS)
def change_alias(request):
    """Permite cambiar el alias público, por ejemplo si otra persona lo eligió
    al registrarse antes con tu correo (observación de SENTINEL)."""
    if request.method == "POST":
        form = AliasChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile")
    else:
        form = AliasChangeForm(instance=request.user)
    return render(request, "accounts/change_alias.html", {"form": form})
