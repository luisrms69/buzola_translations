#!/usr/bin/env python3
"""Prueba del clasificador de delta (`diff_upstream.classify`) — determinista, sin red ni BD.

El dry-run real de Helpdesk sólo pudo ejercitar `sin_cambios` + `eliminada` (el upstream no se movió).
Este test alimenta mutaciones sintéticas para verificar que CADA clase se dispara: nueva, eliminada,
cambio_contexto, cambio_plural, cambio_placeholders y posible_rename. Ejecuta:
    env/bin/python scripts/test_diff_upstream.py     (o: pytest scripts/test_diff_upstream.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diff_upstream import classify


def _fresh(ctx, msgid, plural=""):
	return {"ctx": ctx, "msgid": msgid, "plural": plural, "locs": []}


def _csv(ctx, msgid, plural="", status="existente correcta"):
	return {
		"ctx": ctx,
		"msgid": msgid,
		"plural": plural,
		"status": status,
		"human": True,
		"has_translation": True,
		"block": "05_helpdesk_crm",
	}


def run_case():
	added = {
		"A_new": _fresh("", "Escalate ticket"),  # nueva
		"A_ctx": _fresh("button", "Close"),  # cambio_contexto (ctx nuevo)
		"A_plu": _fresh("", "Ticket", "Tickets"),  # cambio_plural (gana plural)
		"A_ph": _fresh("", "Assigned to {user}"),  # cambio_placeholders ({0}->{user})
		"A_ren": _fresh("", "Resolve this ticket now"),  # posible_rename (alta similitud)
	}
	removed = {
		"R_ctx": _csv("", "Close"),  # par de A_ctx (ctx viejo distinto)
		"R_plu": _csv("", "Ticket", ""),  # par de A_plu (sin plural)
		"R_ph": _csv("", "Assigned to {0}"),  # par de A_ph
		"R_ren": _csv("", "Resolve the ticket now"),  # par de A_ren
		"R_del": _csv("", "Obsolete legacy string"),  # eliminada (sin par)
	}
	by_class = {}
	for c in classify(added, removed, similarity=0.85):
		by_class.setdefault(c["class"], []).append(c)

	expected = {
		"nueva",
		"eliminada",
		"cambio_contexto",
		"cambio_plural",
		"cambio_placeholders",
		"posible_rename",
	}
	got = set(by_class)
	assert expected <= got, f"faltan clases: {expected - got} (obtenidas: {got})"
	assert len(by_class["nueva"]) == 1 and by_class["nueva"][0]["ek_new"] == "A_new"
	assert len(by_class["eliminada"]) == 1 and by_class["eliminada"][0]["ek_old"] == "R_del"
	assert by_class["cambio_contexto"][0]["ek_new"] == "A_ctx"
	assert by_class["cambio_plural"][0]["ek_new"] == "A_plu"
	ph = by_class["cambio_placeholders"][0]
	assert ph["ph_old"] == "{0}" and ph["ph_new"] == "{user}", ph
	ren = by_class["posible_rename"][0]
	assert ren["ek_new"] == "A_ren" and ren["similarity"] >= 0.85, ren
	# cada added y cada removed queda clasificado exactamente una vez (sin pérdidas ni dobles)
	total = sum(len(v) for v in by_class.values())
	assert total == len(added) + len(removed) - 4, total  # 4 pares consumen (1 added + 1 removed) c/u
	return by_class


def test_all_delta_classes_fire():
	run_case()


if __name__ == "__main__":
	bc = run_case()
	for k in sorted(bc):
		print(f"OK {k}: {len(bc[k])}")
	print("PASS test_diff_upstream")
