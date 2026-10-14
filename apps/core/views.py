"""Vistas comunes: salud local del servicio."""

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.posts.models import Category, Post


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


@require_GET
def health(request):
    """Comprobación local sin dependencias externas."""
    return JsonResponse({"status": "ok"})
