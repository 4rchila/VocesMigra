"""Pruebas de las vistas de escritura: creación, edición y eliminación."""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.posts.forms import PostForm
from apps.posts.models import Category, Post, Status

from tests.posts.support import (
    CONTENT,
    context_of,
    create_post,
    create_user,
    rendered,
    template_of,
)


class CreateViewTests(TestCase):
    def setUp(self):
        self.author = create_user()
        self.url = reverse("posts:create")
        self.valid_data = {
            "category": Category.EXPERIENCES,
            "title": "Publicación creada válida",
            "content": CONTENT,
            "status": Status.PUBLISHED,
        }

    def test_get_renders_the_form_template_for_authenticated_people(self):
        self.client.force_login(self.author)

        response, render_mock = rendered(self.client, self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(template_of(render_mock), "posts/post_form.html")
        self.assertIsInstance(context_of(render_mock)["form"], PostForm)

    def test_post_creates_a_published_post_owned_by_the_session_author(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, self.valid_data)

        post = Post.objects.get()
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.category, Category.EXPERIENCES)
        self.assertEqual(post.status, Status.PUBLISHED)
        self.assertRedirects(
            response,
            reverse("posts:detail", args=[post.public_id]),
            fetch_redirect_response=False,
        )

    def test_post_can_save_a_draft(self):
        self.client.force_login(self.author)

        response = self.client.post(
            self.url, {**self.valid_data, "status": Status.DRAFT}
        )

        post = Post.objects.get()
        self.assertEqual(post.status, Status.DRAFT)
        self.assertRedirects(
            response,
            reverse("posts:detail", args=[post.public_id]),
            fetch_redirect_response=False,
        )

    def test_invalid_data_rerenders_the_form_without_persisting(self):
        self.client.force_login(self.author)

        response, render_mock = rendered(
            self.client,
            self.url,
            method="post",
            data={**self.valid_data, "title": "Corto"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(template_of(render_mock), "posts/post_form.html")
        self.assertIn("title", context_of(render_mock)["form"].errors)
        self.assertEqual(Post.objects.count(), 0)

    def test_get_never_changes_state(self):
        self.client.force_login(self.author)

        rendered(self.client, self.url)

        self.assertEqual(Post.objects.count(), 0)


class UpdateViewTests(TestCase):
    def setUp(self):
        self.author = create_user()
        self.other = create_user("lector@example.com", "Lector")
        self.post = create_post(author=self.author)
        self.url = reverse("posts:update", args=[self.post.public_id])

    def test_author_get_renders_the_form_with_the_instance(self):
        self.client.force_login(self.author)

        response, render_mock = rendered(self.client, self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(template_of(render_mock), "posts/post_form.html")
        context = context_of(render_mock)
        self.assertEqual(context["post"], self.post)
        self.assertIsInstance(context["form"], PostForm)

    def test_author_updates_the_post_and_is_redirected_to_the_detail(self):
        self.client.force_login(self.author)
        new_content = "Contenido actualizado con longitud suficiente."

        response = self.client.post(
            self.url,
            {
                "category": Category.HELP,
                "title": "Título actualizado válido",
                "content": new_content,
                "status": Status.PUBLISHED,
            },
        )

        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Título actualizado válido")
        self.assertEqual(self.post.content, new_content)
        self.assertEqual(self.post.category, Category.HELP)
        self.assertRedirects(
            response,
            reverse("posts:detail", args=[self.post.public_id]),
            fetch_redirect_response=False,
        )

    def test_update_never_reassigns_the_author(self):
        self.client.force_login(self.author)

        self.client.post(
            self.url,
            {
                "category": Category.EXPERIENCES,
                "title": "Título actualizado válido",
                "content": CONTENT,
                "status": Status.PUBLISHED,
                "author": self.other.pk,
            },
        )

        self.post.refresh_from_db()
        self.assertEqual(self.post.author, self.author)

    def test_invalid_update_keeps_the_previous_content(self):
        self.client.force_login(self.author)

        response, render_mock = rendered(
            self.client,
            self.url,
            method="post",
            data={
                "category": Category.EXPERIENCES,
                "title": "Corto",
                "content": CONTENT,
                "status": Status.PUBLISHED,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("title", context_of(render_mock)["form"].errors)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Publicación de prueba válida")


class DeleteViewTests(TestCase):
    def setUp(self):
        self.author = create_user()
        self.post = create_post(author=self.author)
        self.url = reverse("posts:delete", args=[self.post.public_id])

    def test_author_get_renders_the_confirmation_template(self):
        self.client.force_login(self.author)

        response, render_mock = rendered(self.client, self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            template_of(render_mock), "posts/post_confirm_delete.html"
        )
        self.assertEqual(context_of(render_mock)["post"], self.post)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_author_post_deletes_the_post_and_redirects_to_the_feed(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url)

        self.assertRedirects(
            response, reverse("posts:list"), fetch_redirect_response=False
        )
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class AuthenticatedRedirectTests(TestCase):
    def test_anonymous_write_attempts_are_redirected_to_the_login_url(self):
        post = create_post(author=create_user())
        urls = [
            reverse("posts:create"),
            reverse("posts:update", args=[post.public_id]),
            reverse("posts:delete", args=[post.public_id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith(settings.LOGIN_URL))
