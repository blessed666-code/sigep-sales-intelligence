#!/usr/bin/env python3
"""
Fase B — Convierte 01_contactos_normalizados.csv al formato de importación
de BillionMail (columnas exactas: email, attributes).

Formato de attributes (JSON escapado por el writer CSV):
    "{""department"": ""..."", ""name"": ""..."", ""position"": ""..."", ""assigned_entity"": ""...""}"

Salida:
    billionmail/02_billionmail_import.csv

Uso (desde la raíz del repo):
    python src/billionmail_export.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from text_format import ENCODING  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "billionmail" / "01_contactos_normalizados.csv"
OUT_CSV = ROOT / "billionmail" / "02_billionmail_import.csv"
REPORT = ROOT / "billionmail" / "_reporte_billionmail.csv"

# Claves EXACTAS requeridas por BillionMail / plantillas.
ATTR_KEYS = ("department", "name", "position", "assigned_entity")
HEADERS = ("email", "attributes")


def build_attributes(row: dict[str, str]) -> str:
    payload = {
        "department": row["Departamento"],
        "name": row["Nombre"],
        "position": row["Cargo"],
        "assigned_entity": row["Entidad_Asignada"],
    }
    # ensure_ascii=False → acentos UTF-8 reales (no \\u00xx)
    return json.dumps(payload, ensure_ascii=False, separators=(", ", ": "))


def main() -> None:
    if not IN_CSV.is_file():
        raise SystemExit(
            f"No existe {IN_CSV}. Ejecuta primero: python src/normalize_contacts.py"
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with IN_CSV.open(encoding=ENCODING, newline="") as fin, OUT_CSV.open(
        "w", encoding=ENCODING, newline=""
    ) as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(HEADERS)

        for row in reader:
            email = (row.get("Correo") or "").strip().lower()
            if not email or "@" not in email:
                continue
            attrs = build_attributes(row)
            # csv.writer duplica comillas internas → formato BillionMail
            writer.writerow([email, attrs])
            written += 1

    size_mb = OUT_CSV.stat().st_size / (1024 * 1024)

    with REPORT.open("w", encoding=ENCODING, newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["filas", "columnas", "tamano_mb", "archivo"],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerow(
            {
                "filas": written,
                "columnas": "email,attributes",
                "tamano_mb": f"{size_mb:.3f}",
                "archivo": str(OUT_CSV.relative_to(ROOT)),
            }
        )

    # QA de formato: leer primera data row cruda
    with OUT_CSV.open(encoding=ENCODING, newline="") as fh:
        lines = fh.read().splitlines()
    header = lines[0] if lines else ""
    sample = lines[1] if len(lines) > 1 else ""

    print(f"Entrada:  {IN_CSV}")
    print(f"Salida:   {OUT_CSV}")
    print(f"Filas:    {written:,}")
    print(f"Tamaño:   {size_mb:.3f} MB (límite BillionMail: 10 MB)")
    print("-" * 60)
    print(f"Header:   {header!r}")
    print(f"Sample:   {sample[:180]}{'…' if len(sample) > 180 else ''}")

    if header != "email,attributes":
        raise SystemExit("ERROR: header debe ser exactamente email,attributes")
    if size_mb >= 10:
        raise SystemExit("ERROR: archivo >= 10 MB")


if __name__ == "__main__":
    main()
