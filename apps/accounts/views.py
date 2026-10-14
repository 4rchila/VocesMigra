"""Vistas de cuenta: registro, acceso, cierre de sesión y página propia.

El cierre de sesión solo acepta POST con CSRF. La página de cuenta solo la ve
su propietaria; el correo nunca se expone fuera de ella.
"""

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import LoginForm, RegistrationForm

FORM_METHODS = ["GET", "POST"]


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


@sensitive_post_parameters("password1", "password2")
@csrf_protect
@never_cache
@require_http_methods(FORM_METHODS)
def register(request):
    """Crea una cuenta con correo y contraseña e inicia la sesión."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


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
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(next_url or settings.LOGIN_REDIRECT_URL)
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
