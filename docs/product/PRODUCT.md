# Voces Migra: definición del producto

## Visión

Voces Migra es una plataforma web comunitaria, mobile-first y centrada en publicaciones para que personas en situación de migración compartan vivencias, planteen problemas, ofrezcan o soliciten ayuda, expresen opiniones y conversen. Debe facilitar información y apoyo entre pares sin convertir la participación en una competencia de popularidad.

No es una red social: el producto se organiza alrededor del contenido y las conversaciones, no de seguidores, reputación ni exposición personal.

## Usuarios

- Persona migrante que busca orientación práctica o experiencias comparables.
- Persona migrante que desea contar una vivencia o pedir ayuda a la comunidad.
- Integrante de la comunidad que comparte recursos o responde preguntas.
- Moderador que revisa reportes y aplica medidas desde Django Admin.

El MVP parte en español, admite distintos niveles de alfabetización digital y debe funcionar desde 360 px, con teclado y tecnologías de asistencia.

## Problemas que resuelve

- La información útil está dispersa y suele carecer de contexto comunitario.
- Pedir ayuda puede exigir revelar más datos personales de los necesarios.
- Las experiencias migratorias necesitan espacios de conversación simples, accesibles y moderables.
- Las personas requieren encontrar publicaciones recientes o relevantes sin un sistema de recomendación personalizado.

## Propuesta de valor

Un espacio sencillo y seguro para publicar, buscar y conversar usando una identidad pública mínima. Las categorías y filtros dan estructura al contenido; los votos y guardados ayudan a recuperar aportes útiles; los reportes y la moderación reducen abuso sin recopilar información migratoria sensible.

## Funcionalidades del MVP

### Cuenta y perfil

- Registro e inicio de sesión con correo y contraseña mediante Django Auth; el correo es privado.
- La verificación de correo no es obligatoria para publicar, comentar, votar o guardar.
- La navegación pública no requiere una cuenta.
- Recuperación de contraseña mediante los mecanismos de Django.
- Perfil público mínimo: alias, descripción breve, país ISO de dos letras, región general opcional e idiomas.
- Alias único sin distinguir mayúsculas/minúsculas, de 3 a 30 caracteres y formado por letras Unicode, números, punto, guion o guion bajo.
- El contacto público opcional se pospone hasta contar con advertencias de privacidad y validación específica.

### Publicaciones y conversación

- Categorías cerradas: vivencias, problemas, ayudas, opiniones y comunidad.
- Publicación con título, cuerpo y una imagen opcional.
- Comentarios planos en publicaciones, sin respuestas anidadas.
- Un voto positivo o negativo por persona y publicación, modificable o revocable.
- Guardar y quitar publicaciones de una lista personal.

### Descubrimiento

- Feed ordenable por recientes o relevancia simple y no personalizada: votos positivos menos negativos, con fecha descendente como desempate.
- Búsqueda textual y filtros básicos por categoría, país o región general e idioma cuando exista el dato.
- Paginación estable y estados vacíos comprensibles.

### Notificaciones y moderación

- Notificación interna al autor cuando otra persona comenta su publicación.
- Lectura y marcado de notificaciones como vistas.
- Reporte de publicaciones y comentarios con motivo predefinido y detalle opcional.
- Revisión de reportes y acciones de moderación mediante Django Admin.

## Exclusiones del MVP

- Videos, historias y aplicación móvil nativa.
- Mensajería privada, seguidores y reputación social.
- GPS, ubicación exacta o seguimiento de ubicación.
- Documentos personales, estado migratorio legal y número telefónico privado.
- Inicio de sesión social y notificaciones push.
- Recomendaciones algorítmicas o personalizadas.

## Flujos principales

### Registro y publicación

1. La persona crea una cuenta con correo y contraseña; no necesita verificar el correo para participar en el MVP.
2. Completa o pospone los campos opcionales del perfil.
3. Elige una categoría, redacta título y cuerpo y, si quiere, adjunta una imagen.
4. Revisa qué datos serán públicos y publica.
5. La publicación aparece en el feed y en los resultados aplicables.

### Descubrimiento y participación

1. La persona abre el feed por recientes o relevancia.
2. Busca texto o aplica filtros básicos.
3. Abre una publicación y puede comentar, votar o guardarla si inició sesión.
4. El autor recibe una notificación interna por el comentario.

### Recuperación de acceso

1. La persona solicita recuperación con su identificador privado de acceso.
2. Recibe y utiliza el flujo estándar de recuperación de Django.
3. La respuesta de la interfaz no revela si una cuenta existe.

### Reporte y moderación

1. Una persona autenticada reporta una publicación o comentario y selecciona un motivo.
2. El reporte queda pendiente sin ocultar automáticamente el contenido.
3. Un moderador revisa contexto e historial desde Django Admin.
4. El moderador resuelve el reporte y, cuando corresponda, oculta contenido o restringe la cuenta dejando trazabilidad administrativa.

## Indicadores iniciales

- Finalización correcta de registro, publicación, comentario, búsqueda y reporte.
- Tiempo de respuesta y ausencia de errores en viewport de 360 px.
- Proporción de reportes atendidos y tiempo hasta resolución.
- Incidentes de exposición de datos sensibles: objetivo cero.

Las métricas no deben convertirse en puntajes públicos ni perfiles de reputación.
