from __future__ import annotations

from itertools import combinations

import pandas as pd
from rapidfuzz import fuzz
from unidecode import unidecode

from src.limpieza_texto import normalizar_texto


COLUMNAS_UNIDAD_REGISTRAL = [
    "DEPARTAMENTO",
    "MUNICIPIO",
    "NIVEL",
    "SECTOR",
    "AREA",
    "STATUS",
    "MODALIDAD",
    "JORNADA",
    "PLAN",
    "DEPARTAMENTAL",
]


def _clave_similitud(valor: object) -> str:
    return unidecode(normalizar_texto(valor)).replace(".", "").replace(",", "")


def _valores_iguales(izquierda: object, derecha: object) -> bool:
    if pd.isna(izquierda):
        return bool(pd.isna(derecha))
    if pd.isna(derecha):
        return False
    return bool(izquierda == derecha)


def _pares_por_bloque(indices: list[int], limite_bloque: int = 80):
    if 1 < len(indices) <= limite_bloque:
        yield from combinations(indices, 2)


# Genera candidatos similares sin eliminar registros automáticamente.
# El bloqueo geográfico y por nombre reduce comparaciones innecesarias;
# también considera coincidencias de teléfono y dirección.
def encontrar_duplicados_parciales(
    df: pd.DataFrame,
    *,
    threshold_nombre: int = 94,
    threshold_direccion: int = 85,
) -> pd.DataFrame:
    trabajo = df.reset_index(drop=False).rename(columns={"index": "indice_original"}).copy()
    trabajo["_nombre"] = trabajo["ESTABLECIMIENTO"].map(_clave_similitud)
    trabajo["_direccion"] = trabajo["DIRECCION"].map(_clave_similitud)
    trabajo["_telefono"] = trabajo["TELEFONO"].fillna("").astype(str)
    trabajo["_bloque"] = (
        trabajo["DEPARTAMENTO"].fillna("").astype(str)
        + "|"
        + trabajo["MUNICIPIO"].fillna("").astype(str)
        + "|"
        + trabajo["_nombre"].str[:18]
    )

    pares: set[tuple[int, int]] = set()
    for _, grupo in trabajo.groupby("_bloque", sort=False):
        pares.update(_pares_por_bloque(grupo.index.tolist()))

    telefonos = trabajo[trabajo["_telefono"].ne("")].groupby(
        ["DEPARTAMENTO", "MUNICIPIO", "_telefono"], sort=False, dropna=False
    )
    for _, grupo in telefonos:
        pares.update(_pares_por_bloque(grupo.index.tolist(), limite_bloque=40))

    resultados = []
    for i, j in sorted(pares):
        fila_i = trabajo.loc[i]
        fila_j = trabajo.loc[j]
        nombre = fuzz.token_set_ratio(fila_i["_nombre"], fila_j["_nombre"])
        direccion = fuzz.token_set_ratio(fila_i["_direccion"], fila_j["_direccion"])
        mismo_telefono = bool(
            fila_i["_telefono"] and fila_i["_telefono"] == fila_j["_telefono"]
        )
        misma_direccion = bool(
            fila_i["_direccion"] and fila_i["_direccion"] == fila_j["_direccion"]
        )
        misma_unidad_registral = all(
            _valores_iguales(fila_i[columna], fila_j[columna])
            for columna in COLUMNAS_UNIDAD_REGISTRAL
        )
        es_candidato = (
            misma_unidad_registral
            and
            nombre >= threshold_nombre
            and (direccion >= threshold_direccion or mismo_telefono or misma_direccion)
        )
        if not es_candidato:
            continue

        columnas_comparadas = [
            "DISTRITO",
            "ESTABLECIMIENTO",
            "DIRECCION",
            "TELEFONO",
            "SUPERVISOR",
            "DIRECTOR",
            *COLUMNAS_UNIDAD_REGISTRAL,
        ]
        campos_diferentes = [
            columna
            for columna in columnas_comparadas
            if not _valores_iguales(fila_i[columna], fila_j[columna])
        ]
        decision = "CONSERVAR"
        justificacion = (
            "Los códigos MINEDUC son distintos y funcionan como identificadores oficiales; "
            "se conservan como unidades registrales separadas. La similitud quedó revisada, "
            "pero no justifica una fusión sin confirmación expresa de la fuente."
        )
        resultados.append(
            {
                "indice_1": int(fila_i["indice_original"]),
                "indice_2": int(fila_j["indice_original"]),
                "codigo_1": fila_i["CODIGO"],
                "codigo_2": fila_j["CODIGO"],
                "establecimiento_1": fila_i["ESTABLECIMIENTO"],
                "establecimiento_2": fila_j["ESTABLECIMIENTO"],
                "direccion_1": fila_i["DIRECCION"],
                "direccion_2": fila_j["DIRECCION"],
                "telefono_1": fila_i["TELEFONO"],
                "telefono_2": fila_j["TELEFONO"],
                "similitud_nombre": round(float(nombre), 2),
                "similitud_direccion": round(float(direccion), 2),
                "telefono_igual": mismo_telefono,
                "campos_diferentes": ", ".join(campos_diferentes) or "NINGUNO",
                "decision": decision,
                "justificacion": justificacion,
            }
        )

    columnas = [
        "indice_1",
        "indice_2",
        "codigo_1",
        "codigo_2",
        "establecimiento_1",
        "establecimiento_2",
        "direccion_1",
        "direccion_2",
        "telefono_1",
        "telefono_2",
        "similitud_nombre",
        "similitud_direccion",
        "telefono_igual",
        "campos_diferentes",
        "decision",
        "justificacion",
    ]
    return pd.DataFrame(resultados, columns=columnas)


# Elimina solamente los registros marcados explícitamente como ELIMINAR.
def aplicar_decisiones_duplicados(
    df: pd.DataFrame,
    revisiones: pd.DataFrame,
) -> pd.DataFrame:
    if revisiones.empty or "decision" not in revisiones:
        return df.copy()
    aprobadas = revisiones[revisiones["decision"].eq("ELIMINAR")]
    indices = set(aprobadas["indice_2"].astype(int).tolist())
    return df.drop(index=indices, errors="ignore").reset_index(drop=True)
