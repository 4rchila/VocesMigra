"""Pruebas de la matriz de permisos de las vistas de publicación."""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.posts.models import Category, Post, Status

from tests.posts.support import CONTENT, create_user, rendered


def make_published(author):
    return Post.objects.create(
        author=author,
        category=Category.EXPERIENCES,
        title="Publicación publicada",
        content=CONTENT,
        status=Status.PUBLISHED,
    )


def writer_payload():
    return {
        "category": Category.EXPERIENCES,
        "title": "Intento de escritura ajena",
        "content": CONTENT,
        "status": Status.PUBLISHED,
    }


class AnonymousPermissionsTests(TestCase):
    def setUp(self):
        self.author = create_user("autora@example.com", "Autora")
        self.post = make_published(self.author)

    def test_anyone_can_read_the_feed_and_published_details(self):
        feed_response, feed_render = rendered(
            self.client, reverse("posts:list")
        )
        detail_response, detail_render = rendered(
            self.client, reverse("posts:detail", args=[self.post.public_id])
        )

        self.assertEqual(feed_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(feed_render.call_args.args[1], "posts/post_list.html")
        self.assertEqual(
            detail_render.call_args.args[1], "posts/post_detail.html"
        )

    def test_write_views_redirect_to_login(self):
        for url in [
            reverse("posts:create"),
            reverse("posts:update", args=[self.post.public_id]),
            reverse("posts:delete", args=[self.post.public_id]),
        ]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith(settings.LOGIN_URL))

    def test_anonymous_post_requests_never_mutate_state(self):
        payload = writer_payload()
        create_response = self.client.post(reverse("posts:create"), payload)
        update_response = self.client.post(
            reverse("posts:update", args=[self.post.public_id]), payload
        )
        delete_response = self.client.post(
            reverse("posts:delete", args=[self.post.public_id])
        )

        self.assertEqual(create_response.status_code, 302)
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Publicación publicada")


class AuthorOnlyPermissionsTests(TestCase):
    def setUp(self):
        self.author = create_user("autora@example.com", "Autora")
        self.other = create_user("lector@example.com", "Lector")
        self.post = make_published(self.author)

    def test_another_person_cannot_open_the_edit_or_delete_views(self):
        self.client.force_login(self.other)

        for name in ["posts:update", "posts:delete"]:
            with self.subTest(name=name):
                response = self.client.get(
                    reverse(name, args=[self.post.public_id])
                )
                self.assertEqual(response.status_code, 404)

    def test_another_person_cannot_mutate_through_direct_post(self):
        self.client.force_login(self.other)

        update_response = self.client.post(
            reverse("posts:update", args=[self.post.public_id]), writer_payload()
        )
        delete_response = self.client.post(
            reverse("posts:delete", args=[self.post.public_id])
        )

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Publicación publicada")

    def test_another_person_can_read_a_published_post(self):
        self.client.force_login(self.other)

        response, _ = rendered(
            self.client, reverse("posts:detail", args=[self.post.public_id])
        )

        self.assertEqual(response.status_code, 200)

    def test_the_author_keeps_full_control_of_their_post(self):
        self.client.force_login(self.author)

        update_response = self.client.post(
            reverse("posts:update", args=[self.post.public_id]), writer_payload()
        )
        delete_response = self.client.post(
            reverse("posts:delete", args=[self.post.public_id])
        )

        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_a_draft_is_invisible_and_untouchable_for_others(self):
        draft = Post.objects.create(
            author=self.author,
            category=Category.HELP,
            title="Borrador privado de la autora",
            content=CONTENT,
            status=Status.DRAFT,
        )
        self.client.force_login(self.other)

        responses = [
            self.client.get(reverse("posts:detail", args=[draft.public_id])),
            self.client.get(reverse("posts:update", args=[draft.public_id])),
            self.client.get(reverse("posts:delete", args=[draft.public_id])),
        ]

        self.assertEqual(
            [response.status_code for response in responses], [404, 404, 404]
        )
