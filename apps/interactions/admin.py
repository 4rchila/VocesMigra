"""Administración básica de interacciones."""

from django.contrib import admin

from .models import Comment, CommentVote, Vote


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_content", "author", "post", "created_at")
    list_select_related = ("author", "post")
    search_fields = ("content", "author__alias")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("post", "author")

    @admin.display(description="comentario")
    def short_content(self, obj):
        return obj.content[:60]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "value", "created_at")
    list_select_related = ("post", "user")
    raw_id_fields = ("post", "user")


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ("comment", "user", "value", "created_at")
    list_select_related = ("comment", "user")
    raw_id_fields = ("comment", "user")
