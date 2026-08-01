app_name = "buzola_translations"
app_title = "Buzola Translations"
app_publisher = "Consultoria en Negocios y Aplicaciones"
app_description = "Traducciones locales en español (México) para las apps del ecosistema Frappe/ERPNext"
app_email = "it@buzola.mx"
app_license = "mit"

# Apps
# ------------------
# Esta app NO declara required_apps: es un catálogo de traducciones que se superpone
# a cualquier app presente en el bench (frappe, erpnext, hrms, helpdesk, crm y futuras).
# El alcance de análisis se define por configuración/descubrimiento, no por dependencias
# rígidas. Para que la sobrescritura funcione, buzola_translations debe instalarse en el
# sitio DESPUÉS de las apps cuyas cadenas traduce (ver docs/adr/0000).

# Traducciones
# ------------------
# El catálogo local vive en buzola_translations/locale/<lang>.po y se compila a .mo con
# `bench compile-po-to-mo --app buzola_translations`. Al cargarse en último lugar,
# sus msgstr sobrescriben los de las apps base (frappe/translate.py: get_translations_from_apps).

# Fixtures
# ------------------
# Sin fixtures: esta app no crea ni gestiona DocTypes. No usa el DocType Translation como
# mecanismo primario (no es versionable). Toda traducción viaja como archivo .po en git.
