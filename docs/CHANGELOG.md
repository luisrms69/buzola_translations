# Changelog

Todas las versiones notables de `buzola_translations`.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/);
versionado [SemVer](https://semver.org/lang/es/).

## [0.0.1] - 2026-08-01

Etapa de setup del repositorio (infraestructura/configuración). Sin release funcional aún.

### Added
- Scaffold inicial de la app Frappe v16 (estructura estándar del ecosistema Buzola).
- ADR-0000: mecanismo de sobrescritura de traducciones vía catálogo `.po` local, **validado
  end-to-end** (prueba mínima reproducible: sobrescribe, persiste, revierte).
- CI/CD: `.github/workflows/ci.yml` (job `Validate`) y `linter.yml` (`Pre-commit`, `Dependency audit`).
- Protección de rama `version-16` mediante ruleset (PR obligatorio, force push/borrado bloqueados,
  historial lineal, checks obligatorios, sin bypass).
- Repositorio público con remoto `upstream` (HTTPS); validación desde clon limpio.

### Pending
- Catálogo `locale/es.po` (aún no generado; corresponde a la etapa funcional de traducciones).
