#!/usr/bin/env python3
"""Extrae el POT OFICIAL FRESCO de cada app (universo vigente) a artefactos NO versionados + manifiesto.

Reproducible y fail-fast:
- Apps / directorio de salida vienen de `scripts/extract_config.json` (sin rutas absolutas de esta
  máquina; el repo se localiza con `frappe.get_app_path`). Añadir una app = editar el JSON.
- Limpia únicamente sus propios artefactos previos (jsonl de las apps configuradas + manifest).
- Si una app no puede extraerse, se registra el error, NO se imprime éxito y el manifiesto queda
  `overall_ok=false`. Solo con todas las apps OK imprime el centinela `EXTRACT_FRESH_OK`.
- Ordena las entradas de forma determinista (por (ctx, msgid)); calcula SHA256 por artefacto.
- Manifiesto: app, versión, rama, commit, conteo y SHA256 de cada artefacto.

Usa el mismo extractor que `bench generate-pot-file` (`babel.extract_from_dir` + `method_map` de
`babel_extractors.csv` + filtro gitignore oficial + `ignore_translatable_strings_from`) sobre el árbol
REAL de la app (limpio, en HEAD), en memoria. NO escribe POT en las apps ni modifica sus repos.

Salida `<output_dir>/<app>.jsonl` — una línea JSON por entrada única `(ctx, msgid)`:
    {"ctx","msgid","plural","locs":[...],"comments":[...]}
`comments` = comentarios del extractor (DocType/label/opción/descripción/tipo de campo). NO son flags.

Ejecutar dentro del bench (solo lectura; no escribe en BD):
    echo "exec(open('.../scripts/extract_fresh_pot.py').read())" | bench --site <site> console
"""


def run():
	import hashlib
	import json
	import os
	import subprocess
	from pathlib import Path

	import frappe
	from babel.messages.extract import DEFAULT_KEYWORDS, extract_from_dir
	from frappe.gettext.translate import (
		_get_ignored_strings,
		get_is_gitignored_function_for_app,
		get_method_map,
	)

	repo_root = Path(frappe.get_app_path("buzola_translations")).parent
	config = json.loads((repo_root / "scripts" / "extract_config.json").read_text(encoding="utf-8"))
	apps = list(config.get("apps") or [])
	if not apps:
		raise SystemExit("FATAL: extract_config.json no define ninguna app")
	if len(apps) != len(set(apps)):
		raise SystemExit(f"FATAL: apps duplicadas en extract_config.json: {sorted(apps)}")
	outdir = Path(config["output_dir"]) if config.get("output_dir") else repo_root / ".artifacts" / "freshpot"
	outdir.mkdir(parents=True, exist_ok=True)

	# Limpieza acotada: solo nuestros artefactos previos (jsonl de apps configuradas + manifest).
	for stale in [outdir / "manifest.json", *(outdir / f"{a}.jsonl" for a in apps)]:
		if stale.exists():
			stale.unlink()

	def app_git(app):
		d = Path(frappe.get_pymodule_path(app, ".."))
		ver = ""
		init = d / app / "__init__.py"
		if init.exists():
			import re

			m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init.read_text())
			ver = m.group(1) if m else ""

		def g(*a):
			return subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True).stdout.strip()

		return ver, g("branch", "--show-current"), g("rev-parse", "--short", "HEAD")

	def extract(app):
		app_path = frappe.get_pymodule_path(app, "..")
		is_gitignored = get_is_gitignored_function_for_app(app)

		def dfilter(dirpath):
			if is_gitignored(str(dirpath)):
				return False
			base = os.path.basename(dirpath)
			return not (base.startswith(".") or base.startswith("_"))

		mm = ([] if app == "frappe" else get_method_map(app)) + get_method_map("frappe")
		kw = DEFAULT_KEYWORDS.copy()
		kw["_lt"] = None
		try:
			ig = _get_ignored_strings(app)
		except Exception:
			ig = set()
		agg = {}
		for fn, ln, msg, comments, ctx in extract_from_dir(
			app_path, mm, keywords=kw, directory_filter=dfilter
		):
			if not msg or (msg, ctx) in ig:
				continue
			is_pl = isinstance(msg, (tuple, list))
			mid = msg[0] if is_pl else msg
			plural = msg[1] if is_pl else ""
			k = (ctx or "", mid)
			e = agg.setdefault(k, {"plural": plural, "locs": set(), "comments": set()})
			if plural and not e["plural"]:
				e["plural"] = plural
			if fn:
				e["locs"].add(f"{fn}:{ln}" if ln else str(fn))
			for c in comments or []:
				if c:
					e["comments"].add(c)
		return agg

	manifest = {"generated_ordering": "sorted-by-(ctx,msgid)", "output_dir": str(outdir), "apps": []}
	overall_ok = True
	for app in apps:
		try:
			agg = extract(app)
			ver, branch, commit = app_git(app)
			path = outdir / f"{app}.jsonl"
			# Orden determinista por (ctx, msgid).
			with open(path, "w", encoding="utf-8") as fh:
				for ctx, mid in sorted(agg):
					e = agg[(ctx, mid)]
					fh.write(
						json.dumps(
							{
								"ctx": ctx,
								"msgid": mid,
								"plural": e["plural"],
								"locs": sorted(e["locs"]),
								"comments": sorted(e["comments"]),
							},
							ensure_ascii=False,
							sort_keys=True,
						)
						+ "\n"
					)
			sha = hashlib.sha256(path.read_bytes()).hexdigest()
			manifest["apps"].append(
				{
					"app": app,
					"version": ver,
					"branch": branch,
					"commit": commit,
					"count": len(agg),
					"sha256": sha,
					"status": "ok",
				}
			)
		except Exception as ex:
			overall_ok = False
			manifest["apps"].append(
				{"app": app, "status": "error", "error": f"{type(ex).__name__}: {str(ex)[:200]}"}
			)

	manifest["overall_ok"] = overall_ok
	(outdir / "manifest.json").write_text(
		json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
	)

	if overall_ok:
		print("EXTRACT_FRESH_OK", str(outdir))
	else:
		errs = [a for a in manifest["apps"] if a["status"] != "ok"]
		print("EXTRACT_FRESH_FAILED", json.dumps(errs, ensure_ascii=False))
		# Señal de fallo adicional (el generador es el gate duro que valida el manifiesto).
		raise SystemExit(1)


run()
