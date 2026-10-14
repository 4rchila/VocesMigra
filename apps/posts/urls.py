"""URLs de publicaciones."""

from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.post_list, name="list"),
    path("nueva/", views.post_create, name="create"),
    path("<uuid:public_id>/", views.post_detail, name="detail"),
    path("<uuid:public_id>/editar/", views.post_update, name="update"),
    path("<uuid:public_id>/eliminar/", views.post_delete, name="delete"),
]
