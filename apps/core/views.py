"""Vistas comunes: portada y salud del servicio."""

import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.posts.models import Category, Post


logger = logging.getLogger(__name__)

HOME_POSTS_LIMIT = 3


@require_GET
def home(request):
    """Portada pública con una muestra reciente del feed publicado."""
    posts = (
        Post.objects.published()
        .select_related("author")
        .order_by("-created_at", "-id")[:HOME_POSTS_LIMIT]
    )
    return render(
        request,
        "core/home.html",
        {
            "posts": posts,
            "categories": Category.choices,
            "selected_category": "",
        },
    )


@never_cache
@require_GET
def health(request):
    """Salud del servicio (1.4): 200 si la base de datos responde, 503 si no.

    No devuelve detalles del error para no filtrar datos de infraestructura;
    el detalle queda solo en el log del servidor.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.error("health: la base de datos no responde", exc_info=True)
        return JsonResponse({"status": "error", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})
