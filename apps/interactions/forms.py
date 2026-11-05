"""Formularios de interacciones con validación de servidor."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import COMMENT_MAX_LENGTH, Comment, VoteValue


class CommentForm(forms.ModelForm):
    """Texto del comentario; el texto se guarda tal cual y se escapa al mostrar."""

    class Meta:
        model = Comment
        fields = ("content",)
        labels = {"content": _("Tu comentario")}
        help_texts = {
            "content": _("Hasta %(max)d caracteres. Evita compartir datos personales.")
            % {"max": COMMENT_MAX_LENGTH}
        }
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 4, "maxlength": COMMENT_MAX_LENGTH, "class": "form-control"}
            ),
        }


class VoteForm(forms.Form):
    """Valida que el voto sea exactamente +1 o -1."""

    value = forms.TypedChoiceField(
        choices=VoteValue.choices,
        coerce=int,
    )
