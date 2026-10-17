"""Pruebas del modelo de publicación: identidad, estado y metadatos."""

import uuid
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.posts.models import Category, Post, Status

from tests.posts.support import create_post, create_user


class CategoryTests(TestCase):
    def test_category_keys_and_labels_are_stable(self):
        self.assertEqual(
            [category.value for category in Category],
            ["experiences", "problems", "help", "opinions", "community"],
        )
        self.assertEqual(
            [str(category.label) for category in Category],
            ["Vivencias", "Problemas", "Ayudas", "Opiniones", "Comunidad"],
        )

    def test_status_exposes_draft_and_published(self):
        self.assertEqual(Status.DRAFT, "draft")
        self.assertEqual(Status.PUBLISHED, "published")


class PostModelTests(TestCase):
    def setUp(self):
        self.author = create_user()

    def test_only_expected_fields_are_stored(self):
        field_names = {field.name for field in Post._meta.get_fields()}
        self.assertEqual(
            field_names,
            {
                "id",
                "public_id",
                "author",
                "category",
                "title",
                "content",
                "status",
                "created_at",
                "updated_at",
            },
        )

    def test_public_id_is_a_unique_uuid_different_from_the_primary_key(self):
        first = create_post(author=self.author)
        second = create_post(
            author=self.author, title="Otro título de prueba válido"
        )

        self.assertIsInstance(first.public_id, uuid.UUID)
        self.assertIsInstance(second.public_id, uuid.UUID)
        self.assertNotEqual(first.public_id, second.public_id)
        self.assertNotEqual(first.pk, first.public_id)

    def test_status_defaults_to_draft(self):
        post = Post.objects.create(
            author=self.author,
            category=Category.PROBLEMS,
            title="Título de prueba válido",
            content="Contenido de prueba con longitud suficiente.",
        )
        self.assertEqual(post.status, Status.DRAFT)

    def test_str_returns_the_title(self):
        post = create_post(author=self.author, title="Un título legible")
        self.assertEqual(str(post), "Un título legible")

    def test_author_is_reachable_through_the_posts_related_name(self):
        post = create_post(author=self.author)
        self.assertEqual(list(self.author.posts.all()), [post])

    def test_get_absolute_url_uses_the_public_id(self):
        post = create_post(author=self.author)
        self.assertEqual(
            post.get_absolute_url(),
            reverse("posts:detail", args=[post.public_id]),
        )

    def test_creation_and_update_timestamps_are_tracked(self):
        post = create_post(author=self.author)
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)

        older = timezone.now() - timedelta(days=2)
        Post.objects.filter(pk=post.pk).update(created_at=older)
        post.refresh_from_db()
        self.assertLess(post.created_at, post.updated_at)

    def test_default_ordering_is_most_recent_first(self):
        oldest = create_post(author=self.author, title="Publicación más antigua")
        newest = create_post(author=self.author, title="Publicación más reciente")

        base = timezone.now() - timedelta(days=1)
        Post.objects.filter(pk=oldest.pk).update(created_at=base)
        Post.objects.filter(pk=newest.pk).update(
            created_at=base + timedelta(hours=1)
        )

        self.assertEqual(list(Post.objects.all()), [newest, oldest])
