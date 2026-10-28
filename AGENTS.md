# AGENTS.md — reglas del repo y quién las hace cumplir

| Regla | Enforcer |
|---|---|
| El host de producción solo se nombra en D5 (`docs/plan/PLAN-OFICIAL.md`); el resto enlaza la guía (`docs/operations/DESPLIEGUE-VERCEL.md`) | `scripts/check_host_refs.py` en CI (falla con `Render` fuera de las excepciones `# host-ok: <motivo>` o `<!-- host-ok: <motivo> -->`) |
| Al cerrar una tarea, borrar las notas "pendiente" que ya se cumplieron | Solo documentación (juicio; la revisa VERITY) |
| Los `.md` nuevos van en `docs/{architecture,operations,plan,product}/` | Solo documentación por ahora; pasa a check de CI si se repite |
| Los comentarios sobre el comportamiento de la plataforma dicen "confirmar en el despliegue" si no se probaron | Solo documentación (juicio) |
| Pruebas, migraciones y `check --deploy` en verde | CI existente (`.github/workflows/ci.yml`) |
