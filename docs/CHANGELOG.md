# Changelog

Todas las versiones notables de `buzola_translations`.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/);
versionado [SemVer](https://semver.org/lang/es/).

## [0.4.0] - 2026-08-24

Resincronización holística del catálogo a las versiones actuales del bench.

### Added
- **Extracción en bindings de atributo Vue:** el extractor (`scripts/extract_fresh_pot.py`) ahora
  captura llamadas `__()` en atributos `:attr="…"` / `v-bind` (antes omitidas por `html_template`) —
  origen del tooltip de CRM sin traducir.

### Changed
- **Resincronizado a las versiones instaladas:** Frappe **16.31.0**, ERPNext **16.32.1**, HRMS **16.16.0**,
  Helpdesk **1.29.0**, CRM **1.81.2**. `locale/es.po` regenerado (**20 992 entradas**, 0 conflictos,
  0 pérdida de placeholders).

### Actualización / operación
- **Requisito de precedencia:** `buzola_translations` debe quedar **última en `installed_apps`** para que
  su overlay prevalezca; si otra app queda después, su `es.po` propio sobrescribe las cadenas comunes.
- **Tras actualizar:** compilar el catálogo (`bench compile-po-to-mo --app buzola_translations`) y ejecutar
  `bench --site <sitio> clear-cache`.
- **No requiere `bench migrate`** (sin cambios de esquema).

## [0.3.0] - 2026-08-14

Incorporación de **Frappe CRM** al catálogo y cierre de cobertura del extractor SPA.

### Added
- **CRM** incorporado al catálogo: baseline lingüístico completo (**1 960 filas** revisadas), **+1 274
  entradas netas** en `locale/es.po` (total **20 879**). `Lead`/`Leads`, `Deal`/`Deals`, `Pipeline`/`Pipelines`
  se conservan en inglés (términos de industria); `Lost→Perdido`, `Won→Ganado`; nombres DocType `CRM …` con
  etiqueta traducida + prefijo (`CRM Lead→Lead de CRM`). 688 términos cross-app reutilizados.
- **Extractor `.vue` — cobertura de `{{ … }}`:** el wrapper ahora corre además `javascript.extract` sobre
  las expresiones `{{ … }}` del `<template>`, recuperando llamadas `__()` multilínea que quedaban fuera
  (ADR-0001). Auditoría de cobertura de las 5 apps: **0 literales estáticos omitidos** en archivos en alcance.
- `crm_consistency.csv` (evidencia de la auditoría de consistencia de CRM).

### Changed
- **16 convergencias globales Gettext** en apps ya publicadas (claves sin contexto compartidas): `Lead/Leads`
  (ERPNext `Prospecto`→`Lead`), `Add a Note`, `Company Description`, `Currency Precision`, `Email Account`,
  `To`/`To User`, `Select View`, `The holiday…`, `Your assignment…` (impersonal), y normalizaciones de
  mayúsculas (`Brand Name`, `Discount Amount`, `Current Password`, `Quick Filters`). Documentadas como
  correcciones deliberadas.
- **Compromisos globales conocidos** (clave sin contexto, sin traducción única perfecta): `Medium→Media`
  (prioridad domina sobre canal), `Read→Leer` (permiso domina sobre estado de notificación).
- Backlog aditivo `sin traducción` en apps publicadas por el fix `{{ }}`: helpdesk +2, hrms +1.

## [0.2.0] - 2026-08-14

Incorporación de **Frappe Helpdesk** al catálogo y arquitectura de soporte multi-app.

### Added
- **Helpdesk** incorporado al catálogo: baseline lingüístico completo (1 569 filas revisadas),
  **+1 188 entradas netas** en `locale/es.po` (total **19 605**). `Ticket`/`Tickets` y `SLA`/`SLAs`
  se conservan en inglés (términos de industria); registro impersonal; 382 términos reutilizados de
  Frappe/ERPNext/HRMS para consistencia cross-app.
- **Extractor común con cobertura SPA:** soporte `.ts`/`.tsx` y wrapper `.vue` (composición de los
  extractores oficiales de Frappe `html_template` ∪ `javascript` sobre `<script>`, con dedup y filtro
  de interpolación `${…}`), sin reimplementar el extractor (`scripts/extract_fresh_pot.py`).
- **Mantenimiento incremental:** `scripts/diff_upstream.py` (delta determinista sin LLM) +
  `working_docs/active/catalog_baseline.json` (manifiesto de punteros `upstream_rev` + hash).
- **Registro único de apps** en `scripts/extract_config.json` (objetos `app/upstream/branch/published/
  exceptions`); `build_po.py` publica solo apps con `published: true`.
- Bloques de revisión por app: `review/05_helpdesk.csv` y `review/07_crm.csv` (split byte-lossless del
  antiguo `05_helpdesk_crm.csv`).
- `docs/adr/0001` — decisiones de arquitectura de esta etapa.

### Changed
- **Convergencias globales Gettext** (una traducción por `msgid` sin contexto, en todas las apps):
  `Change→Cambiar`, `Mention→Mención`, `Primary→Principal`, `Hold→En espera`, `Ringing→Sonando`,
  `Holiday List Name→Nombre de la lista de días festivos`, `Resolution Time→Tiempo de resolución`,
  `Custom Range→Rango personalizado` (correcciones deliberadas y documentadas; no accidentales).
- `es.po` regenerado con `build_po.py`: 0 conflictos, 0 pérdida de placeholders, idempotente.

## [0.1.0] - 2026-08-06

Catálogo español auditado de **Frappe, ERPNext y HRMS** (PR #3, `f997df1`).

### Added
- `locale/es.po` con **18 417 entradas** auditadas (elegibles: frappe 6 183, erpnext 9 996, hrms 2 246),
  **reproducible** desde `review/*.csv` con `scripts/build_po.py`.
- Pipeline de revisión: extractor oficial fresco (`extract_fresh_pot.py`), generador de catálogo con
  gates de integridad (`build_catalog.py`) y generador de `.po` determinista (`build_po.py`).

## [0.0.1] - 2026-08-01

Etapa de setup del repositorio (infraestructura/configuración). Sin release funcional aún.

### Added
- Scaffold inicial de la app Frappe v16 (estructura estándar del ecosistema Buzola).
- ADR-0000: mecanismo de sobrescritura de traducciones vía catálogo `.po` local, **validado
  end-to-end** (prueba mínima reproducible: sobrescribe, persiste, revierte).
- CI/CD: `.github/workflows/ci.yml` (job `Validate`) y `linter.yml` (`Pre-commit`, `Dependency audit`).
- Protección de rama `version-16` mediante ruleset (PR obligatorio, force push/borrado bloqueados,
  historial lineal, checks obligatorios, sin bypass).
- Repositorio público con remoto `upstream` (HTTPS); validación desde clon limpio.
