"""
Formato tipográfico para outreach B2G (nombres, cargos, entidades).

- UTF-8 con BOM (utf-8-sig) en lectura/escritura CSV
- Title case español con partículas
- Restauración de tildes en vocabulario institucional y apellidos frecuentes
"""

from __future__ import annotations

import re
import unicodedata

ENCODING = "utf-8-sig"

# Partículas que van en minúscula (salvo al inicio o tras puntuación fuerte).
_PARTICULAS = frozenset(
    {
        "a",
        "al",
        "con",
        "de",
        "del",
        "e",
        "el",
        "en",
        "la",
        "las",
        "los",
        "o",
        "para",
        "por",
        "u",
        "y",
    }
)

# Token en mayúsculas (sin tildes) → forma ortográfica correcta (minúsculas + tildes).
# Se aplica por palabra completa antes del title case.
_ORTOGRAFIA: dict[str, str] = {
    # Institucional / cargos
    "GOBERNACION": "gobernación",
    "ALCALDIA": "alcaldía",
    "ALCALDIAS": "alcaldías",
    "NACION": "nación",
    "NACIONAL": "nacional",
    "NACIONALES": "nacionales",
    "REPUBLICA": "república",
    "ADMINISTRACION": "administración",
    "ADMINISTRATIVA": "administrativa",
    "ADMINISTRATIVO": "administrativo",
    "ADMINISTRATIVOS": "administrativos",
    "ADMINISTRADORA": "administradora",
    "DIRECCION": "dirección",
    "DIRECCIONES": "direcciones",
    "SECRETARIA": "secretaría",  # cargo/área femenina institucional
    "SECRETARIAS": "secretarías",
    "EDUCACION": "educación",
    "PLANEACION": "planeación",
    "INFORMACION": "información",
    "COMUNICACION": "comunicación",
    "COMUNICACIONES": "comunicaciones",
    "ORGANIZACION": "organización",
    "ORGANIZACIONES": "organizaciones",
    "CONTRALORIA": "contraloría",
    "PROCURADURIA": "procuraduría",
    "REGISTRADURIA": "registraduría",
    "DEFENSORIA": "defensoría",
    "FISCALIA": "fiscalía",
    "PERSONERIA": "personería",
    "AUDITORIA": "auditoría",
    "TESORERIA": "tesorería",
    "NOTARIA": "notaría",
    "NOTARIADO": "notariado",
    "JURIDICA": "jurídica",
    "JURIDICO": "jurídico",
    "JURIDICOS": "jurídicos",
    "PUBLICA": "pública",
    "PUBLICO": "público",
    "PUBLICAS": "públicas",
    "PUBLICOS": "públicos",
    "TECNOLOGIA": "tecnología",
    "TECNOLOGIAS": "tecnologías",
    "TECNOLOGICO": "tecnológico",
    "TECNOLOGICA": "tecnológica",
    "TECNICO": "técnico",
    "TECNICA": "técnica",
    "TECNICOS": "técnicos",
    "TECNICAS": "técnicas",
    "GESTION": "gestión",
    "REGION": "región",
    "REGIONAL": "regional",
    "SECCION": "sección",
    "SECCIONES": "secciones",
    "ATENCION": "atención",
    "PREVENCION": "prevención",
    "PROTECCION": "protección",
    "PROMOCION": "promoción",
    "INNOVACION": "innovación",
    "TRANSFORMACION": "transformación",
    "COORDINACION": "coordinación",
    "INTEGRACION": "integración",
    "OPERACION": "operación",
    "OPERACIONES": "operaciones",
    "SUPERVISION": "supervisión",
    "REGULACION": "regulación",
    "INVESTIGACION": "investigación",
    "CAPACITACION": "capacitación",
    "FORMACION": "formación",
    "CERTIFICACION": "certificación",
    "AUTORIZACION": "autorización",
    "CONTRATACION": "contratación",
    "LIQUIDACION": "liquidación",
    "EVALUACION": "evaluación",
    "PLANIFICACION": "planificación",
    "PARTICIPACION": "participación",
    "CONCILIACION": "conciliación",
    "MEDIACION": "mediación",
    "VIGILANCIA": "vigilancia",
    "PENSIONES": "pensiones",
    "PENSION": "pensión",
    "CREDITO": "crédito",
    "CREDITOS": "créditos",
    "ECONOMICA": "económica",
    "ECONOMICO": "económico",
    "ECONOMICAS": "económicas",
    "ECONOMICOS": "económicos",
    "FINANCIERA": "financiera",
    "FINANCIERO": "financiero",
    "FINANCIERAS": "financieras",
    "FINANCIEROS": "financieros",
    "POLITICA": "política",
    "POLITICAS": "políticas",
    "POLITICO": "político",
    "BASICOS": "básicos",
    "BASICA": "básica",
    "BASICO": "básico",
    "MEDICA": "médica",
    "MEDICO": "médico",
    "MEDICAS": "médicas",
    "MEDICOS": "médicos",
    "ACADEMICA": "académica",
    "ACADEMICO": "académico",
    "ACADEMICAS": "académicas",
    "ACADEMICOS": "académicos",
    "HISTORICA": "histórica",
    "HISTORICO": "histórico",
    "TURISTICO": "turístico",
    "TURISTICA": "turística",
    "LOGISTICA": "logística",
    "LOGISTICO": "logístico",
    "ELECTRICOS": "eléctricos",
    "ELECTRICA": "eléctrica",
    "ELECTRICO": "eléctrico",
    "HIDRAULICA": "hidráulica",
    "HIDRAULICO": "hidráulico",
    "AGRICOLA": "agrícola",
    "AGRICOLAS": "agrícolas",
    "MINERIA": "minería",
    "ENERGIA": "energía",
    "GEOGRAFIA": "geografía",
    "CARTOGRAFIA": "cartografía",
    "BIOLOGIA": "biología",
    "QUIMICA": "química",
    "FISICA": "física",
    "MATEMATICAS": "matemáticas",
    "ESTADISTICA": "estadística",
    "ESTADISTICAS": "estadísticas",
    "DEMOGRAFIA": "demografía",
    "CATEGORIA": "categoría",
    "CATEGORIAS": "categorías",
    "AREA": "área",
    "AREAS": "áreas",
    "NUMERO": "número",
    "NUMEROS": "números",
    "CODIGO": "código",
    "CODIGOS": "códigos",
    "INDICE": "índice",
    "INDICES": "índices",
    "ANALISIS": "análisis",
    "DIAGNOSTICO": "diagnóstico",
    "DIAGNOSTICOS": "diagnósticos",
    "METODOLOGIA": "metodología",
    "TECNOLOGIA": "tecnología",
    "TELECOMUNICACIONES": "telecomunicaciones",
    "INFORMATICA": "informática",
    "AUTOMATIZACION": "automatización",
    "DIGITALIZACION": "digitalización",
    "MODERNIZACION": "modernización",
    "OPTIMIZACION": "optimización",
    "STANDARDIZACION": "estandarización",
    "ESTANDARIZACION": "estandarización",
    "CONSTITUCION": "constitución",
    "CONSTITUCIONAL": "constitucional",
    "LEGISLACION": "legislación",
    "JURISDICCION": "jurisdicción",
    "COMPETENCIA": "competencia",
    "COMPETENCIAS": "competencias",
    "TRANSITO": "tránsito",
    "TRANSICION": "transición",
    "AMBIENTAL": "ambiental",
    "AMBIENTALES": "ambientales",
    "SALUD": "salud",
    "CULTURA": "cultura",
    "CULTURAL": "cultural",
    "CULTURALES": "culturales",
    "DEPORTE": "deporte",
    "DEPORTIVO": "deportivo",
    "DEPORTIVA": "deportiva",
    "EMPRESARIAL": "empresarial",
    "EMPRESARIALES": "empresariales",
    "INDUSTRIAL": "industrial",
    "INDUSTRIALES": "industriales",
    "PORTUARIO": "portuario",
    "PORTUARIA": "portuaria",
    "CARCELARIO": "carcelario",
    "CARCELARIA": "carcelaria",
    "PENITENCIARIO": "penitenciario",
    "PENITENCIARIA": "penitenciaria",
    "GARANTIAS": "garantías",
    "GARANTIA": "garantía",
    "INFRAESTRUCTURA": "infraestructura",
    "ADUANAS": "aduanas",
    "IMPUESTOS": "impuestos",
    "HACIENDA": "hacienda",
    "INTERIOR": "interior",
    "EXTERIORES": "exteriores",
    "DEFENSA": "defensa",
    "JUSTICIA": "justicia",
    "TRABAJO": "trabajo",
    "VIVIENDA": "vivienda",
    "TRANSPORTE": "transporte",
    "COMERCIO": "comercio",
    "INDUSTRIA": "industria",
    "AGRICULTURA": "agricultura",
    "MINAS": "minas",
    "AMBIENTE": "ambiente",
    "CIENCIA": "ciencia",
    "TECNOLOGIA": "tecnología",
    "LIDER": "líder",
    "LIDERES": "líderes",
    "ASESOR": "asesor",
    "ASESORA": "asesora",
    "ASESORES": "asesores",
    "COORDINADOR": "coordinador",
    "COORDINADORA": "coordinadora",
    "DIRECTOR": "director",
    "DIRECTORA": "directora",
    "SUBDIRECTOR": "subdirector",
    "SUBDIRECTORA": "subdirectora",
    "GERENTE": "gerente",
    "SUBGERENTE": "subgerente",
    "SECRETARIO": "secretario",
    "PRESIDENTE": "presidente",
    "VICEPRESIDENTE": "vicepresidente",
    "GOBERNADOR": "gobernador",
    "GOBERNADORA": "gobernadora",
    "ALCALDE": "alcalde",
    "ALCALDESA": "alcaldesa",
    "RECTOR": "rector",
    "RECTORA": "rectora",
    "VICERRECTOR": "vicerrector",
    "VICERRECTORA": "vicerrectora",
    "DECANO": "decano",
    "DECANA": "decana",
    "CONCEJAL": "concejal",
    "CONCEJALES": "concejales",
    "DIPUTADO": "diputado",
    "DIPUTADA": "diputada",
    "PERSONERO": "personero",
    "PERSONERA": "personera",
    "CONTRALOR": "contralor",
    "CONTRALORA": "contralora",
    "PROCURADOR": "procurador",
    "PROCURADORA": "procuradora",
    "DEFENSOR": "defensor",
    "DEFENSORA": "defensora",
    "REGISTRADOR": "registrador",
    "REGISTRADORA": "registradora",
    "SUPERINTENDENTE": "superintendente",
    "COMISIONADO": "comisionado",
    "COMISIONADA": "comisionada",
    "MINISTRO": "ministro",
    "MINISTRA": "ministra",
    "JEFE": "jefe",
    "JEFA": "jefa",
    "OFICINA": "oficina",
    "GRUPO": "grupo",
    "PROGRAMA": "programa",
    "PROYECTO": "proyecto",
    "DEPARTAMENTO": "departamento",
    "MUNICIPAL": "municipal",
    "MUNICIPALES": "municipales",
    "DISTRITAL": "distrital",
    "DISTRITALES": "distritales",
    "GENERAL": "general",
    "GENERALES": "generales",
    "ESPECIAL": "especial",
    "ESPECIALES": "especiales",
    "ESPECIALIZADO": "especializado",
    "ESPECIALIZADA": "especializada",
    "DELEGADO": "delegado",
    "DELEGADA": "delegada",
    "TERRITORIAL": "territorial",
    "TERRITORIALES": "territoriales",
    "UNIVERSIDAD": "universidad",
    "INSTITUTO": "instituto",
    "AGENCIA": "agencia",
    "UNIDAD": "unidad",
    "FONDO": "fondo",
    "SERVICIO": "servicio",
    "SERVICIOS": "servicios",
    "APRENDIZAJE": "aprendizaje",
    "BIENESTAR": "bienestar",
    "FAMILIAR": "familiar",
    "ESTADO": "estado",
    "CIVIL": "civil",
    "PUEBLO": "pueblo",
    "SENADO": "senado",
    "CAMARA": "cámara",
    "CONGRESO": "congreso",
    "POLICIA": "policía",
    "EJERCITO": "ejército",
    "ARMADA": "armada",
    "AEREA": "aérea",
    "FUERZA": "fuerza",
    # Apellidos / nombres frecuentes (Colombia)
    "GOMEZ": "gómez",
    "GONZALEZ": "gonzález",
    "RODRIGUEZ": "rodríguez",
    "MARTINEZ": "martínez",
    "HERNANDEZ": "hernández",
    "LOPEZ": "lópez",
    "PEREZ": "pérez",
    "SANCHEZ": "sánchez",
    "RAMIREZ": "ramírez",
    "GARCIA": "garcía",
    "DIAZ": "díaz",
    "VAZQUEZ": "vázquez",
    "JIMENEZ": "jiménez",
    "ALVAREZ": "álvarez",
    "GUTIERREZ": "gutiérrez",
    "RUIZ": "ruiz",
    "MUÑOZ": "muñoz",
    "MUNOZ": "muñoz",
    "SUAREZ": "suárez",
    "MEJIA": "mejía",
    "CARDENAS": "cárdenas",
    "ORDONEZ": "órdóñez",
    "ORDOÑEZ": "ordoñez",
    "NUÑEZ": "núñez",
    "NUNEZ": "núñez",
    "PEÑA": "peña",
    "PENA": "peña",
    "PINZON": "pinzón",
    "RINCON": "rincón",
    "LEON": "león",
    "BELTRAN": "beltrán",
    "GALVIS": "galvis",
    "CASTAÑEDA": "castañeda",
    "CASTANEDA": "castañeda",
    "CATAÑEDA": "catañeda",
    "PATIÑO": "patiño",
    "PATINO": "patiño",
    "QUIÑONES": "quiñones",
    "QUINONES": "quiñones",
    "IBANEZ": "ibáñez",
    "IBAÑEZ": "ibáñez",
    "MARIN": "marín",
    "MALDONADO": "maldonado",
    "ARBELAEZ": "arbeláez",
    "HECTOR": "héctor",
    "CESAR": "césar",
    "MARIA": "maría",
    "JOSE": "josé",
    "ANDRES": "andrés",
    "ANGEL": "ángel",
    "RAUL": "raúl",
    "JESUS": "jesús",
    "TOMAS": "tomás",
    "NICOLAS": "nicolás",
    "SEBASTIAN": "sebastián",
    "MARTIN": "martín",
    "ADRIAN": "adrián",
    "ROMAN": "román",
    "RAMON": "ramón",
    "RUBEN": "rubén",
    "IVAN": "iván",
    "OSCAR": "óscar",
    "VICTOR": "víctor",
    "MONICA": "mónica",
    "VERONICA": "verónica",
    "ANGELA": "ángela",
    "SONIA": "sonia",
    "LUCIA": "lucía",
    "SOFIA": "sofía",
    "ROCIO": "rocío",
    "INES": "inés",
    "BEATRIZ": "beatriz",
    "AIDE": "aide",
    "GUZMAN": "guzmán",
    "MEDELLIN": "medellín",
    "BOGOTA": "bogotá",
    "ATLANTICO": "atlántico",
    "BOLIVAR": "bolívar",
    "BOYACA": "boyacá",
    "CAQUETA": "caquetá",
    "CORDOBA": "córdoba",
    "CHOCO": "chocó",
    "NARINO": "nariño",
    "QUINDIO": "quindío",
    "VAUPES": "vaupés",
    "GUAINIA": "guainía",
    "ARCHIPIELAGO": "archipiélago",
    "ANIBAL": "aníbal",
    "COMPANIA": "compañía",
    "COMPANIAS": "compañías",
    "ENOLOGIA": "enología",
    "GEOGRAFICA": "geográfica",
    "GEOGRAFICO": "geográfico",
}

_ROMANOS_VALIDOS = frozenset(
    {
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "XII",
        "XIII",
        "XIV",
        "XV",
        "XX",
        "XXI",
        "XXX",
    }
)
_RE_ROMANO = re.compile(r"\b([ivxlcdm]{1,6})\b", flags=re.IGNORECASE)

# Departamentos SIGEP → etiqueta de presentación (33 valores conocidos).
_DEPARTAMENTOS: dict[str, str] = {
    "AMAZONAS": "Amazonas",
    "ANTIOQUIA": "Antioquia",
    "ARAUCA": "Arauca",
    "ARCHIPIÉLAGO DE SAN ANDRÉS. PROVIDENCIA Y SANTA CATALINA": (
        "Archipiélago de San Andrés, Providencia y Santa Catalina"
    ),
    "ARCHIPIELAGO DE SAN ANDRES. PROVIDENCIA Y SANTA CATALINA": (
        "Archipiélago de San Andrés, Providencia y Santa Catalina"
    ),
    "ATLÁNTICO": "Atlántico",
    "ATLANTICO": "Atlántico",
    "BOGOTÁ. D.C.": "Bogotá, D.C.",
    "BOGOTA. D.C.": "Bogotá, D.C.",
    "BOLÍVAR": "Bolívar",
    "BOLIVAR": "Bolívar",
    "BOYACÁ": "Boyacá",
    "BOYACA": "Boyacá",
    "CALDAS": "Caldas",
    "CAQUETÁ": "Caquetá",
    "CAQUETA": "Caquetá",
    "CASANARE": "Casanare",
    "CAUCA": "Cauca",
    "CESAR": "Cesar",
    "CHOCÓ": "Chocó",
    "CHOCO": "Chocó",
    "CUNDINAMARCA": "Cundinamarca",
    "CÓRDOBA": "Córdoba",
    "CORDOBA": "Córdoba",
    "GUAINÍA": "Guainía",
    "GUAINIA": "Guainía",
    "GUAVIARE": "Guaviare",
    "HUILA": "Huila",
    "LA GUAJIRA": "La Guajira",
    "MAGDALENA": "Magdalena",
    "META": "Meta",
    "NARIÑO": "Nariño",
    "NARINO": "Nariño",
    "NORTE DE SANTANDER": "Norte de Santander",
    "PUTUMAYO": "Putumayo",
    "QUINDÍO": "Quindío",
    "QUINDIO": "Quindío",
    "RISARALDA": "Risaralda",
    "SANTANDER": "Santander",
    "SUCRE": "Sucre",
    "TOLIMA": "Tolima",
    "VALLE DEL CAUCA": "Valle del Cauca",
    "VAUPÉS": "Vaupés",
    "VAUPES": "Vaupés",
    "VICHADA": "Vichada",
}

_RE_SPACES = re.compile(r"\s+")
_RE_CARGO_PREFIX = re.compile(
    r"^(?:"
    r"\d+\s*/\s*\d+\s+"  # 290/2013 …
    r"|\d+\s*-\s*\d{4}\s*-?\s*"  # 509-2013- …
    r"|\d+\s+DE\s+\d+\s+"  # 020 DE 2003 …
    r"|\d{2,6}\s+"  # 1045  / 5140 …
    r")"
)
_RE_TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)?|[^\s]")

# Códigos de grado/escala SIGEP a preservar (4035-05, 1020-08, 40-35-05, G-19).
_RE_CODIGO_GRADO = re.compile(r"\b\d{1,4}(?:-\d{2}){1,3}\b")
_RE_CODIGO_LETRA = re.compile(r"\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{1,3}-\d{1,4}\b")
_RE_RESOLUCION = re.compile(r"\b\d{2,4}-\d{4}\b")

# Siglas que deben permanecer en mayúsculas dentro del cargo.
_SIGLAS_CARGO = frozenset({"CEO", "CIO", "CTO", "CFO", "TIC", "TI", "RH", "TH", "SEO"})

# Raíces claramente truncadas en SIGEP (no completamos: solo punto de abreviatura).
_RAICES_TRUNCADAS = frozenset(
    {
        "operac",
        "administ",
        "financ",
        "gestio",
        "comec",
        "comecial",
        "planific",
        "coordinac",
        "organiz",
        "informat",
        "comunic",
        "capacita",
        "contrat",
        "evaluac",
        "investig",
        "supervis",
        "represent",
        "profesion",
        "especializ",
        "universit",
        "jurisdic",
        "constituc",
        "particip",
        "implement",
        "seguimient",
        "presupuest",
        "infraestruct",
    }
)

# Palabras cortas válidas (no llevan punto automático).
_CORTAS_OK = frozenset(
    {
        "a",
        "al",
        "de",
        "del",
        "el",
        "en",
        "la",
        "las",
        "los",
        "y",
        "e",
        "o",
        "u",
        "un",
        "una",
        "tic",
        "cio",
        "seo",
        "ti",
        "rh",
        "th",
        "ss",
        "sa",
        "ese",
        "eps",
        "ips",
        "nrf",
        "nit",
    }
) | {r.lower() for r in _ROMANOS_VALIDOS}

# Terminaciones típicas de palabra española completa.
_RE_FINAL_COMPLETA = re.compile(
    r"(?:"
    r"ción|sión|dad|tad|mente|"
    r"as|es|os|is|"
    r"ar|er|ir|or|ur|"
    r"al|il|el|ol|ul|"
    r"an|en|in|on|un|"
    r"az|ez|iz|oz|uz|"
    r"ad|ed|id|ud|"
    r"[aeiouáéíóúñ]"
    r")$",
    flags=re.IGNORECASE,
)


def fold_key(text: str) -> str:
    """Mayúsculas sin tildes para lookup ortográfico."""
    nfd = unicodedata.normalize("NFD", (text or "").strip())
    sin_tildes = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return sin_tildes.upper()


def limpiar_espacios(text: str) -> str:
    return _RE_SPACES.sub(" ", (text or "").replace("\xa0", " ")).strip()


def limpiar_cargo_ruido(cargo: str) -> str:
    """Quita códigos de grado/resolución al inicio si ensucian la plantilla."""
    t = limpiar_espacios(cargo)
    if not t:
        return t
    m2 = re.match(
        r"^(?:"
        r"\d+\s*/\s*\d+\s+"
        r"|\d+\s*-\s*\d{4}\s*-?\s*"
        r"|\d+\s+[Dd][Ee]\s+\d+\s+"
        r"|\d{2,6}\s+"
        r")",
        t,
    )
    if m2:
        return limpiar_espacios(t[m2.end() :])
    return t


def _proteger_codigos(text: str) -> tuple[str, list[str]]:
    """Reemplaza temporalmente códigos 1020-08 / G-19 / 509-2013 para no romper guiones."""
    guardados: list[str] = []

    def _keep(match: re.Match[str]) -> str:
        guardados.append(match.group(0))
        return f"§C{len(guardados) - 1}§"

    t = _RE_CODIGO_GRADO.sub(_keep, text)
    t = _RE_CODIGO_LETRA.sub(_keep, t)
    t = _RE_RESOLUCION.sub(_keep, t)
    return t, guardados


def _restaurar_codigos(text: str, guardados: list[str]) -> str:
    for i, original in enumerate(guardados):
        text = text.replace(f"§C{i}§", original)
    return text


def _es_token_truncado(token: str) -> bool:
    """True si el token parece abreviatura/corte SIGEP (sin adivinar la forma plena)."""
    if not token or any(ch.isdigit() for ch in token):
        return False
    if token.endswith("."):
        return False

    fold = fold_key(token).lower()
    if fold in _CORTAS_OK or fold in _PARTICULAS:
        return False
    if fold.upper() in _ROMANOS_VALIDOS:
        return False
    if fold in {fold_key(v).lower() for v in _ORTOGRAFIA.values()}:
        return False
    if fold in _RAICES_TRUNCADAS or any(
        fold.startswith(r) and len(fold) <= len(r) + 2 for r in _RAICES_TRUNCADAS
    ):
        # operac, operaci (aún incompleto) sí; operaciones no (más largo y final completa)
        if not _RE_FINAL_COMPLETA.search(token):
            return True
        if fold in _RAICES_TRUNCADAS:
            return True

    # Abreviaturas cortas frecuentes en cortes SIGEP
    if fold in {"fin", "rep", "adm", "gral", "dir", "coord", "subd", "presup"}:
        return True

    # Heurística: 4–8 letras sin terminación española típica
    if 4 <= len(fold) <= 8 and not _RE_FINAL_COMPLETA.search(token):
        return True

    return False


def pulir_cargo_presentacion(cargo: str) -> str:
    """
    Limpieza visual para cuerpo de correo HTML:
    - quita guiones decorativos (no códigos de grado)
    - quita comas/barras finales
    - marca cortes SIGEP con punto (Operac. / Fin.) sin completar la palabra
    """
    t = limpiar_espacios(cargo)
    if not t:
        return t

    t, codigos = _proteger_codigos(t)

    # Guiones decorativos
    t = t.strip(" -_")
    t = re.sub(r"\s*-\s*", " ", t)
    t = re.sub(r"\s*_+\s*", " ", t)

    # Coma o barra final
    t = re.sub(r"[,/;]+$", "", t).strip()

    t = _restaurar_codigos(t, codigos)
    t = limpiar_espacios(t)

    # Punto en tokens truncados (conservar tipografía ya aplicada)
    partes = re.findall(
        r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:\.[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)?|[^\sA-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|\s+",
        t,
    )
    out: list[str] = []
    for parte in partes:
        if not parte.isalpha() and not all(
            ch.isalpha() or ch in "ÁÉÍÓÚÜÑáéíóúüñ" for ch in parte
        ):
            out.append(parte)
            continue
        if _es_token_truncado(parte):
            out.append(parte + ".")
        else:
            out.append(parte)

    result = "".join(out)
    result = limpiar_espacios(result)
    result = result.replace(" .", ".").replace(" ,", ",")
    result = re.sub(r"\.{2,}", ".", result)
    # Espacio tras punto de abreviatura si sigue letra.
    result = re.sub(r"\.([A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", r". \1", result)
    result = limpiar_espacios(result)

    # Restaurar siglas en mayúsculas (CEO, TIC, …)
    def _sigla(match: re.Match[str]) -> str:
        token = match.group(0)
        key = fold_key(token).upper()
        return key if key in _SIGLAS_CARGO else token

    result = re.sub(
        r"\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,3}\b",
        _sigla,
        result,
    )
    return result


def _forma_palabra(token: str) -> str:
    """Devuelve la forma ortográfica preferida en minúsculas si hay glosario."""
    if not token.isalpha() and not all(
        ch.isalpha() or ch in "ÁÉÍÓÚÜÑáéíóúüñ'" for ch in token
    ):
        return token

    key = fold_key(token.replace("'", ""))
    if key in _ORTOGRAFIA:
        base = _ORTOGRAFIA[key]
        # Conservar apóstrofe raro si existía
        if "'" in token:
            return token  # caso raro; no forzar
        return base

    # Si ya trae tildes, respetar y solo bajar a minúsculas
    if any(c in "ÁÉÍÓÚÜÑáéíóúüñ" for c in token):
        return token.lower()

    return token.lower()


def title_case_es(text: str) -> str:
    """Title case español: partículas en minúscula; glosario de tildes."""
    t = limpiar_espacios(text)
    if not t:
        return t

    # Punto usado como separador en SIGEP → coma (ej. BOGOTÁ. D.C.)
    t = t.replace(" .", ".").replace(". ", ", ")
    t = re.sub(r",\s*,", ",", t)

    tokens = _RE_TOKEN.findall(t)
    words: list[str] = []
    force_cap = True

    for tok in tokens:
        if not any(ch.isalpha() for ch in tok):
            words.append(tok)
            if tok in ".,;:!?":
                force_cap = True
            continue

        folded = fold_key(tok).lower()
        is_particle = folded in _PARTICULAS or tok.lower() in _PARTICULAS

        if not force_cap and is_particle:
            words.append(folded if folded in _PARTICULAS else tok.lower())
            force_cap = False
            continue

        word = _forma_palabra(tok)
        capped = word[0].upper() + word[1:] if word else word
        words.append(capped)
        force_cap = False

    parts: list[str] = []
    for i, tok in enumerate(words):
        if i == 0:
            parts.append(tok)
            continue
        prev = parts[-1]
        tok_alpha = any(ch.isalpha() for ch in tok)
        prev_alpha = any(ch.isalpha() for ch in prev)

        if tok in ",.;:!?%" or tok in ")/]":
            parts.append(tok)
        elif prev in "(/[¿¡":
            parts.append(tok)
        elif tok_alpha and prev_alpha:
            parts.append(" ")
            parts.append(tok)
        elif tok_alpha and prev in ",.;:!?":
            parts.append(" ")
            parts.append(tok)
        elif tok[0].isdigit() and prev_alpha:
            parts.append(" ")
            parts.append(tok)
        else:
            if tok_alpha and prev not in "(/[":
                parts.append(" ")
            parts.append(tok)

    result = limpiar_espacios("".join(parts))
    result = result.replace(" ,", ",").replace(" .", ".")
    result = result.replace(",,", ",")
    result = re.sub(r"\s*/\s*", " / ", result)
    result = re.sub(r"\s*&\s*", " & ", result)

    def _romano(match: re.Match[str]) -> str:
        token = match.group(1).upper()
        return token if token in _ROMANOS_VALIDOS else match.group(0)

    return _RE_ROMANO.sub(_romano, result)


def formatear_departamento(raw: str) -> str:
    key = limpiar_espacios(raw)
    if key in _DEPARTAMENTOS:
        return _DEPARTAMENTOS[key]
    folded = fold_key(key)
    for origen, destino in _DEPARTAMENTOS.items():
        if fold_key(origen) == folded:
            return destino
    return title_case_es(key)


def formatear_nombre(raw: str) -> str:
    return title_case_es(raw)


def formatear_cargo(raw: str) -> str:
    base = title_case_es(limpiar_cargo_ruido(raw))
    return pulir_cargo_presentacion(base)


def formatear_entidad(raw: str) -> str:
    t = limpiar_espacios(raw)
    es_sas = bool(re.search(r"\bS\.?\s*A\.?\s*S\.?\s*\.?$", t, flags=re.I))
    es_sa = bool(re.search(r"\bS\.?\s*A\.?\s*\.?$", t, flags=re.I))

    # Retirar sufijo societario y punto final decorativo antes del title case
    t = re.sub(r"\bS\.?\s*A\.?\s*S\.?\s*\.?$", "", t, flags=re.I).rstrip(" .")
    if not es_sas:
        t = re.sub(r"\bS\.?\s*A\.?\s*\.?$", "", t, flags=re.I).rstrip(" .")
    if t.endswith("."):
        t = t[:-1].rstrip()

    formatted = title_case_es(t)
    if es_sas:
        formatted = f"{formatted} S.A.S.".strip()
    elif es_sa:
        formatted = f"{formatted} S.A.".strip()
    return formatted


def formatear_correo(raw: str) -> str:
    return limpiar_espacios(raw).replace(" ", "").lower()
