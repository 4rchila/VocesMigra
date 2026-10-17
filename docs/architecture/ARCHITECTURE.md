# Arquitectura del MVP

## Enfoque

Voces Migra será un monolito modular con renderizado en servidor. Django concentra reglas, autenticación, formularios, vistas, plantillas y administración; PostgreSQL conserva el estado. JavaScript no es requisito para los flujos esenciales. HTMX se incorpora solo cuando una interacción concreta mejore la experiencia sin romper la alternativa HTTP completa.

## Stack aprobado

- Python y Django 5.2 LTS.
- Django Templates con HTML semántico.
- CSS propio, mobile-first desde 360 px.
- HTMX únicamente para mejoras progresivas justificadas.
- PostgreSQL como objetivo productivo; SQLite puede usarse en desarrollo y pruebas locales.
- Django Auth y sesiones del servidor.
- Django TestCase/unittest.
- Pillow para validar y normalizar imágenes.

No se añaden APIs públicas, SPA, colas, cachés distribuidas, almacenamiento externo ni otros servicios en el MVP.

## Módulos

| Módulo | Responsabilidad | Entidades orientativas |
| --- | --- | --- |
| `core` | Páginas comunes, utilidades pequeñas, layout, errores y health check local. | Sin modelo de dominio salvo necesidad demostrada. |
| `accounts` | Usuario, autenticación, recuperación y perfil público. | `User`, `Profile`. |
| `posts` | Categorías, publicaciones, imagen, feeds, búsqueda y filtros. | `Post`; categorías mediante choices o catálogo controlado. |
| `interactions` | Comentarios planos, votos, guardados y sus reglas. | `Comment`, `Vote`, `SavedPost`. |
| `notifications` | Notificaciones internas por comentarios y estado leído. | `Notification`. |
| `moderation` | Reportes, estados, acciones y configuración administrativa. | `Report`, `ModerationAction` si la trazabilidad lo requiere. |

Cada módulo conserva dentro de su paquete modelos, migraciones, formularios, servicios, vistas, URLs, templates con namespace y pruebas. Las reglas reutilizables viven en funciones o servicios explícitos; las vistas coordinan y no concentran lógica de dominio.

## Dependencias permitidas

La dirección permitida es:

- `core` depende solo de Django y biblioteca estándar.
- `accounts` puede depender de `core`.
- `posts` puede depender de `core` y `accounts`.
- `interactions` puede depender de `core`, `accounts` y `posts`.
- `notifications` puede depender de `core`, `accounts`, `posts` e `interactions`.
- `moderation` puede integrar modelos del resto para administrar reportes.
- Ningún módulo de dominio depende de `moderation`.

Se prohíben ciclos. Las integraciones usan interfaces de servicio y claves foráneas explícitas; no se importan vistas ni formularios entre módulos. Las señales se reservan para efectos que no puedan expresarse con claridad en el caso de uso; crear un comentario y su notificación debe coordinarse en una transacción explícita.

## Límites de dominio

- El correo privado y único es el identificador de autenticación; la verificación no bloquea la participación en el MVP y la navegación pública permanece abierta.
- Debe definirse un modelo de usuario propio, con manager personalizado, antes de la primera migración.
- El alias público es único sin distinguir mayúsculas/minúsculas, tiene de 3 a 30 caracteres y acepta letras Unicode, números, punto, guion y guion bajo. El cooldown y los cambios frecuentes quedan pospuestos.
- El perfil guarda país ISO de dos letras, región general opcional e idiomas; no guarda GPS, dirección exacta, documentos ni situación migratoria legal.
- Una publicación tiene exactamente una categoría y como máximo una imagen.
- Los comentarios pertenecen a una publicación y no referencian otros comentarios.
- Un índice único garantiza un voto por usuario y publicación; el valor es positivo o negativo.
- Un índice único garantiza un guardado por usuario y publicación.
- La relevancia es global, determinista y no personalizada: votos positivos menos negativos, con fecha descendente como desempate.
- Solo el destinatario accede a sus notificaciones y guardados.
- Ocultar contenido conserva la trazabilidad requerida para moderación; las consultas públicas excluyen contenido oculto.

## Estructura prevista

```text
manage.py
config/
  settings/
    base.py
    development.py
    test.py
    production.py
  urls.py
  asgi.py
  wsgi.py
apps/
  core/
  accounts/
  posts/
  interactions/
  notifications/
  moderation/
templates/
static/
media/                 # local y no versionado
```

Las plantillas específicas van en `<app>/templates/<app>/`; `templates/` contiene únicamente layout y páginas globales. El CSS común vive en `static/css/`. Cada app mantiene sus pruebas en `<app>/tests/` y sus migraciones junto al modelo correspondiente.

## Configuración

`base.py` contiene valores comunes sin secretos. Los módulos de entorno importan la base y cambian solo lo necesario. Secret key, credenciales de PostgreSQL, host, modo debug y ajustes de correo se leen de variables de entorno con fallo temprano cuando sean obligatorios. No se versionan `.env` ni valores reales.

Desarrollo usa correo en consola, SQLite y medios locales sintéticos. Las pruebas locales pueden usar SQLite, configuración aislada, almacenamiento temporal y un hasher rápido explícito. La configuración queda preparada para PostgreSQL mediante variables de entorno. Producción exige `DEBUG=False`, HTTPS, hosts definidos, cookies seguras, protección CSRF, cabeceras de seguridad y PostgreSQL. No se seleccionan todavía proveedores productivos de correo, hosting o almacenamiento.

## Decisiones técnicas

- HTML server-rendered como contrato principal; HTMX nunca es la única ruta funcional.
- Formularios Django para validación y mensajes de error accesibles.
- Consultas de feed en QuerySets/servicios con `select_related` y `prefetch_related` medidos, no anticipados.
- Paginación por páginas en el MVP para URLs compartibles y comportamiento predecible.
- Búsqueda inicial con capacidades de PostgreSQL sin motor externo.
- Internacionalización activada desde el inicio; cadenas visibles marcadas para traducción y español como idioma inicial.
- Fechas almacenadas con zona horaria y mostradas según configuración.
- Restricciones de base de datos complementan la validación de formularios.
- Accesibilidad verificada con estructura semántica, foco visible, teclado, contraste, etiquetas y mensajes asociados.

## Calidad y observabilidad

Cada caso de uso incluye pruebas de permisos, validación, estados vacíos y error. Las pruebas de vistas comprueban respuesta y efectos persistidos; las reglas de ranking, votos y moderación se prueban de forma determinista. Los logs son estructurados en intención, no contienen secretos ni cuerpos completos y distinguen errores operativos de validación del usuario.
