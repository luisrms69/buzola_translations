# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-01
**Rama activa:** `docs/update-setup-continuity` (rama de trabajo; `version-16` es la protegida)
**Tarea actual:** **Etapa de setup CERRADA** (punto 9). Siguiente etapa: extracción y revisión de traducciones (otra conversación).

---

## Recuperación rápida

Estoy trabajando en:
La app de traducciones locales del ecosistema. La **etapa de setup está COMPLETAMENTE cerrada**
(scaffold, prueba `.po` verde, repo público, CI/CD, rama protegida con ruleset, clon limpio
validado). El plan de la etapa 1 quedó **archivado**. La **etapa funcional** (extraer/proponer/
revisar traducciones y generar `locale/es.po`) va en **otra conversación**.

Fuente rectora / referencia:
`frappe-infrastructure/projects/buzola_translations/plan-rector.md` (rector) y el plan cerrado
`working_docs/archive/PLAN_etapa1_infra_y_metodologia.md`. (Ya **no** hay plan en `working_docs/active/`.)

Objetivo inmediato:
Ninguno de setup pendiente. La siguiente etapa es la **extracción funcional** de traducciones,
en otra conversación.

Criterio de avance:
`version-16` sincronizada (`b72d34c`), CI verde en la rama protegida y ruleset exigiendo PR + checks.

---

## Estado actual

### Ya cerrado — setup técnico del repositorio
- Scaffold estándar + prueba mínima `.po` end-to-end VERDE (sobrescribe, persiste, revierte).
- Repo público `https://github.com/luisrms69/buzola_translations`, remoto `upstream` HTTPS.
- **PR #1 mergeado (squash) en `b72d34c`**: integra `.github/workflows/ci.yml` y `linter.yml`.
- **CI/CD integrado** — checks: `Validate` (CI), `Pre-commit` y `Dependency audit` (Linters).
- **Ruleset `version-16-protection` activo** sobre `refs/heads/version-16`, sin bypass:
  - PR obligatorio (`pull_request`), force push bloqueado (`non_fast_forward`),
    eliminación bloqueada (`deletion`), historial lineal (`required_linear_history`),
    checks obligatorios: `Validate`, `Pre-commit`, `Dependency audit`.
- `version-16` local y remota **sincronizadas** en `b72d34c`; ramas de trabajo previas eliminadas.
- **Registro de la app en el bench: funcional y validado.** Está en `sites/apps.txt` (línea 21),
  el paquete es importable y bench la reconoce; la prueba de install/uninstall ya funcionó. El `.pth`
  actual queda **aceptado**. Falta `.dist-info` (metadata de instalación editable), pero es
  **opcional y no requerido** para el setup — no bloquea el funcionamiento.
- **Clon limpio validado (punto 8).** Clonado `version-16` (`b72d34c`) desde HTTPS a ruta temporal,
  sin copiar del original. Verde: estructura completa del scaffold, `.github/workflows/{ci,linter}.yml`
  presentes, sin `.claude/`/claves/sitios/artefactos, import verificado **desde el clon**,
  `ruff check` + `ruff format --check`, `mkdocs build --strict`, parseo TOML/YAML, workflows
  **autocontenidos** (sin rutas locales/absolutas). El build del paquete quedó confirmado por el
  check `Validate` (verde) en Actions sobre `b72d34c` — no reproducible localmente porque `flit_core`
  (dependencia de *build isolation*) no está en el env del bench. Clon temporal eliminado.

### En progreso
- Ninguno (etapa de setup cerrada). El commit de este cierre queda en la rama `docs/update-setup-continuity`.

### Pendiente inmediato
1. Etapa funcional (otra conversación): extracción real del catálogo (`generate-pot-file`),
   consolidación en `review/` (≤6 archivos), propuestas, revisión y generación de `locale/es.po` real.

### Observaciones opcionales (no bloqueantes)
- Si en el futuro se quisiera el registro 100% canónico (para que `importlib.metadata` liste la app),
  bastaría una **instalación editable** del paquete en el env del bench. Es opcional; no se hace en
  esta etapa y no debe modificarse el entorno por ello.

### No repetir
- Commit/push directo a `version-16` (protegida): todo por rama de trabajo + PR.
- helpdesk `develop`; `docs/active/`; cadenas de prueba `[BUZOLA]` en el catálogo.
- SSH para GitHub: el estándar es HTTPS + `gh`; nunca inspeccionar/usar claves.

---

## Decisiones vigentes
- Catálogo local en `buzola_translations/locale/es.po`; instalar la app **al final** para override
  (validado). Sin DocTypes, fixtures ni `required_apps`.
- `.po` validado (ADR-0000 Aceptado); CSV solo como fallback. `.claude/` ignorado.
- GitHub por **HTTPS + `gh`**, remoto `upstream`, rama protegida `version-16` con ruleset.
- `locale/es.po` **todavía NO contiene traducciones reales** (el catálogo real no se ha generado).

---

## Archivos relevantes ahora

### Leer primero
- `docs/adr/0000-estado-inicial-app.md` (decisión + validación).
- `frappe-infrastructure/projects/buzola_translations/plan-rector.md`.

### No tocar
- `es.po` de apps de terceros (`<bench-path>/apps/{frappe,erpnext,hrms,helpdesk,crm}/.../locale/es.po`).

---

## Riesgos / cuidados
- El override depende del orden de instalación (BD), no de `apps.txt`: buzola debe ser la última
  instalación en cada sitio.
- Registro de la app en el bench vía `apps.txt` + `.pth` (aceptado, funcional). `.dist-info` opcional,
  no requerido. buzola **DESINSTALADA** de `<site>`; helpdesk/telephony siguen instaladas.
- `crm` en `develop` y `helpdesk` en `main`: sus `msgid` pueden moverse entre versiones.

---

## Información faltante
- ¿Catálogo único `es.po` o variante `es_MX.po` separada? (por ahora solo `es.po`).
