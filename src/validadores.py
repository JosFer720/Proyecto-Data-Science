from __future__ import annotations

import re

import pandas as pd

from src import catalogos
from src.limpieza_texto import PATRON_CODIGO, PATRON_DISTRITO, PATRON_TELEFONO


COLUMNAS_REQUERIDAS = [
    "CODIGO",
    "DISTRITO",
    "DEPARTAMENTO",
    "MUNICIPIO",
    "ZONA_CAPITAL",
    "ESTABLECIMIENTO",
    "DIRECCION",
    "TELEFONO",
    "SUPERVISOR",
    "DIRECTOR",
    "NIVEL",
    "SECTOR",
    "AREA",
    "STATUS",
    "MODALIDAD",
    "JORNADA",
    "PLAN",
    "DEPARTAMENTAL",
]

COLUMNAS_TEXTO_LIBRE = ["ESTABLECIMIENTO", "DIRECCION", "SUPERVISOR", "DIRECTOR"]


def es_codigo_valido(valor: object) -> bool:
    return pd.isna(valor) or bool(PATRON_CODIGO.fullmatch(str(valor)))


def es_distrito_valido(valor: object) -> bool:
    return pd.isna(valor) or bool(PATRON_DISTRITO.fullmatch(str(valor)))


def es_telefono_valido(valor: object) -> bool:
    if pd.isna(valor):
        return True
    telefonos = str(valor).split(" / ")
    return bool(telefonos) and all(PATRON_TELEFONO.fullmatch(tel) for tel in telefonos)


def tiene_espacios_extra(valor: object) -> bool:
    if pd.isna(valor):
        return False
    texto = str(valor)
    return texto != texto.strip() or bool(re.search(r"\s{2,}", texto))


def es_texto_residual_invalido(valor: object) -> bool:
    if pd.isna(valor):
        return False
    texto = str(valor).strip()
    return bool(re.fullmatch(r"[\W_]+", texto)) or bool(
        re.match(r"^-{2,}\s*\w", texto)
    )


def es_departamental_consistente(departamento: object, departamental: object) -> bool:
    if pd.isna(departamento) or pd.isna(departamental):
        return True
    depto = catalogos.normalizar_nombre_geografico(str(departamento))
    direccion = catalogos.normalizar_nombre_geografico(str(departamental))
    return direccion == depto or direccion.startswith(f"{depto} ")


def contar_errores_calidad(df: pd.DataFrame) -> dict[str, int]:
    columnas_texto = list(df.select_dtypes(include=["object", "string"]).columns)
    errores_espacios = sum(
        int(df[columna].map(tiene_espacios_extra).sum()) for columna in columnas_texto
    )
    errores_texto_residual = sum(
        int(df[columna].map(es_texto_residual_invalido).sum())
        for columna in COLUMNAS_TEXTO_LIBRE
        if columna in df
    )
    return {
        "duplicados_exactos": int(df.duplicated().sum()),
        "espacios_extra": errores_espacios,
        "textos_residuales_invalidos": errores_texto_residual,
        "telefonos_invalidos": int((~df["TELEFONO"].map(es_telefono_valido)).sum()),
        "codigos_invalidos": int((~df["CODIGO"].map(es_codigo_valido)).sum()),
        "distritos_invalidos": int((~df["DISTRITO"].map(es_distrito_valido)).sum()),
        "departamentos_invalidos": int(
            (
                df["DEPARTAMENTO"].notna()
                & ~df["DEPARTAMENTO"].map(catalogos.es_departamento_valido)
            ).sum()
        ),
        "municipios_invalidos": int(
            sum(
                not catalogos.es_municipio_valido(municipio, departamento)
                for municipio, departamento in zip(df["MUNICIPIO"], df["DEPARTAMENTO"])
                if pd.notna(municipio) and pd.notna(departamento)
            )
        ),
        "relaciones_departamentales_invalidas": int(
            sum(
                not es_departamental_consistente(departamento, departamental)
                for departamento, departamental in zip(
                    df["DEPARTAMENTO"], df["DEPARTAMENTAL"]
                )
            )
        ),
        "columnas_requeridas_ausentes": int(
            len(set(COLUMNAS_REQUERIDAS) - set(df.columns))
        ),
    }
