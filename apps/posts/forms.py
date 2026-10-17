"""Formularios de publicación con validación de servidor."""

from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    """Formulario de creación y edición de publicaciones.

    La autoría no se expone en el formulario: la asigna la vista. Los campos
    conservan los límites y catálogos definidos en el modelo.
    """

    class Meta:
        model = Post
        fields = ("category", "title", "content", "status")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 12}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            if name in self.errors:
                field.widget.attrs["aria-invalid"] = "true"
                field.widget.attrs["aria-describedby"] = f"id_{name}_error"
