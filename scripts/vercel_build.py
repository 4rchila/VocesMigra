"""Paso de build en Vercel: migraciones y tabla de caché.

En Vercel no hay un servidor encendido donde correr comandos, así que se
ejecutan aquí, después de instalar dependencias. Solo en el entorno de
producción (VERCEL_ENV=production): las vistas previas de cada rama no deben
migrar la base real. collectstatic lo corre Vercel por su cuenta.
"""

import os
import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    if os.environ.get("VERCEL_ENV") != "production":
        print("vercel_build: entorno no productivo, se omiten migraciones.")
        return
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False)
    call_command("createcachetable")


if __name__ == "__main__":
    main()
