#!/usr/bin/env python3
"""
Subset con correo válido → limpios_alto_rango_con_correo/.

No modifica limpios_alto_rango/ (queda para outreach LinkedIn u otros canales).

Uso (desde la raíz del repo):
    python src/email_ready.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "limpios_alto_rango"
OUT_DIR = ROOT / "limpios_alto_rango_con_correo"
REPORT = OUT_DIR / "_reporte_con_correo.csv"

COLUMNAS = [
    "Departamento_Filtro",
    "Entidad_Filtro",
    "Nombre",
    "Rol_Contrato",
    "Cargo_Detallado",
    "Fecha_Fin_Cargo",
    "Correo_Perfil",
    "Telefono_Perfil",
    "Entidad_Asignada",
]

_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_INVALIDOS = {
    "",
    "NO REPORTADO",
    "NO REPORTADA",
    "NO ESPECIFICADO",
    "NO ESPECIFICADA",
    "N/A",
    "NA",
    "-",
    ".",
    "SIN CORREO",
    "NONE",
    "NULL",
}


def correo_valido(raw: str) -> bool:
    correo = (raw or "").strip()
    if correo.upper() in _INVALIDOS:
        return False
    correo = correo.replace(" ", "")
    if "@" not in correo:
        return False
    return bool(_RE_EMAIL.match(correo))


def main() -> None:
    if not SRC_DIR.is_dir():
        raise SystemExit(f"No existe la carpeta fuente: {SRC_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    archivos = sorted(SRC_DIR.glob("sigep_*.csv"))
    if not archivos:
        raise SystemExit(f"No hay CSV en {SRC_DIR}")

    print(f"Fuente:  {SRC_DIR}")
    print(f"Salida:  {OUT_DIR}")
    print("-" * 60)

    reportes: list[dict[str, object]] = []
    gran_total = gran_kept = 0

    for src in archivos:
        total = kept = 0
        rows: list[dict[str, str]] = []

        with src.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                total += 1
                correo = (row.get("Correo_Perfil") or "").strip()
                if not correo_valido(correo):
                    continue
                out = {c: (row.get(c) or "") for c in COLUMNAS}
                out["Correo_Perfil"] = correo.replace(" ", "")
                rows.append(out)
                kept += 1

        dest = OUT_DIR / src.name
        with dest.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNAS)
            writer.writeheader()
            writer.writerows(rows)

        pct = round(100.0 * kept / total, 2) if total else 0.0
        reportes.append(
            {
                "archivo": src.name,
                "total_fuente": total,
                "con_correo": kept,
                "sin_correo": total - kept,
                "pct_con_correo": pct,
            }
        )
        gran_total += total
        gran_kept += kept
        print(f"{src.name:<55} {kept:>6}/{total:<6} ({pct}%)")

    with REPORT.open("w", newline="", encoding="utf-8") as f:
        fields = ["archivo", "total_fuente", "con_correo", "sin_correo", "pct_con_correo"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(reportes)
        writer.writerow(
            {
                "archivo": "_TOTAL",
                "total_fuente": gran_total,
                "con_correo": gran_kept,
                "sin_correo": gran_total - gran_kept,
                "pct_con_correo": round(100.0 * gran_kept / gran_total, 2) if gran_total else 0.0,
            }
        )

    pct = round(100.0 * gran_kept / gran_total, 2) if gran_total else 0.0
    print("-" * 60)
    print(f"TOTAL: {gran_kept:,} / {gran_total:,} con correo ({pct}%)")
    print("Listo.")


if __name__ == "__main__":
    main()
