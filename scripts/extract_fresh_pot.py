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
	import io
	import json
	import os
	import re
	import subprocess
	from pathlib import Path

	import frappe
	from babel.messages.extract import DEFAULT_KEYWORDS, extract_from_dir
	from frappe.gettext.extractors.html_template import extract as html_tpl_extract
	from frappe.gettext.extractors.javascript import extract as js_src_extract
	from frappe.gettext.translate import (
		_get_ignored_strings,
		get_is_gitignored_function_for_app,
		get_method_map,
	)

	repo_root = Path(frappe.get_app_path("buzola_translations")).parent
	config = json.loads((repo_root / "scripts" / "extract_config.json").read_text(encoding="utf-8"))
	# Registro único de apps: acepta objetos {app,upstream,branch,published,exceptions} o strings (legado).
	apps = [a if isinstance(a, str) else a["app"] for a in (config.get("apps") or [])]
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

	# --- Wrapper .vue: compone TRES extractores OFICIALES de Frappe (sin regex propio) ---
	# html_template.extract (comportamiento oficial de .vue) omite: (a) backticks y llamadas __()
	# multilínea del bloque <script>, y (b) llamadas __() multilínea dentro de expresiones {{ ... }}
	# del <template>. Se unen con javascript.extract (el de .js) corrido: (1) sobre cada <script> y
	# (2) sobre cada expresión {{ ... }} del template que contenga __(. Todo con offset de línea, dedup
	# por (funcname,msgid) para NO duplicar lo que html ya obtuvo, y filtro de literales con interpolación
	# ${...} (no traducibles estáticamente). Verificado: 0 errores; solo ADICIONES de texto visible real.
	script_block_re = re.compile(r"<script\b[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
	mustache_re = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)

	def _msgkey(messages):
		return messages if isinstance(messages, str) else tuple(messages)

	def _has_interp(messages):
		vals = [messages] if isinstance(messages, str) else list(messages)
		return any(isinstance(v, str) and "${" in v for v in vals)

	def vue_extract(fileobj, keywords, comment_tags, options):
		data = fileobj.read()
		seen = set()
		for lineno, funcname, messages, comments in html_tpl_extract(
			io.BytesIO(data), keywords, comment_tags, options
		):
			seen.add((funcname, _msgkey(messages)))
			yield lineno, funcname, messages, comments
		text = data.decode("utf-8", errors="replace")
		for mblk in script_block_re.finditer(text):
			offset = text[: mblk.start(1)].count("\n")
			try:
				results = list(
					js_src_extract(io.BytesIO(mblk.group(1).encode("utf-8")), keywords, comment_tags, options)
				)
			except Exception:
				continue
			for lineno, funcname, messages, comments in results:
				if _has_interp(messages):
					continue
				key = (funcname, _msgkey(messages))
				if key in seen:
					continue
				seen.add(key)
				yield lineno + offset, funcname, messages, comments
		# 3) expresiones {{ ... }} del <template> que contienen __() (multilínea que html_template omite).
		for mmus in mustache_re.finditer(text):
			expr = mmus.group(1)
			if "__(" not in expr:
				continue
			offset = text[: mmus.start(1)].count("\n")
			try:
				results = list(
					js_src_extract(io.BytesIO(expr.encode("utf-8")), keywords, comment_tags, options)
				)
			except Exception:
				continue
			for lineno, funcname, messages, comments in results:
				if _has_interp(messages):
					continue
				key = (funcname, _msgkey(messages))
				if key in seen:
					continue
				seen.add(key)
				yield lineno + offset, funcname, messages, comments

	def extract(app):
		app_path = frappe.get_pymodule_path(app, "..")
		is_gitignored = get_is_gitignored_function_for_app(app)

		def dfilter(dirpath):
			if is_gitignored(str(dirpath)):
				return False
			base = os.path.basename(dirpath)
			return not (base.startswith(".") or base.startswith("_"))

		# Cobertura SPA: el method_map oficial de Frappe mapea .js/.vue pero NO .ts/.tsx. Los SPA
		# modernos (helpdesk/crm) escriben __() en TypeScript, invisible al extractor por defecto.
		# Reutilizamos EXACTAMENTE el mismo extractor JS oficial (el de .js) para .ts/.tsx — verificado
		# sobre los 67 .ts/.tsx reales de helpdesk (0 errores). Sin regex propio: es el tokenizer JS de
		# babel que ya usa Frappe. `.vue` se remapea a `vue_extract` (prepend → gana sobre el oficial).
		ts_methods = [
			("**.ts", "frappe.gettext.extractors.javascript.extract"),
			("**.tsx", "frappe.gettext.extractors.javascript.extract"),
		]
		# ORDEN CRÍTICO — NO reordenar `ts_methods`: DEBE ir AL FINAL, tras el method_map oficial.
		# Ponerlo antes de get_method_map("frappe") hace que erpnext (frontend banking/ con .ts/.tsx)
		# pierda ~358 cadenas de forma determinista (comprobado). `.vue` sí va al frente para ganar sobre
		# el `**.vue`→html_template oficial. Efecto verificado: erpnext Δ0; frappe/hrms/helpdesk/crm solo
		# ADICIONES; 0 eliminadas, 0 duplicados, 0 interpolación ${…}.
		mm = (
			[("**.vue", vue_extract)]
			+ ([] if app == "frappe" else get_method_map(app))
			+ get_method_map("frappe")
			+ ts_methods
		)
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
