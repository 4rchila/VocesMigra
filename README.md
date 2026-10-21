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

La CI de GitHub Actions corre la suite, comprueba migraciones pendientes y ejecuta `check --deploy` con valores sintéticos en cada push y pull request a `main` y en cada push a ramas `fase-*`. También ejecuta `scripts/check_host_refs.py`, que falla si se nombra el host viejo fuera de D5.

## Despliegue

Producción usa `config.settings.production` en Vercel Hobby (guía en `docs/operations/DESPLIEGUE-VERCEL.md`), con PostgreSQL de Supabase y correo de Brevo (decisión D5 en `docs/plan/PLAN-OFICIAL.md`). Exige `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_ADMIN_URL` y las variables `POSTGRES_*`, y activa HTTPS, cookies seguras, HSTS, CSP y Referrer-Policy. Tras migrar hay que crear la tabla de caché que usa el límite de intentos:

```bash
python manage.py migrate
python manage.py createcachetable
```

Correo: por defecto SMTP en el puerto 587 con STARTTLS (Brevo: `smtp-relay.brevo.com`). Base de datos: `POSTGRES_SSLMODE=require` cifra la conexión; `verify-full` además comprueba el certificado del servidor y es lo recomendable cuando se descargue el certificado raíz de Supabase (`PGSSLROOTCERT`).

### Administración con 2FA

El panel vive en la ruta de `DJANGO_ADMIN_URL` (`/admin/` da 404) y exige contraseña más un código TOTP. Primer acceso:

```bash
python manage.py createsuperuser
python manage.py addstatictoken <correo-del-superusuario>   # código de un solo uso
```

Entra al panel con la contraseña y ese código, crea un dispositivo en "TOTP devices", escanea el QR con tu app de autenticación y desde entonces usa sus códigos. El procedimiento del piloto y los respaldos están en `docs/plan/PILOTO-PRODUCCION.md` y `docs/operations/`.

## Estructura

- `apps/` contiene `core`, `accounts` y `posts`.
- `config/` contiene los settings por entorno (`base`, `development`, `test`, `production`).
- `templates/` y `static/` contienen la interfaz.
- `tests/` contiene las pruebas de backend, publicaciones e interfaz.
- `docs/` contiene producto, privacidad, arquitectura, plan y operación.

## Licencia

MIT, ver `LICENSE`.
