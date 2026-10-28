"""URLs de cuenta."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.register, name="register"),
    path("registro/enviado/", views.register_done, name="register_done"),
    path("activar/<uidb64>/<token>/", views.activate, name="activate"),
    path("entrar/", views.login_view, name="login"),
    path("salir/", views.logout_view, name="logout"),
    path("perfil/", views.profile, name="profile"),
    path("perfil/alias/", views.change_alias, name="change_alias"),
]
