# PLAN — Incorporación de Frappe CRM (etapa 4) — CERRADO (v0.3.0)

Ejecución del sistema estándar (ADR-0001 + `PLAN_etapa3.md` + `PLAN_helpdesk_review.md`). Sin rediseño.

## Estado de partida (verificado)
CRM ya existía en `review/07_crm.csv` (1 949), `extract_config.json` (`published:false`), `catalog_baseline.json`
(`2752c85`/develop). Scripts y one_offs de Helpdesk reutilizados. **Sin deriva upstream.**

## Cierre del extractor común (ampliación ADR-0001)
Al auditar CRM aparecieron 10 literales `__()` **multilínea en el `<template>`** (`{{ … }}`) que el wrapper
`.vue` no capturaba (solo `<script>`). Se **amplió** `vue_extract` con un pase `javascript.extract` sobre las
expresiones `{{ … }}`. Verificado: 0 errores; **0 regresiones** (erpnext/frappe Δ0; adiciones crm +11, helpdesk
+2, hrms +1); es.po v0.2.0 byte-idéntico durante la fase de extractor; idempotente. **Auditoría de cobertura
de las 5 apps: `REAL_OMITIDO = 0`** (residual = dinámicos `${…}`/variable + archivos fuera del alcance oficial).
Criterio de cierre sostenido: todos los literales estáticos `__()` detectables están cubiertos, salvo
excepciones documentadas.

## Terminología cerrada
`Lead/Leads`, `Deal/Deals`, `Pipeline/Pipelines` → **inglés** (slang de industria; revertido upstream). `Stage→Etapa`,
`Prospect→Prospecto`, `Opportunity→Oportunidad`; género `Lost→Perdido`, `Won→Ganado`. Nombres DocType `CRM …`:
etiqueta traducida + prefijo (`CRM Lead→Lead de CRM`, `CRM Enrichment Rule→Regla de enriquecimiento de CRM`),
conservando `Lead`/`Deal` protegidos.

## Revisión + consistencia
- **11 bloques ~178**, 3 olas de ≤5 subagentes, persistencia por bloque, integración idempotente. 1 960 filas
  revisadas al 100% (19 LOCKED: 15 preservadas + 4 corregidas por la nueva decisión Lead/Deal/Lost/Won).
- **Distribución:** `traducción propuesta` ~1 224 · `existente correcta` ~464 · `existente mejorable` ~183 ·
  `igual al inglés válida` ~89.
- **Auditoría global de consistencia** (`crm_consistency.csv`): 0 violaciones de protegidos, registro
  impersonal alineado (tú 23→~1 FP), sin falsos amigos activos. Pase dirigido de 36 filas (registro + términos)
  + reclasificaciones mecánicas (ID, Favicon) + 14 nombres DocType.

## Publicación técnica v0.3.0
`published:true` (crm) + bump `0.3.0`. `build_po` detectó **24 conflictos Gettext** (claves sin contexto
compartidas con apps publicadas). Resolución por **convergencia global deliberada** (autorizada caso por caso):
- 16 cambian el `.po` publicado (Lead/Leads, Add a Note, Company Description, Currency Precision, Email Account,
  To/To User, Select View, The holiday…, Your assignment…, y 4 normalizaciones de mayúsculas).
- 8 adoptan el valor ya publicado (All Day, New Event, Upload Image, `From→De`, `Medium→Media`, `Read→Leer`,
  `description→descripción`, `Choose the days→Elija`).
- **Compromisos globales conocidos:** `Medium→Media` (prioridad domina sobre canal) y `Read→Leer` (permiso
  domina sobre estado de notificación) — clave sin contexto sin traducción única perfecta; documentados en
  `human_notes`.

Resultado: `es.po` **20 879** entradas (v0.3.0), 0 conflictos, 0 pérdida de placeholders, idempotente, `.mo`
compilado, precedencia OK. Diff vs v0.2.0 = +1 274 CRM · 0 eliminadas · 16 convergencias.

## Pendiente
`/ship commit` (autorizado) → `/ship push` → `/ship pr` a `version-16` → merge → `/ship release` (tag+Release
`v0.3.0`), cada uno con autorización separada.
