#!/usr/bin/env python3
"""Delta determinista upstream↔catálogo aprobado (mantenimiento incremental, SIN LLM).

Compara el universo FRESCO de una app (`.artifacts/freshpot/<app>.jsonl`, extraído con
`extract_fresh_pot.py`) contra la fuente de verdad autoritativa: los `review/*.csv`. NO crea ni
lee ninguna copia paralela de traducciones — el CSV es el baseline. Un manifiesto pequeño
(`catalog_baseline.json`) solo guarda punteros (`upstream_rev` + hash del catálogo aprobado) para
la ruta rápida "no-op": si el commit del upstream y el hash del CSV no cambiaron, no hay nada que revisar.

Identidad = la MISMA `entry_key` de `build_catalog.py` (SHA1[:16] de JSON canónico
{app,msgctxt,msgid,msgid_plural}). Clasifica cada cambio de forma mecánica:

  - sin cambios       : entry_key en CSV y en fresco (misma identidad exacta)
  - nueva             : entry_key solo en fresco, sin match secundario
  - eliminada         : entry_key solo en CSV (huérfana/obsoleta), sin match secundario
  - cambio_contexto   : mismo msgid en added y removed con msgctxt distinto
  - cambio_plural     : mismo (ctx,msgid) added/removed que difiere solo en msgid_plural
  - cambio_placeholders: par added/removed con texto base idéntico pero placeholders distintos
  - posible_rename    : par added/removed de alta similitud textual (SequenceMatcher ≥ umbral)

Solo `nueva + posible_rename + cambio_placeholders + cambio_contexto/plural` requieren criterio
lingüístico; `sin cambios` conserva su traducción aprobada (round-trip de build_catalog) y
`eliminada` sale del `.po`. Todo es solo lectura sobre datos locales; no toca BD ni apps de terceros.

Uso:
    env/bin/python scripts/diff_upstream.py --app helpdesk [--fresh-dir ...] [--review-dir ...]
        [--out-prefix working_docs/active/helpdesk_delta] [--baseline ...] [--allow-stale]
        [--similarity 0.85] [--update-baseline]
"""

import argparse
import csv
import difflib
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_catalog import (  # identidad/placeholders idénticos
	BLOCKS,
	app_meta,
	entry_key,
	extract_placeholders,
)

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

CONFIG_PATH = REPO / "scripts" / "extract_config.json"
FRESH_DEFAULT = REPO / ".artifacts" / "freshpot"
REVIEW_DEFAULT = REPO / "review"
BASELINE_DEFAULT = REPO / "working_docs" / "active" / "catalog_baseline.json"


def load_app_config(app):
	"""Registro único = extract_config.json. Acepta lista de strings (legado) u objetos por app."""
	cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
	entries = []
	for a in cfg.get("apps") or []:
		entries.append({"app": a} if isinstance(a, str) else dict(a))
	names = [e["app"] for e in entries]
	if app not in names:
		sys.exit(f"FATAL: app '{app}' no está en {CONFIG_PATH} (registro único de apps)")
	return next(e for e in entries if e["app"] == app), names


def load_fresh(app, fresh_dir):
	"""Universo fresco: (ctx,msgid) -> {plural, locs}. entry_key recomputada con la función oficial."""
	fp = Path(fresh_dir) / f"{app}.jsonl"
	if not fp.exists():
		sys.exit(f"FATAL: falta artefacto fresco {fp} (correr extract_fresh_pot.py)")
	out = {}
	for line in open(fp, encoding="utf-8"):
		r = json.loads(line)
		ctx, mid, plural = r["ctx"], r["msgid"], r.get("plural", "")
		ek = entry_key(app, ctx, mid, plural)
		out[ek] = {"ctx": ctx, "msgid": mid, "plural": plural, "locs": r.get("locs", [])}
	return out


def validate_freshness(app, fresh_dir, allow_stale):
	"""El artefacto fresco debe ser del HEAD actual del upstream (mismo control que build_catalog)."""
	mpath = Path(fresh_dir) / "manifest.json"
	if not mpath.exists():
		sys.exit(f"FATAL: falta {mpath} (correr extract_fresh_pot.py)")
	manifest = json.loads(mpath.read_text(encoding="utf-8"))
	by_app = {a["app"]: a for a in manifest.get("apps", [])}
	a = by_app.get(app)
	if not a or a.get("status") != "ok":
		sys.exit(f"FATAL: app {app} sin artefacto OK en el manifiesto fresco")
	art = Path(fresh_dir) / f"{app}.jsonl"
	if hashlib.sha256(art.read_bytes()).hexdigest() != a["sha256"]:
		sys.exit(f"FATAL: sha256 del artefacto {app} no coincide con el manifiesto (alterado/parcial)")
	head = app_meta(app)["commit"]
	art_commit = a.get("commit", "")
	stale = head and art_commit and not (art_commit.startswith(head) or head.startswith(art_commit))
	if stale:
		msg = (
			f"artefacto de {app} es del commit {art_commit} pero HEAD upstream es {head} "
			"(extracción vieja: re-extraer para un delta real)"
		)
		if not allow_stale:
			sys.exit("FATAL: " + msg)
		print("WARN(stale): " + msg)
	return {
		"upstream_rev": art_commit,
		"branch": a.get("branch", ""),
		"version": a.get("version", ""),
		"fresh_count": a.get("count", 0),
		"head": head,
	}


def load_csv_app(app, review_dir):
	"""Filas del catálogo autoritativo para la app (en cualquier bloque). Fuente de verdad = CSV."""
	out = {}
	for b in BLOCKS:
		p = Path(review_dir) / f"{b}.csv"
		if not p.exists():
			continue
		with open(p, encoding="utf-8", newline="") as fh:
			for row in csv.DictReader(fh):
				if row.get("app") != app:
					continue
				ek = row["entry_key"]
				msgstr = (row.get("proposed_translation") or "").strip() or (
					row.get("current_translation") or ""
				).strip()
				out[ek] = {
					"ctx": row.get("msgctxt", ""),
					"msgid": row.get("msgid", ""),
					"plural": row.get("msgid_plural", ""),
					"status": row.get("status", ""),
					"human": row.get("human_authored", "") == "sí",
					"has_translation": bool(msgstr),
					"block": b,
				}
	return out


def catalog_sha(csv_rows):
	"""Hash estable del catálogo aprobado de la app (identidad + traducción-presente + estado)."""
	payload = sorted(
		f"{ek}|{v['ctx']}|{v['msgid']}|{v['plural']}|{int(v['has_translation'])}|{v['status']}"
		for ek, v in csv_rows.items()
	)
	return hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest()


def norm_text(s):
	return re.sub(r"\s+", " ", (s or "").strip().lower())


def base_no_placeholders(s):
	"""Texto con los placeholders reemplazados por un centinela, para aislar cambios de placeholder."""
	toks = extract_placeholders(s)
	work = norm_text(s)
	# aproximación estable: sustituye cada token detectado por ⟦ph⟧ (orden por longitud desc evita solapes)
	for tok in sorted(set(toks.elements()), key=len, reverse=True):
		work = work.replace(norm_text(tok), " ⟦ph⟧ ")
	return re.sub(r"\s+", " ", work).strip()


def classify(added, removed, similarity):
	"""Empareja added/removed por identidad parcial → clases mecánicas. Determinista y sin LLM."""
	results = []
	a_left, r_left = dict(added), dict(removed)

	# 1) cambio de contexto / plural: mismo msgid presente en ambos lados
	r_by_mid = defaultdict(list)
	for ek, v in r_left.items():
		r_by_mid[v["msgid"]].append(ek)
	for ek_a, va in list(a_left.items()):
		cands = r_by_mid.get(va["msgid"], [])
		match = None
		for ek_r in cands:
			if ek_r not in r_left:
				continue
			vr = r_left[ek_r]
			if vr["ctx"] != va["ctx"]:
				match, kind = ek_r, "cambio_contexto"
				break
			if vr["plural"] != va["plural"]:
				match, kind = ek_r, "cambio_plural"
				break
		if match:
			vr = r_left.pop(match)
			a_left.pop(ek_a)
			results.append(
				{
					"class": kind,
					"ek_old": match,
					"ek_new": ek_a,
					"msgid_old": vr["msgid"],
					"msgid_new": va["msgid"],
					"ctx_old": vr["ctx"],
					"ctx_new": va["ctx"],
					"ph_old": ";".join(sorted(extract_placeholders(vr["msgid"]).elements())),
					"ph_new": ";".join(sorted(extract_placeholders(va["msgid"]).elements())),
					"status_csv": vr["status"],
					"similarity": 1.0,
				}
			)

	# 2) cambio de placeholders: texto base idéntico, placeholders distintos
	r_by_base = defaultdict(list)
	for ek, v in r_left.items():
		r_by_base[base_no_placeholders(v["msgid"])].append(ek)
	for ek_a, va in list(a_left.items()):
		base = base_no_placeholders(va["msgid"])
		cands = [ek for ek in r_by_base.get(base, []) if ek in r_left]
		for ek_r in cands:
			vr = r_left[ek_r]
			if extract_placeholders(vr["msgid"]) != extract_placeholders(va["msgid"]):
				r_left.pop(ek_r)
				a_left.pop(ek_a)
				results.append(
					{
						"class": "cambio_placeholders",
						"ek_old": ek_r,
						"ek_new": ek_a,
						"msgid_old": vr["msgid"],
						"msgid_new": va["msgid"],
						"ctx_old": vr["ctx"],
						"ctx_new": va["ctx"],
						"ph_old": ";".join(sorted(extract_placeholders(vr["msgid"]).elements())),
						"ph_new": ";".join(sorted(extract_placeholders(va["msgid"]).elements())),
						"status_csv": vr["status"],
						"similarity": 1.0,
					}
				)
				break

	# 3) posible rename: mejor similitud textual por encima del umbral (mismo ctx)
	r_items = list(r_left.items())
	for ek_a, va in list(a_left.items()):
		best, best_ratio = None, 0.0
		na = norm_text(va["msgid"])
		for ek_r, vr in r_items:
			if ek_r not in r_left or vr["ctx"] != va["ctx"]:
				continue
			ratio = difflib.SequenceMatcher(None, na, norm_text(vr["msgid"])).ratio()
			if ratio > best_ratio:
				best, best_ratio = ek_r, ratio
		if best and best_ratio >= similarity:
			vr = r_left.pop(best)
			a_left.pop(ek_a)
			results.append(
				{
					"class": "posible_rename",
					"ek_old": best,
					"ek_new": ek_a,
					"msgid_old": vr["msgid"],
					"msgid_new": va["msgid"],
					"ctx_old": vr["ctx"],
					"ctx_new": va["ctx"],
					"ph_old": ";".join(sorted(extract_placeholders(vr["msgid"]).elements())),
					"ph_new": ";".join(sorted(extract_placeholders(va["msgid"]).elements())),
					"status_csv": vr["status"],
					"similarity": round(best_ratio, 3),
				}
			)

	# 4) restos: genuinamente nuevas / eliminadas
	for ek_a, va in a_left.items():
		results.append(
			{
				"class": "nueva",
				"ek_old": "",
				"ek_new": ek_a,
				"msgid_old": "",
				"msgid_new": va["msgid"],
				"ctx_old": "",
				"ctx_new": va["ctx"],
				"ph_old": "",
				"ph_new": ";".join(sorted(extract_placeholders(va["msgid"]).elements())),
				"status_csv": "",
				"similarity": 0.0,
			}
		)
	for ek_r, vr in r_left.items():
		results.append(
			{
				"class": "eliminada",
				"ek_old": ek_r,
				"ek_new": "",
				"msgid_old": vr["msgid"],
				"msgid_new": "",
				"ctx_old": vr["ctx"],
				"ctx_new": "",
				"ph_old": ";".join(sorted(extract_placeholders(vr["msgid"]).elements())),
				"ph_new": "",
				"status_csv": vr["status"],
				"similarity": 0.0,
			}
		)
	return results


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--app", required=True)
	ap.add_argument("--fresh-dir", default=str(FRESH_DEFAULT))
	ap.add_argument("--review-dir", default=str(REVIEW_DEFAULT))
	ap.add_argument("--out-prefix", default="")
	ap.add_argument("--baseline", default=str(BASELINE_DEFAULT))
	ap.add_argument("--similarity", type=float, default=0.85)
	ap.add_argument("--allow-stale", action="store_true")
	ap.add_argument("--update-baseline", action="store_true")
	args = ap.parse_args()

	app = args.app
	cfg, _all_apps = load_app_config(app)
	fresh_meta = validate_freshness(app, args.fresh_dir, args.allow_stale)
	fresh = load_fresh(app, args.fresh_dir)
	csv_rows = load_csv_app(app, args.review_dir)
	cur_sha = catalog_sha(csv_rows)

	# ruta rápida no-op: rev de upstream y hash del catálogo sin cambios desde el último baseline.
	baseline = {}
	if Path(args.baseline).exists():
		baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
	prev = baseline.get(app, {})
	noop = prev.get("upstream_rev") == fresh_meta["upstream_rev"] and prev.get("catalog_sha256") == cur_sha
	if noop:
		print(
			f"NO-OP {app}: upstream_rev={fresh_meta['upstream_rev']} y catalog_sha sin cambios; nada que revisar."
		)

	csv_keys, fresh_keys = set(csv_rows), set(fresh)
	unchanged = csv_keys & fresh_keys
	added = {ek: fresh[ek] for ek in fresh_keys - csv_keys}
	removed = {ek: csv_rows[ek] for ek in csv_keys - fresh_keys}
	changes = classify(added, removed, args.similarity)

	counts = Counter(c["class"] for c in changes)
	counts["sin_cambios"] = len(unchanged)
	review_classes = {"nueva", "posible_rename", "cambio_placeholders", "cambio_contexto", "cambio_plural"}
	needs_review = [c for c in changes if c["class"] in review_classes]

	summary = {
		"app": app,
		"published": cfg.get("published", False),
		"branch": fresh_meta["branch"] or cfg.get("branch", ""),
		"upstream_rev": fresh_meta["upstream_rev"],
		"version": fresh_meta["version"],
		"csv_rows": len(csv_rows),
		"fresh_rows": len(fresh),
		"catalog_sha256": cur_sha,
		"counts": dict(counts),
		"requiere_revision_LLM": len(needs_review),
		"sin_cambios_pct": round(100 * len(unchanged) / max(len(fresh), 1), 1),
		"noop": noop,
	}

	prefix = Path(args.out_prefix) if args.out_prefix else (REPO / "working_docs" / "active" / f"{app}_delta")
	prefix.parent.mkdir(parents=True, exist_ok=True)
	Path(str(prefix) + ".json").write_text(
		json.dumps({"summary": summary, "changes_sample": changes[:200]}, ensure_ascii=False, indent=2),
		encoding="utf-8",
	)
	cols = [
		"class",
		"similarity",
		"status_csv",
		"ctx_old",
		"ctx_new",
		"ph_old",
		"ph_new",
		"msgid_old",
		"msgid_new",
		"ek_old",
		"ek_new",
	]
	with open(str(prefix) + ".csv", "w", encoding="utf-8", newline="") as fh:
		w = csv.DictWriter(fh, fieldnames=cols)
		w.writeheader()
		for c in sorted(changes, key=lambda x: (x["class"], x["msgid_new"] or x["msgid_old"])):
			w.writerow({k: c.get(k, "") for k in cols})

	if args.update_baseline:
		baseline[app] = {
			"upstream_rev": fresh_meta["upstream_rev"],
			"branch": summary["branch"],
			"version": fresh_meta["version"],
			"catalog_sha256": cur_sha,
			"approved_count": sum(1 for v in csv_rows.values() if v["has_translation"]),
		}
		Path(args.baseline).write_text(
			json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
		)

	print(
		f"DELTA {app}: csv={len(csv_rows)} fresco={len(fresh)} | "
		+ " ".join(
			f"{k}={counts[k]}"
			for k in [
				"sin_cambios",
				"nueva",
				"eliminada",
				"cambio_contexto",
				"cambio_plural",
				"cambio_placeholders",
				"posible_rename",
			]
		)
	)
	print(f"  requieren criterio lingüístico (LLM): {len(needs_review)} | salida: {prefix}.csv / .json")


if __name__ == "__main__":
	main()
