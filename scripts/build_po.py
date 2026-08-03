#!/usr/bin/env python3
"""Generador determinista del catálogo oficial `buzola_translations/locale/es.po` desde los CSV aprobados.

Fuente: review/01..04 + filas frappe/erpnext/hrms de review/06. Solo estados elegibles con propuesta.
Excluye po_huérfana/ambigua/conflicto/especializada/vacías y TODO Helpdesk/CRM.

- Auditoría de colisiones por identidad Gettext (msgctxt,msgid,msgid_plural): dedup si idéntico; CONFLICTO
  (y HALT) si difieren.
- Escribe el .po con babel (misma librería que Frappe); orden estable; sin fuzzy; msgctxt/plurales preservados.
- Manifiesto JSON con conteos, exclusiones, conflictos, SHA256 y commits/versiones fuente.

Uso: env/bin/python scripts/build_po.py [--audit-only]
"""

import argparse
import csv
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po

REPO = Path(__file__).resolve().parent.parent
BENCH = REPO.parent.parent
APPS = {"frappe", "erpnext", "hrms"}
ELIGIBLE = {
	"existente correcta",
	"existente mejorable",
	"traducción propuesta",
	"igual al inglés válida",
	"texto no extraíble",
}
CSVS = [
	"01_frappe_plataforma",
	"02_erpnext_operaciones",
	"03_erpnext_contabilidad_finanzas",
	"04_hrms",
	"06_conflictos_historico_especializada",
]
PLACEHOLDER_SPLIT = " || "
LOCALE = REPO / "buzola_translations" / "locale" / "es.po"
MANIFEST = REPO / "working_docs" / "active" / "po_manifest.json"

sys.path.insert(0, str(REPO / "scripts"))
from build_catalog import extract_placeholders


def app_meta(app):
	d = BENCH / "apps" / app
	ver = ""
	init = d / app / "__init__.py"
	if init.exists():
		m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init.read_text())
		ver = m.group(1) if m else ""

	def g(*a):
		return subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True).stdout.strip()

	return {
		"version": ver,
		"branch": g("branch", "--show-current"),
		"commit": g("rev-parse", "--short", "HEAD"),
	}


def load_rows():
	rows = []
	for b in CSVS:
		for r in csv.DictReader(open(REPO / "review" / f"{b}.csv", encoding="utf-8")):
			rows.append(r)
	return rows


def locations(r):
	locs = []
	for ref in (r["all_source_references"] or r["source_reference"] or "").split(PLACEHOLDER_SPLIT):
		ref = ref.strip()
		if not ref:
			continue
		if ":" in ref and ref.rsplit(":", 1)[1].isdigit():
			f, ln = ref.rsplit(":", 1)
			locs.append((f, int(ln)))
		else:
			locs.append((ref, 0))
	return locs[:5]


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--audit-only", action="store_true")
	args = ap.parse_args()
	rows = load_rows()

	excl = {"no_app": 0, "estado": 0, "sin_proposed": 0, "helpdesk_crm": 0}
	per_app = dict.fromkeys(APPS, 0)
	elig = []
	for r in rows:
		app = r["app"]
		if app in ("helpdesk", "crm"):
			excl["helpdesk_crm"] += 1
			continue
		if app not in APPS:
			excl["no_app"] += 1
			continue
		if r["status"] not in ELIGIBLE:
			excl["estado"] += 1
			continue
		if not r["proposed_translation"].strip():
			excl["sin_proposed"] += 1
			continue
		elig.append(r)
		per_app[app] += 1

	# auditoría de colisiones por identidad Gettext
	ident = {}
	for r in elig:
		key = (r["msgctxt"], r["msgid"], r["msgid_plural"])
		ident.setdefault(key, []).append(r)
	conflicts, dedups = [], 0
	ph_loss = []
	final = {}
	for key, group in ident.items():
		props = {g["proposed_translation"] for g in group}
		pplurals = {g["proposed_plural_translations"] for g in group}
		if len(props) > 1 or len(pplurals) > 1:
			conflicts.append(
				{
					"msgctxt": key[0],
					"msgid": key[1][:80],
					"msgid_plural": key[2][:40],
					"apps": sorted({g["app"] for g in group}),
					"variantes": [
						{
							"app": g["app"],
							"entry_key": g["entry_key"],
							"proposed": g["proposed_translation"][:80],
							"ref": g["source_reference"],
						}
						for g in group
					],
				}
			)
			continue
		if len(group) > 1:
			dedups += len(group) - 1
		final[key] = group[0]
	# placeholders
	for r in final.values():
		if extract_placeholders(r["msgid"]) - extract_placeholders(r["proposed_translation"]):
			ph_loss.append(r["entry_key"])

	print(
		f"elegibles={len(elig)} por_app={per_app} dedups={dedups} conflictos={len(conflicts)} ph_loss={len(ph_loss)}"
	)
	print(f"exclusiones={excl}")
	if conflicts:
		(REPO / "working_docs" / "active" / "po_conflicts.json").write_text(
			json.dumps(conflicts, ensure_ascii=False, indent=2), encoding="utf-8"
		)
		print(f"CONFLICTOS registrados en working_docs/active/po_conflicts.json ({len(conflicts)}). HALT.")
	if args.audit_only:
		return
	if conflicts:
		sys.exit("HALT: hay conflictos Gettext; resolver antes de generar.")
	if ph_loss:
		sys.exit(f"HALT: pérdida de placeholders en {ph_loss[:5]}")

	# construir catálogo (orden estable por (msgctxt,msgid,plural))
	# fechas FIJAS (sin now()) -> reproducibilidad byte-idéntica en el tiempo
	fixed = datetime.datetime(2026, 8, 2, 0, 0, 0, tzinfo=datetime.timezone.utc)
	buzola_ver = ""
	m = re.search(
		r'__version__\s*=\s*["\']([^"\']+)["\']', (REPO / "buzola_translations" / "__init__.py").read_text()
	)
	if m:
		buzola_ver = m.group(1)
	cat = Catalog(
		locale="es",
		charset="utf-8",
		project="buzola_translations",
		version=buzola_ver,
		msgid_bugs_address="it@buzola.mx",
		copyright_holder="Buzola",
		creation_date=fixed,
		revision_date=fixed,
		last_translator="Buzola <it@buzola.mx>",
		language_team="es <it@buzola.mx>",
	)
	cat.fuzzy = False
	for key in sorted(final, key=lambda k: (k[0], k[1], k[2])):
		r = final[key]
		ctx = r["msgctxt"] or None
		if r["msgid_plural"]:
			forms = [x for x in (r["proposed_plural_translations"] or "").split(PLACEHOLDER_SPLIT) if x]
			string = (
				tuple([r["proposed_translation"], *forms])
				if forms
				else (r["proposed_translation"], r["proposed_translation"])
			)
			cat.add((r["msgid"], r["msgid_plural"]), string=string, context=ctx, locations=locations(r))
		else:
			cat.add(r["msgid"], string=r["proposed_translation"], context=ctx, locations=locations(r))

	LOCALE.parent.mkdir(parents=True, exist_ok=True)
	with open(LOCALE, "wb") as fh:
		write_po(fh, cat, sort_output=True, width=0, omit_header=False, include_previous=False)
	sha = hashlib.sha256(LOCALE.read_bytes()).hexdigest()

	manifest = {
		"apps": {a: app_meta(a) for a in sorted(APPS)},
		"elegibles_por_app": per_app,
		"total_entradas_po": len(final),
		"dedups": dedups,
		"conflictos": len(conflicts),
		"exclusiones": excl,
		"po_sha256": sha,
		"po_path": str(LOCALE.relative_to(REPO)),
	}
	MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
	print(f"PO escrito: {LOCALE} | entradas={len(final)} | sha256={sha[:16]}")


if __name__ == "__main__":
	main()
