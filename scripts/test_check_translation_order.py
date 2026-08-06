#!/usr/bin/env python3
"""Pruebas unitarias de la lógica pura de check_translation_order (sin tocar sitios reales)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_translation_order import check_order


def test_al_final_ok():
	ok, _ = check_order(["frappe", "erpnext", "hrms", "buzola_translations"])
	assert ok is True


def test_no_instalada():
	ok, motivo = check_order(["frappe", "erpnext"])
	assert ok is False and "NO está instalada" in motivo


def test_no_al_final():
	ok, motivo = check_order(["frappe", "buzola_translations", "erpnext"])
	assert ok is False and "NO está al final" in motivo and "erpnext" in motivo


def test_app_param():
	ok, _ = check_order(["frappe", "x"], app="x")
	assert ok is True


if __name__ == "__main__":
	fns = [test_al_final_ok, test_no_instalada, test_no_al_final, test_app_param]
	for f in fns:
		f()
		print("PASS", f.__name__)
	print("TODAS OK")
