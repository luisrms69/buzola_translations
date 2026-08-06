# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-05
**Rama activa:** `feat/catalog-extraction` (rama de trabajo; `version-16` es la protegida)
**Tarea actual:** Catálogo español **auditado y definitivo** para Frappe, ERPNext y HRMS v16,
**reproducible** desde `review/*.csv` con `scripts/build_po.py`. Versión **0.1.0**. PR **#3 abierto** a `version-16`.

---

## Recuperación rápida

Estoy trabajando en:
La publicación del catálogo español **auditado (auditoría v3, cerrada)**. El catálogo **existe y es real**:
`buzola_translations/locale/es.po` con **18,417 traducciones auditadas**. La auditoría de **Frappe, ERPNext y
HRMS está cerrada**. El catálogo es **reproducible** ejecutando el generador oficial sobre los CSV de `review/`.

Plan que estoy siguiendo:
Fuente autoritativa = `review/*.csv` + `scripts/build_po.py`. La revisión externa (auditoría v3) quedó
incorporada a los CSV (356 filas `CAMBIAR` actualizadas) y el `.po` se **regenera** desde ahí.

Objetivo inmediato:
PR **#3** (`feat/catalog-extraction` → `version-16`) abierto; pendiente de merge manual del usuario.

Criterio de avance:
`build_po.py` regenera `es.po` con 18,417 entradas, 0 vacías/duplicadas/fuzzy, 0 pérdida de placeholders, y
contenido `msgstr` idéntico a la auditoría v3.

---

## Estado actual

### Ya cerrado
- **Catálogo definitivo:** `locale/es.po` = **18,417 entradas** auditadas (Frappe 6183 + ERPNext 9996 +
  HRMS 2246 elegibles − 8 dedups). SHA256 `4294217992df5aaa1778384d84a753020b4f7e07bfbe01d2f897a9ac06dee555`
  (generado por `build_po.py`; ver `working_docs/active/po_manifest.json`).
- **Reproducibilidad:** `env/bin/python apps/buzola_translations/scripts/build_po.py` regenera el `.po` desde
  los CSV; contenido idéntico a la auditoría v3 (0 `msgstr` distintos).
- **Decisiones terminológicas resueltas:** `Item→Artículo`, `Items→Artículos`, `Rate→Precio`,
  **`Payment Entry` resuelto como `Registro de Pago`**, `Mode of Payment→Forma de Pago`,
  `Purchase Receipt→Recepción de compra`, `Stock Reconciliation→Conciliación de inventario` (sentence case).
- **Versión:** `0.1.0` (`buzola_translations/__init__.py`).
- **Compilación:** `bench compile-po-to-mo --app buzola_translations` (el `.mo` vive en `sites/assets`, no se
  versiona).
- **PR #3 abierto** a `version-16` (OPEN; sin merge).

### Pendiente inmediato
1. Commit de reproducibilidad (CSV actualizados + `.po` regenerado + `po_manifest` + `CONTINUITY`) — pendiente
   de autorización de `/ship commit`.
2. Merge de PR #3 (acción manual del usuario en GitHub).

### Fuera de este catálogo (etapa futura)
- **Helpdesk y CRM** NO están incluidos en este catálogo; quedan **pendientes para una etapa futura**.

### No repetir
- No editar `build_po.py` para imitar el encabezado externo (el encabezado oficial de babel es el válido).
- No versionar `.mo` ni los directorios `working_docs/active/semantic_audit/` ni `client_translation_impact/`.
- El `.po` se **genera** desde los CSV; no se edita a mano.

---

## Decisiones vigentes
- Fuente de verdad = `review/*.csv` + `scripts/build_po.py`. El `.po` es un artefacto reproducible.
- `buzola_translations` se instala **al final** de `installed_apps` para que su `.mo` prevalezca.

---

## Archivos relevantes ahora
### Leer primero
- `working_docs/active/po_manifest.json` (sha, conteos, comando de generación).
- `scripts/build_po.py` (generador oficial).
### Probablemente editar
- `review/*.csv` (si cambian decisiones) → luego regenerar `es.po`.
### No tocar
- `.po` de apps de terceros; `.mo` compilado; directorios de auditoría/impacto (untracked, fuera del release).

---

## Riesgos / cuidados
- El SHA256 del `.po` depende del generador (babel) y de la versión en `__init__.py`; regenerar tras cambios.
- Los CSV usan CRLF; conservar el fin de línea al editarlos para diffs limpios.

---

## Información faltante
- Fecha de merge del PR #3 (decisión del usuario).
- Alcance/plazo de la etapa futura de Helpdesk y CRM.
