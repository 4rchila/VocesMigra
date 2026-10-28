"""Pruebas de configuración, entorno y salud del fundamento backend."""

import importlib
import json
import os
import sys
from unittest import mock

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import ConnectionHandler
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from config.settings import base


class AppRegistryTests(SimpleTestCase):
    def test_local_apps_are_installed(self):
        labels = {config.label for config in apps.get_app_configs()}
        self.assertIn("core", labels)
        self.assertIn("accounts", labels)

    def test_auth_user_model_points_to_accounts(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_i18n_and_timezone_are_enabled(self):
        self.assertEqual(settings.LANGUAGE_CODE, "es")
        self.assertTrue(settings.USE_I18N)
        self.assertTrue(settings.USE_TZ)


class EnvironmentHelpersTests(SimpleTestCase):
    def test_env_returns_default_when_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(base.env("FALTANTE", default="x"), "x")

    def test_env_required_raises_when_missing_or_empty(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                base.env("FALTANTE", required=True)
        with mock.patch.dict(os.environ, {"VACIA": "   "}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                base.env("VACIA", required=True)

    def test_env_bool_parses_common_values(self):
        for raw in ["1", "true", "YES", "on", " True "]:
            with mock.patch.dict(os.environ, {"X": raw}, clear=True):
                self.assertTrue(base.env_bool("X"), raw)
        for raw in ["0", "false", "no", "off"]:
            with mock.patch.dict(os.environ, {"X": raw}, clear=True):
                self.assertFalse(base.env_bool("X"), raw)

    def test_env_list_splits_and_strips(self):
        with mock.patch.dict(os.environ, {"X": " a, b ,,c "}, clear=True):
            self.assertEqual(base.env_list("X"), ["a", "b", "c"])


class DatabaseSettingsTests(SimpleTestCase):
    def test_sqlite_default_path_is_local(self):
        database = base.sqlite_database()
        self.assertEqual(database["ENGINE"], "django.db.backends.sqlite3")
        self.assertTrue(str(database["NAME"]).endswith("db.sqlite3"))

    def test_sqlite_accepts_explicit_path(self):
        database = base.sqlite_database("/tmp/voces.sqlite3")
        self.assertEqual(str(database["NAME"]), "/tmp/voces.sqlite3")

    def test_postgres_requires_environment_variables(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                base.postgres_database_from_env()

    def test_postgres_is_built_only_from_environment(self):
        environment = {
            "POSTGRES_DB": "voces",
            "POSTGRES_USER": "voces",
            "POSTGRES_PASSWORD": "sintetica",
            "POSTGRES_HOST": "db.interno",
            "POSTGRES_PORT": "6543",
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            database = base.postgres_database_from_env()
        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["NAME"], "voces")
        self.assertEqual(database["USER"], "voces")
        self.assertEqual(database["PASSWORD"], "sintetica")
        self.assertEqual(database["HOST"], "db.interno")
        self.assertEqual(database["PORT"], "6543")

    def test_postgres_sslmode_defaults_to_require_and_is_configurable(self):
        environment = {
            "POSTGRES_DB": "voces",
            "POSTGRES_USER": "voces",
            "POSTGRES_PASSWORD": "synthetic-only",
            "POSTGRES_HOST": "db.example.test",
            "POSTGRES_PORT": "5432",
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            database = base.postgres_database_from_env()
        self.assertEqual(database["OPTIONS"]["sslmode"], "require")

        environment["POSTGRES_SSLMODE"] = "verify-full"
        with mock.patch.dict(os.environ, environment, clear=True):
            database = base.postgres_database_from_env()
        self.assertEqual(database["OPTIONS"]["sslmode"], "verify-full")

    def test_postgres_backend_builds_connection_params_without_network(self):
        environment = {
            "POSTGRES_DB": "voces",
            "POSTGRES_USER": "voces",
            "POSTGRES_PASSWORD": "synthetic-only",
            "POSTGRES_HOST": "db.example.test",
            "POSTGRES_PORT": "5432",
            "POSTGRES_SSLMODE": "require",
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            database = base.postgres_database_from_env()

        connection = ConnectionHandler({"default": database})["default"]
        params = connection.get_connection_params()

        self.assertEqual(params["dbname"], "voces")
        self.assertEqual(params["user"], "voces")
        self.assertEqual(params["host"], "db.example.test")
        self.assertEqual(params["port"], "5432")
        self.assertEqual(params["sslmode"], "require")

    def test_test_settings_are_isolated_sqlite(self):
        if settings.SETTINGS_MODULE != "config.settings.test":
            self.skipTest("Requiere DJANGO_SETTINGS_MODULE=config.settings.test")
        database = settings.DATABASES["default"]
        self.assertEqual(database["ENGINE"], "django.db.backends.sqlite3")
        self.assertIn("memory", database["NAME"])
        self.assertIn(
            "django.contrib.auth.hashers.MD5PasswordHasher",
            settings.PASSWORD_HASHERS,
        )


class ProductionSettingsTests(SimpleTestCase):
    MODULE = "config.settings.production"

    def _import_production(self, environment):
        saved = sys.modules.pop(self.MODULE, None)
        try:
            with mock.patch.dict(os.environ, environment, clear=True):
                return importlib.import_module(self.MODULE)
        finally:
            sys.modules.pop(self.MODULE, None)
            if saved is not None:
                sys.modules[self.MODULE] = saved

    def full_environment(self):
        return {
            "DJANGO_SECRET_KEY": "clave-sintetica-de-produccion",
            "DJANGO_ALLOWED_HOSTS": "voces.example,www.voces.example",
            "POSTGRES_DB": "voces",
            "POSTGRES_USER": "voces",
            "POSTGRES_PASSWORD": "sintetica",
            "POSTGRES_HOST": "db.interno",
            "POSTGRES_PORT": "5432",
            "DJANGO_ADMIN_URL": "panel-sintetico",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://voces.example",
        }

    def test_requires_secret_key(self):
        environment = self.full_environment()
        environment.pop("DJANGO_SECRET_KEY")
        with self.assertRaises(ImproperlyConfigured):
            self._import_production(environment)

    def test_requires_allowed_hosts(self):
        environment = self.full_environment()
        environment.pop("DJANGO_ALLOWED_HOSTS")
        with self.assertRaises(ImproperlyConfigured):
            self._import_production(environment)

    def test_requires_postgres_variables(self):
        environment = self.full_environment()
        environment.pop("POSTGRES_PASSWORD")
        with self.assertRaises(ImproperlyConfigured):
            self._import_production(environment)

    def test_production_uses_postgres_and_secure_defaults(self):
        module = self._import_production(self.full_environment())
        self.assertFalse(module.DEBUG)
        self.assertEqual(
            module.DATABASES["default"]["ENGINE"], "django.db.backends.postgresql"
        )
        self.assertEqual(module.DATABASES["default"]["NAME"], "voces")
        self.assertEqual(
            module.ALLOWED_HOSTS, ["voces.example", "www.voces.example"]
        )
        self.assertTrue(module.SESSION_COOKIE_SECURE)
        self.assertTrue(module.CSRF_COOKIE_SECURE)
        self.assertTrue(module.SECURE_SSL_REDIRECT)

    def test_requires_admin_url_and_rejects_admin(self):
        environment = self.full_environment()
        environment.pop("DJANGO_ADMIN_URL")
        with self.assertRaises(ImproperlyConfigured):
            self._import_production(environment)
        for value in ["admin", "/admin/", " ADMIN "]:
            environment["DJANGO_ADMIN_URL"] = value
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                self._import_production(environment)

    def test_proxy_csrf_and_headers(self):
        module = self._import_production(self.full_environment())
        self.assertEqual(
            module.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https")
        )
        self.assertEqual(module.CSRF_TRUSTED_ORIGINS, ["https://voces.example"])
        self.assertEqual(module.SECURE_REFERRER_POLICY, "strict-origin-when-cross-origin")
        self.assertEqual(module.TRUSTED_PROXY_COUNT, 1)
        self.assertEqual(
            module.CACHES["default"]["BACKEND"],
            "django.core.cache.backends.db.DatabaseCache",
        )

    def test_csrf_trusted_origins_must_be_https(self):
        environment = self.full_environment()
        environment["DJANGO_CSRF_TRUSTED_ORIGINS"] = "http://voces.example"
        with self.assertRaises(ImproperlyConfigured):
            self._import_production(environment)

    def test_smtp_defaults_to_587_with_tls(self):
        module = self._import_production(self.full_environment())
        self.assertEqual(module.EMAIL_PORT, 587)
        self.assertTrue(module.EMAIL_USE_TLS)

    def test_smtp_without_tls_is_rejected(self):
        environment = self.full_environment()
        environment["EMAIL_USE_TLS"] = "false"
        with self.assertRaises(ImproperlyConfigured):
            self._import_production(environment)


class HealthViewTests(TestCase):
    def test_health_url_is_public_and_stable(self):
        self.assertEqual(reverse("core:health"), "/health/")

    def test_health_returns_ok_json(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(response.content), {"status": "ok", "database": "ok"}
        )
        self.assertIn("no-cache", response["Cache-Control"])

    def test_health_returns_503_when_database_fails(self):
        from django.db import OperationalError

        with mock.patch(
            "apps.core.views.connection.cursor",
            side_effect=OperationalError("host db.secreto.example caido"),
        ), self.assertLogs("apps.core.views", level="ERROR"):
            response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 503)
        body = json.loads(response.content)
        self.assertEqual(body, {"status": "error", "database": "unavailable"})
        self.assertNotIn(b"secreto", response.content)

    def test_health_rejects_non_get_methods(self):
        response = self.client.post(reverse("core:health"))
        self.assertEqual(response.status_code, 405)


class HomeViewTests(TestCase):
    def test_home_renders_the_ui_foundation(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
