# Manual de usuario

Esta app no tiene interfaz propia. Su efecto es que los textos de Frappe/ERPNext/HRMS/
Helpdesk/CRM aparecen con la traducción local aprobada cuando el idioma del sitio o del
usuario es español.

## Activación

1. Instalar la app en el sitio **después** de las apps base.
2. Compilar el catálogo: `bench compile-po-to-mo --app buzola_translations`.
3. `bench build --app buzola_translations` y `bench --site <site> clear-cache`.

(Contenido en desarrollo — primera etapa: auditoría y metodología.)
