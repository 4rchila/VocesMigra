"""Pruebas de migraciones: existencia, dependencias y paridad con los modelos."""

from django.core.management import call_command
from django.db.migrations.loader import MigrationLoader
from django.test import SimpleTestCase, TestCase


class MigrationLoaderTests(SimpleTestCase):
    def test_accounts_has_initial_migration(self):
        loader = MigrationLoader(None, ignore_no_migrations=True)
        self.assertIn(("accounts", "0001_initial"), loader.disk_migrations)

    def test_initial_migration_depends_on_auth(self):
        loader = MigrationLoader(None, ignore_no_migrations=True)
        dependencies = loader.disk_migrations[("accounts", "0001_initial")].dependencies
        self.assertTrue(any(app_label == "auth" for app_label, _ in dependencies))

    def test_user_and_profile_are_created_by_the_initial_migration(self):
        loader = MigrationLoader(None, ignore_no_migrations=True)
        operations = loader.disk_migrations[("accounts", "0001_initial")].operations
        created = {
            operation.name
            for operation in operations
            if operation.__class__.__name__ == "CreateModel"
        }
        self.assertEqual(created, {"User", "Profile"})


class MigrationParityTests(TestCase):
    def test_no_pending_model_changes(self):
        try:
            call_command("makemigrations", "--check", "--dry-run", verbosity=0)
        except SystemExit:
            self.fail("Hay cambios de modelo sin su migración correspondiente.")
