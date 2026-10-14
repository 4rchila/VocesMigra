"""Pruebas del flujo de cuenta: registro, acceso, cierre y página propia.

Las plantillas las aporta el worker de interfaz; estas pruebas verifican el
contrato de nombres de plantilla y contexto sin cargar archivos de plantilla.
"""

from unittest import mock

from django.conf import settings
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.forms import LoginForm, RegistrationForm
from apps.accounts.models import User

PASSWORD = "clave-sintetica-123"
NEW_PASSWORD = "Otra-clave-sintetica-456"


def create_user(email="cuenta@example.com", alias="CuentaUno"):
    return User.objects.create_user(email, alias, PASSWORD)


def rendered(client, url, method="get", data=None):
    """Ejecuta una vista capturando la plantilla y el contexto solicitados."""
    with mock.patch("apps.accounts.views.render", autospec=True) as render_mock:
        render_mock.return_value = HttpResponse("ok")
        response = getattr(client, method)(url, data or {})
    return response, render_mock


def registration_data(**overrides):
    data = {
        "email": "nueva@example.com",
        "alias": "NuevaCuenta",
        "password1": NEW_PASSWORD,
        "password2": NEW_PASSWORD,
    }
    data.update(overrides)
    return data


class UrlContractTests(TestCase):
    def test_url_names_resolve_to_account_paths(self):
        self.assertEqual(reverse("accounts:register"), "/cuenta/registro/")
        self.assertEqual(reverse("accounts:login"), "/cuenta/entrar/")
        self.assertEqual(reverse("accounts:logout"), "/cuenta/salir/")
        self.assertEqual(reverse("accounts:profile"), "/cuenta/perfil/")

    def test_login_url_setting_points_to_login_view(self):
        self.assertEqual(settings.LOGIN_URL, reverse("accounts:login"))


class RegistrationTests(TestCase):
    url = reverse("accounts:register")

    def test_get_renders_register_template_with_form(self):
        response, render_mock = rendered(self.client, self.url)
        self.assertEqual(response.status_code, 200)
        _, template, context = render_mock.call_args.args
        self.assertEqual(template, "accounts/register.html")
        self.assertIsInstance(context["form"], RegistrationForm)

    def test_valid_post_creates_hashed_user_and_logs_in(self):
        response = self.client.post(self.url, registration_data())
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )
        user = User.objects.get(email="nueva@example.com")
        self.assertEqual(user.alias, "NuevaCuenta")
        self.assertNotEqual(user.password, NEW_PASSWORD)
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_email_is_normalized_to_lowercase(self):
        self.client.post(self.url, registration_data(email="  Nueva@Example.COM "))
        self.assertTrue(User.objects.filter(email="nueva@example.com").exists())

    def test_rejects_duplicate_email_case_insensitively(self):
        create_user(email="nueva@example.com")
        response, render_mock = rendered(
            self.client, self.url, "post", registration_data(email="NUEVA@example.com")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", render_mock.call_args.args[2]["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_rejects_duplicate_alias_case_insensitively(self):
        create_user(alias="NuevaCuenta")
        _, render_mock = rendered(
            self.client, self.url, "post", registration_data(alias="nuevacuenta")
        )
        self.assertIn("alias", render_mock.call_args.args[2]["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_rejects_invalid_alias(self):
        for alias in ["ab", "a" * 31, "con espacio", "<script>"]:
            with self.subTest(alias=alias):
                _, render_mock = rendered(
                    self.client, self.url, "post", registration_data(alias=alias)
                )
                self.assertIn("alias", render_mock.call_args.args[2]["form"].errors)
        self.assertFalse(User.objects.exists())

    def test_rejects_mismatched_and_weak_passwords(self):
        cases = [
            {"password2": "no-coincide-789"},
            {"password1": "12345678", "password2": "12345678"},
            {"password1": "corta", "password2": "corta"},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                _, render_mock = rendered(
                    self.client, self.url, "post", registration_data(**overrides)
                )
                self.assertIn("password2", render_mock.call_args.args[2]["form"].errors)
        self.assertFalse(User.objects.exists())

    def test_rejects_missing_email(self):
        _, render_mock = rendered(
            self.client, self.url, "post", registration_data(email="")
        )
        self.assertIn("email", render_mock.call_args.args[2]["form"].errors)
        self.assertFalse(User.objects.exists())

    def test_form_exposes_no_privilege_fields(self):
        self.assertEqual(
            set(RegistrationForm().fields), {"email", "alias", "password1", "password2"}
        )

    def test_privilege_fields_in_post_are_ignored(self):
        self.client.post(
            self.url, registration_data(is_staff="on", is_superuser="on")
        )
        user = User.objects.get(email="nueva@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_authenticated_user_is_redirected(self):
        self.client.force_login(create_user())
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )

    def test_rejects_unsupported_method(self):
        self.assertEqual(self.client.put(self.url).status_code, 405)


class LoginTests(TestCase):
    url = reverse("accounts:login")

    def setUp(self):
        self.user = create_user()

    def test_get_renders_login_template_with_form(self):
        response, render_mock = rendered(self.client, self.url)
        self.assertEqual(response.status_code, 200)
        _, template, context = render_mock.call_args.args
        self.assertEqual(template, "accounts/login.html")
        self.assertIsInstance(context["form"], LoginForm)
        self.assertEqual(context["next"], "")

    def test_valid_credentials_log_in_and_rotate_session(self):
        self.client.get(reverse("core:health"))
        self.client.session.save()
        before = self.client.session.session_key
        response = self.client.post(
            self.url, {"username": "cuenta@example.com", "password": PASSWORD}
        )
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
        self.assertNotEqual(self.client.session.session_key, before)

    def test_email_lookup_is_case_insensitive(self):
        self.client.post(
            self.url, {"username": " CUENTA@Example.com ", "password": PASSWORD}
        )
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_and_unknown_email_get_equivalent_errors(self):
        errors = []
        for username, password in [
            ("cuenta@example.com", "incorrecta-123"),
            ("nadie@example.com", PASSWORD),
        ]:
            response, render_mock = rendered(
                self.client, self.url, "post", {"username": username, "password": password}
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("_auth_user_id", self.client.session)
            errors.append(render_mock.call_args.args[2]["form"].errors)
        self.assertEqual(errors[0], errors[1])

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        rendered(
            self.client, self.url, "post",
            {"username": "cuenta@example.com", "password": PASSWORD},
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_safe_next_url_is_followed(self):
        target = reverse("posts:create")
        response = self.client.post(
            self.url,
            {"username": "cuenta@example.com", "password": PASSWORD, "next": target},
        )
        self.assertRedirects(response, target, fetch_redirect_response=False)

    def test_external_next_url_is_ignored(self):
        response = self.client.post(
            self.url + "?next=https://malicioso.example/",
            {"username": "cuenta@example.com", "password": PASSWORD},
        )
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )

    def test_next_is_passed_to_template_only_when_safe(self):
        _, render_mock = rendered(self.client, self.url + "?next=/publicaciones/")
        self.assertEqual(render_mock.call_args.args[2]["next"], "/publicaciones/")
        _, render_mock = rendered(self.client, self.url + "?next=//malicioso.example/")
        self.assertEqual(render_mock.call_args.args[2]["next"], "")

    def test_post_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            self.url, {"username": "cuenta@example.com", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("_auth_user_id", client.session)


class LogoutTests(TestCase):
    url = reverse("accounts:logout")

    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    def test_post_logs_out_and_redirects_home(self):
        response = self.client.post(self.url)
        self.assertRedirects(
            response, reverse("core:home"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_get_is_rejected_and_keeps_session(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertIn("_auth_user_id", client.session)


class ProfileViewTests(TestCase):
    url = reverse("accounts:profile")

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"], f"{settings.LOGIN_URL}?next={self.url}"
        )

    def test_owner_sees_own_account_only(self):
        owner = create_user()
        create_user(email="otra@example.com", alias="OtraCuenta")
        self.client.force_login(owner)
        response, render_mock = rendered(self.client, self.url)
        self.assertEqual(response.status_code, 200)
        _, template, context = render_mock.call_args.args
        self.assertEqual(template, "accounts/profile.html")
        self.assertEqual(context["account"], owner)
        self.assertIn("no-store", response["Cache-Control"])

    def test_rejects_post(self):
        self.client.force_login(create_user())
        self.assertEqual(self.client.post(self.url).status_code, 405)
