# PLAN — Revisión inicial completa de Helpdesk (baseline)

Reutiliza el **procedimiento estándar probado en etapa 2** (Frappe/ERPNext/HRMS). No inventa proceso nuevo.
Objetivo: crear el **baseline aprobado de Helpdesk** con el mismo rigor; después el mantenimiento usa solo
`diff_upstream.py`. **Nada de `.po/.mo`, `published:true`, instalar, desplegar ni `/ship` hasta autorizar.**

## A. Procedimiento estándar recuperado (evidencia etapa 2)
Dos etapas, ambas checkpointeadas y de bajo consumo de contexto:

**1) Revisión inicial por bloques (patrón `one_offs/acc/`):**
- `prep`: parte el bloque en chunks `<blk>_part<NN>.jsonl` (≤200 filas) = fila + evidencia de contexto.
- `glossary_<blk>.json`: msgid→término aprobado + términos cross-app (consistencia con lo ya aprobado).
- `INSTRUCTIONS_<BLK>.md`: encuadre de dominio + **estados** (`existente correcta`/`existente mejorable`/
  `traducción propuesta`/`igual al inglés válida`/`ambigua`/`conflicto de contexto`/`requiere revisión
  especializada`) + glosario + **preservación de placeholders** + autocontrol de desalineación + trazabilidad
  (`core`/`mx`) + salida `{ek,status,proposed,core,mx,hist_ref,hist_tr,notes}`, una por `entry_key`, con conteo.
- Cada subagente recibe **solo su chunk + glosario + instrucciones**; emite `decisions_part<NN>.jsonl`.
- Olas de ≤5–6 concurrentes; se persiste tras cada bloque; **resumible** vía `checkpoint.json`.
- `integrate_<blk>.py`: mergea `decisions_part*.jsonl` → CSV autoritativo (idempotente, `--status`/`--apply`),
  marca `human_authored=sí` + `review_status`. Luego `build_catalog.py` regenera y valida.
- Regla: **las traducciones upstream NO se aceptan automáticamente**; se juzgan.

**2) Auditoría global de consistencia (patrón `semantic_audit/`):**
- Paquete congelado neutral (`audit_input.csv` + `context_evidence.jsonl`, `audit_id` estable).
- Veredictos: `ACEPTAR`/`CAMBIAR`/`REQUIERE_CONTEXTO`/`NO_TRADUCIR` + `confianza` (alta/media/baja) +
  `alerta_consistencia` (sí/no+nota) + `contexto_faltante`.
- **Tabla terminológica** (`doctype_terminology_changes.csv`): `app,doctype_tecnico,es_actual,es_propuesta,
  entry_key,referencias,cambio_visible,impacto_cursos_docs,estado` → detecta familias/inconsistencias.
- Regla: la auditoría **produce candidatos automáticamente**; solo los señalados van a revisión humana
  detallada. **No** se reenvía todo el universo.

Validaciones técnicas (ya en `build_catalog.py`/`build_po.py`): identidad `entry_key`, filas==únicos==universo,
**pérdida de placeholder = build falla**, vocabulario de estados, round-trip por `human_authored`,
idempotencia (re-correr = hashes idénticos), y `diff_upstream.py` para el delta.

## B. Terminología protegida de Helpdesk (regla de negocio, decidida)
Criterio semántico (mismo que CRM `Lead`/`Deal`): se conserva en inglés lo que es **slang/vocabulario de
industria tech** cuya traducción resulta menos natural para el usuario MX. **Decididos:**
- `Ticket`/`Tickets` → **en inglés** (también en compuestos, salvo que la gramática ES exija otra construcción).
- `SLA`/`SLAs` → **en inglés**.

**NO** se generaliza. `Agent`, `Team`, `Assignment`, `Escalation`, `Customer`, `Contact`, etc. → **se traducen**
al español MX de forma natural, salvo evidencia concreta en la auditoría de que funcionan como nombre propio /
entidad técnica / término de industria (entonces se decide caso por caso, documentado).

## C. Plan de ejecución Helpdesk

### Fase 0 — Universo completo en el CSV (prerequisito, requiere autorización)
El `05_helpdesk.csv` actual (1 425 filas) es del universo viejo; falta lo recuperado por `.ts`+`.vue`.
- Correr `build_catalog.py` para **regenerar los CSV desde el universo fresco** (helpdesk 1 569): las filas
  humanas se preservan por `entry_key`; las nuevas entran como `sin traducción` para revisar.
- **VERIFICAR idempotencia (condición #11):** frappe/erpnext/hrms/crm — ninguna columna humana
  (`proposed_translation`, `status`, etc.) cambia; lo único aditivo permitido = backlog **frappe +6 / hrms +1**
  como `sin traducción`. Si cambia cualquier decisión aprobada → **DETENERSE y reportar** (no continuar).

### Fase 1 — Preparación (sin subagentes)
- `prep_hd.py`: parte `05_helpdesk.csv` + huérfanas/casos helpdesk de `06` en chunks `hd/hd_part<NN>.jsonl`
  (~180 filas → ~9–10 bloques) con fila + evidencia; escribe `hd/checkpoint.json`.
- `hd/glossary_hd.json`: (a) **protegidos** Ticket/SLA; (b) términos cross-app aprobados (Submit→Confirmar,
  Report→Reporte, Status→Estado, etc., extraídos del catálogo aprobado); (c) dominio Helpdesk propuesto
  (Agent→Agente, Team→Equipo, Assignment→Asignación, Escalation→Escalamiento, Customer→Cliente,
  Contact→Contacto, Knowledge Base→Base de Conocimiento…), sujeto a la auditoría.
- `hd/INSTRUCTIONS_HD.md`: dominio soporte/mesa de ayuda + estados + glosario + protegidos + placeholders.

### Fase 2 — Revisión inicial completa (subagentes por bloque)
- ~9–10 subagentes, olas de ≤5 concurrentes; cada uno **solo** su chunk + glosario + instrucciones.
- Evalúa y clasifica **todas** las filas (no retraduce a ciegas; detecta MT errors, falsos amigos, español
  peninsular impropio MX, literalidad, inconsistencias). Emite `decisions_part<NN>.jsonl`, conteo verificado.
- Persistir por bloque; `checkpoint.json` marca bloques terminados → **resume sin reprocesar**.

### Fase 3 — Integración + regeneración + validación técnica
- `integrate_hd.py --apply` → `05_helpdesk.csv` (idempotente). `build_catalog.py` regenera; valida identidad,
  placeholders (0 pérdidas), round-trip, idempotencia. `diff_upstream.py` confirma delta.

### Fase 4 — Auditoría global de consistencia (transversal, automática → candidatos)
- `audit_consistency_hd.py` (determinista, sin LLM) produce la **tabla de consistencia Helpdesk** y alertas:
  mismo término→traducciones distintas · conceptos relacionados incompatibles · **protegidos violados
  (Ticket/SLA)** · confianza media/baja (heurística) · posibles falsos amigos · inconsistencias
  singular/plural · mayúsculas semánticas · término técnico divergente entre módulos · traducciones
  sospechosamente literales · **choque con Frappe/ERPNext/HRMS** para el mismo concepto.
- **Solo los casos señalados** → revisión humana detallada (veredicto/confianza/alerta). Se integran las
  correcciones y se re-valida. No se reenvía todo el universo.

### Fase 5 — Cierre de excepciones / revisión especializada
- Bloque `06` helpdesk (`ambigua`/`conflicto`/`requiere revisión especializada`/huérfanas PO-only 97).
  Resolver los señalados; confirmar huérfanas.

### Fase 6 — Reporte ejecutivo (formato requerido) + validaciones finales
1. universo total revisado; 2. distribución por estado; 3. existentes aceptadas; 4. corregidas; 5. nuevas;
6. tabla de consistencia + nº de alertas; 7. decisiones terminológicas; 8. **confirmación Ticket/SLA
consistentes**; 9. casos de revisión especializada; 10. validaciones técnicas (placeholders/identidad/
round-trip/idempotencia); 11. **confirmación de que Frappe/ERPNext/HRMS/CRM no recibieron cambios humanos**.

## D. Diseño de bajo consumo (obligatorio)
Chunks ≤180 · subagente = chunk + glosario + instrucciones (nunca todo el catálogo) · persistir por bloque ·
resume por `checkpoint.json` sin reprocesar · concurrencia ≤5–6 · sin depender del contexto conversacional.
Tras el baseline, futuras actualizaciones = **solo** `diff_upstream.py` sobre el delta.

## E. No autorizado todavía
Generar/publicar `.po`/`.mo`; `published:true`; instalar/desplegar; `/ship commit|push|pr`. Se pedirá aparte.
