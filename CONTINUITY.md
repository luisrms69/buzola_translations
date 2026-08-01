# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-01
**Rama activa:** `version-16`
**Tarea actual:** Commit inicial del scaffold (autorizado); aún sin historial git previo.

---

## Recuperación rápida

Estoy trabajando en:
La app de traducciones locales del ecosistema. El scaffold estándar está listo y la prueba
mínima de sobrescritura `.po` quedó verde. Voy a crear el commit inicial.

Plan que estoy siguiendo:
`frappe-infrastructure/projects/buzola_translations/plan-rector.md` (rector) y
`working_docs/active/PLAN_etapa1_infra_y_metodologia.md`.

Objetivo inmediato:
Crear el commit inicial `chore: initialize buzola translations app` con 30 archivos staged.
Después: decidir repo remoto y arrancar la extracción real del catálogo.

Criterio de avance:
Commit creado en `version-16`, working tree limpio salvo `CONTINUITY.md` (post-commit),
repos de terceros limpios.

---

## Estado actual

### Ya cerrado
- Auditoría de reglas de frappe-infrastructure (scaffold, docs, git, symlinks).
- Investigación del mecanismo de traducción v16 (evidencia en `docs/adr/0000`).
- Inventario de las 5 apps (helpdesk `main` + telephony instaladas en `<site>`).
- Scaffold estándar + symlink `.claude/commands` + `git init` (rama `version-16`).
- Prueba mínima end-to-end VERDE: `.po` sobrescribe erpnext+hrms, persiste y revierte.

### En progreso
- Commit inicial del scaffold (staged, esperando ejecución autorizada).

### Pendiente inmediato
1. Realizar el commit inicial (sin push/PR).
2. Decidir repo remoto GitHub (`luisrms69/buzola_translations`) y momento del push.
3. Generar `locale/es.po` real tras aprobar traducciones en `review/` (extracción aún no iniciada).

### No repetir
- helpdesk `develop` (exige Python 3.14 pero es rama móvil) — se usó `main`.
- `docs/active/` (no canónico; `/doc-review` lo bloquea).
- Dejar cadenas de prueba `[BUZOLA]` en el catálogo versionable.

---

## Decisiones vigentes
- Catálogo local en `buzola_translations/locale/es.po`; instalar la app **al final** para override
  (validado). Sin DocTypes, fixtures ni `required_apps`.
- `.claude/` completo se ignora (symlink de ruta absoluta no portable).
- `.po` validado como mecanismo (ADR-0000 Aceptado); CSV solo como fallback documentado.

---

## Archivos relevantes ahora

### Leer primero
- `docs/adr/0000-estado-inicial-app.md` (decisión + tabla de validación de la prueba).
- `frappe-infrastructure/projects/buzola_translations/plan-rector.md`.

### Probablemente editar
- `working_docs/active/PLAN_etapa1_infra_y_metodologia.md` (avance de fases).

### No tocar
- `es.po` de apps de terceros (`apps/{frappe,erpnext,hrms,helpdesk,crm}/.../locale/es.po`).

---

## Riesgos / cuidados
- El override depende del orden de instalación (BD), no de `apps.txt`: buzola debe ser la última
  instalación en cada sitio.
- Registro de la app en el bench vía `sites/apps.txt` + `env/.../buzola_translations.pth`
  (no versionados). buzola quedó DESINSTALADA de `<site>`; helpdesk/telephony siguen.
- `crm` en `develop` y `helpdesk` en `main`: sus `msgid` pueden moverse entre versiones.

---

## Información faltante
- ¿Catálogo único `es.po` o variante `es_MX.po` separada? (por ahora solo `es.po`).
- URL/creación del repo remoto y política de CI para esta app.
