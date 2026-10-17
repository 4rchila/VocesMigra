# Voces Migra

Comunidad en línea donde personas migrantes comparten vivencias, problemas, consultas y ayudas, con foco en privacidad y moderación.

Monolito Django 5.2 con plantillas renderizadas en servidor, SQLite en desarrollo y PostgreSQL (Supabase) en producción.

## Requisitos

- Python 3.13
- PostgreSQL 15+ solo para producción

## Instalación local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # rellena con valores locales y sintéticos
export DJANGO_SETTINGS_MODULE=config.settings.development
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
python manage.py migrate
python manage.py runserver
```

Las variables se leen del entorno del proceso; `.env` no se carga solo.

## Pruebas

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test tests apps.accounts.tests
```

La CI de GitHub Actions corre la suite, comprueba migraciones pendientes y ejecuta `check --deploy` con valores sintéticos en cada push y pull request a `main`.

## Despliegue

Producción usa `config.settings.production`, que exige `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` y las variables `POSTGRES_*`, y activa HTTPS, cookies seguras y HSTS. El procedimiento del piloto y los respaldos están en `docs/plan/PILOTO-PRODUCCION.md` y `docs/operations/`. El host definitivo está pendiente de decisión (ver `docs/plan/PLAN-OFICIAL.md`).

## Estructura

- `apps/` contiene `core`, `accounts` y `posts`.
- `config/` contiene los settings por entorno (`base`, `development`, `test`, `production`).
- `templates/` y `static/` contienen la interfaz.
- `tests/` contiene las pruebas de backend, publicaciones e interfaz.
- `docs/` contiene producto, privacidad, arquitectura, plan y operación.

## Licencia

MIT, ver `LICENSE`.
