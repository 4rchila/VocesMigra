"""Modelo de usuario propio y perfil público mínimo.

El correo privado y único es el identificador de acceso. El alias público es
único sin distinguir mayúsculas/minúsculas. No se implementan verificación de
correo, publicaciones, imágenes, comentarios, votos ni moderación.
"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .validators import (
    ALIAS_MAX_LENGTH,
    ALIAS_MIN_LENGTH,
    alias_validator,
    country_validator,
    validate_language_codes,
)


class UserManager(BaseUserManager):
    """Manager propio que usa el correo como identificador."""

    use_in_migrations = True

    def _create_user(self, email, alias, password, **extra_fields):
        if not email:
            raise ValueError(_("El correo es obligatorio."))
        if not alias:
            raise ValueError(_("El alias es obligatorio."))
        email = self.normalize_email(email).lower()
        user = self.model(email=email, alias=alias, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, alias, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, alias, password, **extra_fields)

    def create_superuser(self, email, alias, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("El superusuario debe tener is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("El superusuario debe tener is_superuser=True."))
        return self._create_user(email, alias, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Cuenta de acceso con correo privado y alias público único."""

    email = models.EmailField(_("correo"), unique=True)
    alias = models.CharField(
        _("alias"),
        max_length=ALIAS_MAX_LENGTH,
        validators=[MinLengthValidator(ALIAS_MIN_LENGTH), alias_validator],
    )
    is_active = models.BooleanField(_("activo"), default=True)
    is_staff = models.BooleanField(_("acceso al admin"), default=False)
    date_joined = models.DateTimeField(_("fecha de alta"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["alias"]

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        constraints = [
            models.UniqueConstraint(
                Lower("alias"), name="accounts_user_alias_ci_unique"
            ),
        ]

    def __str__(self):
        return self.alias


class Profile(models.Model):
    """Perfil público mínimo; no guarda ubicación exacta ni datos privados."""

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("usuario"),
    )
    description = models.TextField(_("descripción"), max_length=500, blank=True)
    country = models.CharField(
        _("país"), max_length=2, validators=[country_validator]
    )
    region = models.CharField(_("región"), max_length=100, blank=True)
    languages = models.JSONField(
        _("idiomas"),
        default=list,
        blank=True,
        validators=[validate_language_codes],
    )

    class Meta:
        verbose_name = _("perfil")
        verbose_name_plural = _("perfiles")

    def __str__(self):
        return self.user.alias
