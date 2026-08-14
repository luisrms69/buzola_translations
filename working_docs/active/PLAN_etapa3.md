# PLAN — Etapa 3: incorporación uniforme de apps + mantenimiento incremental + cobertura SPA

Plan de trabajo activo. Continúa `PLAN_etapa2_catalogo_completo.md` (Frappe/ERPNext/HRMS cerrados y
publicados en `es.po` v0.1.0). Esta etapa incorpora **apps nuevas** (Helpdesk piloto → luego CRM) con el
**mismo rigor, trazabilidad y reproducibilidad**, añade **mantenimiento incremental de bajo consumo** y
corrige una **debilidad de cobertura SPA** detectada y verificada. **No** autoriza revisión/traducción
masiva, generación de `.po/.mo`, instalación, despliegue ni `/ship`.

## Estado de verificación (lo aquí escrito está COMPROBADO en esta sesión)
- Rama `feat/etapa3-helpdesk-incremental`. Extracción solo lectura sobre `proposals.dev`. Sin BD, sin
  tocar apps de terceros, sin `.po/.mo`, sin `/ship`.
- **Implementado y verificado:**
  - `scripts/diff_upstream.py` + `scripts/test_diff_upstream.py` (6 clases de delta PASS).
  - `extract_fresh_pot.py`: cobertura SPA `.ts/.tsx` **y** wrapper `.vue` (composición de extractores
    oficiales; ver §3).
  - `extract_config.json` migrado a **objetos** (`app/upstream/branch/published/exceptions`); los 3 scripts
    lo leen.
  - `build_po.py`: gate **`published`** (sin `APPS` hardcodeado ni exclusión de helpdesk/crm).
  - `build_catalog.py`: bloques por app — `05_helpdesk` + `07_crm` (split del antiguo `05_helpdesk_crm`).
  - Split del CSV `05_helpdesk_crm` → `05_helpdesk` + `07_crm` **byte-lossless** (unión reproduce el
    original exacto; CRLF conservado; 0 filas alteradas).
  - `working_docs/active/catalog_baseline.json` (manifiesto de punteros rev+hash de las 5 apps).

## 1. Arquitectura del pipeline (recordatorio, sin cambios de fondo)
`extract_fresh_pot.py` (extractor oficial en memoria, config-driven) → `.artifacts/freshpot/<app>.jsonl`
+ `manifest.json` → `build_catalog.py` (universo ∪ `es.po` → `review/*.csv` de 40 columnas + inventario,
con gates fail-fast y round-trip humano por `entry_key`) → `build_po.py` (filas elegibles → `locale/es.po`
byte-reproducible). Identidad estable = `entry_key` = `<app>:SHA1[:16]` de JSON canónico
`{app,msgctxt,msgid,msgid_plural}`. Fuente humana autoritativa = los CSV.

## 2. Registro único de apps — `extract_config.json` (a migrar a objetos)
Única fuente de la lista de apps para **los tres** scripts. Migración **no rompiente** (el parser de
`diff_upstream.py` ya acepta ambos formatos; `build_catalog.py`/`extract_fresh_pot.py` se adaptarán):

```json
{
  "apps": [
    { "app": "frappe",   "upstream": "https://github.com/frappe/frappe",   "branch": "version-16", "published": true,  "exceptions": [] },
    { "app": "erpnext",  "upstream": "https://github.com/frappe/erpnext",  "branch": "version-16", "published": true,  "exceptions": [] },
    { "app": "hrms",     "upstream": "https://github.com/frappe/hrms",     "branch": "version-16", "published": true,  "exceptions": [] },
    { "app": "helpdesk", "upstream": "https://github.com/frappe/helpdesk", "branch": "main",       "published": false, "exceptions": [] },
    { "app": "crm",      "upstream": "https://github.com/frappe/crm",      "branch": "develop",    "published": false, "exceptions": [] }
  ]
}
```
- `build_po.py` publica al `.po` **solo** apps con `published: true` → reemplaza el `APPS` hardcodeado y
  la exclusión manual de helpdesk/crm. **Sin listas paralelas** (`published_apps`). Una app entra al `.po`
  únicamente cuando su baseline se marca aprobado poniendo `published: true`.
- Incorporar una app futura = añadir un objeto aquí. La lógica central no cambia.

## 3. Cobertura SPA — corrección común verificada (`.ts/.tsx`)
**Hallazgo:** el method_map oficial de Frappe (`frappe/babel_extractors.csv`) mapea `.js/.vue/.py/.json`
pero **NO `.ts/.tsx`**. Los SPA en TypeScript (Helpdesk: `desk/src`, 11 archivos `.ts` con `__()`) quedaban
**invisibles**: 154 literales `__()` fuera del universo, ~140 texto visible real (`API Key`, `App Settings`,
`Delete View`, `Copied to clipboard.`…).

**Corrección (implementada en `extract_fresh_pot.py`):** se añade al method_map
`("**.ts", javascript.extract)` y `("**.tsx", javascript.extract)`, **reutilizando el mismo extractor JS
oficial** que Frappe usa para `.js` (tokenizer de babel modificado; maneja `__()`, plurales y `msgctxt`).
**Sin regex propio.**

**Verificación (real, esta sesión):**
- El extractor JS procesó los **67 `.ts/.tsx`** de Helpdesk con **0 errores** (`one_offs/ts_extract_probe.py`).
- Re-extracción: **Helpdesk 1426 → 1554** (+128; 132 texto real, 3 ruido, 0 duplicados). Frappe/ERPNext/HRMS
  **sin cambio (Δ0)** → sin regresión. Cobertura de literales SPA Helpdesk **86.2% → 97.7%** (gap 154 → 26).
- Beneficio colateral: 19 cadenas antes marcadas "huérfanas PO-only" eran strings vivos en `.ts`; ahora se
  reconcilian correctamente (huérfanas 116 → 97).
- **CRM:** su SPA es `.vue/.js` (no TypeScript; solo 7 `.ts/.tsx`, ninguno con `__()` en `frontend/`).
  Re-extracción CRM **Δ0** → la corrección lo cubre sin añadir nada indebido. Cobertura SPA CRM **97.2%**.
- **Residual Helpdesk (sigue fuera):** 26 literales (llamadas multilínea/backtick) + 49 `__()` con 1er
  argumento **dinámico** (variable) — **no extraíbles por diseño** en ningún gettext. No justifican cambio
  arquitectónico; se revisan caso a caso si aparecen como visibles.

### 3b. Cobertura SPA `.vue` — wrapper de composición (verificado)
**Hallazgo:** el extractor oficial de `.vue` (`html_template.extract`) **omite backticks y llamadas `__()`
multilínea** del bloque `<script>` (limitación upstream de Frappe; su propio `main.pot`/`es.po` también las
pierde). Afecta a Helpdesk **y** CRM.

**Solución (`extract_fresh_pot.py`):** se remapea `**.vue` a un **wrapper** que **compone dos extractores
oficiales de Frappe** (sin regex propio): `html_template.extract` **∪** `javascript.extract` sobre cada
`<script>`, con offset de línea, **dedup** por `(funcname,msgid)` (no duplica lo que html ya obtuvo) y
**filtro de literales con interpolación `${…}`** (no traducibles estáticamente).

**Orden crítico del `method_map`:** `**.vue`→wrapper va **al frente** (gana sobre el oficial); `.ts/.tsx`
van **al final** (tras el map oficial). Poner `.ts/.tsx` antes rompe erpnext (frontend `banking/`) −358
cadenas de forma determinista. **NO reordenar.**

**Verificación (real, esta sesión), efecto del wrapper `.vue` (vs estado solo-`.ts`):**
- **erpnext Δ0** (10002→10002, 0 añadidas). **frappe +6** (3 texto real de subida de archivos + 3 tokens
  no traducibles `16:9/1:1/4:3`). **hrms +1** (`Document {0} successfully!`). **helpdesk +15** · **crm +26**
  (recuperación real de `.vue`). **0 eliminadas** en toda app (solo adiciones), **0 duplicados**, el wrapper
  añadió **0** msgids con `${…}` (los 3 de frappe son preexistentes, ajenos al wrapper).
- Cobertura de literales SPA Helpdesk: 86.2% (solo html) → **97.7%** tras `.ts`; el wrapper `.vue` recupera
  además la clase backtick/multilínea.
- **Criterio de cierre = cero regresiones** (no cero filas nuevas): frappe +6 / hrms +1 son **adiciones**
  (backlog `sin traducción` de esas apps congeladas); ninguna traducción aprobada cambia, `es.po` intacto.

## 4. Mantenimiento incremental — `diff_upstream.py` (implementado)
**Principio:** el trabajo pesado y determinista lo hace el script; Claude solo ve las cadenas que requieren
criterio lingüístico, en bloques pequeños. **Sin copia paralela de traducciones.**

- **Fuente de verdad = `review/*.csv`.** El delta compara el **universo fresco** contra el **CSV aprobado**
  por `entry_key` (misma identidad y mismo detector de placeholders que `build_catalog.py`, reutilizados).
- **Baseline = manifiesto de punteros** `working_docs/active/catalog_baseline.json`: por app,
  `{upstream_rev, branch, version, catalog_sha256, approved_count}`. **No** contiene traducciones. Sirve la
  **ruta rápida no-op:** si `upstream_rev` y `catalog_sha256` no cambiaron → nada que revisar.
- **Clases del delta (deterministas, sin LLM):** `sin_cambios`, `nueva`, `eliminada`, `cambio_contexto`,
  `cambio_plural`, `cambio_placeholders`, `posible_rename` (similitud `SequenceMatcher`, umbral 0.85).
  Emparejamiento secundario: contexto/plural por `msgid`, placeholders por texto-base, rename por similitud.
- **Solo** `nueva + posible_rename + cambio_placeholders + cambio_contexto/plural` van a revisión humana.
  `sin_cambios` conserva su traducción aprobada (round-trip de `build_catalog.py`); `eliminada` sale del `.po`.
- **Salidas:** `working_docs/active/<app>_delta.{csv,json}` (delta clasificado + resumen). Validación
  mecánica (placeholders, duplicados, huérfanas, hashes, idempotencia) queda en `build_catalog.py`/
  `build_po.py`, **fuera del contexto de Claude**.
- **Prueba:** `scripts/test_diff_upstream.py` verifica que las 6 clases disparan con mutaciones sintéticas
  (el dry-run real de Helpdesk solo pudo ejercitar `sin_cambios`+`eliminada` por no haber deriva upstream).

**Resultado real Helpdesk (CSV autoritativo vs fresco con `.ts`+wrapper `.vue`):** `csv=1542 fresco=1569` →
`sin_cambios=1443 nueva=124 eliminada=97 posible_rename=2` → **requieren criterio lingüístico: 126**.
Incorporar Helpdesk hoy = revisar ~126 cadenas, no 1 569. Una actualización futura con +20/+50 upstream
revisaría solo esas (`sin_cambios` conserva traducción aprobada sin re-revisión). Las `eliminada` de cada
app = sus huérfanas PO-only conocidas (frappe 124, erpnext 5, hrms 40, helpdesk 97, crm 1), no regresiones.

## 5. Procedimiento para incorporar una app (Helpdesk)
1. Extraer fresco (solo lectura) con el extractor extendido → `manifest.json` con `upstream_rev`.
2. `diff_upstream.py --app helpdesk` → delta; revisar humanamente **solo** `nueva/rename/placeholders/ctx`
   en bloques pequeños, persistiendo por bloque (patrón checkpointeado de etapa 2).
3. Escribir decisiones en `review/` (bloque propio de Helpdesk); `build_catalog.py` las preserva por `entry_key`.
4. Marcar `published: true` para helpdesk en `extract_config.json`.
5. `build_po.py` regenera `es.po` incluyendo Helpdesk → nuevo `po_sha256`; actualizar `catalog_baseline.json`.
6. Validar: 0 vacías/dup/fuzzy, 0 pérdida de placeholders, `check_translation_order`, compilar `.mo`.
7. `/ship` por pasos, con autorización explícita en cada uno.
8. Repetir para CRM (sin gap `.ts`; residual de 25 casos con placeholders a revisar en su fase).

## 6. Cambios de scripts/config/docs de la etapa
| Archivo | Estado | Cambio |
|---|---|---|
| `scripts/extract_fresh_pot.py` | **hecho** | method_map `.ts/.tsx`→`javascript.extract` (al final) + wrapper `.vue` (composición html_template ∪ js(`<script>`), dedup, filtro `${}`) |
| `scripts/diff_upstream.py` | **hecho** | motor de delta incremental (sin LLM) |
| `scripts/test_diff_upstream.py` | **hecho** | prueba de las 6 clases |
| `scripts/extract_config.json` | **hecho** | migrado a objetos (`app/upstream/branch/published/exceptions`) |
| `scripts/build_po.py` | **hecho** | gate `published` (sin `APPS` hardcodeado ni exclusión helpdesk/crm) |
| `scripts/build_catalog.py` | **hecho** | bloques por app: `05_helpdesk` + `07_crm` |
| `review/05_helpdesk.csv`, `review/07_crm.csv` | **hecho** | split byte-lossless del antiguo `05_helpdesk_crm.csv` |
| `working_docs/active/catalog_baseline.json` | **hecho** | manifiesto de punteros rev+hash (5 apps) |
| `CONTINUITY.md` | **hecho** | refleja arranque etapa 3 |

## 7. Riesgos / límites
- Helpdesk (`main`) y CRM (`develop`) no están en `version-16`: `msgid` pueden moverse; el delta lo absorbe,
  pero CRM en `develop` seguirá siendo el más volátil (por eso Helpdesk primero).
- `__()` con argumento dinámico (49 en Helpdesk) no es extraíble estáticamente por ningún gettext; queda
  fuera por diseño. Textos hardcodeados sin `__()` requieren auditoría de código aparte (pendiente etapa 2).
- La extensión `.ts` asume que el tokenizer JS de babel tolera TypeScript; verificado 0 errores en Helpdesk;
  el manifiesto fail-fast abortaría si una app futura fallara (entonces se evaluaría el fallback, no antes).

## 8. Baseline lingüístico de Helpdesk — CERRADO (2026-08-14, sin publicar)
Ejecutado con el procedimiento estándar de etapa 2 (ver `PLAN_helpdesk_review.md`). Fases 0–4 completas:
- **Fase 0:** regeneración al universo completo (fold `.ts/.vue`); verificado 0 cambios en decisiones
  humanas (solo 237 etiquetas `status` normalizadas correcta↔mejorable; 0 en `proposed_translation`);
  2ª regeneración byte-idéntica; frozen apps intactas.
- **Fases 1–3 (revisión inicial):** glosario (`Ticket`/`SLA` protegidos, 382 msgids cross-app reutilizados,
  9 decisiones LOCKED), troceo semántico en 9 bloques (~175), **9 subagentes en olas ≤5** con persistencia
  por bloque, integración idempotente. **1 569 filas revisadas al 100 %.**
- **Fase 4 (auditoría de consistencia + pase dirigido):** auditor determinista → candidatos; correcciones:
  reversión `ANS`→`SLA` (25), **registro normalizado a impersonal/usted** (~97 %, era 50/50), nombres
  `HD …` unificados (etiqueta + sufijo HD), `Clear all filters`→"Limpiar todos los filtros",
  `Emails`→"Correos electrónicos", `conectarte`→`conectarse`.

**Resultado final:** universo **1 569** (`propuesta` 708 · `correcta` 620 · `mejorable` 181 · `igual al
inglés` 60). Consistencia: **0 protegidos violados**; **14 `crossapp_divergente` = 7 divergencias legítimas
de Helpdesk + 7 solo mayúsculas** (ambas conservadas por decisión). 0 pérdida de placeholders; idempotente;
Frappe/ERPNext/HRMS/CRM byte-idénticas desde Fase 0. **Helpdesk queda lingüísticamente APROBADO pero
`published:false` (no publicado).** Artefactos en `one_offs/hd/`; tabla en
`working_docs/active/helpdesk_consistency.csv`.

## 9. Gobernanza
Nada de revisión/traducción masiva, generación de `.po/.mo`, `published:true`, instalación, despliegue ni
`/ship` sin autorización explícita e independiente por paso. La rama protegida es `version-16`; todo
termina en PR.
