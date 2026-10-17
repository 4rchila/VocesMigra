"""Pruebas de validación del título, el contenido y los catálogos cerrados."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import User
from apps.posts.models import Category, Post, Status

PASSWORD = "clave-sintetica-123"


class PostValidationTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            "valida@example.com", "Valida", PASSWORD
        )

    def make_post(self, **overrides):
        data = {
            "author": self.author,
            "category": Category.COMMUNITY,
            "title": "Título de prueba válido",
            "content": "Contenido de prueba con longitud suficiente.",
            "status": Status.PUBLISHED,
        }
        data.update(overrides)
        return Post(**data)

    def test_valid_post_passes_model_validation(self):
        post = self.make_post()
        post.full_clean()
        self.assertIsNone(post.pk)

    def test_title_requires_at_least_ten_characters(self):
        with self.assertRaises(ValidationError):
            self.make_post(title="a" * 9).full_clean()
        self.make_post(title="a" * 10).full_clean()

    def test_title_allows_at_most_one_hundred_sixty_characters(self):
        self.make_post(title="a" * 160).full_clean()
        with self.assertRaises(ValidationError):
            self.make_post(title="a" * 161).full_clean()

    def test_content_requires_at_least_twenty_characters(self):
        with self.assertRaises(ValidationError):
            self.make_post(content="a" * 19).full_clean()
        self.make_post(content="a" * 20).full_clean()

    def test_content_allows_at_most_ten_thousand_characters(self):
        self.make_post(content="a" * 10000).full_clean()
        with self.assertRaises(ValidationError):
            self.make_post(content="a" * 10001).full_clean()

    def test_category_must_belong_to_the_stable_catalog(self):
        for category in ["", "vivencias", "desconocida", None]:
            with self.subTest(category=category):
                with self.assertRaises(ValidationError):
                    self.make_post(category=category).full_clean()

    def test_status_must_be_draft_or_published(self):
        for status in ["", "archived", "oculta", None]:
            with self.subTest(status=status):
                with self.assertRaises(ValidationError):
                    self.make_post(status=status).full_clean()

    def test_author_is_required(self):
        with self.assertRaises(ValidationError):
            self.make_post(author=None).full_clean()
