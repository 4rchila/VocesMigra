"""URLs de comentarios y votos."""

from django.urls import path

from . import views

app_name = "interactions"

urlpatterns = [
    path("publicaciones/<uuid:public_id>/comentar/", views.comment_create, name="comment_create"),
    path("publicaciones/<uuid:public_id>/votar/", views.post_vote, name="post_vote"),
    path("comentarios/<int:pk>/editar/", views.comment_update, name="comment_update"),
    path("comentarios/<int:pk>/eliminar/", views.comment_delete, name="comment_delete"),
    path("comentarios/<int:pk>/votar/", views.comment_vote, name="comment_vote"),
]
