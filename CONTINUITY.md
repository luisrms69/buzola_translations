# CONTINUITY.md — buzola_translations

**Fecha:** 2026-08-01
**Rama activa:** `docs/update-setup-continuity` (rama de trabajo; `version-16` es la protegida)
**Tarea actual:** Cierre documental del setup. El **setup técnico del repositorio quedó cerrado**.

---

## Recuperación rápida

Estoy trabajando en:
La app de traducciones locales del ecosistema. El **setup técnico está cerrado**: scaffold,
prueba `.po` verde, repo público, CI/CD integrado y rama protegida con ruleset. Falta la **etapa
funcional** (extraer/proponer/revisar traducciones), que va en **otra conversación**.

Plan que estoy siguiendo:
`frappe-infrastructure/projects/buzola_translations/plan-rector.md` (rector) y
`working_docs/active/PLAN_etapa1_infra_y_metodologia.md`.

Objetivo inmediato:
Revisar el **registro canónico de la app en el bench** (`sites/apps.txt` + `.pth` fueron altas
manuales del scaffold no interactivo; conviene confirmar que quedan como corresponde). Después,
la etapa funcional de traducciones en otra conversación.

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

### En progreso
- (Cierre documental de este estado — esta rama.)

### Pendiente inmediato
1. **Normalizar el registro de la app en el bench.** Estado verificado: está en `sites/apps.txt`
   (línea 21) y es importable vía `.pth`, pero **falta el `.dist-info`** (el `.pth` se creó a mano;
   `importlib.metadata.version('buzola_translations')` → `PackageNotFoundError`). Las apps canónicas
   tienen `.pth` **+** `.dist-info`. Normalizar con una **instalación editable** del paquete
   (`pip install -e apps/buzola_translations`, que es lo que hace `bench` internamente) → la ejecuta
   el **usuario** (el hook bloquea instalación de paquetes para Claude). **No borrar** el `.pth`
   manual hasta que la instalación editable cree su reemplazo. No instala en ningún sitio.
2. Etapa funcional (otra conversación): extracción real del catálogo (`generate-pot-file`),
   consolidación en `review/` (≤6 archivos), propuestas, revisión y generación de `locale/es.po` real.

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
- Registro de la app en el bench vía `apps.txt` + `.pth` manual, **sin `.dist-info`** (no canónico
  del todo; import y reconocimiento por bench funcionan, lo demostró la prueba mínima). Normalizar con
  instalación editable (acción del usuario). buzola **DESINSTALADA** de `<site>`; helpdesk/telephony siguen.
- `crm` en `develop` y `helpdesk` en `main`: sus `msgid` pueden moverse entre versiones.

---

## Información faltante
- ¿Catálogo único `es.po` o variante `es_MX.po` separada? (por ahora solo `es.po`).
