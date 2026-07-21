from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import requests

URL_BUSCADOR = "https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/"

CODIGOS_DEPARTAMENTO_MINEDUC = {
    "ALTA VERAPAZ": "16",
    "BAJA VERAPAZ": "15",
    "CHIMALTENANGO": "04",
    "CHIQUIMULA": "20",
    "CIUDAD CAPITAL": "00",
    "EL PROGRESO": "02",
    "ESCUINTLA": "05",
    "GUATEMALA": "01",
    "HUEHUETENANGO": "13",
    "IZABAL": "18",
    "JALAPA": "21",
    "JUTIAPA": "22",
    "PETEN": "17",
    "QUETZALTENANGO": "09",
    "QUICHE": "14",
    "RETALHULEU": "11",
    "SACATEPEQUEZ": "03",
    "SAN MARCOS": "12",
    "SANTA ROSA": "06",
    "SOLOLA": "07",
    "SUCHITEPEQUEZ": "10",
    "TOTONICAPAN": "08",
    "ZACAPA": "19",
}

CODIGOS_NIVEL_MINEDUC = {
    "BASICO": "45",
    "DIVERSIFICADO": "46",
    "PARVULOS": "42",
    "PREPRIMARIA BILINGUE": "41",
    "PRIMARIA": "43",
    "PRIMARIA DE ADULTOS": "44",
}


def _extraer_campo_oculto(html: str, campo: str) -> str:
    import re

    m = re.search(rf'id="{campo}" value="([^"]*)"', html)
    return m.group(1) if m else ""


def descargar_departamento(
    nombre_departamento: str,
    nivel: str = "DIVERSIFICADO",
    session: requests.Session | None = None,
) -> pd.DataFrame:
    nombre_departamento = nombre_departamento.strip().upper()
    if nombre_departamento not in CODIGOS_DEPARTAMENTO_MINEDUC:
        raise ValueError(f"Departamento desconocido para el buscador MINEDUC: {nombre_departamento!r}")
    nivel = nivel.strip().upper()
    if nivel not in CODIGOS_NIVEL_MINEDUC:
        raise ValueError(f"Nivel desconocido para el buscador MINEDUC: {nivel!r}")

    s = session or requests.Session()
    s.headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    )

    r = s.get(URL_BUSCADOR, timeout=20)
    r.raise_for_status()
    html = r.text

    data = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": _extraer_campo_oculto(html, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _extraer_campo_oculto(html, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _extraer_campo_oculto(html, "__EVENTVALIDATION"),
        "_ctl0:ContentPlaceHolder1:cmbDepartamento": CODIGOS_DEPARTAMENTO_MINEDUC[nombre_departamento],
        "_ctl0:ContentPlaceHolder1:cmbMunicipio": "SELECCIONE UNO",
        "_ctl0:ContentPlaceHolder1:cmbNivel": CODIGOS_NIVEL_MINEDUC[nivel],
        "_ctl0:ContentPlaceHolder1:cmbSector": "SELECCIONE UNO",
        "_ctl0:ContentPlaceHolder1:txtCodEstab": "",
        "_ctl0:ContentPlaceHolder1:txtNomEstab": "",
        "_ctl0:ContentPlaceHolder1:txtDirecEstab": "",
        "_ctl0:ContentPlaceHolder1:IbtnConsultar.x": "10",
        "_ctl0:ContentPlaceHolder1:IbtnConsultar.y": "10",
    }
    r2 = s.post(URL_BUSCADOR, data=data, timeout=30)
    r2.raise_for_status()

    tablas = pd.read_html(r2.text, attrs={"id": "_ctl0_ContentPlaceHolder1_grvHistorial"})
    if not tablas:
        raise RuntimeError(
            f"El buscador MINEDUC no devolvió resultados para {nombre_departamento}/{nivel}."
        )
    return tablas[0]


# Une archivos crudos que comparten el mismo esquema sin modificar sus valores.
# Las filas vacías se conservan por defecto para reproducir fielmente la fuente;
# su eliminación corresponde a la etapa posterior de limpieza.
def unir_csvs(
    lista_paths: list[str | Path],
    *,
    eliminar_filas_totalmente_vacias: bool = False,
) -> pd.DataFrame:
    if not lista_paths:
        raise ValueError("lista_paths no puede estar vacía")

    dfs = [pd.read_csv(p, dtype="string", keep_default_na=False) for p in lista_paths]

    columnas_base = list(dfs[0].columns)
    for path, df in zip(lista_paths, dfs):
        if list(df.columns) != columnas_base:
            raise ValueError(f"{path} tiene columnas distintas a las del primer archivo: {list(df.columns)}")

    unido = pd.concat(dfs, ignore_index=True)
    if eliminar_filas_totalmente_vacias:
        unido = unido.dropna(how="all")
    return unido.reset_index(drop=True)


def sha256_archivo(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


# Registra la cobertura, fecha y huella SHA-256 del CSV crudo consolidado.
def crear_manifiesto_consolidado(
    path_csv: str | Path,
    fecha_extraccion: str,
) -> pd.DataFrame:
    path = Path(path_csv)
    df = pd.read_csv(path, dtype="string")
    huella = sha256_archivo(path)
    conteos = (
        df.dropna(subset=["DEPARTAMENTO"])
        .groupby("DEPARTAMENTO", dropna=False)
        .size()
        .rename("registros")
        .reset_index()
        .rename(columns={"DEPARTAMENTO": "consulta_departamento"})
    )
    conteos["nivel"] = "DIVERSIFICADO"
    conteos["fecha_extraccion"] = fecha_extraccion
    conteos["archivo_consolidado"] = path.name
    conteos["sha256_consolidado"] = huella
    return conteos[
        [
            "consulta_departamento",
            "nivel",
            "registros",
            "fecha_extraccion",
            "archivo_consolidado",
            "sha256_consolidado",
        ]
    ]
