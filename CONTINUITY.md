# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-01
**Rama activa:** `version-16` (publicada en `upstream`, HTTPS)
**Tarea actual:** Setup del repositorio **COMPLETADO**. Listo para la etapa funcional (extracción del catálogo), que se realizará en **otra conversación**.

---

## Recuperación rápida

Estoy trabajando en:
La app de traducciones locales del ecosistema. El setup quedó **cerrado**: scaffold estándar,
prueba mínima `.po` verde y repositorio remoto publicado. Falta la **etapa funcional** (extraer,
proponer y revisar traducciones), que va en otra conversación.

Plan que estoy siguiendo:
`frappe-infrastructure/projects/buzola_translations/plan-rector.md` (rector) y
`working_docs/active/PLAN_etapa1_infra_y_metodologia.md`.

Objetivo inmediato:
Arrancar la extracción real del catálogo (otra conversación): `generate-pot-file`, consolidar en
`review/` (≤6 archivos), proponer traducciones y, tras aprobación, generar `locale/es.po` real.

Criterio de avance:
Repo publicado con HEAD `cc241f5`, working tree limpio, apto para la etapa funcional.

---

## Estado actual

### Ya cerrado
- Auditoría de reglas de frappe-infrastructure; investigación del mecanismo v16 (`docs/adr/0000`);
  inventario de las 5 apps (helpdesk `main` + telephony instaladas en `<site>`).
- Scaffold estándar + symlink `.claude/commands`; 2 commits: `985592c` (scaffold) y `cc241f5` (docs).
- Prueba mínima end-to-end **VERDE**: `.po` sobrescribe erpnext+hrms, persiste y revierte.
- **Repo remoto publicado:** `https://github.com/luisrms69/buzola_translations` (PUBLIC), remoto
  `upstream` **HTTPS**, `version-16 -> upstream/version-16`, HEAD `cc241f5`. Sin `origin`.

### En progreso
- (Setup cerrado; sin trabajo en curso.)

### Pendiente inmediato (etapa funcional — otra conversación)
1. Extracción real de cadenas (`generate-pot-file`) y consolidación en `review/` (≤6 archivos).
2. Propuestas + revisión humana; después generar `locale/es.po` real.

### No repetir
- helpdesk `develop` (exige Python 3.14 pero es rama móvil) — se usó `main`.
- `docs/active/` (no canónico; `/doc-review` lo bloquea).
- Dejar cadenas de prueba `[BUZOLA]` en el catálogo versionable.
- SSH para GitHub: el estándar es **HTTPS + `gh`** (nunca inspeccionar/usar claves).

---

## Decisiones vigentes
- Catálogo local en `buzola_translations/locale/es.po`; instalar la app **al final** para override
  (validado). Sin DocTypes, fixtures ni `required_apps`.
- `.claude/` completo se ignora. `.po` validado (ADR-0000 Aceptado); CSV solo como fallback.
- GitHub por **HTTPS + `gh`**, remoto `upstream`.
- `locale/es.po` **todavía NO contiene traducciones reales** (el catálogo real no se ha generado).

---

## Archivos relevantes ahora

### Leer primero
- `docs/adr/0000-estado-inicial-app.md` (decisión + tabla de validación).
- `frappe-infrastructure/projects/buzola_translations/plan-rector.md`.

### No tocar
- `es.po` de apps de terceros (`<bench-path>/apps/{frappe,erpnext,hrms,helpdesk,crm}/.../locale/es.po`).

---

## Riesgos / cuidados
- El override depende del orden de instalación (BD), no de `apps.txt`: buzola debe ser la última
  instalación en cada sitio.
- Registro de la app en el bench vía `apps.txt` + `.pth` (no versionados). buzola quedó
  **DESINSTALADA** de `<site>`; helpdesk/telephony siguen instaladas.
- `crm` en `develop` y `helpdesk` en `main`: sus `msgid` pueden moverse entre versiones.

---

## Información faltante
- ¿Catálogo único `es.po` o variante `es_MX.po` separada? (por ahora solo `es.po`).
- Política de CI para esta app.
