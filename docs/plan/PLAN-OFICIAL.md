# Plan oficial de desarrollo: Voces Migra

Objetivo: llevar la base del MVP a una aplicación desplegada, segura y presentable en la universidad.

## Roles

- **German**: decide producto, aprueba cada fase, hace o autoriza commits y push.
- **ARCHITECT**: coordina el proyecto, asigna tareas y consolida resultados (jefe de Workers).
- **SHOGUN**: coordinador general del equipo; recibe resúmenes.
- **FORGE**: implementa código, pruebas y documentación técnica.
- **VERITY**: revisa cada entrega contra sus criterios (cumple, cumple con observaciones o no cumple).
- **SENTINEL**: audita seguridad y privacidad en las tareas marcadas.

## Flujo por tarea

1. ARCHITECT asigna la tarea con criterios.
2. FORGE trabaja en una rama por tarea o fase (p. ej. `fase-1-seguridad`) y entrega con la suite verde y la CI verde.
3. VERITY revisa y, cuando la tarea lo indica, SENTINEL audita.
4. German aprueba y se integra a `main` por pull request. Nadie hace push sin el OK de German.

## Decisiones de German (13 oct 2026)

| # | Decisión | Resultado |
| --- | --- | --- |
| D1 | Categorías | Se mantienen las cinco de `PRODUCT.md`; no se agrega "consultas" |
| D2 | Imágenes | Máximo 5 MB, redimensionadas a 1600 px por lado como máximo y guardadas en WebP sin metadatos |
| D3 | Comentarios previos | No existen; se implementan desde cero en la Fase 2 |
| D4 | Bloqueantes de seguridad | Van en la Fase 1, antes de la moderación |
| D5 | Hosting y correo | Confirmada (19 oct 2026, decisión de German): Vercel Hobby (app), Supabase Free (PostgreSQL y Storage de imágenes), Brevo Free (SMTP) |
| D7 | Dominio | `.tech` gratis 1 año del GitHub Student Developer Pack (confirmada 17 oct 2026); la renovación se paga |
| D6 | Licencia | MIT |

## Fase 0: base oficial (hecha, en revisión)

- [FORGE] Traslado del MVP sin la capa de agentes, con README, LICENSE, `.gitignore` y CI.
- [VERITY] Revisión del traslado. [SENTINEL] Auditoría del árbol y la CI.
- Criterios: 226 pruebas pasan (verificado el 21 oct 2026), `check --deploy` sin avisos con valores sintéticos, sin migraciones pendientes, ningún secreto ni dato real en el árbol.

## Fase 1: seguridad base y operación

Estado (19 oct 2026): implementada en la rama `fase-1-seguridad` y revisada: SENTINEL aprueba con observaciones (1.1–1.3, 1.5–1.7) y VERITY dictamina «cumple con observaciones» (ver [CIERRE-FASE-1.md](CIERRE-FASE-1.md)). Las tareas 1.5–1.8 van en un commit aparte.

| Tarea | Responsable | Revisión | Criterio verificable |
| --- | --- | --- | --- |
| 1.1 Límite de intentos en login y registro | FORGE | SENTINEL | Prueba: el intento N+1 en la ventana devuelve bloqueo; el éxito no revela si la cuenta existe |
| 1.2 Registro sin enumeración de correos | FORGE | SENTINEL | Prueba: misma respuesta y mismo código para correo nuevo y existente; el aviso llega solo al dueño |
| 1.3 Admin en ruta configurable con 2FA (`django-otp`) | FORGE | SENTINEL | `/admin/` devuelve 404; sin OTP no se entra al panel |
| 1.4 `/health/` con comprobación de base de datos | FORGE | VERITY | Prueba: devuelve 503 si la base falla |
| 1.5 Cabeceras CSP, Referrer-Policy, `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER` | FORGE | SENTINEL | Pruebas de cabeceras en respuestas de producción |
| 1.6 SMTP con 587/TLS por defecto y `verify-full` documentado | FORGE | SENTINEL | Prueba de settings |
| 1.7 `LOGGING` sin correos ni IP completas | FORGE | SENTINEL | Prueba: un login fallido no deja el correo en el log |
| 1.8 `region` como lista cerrada | FORGE | VERITY | Un valor fuera de lista se rechaza |

## Fase 2: publicaciones e interacciones 

- [FORGE] Categorías finales, imagen opcional con Pillow sin metadatos, comentarios sin hilos, votos y guardados únicos.
- [VERITY] Totales de votos, acceso horizontal y archivos inválidos. [SENTINEL] Carga de imágenes.
- Criterios: los de la Fase 2 de `MVP-ROADMAP.md` con D1 a D3 aplicadas.

### Condiciones del Storage de imágenes (SENTINEL)

| Tarea | Responsable | Revisión | Criterio verificable |
| --- | --- | --- | --- |
| 2.S1 Bucket privado en Supabase Storage, acceso solo desde Django con llave guardada como variable secreta del host de D5 (ver [DESPLIEGUE-VERCEL.md](../operations/DESPLIEGUE-VERCEL.md)) | FORGE | SENTINEL | La llave no aparece en el repo ni en el HTML; una petición anónima directa al bucket falla |
| 2.S2 Las imágenes se muestran con URL firmada de corta duración o las sirve Django | FORGE | SENTINEL | La URL caduca; las imágenes de borradores u ocultas no son accesibles |
| 2.S3 Solo se sube la imagen procesada (WebP, máximo 1600 px, sin EXIF) | FORGE | SENTINEL | Prueba: el archivo almacenado no tiene metadatos y respeta el tamaño |
| 2.S4 Borrar la publicación borra la imagen, más un comando que limpia huérfanos | FORGE | VERITY | Prueba de borrado y prueba del comando de limpieza |
| 2.S5 Actualizar `PILOTO-PRODUCCION.md`: Supabase pasa a usarse también como Storage | FORGE | VERITY | El documento refleja el uso y la política de borrado |

## Fase 3: feed, búsqueda y notificaciones

- [FORGE] Orden reciente y por relevancia, búsqueda, filtros y notificaciones internas.
- [VERITY] Pruebas deterministas de orden y ausencia de N+1. [SENTINEL] Aislamiento de notificaciones.
- Criterios: los de la Fase 3 del roadmap.

## Fase 4: reportes y moderación

- [FORGE] Reportes, flujo de moderación con trazabilidad, ocultar en lugar de borrar, accesibilidad a 360 px y por teclado, páginas de error.
- [VERITY] Recorrido completo de reporte. [SENTINEL] Permisos de moderador.
- Criterios: los de la Fase 4 del roadmap.

## Fase 5: despliegue y presentación

- [FORGE] Despliegue en el host elegido con PostgreSQL de Supabase, correo real, `collectstatic`, migraciones y respaldo probado.
- [SENTINEL] Auditoría del entorno publicado. [VERITY] Recorrido sintético de registro a resolución de reporte en el entorno publicado.
- [FORGE + ARCHITECT] Material de presentación: README final, diagrama de arquitectura y guion de demo con datos sintéticos.
- [FORGE] Variables del host según [DESPLIEGUE-VERCEL.md](../operations/DESPLIEGUE-VERCEL.md) (`DJANGO_ADMIN_URL`, `DJANGO_CSRF_TRUSTED_ORIGINS`, cabecera de IP) y `python manage.py createcachetable` tras migrar (la proxy header ya quedó en la Fase 1).
- [German + FORGE] Dominio `.tech` (D7) con SPF, DKIM y DMARC (`p=quarantine`) para Brevo. [SENTINEL] verifica los registros DNS.
- [German] Activar 2FA en la cuenta del registrador del dominio y anotar la fecha de vencimiento; MALENIA crea un aviso un mes antes. Si el dominio vence y otra persona lo registra, recibe el tráfico y los correos de la app.
- [FORGE] HSTS queda sin `preload` ni `includeSubDomains` mientras el dominio no sea definitivo (salir de la lista de preload tarda meses).
- [FORGE] Antes de la presentación, comprobar que el proyecto de Supabase no esté en pausa (se pausa tras una semana sin actividad) y comprobar `/health/` en el despliegue (ver [DESPLIEGUE-VERCEL.md](../operations/DESPLIEGUE-VERCEL.md)).
- Criterios: URL pública con HTTPS, `/health/` en 200 con base de datos, CI verde en `main`, respaldo restaurado una vez, ningún dato real.

## Fuera de alcance para la presentación

Mensajería privada, contacto público, recomendaciones algorítmicas y app móvil.
