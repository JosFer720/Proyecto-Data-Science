from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

import pandas as pd
from unidecode import unidecode

from src.diagnostico import SENTINELAS_FALTANTES


PATRON_CODIGO = re.compile(r"^\d{2}-\d{2}-\d{4}-\d{2}$")
PATRON_DISTRITO = re.compile(r"^(?:\d{2}-\d{3}|\d{2}-\d{2}-\d{4})$")
PATRON_TELEFONO = re.compile(r"^[2-7]\d{7}$")


def es_valor_faltante(valor: object) -> bool:
    if valor is None or pd.isna(valor):
        return True
    texto = normalizar_texto(valor, mayusculas=True, quitar_tildes=False)
    return texto in SENTINELAS_FALTANTES or not any(
        caracter.isalnum() for caracter in texto
    )


# Normaliza Unicode, espacios, mayúsculas y tildes según la configuración.
def normalizar_texto(
    valor: object,
    *,
    mayusculas: bool = True,
    quitar_tildes: bool = False,
) -> str:
    if valor is None or pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKC", str(valor))
    texto = re.sub(r"[\u200B-\u200D\uFEFF]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    if mayusculas:
        texto = texto.upper()
    if quitar_tildes:
        texto = unidecode(texto)
    return texto


def limpiar_valor_texto(valor: object, *, quitar_tildes: bool = False) -> object:
    if es_valor_faltante(valor):
        return pd.NA
    texto = normalizar_texto(valor, quitar_tildes=quitar_tildes)
    return texto if texto else pd.NA


def limpiar_prefijo_decorativo(valor: object) -> object:
    limpio = limpiar_valor_texto(valor)
    if pd.isna(limpio):
        return pd.NA
    texto = re.sub(r"^-{2,}\s*(?=\w)", "", str(limpio))
    return texto if texto else pd.NA


def limpiar_codigo(valor: object) -> object:
    if es_valor_faltante(valor):
        return pd.NA
    texto = normalizar_texto(valor).replace(" ", "")
    return texto if PATRON_CODIGO.fullmatch(texto) else pd.NA


def limpiar_distrito(valor: object) -> object:
    if es_valor_faltante(valor):
        return pd.NA
    texto = normalizar_texto(valor).replace(" ", "")
    return texto if PATRON_DISTRITO.fullmatch(texto) else pd.NA


# Extrae teléfonos guatemaltecos completos sin inventar dígitos faltantes.
def extraer_telefonos_validos(valor: object) -> list[str]:
    if es_valor_faltante(valor):
        return []
    texto = normalizar_texto(valor)
    candidatos = re.findall(r"(?<!\d)(\d{8})(?!\d)", texto)
    validos = []
    for telefono in candidatos:
        if PATRON_TELEFONO.fullmatch(telefono) and telefono not in validos:
            validos.append(telefono)
    return validos


def limpiar_telefono(valor: object) -> object:
    telefonos = extraer_telefonos_validos(valor)
    return " / ".join(telefonos) if telefonos else pd.NA


def aplicar_mapa_categorias(
    valor: object,
    mapa: Mapping[str, str],
) -> object:
    limpio = limpiar_valor_texto(valor, quitar_tildes=True)
    if pd.isna(limpio):
        return pd.NA
    return mapa.get(str(limpio), str(limpio))


def limpiar_columnas_texto(
    df: pd.DataFrame,
    columnas: list[str],
    *,
    quitar_tildes: bool = False,
) -> pd.DataFrame:
    resultado = df.copy()
    for columna in columnas:
        resultado[columna] = resultado[columna].map(
            lambda valor: limpiar_valor_texto(valor, quitar_tildes=quitar_tildes)
        ).astype("string")
    return resultado
