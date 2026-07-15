#!/usr/bin/env python3
"""Tests unitarios del clasificador y del filtro de correo."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from classify import es_cargo_alto_rango  # noqa: E402
from clean import es_cargo_activo  # noqa: E402
from email_ready import correo_valido  # noqa: E402
from text_format import formatear_cargo, formatear_correo, formatear_nombre  # noqa: E402


class TestClassify(unittest.TestCase):
    def test_incluye_secretario_despacho(self) -> None:
        self.assertTrue(es_cargo_alto_rango("SECRETARIO DE DESPACHO"))

    def test_incluye_alcalde(self) -> None:
        self.assertTrue(es_cargo_alto_rango("ALCALDE"))

    def test_excluye_profesional_universitario(self) -> None:
        self.assertFalse(es_cargo_alto_rango("PROFESIONAL UNIVERSITARIO"))

    def test_excluye_contador(self) -> None:
        self.assertFalse(es_cargo_alto_rango("CONTADOR PUBLICO"))

    def test_excluye_abogado(self) -> None:
        self.assertFalse(es_cargo_alto_rango("ABOGADO LITIGANTE - ASESOR"))

    def test_excluye_auxiliar(self) -> None:
        self.assertFalse(es_cargo_alto_rango("AUXILIAR ADMINISTRATIVO"))


class TestActivo(unittest.TestCase):
    def test_actual(self) -> None:
        self.assertTrue(es_cargo_activo("Actual", hoy=date(2026, 7, 14)))

    def test_fecha_futura(self) -> None:
        self.assertTrue(es_cargo_activo("31/12/2026", hoy=date(2026, 7, 14)))

    def test_fecha_pasada(self) -> None:
        self.assertFalse(es_cargo_activo("31/12/2024", hoy=date(2026, 7, 14)))

    def test_no_especificada(self) -> None:
        self.assertFalse(es_cargo_activo("No especificada", hoy=date(2026, 7, 14)))


class TestEmail(unittest.TestCase):
    def test_correo_ok(self) -> None:
        self.assertTrue(correo_valido("jefe@ejemplo.gov.co"))

    def test_no_reportado(self) -> None:
        self.assertFalse(correo_valido("No reportado"))

    def test_vacio(self) -> None:
        self.assertFalse(correo_valido(""))


class TestTextFormat(unittest.TestCase):
    def test_nombre_title_case(self) -> None:
        self.assertEqual(
            formatear_nombre("CONSUELO GOMEZ ARBELAEZ"),
            "Consuelo Gómez Arbeláez",
        )

    def test_correo_minusculas(self) -> None:
        self.assertEqual(
            formatear_correo("Jefe@Ejemplo.GOV.CO"),
            "jefe@ejemplo.gov.co",
        )

    def test_cargo_abreviado_sin_adivinar(self) -> None:
        self.assertEqual(
            formatear_cargo("GERENTE OPERAC, FINANCIERAS"),
            "Gerente Operac., Financieras",
        )

    def test_cargo_quita_guion_final(self) -> None:
        self.assertEqual(formatear_cargo("ASESOR-"), "Asesor")


if __name__ == "__main__":
    unittest.main()
