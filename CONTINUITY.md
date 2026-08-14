# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-14
**Rama activa:** `feat/etapa3-helpdesk-incremental` (rama de trabajo; `version-16` es la protegida)
**Tarea actual:** Etapa 3 — **Helpdesk publicado técnicamente en v0.2.0** (local, sin push/PR). `helpdesk`
con `published:true`; `es.po` regenerado (**19 605 entradas**, sha `da19befa…`, 0 conflictos, idempotente);
`.mo` compilado; precedencia validada (`buzola_translations` al final de `installed_apps`). **`/ship commit`
ejecutado en esta rama; pendiente `/ship push` y `/ship pr` a `version-16` (aún sin autorizar).**

---

## Recuperación rápida

**Etapa 2 (cerrada, mergeada):** catálogo español auditado de Frappe/ERPNext/HRMS, **v0.1.0**,
`locale/es.po` = 18 417 entradas. PR #3 mergeado → `f997df1` en `version-16`.

**Etapa 3 (en curso, esta rama):**
1. **Extractor común mejorado** (`extract_fresh_pot.py`): cobertura SPA `.ts/.tsx` + wrapper `.vue`
   (composición de extractores oficiales, sin regex propio; orden del `method_map` es crítico — ver
   comentario en el código: `.ts/.tsx` al final).
2. **Registro único** `extract_config.json` (objetos con `published`); `build_po.py` publica solo apps
   `published:true`; bloques por app (`05_helpdesk`, `07_crm`).
3. **Mantenimiento incremental** (`diff_upstream.py` + `catalog_baseline.json`): probado; futuras
   actualizaciones revisan solo el delta.
4. **Baseline lingüístico de Helpdesk: revisión inicial completa + auditoría de consistencia — APROBADO.**

---

## Baseline Helpdesk — cerrado (esta rama, sin publicar)

- **Universo:** `review/05_helpdesk.csv` = **1 569 filas**, 100 % `human_authored=sí` (revisado íntegro).
- **Distribución final:** `traducción propuesta` 708 · `existente correcta` 620 · `existente mejorable`
  181 · `igual al inglés válida` 60.
- **Terminología protegida:** `Ticket`/`Tickets` y `SLA`/`SLAs` en inglés (0 violaciones; se revirtieron
  25 casos `ANS`→`SLA` del upstream). `Feedback`→Comentarios; `Service Level Agreement`→"Acuerdo de Nivel
  de Servicio" (sigla SLA en inglés). Nombres DocType `HD …`: etiqueta traducida + sufijo "HD".
- **Registro:** normalizado al estándar del ecosistema (~97 % impersonal/usted; era 50/50 en la revisión
  inicial). Pase dirigido de 81 filas de registro + 37 `HD …` + 2 términos.
- **Consistencia final (auditoría re-ejecutada):** 71 alertas → 0 protegidos violados; **14
  `crossapp_divergente` = 7 divergencias legítimas de Helpdesk** (Submit→Enviar, Hold→En espera,
  Primary→Principal, Ringing→Sonando, Change→Cambiar, Mention→Mención, Holiday List→días festivos) **+ 7
  solo mayúsculas** (se conservan); el resto (glosario_desviado/falso_amigo) son falsos positivos.
- **Validaciones:** 0 pérdida de placeholders · identidad `entry_key` sin colisiones · **2ª regeneración
  byte-idéntica (idempotente)** · Frappe/ERPNext/HRMS/CRM **IGUAL desde Fase 0** (0 cambios humanos
  accidentales; único aditivo autorizado: frappe +6, hrms +1 `sin traducción`, backlog).
- **Estado:** **lingüísticamente aprobado, NO publicado** (sigue `published:false`).

Artefactos del baseline (en `one_offs/hd/`, gitignored): `glossary_hd.json`, `INSTRUCTIONS_HD.md`,
`hd_part01..09.jsonl` + `_results`, `hd_fix*`, `checkpoint.json`. Tabla de consistencia:
`working_docs/active/helpdesk_consistency.csv`.

---

## Pendiente (requiere autorización explícita, por paso)
1. **Publicación Helpdesk:** `published:true` → `build_po.py` regenera `es.po` → `bench compile-po-to-mo`
   → validar precedencia (`check_translation_order`) → `/ship` (commit → push → PR a `version-16`).
2. **CRM:** mismo procedimiento (universo 1 949; +26 `.vue`; sin gap `.ts`).
3. **Backlog frappe (+6) / hrms (+1):** folding en su próximo ciclo.

## No repetir / cuidados
- **NO reordenar `ts_methods`** en `extract_fresh_pot.py` (debe ir al final; antes rompe erpnext −358).
- La regeneración de `build_catalog` normaliza `status` (correcta↔mejorable) para hacerlo coherente con
  `current`/`proposed`; **no cambia traducciones** y `es.po` no se afecta (ambos elegibles).
- No versionar `.mo` ni `working_docs/active/semantic_audit/` ni `client_translation_impact/`.
- El `.po` se **genera** desde los CSV; no se edita a mano.

## Archivos relevantes ahora
- `working_docs/active/PLAN_etapa3.md`, `PLAN_helpdesk_review.md` (procedimiento y cierre).
- `working_docs/active/helpdesk_consistency.csv`, `catalog_baseline.json`, `inventario_cobertura.csv`.
- `scripts/`: `extract_fresh_pot.py`, `diff_upstream.py` (+test), `build_catalog.py`, `build_po.py`,
  `extract_config.json`.

## Información faltante
- Fecha/autorización de la fase de publicación de Helpdesk.
- Alcance/plazo de la revisión de CRM.
