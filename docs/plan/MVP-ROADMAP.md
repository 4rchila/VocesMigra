# Roadmap del MVP

## Reglas de entrega

Cada fase termina con pruebas automáticas, revisión responsive desde 360 px, recorrido por teclado, comprobación de permisos y datos sintéticos. Una historia no está terminada si solo funciona por HTMX: su flujo HTTP completo debe seguir disponible. No se inicia una fase dependiente mientras fallen sus criterios de aceptación.

## Fase 1: base, cuenta y perfil

### Historias

- Como visitante, quiero registrarme, iniciar y recuperar mi acceso para participar.
- Como usuario, quiero cerrar todas las acciones de mi sesión de forma segura.
- Como usuario, quiero editar un perfil público mínimo y entender qué campos son visibles.

### Criterios de aceptación

- Django 5.2 arranca con configuración separada, SQLite local y PostgreSQL preparado mediante variables de entorno como objetivo productivo.
- Existe usuario propio desde la primera migración; usa correo único como identificador, manager personalizado y recuperación sin enumeración.
- La verificación de correo no bloquea la participación y la navegación pública está disponible.
- El alias es único sin distinguir mayúsculas/minúsculas, mide de 3 a 30 caracteres y admite letras Unicode, números, punto, guion y guion bajo.
- El perfil incluye descripción, país ISO de dos letras, región general opcional e idiomas; el contacto público queda pospuesto.
- Solo el propietario edita el perfil; correo, credenciales y datos privados nunca aparecen públicamente.
- Registro, acceso, cierre, recuperación y perfil tienen pruebas positivas, negativas y de autorización.

Dependencias: ninguna decisión de producto pendiente para iniciar el fundamento; cambios frecuentes de alias y cooldown quedan diferidos.

## Fase 2: publicaciones e interacciones

### Historias

- Como usuario, quiero publicar en una categoría con una imagen opcional.
- Como lector autenticado, quiero comentar sin hilos, votar y guardar publicaciones.
- Como autor, quiero editar o retirar mi contenido sin alterar contenido ajeno.

### Criterios de aceptación

- Las cinco categorías están disponibles y el título y cuerpo tienen validación de servidor.
- La imagen se limita a una JPEG, PNG o WebP de hasta 5 MB, se reencodifica con Pillow y queda sin metadatos antes de producción.
- Los comentarios no admiten padre ni respuestas anidadas.
- La base impide votos y guardados duplicados; cambiar o revocar un voto produce totales correctos.
- Solo propietarios o moderadores autorizados modifican contenido; lo oculto no aparece en consultas públicas.
- Casos de uso, restricciones, archivos inválidos y acceso horizontal tienen pruebas.

Dependencias: Fase 1 y decisión posterior sobre dimensiones y redimensionamiento.

## Fase 3: feed, búsqueda y notificaciones

### Historias

- Como visitante, quiero ordenar por reciente o relevancia y filtrar contenido útil.
- Como visitante, quiero buscar publicaciones por texto.
- Como autor, quiero saber dentro de la plataforma cuando comentan mi publicación.

### Criterios de aceptación

- El orden reciente es estable; la relevancia ordena por votos positivos menos negativos y desempata por fecha descendente, con pruebas deterministas.
- Búsqueda y filtros por categoría, región e idioma se pueden combinar y conservan paginación.
- No hay personalización, perfilado ni recomendaciones algorítmicas.
- Un comentario de otra persona crea una sola notificación para el autor; el autocomentario no la crea.
- Solo el destinatario lista y marca sus notificaciones; existen estados vacío y leído.
- Las consultas principales evitan crecimiento N+1 comprobable.

Dependencias: Fases 1 y 2.

## Fase 4: reportes, moderación y endurecimiento

### Historias

- Como usuario, quiero reportar contenido indicando un motivo.
- Como moderador, quiero revisar y resolver reportes con trazabilidad.
- Como persona con necesidades de accesibilidad, quiero completar todos los flujos con una interfaz clara y responsive.

### Criterios de aceptación

- Publicaciones y comentarios se reportan una vez por usuario y motivo aplicable, sin borrado automático.
- Django Admin filtra pendientes, muestra contexto y registra resolución, actor y fecha.
- Los permisos de moderación no se conceden a usuarios comunes y se prueban acciones sensibles.
- Los flujos principales funcionan a 360 px, con teclado, foco visible, etiquetas y contraste revisado.
- Las cadenas visibles están preparadas para traducción y el contenido inicial está en español.
- Se verifican CSRF, cookies y cabeceras de producción, logs sin datos sensibles y páginas de error.

Dependencias: Fases 1 a 3 y política operativa de moderación aprobada.

## Fase 5: validación del MVP

### Criterios de salida

- Suite completa verde con pruebas de dominio, vistas, permisos y regresión.
- Recorrido manual con datos totalmente sintéticos de registro a reporte y resolución.
- No existen funciones excluidas, servicios externos no aprobados ni datos reales.
- `git diff --check`, comprobaciones de Django y revisión de migraciones pasan.
- Riesgos conocidos y decisiones diferidas quedan documentados antes del despliegue.

## Organización del trabajo

La asignación de tareas, responsables y revisiones del desarrollo oficial está en `docs/plan/PLAN-OFICIAL.md`.

## Decisiones diferidas

1. Cooldown y política de cambios frecuentes del alias.
2. Advertencias, formato y validación del contacto público opcional.
3. Dimensiones y redimensionamiento de imágenes.
4. Plazos de conservación, eliminación, apelación y respuesta de moderación.
5. Proveedores productivos de correo, hosting y almacenamiento.
