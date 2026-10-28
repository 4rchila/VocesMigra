# Nota de cierre: Fase 1, bloqueos de seguridad

**Fecha:** 2026-10-19
**Rama:** `fase-1-seguridad` (local, **sin push**)
**Dictamen:** SENTINEL aprueba con observaciones y VERITY: **cumple con observaciones**.

## Qué se hizo

| Commit / parche | Contenido |
|---|---|
| `ee3fc97` | 1.1 a 1.4: límite de intentos (cuenta+IP, IP y registro), registro sin enumeración de correos, admin en ruta obligatoria con TOTP y `/health/` con chequeo de base de datos |
| `3b8ee38` | 1.5 a 1.8: CSP sin `unsafe-inline`, Referrer-Policy, CSRF solo https, SMTP 587 con TLS, logs sin datos personales, región ISO 3166-2 (la migración `0002` borra las regiones escritas como texto libre; aprobada por German) |
| `c48e90e` | Documentación: D5 confirmada, dominio `.tech` (D7), DMARC y 2FA del registrador |
| `d1b4e6e` (parche `0004-Fase-1-activacion-vercel-limite-alias.patch`) | La contraseña se fija al activar la cuenta, `purge_unactivated_accounts`, ajustes para Vercel (IP real, build, configuración), límite global de 50 intentos por hora por cuenta y cambio de alias desde el perfil |

**Decisiones:** D5 queda con Vercel Hobby, Supabase y Brevo. HSTS va sin `preload` ni `includeSubDomains`.

## Comprobaciones
- 226/226 pruebas pasan. `makemigrations --check` no detecta cambios y `check --deploy` sale limpio (W005/W021 silenciados a propósito).
- Hay una prueba que reproduce el ataque de registrar primero el correo de otra persona.
- Hay una prueba que confirma que un `X-Forwarded-For` falso se ignora.

## Sin comprobar
- El despliegue real en Vercel: migraciones en el build, `collectstatic` y la cabecera de IP.
- PostgreSQL real y el correo real con Brevo.

## Pendientes
1. Aplicar los parches con `git am` en este orden: 0001, 0002, 0003 y 0004.
2. `purge_unactivated_accounts` queda como paso manual. El cron con `CRON_SECRET` pasa a la Fase 2.
3. Fase 2: conectar Supabase Storage antes de las imágenes.
4. Riesgo aceptado para el MVP: alguien puede bloquear una cuenta ajena durante una hora con 50 intentos fallidos.

## Siguiente paso
German aprueba el push. Después sigue la rama aparte con ruff, pre-commit y las reglas en posts.
