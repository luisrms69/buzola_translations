# PLAN — Etapa 2: catálogo completo de revisión + precedencia

Plan de trabajo activo. Fuente rectora: `frappe-infrastructure/projects/buzola_translations/plan-rector.md`.
No publicable. Esta etapa produce el **catálogo completo** (todo el universo POT/PO) para una **segunda
revisión humana por bloques**. No genera aún `locale/es.po` ni `.mo`.

## Entorno real (2026-08-02)
| App | Versión | Rama | Commit | main.pot | es.po |
|---|---|---|---|---|---|
| frappe | 16.26.3 | version-16 | 4113465 | sí | sí |
| erpnext | 16.27.0 | version-16 | 9d5c760 | sí | sí |
| hrms | 16.12.2 | version-16 | c703255 | sí | sí |
| helpdesk | 1.28.1 | main | 7b4b400 | sí | sí |
| crm | 2.0.0-dev | develop | 2752c85 | sí | sí |
Repos de terceros **limpios** antes y después (0 modificaciones).

## Fuente y mecanismo (oficial, no reinventado)
- Verdad = `<app>/<app>/locale/main.pot` (universo) y `es.po` (traducciones) — salida de
  `bench generate-pot-file` / `create-po-file` / `update-po-files`. Se **consumen en lectura** con
  `babel` (misma librería que Frappe). **No** se ejecutó `generate-pot-file` (escribiría en las apps).
- Comandos oficiales revisados (ayuda real): `generate-pot-file`, `create-po-file`, `update-po-files`,
  `compile-po-to-mo`, `migrate-csv-to-po`. Solo se usó lectura de `.pot`/`.po`.
- Scripts (`scripts/`): `extract_fresh_pot.py` (extractor oficial config-driven + manifiesto) y
  `build_catalog.py` (universo → 6 CSV + inventario). Ninguno descubre cadenas. **La capa humana ya
  NO vive en código:** `human_decisions.py` fue **retirada** (movida a `one_offs/`, gitignored) tras
  migrar sus decisiones a los CSV. **Los 6 CSV son la fuente humana autoritativa.**
- **Configuración ÚNICA de apps:** `scripts/extract_config.json` (apps + directorio de salida). **Ambos**
  scripts leen de ahí; `build_catalog.py` **no** tiene lista hardcodeada. Añadir una app = editar el JSON;
  la lógica central no cambia. El generador valida: ≥1 app, sin duplicados, que **todas** las apps de config
  aparezcan **exactamente una vez** en el manifiesto, que el manifiesto **no** traiga apps inesperadas, y que
  cada app tenga repo, artefacto fresco y `es.po` cuando corresponda.

### Comandos exactos (reproducibles)
```bash
# 1) Extracción oficial fresca → <repo>/.artifacts/freshpot/<app>.jsonl + manifest.json (NO versionado).
#    Config-driven, fail-fast: si una app no extrae, overall_ok=false y no imprime EXTRACT_FRESH_OK.
echo "exec(open('.../scripts/extract_fresh_pot.py').read())" | bench --site <site> console
# 2) Catálogo desde el universo fresco (+ es.po) → 6 CSV + inventario.
#    Valida manifiesto (existencia + SHA256 + commit == HEAD) ANTES de generar; escritura atómica.
env/bin/python apps/buzola_translations/scripts/build_catalog.py \
  --review-dir apps/buzola_translations/review \
  --inventory-out apps/buzola_translations/working_docs/active/inventario_cobertura.csv
#    (--fresh-dir por defecto = <repo>/.artifacts/freshpot; --nonmigrable-out para el reporte de bootstrap)
```

### Reproducibilidad y fail-fast (integridad)
- **Extractor:** apps/salida por `extract_config.json` (sin rutas absolutas de la máquina; el repo se
  localiza con `frappe.get_app_path`). Limpia solo sus artefactos previos. Ordena por `(ctx,msgid)`.
  Manifiesto con `app, versión, rama, commit, count, sha256` por artefacto + `overall_ok`.
- **Generador (gates duros, exit≠0):** rechaza manifiesto ausente / `overall_ok=false` / SHA256 distinto /
  commit del artefacto ≠ HEAD actual (artefacto viejo). Falla ante colisión de `entry_key`, filas
  duplicadas, estado fuera del vocabulario, propuesta humana que **pierde un placeholder** del origen, o
  reconciliación incorrecta (`filas ≠ entry_key únicos ≠ Σuniverso`). Genera en `.tmp_build/` y solo
  **reemplaza** los CSV si todas las validaciones pasan (sin escrituras parciales). Orden de filas
  estable `(app, msgctxt, msgid)` → **ejecución repetible sin cambios de diff** (verificado: re-correr
  con fuente CSV produce hashes idénticos).

## Verificación de la extracción oficial (tarea 2)
**Objetivo:** confirmar que el `main.pot` versionado es completo/vigente vs una extracción oficial nueva.
- **Aislamiento con worktree: NO viable.** Los extractores oficiales (navbar/doctype) resuelven rutas
  con `frappe.get_app_path` y **no son relocalizables**: extraer sobre un worktree en `/tmp` aborta con
  `ValueError: '...hooks.py' is not in the subpath of '<bench>'`. Reimplementar el extractor está prohibido.
- **Método usado:** extracción **oficial en memoria** (`babel.extract_from_dir` + `method_map` de
  `babel_extractors.csv` + filtro gitignore oficial `get_is_gitignored_function_for_app` +
  `ignore_translatable_strings_from`) sobre el **árbol REAL** de cada app (limpio, en HEAD) **sin escribir
  POT** → solo lectura, sin modificar repos (0 sucios antes/después). Script: `scripts/extract_fresh_pot.py`,
  ejecutable con `bench --site <site> console`.
- **Resultado por app** (POT versionado vs extraído fresco; claves `(msgctxt,msgid)`; con filtro gitignore oficial):

  | App | versionado | extraído | coincid | nuevas | ausentes | Estado |
  |---|---|---|---|---|---|---|
  | frappe | 6180 | 6182 | 6180 | 2 | 0 | **completo y vigente** |
  | erpnext | 9985 | 10002 | 9982 | 20 | 3 | prácticamente completo |
  | hrms | 2229 | 2244 | 2228 | 16 | 1 | prácticamente completo |
  | crm | 1781 | 1924 | 1780 | 144 | 1 | **POT desactualizado** (faltan ~144) |
  | helpdesk | 1317 | 1426 | 1201 | 225 | 116 | **POT notablemente stale** |

- **Conclusión:** el `main.pot` versionado es **completo y vigente para frappe/erpnext/hrms** (nuevas ≤20,
  ausentes ≤3, diferencias = strings añadidos tras la última generación). **NO se declara cobertura
  completa para `crm` (+144) ni `helpdesk` (+225/−116):** su POT versionado está **desactualizado** vs el
  código actual (apps de frontend en `develop`/`main`; ejemplos de "nuevas" reales: helpdesk *"First
  Response"*, *"Invite"*; crm *"No Website"*, *"Max Depth"*). El catálogo de esta etapa, construido desde
  el POT versionado, **omite** esas ~369 cadenas nuevas de crm+helpdesk.
- **Recomendación (NO ejecutada, requiere autorización):** regenerar el POT oficial de `crm` y `helpdesk`
  (`bench generate-pot-file --app crm|helpdesk`, que **escribe** en esos repos) y re-correr `build_catalog.py`
  para incorporar sus cadenas nuevas; o tratar los deltas frescos como entradas adicionales. Las 116
  "ausentes" de helpdesk son cadenas del POT que ya no están en el código (candidatas a huérfanas).
- **Caveats:** el `UnicodeDecodeError` de frappe del primer intento se debía a un archivo no-UTF-8 en un
  directorio gitignored; el filtro oficial lo excluye (por eso frappe ahora extrae limpio). Una
  verificación byte-exacta definitiva requeriría `bench generate-pot-file` in-place (modifica repos) →
  requiere autorización.

## Universo, identidad y reconciliación (universo FRESCO)
- **Universo PRINCIPAL = extracción oficial FRESCA** (`extract_fresh_pot.py` → `/tmp/bt_freshpot/<app>.jsonl`,
  artefacto NO versionado) **∪ `es.po`**. El `main.pot` versionado **ya no** es el universo (solo sirvió
  para medir deriva; no se escribió ni reemplazó ningún POT en las apps).
- **Entrada única** = par `(msgctxt, msgid)`. Varias referencias `#:` del mismo `msgid` **no** duplican.
- **`entry_key` (corregido):** hash SHA1[:16] de **JSON canónico con claves ordenadas**
  `{"app","msgctxt","msgid","msgid_plural"}` (incluye `msgid_plural`; delimitación estructurada, no
  concatenación). Estable, reproducible, independiente de la fila.
- **Cobertura verificada:** filas escritas **22 064** = `entry_key` únicos **22 064** = universo
  **22 064** (Σ `pot_fresco` 21 778 + Σ `PO-only` 286). **Sin entradas perdidas ni duplicadas.**
  Todas las entradas del POT fresco quedan asignadas a un bloque.
- **Recuento fresco por app** (POT fresco / PO / traducidas-en-POT / sin-trad en PO / POT-only / PO-only):
  frappe 6182/5902/**5169**/630/404/124 · erpnext 10002/9978/**7773**/2201/29/5 · hrms 2244/2172/**813**/1351/112/40 ·
  helpdesk 1426/1315/**808**/432/227/116 · crm 1924/1781/**673**/1107/144/1.
  **TOTAL** POT 21 778 / PO 21 148 / trad-en-POT 15 236 / POT-only 916 / PO-only 286.
- **Separación de universos:**
  - **POT-only** (fresco sin PO): en el universo vigente pero sin entrada en `es.po` → `sin traducción`.
  - **PO-only** (`es.po` sin POT fresco, **286**): **`po_huérfana_o_obsoleta`**, ruteada al bloque 06 para
    auditoría; **queda fuera** de la generación automática de `es.po` mientras no se apruebe expresamente.
    Solo con evidencia en el código v16 una entrada podría promoverse a `texto no extraíble`.
  - El catálogo principal se reconcilia contra el **POT fresco**; las huérfanas quedan separadas.

### POT-only vs PO-only (identidad de conjuntos, universo FRESCO)
- **Resta naive:** `|POT| − |PO|` = 21 778 − 21 148 = **630**. Supone `PO ⊆ POT` (falso).
- **Conjuntos:** `|POT \ PO|` = **916** (`missing_from_po`, POT-only) y `|PO \ POT|` = **286** (PO-only).
  Identidad: `|POT|−|PO| = |POT\PO| − |PO\POT|` → `630 = 916 − 286`. Misma clave `(msgctxt, msgid)`
  (contexto distinto = clave distinta; sin dobles por referencias múltiples).

## Inventario de cobertura (`working_docs/active/inventario_cobertura.csv`)
**Cobertura contra el universo VIGENTE (POT), sin inflar con huérfanas.** Métricas por app + **fila
TOTAL** verificable:
- `pot_entries` / `po_entries` = claves únicas en POT fresco / en `es.po`.
- `translated_in_pot` = en POT **y** en PO **y** `msgstr`≠∅ (numerador de cobertura vigente).
- `untranslated_in_pot` = `pot_entries − translated_in_pot`; `untranslated_in_po` = en PO con `msgstr`=∅.
- `missing_from_po` = POT-only (en POT, ausente del PO); `po_only_orphan` = PO-only (en PO, ausente del POT).
- `translated_po_only` = PO-only con `msgstr`≠∅ (**NO** cuenta como traducción del POT vigente).
- `equal_to_source_in_pot` = en POT con `msgstr==msgid`.
- `coverage_pot_percent` = `translated_in_pot / pot_entries` (**cobertura del universo vigente**).
  `coverage_po_percent` = `(translated_in_pot + translated_po_only) / po_entries` (proporción de `es.po`
  con traducción, huérfanas incluidas — métrica de estado del PO, **no** de cobertura vigente).
- **Control:** frappe `translated_in_pot`=5169 / `pot_entries`=6182 = **83.6 %** (antes 85.3 % inflaba con
  103 huérfanas traducidas). TOTAL: `cov_pot`=**70.0 %**, `cov_po`=72.9 %.
- La fila **TOTAL** suma conteos y recomputa cobertura desde los numeradores/denominadores agregados.

## Distribución en 6 bloques (todos los CSV en `review/`, UTF-8)
| Bloque | Filas | Contenido |
|---|---|---|
| `01_frappe_plataforma.csv` | 6182 | Frappe (plataforma/UI/permisos/workflow) |
| `02_erpnext_operaciones.csv` | 6504 | ERPNext ventas/compras/inventario/manufactura/proyectos |
| `03_erpnext_contabilidad_finanzas.csv` | 3495 | ERPNext accounts/assets/regional (contable/fiscal MX) |
| `04_hrms.csv` | 2243 | HRMS RRHH/nómina |
| `05_helpdesk_crm.csv` | 3348 | Helpdesk + CRM |
| `06_conflictos_historico_especializada.csv` | 292 | ambigua/conflicto/especializada + huérfanas PO-only (286) |
| **Total** | **22 064** | cada entrada en **un** bloque; ninguna app queda fuera |

## Estados (vocabulario controlado) — distribución (universo fresco, estados NORMALIZADOS)
`pendiente de segunda revisión` 14 795 · `sin traducción` 6 527 · `po_huérfana_o_obsoleta` 286 ·
`igual al inglés requiere revisión` 215 · `igual al inglés válida` 142 · `existente correcta` 43 ·
`existente mejorable` 36 · `traducción propuesta` 14 · `conflicto de contexto` 2 · `ambigua` 2 ·
`requiere revisión especializada` 2. (`texto no extraíble` automático = 0.)
`review_status`: `pendiente de segunda revisión` 21 964 · `revisado (muestra etapa 2)` 100.
- **Normalización (integridad):** el estado humano se recalcula para ser coherente con
  `current_translation` / `proposed_translation`: actual≠∅ y sin propuesta (o propuesta==actual) →
  `existente correcta`; actual≠∅ y propuesta distinta → `existente mejorable`; actual=∅ y propuesta≠∅ →
  `traducción propuesta`; actual=∅ sin propuesta → `sin traducción`. **Prevalecen cuando el humano los
  fija:** `ambigua`, `conflicto de contexto`, `requiere revisión especializada` (y `específica de
  México/cliente`, `candidata a core`). Esto corrigió ≥10 estados de Frappe (p. ej. `Save/Submit/Print/
  Rename/Duplicate/Draft/Email/Report` → `traducción propuesta` porque el `es.po` actual está vacío;
  `Attach/Yesterday` → `existente correcta`).
- **No** se declara "correcta" por no estar vacía: las traducidas sin decisión humana quedan
  `pendiente de segunda revisión`. **No** se declara "incorrecta" por ser igual al inglés: se separa en
  `igual al inglés válida` (heurística: siglas/códigos/números, p. ej. `API`, `ASC`, `0-30`) vs
  `igual al inglés requiere revisión`. La heurística prioriza; la clasificación final la valida el humano.

## Revisión humana de Frappe — CERRADA (bloques 1–3)
Las 6 306 entradas de Frappe (6 182 POT + 124 PO-only) quedaron **revisadas** (`human_authored=sí`):
- Bloque 1 (`revisado segunda revisión Frappe 1`): 52 decisiones puntuales.
- Bloque 2 (`revisado segunda revisión Frappe 2`): 121 propuestas.
- Bloque 3 (`revisado segunda revisión Frappe 3`): 5 988 activas + 124 PO-only auditadas.
- Muestra etapa 2 preservada: 21. **Total preservadas de rondas previas: 194.**

Distribución final Frappe (tras corrección de cierre): `existente correcta` 3 400 · `existente mejorable`
1 610 · `traducción propuesta` 994 · `igual al inglés válida` 172 · `po_huérfana_o_obsoleta` 117 ·
`texto no extraíble` 7 (con propuesta, aprobadas para generación local) · `conflicto de contexto` 2 ·
`requiere revisión especializada` 4. Corrección de cierre: 3 asignaciones equivocadas de fusión
reparadas; 10 filas movidas de `igual al inglés válida` a estado correcto (la propuesta traducía o
cambiaba el texto); 7 `texto no extraíble` completadas con propuesta.
Ninguna fila Frappe queda en `sin traducción` / `igual al inglés requiere revisión` /
`pendiente de segunda revisión`. Placeholders: 0 propuestas con pérdida.

**Dos refinamientos del generador** (para respetar decisiones humanas):
- `igual al inglés válida` ahora **prevalece** (no se recalcula a `existente correcta`).
- Una PO-only auditada puede fijarse como `texto no extraíble` (visible en código pero no capturada
  por el extractor, con evidencia `file:line`); las demás siguen `po_huérfana_o_obsoleta`.

## Revisión humana de ERPNext OPERACIONES — CERRADA (bloque 02)
6 495 filas revisadas (`revisado segunda revisión ERPNext operaciones`): 6 492 activas del bloque 02 +
3 huérfanas de operaciones del bloque 06. Preservadas 15 decisiones previas (muestra etapa 2); 2 huérfanas
de contabilidad del bloque 06 quedan **sin tocar** (fuera de alcance). Distribución: `existente correcta`
4 344 · `traducción propuesta` 1 575 · `existente mejorable` 507 · `igual al inglés válida` 64 ·
`po_huérfana_o_obsoleta` 3 · `requiere revisión especializada` 1 · `ambigua` 1. 2 filas movidas a bloque 06
(`title` ambigua; `Purchase Expense Contra Account` especializada). Terminología canónica MX aplicada
(Item→Artículo, Warehouse→Almacén, Stock Entry→Movimiento de Inventario, Submit→Confirmar, Lead→Prospecto,
etc.). Solo cambiaron los CSV 02 y 06; Frappe, contabilidad/finanzas (03), HRMS, Helpdesk y CRM intactos.

**Corrección focalizada (sin subagentes):** 162 filas corregidas — 41 asignaciones exactas + 21 explícitas
con género (`Vale de Trabajo`, `Movimiento de Inventario`, `Amount`→Importe) + ~100 por auditoría dirigida:
`submit`→confirmar (no "validar"), `Report`→Reporte (no "Informe"), `coste`→costo, `Item`→Artículo (de
elemento/ítem), `Pick List`→Lista de Surtido, ortografía. Residuales verificados = 0.

**Terminología CRM (corrección posterior, 71 filas):** las entidades CRM `Lead`/`Leads` y `Deal`/`Deals`
se **conservan en inglés** (anglicismos adoptados = nombres de DocType); `Prospect`=Prospecto,
`Opportunity`=Oportunidad. Se revirtió `Lead`→Prospecto/Cliente potencial en 38 filas (solo `Lead Time`
se traduce → "plazo de entrega"). `Job Card` normalizado a **Vale de Trabajo** (0 `ficha`/`tarjeta`).
Verificado: 0 `Lead` de CRM como cliente potencial/prospecto/iniciativa/oportunidad; Deal=Deal.

## Revisión humana de ERPNext CONTABILIDAD/FINANZAS — CERRADA (bloque 03)
3 472 filas revisadas (`revisado segunda revisión ERPNext contabilidad finanzas`): 3 470 activas del
bloque 03 + 2 huérfanas de contabilidad del bloque 06. Preservadas 25 decisiones previas (muestra etapa 2).
Distribución final block03 (tras corrección): `existente correcta` 1 662 · `existente mejorable` 1 185 ·
`traducción propuesta` 629 · `igual al inglés válida` 19 (= 3 495). Corrección focalizada (67 filas): Write Off
→**ajuste/castigo** (no cancelación), Submit→Confirmar, TDS **no** se localiza a ISR, `Tax Id`→Identificación
fiscal (no RFC), Party→tercero, `Periodo/Numero`→Período/Número, LPO resuelto (`Customer LPO`→"LPO del cliente",
sale de especializada y vuelve a accounts/03). Auditoría `mexico_specific`: de 22 quedan **2** (Régimen Fiscal,
Forma de Pago SAT); se quitó la marca a 20 (contenido genérico o regional India/EAU/Italia/Sudáfrica).
Terminología contable MX aplicada (Journal Entry→Asiento Contable,
Debit/Credit→Debe/Haber, General Ledger→Libro Mayor, Amount→Importe, Party→Tercero, Write Off→Cancelación,
Cost Center→Centro de Costos, Profit and Loss→Estado de Resultados, etc.). **Método:** checkpointeado —
18 subagentes (4 waves, ≤5 simultáneos, ≤195 filas c/u), integrando y persistiendo al CSV tras cada wave
(reanudable sin reprocesar). Solo cambiaron los CSV 03 y 06; Frappe, ERPNext operaciones, HRMS, Helpdesk
y CRM intactos.

## Revisión humana de HRMS — CERRADA (bloque 04)
2 269 filas revisadas (`revisado segunda revisión HRMS`): 2 229 activas del bloque 04 + 40 PO-only del
bloque 06. Preservadas 14 decisiones previas (muestra etapa 2) + `Sick Leave` (especializada). Distribución:
`traducción propuesta` 1 414 · `existente correcta` 447 · `existente mejorable` 334 · `po_huérfana_o_obsoleta`
36 · `igual al inglés válida` 31 · `texto no extraíble` 4 (SPA Vue de HRMS, con evidencia `file`) ·
`requiere revisión especializada` 2 · `ambigua` 1. 3 filas movidas al bloque 06.

**Corrección focalizada (113 filas):** términos normalizados — Journal Entry→Asiento Contable,
Submit→Confirmar, Reports→Reportes, Earning→Percepción, Accrual→Devengo, Arrear→Retroactivo, Encashment→Pago
de ausencias, Loan Repayment→Pago de préstamo, Benefit Claim→Reclamación, Income Tax Slab→**Tarifa de ISR**,
Employee Checkin→Registro de Entrada/Salida (sin check-in/checada), Full and Final→Finiquito, `Periodo`→`Período`,
Amount→Importe. 4 `texto no extraíble` con propuesta (SPA Vue); 2 especializadas resueltas → bloque 04.
Auditoría `mexico_specific`: de 26 quedan **16** (ISR, percepciones/deducciones, finiquito, seguro de gastos
médicos, aportaciones patronales); se quitó la marca a decisiones de español general. Total HRMS = 2 284
(2 242 en bloque 04 + 42 en bloque 06). Terminología laboral MX
(Leave→Ausencia, Payroll→Nómina, Salary Slip→Recibo de Nómina, Job Applicant→Candidato, Employee
Checkin→Registro de Entrada/Salida, Expense Claim→Reembolso de Gastos); se corrigieron errores de máquina
frecuentes (Slab→"Losa"→Tramo; Leave verbo "Dejar"→sustantivo Ausencia; relieving→"alivio"→baja).
**Método:** 6 subagentes (1 wave, ≤6 simultáneos, ~372 filas c/u) + auditoría PO-only local por grep;
integración y persistencia al CSV. Solo cambiaron los CSV 04 y 06; Frappe y ambos ERPNext, Helpdesk y CRM intactos.

## Términos ambiguos y conflictos
Bare `Leave/Return/Posting/Issue/Shift/Claim/Entry` sin decisión humana → `ambigua` (bloque 06). Los
conflictos analizados en la muestra (p. ej. `Leave`→"Salir"→**Ausencia**; `Return`→"Retornar"→**Devolución**;
`Shift`→"Cambio"→**Turno**) van con `conflicto de contexto`. Regla: significados incompatibles → una fila
por uso funcional + `msgctxt`; **nunca** traducción global forzada.

## Columnas del catálogo (40, semántica separada)
- **Identidad/universo:** `entry_key` (`app:`+SHA1[:16] de JSON canónico `{app,msgctxt,msgid,msgid_plural}`),
  `app`/`origin_app`, `source_text`/`msgid`/`msgid_plural`/`msgctxt`.
- **Ubicación técnica (separadas, NO se intercambian):** `module` = módulo técnico real de la app
  (parts[1] de la ruta; **ignora rutas de test/cypress** para el primario y elige el módulo más frecuente),
  `all_modules` = todos los módulos de **todas** las referencias, `cross_module` = `sí` cuando la cadena es
  transversal a >1 módulo. `functional_domain` = dominio funcional de revisión (humano, o mapeado del
  módulo). `doctype_or_view`, `source_kind`, `source_reference` (POT, 1ª), `all_source_references` (todas),
  `po_reference` = referencias **del `es.po`** (no copia del POT).
- **Contexto legible:** `context` (explicación funcional), `field_or_action` (tipo de elemento visible),
  `user_role`. Se rellenan aprovechando los **comentarios oficiales del extractor** (nombre de DocType,
  label, opción, descripción, tipo de campo), preservados crudos en `extracted_comments` (JSON).
- **`flags`** = **solo flags Gettext reales** (de `es.po`, p. ej. `python-format`); los comentarios ya
  **no** contaminan esta columna.
- **Traducción:** `current_translation`(+plural), `proposed_translation`(+plural).
- **Placeholders:** `placeholders_source` / `placeholders_current` / `placeholders_proposed` /
  `placeholder_status` (ver abajo).
- **Estado/revisión:** `status`, `review_status`, `human_authored` (marca de fila humana → round-trip),
  `core_candidate`, `mexico_specific`, `client_specific`, `human_notes` (nota humana), `notes` (auto).
- **Trazabilidad histórica (columnas humanas, vacías por defecto):** `historical_reference`,
  `historical_translation` — se pueblan solo en la 2ª revisión con evidencia v15/`es-MX`.

## Placeholders (detección y comparación — clasifica, NO corrige)
- **Gramática estricta (sin falsos positivos):** llave Python VÁLIDA = `{}` | `{campo(.attr|[idx])*(!conv)?(:spec)?}`
  (`{0}`, `{name}`, `{0:.2f}`, `{name!r}`); se **normaliza** `{0:.2f}`→`{0}`, `{name!r}`→`{name}`. **No** se
  cuentan objetos/JSON (`{"label"}`, `{"status" }`), CSS (`{ padding }`) ni bloques de código. En `%`-format
  se exige conversor válido sin espacio tras `%` (`%s`/`%d`/`%.2f`/`%(x)s`), por lo que texto natural como
  `Use % for…` o `50% de` **no** se detecta. También JS `${name}`, Jinja `{{ var }}`/`{% … %}`. Los flags
  Gettext reales (`python-format`) quedan en la columna `flags` como refuerzo.
- **Corrección aplicada:** la regex anterior marcaba cualquier `{…}`/`% x` → **26 tokens falsos positivos
  en 23 filas eliminados** (ejemplos: `{"label"}`, `{ padding }`, `{#####}`, bloques Jinja).
- **Señal verificable:** `placeholders_source` / `placeholders_current` / `placeholders_proposed` +
  `placeholder_status` con **pérdida/extra** origen→actual y origen→propuesta.
- **Pérdidas reales tras la corrección = 4** (frappe 3, erpnext 1), incluidos los tres priorizados:
  `…field {4}` → *actual pierde {4}*; `Added default log doctypes: {}` → *actual pierde {}*;
  `Cannot set Notification…{0}…{1}` → *actual pierde {1}*; (+ erpnext `Item {} does not exist.` → `{}`↔`{0}`).
  Se **clasifican** para revisión; no se tocan traducciones. Una **propuesta humana** que perdiera un
  placeholder **falla el build** (hoy 0).

## Capa humana invertida — los CSV son autoritativos (integridad)
- `human_decisions.py` **retirada** (a `one_offs/`). El generador lee las columnas humanas de los CSV
  existentes (`human_authored=sí`) por `entry_key` (respaldo: identidad Gettext completa) y las preserva
  entre regeneraciones. **Las heurísticas nunca sobrescriben** una decisión humana.
- **Migración por identidad exacta**, nunca por `msgid` a secas → sin propagación a otros contextos.
- **Decisiones no migrables (15/115):** persistidas en `working_docs/active/decisiones_no_migradas.csv`
  con columna `classification`: **7 `no_existe_msgid_exacto`** (no existen como `msgid` exacto en ninguna app)
  y **8 `cross_app_pendiente_validacion`** (el string vive en **otra app** — p. ej. `Employee`/`Timesheet`/
  `Shift` bajo `hrms` viven en `erpnext`). Las 8 cross-app **NO se migran automáticamente**: quedan
  pendientes de validar su contexto en la app donde realmente existe la cadena. No se inventan propuestas.

## Referencias históricas (v15/es-MX) — secundarias
Disponibles en `frappe-bench-v16/frappe-bench/apps/` (rama `version-15`): erpnext `es.csv`, hrms
`es.csv`+`es-MX.csv`, frappe `es-MX.csv`. Uso: detectar regresión / terminología MX / cambios de `msgid`.
**No** son fuente de verdad, **no** se copian automáticamente, **no** se convierten en `es_MX.po`. Las
columnas **`historical_reference`/`historical_translation`** están **presentes y vacías por defecto** y se
tratan como columnas humanas (round-trip); se poblarán **solo** durante la 2ª revisión cuando una
referencia v15/`es-MX` aporte evidencia útil (sin volcado masivo).

## Textos visibles NO marcados (`_()`/`__()`)
No aparecen en el catálogo oficial. Requieren **auditoría de código dedicada** (grep de cadenas
hardcodeadas con archivo/referencia/razón). Quedan **separados** del catálogo normal; se incorporarán
al bloque 06 solo con evidencia concreta. Pendiente para una iteración posterior.

## Orden de carga y precedencia (evidencia código v16)
- `frappe/boot.py:220 load_translations` → `get_messages_for_boot` → `frappe/translate.py:135
  get_all_translations`.
- `translate.py:172-181 get_translations_from_apps`: itera `frappe.get_installed_apps(_ensure_on_bench=True)`
  (línea 179) y por cada app aplica `translations.update(get_translations_from_csv)` (180) y luego
  `translations.update(get_translations_from_mo)` (181). **`.update()` → la ÚLTIMA app en el orden gana;
  dentro de una app, `.mo` (compilado del `.po`) prevalece sobre `.csv`.**
- Orden de apps = `get_installed_apps` (`frappe/__init__.py:924-938`): lee `installed_apps` del **DExtra
  de la BD del sitio** (línea 936, `db.get_global("installed_apps")`), filtrado por presencia en bench.
  **Depende del orden de instalación en la BD, NO de `apps.txt`.**
- `.mo`: `gettext/translate.py:348 get_translations_from_mo` → `gettext.find(app, locale_dir, (lang,))`
  (365) carga `sites/assets/locale/<lang>/LC_MESSAGES/<app>.mo`; `compile_translations` (250) lo genera.
- Sin `msgctxt`: la clave es el `msgid` a secas; con `msgctxt` la clave es `"msgid:context"`
  (`get_translation_dict_from_file`), por lo que contexto distinto = entrada distinta (no colisiona).
- DocType `Translation` (BD): `get_user_translations` (221) se aplica **después** de las apps
  (`get_all_translations:156-158`) → sobrescribe todo. `buzola_translations` **no** lo usa.
- Caché: `MERGED_TRANSLATION_KEY` (29); `clear_cache` (239-242) limpia bootinfo + user + merged.

### Precedencia — análisis separado (no basta "instalar al final")
**Comportamiento actual observado:** en `<site>` con buzola instalada al final, su `.mo` se aplicó en
último lugar y sobrescribió cadenas de erpnext/hrms (ADR-0000: sobrescribe, persiste, revierte).

**Condición necesaria para que la sobrescritura funcione:** (1) `buzola_translations/locale/es.po`
con el `msgid`/`msgctxt` exacto; (2) compilado a `.mo` (`bench compile-po-to-mo --app buzola_translations`);
(3) buzola **presente en `installed_apps` del sitio DESPUÉS** de las apps cuyas cadenas sobrescribe;
(4) caché limpiada (`clear-cache`).

**Qué ocurre al instalar otra app después:** `install-app` **agrega** la nueva app al final de
`installed_apps` → quedaría **después** de buzola y sus traducciones ganarían para los `msgid` en común
→ buzola **perdería** precedencia sobre esa app. (Riesgo real.)

**Qué ocurre durante `bench update`:** recompila `.mo` de cada app desde su `.po` y reconstruye assets,
pero **no** reordena `installed_apps` → el orden relativo se conserva; buzola mantiene precedencia si
seguía siendo la última. Los `.po`/`.mo` de buzola viven en su repo/assets; `bench update` de terceros
**no** los revierte.

**Cómo verificar automáticamente la precedencia (solo lectura, sin BD de escritura):**
```
bench --site <site> execute frappe.get_installed_apps
# válido si  installed_apps[-1] == "buzola_translations"  (o buzola después de {frappe,erpnext,hrms,helpdesk,crm})
```
Un check idempotente compararía el índice de `buzola_translations` contra el de cada app objetivo en
`installed_apps`; si alguna app objetivo aparece **después**, el orden es inválido.

**Mecanismo mínimo para detectar/corregir un orden inválido (a evaluar, NO implementar sin autorización):**
- **Detección:** script/CI que lea `installed_apps` por sitio y falle si buzola no está tras las apps
  objetivo. Sin cambios en terceros.
- **Corrección (opciones soportadas por Frappe, a evaluar):** (a) **reinstalar buzola al final** tras
  instalar/actualizar cualquier app objetivo (`uninstall-app` + `install-app buzola_translations`) — la
  reubica al final de `installed_apps`; (b) evaluar si un hook/patch de la app puede reubicar
  `buzola_translations` al final de `installed_apps` de forma controlada tras cada cambio.
  *(No se propone el DocType `Translation` como respaldo: la solución se mantiene basada en el `.po`
  local + verificación controlada del orden de carga.)*
- **Recomendación fundamentada:** mantener **`.po` local + regla "buzola siempre al final"** con un
  **check automático del orden de carga** (detección arriba). Es el mínimo estable, sin tocar terceros
  ni depender de datos en BD; coincide con ADR-0000. El mecanismo de verificación/corrección del orden
  **NO se implementa en esta etapa** — queda como **decisión pendiente con alternativas (a)/(b)**,
  sujeto a autorización.

## Contrato del generador de `es.po` (NO implementado aún)
- **Entrada:** filas de los 6 CSV con `review_status == "aprobado"` (estado a introducir en la 2ª
  revisión) y `proposed_translation` (o `proposed_plural_translations`) no vacía. **Solo** filas
  aprobadas; nunca `pendiente`/`ambigua`/`conflicto`.
- **Salida:** un único `buzola_translations/locale/es.po` con `msgid`/`msgctxt`/plurales exactos de la
  identidad Gettext y `msgstr` = propuesta aprobada; preserva placeholders y contexto.
- **Idempotencia:** re-generar preserva decisiones humanas; entradas nuevas/eliminadas/cambiadas en las
  apps se detectan por `entry_key` y se marcan para re-revisión (no se pisan decisiones existentes).
- No se genera hasta aprobar la 2ª revisión.

## Riesgos y limitaciones
- `crm` (develop) y `helpdesk` (main) no están en `version-16`: sus `msgid` pueden moverse.
- Precedencia atada al orden de instalación (mitigación arriba).
- "igual al inglés" es heurístico (incluye códigos que no deben traducirse).
- Textos no marcados requieren auditoría de código aparte.
- Estado `específica de cliente` existe en el esquema pero **no se usa** (sin datos de cliente).

## Archivos de esta etapa
- `scripts/extract_fresh_pot.py` + `scripts/extract_config.json` (extractor oficial config-driven).
- `scripts/build_catalog.py` (universo → 6 CSV + inventario; gates de integridad).
- `review/01..06_*.csv` (catálogo completo, **40 columnas**; fuente humana autoritativa).
- `working_docs/active/inventario_cobertura.csv` (cobertura corregida + fila TOTAL).
- `working_docs/active/decisiones_no_migradas.csv` (15 decisiones humanas no migrables + motivo).
- `one_offs/human_decisions.py.retired` (capa humana legacy retirada; gitignored, no versionar).
- `.artifacts/freshpot/` (POT fresco + `manifest.json`; gitignored, reproducible).
- Este documento. (La muestra etapa 2 se archivó en `working_docs/archive/`.)

## Siguiente fase (otra autorización)
Segunda revisión humana por bloques → marcar filas `aprobado` con `proposed_translation` → implementar
el generador → generar `locale/es.po` → compilar/validar precedencia. Nada de `/ship` ni generación hasta
aprobación.
