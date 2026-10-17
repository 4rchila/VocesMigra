"""Pruebas de integración real entre vistas y plantillas de publicaciones."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.posts.models import Category, Post, Status


class PostsTemplateIntegrationTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            "autora@example.com", "Autora", "clave-sintetica-123"
        )

    def test_post_list_renders_public_id_and_stable_categories(self):
        post = Post.objects.create(
            author=self.author,
            category=Category.EXPERIENCES,
            title="Una experiencia migratoria compartida",
            content="Contenido comunitario con longitud suficiente para la prueba.",
            status=Status.PUBLISHED,
        )

        response = self.client.get(reverse("posts:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, post.title)
        self.assertContains(response, post.get_absolute_url())
        self.assertContains(response, "?categoria=experiences")
        self.assertContains(response, "Vivencias")

    def test_post_detail_renders_content_and_public_id_actions(self):
        post = Post.objects.create(
            author=self.author,
            category=Category.HELP,
            title="Orientación comunitaria para un trámite",
            content="Información detallada y útil para acompañar este proceso migratorio.",
            status=Status.PUBLISHED,
        )
        self.client.force_login(self.author)

        response = self.client.get(post.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, post.content)
        self.assertContains(response, reverse("posts:update", args=[post.public_id]))
        self.assertContains(response, reverse("posts:delete", args=[post.public_id]))

    def test_update_form_uses_public_id_cancel_link(self):
        post = Post.objects.create(
            author=self.author,
            category=Category.COMMUNITY,
            title="Actualización comunitaria de una publicación",
            content="Contenido válido que puede ser actualizado por su autora.",
            status=Status.DRAFT,
        )
        self.client.force_login(self.author)

        response = self.client.get(reverse("posts:update", args=[post.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, post.get_absolute_url())

    def test_delete_confirmation_uses_public_id_links(self):
        post = Post.objects.create(
            author=self.author,
            category=Category.OPINIONS,
            title="Una opinión que puede eliminar su autora",
            content="Contenido válido para comprobar la confirmación de eliminación.",
            status=Status.DRAFT,
        )
        self.client.force_login(self.author)

        response = self.client.get(reverse("posts:delete", args=[post.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("posts:delete", args=[post.public_id]))
        self.assertContains(response, post.get_absolute_url())

    def test_home_renders_recent_published_posts(self):
        published = Post.objects.create(
            author=self.author,
            category=Category.PROBLEMS,
            title="Un problema compartido con la comunidad",
            content="Contenido publicado que debe aparecer en la portada institucional.",
            status=Status.PUBLISHED,
        )
        draft = Post.objects.create(
            author=self.author,
            category=Category.HELP,
            title="Un borrador privado que no debe aparecer",
            content="Contenido de borrador suficiente para comprobar que no se publica.",
            status=Status.DRAFT,
        )

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, published.title)
        self.assertContains(response, published.get_absolute_url())
        self.assertNotContains(response, draft.title)
        self.assertContains(response, "?categoria=problems")
