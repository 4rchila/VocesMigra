# Exportación y restauración: Supabase Free

## Alcance y límites

Este procedimiento es para la futura base PostgreSQL del piloto; no crea un proyecto ni conecta datos. El plan Free no ofrece backups descargables automáticos diarios. La documentación de Supabase recomienda exportar regularmente y mantener copias fuera del proyecto. Una exportación lógica contiene datos personales y debe tratarse como un secreto operativo.

La copia cubre PostgreSQL. No respalda archivos externos ni objetos de Storage; este proyecto no debe habilitar Storage para el piloto sin definir primero una estrategia independiente.

## Preparación cuando exista el proyecto

1. Instala una versión compatible de Supabase CLI, Docker y PostgreSQL client tools (`psql`). La orden `supabase db dump` usa Docker.
2. Obtén la cadena de conexión desde el panel del proyecto. No la pegues en Git, issues, tickets, informes ni historial del shell. Cárgala desde un gestor de secretos en la variable `SUPABASE_DB_URL`; desactiva `set -x` y no imprimas el entorno. `--db-url`/`--dbname` reciben la URL como argumento de proceso: opera desde un host confiable y no compartido, no desde un runner multiusuario.
3. Elige la red según el host que ejecuta el comando:
   - Con IPv6, prefiere la conexión directa para operaciones de mantenimiento y `pg_dump`.
   - En una red solo IPv4 y sin el add-on IPv4, usa Supavisor Session Pooler por el puerto de sesión `5432`. No uses el Transaction Pooler para una aplicación Django persistente sin validar primero sus restricciones.
   - La conexión directa de Free requiere IPv6; el Session Pooler compartido está disponible por IPv4. Revisa el endpoint y usuario vigentes en el panel, no copies valores de ejemplos.
4. Guarda las exportaciones fuera del repositorio, con permisos privados y cifrado antes de copiarlas fuera del equipo. El directorio `backups/` está ignorado por Git como segunda barrera, no como control de acceso.

## Exportación lógica

Ejecuta desde un directorio del proyecto solo cuando ya exista el proyecto y se haya aprobado la operación. Los valores se cargan desde el entorno; no reemplaces la variable con una URL literal en el comando:

```bash
set -euo pipefail
set +x
: "${SUPABASE_DB_URL:?Carga la URL desde el gestor de secretos}"
umask 077
backup_dir="${XDG_STATE_HOME:-$HOME/.local/state}/voces-migra/backups/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$backup_dir"

supabase db dump --db-url "$SUPABASE_DB_URL" -f "$backup_dir/roles.sql" --role-only
supabase db dump --db-url "$SUPABASE_DB_URL" -f "$backup_dir/schema.sql"
supabase db dump --db-url "$SUPABASE_DB_URL" -f "$backup_dir/data.sql" --use-copy --data-only -x "storage.buckets_vectors" -x "storage.vector_indexes"

sha256sum "$backup_dir/roles.sql" "$backup_dir/schema.sql" "$backup_dir/data.sql" > "$backup_dir/SHA256SUMS"
```

Comprueba que los tres archivos existen y no están vacíos. Conserva el checksum con la copia cifrada. No subas ni los `.sql` ni los checksums a GitHub. La copia debe ir a almacenamiento privado fuera del proyecto, cifrada, con retención definida y acceso limitado. En Free no existe una copia automática de plataforma que sustituya este procedimiento.

Cadencia inicial propuesta para un piloto con datos reales: exportación antes de cada migración y al menos diaria mientras haya actividad; acordar antes de abrir el servicio el RPO/RTO y retención. La automatización del backup no se configura en este cambio.

## Restauración ensayada

Restaura primero en un proyecto de recuperación vacío, nunca encima de la base activa como prueba. La restauración es destructiva para el destino; confirma proyecto, endpoint y base antes de ejecutarla. Usa la conexión del destino en `TARGET_DB_URL`, cargada de la misma forma protegida que la conexión de origen.

```bash
set -euo pipefail
set +x
: "${TARGET_DB_URL:?Carga la conexión del destino desde el gestor de secretos}"

psql \
  --single-transaction \
  --variable ON_ERROR_STOP=1 \
  --file "$backup_dir/roles.sql" \
  --file "$backup_dir/schema.sql" \
  --command 'SET session_replication_role = replica' \
  --file "$backup_dir/data.sql" \
  --dbname "$TARGET_DB_URL"
```

Después:

1. Comprueba `python manage.py showmigrations` y `python manage.py migrate --check` con `DJANGO_SETTINGS_MODULE=config.settings.production` apuntando al destino de recuperación.
2. Comprueba desde Django, sin consultar datos en una interfaz pública, que funcionan login, sesión, lectura de publicaciones y permisos. Usa una cuenta sintética autorizada para el ensayo; nunca copies registros personales a un entorno de prueba no aprobado.
3. Revisa errores de restauración y conteos esperados usando consultas agregadas, sin imprimir correos, contraseñas hash, contenido ni datos personales.
4. Registra duración, errores y versión de PostgreSQL/CLI; elimina la conexión temporal y protege o elimina el proyecto de ensayo según la política aprobada.

Si se incorporan Supabase Vault, cifrado de columnas, Storage u otros servicios, este procedimiento deja de ser suficiente: sus claves/objetos requieren una estrategia adicional documentada antes de utilizarlos.

## Referencias oficiales

- [Backups de Supabase](https://supabase.com/docs/guides/platform/backups)
- [Backup y restore con Supabase CLI](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore)
- [Conectar a PostgreSQL](https://supabase.com/docs/guides/database/connecting-to-postgres)
