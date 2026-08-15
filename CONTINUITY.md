# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-14
**Rama activa:** `feat/etapa4-crm` (rama de trabajo; `version-16` es la protegida)
**Tarea actual:** Etapa 4 — **CRM publicado técnicamente en v0.3.0** (local, sin push/PR). `crm` con
`published:true`; `es.po` = **20 879 entradas** (sha `099a9a8a…`), 0 conflictos, idempotente; `.mo`
compilado; precedencia validada. **`/ship commit` de v0.3.0 autorizado; pendiente `/ship push` y `/ship pr`
(autorizaciones separadas).**

---

## Recuperación rápida

Catálogo español (México) que se superpone a Frappe/ERPNext/HRMS/Helpdesk/CRM vía `locale/es.po`.
Publicado: **v0.1.0** (Frappe/ERPNext/HRMS, PR #3), **v0.2.0** (Helpdesk, PR #4, tag+Release), **v0.3.0**
(CRM — en esta rama, técnicamente publicado, sin `/ship` aún).

**Sistema (cerrado, ver ADR-0001 + PLAN_etapa3):** extractor común SPA (`.ts/.tsx` + wrapper `.vue` que
compone html_template ∪ js(`<script>`) ∪ js(`{{ }}`)); `extract_config.json` registro único con `published`;
`build_po.py` publica solo `published:true`; mantenimiento incremental `diff_upstream.py` + `catalog_baseline.json`;
revisión por bloques (subagentes olas ≤5) + auditoría de consistencia + resolución de conflictos Gettext.

---

## CRM v0.3.0 — cerrado (esta rama, sin push)
- **Universo:** `review/07_crm.csv` = 1 960 filas 100% revisadas + 3 en bloque 06. Sin deriva upstream (`2752c85`).
- **Protegidos:** `Lead/Deal/Pipeline` inglés (0 violaciones); `Lost→Perdido`, `Won→Ganado`; nombres DocType
  `CRM …` traducidos (etiqueta + prefijo).
- **Extractor `{{ }}`:** ampliación del wrapper `.vue`; auditoría 5 apps = **0 literales estáticos omitidos**.
  Backlog aditivo `sin traducción`: helpdesk +2, hrms +1.
- **Publicación:** `es.po` **20 879** (v0.3.0). Diff vs v0.2.0 = **+1 274 CRM, 0 eliminadas, 16 convergencias**
  deliberadas en apps publicadas (Lead/Leads, Add a Note, To/To User, mayúsculas, etc.). **Compromisos
  globales conocidos:** `Medium→Media`, `Read→Leer` (clave sin contexto, menor daño global).
- **Validaciones:** 0 conflictos, 0 pérdida placeholders, idempotente, precedencia OK, `.mo` compilado.

---

## Pendiente (autorización explícita por paso)
1. **v0.3.0:** `/ship commit` (autorizado) → `/ship push` → `/ship pr` a `version-16` → merge (usuario) →
   `/ship release` (tag+Release `v0.3.0`).
2. Próximas apps: mismo procedimiento estándar.

## No repetir / cuidados
- **NO reordenar `ts_methods`** en `extract_fresh_pot.py` (van al final; antes rompe erpnext −358).
- `es.po` se **genera** desde los CSV; no se edita a mano. `.mo` no se versiona.
- Al publicar, `build_po` HALTA ante conflictos Gettext (claves sin contexto compartidas) → resolver con
  convergencia global documentada (patrón Helpdesk/CRM).

## Archivos relevantes
- `working_docs/active/PLAN_etapa3.md`, `PLAN_helpdesk_review.md`, `PLAN_crm_review.md`.
- `working_docs/active/crm_consistency.csv`, `helpdesk_consistency.csv`, `catalog_baseline.json`, `po_manifest.json`.
- `scripts/`: `extract_fresh_pot.py`, `diff_upstream.py` (+test), `build_catalog.py`, `build_po.py`, `extract_config.json`.
