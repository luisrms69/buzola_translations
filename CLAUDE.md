# CLAUDE.md — buzola_translations

Las reglas globales del ecosistema están en
`/home/erpnext/Developer/frappe-infrastructure/.claude/CLAUDE.md` y en los CLAUDE.md de
`~/.claude` y `frappe-bench-v16/.claude`. Este archivo solo añade contexto local.

## Qué es esta app

Catálogo de traducciones locales en español (México) que se **superpone** a otras apps
(frappe, erpnext, hrms, helpdesk, crm y futuras) mediante un `.po` propio en
`buzola_translations/locale/`. **No** crea DocTypes, dashboards ni interfaz. **No** forkea
apps. **No** copia los catálogos `es.po` de terceros al repo.

## Estado

- **Versión:** 0.0.1 (scaffold inicial).
- **Rama protegida:** `version-16` (estándar Frappe; PR siempre a `version-16`).
- **Fuente rectora:** `frappe-infrastructure/projects/buzola_translations/plan-rector.md`.
- **Plan de trabajo activo:** `working_docs/active/`.
- **Decisión técnica:** `docs/adr/0000-estado-inicial-app.md`.

## Apps objetivo (bench v16) y catálogos

| App | Versión | Rama | `es.po` |
|---|---|---|---|
| frappe | 16.26.3 | version-16 | `apps/frappe/frappe/locale/es.po` |
| erpnext | 16.27.0 | version-16 | `apps/erpnext/erpnext/locale/es.po` |
| hrms | 16.12.2 | version-16 | `apps/hrms/hrms/locale/es.po` |
| helpdesk | 1.28.1 | main | `apps/helpdesk/helpdesk/locale/es.po` |
| crm | 2.0.0-dev | develop | `apps/crm/crm/locale/es.po` |

## Reglas locales

- El destino final del catálogo es `buzola_translations/locale/es.po`. **No** editar los
  `es.po` de las apps de terceros.
- Toda escritura en BD, `install-app`, `bench migrate` → avisar y esperar autorización.
- Scripts auxiliares de auditoría van en `scripts/` (consumen salidas de bench, no reimplementan
  el extractor). Los temporales de una sola vez, en `one_offs/` (no versionado).
- Los archivos grandes de revisión humana van en `review/` (CSV UTF-8, ≤6 archivos).

## Antes de cada PR

- [ ] `ruff` y `ruff format` sobre `.py`
- [ ] `/doc-review` (hay `docs/` y `mkdocs.yml`)
- [ ] Catálogo `.po` compila y sobrescribe (prueba mínima verde)
- [ ] Sin modificaciones a apps de terceros
- [ ] CONTINUITY.md actualizado (`/update-continuity`)
