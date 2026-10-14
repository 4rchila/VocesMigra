"""Vistas de publicaciones: feed público, detalle y gestión del autor.

Las vistas coordinan; las reglas de consulta viven en el QuerySet del modelo.
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import PostForm
from .models import Category, Post

POSTS_PER_PAGE = 15
CATEGORY_PARAM = "categoria"
WRITE_METHODS = ["GET", "POST"]


def _selected_category(request):
    """Devuelve la categoría solicitada solo si pertenece al catálogo."""
    requested = request.GET.get(CATEGORY_PARAM, "").strip()
    return requested if requested in Category.values else ""


@require_GET
def post_list(request):
    """Feed público de publicaciones publicadas, con filtro y paginación."""
    selected_category = _selected_category(request)

    posts = Post.objects.published().select_related("author")
    if selected_category:
        posts = posts.filter(category=selected_category)

    page_obj = Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get("page"))

    context = {
        "posts": list(page_obj.object_list),
        "page_obj": page_obj,
        "categories": Category.choices,
        "selected_category": selected_category,
    }
    return render(request, "posts/post_list.html", context)


@require_GET
def post_detail(request, public_id):
    """Detalle público; la autoría puede consultar además sus borradores."""
    post = get_object_or_404(
        Post.objects.visible_to(request.user).select_related("author"),
        public_id=public_id,
    )
    return render(request, "posts/post_detail.html", {"post": post})


@login_required
@require_http_methods(WRITE_METHODS)
def post_create(request):
    """Crea una publicación autenticada y asigna la autoría de la sesión."""
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, "posts/post_form.html", {"form": form})


@login_required
@require_http_methods(WRITE_METHODS)
def post_update(request, public_id):
    """Edita una publicación existente solo si pertenece a quien la solicita."""
    post = get_object_or_404(Post, public_id=public_id, author=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)
    return render(request, "posts/post_form.html", {"form": form, "post": post})


@login_required
@require_http_methods(WRITE_METHODS)
def post_delete(request, public_id):
    """Confirma y elimina una publicación solo para su autoría."""
    post = get_object_or_404(Post, public_id=public_id, author=request.user)
    if request.method == "POST":
        post.delete()
        return redirect("posts:list")
    return render(request, "posts/post_confirm_delete.html", {"post": post})
