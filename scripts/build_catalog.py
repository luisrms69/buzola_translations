#!/usr/bin/env python3
"""Catálogo COMPLETO de revisión humana + inventario de cobertura (integridad + reproducibilidad).

Universo PRINCIPAL = extracción OFICIAL FRESCA (`extract_fresh_pot.py` → `<fresh-dir>/<app>.jsonl`
+ `manifest.json`, artefactos NO versionados), unida con las traducciones de `es.po`. El `main.pot`
versionado NO se usa como universo.

Reglas de integridad (este generador es fail-fast):
- Valida el manifiesto ANTES de generar: existencia de artefactos, SHA256 y que el commit coincide con
  el HEAD actual de cada app (rechaza artefactos viejos/parciales/de otro commit).
- Genera primero en un directorio temporal; solo reemplaza los CSV si TODAS las validaciones pasan.
- Falla (exit != 0) ante: colisión de entry_key, filas duplicadas, estado inválido, propuesta humana que
  pierde un placeholder del origen, o reconciliación incorrecta (filas != Σ universo != entry_key únicos).
- Orden de filas estable (app, msgctxt, msgid) → ejecución repetible sin cambios de diff.

Capa humana (los 6 CSV son la fuente autoritativa):
- Se leen los CSV existentes; las filas con `human_authored=sí` preservan sus columnas humanas por
  `entry_key` (respaldo: identidad Gettext completa (app,msgctxt,msgid,msgid_plural)).
- Si aún no hay capa humana en los CSV (bootstrap), se siembra UNA vez desde `human_decisions.py`
  (legacy), por identidad EXACTA — nunca por msgid a secas → no se propaga a varios contextos.
- Las heurísticas NUNCA sobrescriben una decisión humana. Las decisiones que no puedan migrarse se
  reportan y se persisten en `working_docs/active/decisiones_no_migradas.csv`.

Uso:
    env/bin/python .../build_catalog.py [--fresh-dir <dir>] \
        --review-dir .../review --inventory-out .../inventario_cobertura.csv \
        [--nonmigrable-out .../decisiones_no_migradas.csv]
"""

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from babel.messages.pofile import read_po

REPO = Path(__file__).resolve().parent.parent
BENCH = REPO.parent.parent
CONFIG_PATH = REPO / "scripts" / "extract_config.json"


def load_apps():
	"""ÚNICA fuente de la lista de apps: scripts/extract_config.json (la misma que usa el extractor).
	Añadir una app futura = editar el JSON, nunca la lógica central."""
	cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
	# Registro único: objetos {app,...} o strings (legado).
	apps = [a if isinstance(a, str) else a["app"] for a in (cfg.get("apps") or [])]
	if not apps:
		sys.exit(f"FATAL: {CONFIG_PATH} no define ninguna app (se requiere al menos una)")
	dups = sorted({a for a in apps if apps.count(a) > 1})
	if dups:
		sys.exit(f"FATAL: apps duplicadas en {CONFIG_PATH}: {dups}")
	return apps


APPS = load_apps()

BLOCKS = {
	"01_frappe_plataforma": "Plataforma y experiencia general de Frappe",
	"02_erpnext_operaciones": "ERPNext: ventas, compras, inventario, manufactura y proyectos",
	"03_erpnext_contabilidad_finanzas": "ERPNext: contabilidad, finanzas y activos",
	"04_hrms": "HRMS: RRHH y nómina",
	"05_helpdesk": "Helpdesk (SPA)",
	"06_conflictos_historico_especializada": "Conflictos, ambiguos, huérfanas y revisión especializada",
	"07_crm": "CRM (SPA)",
}
ERP_ACCT = {"accounts", "asset", "assets", "regional"}
AMBIGUOUS = {"Leave", "Return", "Posting", "Issue", "Shift", "Claim", "Entry"}
TEST_PATH_RE = re.compile(r"(^|/)(tests?|cypress|ui-tests|test_[^/]*|[^/]*\.test\.[jt]s)(/|$|:)")

# Dominios funcionales por módulo técnico (para filas SIN decisión humana; el revisor los refina).
MODULE_DOMAIN = {
	"accounts": "Contabilidad",
	"asset": "Activos",
	"assets": "Activos",
	"selling": "Ventas",
	"buying": "Compras",
	"stock": "Inventarios",
	"manufacturing": "Manufactura",
	"projects": "Proyectos",
	"crm": "CRM",
	"support": "Soporte",
	"hr": "Recursos Humanos",
	"payroll": "Nómina",
	"regional": "Fiscal/Regional",
	"setup": "Configuración",
	"core": "Plataforma",
	"desk": "Plataforma",
	"website": "Sitio Web",
	"workflow": "Flujos de trabajo",
	"automation": "Automatización",
}

PROSPECT_STATUS = {  # estados que PREVALECEN sobre la normalización cuando los fija un humano
	"ambigua",
	"conflicto de contexto",
	"requiere revisión especializada",
	"igual al inglés válida",
	"candidata para contribuir al core",
	"específica de México",
	"específica de cliente",
}
CONTROLLED_STATUS = {
	"sin traducción",
	"traducción propuesta",
	"existente correcta",
	"existente mejorable",
	"igual al inglés válida",
	"igual al inglés requiere revisión",
	"ambigua",
	"conflicto de contexto",
	"texto no extraíble",
	"requiere revisión especializada",
	"candidata para contribuir al core",
	"específica de México",
	"específica de cliente",
	"pendiente de segunda revisión",
	"po_huérfana_o_obsoleta",
}

COLUMNS = [
	"entry_key",
	"app",
	"origin_app",
	"module",
	"all_modules",
	"cross_module",
	"functional_domain",
	"source_text",
	"msgid",
	"msgid_plural",
	"msgctxt",
	"current_translation",
	"current_plural_translations",
	"proposed_translation",
	"proposed_plural_translations",
	"context",
	"field_or_action",
	"user_role",
	"source_reference",
	"all_source_references",
	"po_reference",
	"source_kind",
	"doctype_or_view",
	"extracted_comments",
	"placeholders_source",
	"placeholders_current",
	"placeholders_proposed",
	"placeholder_status",
	"flags",
	"pluralization",
	"status",
	"review_status",
	"human_authored",
	"core_candidate",
	"mexico_specific",
	"client_specific",
	"human_notes",
	"historical_reference",
	"historical_translation",
	"notes",
]
# Columnas humanas que se preservan (round-trip) entre regeneraciones.
HUMAN_FIELDS = [
	"proposed_translation",
	"proposed_plural_translations",
	"context",
	"field_or_action",
	"user_role",
	"functional_domain",
	"status",
	"review_status",
	"core_candidate",
	"mexico_specific",
	"client_specific",
	"human_notes",
	"historical_reference",
	"historical_translation",
]
LIST_SEP = " || "

# ------------------------------------------------------------------ placeholders

JINJA_VAR = re.compile(r"\{\{.*?\}\}")
JINJA_BLK = re.compile(r"\{%.*?%\}")
JS_TMPL = re.compile(r"\$\{[A-Za-z_$][\w.$]*\}")
# %-format REAL: sin espacio tras `%`, especificador inequívoco. Rechaza texto natural ("Use % for",
# "50% de") porque exige un conversor válido tras banderas/ancho/precisión OPCIONALES y sin espacios.
_PCT_TAIL = r"[-+#0]*\d*(?:\.\d+)?[sdioxXeEfFgGcr]"
PCT_NAMED = re.compile(r"%\(\w+\)" + _PCT_TAIL)
PCT_SIMPLE = re.compile(r"%" + _PCT_TAIL)
# Llave Python VÁLIDA: `{}` | `{campo(.attr|[idx])*(!conv)?(:spec)?}`. Campo = identificador o índice.
# Rechaza JSON/objetos (`{"label"}`) y texto entre llaves (`{ texto }`).
PY_BRACE = re.compile(
	r"\{\}|\{(?:[A-Za-z_]\w*|\d+)(?:\.[A-Za-z_]\w*|\[[^\[\]{}]*\])*(?:![rsa])?(?::[^{}]*)?\}"
)
CODEISH = re.compile(r"(</?\w+>|```|;\s*$|\bfunction\b|\bdef \b|\bconst \b|=>|\bimport \b)")


def _norm_brace(tok):
	if tok == "{}":
		return "{}"
	inner = tok[1:-1]
	inner = inner.split(":")[0].split("!")[0]
	return "{" + inner + "}"


def extract_placeholders(s):
	"""Counter normalizado de placeholders REALES: Jinja `{{}}`/`{%%}`, JS `${name}`, %-format
	(nombrado/simple, con conversor válido) y llaves Python VÁLIDAS `{}`/`{0}`/`{name}`/`{0:.2f}`/`{name!r}`.
	Normaliza spec/conversión: `{0:.2f}`->`{0}`, `{name!r}`->`{name}`. NO cuenta `{"json"}` ni `% texto`."""
	if not s:
		return Counter()
	toks = []
	work = s
	for rx in (JINJA_VAR, JINJA_BLK, JS_TMPL):
		for m in rx.findall(work):
			toks.append(re.sub(r"\s+", " ", m.strip()))
		work = rx.sub(" ", work)
	work = work.replace("%%", " ")
	for m in PCT_NAMED.findall(work):
		toks.append(m)
	work = PCT_NAMED.sub(" ", work)
	for m in PCT_SIMPLE.findall(work):
		toks.append(m)
	work = PCT_SIMPLE.sub(" ", work)
	for m in PY_BRACE.findall(work):
		toks.append(_norm_brace(m))
	return Counter(toks)


def ph_str(counter):
	return ";".join(sorted(counter.elements()))


def placeholder_status(src_c, cur, prop, cur_present, prop_present, codeish):
	"""Clasifica pérdida/extra de placeholders origen->actual y origen->propuesta. No corrige."""
	if not src_c and not cur and not prop:
		return ""
	parts = []
	if cur_present:
		miss = src_c - cur
		extra = cur - src_c
		if miss:
			parts.append("actual pierde: " + ";".join(sorted(miss.elements())))
		elif extra:
			parts.append("actual añade: " + ";".join(sorted(extra.elements())))
	if prop_present:
		miss = src_c - prop
		if miss:
			parts.append("propuesta pierde: " + ";".join(sorted(miss.elements())))
	if not parts:
		if not src_c:
			return "sin placeholders"
		return "ok"
	res = " | ".join(parts)
	if codeish:
		res = "[posible ejemplo de código/plantilla] " + res
	return res


# ------------------------------------------------------------------ metadatos / io


def app_meta(app):
	d = BENCH / "apps" / app
	ver = ""
	init = d / app / "__init__.py"
	if init.exists():
		m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init.read_text())
		ver = m.group(1) if m else ""

	def git(*a):
		return subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True).stdout.strip()

	return {
		"version": ver,
		"branch": git("branch", "--show-current"),
		"commit": git("rev-parse", "--short", "HEAD"),
	}


def validate_manifest(fresh_dir):
	"""Config↔manifiesto↔artefactos. Rechaza: manifiesto ausente/parcial, apps de config faltantes o
	duplicadas o inesperadas en el manifiesto, repo/artefacto ausente, SHA256 distinto, o commit que no
	es el HEAD actual. `es.po` se verifica cuando corresponde (se reporta si falta)."""
	fd = Path(fresh_dir)
	mpath = fd / "manifest.json"
	if not mpath.exists():
		sys.exit(f"FATAL: falta manifiesto {mpath} (correr extract_fresh_pot.py)")
	manifest = json.loads(mpath.read_text(encoding="utf-8"))
	if not manifest.get("overall_ok"):
		sys.exit(f"FATAL: manifiesto marca overall_ok=false: {manifest.get('apps')}")

	manifest_apps = [a["app"] for a in manifest["apps"]]
	mdups = sorted({a for a in manifest_apps if manifest_apps.count(a) > 1})
	if mdups:
		sys.exit(f"FATAL: apps duplicadas en el manifiesto: {mdups}")
	missing = sorted(set(APPS) - set(manifest_apps))
	if missing:
		sys.exit(f"FATAL: apps de config ausentes del manifiesto: {missing}")
	unexpected = sorted(set(manifest_apps) - set(APPS))
	if unexpected:
		sys.exit(f"FATAL: manifiesto con apps inesperadas (no están en config): {unexpected}")

	by_app = {a["app"]: a for a in manifest["apps"]}
	es_po_status = {}
	for app in APPS:
		a = by_app[app]  # existencia y unicidad ya garantizadas arriba
		if a.get("status") != "ok":
			sys.exit(f"FATAL: app {app} sin artefacto OK en el manifiesto")
		repo = BENCH / "apps" / app
		if not (repo / ".git").exists() and not repo.exists():
			sys.exit(f"FATAL: repo de {app} ausente en {repo}")
		path = fd / f"{app}.jsonl"
		if not path.exists():
			sys.exit(f"FATAL: falta artefacto {path}")
		sha = hashlib.sha256(path.read_bytes()).hexdigest()
		if sha != a["sha256"]:
			sys.exit(f"FATAL: SHA256 no coincide para {app} (artefacto alterado/parcial)")
		cur_commit = app_meta(app)["commit"]
		if (
			a.get("commit")
			and cur_commit
			and not a["commit"].startswith(cur_commit)
			and not cur_commit.startswith(a["commit"])
		):
			sys.exit(
				f"FATAL: artefacto de {app} es de commit {a['commit']} pero HEAD actual es {cur_commit} "
				"(artefacto viejo: re-extraer)"
			)
		es_po_status[app] = (BENCH / "apps" / app / app / "locale" / "es.po").exists()
	manifest["_es_po_status"] = es_po_status
	return manifest


def load_es(app):
	"""es.po: traducción actual, referencias del PO y flags Gettext reales."""
	p = BENCH / "apps" / app / app / "locale" / "es.po"
	d = {}
	if not p.exists():
		return d
	for m in read_po(open(p, "rb")):
		if not m.id:
			continue
		is_pl = isinstance(m.id, (tuple, list))
		mid = m.id[0] if is_pl else m.id
		plural = m.id[1] if is_pl else ""
		if isinstance(m.string, (tuple, list)):
			forms = [x or "" for x in m.string]
			cur, cpl = (forms[0] if forms else ""), forms[1:]
		else:
			cur, cpl = (m.string or ""), []
		locs = [f"{f}:{ln}" if ln else f for f, ln in (m.locations or [])]
		d.setdefault(
			(m.context or "", mid),
			{
				"current": cur,
				"current_plural": cpl,
				"plural": plural,
				"po_locs": locs,
				"flags": sorted(x for x in (m.flags or []) if x),
			},
		)
	return d


def load_fresh(app, fresh_dir):
	fp = Path(fresh_dir) / f"{app}.jsonl"
	if not fp.exists():
		return None
	d = {}
	for line in open(fp, encoding="utf-8"):
		r = json.loads(line)
		d[(r["ctx"], r["msgid"])] = {
			"plural": r.get("plural", ""),
			"locs": r.get("locs", []),
			"comments": r.get("comments", []),
		}
	return d


def build_entries(fresh, es):
	keys = {}

	def base():
		return {
			"msgid_plural": "",
			"locations": [],
			"po_locs": [],
			"comments": [],
			"flags": [],
			"in_pot": False,
			"in_po": False,
			"current": "",
			"current_plural": [],
		}

	for (ctx, mid), f in fresh.items():
		e = keys.setdefault((ctx, mid), base())
		e["in_pot"] = True
		if f["plural"]:
			e["msgid_plural"] = f["plural"]
		e["locations"] = list(f["locs"])
		e["comments"] = list(f["comments"])
	for (ctx, mid), p in es.items():
		e = keys.setdefault((ctx, mid), base())
		e["in_po"] = True
		e["current"] = p["current"]
		e["current_plural"] = p["current_plural"]
		e["po_locs"] = p["po_locs"]
		e["flags"] = p["flags"]
		if p["plural"] and not e["msgid_plural"]:
			e["msgid_plural"] = p["plural"]
		if not e["locations"]:
			e["locations"] = p["po_locs"]
	return keys


def entry_key(app, ctx, msgid, plural):
	canonical = json.dumps(
		{"app": app, "msgctxt": ctx, "msgid": msgid, "msgid_plural": plural},
		ensure_ascii=False,
		sort_keys=True,
	)
	return f"{app}:" + hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------ capa humana


def load_human_from_csv(review_dir):
	"""Fuente autoritativa: filas con human_authored=sí de los CSV existentes.
	Índices por entry_key y por identidad completa (respaldo)."""
	by_ekey, by_identity = {}, {}
	for b in BLOCKS:
		p = Path(review_dir) / f"{b}.csv"
		if not p.exists():
			continue
		with open(p, encoding="utf-8", newline="") as fh:
			for row in csv.DictReader(fh):
				if row.get("human_authored") != "sí":
					continue
				rec = {k: row.get(k, "") for k in HUMAN_FIELDS}
				by_ekey[row["entry_key"]] = rec
				ident = (row["app"], row.get("msgctxt", ""), row["msgid"], row.get("msgid_plural", ""))
				by_identity[ident] = rec
	return by_ekey, by_identity


def load_legacy_seed():
	"""Bootstrap único desde human_decisions.py (legacy). Identidad EXACTA (app,'',src,'') → sin
	propagación por msgid. Devuelve índices y la lista cruda para el reporte de no-migrables."""
	sys.path.insert(0, str(REPO / "scripts"))
	try:
		from human_decisions import AUTHORED
	except Exception:
		return {}, {}, []
	by_ekey, by_identity, raw = {}, {}, []
	for app, items in AUTHORED.items():
		for src, proposed, status, field_action, role, domain, note in items:
			core = "sí" if "core" in note.lower() else ""
			mx = "sí" if ("méxico" in note.lower() or " mx" in note.lower()) else ""
			rec = {
				"proposed_translation": proposed,
				"proposed_plural_translations": "",
				"context": note or domain,
				"field_or_action": field_action,
				"user_role": role,
				"functional_domain": domain,
				"status": status,
				"review_status": "revisado (muestra etapa 2)",
				"core_candidate": core,
				"mexico_specific": mx,
				"client_specific": "",
				"human_notes": note,
			}
			ek = entry_key(app, "", src, "")
			by_ekey[ek] = rec
			by_identity[(app, "", src, "")] = rec
			raw.append({"app": app, "src": src, "ekey": ek, **rec})
	return by_ekey, by_identity, raw


# ------------------------------------------------------------------ derivación técnica


def modules_from_locs(locations):
	"""Todos los módulos técnicos reales (parts[1]), ignorando rutas de test/cypress para el primario."""
	real, all_mods = [], []
	for loc in locations:
		path = loc.split(":")[0]
		parts = path.split("/")
		if len(parts) < 2:
			continue
		mod = parts[1].lower()
		all_mods.append(mod)
		if not TEST_PATH_RE.search(path):
			real.append(mod)
	pool = real or all_mods
	if not pool:
		return "", []
	freq = Counter(pool)
	primary = sorted(freq, key=lambda m: (-freq[m], m))[0]
	return primary, sorted(set(all_mods))


def parse_comments(comments):
	"""Extrae DocType, tipo de elemento y contexto técnico de los comentarios oficiales del extractor."""
	doctype, field_action, ctx = "", "", ""
	for c in comments:
		mdt = re.search(r"in DocType '([^']+)'", c)
		if mdt and not doctype:
			doctype = mdt.group(1)
		mws = re.search(r"in the ([^']+?) Workspace", c)
		if mws and not doctype:
			doctype = mws.group(1) + " (Workspace)"
		mwf = re.search(r"in the ([^']+?) Web Form", c)
		if mwf and not doctype:
			doctype = mwf.group(1) + " (Web Form)"
		low = c.lower()
		if not field_action:
			if low.startswith("label of"):
				field_action = "etiqueta de campo/elemento"
			elif low.startswith("description of"):
				field_action = "descripción"
			elif low.startswith("content of"):
				field_action = "contenido de campo"
			elif low.startswith("name of a doctype"):
				field_action, doctype = "nombre de DocType", doctype or "(este)"
			elif low.startswith("name of a role"):
				field_action = "nombre de rol"
			elif low.startswith("name of a report"):
				field_action = "nombre de reporte"
			elif "workspace" in low:
				field_action = "elemento de workspace"
			elif "onboarding" in low:
				field_action = "paso de onboarding"
			elif low.startswith("option for") or "option" in low:
				field_action = "opción de campo select"
		if not ctx:
			ctx = c
	return doctype, field_action, ctx


def derive_source_kind(locations):
	if not locations:
		return "code", ""
	path = locations[0].split(":")[0]
	parts = path.split("/")
	dv = ""
	kind = "code"
	if "/doctype/" in path:
		try:
			dv = parts[parts.index("doctype") + 1].replace("_", " ").title()
		except Exception:
			dv = ""
		kind = "doctype-json" if path.endswith(".json") else "doctype-controller"
	elif "/report/" in path:
		kind = "report"
	elif "/workspace/" in path or "workspace" in path:
		kind = "workspace"
	elif "/page/" in path:
		kind = "page"
	elif path.endswith((".js", ".vue", ".ts", ".tsx")):
		kind = "client-js"
	elif path.endswith(".py"):
		kind = "python"
	elif path.endswith(".html"):
		kind = "jinja-html"
	return kind, dv


def assign_block(app, module, status):
	if status in {
		"conflicto de contexto",
		"ambigua",
		"requiere revisión especializada",
		"texto no extraíble",
		"po_huérfana_o_obsoleta",
	}:
		return "06_conflictos_historico_especializada"
	if app == "frappe":
		return "01_frappe_plataforma"
	if app == "erpnext":
		return "03_erpnext_contabilidad_finanzas" if module in ERP_ACCT else "02_erpnext_operaciones"
	if app == "hrms":
		return "04_hrms"
	if app == "crm":
		return "07_crm"
	return "05_helpdesk"


def is_code_like(s):
	s = s.strip()
	if not s:
		return False
	if re.fullmatch(r"[^a-zñáéíóú]+", s):
		return True
	return len(s) <= 4 and s.isupper()


def normalize_status(cur, prop, human):
	"""Estado coherente con current/proposed. Los estados PREVALECIENTES humanos se respetan."""
	if human and human.get("status") in PROSPECT_STATUS:
		return human["status"]
	cur, prop = (cur or "").strip(), (prop or "").strip()
	if cur and (not prop or prop == cur):
		return "existente correcta"
	if cur and prop and prop != cur:
		return "existente mejorable"
	if not cur and prop:
		return "traducción propuesta"
	return "sin traducción"


def classify(e, msgid, human, is_ambiguous):
	if e["in_po"] and not e["in_pot"]:
		# PO-only: por defecto huérfana, pero una auditoría humana puede marcarla como texto no
		# extraíble (visible en el código pero no capturada por el extractor oficial, con evidencia).
		if human and human.get("status") in {"po_huérfana_o_obsoleta", "texto no extraíble"}:
			return human["status"]
		return "po_huérfana_o_obsoleta"
	if human:
		return normalize_status(e["current"], human.get("proposed_translation", ""), human)
	if is_ambiguous:
		return "ambigua"
	cur = (e["current"] or "").strip()
	if not cur:
		return "sin traducción"
	if cur == msgid.strip():
		return "igual al inglés válida" if is_code_like(msgid) else "igual al inglés requiere revisión"
	return "pendiente de segunda revisión"


# ------------------------------------------------------------------ main


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--fresh-dir", default=str(REPO / ".artifacts" / "freshpot"))
	ap.add_argument("--review-dir", required=True)
	ap.add_argument("--inventory-out", required=True)
	ap.add_argument(
		"--nonmigrable-out", default=str(REPO / "working_docs" / "active" / "decisiones_no_migradas.csv")
	)
	args = ap.parse_args()

	manifest = validate_manifest(args.fresh_dir)

	# Capa humana: autoritativa desde CSV; si no hay, bootstrap único desde legacy.
	hum_ekey, hum_ident = load_human_from_csv(args.review_dir)
	seed_source = "csv"
	legacy_raw = []
	if not hum_ekey:
		hum_ekey, hum_ident, legacy_raw = load_legacy_seed()
		seed_source = "legacy(human_decisions.py)"

	def human_for(app, ctx, msgid, plural, ekey):
		return hum_ekey.get(ekey) or hum_ident.get((app, ctx, msgid, plural))

	rows_by_block = {b: [] for b in BLOCKS}
	inv, ekeys = [], Counter()
	matched_ekeys = set()
	proposal_ph_loss = []
	for app in APPS:
		fresh = load_fresh(app, args.fresh_dir)
		es = load_es(app)
		keys = build_entries(fresh, es)
		st = Counter()
		app_blocks = set()
		for (ctx, msgid), e in keys.items():
			cur = (e["current"] or "").strip()
			in_pot, in_po = e["in_pot"], e["in_po"]
			if in_pot:
				st["pot"] += 1
			if in_po:
				st["po"] += 1
				st["trad" if cur else "untr_po"] += 1
			if in_pot and in_po and cur:
				st["trad_pot"] += 1
			if in_pot and (not in_po or not cur):
				st["untr_pot"] += 1
			if in_pot and not in_po:
				st["missing_po"] += 1
			if in_po and not in_pot:
				st["po_only"] += 1
				if cur:
					st["trad_po_only"] += 1
			if in_pot and in_po and cur and cur == msgid.strip():
				st["eq_pot"] += 1
			if ctx:
				st["ctx"] += 1
			if e["msgid_plural"]:
				st["plural"] += 1

			ek = entry_key(app, ctx, msgid, e["msgid_plural"])
			ekeys[ek] += 1
			human = human_for(app, ctx, msgid, e["msgid_plural"], ek)
			if human:
				matched_ekeys.add(ek)
			is_amb = (msgid.strip() in AMBIGUOUS) and not human
			status = classify(e, msgid, human, is_amb)
			if human and human.get("status") in PROSPECT_STATUS:
				status = human["status"]
			if status not in CONTROLLED_STATUS:
				status = "pendiente de segunda revisión"

			# placeholders
			proposed = human.get("proposed_translation", "") if human else ""
			src_c = extract_placeholders(msgid)
			cur_c = extract_placeholders(e["current"])
			prop_c = extract_placeholders(proposed)
			codeish = bool(CODEISH.search(msgid))
			ph_stat = placeholder_status(src_c, cur_c, prop_c, bool(cur), bool(proposed), codeish)
			if src_c:
				st["ph"] += 1
			if "actual pierde" in ph_stat:
				st["ph_issue"] += 1
			miss_prop = src_c - prop_c
			if proposed and miss_prop:
				proposal_ph_loss.append((app, msgid, ";".join(sorted(miss_prop.elements()))))

			primary_mod, all_mods = modules_from_locs(e["locations"])
			dt_c, fa_c, ctx_c = parse_comments(e["comments"])
			kind, dv = derive_source_kind(e["locations"])
			doctype_or_view = dv or dt_c
			functional_domain = (
				human["functional_domain"]
				if human and human.get("functional_domain")
				else MODULE_DOMAIN.get(primary_mod, primary_mod.title())
			)
			context = human["context"] if human and human.get("context") else ctx_c
			field_or_action = human["field_or_action"] if human and human.get("field_or_action") else fa_c
			po_reference = LIST_SEP.join(e["po_locs"])

			block = assign_block(app, primary_mod, status)
			app_blocks.add(block)
			if status in {"conflicto de contexto", "ambigua"}:
				st["conflict"] += 1
			if status == "requiere revisión especializada":
				st["special"] += 1

			note = human.get("human_notes", "") if human else ""
			auto = []
			if in_po and not in_pot:
				auto.append(
					"PO-only: en es.po, ausente del POT fresco -> huérfana/obsoleta; NO usar sin validación"
				)
			if in_pot and not in_po:
				auto.append("POT-only: en el universo fresco, sin traducir")
			rows_by_block[block].append(
				{
					"entry_key": ek,
					"app": app,
					"origin_app": app,
					"module": primary_mod,
					"all_modules": ";".join(all_mods),
					"cross_module": "sí" if len(all_mods) > 1 else "",
					"functional_domain": functional_domain,
					"source_text": msgid,
					"msgid": msgid,
					"msgid_plural": e["msgid_plural"],
					"msgctxt": ctx,
					"current_translation": e["current"],
					"current_plural_translations": LIST_SEP.join(e["current_plural"]),
					"proposed_translation": proposed,
					"proposed_plural_translations": (
						human.get("proposed_plural_translations", "") if human else ""
					),
					"context": context,
					"field_or_action": field_or_action,
					"user_role": (human.get("user_role", "") if human else ""),
					"source_reference": (e["locations"][0] if e["locations"] else ""),
					"all_source_references": LIST_SEP.join(e["locations"]),
					"po_reference": po_reference,
					"source_kind": kind,
					"doctype_or_view": doctype_or_view,
					"extracted_comments": json.dumps(e["comments"], ensure_ascii=False),
					"placeholders_source": ph_str(src_c),
					"placeholders_current": ph_str(cur_c),
					"placeholders_proposed": ph_str(prop_c),
					"placeholder_status": ph_stat,
					"flags": ",".join(e["flags"]),
					"pluralization": "plural" if e["msgid_plural"] else "",
					"status": status,
					"review_status": (
						human.get("review_status", "revisado (muestra etapa 2)")
						if human
						else "pendiente de segunda revisión"
					),
					"human_authored": "sí" if human else "",
					"core_candidate": (human.get("core_candidate", "") if human else ""),
					"mexico_specific": (human.get("mexico_specific", "") if human else ""),
					"client_specific": (human.get("client_specific", "") if human else ""),
					"human_notes": note,
					"historical_reference": (human.get("historical_reference", "") if human else ""),
					"historical_translation": (human.get("historical_translation", "") if human else ""),
					"notes": " | ".join(auto),
				}
			)

		meta = app_meta(app)
		universe = st["pot"] + st["po_only"]
		trad_in_po = st["trad"]
		inv.append(
			{
				"app": app,
				"version": meta["version"],
				"branch": meta["branch"],
				"commit": meta["commit"],
				"pot_entries": st["pot"],
				"po_entries": st["po"],
				"translated_in_pot": st["trad_pot"],
				"untranslated_in_pot": st["untr_pot"],
				"untranslated_in_po": st["untr_po"],
				"missing_from_po": st["missing_po"],
				"po_only_orphan": st["po_only"],
				"translated_po_only": st["trad_po_only"],
				"equal_to_source_in_pot": st["eq_pot"],
				"context_entries": st["ctx"],
				"plural_entries": st["plural"],
				"placeholder_source_entries": st["ph"],
				"current_placeholder_issues": st["ph_issue"],
				"conflict_entries": st["conflict"],
				"specialized_review_entries": st["special"],
				"coverage_pot_percent": round(100 * st["trad_pot"] / st["pot"], 1) if st["pot"] else 0,
				"coverage_po_percent": round(100 * trad_in_po / st["po"], 1) if st["po"] else 0,
				"universe": universe,
				"review_csv": ";".join(sorted(app_blocks)),
			}
		)

	# ---- validaciones de integridad (fail-fast, ANTES de escribir) ----
	total = sum(len(v) for v in rows_by_block.values())
	collisions = {k: c for k, c in ekeys.items() if c > 1}
	uni_sum = sum(r["universe"] for r in inv)
	all_statuses = {row["status"] for v in rows_by_block.values() for row in v}
	bad_status = all_statuses - CONTROLLED_STATUS
	errs = []
	if collisions:
		errs.append(f"colisiones entry_key: {list(collisions)[:5]} ...")
	if total != len(ekeys):
		errs.append(f"filas ({total}) != entry_key únicos ({len(ekeys)})")
	if total != uni_sum:
		errs.append(f"reconciliación: filas ({total}) != Σuniverso ({uni_sum})")
	if bad_status:
		errs.append(f"estados inválidos: {bad_status}")
	if proposal_ph_loss:
		errs.append(f"propuestas humanas que pierden placeholders: {proposal_ph_loss[:5]}")
	if errs:
		sys.exit("FATAL validaciones:\n  - " + "\n  - ".join(errs))

	# ---- escritura atómica: temp -> replace ----
	review = Path(args.review_dir)
	review.mkdir(parents=True, exist_ok=True)
	tmp = review / ".tmp_build"
	tmp.mkdir(exist_ok=True)
	for b in BLOCKS:
		rows = sorted(rows_by_block[b], key=lambda r: (r["app"], r["msgctxt"], r["msgid"]))
		with open(tmp / f"{b}.csv", "w", encoding="utf-8", newline="") as fh:
			w = csv.DictWriter(fh, fieldnames=COLUMNS)
			w.writeheader()
			w.writerows(rows)
	for b in BLOCKS:
		os.replace(tmp / f"{b}.csv", review / f"{b}.csv")
	tmp.rmdir()

	# ---- inventario + fila TOTAL ----
	inv_cols = [
		"app",
		"version",
		"branch",
		"commit",
		"pot_entries",
		"po_entries",
		"translated_in_pot",
		"untranslated_in_pot",
		"untranslated_in_po",
		"missing_from_po",
		"po_only_orphan",
		"translated_po_only",
		"equal_to_source_in_pot",
		"context_entries",
		"plural_entries",
		"placeholder_source_entries",
		"current_placeholder_issues",
		"conflict_entries",
		"specialized_review_entries",
		"coverage_pot_percent",
		"coverage_po_percent",
		"universe",
		"review_csv",
	]
	sum_cols = [
		c
		for c in inv_cols
		if c
		not in {
			"app",
			"version",
			"branch",
			"commit",
			"coverage_pot_percent",
			"coverage_po_percent",
			"review_csv",
		}
	]
	total_row = {"app": "TOTAL", "version": "", "branch": "", "commit": "", "review_csv": ""}
	for c in sum_cols:
		total_row[c] = sum(r[c] for r in inv)
	tot_pot = total_row["pot_entries"]
	tot_po = total_row["po_entries"]
	total_row["coverage_pot_percent"] = (
		round(100 * total_row["translated_in_pot"] / tot_pot, 1) if tot_pot else 0
	)
	total_row["coverage_po_percent"] = (
		round(100 * (sum(r["translated_in_pot"] + r["translated_po_only"] for r in inv)) / tot_po, 1)
		if tot_po
		else 0
	)
	with open(args.inventory_out, "w", encoding="utf-8", newline="") as fh:
		w = csv.DictWriter(fh, fieldnames=inv_cols)
		w.writeheader()
		w.writerows(inv)
		w.writerow(total_row)

	# ---- reporte de decisiones NO migrables (solo en bootstrap legacy) ----
	nonmig = []
	if legacy_raw:
		# Índice global src -> {app: set(ctx)} para diagnosticar por qué no migra (contexto / otra app).
		src_index = {}
		for app in APPS:
			fr = load_fresh(app, args.fresh_dir) or {}
			for ctx, mid in list(fr) + list(load_es(app)):
				src_index.setdefault(mid, {}).setdefault(app, set()).add(ctx)
		for d in legacy_raw:
			if d["ekey"] in matched_ekeys:
				continue
			apps_with = src_index.get(d["src"], {})
			same = apps_with.get(d["app"], set())
			others = sorted(a for a in apps_with if a != d["app"])
			if others:
				# El string existe pero en OTRA app → NO se migra automáticamente; queda pendiente de
				# validar su contexto en la app donde realmente vive.
				classification = "cross_app_pendiente_validacion"
				reason = (
					f"no existe en {d['app']}; el string vive en: {';'.join(others)} "
					"(decisión filada en la app equivocada; pendiente de validar contexto, NO migrada)"
				)
			elif any(c for c in same):
				classification = "cross_app_pendiente_validacion"
				reason = f"existe en {d['app']} solo con contexto: " + ";".join(sorted(c for c in same if c))
			else:
				classification = "no_existe_msgid_exacto"
				reason = "no existe como msgid exacto en ninguna app del universo fresco"
			nonmig.append(
				{
					"app": d["app"],
					"source_text": d["src"],
					"proposed": d["proposed_translation"],
					"classification": classification,
					"reason": reason,
				}
			)
		Path(args.nonmigrable_out).parent.mkdir(parents=True, exist_ok=True)
		with open(args.nonmigrable_out, "w", encoding="utf-8", newline="") as fh:
			w = csv.DictWriter(fh, fieldnames=["app", "source_text", "proposed", "classification", "reason"])
			w.writeheader()
			w.writerows(nonmig)

	# ---- resumen ----
	human_rows = sum(1 for v in rows_by_block.values() for row in v if row["human_authored"] == "sí")
	tech_ctx = sum(
		1
		for v in rows_by_block.values()
		for row in v
		if row["extracted_comments"] not in ("", "[]")
		or row["human_authored"] == "sí"
		or row["doctype_or_view"]
	)
	ph_issues = sum(
		1 for v in rows_by_block.values() for row in v if "actual pierde" in row["placeholder_status"]
	)
	print(f"OK seed_source={seed_source} manifest_ok={manifest['overall_ok']}")
	print(f"apps (desde config): {APPS}")
	print(f"es.po presente por app: {manifest.get('_es_po_status')}")
	print(f"filas por bloque: { {b: len(rows_by_block[b]) for b in BLOCKS} }")
	print(
		f"total filas: {total} | entry_key únicos: {len(ekeys)} | Σuniverso: {uni_sum} | colisiones: {len(collisions)}"
	)
	print(f"humanas en catálogo: {human_rows} | no migrables (legacy): {len(nonmig)}")
	print(f"contexto técnico utilizable: {tech_ctx}/{total} = {round(100 * tech_ctx / total, 1)}%")
	print(
		f"placeholder: origen={sum(r['placeholder_source_entries'] for r in inv)} | actual pierde={ph_issues} | propuestas que pierden={len(proposal_ph_loss)}"
	)
	for r in inv:
		print(
			f"  {r['app']:9} pot={r['pot_entries']:6} po={r['po_entries']:6} trad_pot={r['translated_in_pot']:6} "
			f"cov_pot={r['coverage_pot_percent']:5}% POTonly={r['missing_from_po']:5} POonly={r['po_only_orphan']:4} "
			f"trad_po_only={r['translated_po_only']:4}"
		)
	if nonmig:
		by_class = Counter(d["classification"] for d in nonmig)
		print(f"NO MIGRABLES por clasificación: {dict(by_class)}")
		for d in nonmig:
			print(
				f"  [{d['classification']:30}] {d['app']:9} {d['source_text'][:38]:38} -> {d['reason'][:60]}"
			)


if __name__ == "__main__":
	main()
