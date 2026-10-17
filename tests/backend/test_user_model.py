"""Pruebas del usuario propio, su manager y la unicidad del alias."""

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User

PASSWORD = "clave-sintetica-123"


def create_user(**overrides):
    data = {"email": "persona@example.com", "alias": "Persona"}
    data.update(overrides)
    return User.objects.create_user(data["email"], data["alias"], PASSWORD)


class UserManagerTests(TestCase):
    def test_create_user_uses_email_and_hashes_password(self):
        user = create_user()
        self.assertEqual(user.email, "persona@example.com")
        self.assertEqual(user.alias, "Persona")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_create_user_normalizes_email_case_and_spaces(self):
        user = create_user(email="  Persona@Example.COM  ")
        self.assertEqual(user.email, "persona@example.com")

    def test_create_user_requires_email_and_alias(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", "Persona", PASSWORD)
        with self.assertRaises(ValueError):
            User.objects.create_user("persona@example.com", "", PASSWORD)

    def test_create_superuser_sets_privileges(self):
        user = User.objects.create_superuser("admin@example.com", "AdminUno", PASSWORD)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_superuser_rejects_downgraded_flags(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                "admin@example.com", "AdminUno", PASSWORD, is_staff=False
            )
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                "admin@example.com", "AdminUno", PASSWORD, is_superuser=False
            )

    def test_authentication_uses_email_as_identifier(self):
        create_user()
        self.assertIsNotNone(authenticate(username="persona@example.com", password=PASSWORD))
        self.assertIsNone(authenticate(username="persona@example.com", password="incorrecta"))


class UserIdentifierTests(TestCase):
    def test_username_field_and_required_fields(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertEqual(User.REQUIRED_FIELDS, ["alias"])

    def test_str_returns_public_alias(self):
        self.assertEqual(str(create_user()), "Persona")

    def test_email_is_unique_case_insensitively_after_normalization(self):
        create_user()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_user(email="PERSONA@example.com", alias="OtraPersona")

    def test_alias_is_unique_case_insensitively(self):
        create_user(alias="PersonaUno")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_user(email="otra@example.com", alias="personauno")

    def test_distinct_aliases_are_allowed(self):
        create_user(alias="PersonaUno")
        second = create_user(email="otra@example.com", alias="PersonaDos")
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(second.alias, "PersonaDos")


class AliasValidationTests(TestCase):
    def make_user(self, alias):
        return User(email="valido@example.com", alias=alias, password=PASSWORD)

    def test_alias_requires_minimum_length(self):
        with self.assertRaises(ValidationError):
            self.make_user("ab").full_clean()

    def test_alias_allows_maximum_length(self):
        self.make_user("a" * 30).full_clean()

    def test_alias_rejects_longer_than_maximum(self):
        with self.assertRaises(ValidationError):
            self.make_user("a" * 31).full_clean()

    def test_alias_accepts_unicode_letters_numbers_and_symbols(self):
        for alias in ["María.2024", "café_con-leche", "Ünïcøde.99", "a.b-c_9"]:
            with self.subTest(alias=alias):
                self.make_user(alias).full_clean()

    def test_alias_rejects_spaces_and_other_symbols(self):
        for alias in ["con espacio", "arroba@", "barra/", "emoji😀", "punto!"]:
            with self.subTest(alias=alias):
                with self.assertRaises(ValidationError):
                    self.make_user(alias).full_clean()
