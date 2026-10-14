"""Pruebas del perfil público mínimo (país ISO, región e idiomas)."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import Profile, User


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "perfil@example.com", "PerfilUno", "clave-sintetica-123"
        )

    def test_profile_only_stores_minimal_public_fields(self):
        field_names = {field.name for field in Profile._meta.get_fields()}
        self.assertEqual(
            field_names,
            {"id", "user", "description", "country", "region", "languages"},
        )

    def test_profile_accepts_required_country_and_optional_region(self):
        profile = Profile(
            user=self.user,
            country="ES",
            region="Comunidad de Madrid",
            description="Descripción sintética.",
            languages=["es", "en"],
        )
        profile.full_clean()
        self.assertIsNone(profile.pk)

    def test_region_is_optional(self):
        profile = Profile(user=self.user, country="ES")
        profile.full_clean()
        self.assertEqual(profile.region, "")

    def test_country_requires_two_uppercase_iso_letters(self):
        for country in ["es", "ESP", "E1", "12", "E", ""]:
            with self.subTest(country=country):
                with self.assertRaises(ValidationError):
                    Profile(user=self.user, country=country).full_clean()

    def test_languages_accept_iso_codes_without_repetition(self):
        for languages in [[], ["es"], ["es", "en", "pt"]]:
            with self.subTest(languages=languages):
                Profile(user=self.user, country="ES", languages=languages).full_clean()

    def test_languages_reject_invalid_values(self):
        for languages in [["español"], ["e"], ["ES"], ["es", "es"], "es", [1]]:
            with self.subTest(languages=languages):
                with self.assertRaises(ValidationError):
                    Profile(
                        user=self.user, country="ES", languages=languages
                    ).full_clean()

    def test_profile_is_reachable_from_user_and_str_uses_alias(self):
        profile = Profile.objects.create(user=self.user, country="ES")
        self.assertEqual(self.user.profile, profile)
        self.assertEqual(str(profile), "PerfilUno")

    def test_one_profile_per_user(self):
        Profile.objects.create(user=self.user, country="ES")
        with self.assertRaises(ValidationError):
            Profile(user=self.user, country="FR").full_clean()
