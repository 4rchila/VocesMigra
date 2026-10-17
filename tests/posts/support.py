"""Utilidades compartidas por las pruebas de publicaciones."""

from unittest import mock

from django.http import HttpResponse

from apps.accounts.models import User
from apps.posts.models import Category, Post, Status

PASSWORD = "clave-sintetica-123"
CONTENT = "Contenido de prueba con longitud suficiente."


def create_user(email="autora@example.com", alias="Autora"):
    return User.objects.create_user(email, alias, PASSWORD)


def create_post(author=None, **overrides):
    data = {
        "author": author or create_user(),
        "category": Category.EXPERIENCES,
        "title": "Publicación de prueba válida",
        "content": CONTENT,
        "status": Status.PUBLISHED,
    }
    data.update(overrides)
    return Post.objects.create(**data)


def rendered(client, url, method="get", data=None):
    """Ejecuta una vista capturando la plantilla y el contexto solicitados.

    Las plantillas de publicaciones las aporta el worker de interfaz, así que
    estas pruebas verifican el contrato de nombres y contextos sin cargar
    archivos de plantilla.
    """
    with mock.patch("apps.posts.views.render", autospec=True) as render_mock:
        render_mock.return_value = HttpResponse("ok")
        response = getattr(client, method)(url, data or {})
    return response, render_mock


def template_of(render_mock):
    return render_mock.call_args.args[1]


def context_of(render_mock):
    return render_mock.call_args.args[2]
