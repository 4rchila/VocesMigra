"""URLs de cuenta."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.register, name="register"),
    path("entrar/", views.login_view, name="login"),
    path("salir/", views.logout_view, name="logout"),
    path("perfil/", views.profile, name="profile"),
]
