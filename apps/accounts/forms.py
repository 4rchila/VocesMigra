"""Formularios de registro y acceso con correo privado y contraseña.

Las contraseñas se validan y guardan solo mediante Django Auth. Ni el acceso
ni el registro revelan si un correo tiene cuenta.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


def _style_fields(form):
    """Aplica clases y atributos accesibles comunes a todos los campos."""
    for name, field in form.fields.items():
        field.widget.attrs.setdefault("class", "form-control")
        if name in form.errors:
            field.widget.attrs["aria-invalid"] = "true"
            field.widget.attrs["aria-describedby"] = f"id_{name}_error"


class RegistrationForm(BaseUserCreationForm):
    """Registro con correo privado, alias público y contraseña confirmada."""

    class Meta:
        model = User
        fields = ("email", "alias")
        labels = {
            "email": _("Correo (privado)"),
            "alias": _("Alias público"),
        }
        help_texts = {
            "email": _("Solo se usa para acceder; nunca se muestra públicamente."),
            "alias": _(
                "Entre 3 y 30 caracteres: letras, números, punto, guion y "
                "guion bajo."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["alias"].widget.attrs["autocomplete"] = "username"
        _style_fields(self)

    def clean_email(self):
        # No se valida aquí si el correo ya existe: la vista responde igual en
        # ambos casos para no revelar qué correos están registrados (1.2).
        return User.objects.normalize_email(self.cleaned_data["email"]).lower()

    def validate_unique(self):
        # La unicidad del correo la resuelve la vista sin revelar nada; aquí se
        # excluye para que el formulario no responda "ya existe" (1.2).
        exclude = self._get_validation_exclusions()
        exclude.add("email")
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as error:
            self._update_errors(error)

    def clean_alias(self):
        alias = self.cleaned_data["alias"].strip()
        if User.objects.filter(alias__iexact=alias).exists():
            raise forms.ValidationError(
                _("Este alias ya está en uso."), code="alias_taken"
            )
        return alias


class LoginForm(AuthenticationForm):
    """Acceso con correo y contraseña; el error no distingue la causa."""

    error_messages = {
        "invalid_login": _("Correo o contraseña incorrectos."),
        "inactive": _("Correo o contraseña incorrectos."),
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = _("Correo")
        self.fields["username"].widget = forms.EmailInput(
            attrs={"autofocus": True, "autocomplete": "email"}
        )
        _style_fields(self)

    def clean_username(self):
        return User.objects.normalize_email(self.cleaned_data["username"]).lower()
