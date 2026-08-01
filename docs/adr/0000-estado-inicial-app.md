# ADR-0000 — Estado inicial y mecanismo de sobrescritura de traducciones

- **Estado:** **Aceptado** — validado por prueba mínima reproducible end-to-end el 2026-08-01
  (ver "Validación" al final). `.po` sobrescribió correctamente cadenas de ERPNext y HRMS, por lo
  que **no fue necesario** recurrir al mecanismo CSV. CSV queda documentado solo como fallback si
  en el futuro apareciera un caso donde `.po` no sobrescriba.
- **Fecha:** 2026-08-01
- **Contexto de versión:** Frappe 16.26.3, ERPNext 16.27.0, HRMS 16.12.2, Helpdesk 1.28.1 (main),
  CRM 2.0.0-dev, Python 3.14.6, bench `/home/erpnext/frappe-bench-v16`.

## Contexto

Se necesita mantener traducciones locales en español (México) para varias apps del ecosistema
sin modificar sus repositorios (sobreviven a `bench update`) y de forma versionable y ampliable
a nuevas apps por configuración.

## Investigación (evidencia de código fuente v16)

`frappe/translate.py::get_all_translations()` construye el diccionario final en este orden
(cada `.update()` sobrescribe lo previo):

1. `get_translations_from_apps(lang)` — itera `frappe.get_installed_apps()` en **orden de
   instalación** y, por cada app, aplica `translations.update(csv)` y luego
   `translations.update(mo)` (`translate.py:179-181`). **La última app instalada gana.**
   Dentro de una app, el `.mo` (compilado de `.po`) tiene precedencia sobre el `.csv`.
2. Idioma hijo (`es-MX`) sobre padre (`es`) (`translate.py:149-152`).
3. `get_user_translations(lang)` — DocType `Translation` (BD) — sobrescribe **todo**
   (`translate.py:156-158`).

Formatos: v16 usa gettext. Catálogo fuente en `<app>/<app>/locale/<lang>.po`; se compila a
`sites/assets/locale/<lang>/LC_MESSAGES/<app>.mo` con `bench compile-po-to-mo`. El CSV
(`<app>/<app>/translations/<lang>.csv`) es legacy pero aún se lee.

## Decisión (provisional, sujeta a la prueba end-to-end)

El catálogo local se publica **provisionalmente** como **archivo `.po`** en `buzola_translations/buzola_translations/locale/es.po`
(y, si se requiere variante regional, `es_MX.po`).

- **Sobrescritura** garantizada instalando `buzola_translations` en el sitio **después** de las
  apps cuyas cadenas traduce (queda última en el orden de instalación → su `.mo` gana).
- **No** se usa el DocType `Translation` como mecanismo primario: no es versionable en git y la
  app no debe gestionar datos en BD. Queda como recurso puntual de override urgente, no como fuente.
- **No** se usa CSV como formato definitivo (Frappe empuja `migrate-csv-to-po`); se conserva solo
  como material de referencia v15.
- La app **no declara `required_apps`**: se superpone a lo que exista. El alcance de análisis se
  define por configuración/descubrimiento, permitiendo añadir apps sin tocar el núcleo.

## Consecuencias

- Positivas: versionable, sobrevive `bench update`, no forkea apps, ampliable por configuración.
- Riesgo a validar: el override depende del **orden de instalación** (leído de la BD, no de
  `apps.txt`). Si se reinstala/reordena, hay que reinstalar `buzola_translations` al final.
- Requiere `compile-po-to-mo` + `bench build` + `clear-cache` tras cada cambio de catálogo.

## Validación (resultados demostrados — 2026-08-01, sitio `proposals.dev`)

Prueba end-to-end con dos cadenas (ERPNext + HRMS), sin `bench build` (bastó `compile-po-to-mo`,
que escribe el `.mo` directamente):

| Cadena (msgid) | App | ANTES | DESPUÉS (buzola instalada + compilada) | REVERT (uninstall + rm .mo) |
|---|---|---|---|---|
| `Posting Date` | erpnext | `Fecha de Contabilización` | `Fecha de Registro [BUZOLA]` | `Fecha de Contabilización` |
| `Leave Application` | hrms | `Solicitud de vacaciones` | `Solicitud de Ausencia [BUZOLA]` | `Solicitud de vacaciones` |

- **Orden/precedencia:** `frappe.get_installed_apps()` terminó en `[..., telephony, helpdesk,
  buzola_translations]`; `buzola_translations` quedó **última** → su `.mo` gana por `.update()`.
- **Persistencia:** un proceso nuevo (`bench console`) sin limpiar caché siguió devolviendo el
  valor local → no es artefacto de proceso.
- **Reversibilidad:** `uninstall-app` + eliminar el `.mo` + `clear-cache` revierte a los valores
  originales; `buzola_translations` deja de estar en `get_installed_apps()`.
- **No intrusión:** `git status` de frappe/erpnext/hrms/crm/helpdesk/telephony quedó **limpio**
  (los artefactos de build `yarn.lock`/`auto-imports.d.ts` producidos por `bench build` se
  restauraron).

Conclusión: `.po` en la app local, instalada al final, es un mecanismo válido y reversible de
sobrescritura. No se modificó ninguna app de terceros.
