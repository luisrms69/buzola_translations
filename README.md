### Buzola Translations

Traducciones locales en español (México) para las apps del ecosistema Frappe/ERPNext
(Frappe Framework, ERPNext, Frappe HR/HRMS, Frappe Helpdesk, Frappe CRM y futuras apps).

La app se superpone a los catálogos originales sin modificarlos: publica un catálogo `.po`
propio que, al cargarse en último lugar, sobrescribe las traducciones base. No crea DocTypes,
dashboards ni interfaz administrativa. No es un fork de las apps traducidas.

### Instalación

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench --site <site> install-app buzola_translations   # instalar DESPUÉS de las apps base
bench compile-po-to-mo --app buzola_translations
bench build --app buzola_translations
bench --site <site> clear-cache
```

> El orden importa: `buzola_translations` debe instalarse después de las apps cuyas cadenas
> traduce para que su catálogo tenga precedencia (ver `docs/adr/0000-estado-inicial-app.md`).

### Alcance

Ver el documento rector del proyecto en
`frappe-infrastructure/projects/buzola_translations/plan-rector.md`
y el plan de trabajo activo en `working_docs/active/`.

### Contributing

Esta app usa `pre-commit` para formato y linting (solo `.py`):

```bash
cd apps/buzola_translations
pre-commit install
```

### License

mit
