#!/usr/bin/env python3
"""Falla si aparece el nombre del host viejo fuera de D5 / la guía de despliegue.

Criterio: regex r"\brender\b" sin distinguir mayúsculas. \b exige palabra
completa, así que "renderizadas" o "render_to_string" no coinciden. Para no
marcar llamadas de Django como `render(request, ...)` o `.render()`, se ignora
la coincidencia si va precedida de "." o seguida de "(" o "_".

Excepciones (misma línea, motivo no vacío):
  Python/YAML/.env:  # host-ok: <motivo>
  Markdown:          <!-- host-ok: <motivo> -->

Uso: python scripts/check_host_refs.py [raíz]   (0 = limpio, 1 = hallazgos)
"""
import re
import sys
from pathlib import Path

TARGETS = ["README.md", "docs", "config", "scripts", "vercel.json", ".env.example"]
SUFFIXES = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".example", ".html", ".sh"}
PATTERN = re.compile(r"(?<![.\w])render\b(?![(_])", re.IGNORECASE)
HOST_OK = re.compile(r"(#|<!--)\s*host-ok:\s*\S")
SELF = Path(__file__).resolve()


def files(root):
    for t in TARGETS:
        p = root / t
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and (f.suffix in SUFFIXES or f.name.startswith(".env")):
                    yield f


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    hits = []
    for f in files(root):
        if f.resolve() == SELF:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(lines, 1):
            if PATTERN.search(line) and not HOST_OK.search(line):
                hits.append(f"{f.relative_to(root)}:{n}: {line.strip()}")
    if hits:
        print("El host es Vercel (D5). Enlaza docs/operations/DESPLIEGUE-VERCEL.md "
              "en vez de nombrar el proveedor (o marca la línea con host-ok: <motivo>).")
        print("\n".join(hits))
        return 1
    print("check_host_refs: sin referencias al host viejo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
