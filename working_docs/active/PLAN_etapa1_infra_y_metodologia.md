# PLAN — Etapa 1: infraestructura, investigación y metodología

Plan de trabajo activo. Fuente rectora: `frappe-infrastructure/projects/buzola_translations/plan-rector.md`.
No es documentación publicable. Se archiva o migra al cerrar la etapa.

## Objetivo de la etapa

Dejar lista la infraestructura, probar el mecanismo de sobrescritura y validar la metodología de
traducción con una muestra — **sin** generar aún el catálogo completo ni los archivos finales.

## Fases

### F1 — Infraestructura (HECHO)
- [x] Auditoría de reglas frappe-infrastructure (scaffold, docs, git, symlinks).
- [x] Scaffold estándar de la app + symlink `.claude/commands`.
- [x] ADR-0000 con la decisión técnica y evidencia de código.
- [x] Documento rector en `projects/buzola_translations/`.

### F2 — Investigación técnica (HECHO)
- [x] Mecanismo de traducción v16 (`frappe/translate.py`): orden de carga, precedencia, caché.
- [x] Inventario de catálogos de las 5 apps (+ instalación helpdesk/telephony).

### F3 — Prueba mínima reproducible (PENDIENTE — requiere autorización BD)
Pasos propuestos (sitio candidato: `<site>`, que ya tiene las 5 apps):
1. `bench --site <site> install-app buzola_translations`  ⚠️ escribe BD
2. Poner en `buzola_translations/locale/es.po` una cadena de prueba, p. ej. sobrescribir
   una `msgid` conocida de frappe/erpnext con un valor local reconocible.
3. `bench compile-po-to-mo --app buzola_translations`
4. `bench build --app buzola_translations`
5. `bench --site <site> clear-cache`
6. Verificar con `bench --site <site> execute frappe.translate.get_all_translations`
   (o `_()`), que la cadena devuelve el valor local.
7. Confirmar `git status` en apps de terceros = limpio (no se modificaron).
8. Registrar comandos y salidas reales en el ADR-0000 (sección validación).

### F4 — Metodología y muestra (EN PROGRESO)
- [x] Agrupación ≤6 archivos definida (ver rector §10).
- [ ] Muestra de catálogo (`review/_muestra_metodologia.csv`) con cadenas reales y contexto.
- [ ] Revisión de la muestra con el usuario para calibrar criterios.

## Pendiente de autorización explícita
- `install-app buzola_translations` (BD), `git init` + rama `version-16`, cualquier PR.

## No repetir
- helpdesk `develop` (rama móvil); se usó `main`.
- `docs/active/` (no canónico).
