#!/usr/bin/env python3
"""Verificador NO destructivo del orden de resolución de traducciones.

Confirma que `buzola_translations` esté instalada y quede AL FINAL de `installed_apps` de un sitio
(para que su `.mo` prevalezca sobre frappe/erpnext/hrms). Solo LECTURA: consulta el orden vía
`bench --site <site> execute frappe.get_installed_apps`. NO modifica el orden ni la BD. No es un hook ni
forma parte de la ejecución normal de la app; se ejecuta manualmente en operación/CI.

Uso:
    env/bin/python scripts/check_translation_order.py --site <site> [--app buzola_translations]
Salida: exit 0 si está instalada y al final; exit!=0 con mensaje claro en caso contrario.
"""

import argparse
import json
import subprocess
import sys

TARGET = "buzola_translations"


def check_order(installed, app=TARGET):
	"""Función pura y testeable. Devuelve (ok, motivo)."""
	if app not in installed:
		return False, f"{app} NO está instalada en el sitio"
	if installed[-1] != app:
		idx = installed.index(app)
		after = installed[idx + 1 :]
		return (
			False,
			f"{app} NO está al final (posición {idx} de {len(installed)}); apps posteriores: {after}",
		)
	return True, f"{app} está instalada y AL FINAL de installed_apps ({len(installed)} apps)"


def get_installed_apps(site, bench_path="/home/erpnext/frappe-bench-v16"):
	"""Consulta soportada, solo lectura."""
	res = subprocess.run(
		["bench", "--site", site, "execute", "frappe.get_installed_apps"],
		capture_output=True,
		text=True,
		cwd=bench_path,
		timeout=120,
	)
	# la salida del execute imprime el repr de la lista; tomar la última línea con corchetes
	for line in reversed(res.stdout.splitlines()):
		line = line.strip()
		if line.startswith("[") and line.endswith("]"):
			return json.loads(line.replace("'", '"'))
	raise RuntimeError(f"No se pudo leer installed_apps de {site}: {res.stdout[-300:]} {res.stderr[-300:]}")


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--site", required=True)
	ap.add_argument("--app", default=TARGET)
	ap.add_argument("--bench", default="/home/erpnext/frappe-bench-v16")
	args = ap.parse_args()
	installed = get_installed_apps(args.site, args.bench)
	ok, reason = check_order(installed, args.app)
	print(("OK: " if ok else "ERROR: ") + reason)
	print("installed_apps:", installed)
	sys.exit(0 if ok else 1)


if __name__ == "__main__":
	main()
