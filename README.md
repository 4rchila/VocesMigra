# Voces Migra

Comunidad en línea donde personas migrantes comparten vivencias, problemas, consultas y ayudas, con foco en privacidad y moderación.

Monolito Django 5.2 con plantillas renderizadas en servidor, SQLite en desarrollo y PostgreSQL (Supabase) en producción.

## Estado actual

| Componente | Estado |
|---|---|
| Aplicación | Django 5.2 desplegado en Vercel Hobby: <https://vocesmigra.vercel.app> |
| Base de datos | PostgreSQL de Supabase (conexión con `POSTGRES_SSLMODE`) |
| Row Level Security (RLS) en Supabase | Activo en las 16 tablas del esquema `public`, sin políticas y sin `FORCE`. Las 16 tablas previas se activaron directamente en Supabase; las tablas de `interactions` lo activan en su propia migración (`interactions/0001_initial`, solo PostgreSQL). Bloquea el acceso por la API pública de Supabase; Django no se ve afectado porque se conecta con el rol `postgres`, que tiene `BYPASSRLS`. El aviso `rls_disabled_in_public` del advisor quedó resuelto |
| Correo | SMTP de Brevo (registro y activación de cuentas) |
| Administración | Ruta secreta configurable con `DJANGO_ADMIN_URL` (`/admin/` da 404) y 2FA TOTP con `django-otp` |
| Dominio | Solo `vocesmigra.vercel.app`; se descartó el dominio `.tech` (D7) |

Documentación del proyecto: [PLAN-OFICIAL.md](docs/plan/PLAN-OFICIAL.md), [CIERRE-FASE-1.md](docs/plan/CIERRE-FASE-1.md) y [DESPLIEGUE-VERCEL.md](docs/operations/DESPLIEGUE-VERCEL.md).

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

Las variables se leen del entorno del proceso; `.env` no se carga solo. Cárgalo antes de arrancar, por ejemplo con `set -a; source .env; set +a`.

Resultado esperado: `runserver` muestra `Starting development server at http://127.0.0.1:8000/` y la portada abre en el navegador. En desarrollo el correo sale por la consola.

Errores comunes:

- `ImproperlyConfigured` por `DJANGO_SECRET_KEY`: la variable no está exportada en esa terminal.
- `DJANGO_ADMIN_URL no puede estar vacía ni ser 'admin'`: elige otra ruta.
- `ModuleNotFoundError: No module named 'django'`: el entorno virtual no está activado.

## Variables de entorno

Solo nombres; los valores nunca se versionan. La plantilla es `.env.example`.

| Variable | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | Clave criptográfica de Django |
| `DJANGO_DEBUG` | Modo depuración (solo local) |
| `DJANGO_ALLOWED_HOSTS` | Hosts aceptados, separados por comas |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes `https://` que envían formularios (producción) |
| `DJANGO_ADMIN_URL` | Ruta del panel de administración; obligatoria en producción |
| `TRUSTED_PROXY_COUNT` | Proxies delante de la app (0 local, 1 en producción) |
| `CLIENT_IP_HEADER` | Cabecera con la IP real del cliente que pone el proveedor |
| `SQLITE_PATH` | Ruta de SQLite en desarrollo |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_SSLMODE` | Conexión a PostgreSQL (Supabase) |
| `DJANGO_EMAIL_BACKEND` | Backend de correo |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD`, `EMAIL_USE_TLS` | Servidor SMTP (Brevo) |
| `DEFAULT_FROM_EMAIL` | Remitente de los correos |

## Datos de demostración

```bash
python manage.py seed_demo
```

En preparación: el comando lo está desarrollando el equipo y todavía no existe en esta versión del código. Esta sección se completará con lo que cree y cómo limpiarlo cuando se integre.

## Pruebas

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test tests apps.accounts.tests
```

Usa SQLite en memoria y no necesita variables. Resultado esperado: `Ran 236 tests` y `OK` (comprobado el 4 nov 2026 sobre el commit `2bb1989`).

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

## Metodología de desarrollo

El proyecto se desarrolló con un sistema agéntico. En una primera etapa, el trabajo se orquestó con HERMES y agentes como Codex y OpenCode. Después se finalizó con Grok Bot, un equipo de agentes coordinado por ARCHITECT: FORGE en desarrollo, VERITY en QA, SENTINEL en seguridad y SCRIBE en documentación.

## Licencia

MIT, ver `LICENSE`.
