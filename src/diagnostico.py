from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

import pandas as pd


SENTINELAS_FALTANTES = frozenset(
    {
        "",
        "-",
        ".",
        "--",
        "---",
        "N/A",
        "NA",
        "NAN",
        "NULL",
        "NONE",
        "SIN DATO",
        "SIN DATOS",
        "SIN INFORMACION",
        "SIN INFORMACIÓN",
        "NO DISPONIBLE",
    }
)


TIPOS_ESPERADOS_CRUDO = {
    "CODIGO": "texto identificador",
    "DISTRITO": "texto identificador",
    "DEPARTAMENTO": "texto categórico",
    "MUNICIPIO": "texto categórico",
    "ESTABLECIMIENTO": "texto",
    "DIRECCION": "texto",
    "TELEFONO": "texto identificador",
    "SUPERVISOR": "texto",
    "DIRECTOR": "texto",
    "NIVEL": "texto categórico",
    "SECTOR": "texto categórico",
    "AREA": "texto categórico",
    "STATUS": "texto categórico",
    "MODALIDAD": "texto categórico",
    "JORNADA": "texto categórico",
    "PLAN": "texto categórico",
    "DEPARTAMENTAL": "texto categórico",
}


def _normalizar_para_comparar(valor: object) -> str:
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKC", str(valor)).strip().upper()
    return re.sub(r"\s+", " ", texto)


# Identifica NA, vacíos y centinelas que representan datos ausentes.
def mascara_faltantes(serie: pd.Series) -> pd.Series:
    normalizada = serie.map(_normalizar_para_comparar)
    solo_guiones = normalizada.str.fullmatch(r"-+", na=False)
    return serie.isna() | normalizada.isin(SENTINELAS_FALTANTES) | solo_guiones


def resumen_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    conteo = pd.Series(
        {columna: int(mascara_faltantes(df[columna]).sum()) for columna in df.columns},
        name="faltantes",
    )
    porcentaje = (conteo / len(df) * 100).round(2)
    return pd.DataFrame({"faltantes": conteo, "porcentaje": porcentaje}).sort_values(
        "faltantes", ascending=False
    )


def resumen_faltantes_total(df: pd.DataFrame) -> pd.Series:
    total = int(sum(mascara_faltantes(df[columna]).sum() for columna in df.columns))
    celdas = int(df.shape[0] * df.shape[1])
    return pd.Series(
        {
            "celdas_faltantes": total,
            "celdas_totales": celdas,
            "porcentaje": round(total / celdas * 100, 2) if celdas else 0.0,
            "variables_con_faltantes": int(
                sum(mascara_faltantes(df[columna]).any() for columna in df.columns)
            ),
        }
    )


def resumen_tipos(
    df: pd.DataFrame,
    tipos_esperados: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    esperados = tipos_esperados or TIPOS_ESPERADOS_CRUDO
    return pd.DataFrame(
        {
            "tipo_observado": [str(tipo) for tipo in df.dtypes],
            "tipo_esperado": [esperados.get(columna, "no definido") for columna in df.columns],
        },
        index=pd.Index(df.columns, name="columna"),
    )


def contar_unicos(df: pd.DataFrame) -> pd.Series:
    conteos = {}
    for columna in df.columns:
        serie = df[columna].mask(mascara_faltantes(df[columna]))
        conteos[columna] = int(serie.nunique(dropna=True))
    return pd.Series(conteos, name="valores_unicos")


def contar_duplicados_exactos(df: pd.DataFrame) -> int:
    return int(df.duplicated().sum())


# Cuenta espacios, caracteres invisibles y minúsculas en las columnas textuales.
def resumen_formato_texto(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for columna in df.columns:
        serie = df[columna].astype("string")
        no_faltante = ~mascara_faltantes(serie)
        valores = serie.fillna("")
        filas.append(
            {
                "variable": columna,
                "espacios_extremos": int((no_faltante & valores.ne(valores.str.strip())).sum()),
                "espacios_multiples": int(
                    (no_faltante & valores.str.contains(r"\s{2,}", regex=True, na=False)).sum()
                ),
                "caracteres_invisibles": int(
                    (
                        no_faltante
                        & valores.map(
                            lambda valor: any(
                                unicodedata.category(caracter) in {"Cc", "Cf"}
                                for caracter in valor
                            )
                        )
                    ).sum()
                ),
                "contiene_minusculas": int(
                    (no_faltante & valores.str.contains(r"[a-záéíóúüñ]", regex=True, na=False)).sum()
                ),
            }
        )
    return pd.DataFrame(filas).set_index("variable")


def resumen_patrones_identificadores(df: pd.DataFrame) -> pd.DataFrame:
    codigo = df["CODIGO"].astype("string")
    distrito = df["DISTRITO"].astype("string")
    return pd.DataFrame(
        [
            {
                "variable": "CODIGO",
                "patron": "NN-NN-NNNN-NN",
                "validos": int(codigo.str.fullmatch(r"\d{2}-\d{2}-\d{4}-\d{2}", na=False).sum()),
                "invalidos_no_faltantes": int(
                    (
                        ~mascara_faltantes(codigo)
                        & ~codigo.str.fullmatch(r"\d{2}-\d{2}-\d{4}-\d{2}", na=False)
                    ).sum()
                ),
            },
            {
                "variable": "DISTRITO",
                "patron": "NN-NNN o NN-NN-NNNN",
                "validos": int(
                    distrito.str.fullmatch(r"(?:\d{2}-\d{3}|\d{2}-\d{2}-\d{4})", na=False).sum()
                ),
                "invalidos_no_faltantes": int(
                    (
                        ~mascara_faltantes(distrito)
                        & ~distrito.str.fullmatch(
                            r"(?:\d{2}-\d{3}|\d{2}-\d{2}-\d{4})", na=False
                        )
                    ).sum()
                ),
            },
        ]
    ).set_index("variable")
