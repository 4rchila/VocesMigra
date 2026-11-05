from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import Profile, User
from apps.posts.models import Post


def run(*args):
    call_command("seed_demo", *args, stdout=StringIO())


class SeedDemoTests(TestCase):
    def test_idempotent(self):
        run()
        counts = (User.objects.count(), Profile.objects.count(), Post.objects.count())
        self.assertEqual(counts[0], 36)
        self.assertGreaterEqual(counts[2], 100)
        run()
        self.assertEqual(
            counts, (User.objects.count(), Profile.objects.count(), Post.objects.count())
        )

    def test_dry_run_writes_nothing(self):
        run("--dry-run")
        self.assertEqual(User.objects.count(), 0)

    def test_users_valid(self):
        run()
        for u in User.objects.filter(email__startswith="demo."):
            self.assertFalse(u.has_usable_password())
            u.profile.full_clean()
            u.full_clean(exclude=["password"])
        for p in Post.objects.all():
            p.full_clean()

    def test_purge_only_demo_and_never_6_7(self):
        for pk, email in ((6, "demo.protegido@example.com"), (7, "real@example.com")):
            User.objects.create_user(email, f"Prot{pk}", "x", pk=pk)
        real = User.objects.create_user("persona@gmail.com", "Persona", "x")
        run()
        run("--purge")
        self.assertEqual(
            set(User.objects.values_list("pk", flat=True)), {6, 7, real.pk}
        )
        self.assertEqual(User.objects.get(pk=6).email, "demo.protegido@example.com")

    def test_seed_does_not_modify_pk_6_7(self):
        for pk in (6, 7):
            User.objects.create_user(f"u{pk}@example.com", f"Cuenta{pk}", "x", pk=pk)
        before = list(User.objects.filter(pk__in=[6, 7]).values())
        run()
        self.assertEqual(before, list(User.objects.filter(pk__in=[6, 7]).values()))
        self.assertFalse(Profile.objects.filter(user_id__in=[6, 7]).exists())
