# PLAN — Etapa 1: infraestructura, investigación y metodología

Plan de trabajo activo. Fuente rectora: `frappe-infrastructure/projects/buzola_translations/plan-rector.md`.
No es documentación publicable. Se archiva o migra al cerrar la etapa.

## Objetivo de la etapa

Dejar lista la infraestructura, probar el mecanismo de sobrescritura y validar la metodología de
traducción con una muestra — **sin** generar aún el catálogo completo ni los archivos finales.

## Fases

### F1 — Infraestructura (HECHO)
- [x] Auditoría de reglas frappe-infrastructure (scaffold, docs, git, symlinks).
- [x] Scaffold estándar de la app + symlink `.claude/commands`.
- [x] ADR-0000 con la decisión técnica y evidencia de código.
- [x] Documento rector en `projects/buzola_translations/`.

### F2 — Investigación técnica (HECHO)
- [x] Mecanismo de traducción v16 (`frappe/translate.py`): orden de carga, precedencia, caché.
- [x] Inventario de catálogos de las 5 apps (+ instalación helpdesk/telephony).

### F3 — Prueba mínima reproducible (HECHO — 2026-08-01, sitio `<site>`)
- [x] Instalación de la app y override de dos cadenas (erpnext + hrms) con valor local.
- [x] Persistencia tras `compile-po-to-mo` + `clear-cache`; reversibilidad al desinstalar.
- [x] Apps de terceros sin modificar. Evidencia y tabla ANTES/DESPUÉS en `docs/adr/0000`.

### F4 — Metodología y muestra (HECHO)
- [x] Agrupación ≤6 archivos definida (ver rector §10).
- [x] Muestra de catálogo (`review/_muestra_metodologia.csv`) con cadenas reales y contexto.

### F5 — Publicación del repositorio (HECHO — 2026-08-01)
- [x] Repo público `https://github.com/luisrms69/buzola_translations`, remoto `upstream` HTTPS.
- [x] `version-16 -> upstream/version-16`, HEAD `cc241f5`, 2 commits publicados, sin `origin`.

## Cerrado / pendiente
- **Infraestructura: CERRADA** (F1–F5). El repo está apto para la etapa funcional.
- **Pendiente (etapa funcional — otra conversación):** extracción real del catálogo
  (`generate-pot-file`), consolidación en `review/`, propuestas, revisión humana y generación de
  `locale/es.po` real (aún sin traducciones reales).

## No repetir
- helpdesk `develop` (rama móvil); se usó `main`.
- `docs/active/` (no canónico).
- SSH para GitHub; el estándar es HTTPS + `gh`.
