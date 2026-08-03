# Instalación en sitio de validación y reversibilidad — catálogo candidato

## Sitio de validación
`buzola-demo.dev` (puerto 8411; documentado como sitio demo no productivo). Apps instaladas: **frappe
16.26.3, erpnext 16.27.0, hrms 16.12.2** (sin Helpdesk ni CRM → confirma la exclusión). `buzola_translations`
**no** está instalada. Frappe/ERPNext/HRMS coinciden con los commits del manifiesto `po_manifest.json`.

## Instalación (MODIFICA LA BD del sitio — requiere autorización explícita)
El catálogo ya está generado (`buzola_translations/buzola_translations/locale/es.po`) y compilado
(`sites/assets/locale/es/LC_MESSAGES/buzola_translations.mo`). Para que el sitio lo aplique, la app debe
quedar en `installed_apps` **después** de frappe/erpnext/hrms. Comandos soportados (no ejecutados aún):

```bash
# 1) Instalar la app (añade buzola_translations al final de installed_apps + migrate). ESCRIBE EN BD.
bench --site buzola-demo.dev install-app buzola_translations
# 2) Compilar .mo (ya hecho; reejecutable, no toca BD)
bench compile-po-to-mo --app buzola_translations
# 3) Reconstruir solo assets necesarios
bench build --app buzola_translations
# 4) Limpiar caché (soportado)
bench --site buzola-demo.dev clear-cache
# 5) Verificar orden efectivo (installed_apps[-1] debe ser buzola_translations)
bench --site buzola-demo.dev execute frappe.get_installed_apps
# 6) Confirmar idioma del sitio/usuario de prueba = es (System Settings / User)
```
No editar tablas ni configuración manualmente para forzar el orden. `install-app` agrega la app al final,
lo que garantiza la precedencia del `.mo` sobre frappe/erpnext/hrms.

## Reversibilidad (soportada, NO destructiva)
Para retirar temporalmente el catálogo local y confirmar que reaparecen las traducciones originales:

```bash
# Opción A — desinstalar la app de traducciones (deja de cargar su .mo). NO elimina datos del negocio.
bench --site buzola-demo.dev uninstall-app buzola_translations --no-backup   # (o con backup)
bench --site buzola-demo.dev clear-cache
# -> reaparecen las traducciones originales de frappe/erpnext/hrms.

# Opción B — sin desinstalar: quitar el .mo compilado y limpiar caché
rm -f sites/assets/locale/es/LC_MESSAGES/buzola_translations.mo
bench --site buzola-demo.dev clear-cache
# -> el sitio deja de aplicar el catálogo local; recompilar lo restaura.
```
Ambas son reversibles y no borran datos del sitio. `buzola_translations` no crea DocTypes ni datos, por lo
que desinstalarla no afecta registros de negocio.

## Validación funcional prevista (post-instalación)
- Frappe: etiqueta de DocType, botón/acción, mensaje, y una corrección (p. ej. `Journal Entry`→Asiento Contable).
- ERPNext: ventas/compras, inventario, contabilidad, nombre de DocType, cadena con placeholders.
- HRMS: Employee, asistencia/checada, ausencias, nómina, una nueva y una corregida.
- Terminología: `Lead`→Lead, `Deal`→Deal, `Prospect`→Prospecto, `Opportunity`→Oportunidad, `Job Card`→Vale
  de Trabajo; `Payment Entry` documentado para decisión final (ver `doctype_terminology_changes.csv`).
- Confirmar: no se cargan cadenas de Helpdesk/CRM; sin errores de `.mo`/JS/import; identidad técnica de
  DocTypes intacta; sin cambios de funcionalidad/permisos/datos/rutas/API.

---

## Orden de resolución de traducciones (Frappe v16) — verificado en código
- `frappe/translate.py: get_translations_from_apps` itera `frappe.get_installed_apps()` y aplica
  `translations.update(...)` por cada app → **la ÚLTIMA app en `installed_apps` gana**; dentro de una app,
  `.mo` (compilado del `.po`) prevalece sobre `.csv`.
- `installed_apps` se lee de la BD del sitio (`db.get_global("installed_apps")`), filtrado por presencia en
  el bench. **No depende de `apps.txt`.**
- **Cómo se consulta (soportado, solo lectura):** `bench --site <site> execute frappe.get_installed_apps`.
- **Cómo se actualiza (soportado):** `bench --site <site> install-app <app>` agrega la app **al final**;
  `uninstall-app` la retira. **No** editar la tabla directamente.
- **Al instalar otra app después:** queda al final y **desplazaría** a `buzola_translations`, que perdería
  precedencia sobre esa app para los `msgid` en común.

### Comprobación posterior a CADA instalación de apps (obligatoria)
```bash
env/bin/python apps/buzola_translations/scripts/check_translation_order.py --site <site>
# exit 0 si buzola_translations está AL FINAL; exit!=0 con mensaje claro si no.
```
El script es **no destructivo** (solo lectura), no modifica el orden y no es un hook.

### Procedimiento soportado para corregir el orden (si el verificador falla)
Reubicar `buzola_translations` al final **reinstalándola** (mecanismo soportado; no editar BD):
```bash
bench --site <site> uninstall-app buzola_translations --yes   # (con backup previo)
bench --site <site> install-app buzola_translations           # vuelve al final de installed_apps
bench --site <site> clear-cache
env/bin/python apps/buzola_translations/scripts/check_translation_order.py --site <site>  # verificación posterior
```
No se añaden hooks ni código ejecutable en la app para controlar el orden; la operación es manual/CI.
