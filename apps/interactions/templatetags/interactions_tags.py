"""Etiqueta que inserta comentarios y votos en el detalle de una publicación.

Se usa desde la plantilla de ``posts`` para no crear una dependencia de
importación de ``posts`` hacia ``interactions``.
"""

from django import template
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.interactions.forms import CommentForm
from apps.interactions.models import Comment, CommentVote, Vote
from apps.interactions.services import user_votes

register = template.Library()

COMMENTS_LIMIT = 100


@register.inclusion_tag("interactions/_section.html", takes_context=True)
def interactions_section(context, post):
    request = context["request"]
    user = request.user
    comments = list(
        Comment.objects.filter(post=post)
        .select_related("author")
        .by_relevance()[:COMMENTS_LIMIT]
    )
    comment_votes = user_votes(CommentVote, "comment", user, [c.pk for c in comments])
    for comment in comments:
        comment.my_vote = comment_votes.get(comment.pk)
    post_score = Vote.objects.filter(post=post).aggregate(
        total=Coalesce(Sum("value"), 0)
    )["total"]
    return {
        "request": request,
        "user": user,
        "post": post,
        "comments": comments,
        "post_score": post_score,
        "post_vote": user_votes(Vote, "post", user, [post.pk]).get(post.pk),
        "comment_form": context.get("comment_form") or CommentForm(),
    }
