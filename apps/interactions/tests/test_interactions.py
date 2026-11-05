"""Pruebas de comentarios, votos y orden por relevancia."""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.interactions.models import (
    COMMENT_MAX_LENGTH,
    Comment,
    CommentVote,
    Vote,
)
from apps.posts.models import Category, Post, Status

PASSWORD = "clave-sintetica-123"


def make_user(n):
    return User.objects.create_user(f"u{n}@example.com", f"Persona{n}", PASSWORD)


def make_post(author, title="Publicación de prueba válida", **kw):
    data = {
        "author": author,
        "category": Category.EXPERIENCES,
        "title": title,
        "content": "Contenido de prueba con longitud suficiente.",
        "status": Status.PUBLISHED,
    }
    data.update(kw)
    return Post.objects.create(**data)


class Base(TestCase):
    def setUp(self):
        self.author = make_user(1)
        self.other = make_user(2)
        self.post = make_post(self.author)

    def login(self, user):
        self.client.force_login(user)

    def vote_url(self):
        return reverse("interactions:post_vote", args=[self.post.public_id])

    def comment_url(self):
        return reverse("interactions:comment_create", args=[self.post.public_id])


class ConstraintTests(Base):
    def test_unique_vote_per_user_and_post(self):
        Vote.objects.create(post=self.post, user=self.other, value=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(post=self.post, user=self.other, value=-1)

    def test_unique_comment_vote_per_user_and_comment(self):
        c = Comment.objects.create(post=self.post, author=self.author, content="hola")
        CommentVote.objects.create(comment=c, user=self.other, value=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CommentVote.objects.create(comment=c, user=self.other, value=1)

    def test_db_rejects_values_other_than_plus_minus_one(self):
        for bad in (0, 2, -2):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Vote.objects.create(post=self.post, user=self.other, value=bad)
        c = Comment.objects.create(post=self.post, author=self.author, content="hola")
        with self.assertRaises(IntegrityError), transaction.atomic():
            CommentVote.objects.create(comment=c, user=self.other, value=5)

    def test_comment_has_no_parent_field(self):
        names = {f.name for f in Comment._meta.concrete_fields}
        self.assertEqual(
            names, {"id", "post", "author", "content", "created_at", "updated_at"}
        )


class VoteViewTests(Base):
    def test_vote_requires_login(self):
        r = self.client.post(self.vote_url(), {"value": 1})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("accounts:login"), r["Location"])
        self.assertEqual(Vote.objects.count(), 0)

    def test_vote_up_and_down_stored(self):
        self.login(self.other)
        self.client.post(self.vote_url(), {"value": 1})
        self.assertEqual(Vote.objects.get().value, 1)
        self.client.post(self.vote_url(), {"value": -1})
        self.assertEqual(Vote.objects.get().value, -1)

    def test_double_vote_same_value_does_not_duplicate_and_revokes(self):
        self.login(self.other)
        self.client.post(self.vote_url(), {"value": 1})
        self.client.post(self.vote_url(), {"value": 1})
        self.assertEqual(Vote.objects.count(), 0)
        self.client.post(self.vote_url(), {"value": 1})
        self.assertEqual(Vote.objects.count(), 1)

    def test_server_rejects_invalid_values(self):
        self.login(self.other)
        for bad in ("0", "2", "-2", "abc", "", "1.5"):
            self.client.post(self.vote_url(), {"value": bad})
        self.assertEqual(Vote.objects.count(), 0)

    def test_get_not_allowed(self):
        self.login(self.other)
        self.assertEqual(self.client.get(self.vote_url()).status_code, 405)

    def test_cannot_vote_on_draft(self):
        draft = make_post(self.author, "Borrador de prueba válido", status=Status.DRAFT)
        self.login(self.other)
        r = self.client.post(
            reverse("interactions:post_vote", args=[draft.public_id]), {"value": 1}
        )
        self.assertEqual(r.status_code, 404)

    def test_comment_vote_double_and_invalid(self):
        c = Comment.objects.create(post=self.post, author=self.author, content="hola")
        url = reverse("interactions:comment_vote", args=[c.pk])
        self.assertEqual(self.client.post(url, {"value": 1}).status_code, 302)
        self.assertEqual(CommentVote.objects.count(), 0)
        self.login(self.other)
        self.client.post(url, {"value": 3})
        self.assertEqual(CommentVote.objects.count(), 0)
        self.client.post(url, {"value": -1})
        self.client.post(url, {"value": -1})
        self.assertEqual(CommentVote.objects.count(), 0)
        self.client.post(url, {"value": 1})
        self.client.post(url, {"value": -1})
        self.assertEqual(CommentVote.objects.get().value, -1)


class CommentViewTests(Base):
    def test_comment_without_session_redirects_and_saves_nothing(self):
        r = self.client.post(self.comment_url(), {"content": "hola"})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("accounts:login"), r["Location"])
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_create(self):
        self.login(self.other)
        r = self.client.post(self.comment_url(), {"content": "Gracias por compartir"})
        self.assertEqual(r.status_code, 302)
        c = Comment.objects.get()
        self.assertEqual((c.author, c.post), (self.other, self.post))

    def test_csrf_enforced_on_comment_and_vote(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.other)
        self.assertEqual(client.post(self.comment_url(), {"content": "x"}).status_code, 403)
        self.assertEqual(client.post(self.vote_url(), {"value": 1}).status_code, 403)
        c = Comment.objects.create(post=self.post, author=self.other, content="hola")
        for name in ("comment_update", "comment_delete", "comment_vote"):
            r = client.post(reverse(f"interactions:{name}", args=[c.pk]), {"content": "x", "value": 1})
            self.assertEqual(r.status_code, 403, name)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Vote.objects.count() + CommentVote.objects.count(), 0)

    def test_length_limit_and_blank(self):
        self.login(self.other)
        r = self.client.post(self.comment_url(), {"content": "a" * (COMMENT_MAX_LENGTH + 1)})
        self.assertEqual(r.status_code, 400)
        r = self.client.post(self.comment_url(), {"content": "   "})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)
        ok = self.client.post(self.comment_url(), {"content": "a" * COMMENT_MAX_LENGTH})
        self.assertEqual(ok.status_code, 302)

    def test_comment_text_is_escaped(self):
        Comment.objects.create(
            post=self.post, author=self.author,
            content='<script>alert("x")</script><b>negrita</b>',
        )
        r = self.client.get(self.post.get_absolute_url())
        body = r.content.decode()
        self.assertNotIn("<script>alert", body)
        self.assertNotIn("<b>negrita</b>", body)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", body)

    def test_only_author_can_edit_and_delete(self):
        c = Comment.objects.create(post=self.post, author=self.author, content="mío")
        edit = reverse("interactions:comment_update", args=[c.pk])
        delete = reverse("interactions:comment_delete", args=[c.pk])
        # Anónimo
        self.assertEqual(self.client.post(edit, {"content": "x"}).status_code, 302)
        self.assertEqual(self.client.post(delete).status_code, 302)
        # Otra persona
        self.login(self.other)
        self.assertEqual(self.client.get(edit).status_code, 404)
        self.assertEqual(self.client.post(edit, {"content": "hack"}).status_code, 404)
        self.assertEqual(self.client.post(delete).status_code, 404)
        c.refresh_from_db()
        self.assertEqual(c.content, "mío")
        # Autoría
        self.login(self.author)
        self.assertEqual(self.client.post(edit, {"content": "editado"}).status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.content, "editado")
        self.assertEqual(self.client.post(delete).status_code, 302)
        self.assertFalse(Comment.objects.exists())

    def test_edit_delete_links_only_for_comment_author(self):
        c = Comment.objects.create(post=self.post, author=self.other, content="x")
        edit = reverse("interactions:comment_update", args=[c.pk])
        self.login(self.author)  # autor de la publicación, no del comentario
        self.assertNotContains(self.client.get(self.post.get_absolute_url()), edit)
        self.login(self.other)
        self.assertContains(self.client.get(self.post.get_absolute_url()), edit)

    def test_anonymous_sees_login_prompts_not_forms(self):
        r = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(r, self.comment_url())
        self.assertContains(r, "para comentar")


class RelevanceOrderTests(Base):
    def setUp(self):
        super().setUp()
        self.voters = [make_user(n) for n in range(10, 14)]
        self.now = timezone.now()

    def _post(self, title, age_days, votes):
        p = make_post(self.author, title)
        Post.objects.filter(pk=p.pk).update(created_at=self.now - timedelta(days=age_days))
        for voter, value in zip(self.voters, votes):
            Vote.objects.create(post=p, user=voter, value=value)
        return p

    def test_feed_relevance_order_is_deterministic(self):
        Post.objects.all().delete()
        a = self._post("Publicación con puntaje dos", 5, [1, 1])
        b = self._post("Publicación puntaje dos más nueva", 1, [1, 1, 1, -1])
        c = self._post("Publicación sin votos reciente", 0, [])
        d = self._post("Publicación puntaje negativo", 2, [-1])
        e = self._post("Publicación puntaje uno", 3, [1])
        expected = [b.pk, a.pk, e.pk, c.pk, d.pk]  # b y a empatan en 2: gana la más nueva
        for _ in range(3):
            r = self.client.get(reverse("posts:list"), {"orden": "relevancia"})
            self.assertEqual([p.pk for p in r.context["posts"]], expected)

    def test_feed_default_and_unknown_order_are_recent(self):
        Post.objects.all().delete()
        old = self._post("Publicación antigua con votos", 9, [1, 1, 1])
        new = self._post("Publicación nueva sin votos", 0, [])
        for params in ({}, {"orden": "reciente"}, {"orden": "basura"}):
            r = self.client.get(reverse("posts:list"), params)
            self.assertEqual([p.pk for p in r.context["posts"]], [new.pk, old.pk], params)

    def test_relevance_ties_break_by_id_when_same_timestamp(self):
        Post.objects.all().delete()
        p1, p2 = self._post("Publicación gemela uno", 1, []), self._post("Publicación gemela dos", 1, [])
        Post.objects.update(created_at=self.now)
        r = self.client.get(reverse("posts:list"), {"orden": "relevancia"})
        self.assertEqual([p.pk for p in r.context["posts"]], [p2.pk, p1.pk])

    def test_relevance_keeps_category_filter_and_excludes_drafts(self):
        Post.objects.all().delete()
        self._post("Publicación de vivencias A", 1, [1])
        make_post(self.author, "Publicación de ayudas B", category=Category.HELP)
        make_post(self.author, "Borrador oculto con votos", status=Status.DRAFT)
        r = self.client.get(reverse("posts:list"), {"orden": "relevancia", "categoria": "help"})
        self.assertEqual([p.title for p in r.context["posts"]], ["Publicación de ayudas B"])

    def test_comment_relevance_order(self):
        base = self.now
        def mk(text, age, votes):
            c = Comment.objects.create(post=self.post, author=self.author, content=text)
            Comment.objects.filter(pk=c.pk).update(created_at=base - timedelta(hours=age))
            for voter, value in zip(self.voters, votes):
                CommentVote.objects.create(comment=c, user=voter, value=value)
            return c
        a = mk("a", 5, [1, 1])
        b = mk("b", 1, [1, 1, 1, -1])
        c = mk("c", 0, [])
        d = mk("d", 2, [-1])
        got = list(Comment.objects.filter(post=self.post).by_relevance())
        self.assertEqual([x.pk for x in got], [b.pk, a.pk, c.pk, d.pk])
        self.assertEqual([x.score for x in got], [2, 2, 0, -1])
        r = self.client.get(self.post.get_absolute_url())
        html = r.content.decode()
        positions = [html.index(f'id="comentario-{x.pk}"') for x in (b, a, c, d)]
        self.assertEqual(positions, sorted(positions))

    def test_pagination_links_keep_order(self):
        Post.objects.all().delete()
        for i in range(16):
            make_post(self.author, f"Publicación numero {i:02d} de prueba")
        r = self.client.get(reverse("posts:list"), {"orden": "relevancia"})
        self.assertContains(r, "page=2&orden=relevancia")


class SeedInteractionsTests(TestCase):
    def run_seed(self, *args):
        call_command("seed_demo", *args, stdout=StringIO())

    def counts(self):
        return (Comment.objects.count(), Vote.objects.count(), CommentVote.objects.count())

    def test_seed_creates_visible_interactions_idempotently(self):
        self.run_seed()
        first = self.counts()
        self.assertTrue(all(n > 0 for n in first), first)
        self.run_seed()
        self.assertEqual(first, self.counts())
        self.assertFalse(Comment.objects.filter(post__status=Status.DRAFT).exists())
        self.assertFalse(Vote.objects.filter(post__status=Status.DRAFT).exists())

    def test_seed_is_deterministic(self):
        # pk 6 y 7 reservados: la siembra nunca los usa, así que el resultado
        # no depende de qué pk tome cada cuenta demo.
        for pk in (6, 7):
            User.objects.create_user(f"real{pk}@gmail.com", f"Real{pk}", "x", pk=pk)
        self.run_seed()
        snapshot = sorted(Vote.objects.values_list("post__title", "user__email", "value"))
        self.run_seed("--purge")
        self.assertEqual(self.counts(), (0, 0, 0))
        self.run_seed()
        self.assertEqual(
            snapshot,
            sorted(Vote.objects.values_list("post__title", "user__email", "value")),
        )

    def test_seed_never_touches_pk_6_7_and_purge_cascades(self):
        for pk in (6, 7):
            User.objects.create_user(f"demo.protegido{pk}@example.com", f"Prot{pk}", "x", pk=pk)
        real = User.objects.create_user("persona@gmail.com", "Persona", "x")
        self.run_seed()
        for model, field in ((Comment, "author"), (Vote, "user"), (CommentVote, "user")):
            self.assertFalse(model.objects.filter(**{f"{field}__pk__in": [6, 7]}).exists())
        self.run_seed("--purge")
        self.assertEqual(self.counts(), (0, 0, 0))
        self.assertEqual(set(User.objects.values_list("pk", flat=True)), {6, 7, real.pk})


class RlsMigrationTests(TestCase):
    def test_migration_enables_rls_for_every_new_table(self):
        from django.db.migrations.loader import MigrationLoader

        loader = MigrationLoader(None, ignore_no_migrations=True)
        ops = loader.disk_migrations[("interactions", "0001_initial")].operations
        sql = " ".join(s for op in ops if hasattr(op, "sql") for s in op.sql)
        for model in (Comment, Vote, CommentVote):
            self.assertIn(
                f"ALTER TABLE {model._meta.db_table} ENABLE ROW LEVEL SECURITY", sql
            )


class ReviewFollowUpTests(Base):
    """Correcciones VERITY/SENTINEL sobre 7a4f14f."""

    def test_cast_vote_integrity_error_rereads_and_applies(self):
        from unittest.mock import patch
        from django.db.models.query import QuerySet
        from apps.interactions.services import cast_vote

        Vote.objects.create(post=self.post, user=self.other, value=1)
        original_first = QuerySet.first
        forced = {"once": True}

        def first_none_once(self):
            if self.model is Vote and forced["once"]:
                forced["once"] = False
                return None
            return original_first(self)

        with (
            patch.object(QuerySet, "first", first_none_once),
            patch.object(Vote.objects, "create", side_effect=IntegrityError("duplicate")),
        ):
            # Misma valoración que la fila concurrente → revoca.
            result = cast_vote(Vote, "post", self.post, self.other, 1)
        self.assertIsNone(result)
        self.assertEqual(Vote.objects.count(), 0)

        Vote.objects.create(post=self.post, user=self.other, value=1)
        forced["once"] = True
        with (
            patch.object(QuerySet, "first", first_none_once),
            patch.object(Vote.objects, "create", side_effect=IntegrityError("duplicate")),
        ):
            result = cast_vote(Vote, "post", self.post, self.other, -1)
        self.assertEqual(result, -1)
        self.assertEqual(Vote.objects.get().value, -1)


    def test_invalid_comment_400_keeps_post_detail_context(self):
        self.login(self.other)
        r = self.client.post(self.comment_url(), {"content": "   "})
        self.assertEqual(r.status_code, 400)
        self.assertTemplateUsed(r, "posts/post_detail.html")
        self.assertEqual(r.context["post"], self.post)
        self.assertContains(r, self.post.title, status_code=400)
        self.assertContains(r, "comentarios", status_code=400)
        self.assertTrue(r.context["comment_form"].errors)

    def test_cannot_edit_or_delete_comment_on_draft_post(self):
        draft = make_post(self.author, "Borrador con comentario válido", status=Status.DRAFT)
        c = Comment.objects.create(post=draft, author=self.author, content="oculto")
        self.login(self.author)
        edit = reverse("interactions:comment_update", args=[c.pk])
        delete = reverse("interactions:comment_delete", args=[c.pk])
        self.assertEqual(self.client.get(edit).status_code, 404)
        self.assertEqual(self.client.post(edit, {"content": "no"}).status_code, 404)
        self.assertEqual(self.client.post(delete).status_code, 404)
        self.assertTrue(Comment.objects.filter(pk=c.pk).exists())

    def test_cannot_vote_own_post_or_comment(self):
        self.login(self.author)
        self.assertEqual(self.client.post(self.vote_url(), {"value": 1}).status_code, 302)
        self.assertEqual(Vote.objects.count(), 0)
        c = Comment.objects.create(post=self.post, author=self.author, content="mío")
        url = reverse("interactions:comment_vote", args=[c.pk])
        self.assertEqual(self.client.post(url, {"value": 1}).status_code, 302)
        self.assertEqual(CommentVote.objects.count(), 0)
        # Otra persona sí puede.
        self.login(self.other)
        self.client.post(self.vote_url(), {"value": 1})
        self.client.post(url, {"value": 1})
        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(CommentVote.objects.count(), 1)


