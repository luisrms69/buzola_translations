# Changelog

Todas las versiones notables de `buzola_translations`.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/);
versionado [SemVer](https://semver.org/lang/es/).

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
