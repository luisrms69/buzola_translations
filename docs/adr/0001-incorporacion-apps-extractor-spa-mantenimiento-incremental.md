# ADR-0001 — Incorporación uniforme de apps, extractor SPA y mantenimiento incremental

**Estado:** Aceptada · **Fecha:** 2026-08-14 · **Versión:** 0.2.0

## Contexto

La etapa inicial (ADR-0000, v0.1.0) cubrió Frappe/ERPNext/HRMS con un pipeline que consume las salidas
oficiales de gettext y consolida un `locale/es.po` reproducible desde `review/*.csv`. Al incorporar
**Frappe Helpdesk** (y preparar CRM) surgieron necesidades nuevas:

1. Helpdesk y CRM son **SPA** (Vue) con textos marcados `__()` en `.vue` y **TypeScript** (`.ts/.tsx`).
2. Incorporar apps no debe duplicar scripts por app.
3. El baseline inicial revisa miles de cadenas, pero **el mantenimiento no puede repetir esa auditoría**
   cada vez que el upstream cambia unas pocas cadenas.
4. El catálogo `.po` es un **override plano** por `(msgctxt, msgid)`: un `msgid` sin contexto solo puede
   tener una traducción en todo el ecosistema.

## Decisión

1. **Cobertura SPA en el extractor común** (`scripts/extract_fresh_pot.py`), reutilizando extractores
   **oficiales** de Frappe (sin regex propio):
   - `.ts`/`.tsx` → `frappe.gettext.extractors.javascript.extract` (el mismo de `.js`). **Orden crítico:**
     estos patrones van **al final** del `method_map`; anteponerlos rompe la extracción de erpnext
     (`banking/`, `.tsx`).
   - `.vue` → wrapper que **compone** `html_template.extract` ∪ `javascript.extract` sobre cada bloque
     `<script>`, con offset de línea, dedup por `(funcname,msgid)` y filtro de literales con interpolación
     `${…}` (no traducibles estáticamente). Recupera backticks y llamadas `__()` multilínea que el
     extractor oficial de `.vue` omite.

2. **Registro único de apps** en `scripts/extract_config.json`: objetos
   `{app, upstream, branch, published, exceptions}`, leídos por los tres scripts. Incorporar una app =
   agregar un objeto; la lógica central no cambia. `build_po.py` publica al `.po` **solo** apps con
   `published: true` (gate explícito, sin listas paralelas).

3. **Baseline por manifiesto de punteros** (`working_docs/active/catalog_baseline.json`): por app,
   `upstream_rev` + hash del catálogo aprobado. **No** se duplican las traducciones; la fuente de verdad
   sigue siendo `review/*.csv`.

4. **Mantenimiento por delta** (`scripts/diff_upstream.py`, determinista, sin LLM): compara el universo
   fresco contra el CSV aprobado por `entry_key` y clasifica cada cambio (sin cambios / nueva / eliminada /
   cambio de contexto / plural / placeholders / posible rename). Solo las cadenas nuevas o cambiadas van a
   revisión lingüística; **no se re-auditan** las que no cambiaron.

5. **Convergencia global para claves Gettext compartidas:** cuando un `msgid` sin `msgctxt` aparece en
   varias apps, el `.po` exige una sola traducción. `build_po.py` **detiene** la generación ante
   traducciones divergentes (conflictos), que se resuelven eligiendo una forma global correcta para todos
   los contextos reales, documentada como convergencia deliberada.

## Consecuencias

- Incorporar CRM u otra app es un procedimiento estándar (config + revisión del delta), no scripts nuevos.
- El mantenimiento futuro revisa decenas de cadenas (el delta), no miles.
- La cobertura SPA sube de forma medible (Helpdesk: 86.2 % → 97.7 % de literales `__()`); quedan fuera,
  por diseño, las llamadas `__()` con argumento **dinámico** (no extraíbles por ningún gettext).
- La convergencia global puede requerir **cambios deliberados** en traducciones ya publicadas de otras
  apps cuando comparten una clave sin contexto; se documentan como tales (no accidentales).
- Restricción operativa: `buzola_translations` debe instalarse **al final** de `installed_apps` para que su
  `.mo` prevalezca (ver ADR-0000).

## Alternativas descartadas

- **Regex propio para SPA:** rechazado; se reutilizan los extractores oficiales de Frappe.
- **Copiar/duplicar el baseline de traducciones por app:** rechazado (riesgo de divergencia); el CSV es la
  única fuente de verdad y el baseline son solo punteros.
- **Re-auditar el universo completo en cada actualización:** rechazado por costo; se sustituye por el delta.
- **`msgctxt` inventado para separar usos de una misma clave:** inviable (el contexto lo define el código
  fuente); se opta por convergencia global.
