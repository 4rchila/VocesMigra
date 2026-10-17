"""Modelos de publicaciones y categorías estables.

Una publicación pertenece a una persona autora y a una única categoría del
catálogo cerrado. El identificador público es un UUID distinto de la clave
primaria para no exponer el conteo interno. No se implementan imágenes,
comentarios, votos, guardados, seguidores, búsqueda ni moderación.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

TITLE_MIN_LENGTH = 10
TITLE_MAX_LENGTH = 160
CONTENT_MIN_LENGTH = 20
CONTENT_MAX_LENGTH = 10000
CATEGORY_MAX_LENGTH = 20
STATUS_MAX_LENGTH = 10


class Category(models.TextChoices):
    """Catálogo cerrado y estable de categorías de publicación."""

    EXPERIENCES = "experiences", _("Vivencias")
    PROBLEMS = "problems", _("Problemas")
    HELP = "help", _("Ayudas")
    OPINIONS = "opinions", _("Opiniones")
    COMMUNITY = "community", _("Comunidad")


class Status(models.TextChoices):
    """Estado editorial de una publicación."""

    DRAFT = "draft", _("Borrador")
    PUBLISHED = "published", _("Publicada")


class PostQuerySet(models.QuerySet):
    """Consultas reutilizables del feed y del acceso público."""

    def published(self):
        """Publicaciones visibles en el feed público."""
        return self.filter(status=Status.PUBLISHED)

    def visible_to(self, user):
        """Publicaciones publicadas, más los borradores de la propia persona."""
        if user is None or not user.is_authenticated:
            return self.published()
        return self.filter(
            models.Q(status=Status.PUBLISHED) | models.Q(author=user)
        )


class Post(models.Model):
    """Publicación con título, cuerpo, categoría y estado editorial."""

    public_id = models.UUIDField(
        _("identificador público"),
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("autor"),
    )
    category = models.CharField(
        _("categoría"),
        max_length=CATEGORY_MAX_LENGTH,
        choices=Category.choices,
    )
    title = models.CharField(
        _("título"),
        max_length=TITLE_MAX_LENGTH,
        validators=[MinLengthValidator(TITLE_MIN_LENGTH)],
    )
    content = models.TextField(
        _("contenido"),
        max_length=CONTENT_MAX_LENGTH,
        validators=[
            MinLengthValidator(CONTENT_MIN_LENGTH),
            MaxLengthValidator(CONTENT_MAX_LENGTH),
        ],
    )
    status = models.CharField(
        _("estado"),
        max_length=STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(_("fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(
        _("fecha de actualización"), auto_now=True
    )

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("publicación")
        verbose_name_plural = _("publicaciones")
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="posts_status_created_idx",
            ),
            models.Index(
                fields=["category", "-created_at"],
                name="posts_category_created_idx",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("posts:detail", args=[self.public_id])
