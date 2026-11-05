"""Comentarios planos y votos de publicaciones y comentarios.

Los comentarios no tienen padre (sin hilos). Un voto vale +1 o -1; la base de
datos impide más de un voto por persona y elemento (UniqueConstraint) y
rechaza cualquier otro valor (CheckConstraint). El puntaje de relevancia es la
suma de votos; el desempate por fecha descendente lo aplican los QuerySets.
"""

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

COMMENT_MAX_LENGTH = 1000
VOTE_UP = 1
VOTE_DOWN = -1


class VoteValue(models.IntegerChoices):
    """Valores permitidos de un voto."""

    UP = VOTE_UP, _("Útil")
    DOWN = VOTE_DOWN, _("No útil")


class CommentQuerySet(models.QuerySet):
    def with_score(self):
        """Anota ``score``: suma de votos (0 si no hay)."""
        return self.annotate(score=Coalesce(Sum("votes__value"), 0))

    def by_relevance(self):
        """Orden determinista: puntaje desc, fecha desc, id desc."""
        return self.with_score().order_by("-score", "-created_at", "-id")


class Comment(models.Model):
    """Comentario plano en una publicación (sin padre ni respuestas)."""

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("publicación"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("autor"),
    )
    content = models.TextField(
        _("comentario"),
        max_length=COMMENT_MAX_LENGTH,
        validators=[MaxLengthValidator(COMMENT_MAX_LENGTH)],
    )
    created_at = models.DateTimeField(_("fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("fecha de actualización"), auto_now=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("comentario")
        verbose_name_plural = _("comentarios")
        indexes = [
            models.Index(
                fields=["post", "-created_at"],
                name="comments_post_created_idx",
            ),
        ]

    def __str__(self):
        return self.content[:60]


class Vote(models.Model):
    """Voto de una persona sobre una publicación: +1 o -1, uno por persona."""

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name=_("publicación"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_votes",
        verbose_name=_("persona"),
    )
    value = models.SmallIntegerField(_("valor"), choices=VoteValue.choices)
    created_at = models.DateTimeField(_("fecha de creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("voto de publicación")
        verbose_name_plural = _("votos de publicaciones")
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"], name="vote_unique_user_post"
            ),
            models.CheckConstraint(
                condition=models.Q(value__in=[VOTE_UP, VOTE_DOWN]),
                name="vote_value_plus_minus_one",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.post_id}: {self.value:+d}"


class CommentVote(models.Model):
    """Voto de una persona sobre un comentario: +1 o -1, uno por persona."""

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name=_("comentario"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_votes",
        verbose_name=_("persona"),
    )
    value = models.SmallIntegerField(_("valor"), choices=VoteValue.choices)
    created_at = models.DateTimeField(_("fecha de creación"), auto_now_add=True)

    class Meta:
        verbose_name = _("voto de comentario")
        verbose_name_plural = _("votos de comentarios")
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"], name="commentvote_unique_user_comment"
            ),
            models.CheckConstraint(
                condition=models.Q(value__in=[VOTE_UP, VOTE_DOWN]),
                name="commentvote_value_plus_minus_one",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} → comentario {self.comment_id}: {self.value:+d}"
