# Auditoría — dependencia de apps personalizadas en etiquetas traducidas

**Objetivo:** confirmar que ninguna app personalizada use nombres de DocType, campos o etiquetas
**traducidas** como identificadores técnicos (lo que se rompería al instalar el catálogo `es.po`).
El catálogo solo cambia **texto visible**; la identidad técnica (nombres de DocType en inglés, `fieldname`
en snake_case) no cambia. Una app correcta debe usar `Payment Entry`, `Sales Invoice`, `Employee`,
`posting_date`, `payment_type`, etc., y **nunca** `Entrada de pago`, `Registro de Pago`, `Factura de venta`,
`Empleado`, `Fecha de Contabilización`.

## Alcance
Apps auditadas (todas menos frappe, erpnext, hrms, helpdesk, crm, buzola_translations):
`condominium_management, dfp_external_storage, erpnext_custom, erpnext_proposals, facturacion_mexico,
facturacion_mx, cliente_customs, meetings, offsite_backups, payments, planning, project_management,
strategic_planning, telephony, wiki`.

## Método (mecánico, sin modificar apps)
Búsquedas `grep` sobre `.py`, `.js` y `.json` de cada app:
1. **Contexto técnico + nombre español de DocType:** líneas con `frappe.get_doc/new_doc/get_all/get_list/
   get_value/get_single/db.get|set|count|exists`, `"doctype"`, `reference_doctype`, `set_route`,
   `frappe.get_meta`, que contuvieran entre comillas un nombre traducido de alto uso
   (`Entrada de pago`, `Registro de Pago`, `Factura de Venta/Compra`, `Nota de Entrega`, `Orden de Venta/
   Compra`, `Recibo de Nómina`, `Asiento Contable`, `Fecha de Contabilización`, `Centro de Costos`,
   `Empleado`, `Almacén`, `Artículo`).
2. **Identificador de DocType con acento español** en `get_doc/new_doc/get_all/get_list/reference_doctype/
   "doctype":/doctype=` (los nombres canónicos son en inglés y no llevan acentos).
3. **Referencias en JSON** (`ref_doctype`, `reference_doctype`, `document_type`, `link_doctype`,
   `parent_doctype`) con valores en español.
4. **`set_route`, `db.get_value`, `db.exists`, `get_cached_doc`** con cadenas acentuadas.

## Resultado

**Hallazgos con impacto (dependencia técnica real de una traducción): 0.**
No se encontró ninguna app personalizada que use un nombre traducido como identificador técnico. No hay
bloqueantes para instalar el catálogo.

| Clasificación | Conteo | Notas |
|---|---|---|
| Uso incorrecto que rompe funcionalidad | **0** | — |
| Texto visible legítimo (labels/mensajes con `_()`) | (no auditado como riesgo) | El catálogo los traduce correctamente; no son identificadores. |
| Comentario/documentación sin impacto | 0 relevantes | — |
| Falso positivo | 0 | Los patrones no arrojaron coincidencias. |

**Confirmación positiva:** las apps de facturación (las más propensas a referenciar `Payment Entry`) usan el
**nombre canónico en inglés**. Ej.: `facturacion_mexico` referencia `"Payment Entry"` en `hooks.py`,
`ereceipts/api.py`, `facturas_globales/...`, `dashboard_fiscal/...` — nunca la traducción.

## Conclusión
No existe dependencia técnica de etiquetas traducidas en las apps personalizadas. **Instalar el catálogo
`es.po` de `buzola_translations` no rompería la lógica de ninguna app personalizada** (solo cambia texto
visible). Sin bloqueantes desde esta auditoría.

---

# Ampliación (auditoría exhaustiva para facturacion-v16.dev)

**Método:** 744 patrones (nombres español `es_actual`+`es_propuesta` de `doctype_terminology_changes.csv`
≥6 car. + términos de alto riesgo), `grep -F` sobre `.py/.js/.ts/.vue/.json/.html/.jinja/.sql` de **15 apps
personalizadas**, incluyendo tests, fixtures, patches, reportes y hooks (excluyendo `.po`/`locale`/`dist`).

**71 coincidencias**, clasificadas — **0 dependencias técnicas reales**:

| Clasificación | Ejemplos | Impacto |
|---|---|---|
| **Texto visible legítimo** (`"label":` en `.json` de doctypes propios) | condominium `"label":"Moneda"`, facturacion `"label":"Factura de Venta"`, planning `"label":"Tareas"` | Ninguno: son labels del propio doctype, no identificadores; el catálogo no los usa como clave técnica. |
| **`_()` correcto** (label traducido + `fieldname` canónico) | cliente_customs `_("Vendedor")` con `"fieldname":"sales_person"` | Patrón correcto. |
| **DocType propio con nombre español canónico** | facturacion_mx **`Forma de Pago`** (tiene su propio `doctype/forma_de_pago/`) — `"name"`, `"doctype"`, `"options"`, fixtures | Ninguno: es su nombre canónico real, no una traducción de ERPNext; el catálogo no traduce `Forma de Pago`. |
| **Comparación interna de app** (label propio hardcodeado) | facturacion_mexico `field_labels={"payment_form":"Forma de Pago"}` y `if "Forma de Pago" in error` | Ninguno: compara contra su **propio** label hardcodeado (no gettext); consistente sin importar el catálogo. También matches contra terminología **SAT** (externa, fija). |
| **Test data / valores enum de app** | condominium `entity_name="Usuario"`/`"Artículo"`, `_FakeItem(...,"Producto")`, meeting_type `"Evaluación"` | Ninguno: datos de prueba / valores propios, no lookups de DocType de ERPNext. |
| **Dato/clave de estructura** | facturacion `"Reporte": report_data.get(...)` (clave de dict) | Ninguno. |

**Confirmación de nombres técnicos canónicos** (uso correcto, extenso): `"Payment Entry"` 68 · `"Sales Invoice"`
617 · `"Employee"` 4 · `posting_date` 69 · `payment_type` 17 ocurrencias en las apps personalizadas.

**Búsqueda dirigida** de `get_doc/new_doc/get_all/get_list/db.*` con nombre traducido de ERPNext/Frappe/HRMS
(`Entrada de pago`, `Registro de Pago`, `Factura de Venta`, `Empleado`, `Fecha de Contabilización`, `Asiento
Contable`, `Recibo de Nómina`, `Almacén`, `Movimiento de Inventario`): **0 coincidencias**.

**Conclusión:** ninguna app personalizada depende técnicamente de una etiqueta traducida. Instalar el catálogo
**no rompe funcionalidad**. Sin bloqueantes.

## Tests de apps personalizadas
Inventario (auditados estáticamente en la búsqueda anterior): condominium_management 238 · facturacion_mexico
133 · wiki 19 · strategic_planning 11 · payments 8 · erpnext_proposals 27 · facturacion_mx 15 · planning 5 ·
telephony 4 · meetings 3 · offsite_backups 3 · cliente_customs 2 · project_management 2 · dfp_external_storage 1.
**Ejecución: NO realizada.** Motivo: las suites de facturación crean documentos fiscales / registros y
**alterarían** el sitio de validación compartido `facturacion-v16.dev`; no hay sitio de pruebas dedicado
autorizado (y no debe crearse). No se afirma que los tests pasen; solo se auditaron estáticamente (0
dependencias de etiquetas traducidas en su código/datos de prueba).
