#!/usr/bin/env python3
"""
Limpieza: alto rango (classify) + cargos vigentes → limpios_alto_rango/.

Uso (desde la raíz del repo):
    python -m src.clean
    # o
    python src/clean.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

# Permitir ejecución directa: python src/clean.py
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from classify import es_cargo_alto_rango, normalizar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INPUT_GLOB = "sigep_*.csv"
OUT_DIR = ROOT / "limpios_alto_rango"
REPORT_PATH = OUT_DIR / "_reporte_limpieza.csv"
REJECTED_SAMPLE = OUT_DIR / "_muestra_rechazados.tsv"
TOP_KEPT = OUT_DIR / "_top_cargos_conservados.tsv"

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


def es_cargo_activo(fecha_fin_raw: str, hoy: date | None = None) -> bool:
    hoy = hoy or date.today()
    raw = (fecha_fin_raw or "").strip()
    if not raw:
        return False

    n = normalizar(raw)
    if n == "ACTUAL":
        return True
    if n in {"NO ESPECIFICADA", "NO ESPECIFICADO", "NO REPORTADO", "N/A", "NA", "-"}:
        return False

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date() >= hoy
        except ValueError:
            continue
    return False


def procesar_archivo(
    src: Path,
    cargos_kept: Counter[str],
    cargos_rej: Counter[str],
    hoy: date,
) -> dict[str, int | str]:
    kept_rows: list[dict[str, str]] = []
    total = kept = rejected = rej_cargo = rej_fecha = 0

    with src.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            total += 1
            clean_row = {k.lstrip("\ufeff"): (v if v is not None else "") for k, v in row.items()}
            cargo = clean_row.get("Cargo_Detallado", "")
            fecha_fin = clean_row.get("Fecha_Fin_Cargo", "")
            cargo_n = normalizar(cargo)

            if not es_cargo_alto_rango(cargo):
                rejected += 1
                rej_cargo += 1
                cargos_rej[cargo_n] += 1
                continue

            if not es_cargo_activo(fecha_fin, hoy=hoy):
                rejected += 1
                rej_fecha += 1
                continue

            kept_rows.append({c: clean_row.get(c, "") for c in COLUMNAS})
            cargos_kept[cargo_n] += 1
            kept += 1

    dest = OUT_DIR / src.name
    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(kept_rows)

    return {
        "archivo": src.name,
        "total": total,
        "conservados": kept,
        "rechazados": rejected,
        "rechazados_cargo": rej_cargo,
        "rechazados_fecha": rej_fecha,
        "pct_conservado": round(100.0 * kept / total, 2) if total else 0.0,
        "salida": dest.name,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    archivos = sorted(p for p in ROOT.glob(INPUT_GLOB) if p.parent == ROOT)
    if not archivos:
        raise SystemExit(f"No se encontraron {INPUT_GLOB} en {ROOT}")

    print(f"Entrada: {len(archivos)} CSV")
    print(f"Salida:  {OUT_DIR}")
    hoy = date.today()
    print(f"Fecha corte (activos): {hoy.isoformat()}")
    print("-" * 60)

    reportes: list[dict[str, int | str]] = []
    gran_total = gran_kept = gran_rej_cargo = gran_rej_fecha = 0
    cargos_kept: Counter[str] = Counter()
    cargos_rej: Counter[str] = Counter()

    for src in archivos:
        stats = procesar_archivo(src, cargos_kept, cargos_rej, hoy=hoy)
        reportes.append(stats)
        gran_total += int(stats["total"])
        gran_kept += int(stats["conservados"])
        gran_rej_cargo += int(stats["rechazados_cargo"])
        gran_rej_fecha += int(stats["rechazados_fecha"])
        print(
            f"{stats['archivo']:<55} "
            f"{stats['conservados']:>7}/{stats['total']:<7} "
            f"({stats['pct_conservado']}%)  "
            f"[fecha↓{stats['rechazados_fecha']}]"
        )

    report_fields = [
        "archivo",
        "total",
        "conservados",
        "rechazados",
        "rechazados_cargo",
        "rechazados_fecha",
        "pct_conservado",
        "salida",
    ]
    with REPORT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=report_fields)
        writer.writeheader()
        writer.writerows(reportes)
        writer.writerow(
            {
                "archivo": "_TOTAL",
                "total": gran_total,
                "conservados": gran_kept,
                "rechazados": gran_total - gran_kept,
                "rechazados_cargo": gran_rej_cargo,
                "rechazados_fecha": gran_rej_fecha,
                "pct_conservado": round(100.0 * gran_kept / gran_total, 2) if gran_total else 0.0,
                "salida": "",
            }
        )

    with REJECTED_SAMPLE.open("w", encoding="utf-8") as f:
        f.write("freq\tcargo_normalizado\n")
        for cargo, n in cargos_rej.most_common(100):
            f.write(f"{n}\t{cargo}\n")

    with TOP_KEPT.open("w", encoding="utf-8") as f:
        f.write("freq\tcargo_normalizado\n")
        for cargo, n in cargos_kept.most_common(80):
            f.write(f"{n}\t{cargo}\n")

    pct = round(100.0 * gran_kept / gran_total, 2) if gran_total else 0.0
    print("-" * 60)
    print(f"TOTAL: {gran_kept:,} / {gran_total:,} ({pct}%)")
    print("Listo.")


if __name__ == "__main__":
    main()
