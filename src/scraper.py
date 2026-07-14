import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
from urllib.parse import urlparse, parse_qs
from typing import List, Dict
import re
import os
import zipfile
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==========================================
# CONFIGURACIÓN GENERAL Y CARPETAS
# ==========================================
BASE_URL = "https://www.funcionpublica.gov.co/dafpIndexerBHV/hvSigep/index"
DOMINIO_BASE = "https://www.funcionpublica.gov.co"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.funcionpublica.gov.co/sigep2/directorio"
}

session = requests.Session()
retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('https://', HTTPAdapter(max_retries=retries))
session.mount('http://', HTTPAdapter(max_retries=retries))

# Raíz del repo (padre de src/)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_OUTPUT = os.path.join(_ROOT, "datos_sigep")
os.makedirs(CARPETA_OUTPUT, exist_ok=True)

DEPARTAMENTOS_COLOMBIA = [
    "BOGOTÁ. D.C.", "ANTIOQUIA", "VALLE DEL CAUCA", "SANTANDER", "CUNDINAMARCA",
    "NORTE DE SANTANDER", "BOYACÁ", "META", "TOLIMA", "BOLÍVAR", "CALDAS",
    "CAUCA", "RISARALDA", "CASANARE", "NARIÑO", "CÓRDOBA", "ATLÁNTICO",
    "MAGDALENA", "CAQUETÁ", "HUILA", "QUINDÍO", "CESAR", "LA GUAJIRA",
    "GUAVIARE", "SUCRE", "CHOCÓ", "PUTUMAYO", "ARAUCA",
    "ARCHIPIÉLAGO DE SAN ANDRÉS. PROVIDENCIA Y SANTA CATALINA",
    "VAUPÉS", "AMAZONAS", "VICHADA", "GUAINÍA"
]

# ==========================================
# EXTRACCIÓN QUIRÚRGICA DEL PERFIL
# ==========================================

def extraer_datos_perfil_profundo(url_detalle: str) -> Dict[str, str]:
    url_completa = DOMINIO_BASE + url_detalle
    datos_perfil = {
        "Cargo_Detallado": "No especificado", "Fecha_Fin_Cargo": "No especificada",
        "Correo_Perfil": "No reportado", "Telefono_Perfil": "No reportado"
    }
    try:
        r = session.get(url_completa, headers=HEADERS, timeout=10)
        if r.status_code != 200: return datos_perfil
        soup = BeautifulSoup(r.text, "html.parser")

        contenedor_contacto = soup.find("div", id="datosContacto")
        if contenedor_contacto:
            spans = contenedor_contacto.find_all("span", class_="texto_detalle_directorio")
            for span in spans:
                texto = span.get_text().strip()
                if re.match(r"[^@]+@[^@]+\.[^@]+", texto): datos_perfil["Correo_Perfil"] = texto
                elif re.match(r"^\d+$", texto) and len(texto) >= 7: datos_perfil["Telefono_Perfil"] = texto

        tabla_experiencia = soup.select_one("#experienciaLaboral > div > table")
        if tabla_experiencia:
            tbody = tabla_experiencia.find("tbody")
            filas = tbody.find_all("tr") if tbody else tabla_experiencia.find_all("tr")[1:]

            for fila in filas:
                tds = fila.find_all("td")
                if len(tds) >= 4:
                    fecha_fin_texto = tds[3].get_text().strip()
                    if "actual" in fecha_fin_texto.lower():
                        datos_perfil["Cargo_Detallado"] = tds[0].get_text().strip().replace("'", "").replace("`", "").strip()
                        datos_perfil["Fecha_Fin_Cargo"] = fecha_fin_texto
                        return datos_perfil
            if filas:
                tds_primeras = filas[0].find_all("td")
                if len(tds_primeras) >= 4:
                    datos_perfil["Cargo_Detallado"] = tds_primeras[0].get_text().strip().replace("'", "").replace("`", "").strip()
                    datos_perfil["Fecha_Fin_Cargo"] = tds_primeras[3].get_text().strip()
        return datos_perfil
    except Exception:
        return datos_perfil

# ==========================================
# GESTIÓN DE IFRAME / LISTADOS
# ==========================================

def obtener_mapa_entidades(dpto: str) -> Dict[str, str]:
    params = {"find": "FindNext", "query": "", "dptoSeleccionado": dpto, "offset": "0", "max": "10"}
    mapa_entidades = {}
    try:
        r = session.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        lista_entidades = soup.find("ul", id="listFiltroEntidad")
        if not lista_entidades: return mapa_entidades
        for a in lista_entidades.find_all("a"):
            href = a.get("href")
            nombre_entidad = a.get_text().strip().split("(")[0].strip()
            if href:
                id_entidad = parse_qs(urlparse("https://base.com" + href).query).get("entidadSeleccionado")
                if id_entidad: mapa_entidades[nombre_entidad] = id_entidad[0]
        return mapa_entidades
    except Exception: return mapa_entidades

def consultar_pagina_sigep(dpto: str, entidad_id: str, offset: int) -> List[Dict]:
    params = {
        "find": "FindNext", "query": "", "dptoSeleccionado": dpto, "entidadSeleccionado": entidad_id,
        "munSeleccionado": "", "tipoAltaSeleccionado": "", "offset": str(offset), "max": "10"
    }
    try:
        r = session.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        filas = soup.find_all("tr", class_=["odd", "even"])

        resultados_pagina = []
        for fila in filas:
            col_datos = fila.find("td", class_="columna-datos")
            if col_datos:
                lineas = [l.strip() for l in col_datos.get_text(separator="\n").split("\n") if l.strip()]
                enlace_perfil = col_datos.find("a", href=True)
                url_hv = enlace_perfil.get("href") if enlace_perfil else None
                if len(lineas) >= 3:
                    resultados_pagina.append({
                        "Nombre": lineas[0], "Rol_Contrato": lineas[1], "Entidad_Asignada": lineas[2],
                        "Detalles_Contacto": lineas[3] if len(lineas) > 3 else "No registra", "URL_Hoja_Vida": url_hv
                    })
        return resultados_pagina
    except Exception: return []

# ==========================================
# ORQUESTADOR INTEGRAL ANTI-DESBORDAMIENTO
# ==========================================

def main():
    print("==================================================")
    print("[INFO] INICIANDO RASPADO MAESTRO SEGURO (NACIONAL)")
    print("==================================================\n")

    archivo_backup = "backup_sigep_nacional.csv"

    # Única barra tqdm permitida (Nivel Superior)
    pbar_dptos = tqdm(DEPARTAMENTOS_COLOMBIA, desc="Progreso Nacional")

    for dpto in pbar_dptos:
        nombre_archivo_dpto = f"sigep_{dpto.lower().replace('.', '').replace(', ', '_').replace(' ', '_')}.csv"
        ruta_completa_csv = os.path.join(CARPETA_OUTPUT, nombre_archivo_dpto)

        entidades_completadas = set()
        if os.path.exists(ruta_completa_csv):
            try:
                # Leer entidades ya procesadas para reanudar sin duplicar
                df_existente = pd.read_csv(ruta_completa_csv, usecols=["Entidad_Filtro"])
                entidades_completadas = set(df_existente["Entidad_Filtro"].unique())
            except Exception:
                pass

        pbar_dptos.set_postfix_str(f"Procesando: {dpto[:12]}")

        dict_entidades = obtener_mapa_entidades(dpto)
        if not dict_entidades: continue

        registros_departamento = []
        total_entidades = len(dict_entidades)

        for idx, (nombre_entidad, id_entidad) in enumerate(dict_entidades.items(), 1):
            if nombre_entidad in entidades_completadas:
                continue
            offset = 0
            paginando = True
            nombres_pagina_anterior = set()

            while paginando:
                pbar_dptos.set_postfix_str(
                    f"Dpto: {dpto[:10]} | Ent: {idx}/{total_entidades} - {nombre_entidad[:20]} | Reg: {offset}"
                )

                registros_pagina = consultar_pagina_sigep(dpto, id_entidad, offset)
                if not registros_pagina: break

                nombres_actuales = {r["Nombre"] for r in registros_pagina}
                if nombres_actuales == nombres_pagina_anterior: break
                nombres_pagina_anterior = nombres_actuales

                def procesar_registro(r):
                    r["Departamento_Filtro"] = dpto
                    r["Entidad_Filtro"] = nombre_entidad
                    if r["URL_Hoja_Vida"]:
                        info_profunda = extraer_datos_perfil_profundo(r["URL_Hoja_Vida"])
                        r["Cargo_Detallado"] = info_profunda["Cargo_Detallado"]
                        r["Fecha_Fin_Cargo"] = info_profunda["Fecha_Fin_Cargo"]
                        r["Correo_Perfil"] = info_profunda["Correo_Perfil"]
                        r["Telefono_Perfil"] = info_profunda["Telefono_Perfil"]
                    else:
                        r["Cargo_Detallado"] = "No registra"
                        r["Fecha_Fin_Cargo"] = "N/A"
                        r["Correo_Perfil"] = "N/A"
                        r["Telefono_Perfil"] = "N/A"
                    return r

                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    registros_procesados = list(executor.map(procesar_registro, registros_pagina))

                registros_departamento.extend(registros_procesados)
                offset += 10
                time.sleep(0.1)

            # Guardado incremental por ENTIDAD (Resiliencia ante caídas)
            if registros_departamento:
                df_dpto = pd.DataFrame(registros_departamento)
                columnas_ordenadas = [
                    "Departamento_Filtro", "Entidad_Filtro", "Nombre",
                    "Rol_Contrato", "Cargo_Detallado", "Fecha_Fin_Cargo",
                    "Correo_Perfil", "Telefono_Perfil", "Entidad_Asignada"
                ]
                df_dpto = df_dpto[columnas_ordenadas]
                df_dpto.drop_duplicates(inplace=True)
                
                es_nuevo = not os.path.exists(ruta_completa_csv)
                df_dpto.to_csv(ruta_completa_csv, mode='a', header=es_nuevo, index=False, encoding="utf-8-sig")
                registros_departamento = [] # Reiniciar memoria para la siguiente entidad

    # ==========================================
    # CONSOLIDACIÓN Y DESCARGA
    # ==========================================
    print("\n\n==================================================")
    print("[INFO] GENERANDO COMPRESIÓN Y ENTREGABLES...")
    print("==================================================")

    archivos_guardados = [os.path.join(CARPETA_OUTPUT, f) for f in os.listdir(CARPETA_OUTPUT) if f.endswith('.csv')]

    if archivos_guardados:
        lista_dfs = [pd.read_csv(f) for f in archivos_guardados]
        df_completo = pd.concat(lista_dfs, ignore_index=True)
        df_completo.drop_duplicates(inplace=True)

        nombre_excel = os.path.join(_ROOT, "directorio_sigep_nacional_consolidado.xlsx")
        df_completo.to_excel(nombre_excel, index=False, engine='openpyxl')

        nombre_zip = os.path.join(_ROOT, "set_datos_sigep_por_departamento.zip")
        with zipfile.ZipFile(nombre_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for archivo in archivos_guardados:
                zipf.write(archivo, os.path.basename(archivo))

        print(f"[OK] Proceso Nacional finalizado.")
        print(f"[INFO] Archivos guardados: {nombre_excel}, {nombre_zip}")
    else:
        print("[ERROR] No hay archivos parciales generados.")

if __name__ == "__main__":
    main()