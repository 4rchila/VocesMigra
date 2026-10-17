"""Administración de publicaciones."""

from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Revisión administrativa básica sin moderación avanzada."""

    list_display = ("title", "author", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "content", "author__alias")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("author",)
    readonly_fields = ("public_id", "created_at", "updated_at")
