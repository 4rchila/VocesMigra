"""Borra cuentas que nunca se activaron y cuyo enlace ya caducó.

Libera el correo y el alias si alguien registró el correo de otra persona.
Solo toca cuentas inactivas que nunca iniciaron sesión, para no borrar
cuentas desactivadas a propósito por moderación. Pensado para un cron diario.
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Elimina cuentas sin activar con el enlace de activación caducado."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, dry_run=False, **options):
        cutoff = timezone.now() - timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
        stale = User.objects.filter(
            is_active=False, last_login__isnull=True, date_joined__lt=cutoff
        )
        count = stale.count()
        if not dry_run:
            stale.delete()
        self.stdout.write(f"{'Se borrarían' if dry_run else 'Borradas'}: {count}")
