# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-24
**Rama activa:** `feat/locale-resync-v16` (rama de trabajo; `version-16` es la protegida)
**Tarea actual:** **Resincronización holística del catálogo a las versiones actuales del bench** (Frappe 16.31.0,
ERPNext 16.32.1, HRMS 16.16.0, Helpdesk 1.29.0, CRM 1.81.2): 5 apps revisadas + consolidación cross-app +
regeneración (`build_catalog`→`build_po`→`.mo`) + validación funcional en `buzola-demo.dev`.
**Estado:** commit del cierre holístico listo. **Pendiente `/ship push` y `/ship pr` a `version-16`** (autorizaciones separadas).

---

## Recuperación rápida

Catálogo español (México) que se superpone a Frappe/ERPNext/HRMS/Helpdesk/CRM vía `locale/es.po`.
`es.po` se **genera** desde `review/*.csv` con `build_po.py`; **nunca** se edita a mano. `.mo` no se versiona
(se compila a `sites/assets/locale/es/LC_MESSAGES/buzola_translations.mo`).

**Pipeline:** `extract_fresh_pot.py` (POT fresco por app, artefactos en `.artifacts/`, gitignored) →
`diff_upstream.py` (delta vs catálogo: nueva/eliminada/rename/contexto/placeholder) → `build_catalog.py` (regenera
los 7 `review/*.csv` preservando `human_authored=sí` por `entry_key`) → `build_po.py` (emite `es.po` solo de estados
elegibles con `proposed`; dedup por identidad Gettext; **HALT** si hay conflicto).

## Esta resincronización (lo hecho en esta rama)

- **Lotes lingüísticos aplicados (391) — todos `human_authored=sí`, verificados en runtime:**
  CRM 100 (commit `01cfa2f`, incluye fix del extractor de bindings Vue `:attr="__()"`) · Frappe 132 ·
  ERPNext 161 (Operaciones 101 / Contabilidad 60) · HRMS 10 · Helpdesk 88.
- **Umbral de renames:** 0.85 correcto para Frappe/HRMS/Helpdesk; **ERPNext requirió revisar 0.70** (renames
  reales tipo "reword/extend"). Bandas <0.70 = ruido en todas.
- **Decisiones terminológicas fijadas:** Submit→**Confirmar** (doc) / **Enviar** (form); DuckDB (propio);
  Reporte de instantánea; Solicitud de formulario web; Configuración de Frappe Cloud; repost→**reprocesar**;
  Overdue→**vencido/vencimiento** (NO "mora"); reverse→**reversión**; Dunning→**gestión de cobranza**;
  Landed Cost Voucher→Comprobante de costo de importación; apply→**postularse**; merge→combinar.
- **Consolidación cross-app:** barrido de 845 identidades compartidas → **6 divergencias latentes** normalizadas
  a su valor consensuado (`Add Column→Agregar columna`, `Add Sort→Agregar orden`, `Collapse→Contraer`,
  `Count→Cantidad`, `Submit→Enviar`, `Apps→Aplicaciones`). **0 divergencias** tras normalizar.
  NO se hizo la normalización global `Añadir→Agregar` (fuera de alcance).
- **Regeneración:** `build_catalog` EXIT 0 (22 348 filas, 0 colisiones, 0 pérdidas humanas). `build_po` EXIT 0 →
  **`es.po` = 20 992 entradas**, 0 conflictos, 0 pérdida de placeholders, 1 050 dedups, 251 huérfanas excluidas.
  `.mo` compilado (20 992 = 20 992).
- **Validación funcional (`buzola-demo.dev`):** 391/391 lotes + 6 consolidaciones + tooltip CRM ✅, 0 placeholders
  visibles; `po_huérfana` no publicables excluidas.

## ⚠️ CUIDADO CRÍTICO — `buzola_translations` debe ser la ÚLTIMA en `installed_apps`

El merge de `get_all_translations` recorre `installed_apps` (lee `db.get_global("installed_apps")`) y **la última
app gana**. Si otra app (p. ej. `crm`, tras reinstalarse) queda después de buzola, su `es.po` propio **sobrescribe**
el overlay para cadenas comunes (se vio: `Add Column`, `Count`, `High/Low/Medium`…). Las cadenas **nuevas** no se
ven afectadas (upstream vacío). **Fix aplicado en `buzola-demo.dev`** con `frappe.installer.remove_from_installed_apps`
+ `add_to_installed_apps` (solo edita la lista, no toca esquema; **es escritura en BD** + `clear-cache` + restart).
Orden correcto final: `[frappe, erpnext, hrms, crm, buzola_translations]`. **Replicar en cualquier sitio real.**

## Pendiente (autorización explícita por paso)

1. **`/ship push`** de `feat/locale-resync-v16` → **`/ship pr`** a `version-16` (con bump de versión y gate de versionado).
2. Sitios reales: asegurar que `buzola_translations` sea la última en `installed_apps`.
3. Fuera de alcance de esta rama: normalización estilística global `Añadir→Agregar` (~52), 4 avisos históricos de
   placeholders en traducciones `current` upstream, 2 `sin_proposed`.

## No repetir / cuidados

- **NO reordenar `ts_methods`** en `extract_fresh_pot.py` (van al final; antes rompe erpnext −358).
- **NO editar `es.po` a mano**; se regenera desde CSV. `.mo` no se versiona.
- Las decisiones humanas viven en `review/*.csv` con `human_authored=sí`; `build_catalog` solo preserva **esas** filas
  por `entry_key` → cualquier cambio manual en una fila debe marcar `human_authored=sí` o se revierte en el round-trip.
- Artefactos temporales en `one_offs/` y `.artifacts/` (ambos gitignored). Los lotes de esta resync vivieron en
  `one_offs/<app>_delta/`.

## Archivos relevantes

- `scripts/`: `extract_fresh_pot.py`, `diff_upstream.py` (+test), `build_catalog.py`, `build_po.py`, `extract_config.json`.
- `working_docs/active/`: `po_manifest.json`, `inventario_cobertura.csv`, `catalog_baseline.json`.
- `review/01..07` (fuente autoritativa) · `buzola_translations/locale/es.po` (generado).
