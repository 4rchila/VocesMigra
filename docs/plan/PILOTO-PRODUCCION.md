# Plan de preparación para un piloto temporal

## Estado y decisión de infraestructura

Este documento es un plan, no una orden de despliegue. No crea Supabase, no conecta datos, no despliega Django y no configura un pipeline de despliegue.

La única infraestructura de base de datos aprobada para el piloto es Supabase Free como PostgreSQL. Django seguirá siendo dueño de la autenticación, sesiones, grupos y permisos mediante `accounts.User` y sus migraciones. No usar Supabase Auth, sus clientes de autenticación ni el Data API para las tablas Django; mantener el Data API deshabilitado. El servidor Django se conectará a PostgreSQL desde el backend, nunca desde el navegador. No asumir RLS como sustituto de los permisos de Django.

## Lectura del estado actual del repositorio

- Django 5.2.17 es un monolito WSGI con plantillas server-rendered. `development.py` y `test.py` conservan SQLite; `production.py` ya exige clave, hosts y PostgreSQL por variables de entorno.
- El helper PostgreSQL usa `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` y `POSTGRES_PORT`; con este cambio añade psycopg 3 y TLS (`POSTGRES_SSLMODE`, por defecto `require`). No contiene ni necesita una URL real de Supabase.
- `STATIC_ROOT` ya apunta a `staticfiles/`, pero no hay integración de `collectstatic` ni backend de almacenamiento estático. El host futuro deberá servir esos archivos explícitamente.
- Producción ya establece `DEBUG=False`, redirección HTTPS, cookies seguras, HSTS, `X-Content-Type-Options` y `X-Frame-Options`. Aún se debe decidir el proxy TLS y configurar `SECURE_PROXY_SSL_HEADER` solo para el proxy de confianza, además de `CSRF_TRUSTED_ORIGINS` para el dominio final.
- SMTP se configura por entorno (`EMAIL_HOST`, `EMAIL_PORT`, usuario, contraseña y TLS), pero no hay proveedor elegido ni comprobación de entregabilidad.
- El endpoint `/health/` responde `{"status":"ok"}` sin comprobar PostgreSQL. Sirve como liveness básico, no como readiness de dependencias.
- En `main` existen cuentas/perfiles y publicaciones. No existen modelos/endpoints de comentarios o reportes ni moderación operativa; `apps/posts/admin.py` solo ofrece administración básica de publicaciones. La especificación de privacidad describe controles previstos, no funcionalidades ya implementadas.
- No hay carga de imágenes implementada ni `MEDIA_ROOT` configurado. No aceptar archivos reales en el piloto hasta aprobar almacenamiento privado/público, validación, reencodificación y eliminación de EXIF.

## Fases y gates

### 1. Cerrar alcance y operación

- Aprobar dominio, alojamiento de Django, duración del piloto, responsables, canal de contacto, política comunitaria, moderación, apelaciones y criterios de cierre/eliminación.
- Definir RPO/RTO, frecuencia de exportación, retención, cifrado y destino privado de backups según `docs/operations/SUPABASE-FREE-BACKUP-RESTORE.md`.
- Mantener solo datos sintéticos mientras se configura el entorno. No cargar datos de usuarios en previews o pruebas.

### 2. Preparar Supabase Free, sin Data API

Cuando se autorice crear el proyecto, usarlo exclusivamente para PostgreSQL. No habilitar Supabase Auth ni Data API para acceder a tablas Django. Revisar en el panel qué extensiones y roles están disponibles y usar una cuenta de base de datos con privilegios mínimos compatibles con migraciones y runtime.

Elegir conexión solo después de conocer el alojamiento:

- Host Django con IPv6: conexión directa PostgreSQL de Supabase, puerto 5432.
- Host solo IPv4 sin add-on IPv4: Supavisor Session Pooler, puerto de sesión 5432; es el modo compatible con procesos Django persistentes en IPv4.
- No elegir el Transaction Pooler para este servidor WSGI persistente sin una prueba específica. No contratar add-ons ni crear el proyecto en esta etapa.

Cargar los valores `POSTGRES_*` mediante el gestor de secretos del host. No pegar URLs/contraseñas en GitHub, documentación, logs ni comandos registrados. Mantener `sslmode=require` como mínimo; mejorar a `verify-full` cuando se configure y pruebe la CA correspondiente.

### 3. Endurecer settings para el proveedor de Django

Antes del piloto, revisar y probar con el host real:

- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` exacto y `CSRF_TRUSTED_ORIGINS` limitado al HTTPS elegido.
- Terminación TLS y proxy confiable; configurar `SECURE_PROXY_SSL_HEADER` solo si el host garantiza y elimina/reemplaza la cabecera entrante. Validar que no haya bucles de redirección.
- Revisar HSTS (actualmente un año, subdominios y preload) solo después de confirmar dominio y HTTPS permanente.
- `python manage.py check --deploy` en el entorno de configuración de producción. No imprimir settings ni entorno, porque contienen secretos.
- Registro de errores sin contraseñas, tokens, correos de recuperación ni cuerpos completos; acceso y retención limitados.

### 4. Estáticos y correo

- Ejecutar `python manage.py collectstatic --noinput` en el proceso de publicación manual y comprobar que el host sirve `STATIC_ROOT`. Elegir entre estáticos integrados al host, proxy/CDN o un backend explícito; hoy no hay WhiteNoise ni almacenamiento externo configurado.
- Elegir un SMTP transaccional, cargar credenciales solo como secretos, usar TLS y validar dominio remitente (SPF/DKIM/DMARC), rebotes y límites. Probar recuperación de acceso sin enumeración con una cuenta sintética. El correo de desarrollo seguirá en consola.
- No activar uploads de usuario hasta decidir dónde viven los medios y cómo se protegen y borran.

### 5. Moderación y privacidad antes de datos reales

La moderación de reportes está en el roadmap, no implementada en `main`. Antes de abrir a participantes reales se requieren, como mínimo:

- flujo de reporte para publicación y comentario, motivos, estado y deduplicación;
- grupo de moderación con mínimo privilegio, cola de pendientes y acciones trazables (actor, fecha, motivo y resolución);
- reglas comunitarias, tiempos de respuesta, apelación, retención y canal de contacto aprobados;
- pruebas de autorización para reportar, ocultar, revisar y resolver; ausencia de borrado automático por un reporte;
- datos sintéticos para ensayar abuso, escalamiento y errores, sin reutilizar experiencias reales.

Los cambios sin integrar del Run de comentarios no forman parte de `main` ni de este plan operativo; este documento no los integra ni altera.

### 6. Ensayo de despliegue temporal (manual, no CI/CD)

Realizar una única prueba en un entorno efímero aislado con cuentas y contenido sintéticos:

1. Crear snapshot/backup del destino antes de la primera migración.
2. Instalar dependencias desde `requirements.txt`; comprobar `python manage.py check --deploy`.
3. Ejecutar `python manage.py makemigrations --check --dry-run`, revisar el plan de migraciones y ejecutar `python manage.py migrate` manualmente.
4. Ejecutar `python manage.py collectstatic --noinput` y comprobar CSS, errores 404 y permisos de archivos.
5. Validar HTTPS, hosts, cookies, CSRF, registro, login, logout, recuperación SMTP, permisos de publicaciones y Admin.
6. Validar `/health/` como liveness y hacer una comprobación de readiness PostgreSQL controlada por el host sin exponer detalles. El endpoint actual no comprueba DB.
7. Ejecutar exportación y restauración en un destino vacío siguiendo el procedimiento de backup; comprobar el retorno a un flujo funcional.
8. Revisar logs y borrar el entorno sintético conforme a la política.

No publicar un pipeline de deploy automático. El workflow de GitHub ejecuta únicamente pruebas. El paso a un piloto con personas reales requiere una aprobación separada tras revisar seguridad, moderación, backups restaurados y limitaciones del plan Free.

## Referencias de producto y proveedor

- Decisiones funcionales y fases: `docs/plan/MVP-ROADMAP.md`, `docs/product/PRODUCT.md`, `docs/product/SAFETY-PRIVACY.md`.
- Configuración real: `config/settings/base.py`, `development.py`, `test.py`, `production.py`.
- Supabase: [conexiones PostgreSQL](https://supabase.com/docs/guides/database/connecting-to-postgres), [pooling y límites](https://supabase.com/docs/guides/database/connecting-to-postgres/pooling-and-limits), [desactivar Data API](https://supabase.com/docs/guides/api/securing-your-api), [backups](https://supabase.com/docs/guides/platform/backups).
