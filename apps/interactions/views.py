"""Vistas de comentarios y votos. Solo POST con CSRF y sesión para escribir."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.posts.models import Post, Status

from .forms import CommentForm, VoteForm
from .models import Comment, CommentVote, Vote
from .services import cast_vote

COMMENTS_ANCHOR = "#comentarios"


def _post_url(post, anchor=COMMENTS_ANCHOR):
    return f"{post.get_absolute_url()}{anchor}"


def _published_post(public_id):
    """Solo se interactúa con publicaciones publicadas."""
    return get_object_or_404(
        Post.objects.published().select_related("author"), public_id=public_id
    )


def _published_own_comment(pk, user):
    """Comentario propio sobre una publicación publicada."""
    return get_object_or_404(
        Comment.objects.select_related("post", "post__author").filter(
            post__status=Status.PUBLISHED
        ),
        pk=pk,
        author=user,
    )


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
    # Mismo contexto que post_detail + formulario con errores (vía interactions_section).
    return render(
        request,
        "posts/post_detail.html",
        {"post": post, "comment_form": form},
        status=400,
    )


@login_required
@require_http_methods(["GET", "POST"])
def comment_update(request, pk):
    comment = _published_own_comment(pk, request.user)
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
    comment = _published_own_comment(pk, request.user)
    if request.method == "POST":
        post = comment.post
        comment.delete()
        messages.success(request, _("Comentario eliminado."))
        return HttpResponseRedirect(_post_url(post))
    return render(
        request, "interactions/comment_confirm_delete.html", {"comment": comment}
    )


@login_required
@require_POST
def post_vote(request, public_id):
    post = _published_post(public_id)
    if post.author_id == request.user.id:
        messages.error(request, _("No puedes valorar tu propia publicación."))
        return redirect(_post_url(post, "#votos"))
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
        Comment.objects.select_related("post", "author").filter(
            post__status=Status.PUBLISHED
        ),
        pk=pk,
    )
    if comment.author_id == request.user.id:
        messages.error(request, _("No puedes valorar tu propio comentario."))
        return redirect(_post_url(comment.post, f"#comentario-{comment.pk}"))
    form = VoteForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Voto no válido."))
        return redirect(_post_url(comment.post, f"#comentario-{comment.pk}"))
    cast_vote(CommentVote, "comment", comment, request.user, form.cleaned_data["value"])
    return redirect(_post_url(comment.post, f"#comentario-{comment.pk}"))
