"""Vistas de comentarios y votos. Solo POST con CSRF y sesión para escribir."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.posts.models import Post

from .forms import CommentForm, VoteForm
from .models import Comment, CommentVote, Vote
from .services import cast_vote

COMMENTS_ANCHOR = "#comentarios"


def _post_url(post, anchor=COMMENTS_ANCHOR):
    return f"{post.get_absolute_url()}{anchor}"


def _published_post(public_id):
    """Solo se interactúa con publicaciones publicadas."""
    return get_object_or_404(Post.objects.published(), public_id=public_id)


@login_required
@require_POST
def comment_create(request, public_id):
    post = _published_post(public_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        messages.success(request, _("Comentario publicado."))
        return HttpResponseRedirect(_post_url(post))
    # Reutiliza el detalle para mostrar los errores junto al campo.
    return render(
        request,
        "posts/post_detail.html",
        {"post": post, "comment_form": form},
        status=400,
    )


@login_required
@require_http_methods(["GET", "POST"])
def comment_update(request, pk):
    comment = get_object_or_404(
        Comment.objects.select_related("post"), pk=pk, author=request.user
    )
    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, _("Comentario actualizado."))
            return HttpResponseRedirect(_post_url(comment.post))
    else:
        form = CommentForm(instance=comment)
    return render(
        request, "interactions/comment_form.html", {"form": form, "comment": comment}
    )


@login_required
@require_http_methods(["GET", "POST"])
def comment_delete(request, pk):
    comment = get_object_or_404(
        Comment.objects.select_related("post"), pk=pk, author=request.user
    )
    if request.method == "POST":
        post = comment.post
        comment.delete()
        messages.success(request, _("Comentario eliminado."))
        return HttpResponseRedirect(_post_url(post))
    return render(request, "interactions/comment_confirm_delete.html", {"comment": comment})


@login_required
@require_POST
def post_vote(request, public_id):
    post = _published_post(public_id)
    form = VoteForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Voto no válido."))
        return redirect(_post_url(post, "#votos"))
    cast_vote(Vote, "post", post, request.user, form.cleaned_data["value"])
    return redirect(_post_url(post, "#votos"))


@login_required
@require_POST
def comment_vote(request, pk):
    comment = get_object_or_404(
        Comment.objects.select_related("post").filter(post__status="published"), pk=pk
    )
    form = VoteForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Voto no válido."))
        return redirect(_post_url(comment.post, f"#comentario-{comment.pk}"))
    cast_vote(CommentVote, "comment", comment, request.user, form.cleaned_data["value"])
    return redirect(_post_url(comment.post, f"#comentario-{comment.pk}"))
