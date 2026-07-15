#!/usr/bin/env python3
"""
Fase A — Unifica limpios_alto_rango_con_correo/ en un CSV tipográficamente
correcto para plantillas (BillionMail / outreach).

Salida:
    billionmail/01_contactos_normalizados.csv
    billionmail/_reporte_normalizacion.csv

No modifica limpios_alto_rango/ ni limpios_alto_rango_con_correo/.

Uso (desde la raíz del repo):
    python src/normalize_contacts.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from text_format import (  # noqa: E402
    ENCODING,
    formatear_cargo,
    formatear_correo,
    formatear_departamento,
    formatear_entidad,
    formatear_nombre,
)

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "limpios_alto_rango_con_correo"
OUT_DIR = ROOT / "billionmail"
OUT_CSV = OUT_DIR / "01_contactos_normalizados.csv"
REPORT = OUT_DIR / "_reporte_normalizacion.csv"
DUPES = OUT_DIR / "_emails_duplicados_omitidos.csv"

COLUMNAS_OUT = [
    "Departamento",
    "Nombre",
    "Cargo",
    "Correo",
    "Entidad_Asignada",
]


def main() -> None:
    if not SRC_DIR.is_dir():
        raise SystemExit(f"No existe la carpeta fuente: {SRC_DIR}")

    archivos = sorted(SRC_DIR.glob("sigep_*.csv"))
    if not archivos:
        raise SystemExit(f"No hay CSV en {SRC_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    seen_emails: set[str] = set()
    rows_out: list[dict[str, str]] = []
    dup_rows: list[dict[str, str]] = []
    total_in = 0
    vacios_correo = 0

    for src in archivos:
        with src.open(encoding=ENCODING, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                total_in += 1
                correo = formatear_correo(row.get("Correo_Perfil", ""))
                if not correo or "@" not in correo:
                    vacios_correo += 1
                    continue

                departamento = formatear_departamento(
                    row.get("Departamento_Filtro", "")
                )
                nombre = formatear_nombre(row.get("Nombre", ""))
                cargo = formatear_cargo(row.get("Cargo_Detallado", ""))
                entidad = formatear_entidad(row.get("Entidad_Asignada", ""))

                if correo in seen_emails:
                    dup_rows.append(
                        {
                            "Correo": correo,
                            "Nombre": nombre,
                            "Departamento": departamento,
                            "Archivo_origen": src.name,
                        }
                    )
                    continue

                seen_emails.add(correo)
                rows_out.append(
                    {
                        "Departamento": departamento,
                        "Nombre": nombre,
                        "Cargo": cargo,
                        "Correo": correo,
                        "Entidad_Asignada": entidad,
                    }
                )

    with OUT_CSV.open("w", encoding=ENCODING, newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNAS_OUT, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows_out)

    with DUPES.open("w", encoding=ENCODING, newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["Correo", "Nombre", "Departamento", "Archivo_origen"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(dup_rows)

    with REPORT.open("w", encoding=ENCODING, newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "filas_entrada",
                "filas_salida",
                "emails_unicos",
                "duplicados_omitidos",
                "correo_vacio_omitido",
                "archivo_salida",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "filas_entrada": total_in,
                "filas_salida": len(rows_out),
                "emails_unicos": len(seen_emails),
                "duplicados_omitidos": len(dup_rows),
                "correo_vacio_omitido": vacios_correo,
                "archivo_salida": str(OUT_CSV.relative_to(ROOT)),
            }
        )

    print(f"Fuente:   {SRC_DIR} ({len(archivos)} archivos)")
    print(f"Entrada:  {total_in:,} filas")
    print(f"Salida:   {len(rows_out):,} filas únicas → {OUT_CSV}")
    print(f"Omitidos: {len(dup_rows):,} duplicados de email → {DUPES.name}")
    if rows_out:
        s = rows_out[0]
        print("-" * 60)
        print("Muestra fila 1:")
        for k in COLUMNAS_OUT:
            print(f"  {k}: {s[k]}")


if __name__ == "__main__":
    main()
