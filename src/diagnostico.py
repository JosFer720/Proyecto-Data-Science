from __future__ import annotations

import pandas as pd


def resumen_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    faltantes = {}
    for col in df.columns:
        serie = df[col]
        es_na = serie.isna()
        if serie.dtype == object:
            es_na = es_na | serie.fillna("").astype(str).str.strip().eq("")
        faltantes[col] = int(es_na.sum())

    conteo = pd.Series(faltantes, name="faltantes")
    porcentaje = (conteo / len(df) * 100).round(2)
    return pd.DataFrame({"faltantes": conteo, "porcentaje": porcentaje}).sort_values(
        "faltantes", ascending=False
    )


def resumen_tipos(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"columna": df.columns, "tipo": [str(t) for t in df.dtypes]}).set_index("columna")


def contar_unicos(df: pd.DataFrame) -> pd.Series:
    return df.nunique(dropna=True).rename("valores_unicos")


def contar_duplicados_exactos(df: pd.DataFrame) -> int:
    return int(df.duplicated().sum())
