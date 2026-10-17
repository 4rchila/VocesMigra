# Seguridad y privacidad del MVP

## Principios

- Recopilar solo datos necesarios para autenticación, perfil mínimo y operación comunitaria.
- Tratar todo contenido y metadato como potencialmente sensible, aunque sea público.
- Explicar la visibilidad antes de publicar y ofrecer edición o eliminación cuando sea compatible con moderación y obligaciones aplicables.
- Aplicar permisos en servidor; ocultar controles en la interfaz no es autorización.
- Usar exclusivamente datos sintéticos en desarrollo, pruebas, demostraciones y capturas.

## Datos y visibilidad

### Datos privados

El correo usado para acceder, las credenciales, los tokens de recuperación, los registros técnicos y la lista de publicaciones guardadas no son públicos. Las contraseñas se almacenan solo mediante Django Auth. Nunca se registran contraseñas, tokens ni contenido de correos de recuperación.

### Perfil público mínimo

Son públicos el alias, descripción, idiomas, país ISO de dos letras y región general opcional elegidos por la persona. Nunca se almacena GPS, dirección exacta, documentos personales ni situación migratoria legal.

País o región general es texto o una opción geográfica amplia; no admite coordenadas, barrio, dirección ni ubicación en tiempo real. La interfaz debe advertir que no se publique ubicación exacta en descripción, publicaciones, comentarios o imágenes.

### Contacto público opcional

El contacto público opcional queda pospuesto. Solo podrá implementarse después de definir advertencias de privacidad, formatos admitidos, validación específica y retiro simple; no forma parte del perfil inicial.

## Imágenes

- Una publicación admite como máximo una imagen y nunca la exige.
- Solo se aceptarán JPEG, PNG o WebP de hasta 5 MB; se validará el tipo real y el nombre se reemplazará por uno generado.
- Se rechazarán formatos activos o no previstos y se reencodificará la imagen con Pillow antes de servirla.
- Se eliminarán todos los metadatos, incluida geolocalización EXIF, antes de producción.
- La interfaz recuerda evitar rostros, documentos, matrículas, direcciones y otros identificadores.
- Los archivos se sirven como medios no ejecutables desde una ruta separada de estáticos.

Las dimensiones máximas y la estrategia de redimensionamiento se decidirán antes de implementar cargas.

## Reportes y moderación

Se pueden reportar publicaciones y comentarios por acoso, odio o discriminación, datos personales, fraude, contenido peligroso, spam u otro motivo. Un reporte incluye objetivo, reportante, motivo, detalle opcional, estado y marcas temporales.

Django Admin es la única interfaz de moderación del MVP. Los permisos de moderador se asignan por grupos, con mínimo privilegio. Las acciones sensibles deben conservar actor, fecha, motivo y resolución. Reportar no elimina contenido automáticamente; los casos de riesgo inmediato pueden ocultarse mediante una acción moderada y trazable.

La política operativa de apelación, conservación y tiempos de respuesta debe aprobarse antes de abrir el servicio a usuarios reales.

## Amenazas principales y controles

| Amenaza | Control mínimo del MVP |
| --- | --- |
| Enumeración de cuentas | Respuestas equivalentes en acceso y recuperación; límites de intentos aplicables. |
| Toma de cuenta | Hash de Django, protección CSRF, cookies seguras en producción y rotación de sesión. |
| Acceso indebido | Verificación de propietario o permiso en cada edición, borrado y vista privada. |
| XSS e inyección | Autoescape de Templates, ORM, validación de formularios y sin HTML aportado por usuarios. |
| Carga maliciosa | Validación por contenido, normalización con Pillow, límites y almacenamiento no ejecutable. |
| Exposición geográfica | Solo región amplia, advertencias y eliminación de EXIF. |
| Spam y abuso | Autenticación para participar, reportes, límites de frecuencia y revisión administrativa. |
| Hostigamiento por contacto | Campo opcional, advertencia previa, retiro simple y reporte de abuso. |
| CSRF o clickjacking | Middleware y cabeceras de seguridad de Django; formularios POST con token CSRF. |
| Fuga por logs | No registrar secretos ni cuerpos completos; acceso restringido y retención limitada. |

## Desarrollo y pruebas

Queda prohibido usar datos reales o plausiblemente atribuibles a una persona real. Fixtures y ejemplos usarán nombres, correos, ubicaciones, textos e imágenes completamente sintéticos. No se copiarán incidentes, documentos, conversaciones ni perfiles reales en issues, commits, pruebas o documentación.

Los secretos se suministran por variables de entorno y no se versionan. Los archivos locales se usan solo durante desarrollo; los medios sintéticos generados durante pruebas se aíslan y eliminan al finalizar. No se seleccionan todavía proveedores productivos de correo, hosting o almacenamiento. Cualquier exportación para depuración debe anonimizarse y autorizarse antes de salir del entorno previsto.

## Revisión previa al lanzamiento

- Confirmar matriz de permisos y pruebas de acceso horizontal.
- Probar recuperación sin enumeración, CSRF, sesiones y cierre de sesión.
- Verificar carga, normalización y eliminación de EXIF en imágenes.
- Revisar cookies, HTTPS, hosts, cabeceras, logs, backups y retención.
- Ensayar reporte, ocultamiento y auditoría con datos sintéticos.
- Publicar reglas comunitarias, aviso de privacidad y canal de contacto operativo.
