# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-02
**Rama activa:** `feat/catalog-extraction` (rama de trabajo; `version-16` es la protegida)
**Tarea actual:** Catálogo español **revisado, generado, compilado, instalado y validado** para Frappe +
ERPNext + HRMS. Pendiente: revisión de Helpdesk y CRM.

---

## Recuperación rápida

Estoy trabajando en:
El catálogo local de traducciones. Ya están **cerradas** la revisión humana de **Frappe, ERPNext
(operaciones y contabilidad/finanzas) y HRMS**. Con esos CSV aprobados se generó el `.po` oficial, se
compiló el `.mo` y se **instaló y validó funcionalmente** `buzola_translations` en dos sitios no
productivos. Falta revisar **Helpdesk y CRM** y luego regenerar el `.po` incluyéndolos.

Plan que estoy siguiendo:
`working_docs/active/PLAN_etapa2_catalogo_completo.md` (fuente rectora:
`frappe-infrastructure/projects/buzola_translations/plan-rector.md`).

Objetivo inmediato:
Punto de recuperación (este commit). Después: **revisión de Helpdesk y CRM** (bloque 05), regenerar
`es.po` incluyéndolos, y resolver la **decisión terminológica de `Payment Entry`**.

Criterio de avance:
22 064 `entry_key` únicos en `review/`; `es.po` determinista (byte-idéntico) con 0 pérdidas de
placeholders; `.mo` compila; verificador de orden en verde en los sitios de validación.

---

## Estado actual

### Ya cerrado
- **Revisión humana:** Frappe (6 306), ERPNext operaciones (bloque 02) y contabilidad/finanzas (bloque
  03), HRMS (2 284). Estados controlados; sin filas activas pendientes en esos bloques.
- **Generador determinista** `scripts/build_po.py` → `buzola_translations/locale/es.po` (**18 417
  entradas**, `Language: es`, UTF-8, 0 fuzzy, 0 duplicados, 0 conflictos Gettext, 8 dedups). Manifiesto
  `working_docs/active/po_manifest.json`.
- **Compilación** `.mo` con `bench compile-po-to-mo` (byte-idéntica). Excluye Helpdesk/CRM (119).
- **Instalado y validado** en `buzola-demo.dev` (frappe+erpnext+hrms) y `facturacion-v16.dev`
  (frappe+erpnext+facturacion_mexico+payments): `buzola_translations` queda **al final** de
  `installed_apps`; las traducciones locales **prevalecen**; identidad técnica de DocTypes **intacta**;
  apps personalizadas cargan sin errores. `buzola_translations` es **exclusivamente lingüística**
  (sin DocTypes/hooks/overrides/fixtures/patches).
- **Auditorías:** `doctype_terminology_changes.csv` (444 nombres visibles con cambio; incluye
  `Payment Entry`), `custom_apps_translation_dependency_audit.md` (0 dependencias técnicas reales),
  `install_and_reversibility.md` (orden + reversibilidad + verificador).
- **Verificador de orden** `scripts/check_translation_order.py` (+ `test_check_translation_order.py`,
  4/4 PASS).

### Pendiente inmediato
1. Revisión humana de **Helpdesk** y **CRM** (bloque 05).
2. Regenerar `es.po` incluyendo Helpdesk/CRM tras su revisión.
3. **Decisión `Payment Entry`**: catálogo propone **"Registro de Pago"**; clientes/cursos usan
   **"Entrada de pago"** — pendiente de consulta transversal (ver `doctype_terminology_changes.csv`).

### No repetir
- Commit/push directo a `version-16` (protegida): todo por rama de trabajo + PR; solo `/ship`.
- Incluir Helpdesk/CRM en el `.po` antes de su revisión.
- Editar la BD para forzar el orden de apps: se usa `install-app`/`uninstall-app` (soportado).
- SSH para GitHub: estándar HTTPS + `gh`.

---

## Decisiones vigentes
- Fuente autoritativa = los 6 CSV de `review/`; el `.po` se **genera** de ahí (no se edita a mano).
- Instalar `buzola_translations` **al final** de `installed_apps` para override; verificar con
  `scripts/check_translation_order.py --site <site>`.
- Entidades CRM en inglés: `Lead`, `Deal`; `Prospect`→Prospecto, `Opportunity`→Oportunidad;
  `Job Card`→Vale de Trabajo.
- Estados excluidos del `.po`: po_huérfana/ambigua/conflicto/especializada/sin propuesta.

---

## Archivos relevantes ahora
### Leer primero
- `working_docs/active/PLAN_etapa2_catalogo_completo.md` (estado por app + método).
- `working_docs/active/doctype_terminology_changes.csv` (incluye caso `Payment Entry`).
### Probablemente editar
- `review/05_helpdesk_crm.csv` (siguiente revisión) → luego regenerar `es.po`.
### No tocar
- `es.po` de apps de terceros; la BD de los sitios (usar comandos soportados).

---

## Riesgos / cuidados
- El override depende del orden de instalación (BD), no de `apps.txt`: al instalar otra app después,
  `buzola_translations` deja de ser la última → correr el verificador y reinstalarla al final.
- `.mo` en `sites/assets` es artefacto (gitignored); no versionar. Respaldos/one_offs/.artifacts fuera del commit.

---

## Información faltante
- ¿Migrar o conservar nombres visibles de DocType que cambian (444, p. ej. `Payment Entry`)? — pendiente de consulta a clientes.
