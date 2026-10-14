"""Pruebas de las consultas del feed público y del acceso al detalle."""

from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.posts.models import Category, Post, Status

from tests.posts.support import (
    CONTENT,
    context_of,
    create_post,
    create_user,
    rendered,
    template_of,
)


class PostQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = create_user("autora@example.com", "Autora")
        cls.other = create_user("lector@example.com", "Lector")
        cls.published = Post.objects.create(
            author=cls.author,
            category=Category.EXPERIENCES,
            title="Publicación publicada",
            content=CONTENT,
            status=Status.PUBLISHED,
        )
        cls.draft = Post.objects.create(
            author=cls.author,
            category=Category.HELP,
            title="Borrador privado de la autora",
            content=CONTENT,
            status=Status.DRAFT,
        )

    def test_published_returns_only_published_posts(self):
        self.assertEqual(list(Post.objects.published()), [self.published])

    def test_visible_to_none_or_anonymous_returns_only_published(self):
        for user in [None, AnonymousUser()]:
            with self.subTest(user=user):
                self.assertEqual(
                    list(Post.objects.visible_to(user)), [self.published]
                )

    def test_visible_to_author_includes_own_drafts(self):
        self.assertCountEqual(
            Post.objects.visible_to(self.author), [self.published, self.draft]
        )

    def test_visible_to_another_person_excludes_foreign_drafts(self):
        self.assertEqual(list(Post.objects.visible_to(self.other)), [self.published])


class FeedViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = create_user("autora@example.com", "Autora")

    def test_list_is_public_and_requests_the_feed_template(self):
        create_post(author=self.author)

        response, render_mock = rendered(self.client, reverse("posts:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(template_of(render_mock), "posts/post_list.html")

    def test_list_shows_only_published_posts(self):
        visible = create_post(author=self.author)
        create_post(author=self.author, status=Status.DRAFT)

        _, render_mock = rendered(self.client, reverse("posts:list"))

        self.assertEqual(context_of(render_mock)["posts"], [visible])

    def test_list_orders_most_recent_first(self):
        base = timezone.now() - timedelta(days=3)
        oldest = create_post(author=self.author, title="Publicación más antigua")
        newest = create_post(author=self.author, title="Publicación más reciente")
        Post.objects.filter(pk=oldest.pk).update(created_at=base)
        Post.objects.filter(pk=newest.pk).update(
            created_at=base + timedelta(days=1)
        )

        _, render_mock = rendered(self.client, reverse("posts:list"))

        self.assertEqual(context_of(render_mock)["posts"], [newest, oldest])

    def test_list_filters_by_category(self):
        experiences = create_post(
            author=self.author,
            category=Category.EXPERIENCES,
            title="Experiencia de viaje",
        )
        create_post(
            author=self.author,
            category=Category.OPINIONS,
            title="Opinión comunitaria",
        )

        _, render_mock = rendered(
            self.client,
            reverse("posts:list"),
            data={"categoria": "experiences"},
        )

        context = context_of(render_mock)
        self.assertEqual(context["posts"], [experiences])
        self.assertEqual(context["selected_category"], "experiences")

    def test_list_exposes_the_stable_category_catalog(self):
        _, render_mock = rendered(self.client, reverse("posts:list"))

        context = context_of(render_mock)
        self.assertEqual(
            [value for value, _ in context["categories"]],
            ["experiences", "problems", "help", "opinions", "community"],
        )
        self.assertEqual(context["selected_category"], "")

    def test_list_ignores_an_unknown_category(self):
        visible = create_post(author=self.author)

        _, render_mock = rendered(
            self.client,
            reverse("posts:list"),
            data={"categoria": "vivencias"},
        )

        context = context_of(render_mock)
        self.assertEqual(context["posts"], [visible])
        self.assertEqual(context["selected_category"], "")

    def test_list_paginates_fifteen_posts_per_page(self):
        for index in range(16):
            create_post(author=self.author, title=f"Publicación paginada {index:02d}")

        _, first_render = rendered(self.client, reverse("posts:list"))
        _, second_render = rendered(
            self.client, reverse("posts:list"), data={"page": 2}
        )

        first_context = context_of(first_render)
        second_context = context_of(second_render)
        self.assertEqual(len(first_context["posts"]), 15)
        self.assertEqual(first_context["page_obj"].number, 1)
        self.assertEqual(second_context["page_obj"].number, 2)
        self.assertEqual(len(second_context["posts"]), 1)
        self.assertEqual(second_context["page_obj"].paginator.num_pages, 2)

    def test_list_uses_select_related_for_authors_without_extra_queries(self):
        for index in range(4):
            create_post(author=self.author, title=f"Publicación con autora {index:02d}")

        with self.assertNumQueries(2):
            _, render_mock = rendered(self.client, reverse("posts:list"))

        self.assertEqual(len(context_of(render_mock)["posts"]), 4)

    def test_detail_is_public_for_published_posts(self):
        post = create_post(author=self.author)

        response, render_mock = rendered(
            self.client, reverse("posts:detail", args=[post.public_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(template_of(render_mock), "posts/post_detail.html")
        self.assertEqual(context_of(render_mock)["post"], post)

    def test_detail_uses_select_related_for_the_author(self):
        post = create_post(author=self.author)

        with self.assertNumQueries(1):
            _, render_mock = rendered(
                self.client, reverse("posts:detail", args=[post.public_id])
            )

        self.assertEqual(context_of(render_mock)["post"].author, self.author)

    def test_detail_hides_drafts_from_other_people(self):
        draft = create_post(author=self.author, status=Status.DRAFT)

        response = self.client.get(
            reverse("posts:detail", args=[draft.public_id])
        )

        self.assertEqual(response.status_code, 404)

    def test_detail_shows_an_own_draft_to_its_author(self):
        draft = create_post(author=self.author, status=Status.DRAFT)
        self.client.force_login(self.author)

        response, render_mock = rendered(
            self.client, reverse("posts:detail", args=[draft.public_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(context_of(render_mock)["post"], draft)

    def test_detail_returns_404_for_an_unknown_identifier(self):
        response = self.client.get(
            reverse("posts:detail", args=["11111111-1111-1111-1111-111111111111"])
        )

        self.assertEqual(response.status_code, 404)


class UrlContractTests(TestCase):
    def test_public_url_names_and_paths_are_stable(self):
        post = create_post(author=create_user())

        self.assertEqual(reverse("posts:list"), "/publicaciones/")
        self.assertEqual(
            reverse("posts:detail", args=[post.public_id]),
            f"/publicaciones/{post.public_id}/",
        )
        self.assertEqual(reverse("posts:create"), "/publicaciones/nueva/")
        self.assertEqual(
            reverse("posts:update", args=[post.public_id]),
            f"/publicaciones/{post.public_id}/editar/",
        )
        self.assertEqual(
            reverse("posts:delete", args=[post.public_id]),
            f"/publicaciones/{post.public_id}/eliminar/",
        )
