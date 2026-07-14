#!/usr/bin/env python3
"""
Clasificación de cargos SIGEP para segmentación de alto rango / decisores.

Reglas de negocio (inclusión + exclusión con límites de palabra).
No lee ni escribe CSV: solo decide si un cargo pasa el filtro.
"""

from __future__ import annotations

import re
import unicodedata

_RE_BASURA = re.compile(r"[´¨`]+")
_RE_SPACES = re.compile(r"\s+")

_RE_PROFESIONAL = re.compile(r"\bPROFESIONAL\s+(UNIVERSITARIO|ESPECIALIZADO)\b")

_RE_EXCLUDE = [
    re.compile(p)
    for p in [
        r"\bAUXILIAR\b",
        r"\bAYUDANTE\b",
        r"\bASISTENTE\b",
        r"\bOPERARI[OA]\b",
        r"\bCONDUCTOR\b",
        r"\bCELADOR\b",
        r"\bDRAGONEANTE\b",
        r"\bMENSAJERO\b",
        r"\bDOCENTE\b",
        r"\bINSTRUCTOR\b",
        r"\bSERVICIOS GENERALES\b",
        r"\bSECRETARIA EJECUTIVA\b",
        r"\bSECRETARIO EJECUTIVO\b",
        r"^SECRETARIA$",
        r"^CARGO\s+DE\s+SECRETARIA$",
        r"\bABOGAD",
        r"\bLITIGANTE\b",
        r"\bDEFENSOR DE FAMILIA",
        r"\bASESOR COMERCIAL\b",
        r"E*ENFERMER[AO]?\b",
        r"\bJEFE DE ENFERMERIA\b",
        r"\bCOORDINADOR\b.{0,30}\bENFERMER",
        r"\bMAGISTRADO\b",
        r"\bREVISOR FISCAL\b",
    ]
]

_RE_CONTADOR = re.compile(r"\bCONTADOR[A]?\b")
_RE_CONTADOR_OVERRIDE = re.compile(
    r"\b(DIRECTOR[A]?|SUBDIRECTOR[A]?|GERENTE|SUBGERENTE|SECRETARIO|ALCALDE)\b"
)
_RE_FISCAL = re.compile(r"\bFISCAL")
_RE_FISCAL_OVERRIDE = re.compile(
    r"\b(DIRECTOR[A]?|SUBDIRECTOR[A]?|GERENTE|SUBGERENTE|JEFE|SECRETARIO)\b"
)
_RE_TESORERO = re.compile(r"\bTESORERO\b")
_RE_TESORERO_OVERRIDE = re.compile(
    r"\b(SECRETARIO|DIRECTOR[A]?|GERENTE|SUBGERENTE|ALCALDE|GOBERNADOR)\b"
)
_RE_TECNICO = re.compile(r"\bTECNIC[OA]\b")
_RE_MANDO_OVERRIDE = re.compile(
    r"\b("
    r"DIRECTOR[A]?|SUBDIRECTOR[A]?|GERENTE|SUBGERENTE|"
    r"JEFE|SECRETARIO|PRESIDENTE|VICEPRESIDENTE|"
    r"ALCALDE|GOBERNADOR|RECTOR|COORDINADOR|ASESOR|LIDER"
    r")\b"
)

_JUNK = {
    "",
    "NO ESPECIFICADO",
    "NO REPORTADO",
    "REQUIERE CORRECION",
    "N/A",
    "NA",
    "-",
    ".",
}

_RE_INCLUDE = [
    re.compile(p)
    for p in [
        r"\bPRESIDENTE\b",
        r"\bVICEPRESIDENTE\b",
        r"\bGOBERNADOR[A]?\b",
        r"\bVICEGOBERNADOR[A]?\b",
        r"\bALCALDE[SA]?\b",
        r"\bVICEALCALDE\b",
        r"\bRECTOR[A]?\b",
        r"\bVICERRECTOR[A]?\b",
        r"\bDECAN[OA]\b",
        r"\bGERENTE\b",
        r"\bSUBGERENTE\b",
        r"\bDIRECTOR[A]?\b",
        r"\bSUBDIRECTOR[A]?\b",
        r"\bSECRETARIO\b",
        r"\bSECRETARIA\s+(GENERAL|DE\s+DESPACHO|DE\b)",
        r"\bJEFE\b",
        r"\bCOORDINADOR[A]?\b",
        r"\bASESOR[A]?\b",
        r"\bLIDER\b",
        r"\bARQUITECTO\b.{0,40}\b(TI|EMPRESARIAL)\b",
        r"\bARQUITECTO EMPRESARIAL\b",
        r"\bCHIEF INFORMATION OFFICER\b",
        r"(?<![A-Z0-9])CIO(?![A-Z0-9])",
        r"\bPERSONERO\b",
        r"\bCONTRALOR\b",
        r"\bPROCURADOR\b",
        r"\bDEFENSOR\b",
        r"\bSUPERINTENDENTE\b",
        r"\bCOMISIONADO\b",
        r"\bREGISTRADOR\b",
        r"\bCONCEJAL\b",
        r"\bDIPUTADO\b",
        r"\bMINISTRO\b",
        r"\bVICEMINISTRO\b",
        r"\bINTENDENTE\b",
    ]
]


def normalizar(texto: str) -> str:
    s = (texto or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = _RE_BASURA.sub("", s)
    s = _RE_SPACES.sub(" ", s)
    return s


def es_excluido(cargo_n: str) -> bool:
    if cargo_n in _JUNK:
        return True
    if _RE_PROFESIONAL.search(cargo_n):
        return True
    for rx in _RE_EXCLUDE:
        if rx.search(cargo_n):
            return True
    if _RE_CONTADOR.search(cargo_n) and not _RE_CONTADOR_OVERRIDE.search(cargo_n):
        return True
    if _RE_TESORERO.search(cargo_n) and not _RE_TESORERO_OVERRIDE.search(cargo_n):
        return True
    if _RE_FISCAL.search(cargo_n) and not _RE_FISCAL_OVERRIDE.search(cargo_n):
        return True
    if _RE_TECNICO.search(cargo_n) and not _RE_MANDO_OVERRIDE.search(cargo_n):
        return True
    return False


def es_incluido(cargo_n: str) -> bool:
    return any(rx.search(cargo_n) for rx in _RE_INCLUDE)


def es_cargo_alto_rango(cargo_raw: str) -> bool:
    """True si el cargo entra en el segmento de interés comercial."""
    cargo_n = normalizar(cargo_raw)
    if es_excluido(cargo_n):
        return False
    return es_incluido(cargo_n)
