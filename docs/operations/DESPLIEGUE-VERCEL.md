# Guía de despliegue en Vercel (Fase 1)

**Audiencia:** German, que despliega y administra VocesMigra.
**Versión de referencia:** rama `fase-1-seguridad` (`c48e90e` + parche `0004-0005-activacion-vercel.diff`), validada por SENTINEL y VERITY el 2026-10-19.
**Estado:** nada de esto se ha probado contra un despliegue real. Los puntos marcados **[verificar]** se confirman en el primer despliegue.

## 1. Arquitectura (decisión D5)

| Pieza | Servicio |
|---|---|
| App Django (funciones Python) | Vercel Hobby, uso no comercial |
| Base de datos PostgreSQL | Supabase |
| Correo SMTP | Brevo (`smtp-relay.brevo.com:587`, TLS obligatorio) |
| Dominio | `.tech` del GitHub Student Developer Pack (D7), gratis el primer año |

Vercel no tiene disco permanente ni procesos que queden encendidos. Por eso las migraciones corren en el build, y los archivos subidos tendrán que ir a Supabase Storage (eso es trabajo de la Fase 2, todavía no está hecho).

## 2. Requisitos previos

- Cuenta de Vercel conectada al repositorio de GitHub.
- Proyecto de Supabase con los datos de conexión a PostgreSQL.
- Cuenta de Brevo con una clave SMTP.
- Dominio `.tech` activado, con 2FA en la cuenta del registrador.
- La Fase 1 subida a GitHub (el push lo apruebas tú).

## 3. Archivos que usa Vercel

- `pyproject.toml`: dice que la app arranca en `config.wsgi:application` y que el build es `python scripts/vercel_build.py`.
- `scripts/vercel_build.py`: corre `migrate` y `createcachetable`, pero solo cuando `VERCEL_ENV=production`. En las vistas previas no toca la base.
- `vercel.json`: limita cada petición a 30 segundos y deja fuera del paquete las pruebas, `docs/` y `db.sqlite3`.

## 4. Variables de entorno

Configúralas en Vercel, dentro de *Settings → Environment Variables* del proyecto. **Los secretos nunca van al repo.**

> **Importante (SENTINEL):** marca las variables de base de datos y de correo **solo para Production**. Si quedan disponibles para Preview, cada vista previa de una rama usaría la base real y podría mandar correos reales.

| Variable | Entorno | Valor |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Production | `config.settings.production` **[verificar** dónde lo toma la app en Vercel**]** |
| `DJANGO_SECRET_KEY` | **Solo Production** | Clave larga y aleatoria. Si una vista previa necesita una, usa otra distinta (SENTINEL) |
| `DJANGO_ALLOWED_HOSTS` | Production | `tu-dominio.tech` y el dominio `.vercel.app` del proyecto |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Production | `https://tu-dominio.tech` (solo acepta `https://`) |
| `DJANGO_ADMIN_URL` | Production | Ruta secreta del admin; no puede ser `admin` |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | **Solo Production** | Datos de Supabase |
| `POSTGRES_SSLMODE` | Production | `require` |
| `EMAIL_HOST` | Production | `smtp-relay.brevo.com` |
| `EMAIL_PORT` | Production | `587` |
| `EMAIL_USER`, `EMAIL_PASSWORD` | **Solo Production** | Credenciales SMTP de Brevo |
| `DEFAULT_FROM_EMAIL` | Production | Remitente del dominio `.tech` |

`CLIENT_IP_HEADER` y `TRUSTED_PROXY_COUNT` ya tienen valores por defecto para Vercel en `production.py` (`HTTP_X_VERCEL_FORWARDED_FOR` y `1`). No hace falta definirlas.

> La app no usa `DATABASE_URL`. Lee las cinco variables `POSTGRES_*` (`config/settings/base.py`, líneas 52 a 61).

## 5. Proteger las vistas previas

En la configuración de *Deployment Protection* del proyecto, activa la protección para que las vistas previas no queden públicas.

## 6. Primer despliegue

1. Aprueba el push de la Fase 1 y sube la rama a GitHub.
2. En Vercel (plan Hobby), crea un proyecto nuevo con *Add New → Project* e importa el repositorio `4rchila/VocesMigra`. Configura las variables del paso 4 antes de desplegar.
3. Despliega a Production.
4. En el registro del build, comprueba que `vercel_build` corrió las migraciones y `createcachetable`.
5. Crea el superusuario y el primer acceso al admin desde tu PC, apuntando a Supabase (ver el README: `createsuperuser` y `addstatictoken`). Después entra a la ruta de `DJANGO_ADMIN_URL` y registra tu dispositivo TOTP.

### Resultado esperado
- `https://tu-dominio.tech/health/` responde 200.
- `/admin/` responde 404, y la ruta secreta pide contraseña y código TOTP.
- El registro manda el correo de activación por Brevo.

## 7. Verificaciones del primer despliegue [verificar]

Estas no se pudieron probar sin un despliegue real (FORGE y VERITY):
- Que las migraciones y `createcachetable` corran durante el build.
- Que `collectstatic` automático de Vercel funcione y que se carguen los estilos.
- Que la IP real llegue en `X-Vercel-Forwarded-For`. Prueba con 6 intentos fallidos de login: el sexto debe responder 429.

## 8. Dominio y correo

1. Agrega el dominio `.tech` al proyecto en Vercel y crea los registros DNS que te indique.
2. En Brevo, autentica el dominio con **SPF** y **DKIM**.
3. Agrega un registro **DMARC** con `p=quarantine`.
4. Anota la fecha de vencimiento del dominio y pásasela a MALENIA para el aviso de renovación.
5. **No actives HSTS preload** ni `includeSubDomains` mientras el dominio no sea definitivo.

## 9. Tareas periódicas (diaria, a mano)

`purge_unactivated_accounts` borra las cuentas sin activar cuyo enlace ya caducó. En la Fase 1 queda como paso manual. El cron diario con `CRON_SECRET` se deja para la Fase 2 (decisión de ARCHITECT). Córrelo una vez al día, a mano, desde tu PC, con las variables `POSTGRES_*` de producción y `DJANGO_SETTINGS_MODULE=config.settings.production`, apuntando a Supabase:

```bash
python manage.py purge_unactivated_accounts --dry-run   # muestra cuántas borraría
python manage.py purge_unactivated_accounts
```

## 10. Problemas comunes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El login da error 500 | Falta la tabla de caché | Corre `python manage.py createcachetable` contra Supabase |
| `ImproperlyConfigured` al arrancar | Falta una variable obligatoria o un origen CSRF no es `https://` | Revisa la tabla del paso 4 |
| Error 400 Bad Request | El dominio no está en `DJANGO_ALLOWED_HOSTS` | Agrégalo |
| Una vista previa falla al conectar a la base | Es lo esperado si las variables de base son solo de Production | No es un error |
| Todos los usuarios reciben 429 | La cabecera de IP no llega como se espera | Revisa `CLIENT_IP_HEADER` y avísale a SENTINEL |

## Discrepancias abiertas

- `README.md` todavía dice que producción usa **Render Free**. Hay que actualizarlo a Vercel. Está en la rama de FORGE y no lo edité.
- Hay dos versiones sobre los estáticos: el comentario de `production.py` dice que los sirve el CDN de Vercel, mientras que el resumen de FORGE dice que WhiteNoise los sirve fuera del CDN. Se confirma en el primer despliegue.
- Las imágenes siguen en `FileSystemStorage`. Hay que conectar Supabase Storage antes de la Fase 2.
