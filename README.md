# SIGEP Sales Intelligence

Pipeline en Python para **extracción, segmentación y preparación de leads** a partir del directorio público SIGEP (Función Pública — Colombia).

Diseñado para ventas B2G / outreach a personal de alto rango en entidades públicas (secretario de despacho, director, alcalde, gerente, etc.).

> **Nota:** este repositorio publica **código y documentación**. Los datasets con nombres, correos y teléfonos **no se versionan** (PII).

---

## Pipeline

```text
SIGEP (web)
    │
    ▼
[1] scraper.py          → CSV por departamento (crudo)
    │
    ▼
[2] classify.py         → reglas de cargo (alto rango sí/no)
    │
[3] clean.py            → aplica classify + solo cargos vigentes
    │                      → limpios_alto_rango/
    ▼
[4] email_ready.py      → subset con correo válido
                           → limpios_alto_rango_con_correo/
```

| Etapa | Salida típica (corrida real) |
|-------|------------------------------|
| Scraping nacional | ~395 000 filas · 33 departamentos |
| Alto rango + activos | ~21 000 filas |
| Con correo usable | ~13 500 filas |

*(Las cifras exactas dependen de la fecha de corrida y de la calidad de SIGEP.)*

---

## Stack

- Python 3.10+
- `requests` + `BeautifulSoup` (scraping)
- `pandas` / `csv` (I/O)
- Regex + normalización Unicode (clasificación de cargos)
- `unittest` (tests del filtro)

---

## Instalación

```bash
git clone https://github.com/<TU_USUARIO>/sigep-sales-intelligence.git
cd sigep-sales-intelligence
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Uso

Desde la **raíz del repo**:

```bash
# 1) Extraer (puede tardar horas a escala nacional)
python src/scraper.py

# 2) Segmentar alto rango + vigentes
python src/clean.py

# 3) Quedarse solo con correos válidos (campañas email)
python src/email_ready.py
```

Tests:

```bash
python -m unittest discover -s tests -v
```

---

## Estructura

```text
sigep-sales-intelligence/
├── README.md
├── LICENSE
├── requirements.txt
├── src/
│   ├── scraper.py      # extracción SIGEP
│   ├── classify.py     # taxonomía de cargos
│   ├── clean.py        # limpieza + vigencia
│   └── email_ready.py  # subset con email
├── docs/
│   ├── architecture.md
│   └── methodology.md
├── sample/
│   └── sample.csv      # ejemplo sintético (sin PII real)
├── assets/             # diagramas (opcional)
└── tests/
```

---

## Documentación

- [Architecture](docs/architecture.md) — flujo técnico
- [Methodology](docs/methodology.md) — criterios de inclusión/exclusión

---

## Ética y datos

- Fuente: directorio público de hojas de vida SIGEP (Función Pública).
- Uso responsable: no se publican dumps con datos personales en este repo.
- Cumple con la idea de **código abierto + datos sensibles fuera de Git**.

Próximo paso de producto (fuera de este release): normalización de columnas para importación en **BillionMail**.

---

## Autor

**Danniel Mena** — ARKA (Bogotá)  
Scraping · data cleaning · sales intelligence

---

## License

MIT — ver [LICENSE](LICENSE).
