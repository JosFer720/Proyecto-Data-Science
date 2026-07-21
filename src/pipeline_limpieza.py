from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src import catalogos
from src.duplicados import aplicar_decisiones_duplicados, encontrar_duplicados_parciales
from src.limpieza_texto import (
    aplicar_mapa_categorias,
    limpiar_codigo,
    limpiar_columnas_texto,
    limpiar_distrito,
    limpiar_telefono,
    limpiar_valor_texto,
)


MAPA_MUNICIPIOS = {
    "LA TINTA": "SANTA CATALINA LA TINTA",
    "SAN MIGUEL TUCURU": "TUCURU",
    "SANTA CRUZ EL CHOL": "EL CHOL",
    "SAN PEDRO YEPOCAPA": "YEPOCAPA",
    "SAN MIGUEL POCHUTA": "POCHUTA",
    "COLOMBA COSTA CUCA": "COLOMBA",
    "GENOVA COSTA CUCA": "GENOVA",
    "SAN MIGUEL USPANTAN": "USPANTAN",
    "SANTO TOMAS CHICHICASTENANGO": "CHICHICASTENANGO",
    "PACHALUN": "PACHALUM",
    "SAN MIGUEL DUENAS": "SAN MIGUEL DUENAS",
    "SAN JOSE EL RODEO": "EL RODEO",
    "PUEBLO NUEVO": "PUEBLO NUEVO SUCHITEPEQUEZ",
    "SAN MIGUEL PANAM": "SAN MIGUEL PANAN",
    "SAN BARTOLO AGUAS CALIENTES": "SAN BARTOLO",
}

COLUMNAS_TEXTO_LIBRE = ["ESTABLECIMIENTO", "DIRECCION", "SUPERVISOR", "DIRECTOR"]
COLUMNAS_CATEGORICAS = [
    "NIVEL",
    "SECTOR",
    "AREA",
    "STATUS",
    "MODALIDAD",
    "JORNADA",
    "PLAN",
    "DEPARTAMENTAL",
]


@dataclass
class ResultadoLimpieza:
    datos: pd.DataFrame
    transformaciones: pd.DataFrame
    duplicados_revisados: pd.DataFrame


def _cantidad_cambios(antes: pd.Series, despues: pd.Series) -> int:
    izquierda = antes.astype("string").fillna("<NA>")
    derecha = despues.astype("string").fillna("<NA>")
    return int(izquierda.ne(derecha).sum())


def limpiar_establecimientos(df_raw: pd.DataFrame) -> ResultadoLimpieza:
    df = df_raw.copy()
    transformaciones: list[dict[str, object]] = []

    def registrar(
        variable: str,
        problema: str,
        transformacion: str,
        afectados: int,
        justificacion: str,
    ) -> None:
        transformaciones.append(
            {
                "Variable": variable,
                "Problema detectado": problema,
                "Transformación": transformacion,
                "Registros afectados": int(afectados),
                "Justificación": justificacion,
            }
        )

    # 1. Estandarizar ausencias y texto sin imputar información desconocida.
    for columna in df.columns:
        antes = df[columna].copy()
        df[columna] = df[columna].map(limpiar_valor_texto).astype("string")
        cambios = _cantidad_cambios(antes, df[columna])
        if cambios:
            registrar(
                columna,
                "Vacíos, marcadores de ausencia o formato textual inconsistente",
                "Convertir marcadores a NA; normalizar Unicode, espacios y mayúsculas",
                cambios,
                "Distingue ausencia real de texto y deja una representación uniforme.",
            )

    filas_vacias = df.isna().all(axis=1)
    registrar(
        "TODAS",
        "Filas separadoras completamente vacías",
        "Eliminar filas con NA en las 17 variables",
        int(filas_vacias.sum()),
        "No representan establecimientos y causaban los duplicados exactos del crudo.",
    )
    df = df.loc[~filas_vacias].reset_index(drop=True)

    # 2. Formatos de identificadores y teléfono.
    for columna, funcion, descripcion in [
        ("CODIGO", limpiar_codigo, "Validar patrón NN-NN-NNNN-NN"),
        ("DISTRITO", limpiar_distrito, "Aceptar NN-NNN o NN-NN-NNNN; lo demás pasa a NA"),
        (
            "TELEFONO",
            limpiar_telefono,
            "Extraer números completos de 8 dígitos y separarlos con ' / '; no inferir dígitos",
        ),
    ]:
        antes = df[columna].copy()
        df[columna] = df[columna].map(funcion).astype("string")
        registrar(
            columna,
            "Formato inconsistente o valor incompleto",
            descripcion,
            _cantidad_cambios(antes, df[columna]),
            "Los identificadores y teléfonos se conservan como texto para no perder ceros.",
        )

    # 3. Geografía: conservar la zona antes de llevar las filas al catálogo oficial.
    departamento_original = df["DEPARTAMENTO"].copy()
    municipio_original = df["MUNICIPIO"].copy()
    es_capital = departamento_original.eq("CIUDAD CAPITAL")
    zona_capital = municipio_original.where(
        es_capital & municipio_original.str.fullmatch(r"ZONA \d{1,2}", na=False)
    )
    df["ZONA_CAPITAL"] = zona_capital.astype("string")
    registrar(
        "ZONA_CAPITAL",
        "El buscador guarda la zona de la capital en MUNICIPIO",
        "Crear variable derivada con ZONA N antes de normalizar la geografía",
        int(zona_capital.notna().sum()),
        "Preserva información útil sin tratar una zona como municipio oficial.",
    )

    antes = df["DEPARTAMENTO"].copy()
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].map(
        lambda valor: aplicar_mapa_categorias(valor, {"CIUDAD CAPITAL": "GUATEMALA"})
    ).astype("string")
    registrar(
        "DEPARTAMENTO",
        "CIUDAD CAPITAL no es un departamento oficial",
        "Reemplazar CIUDAD CAPITAL por GUATEMALA",
        _cantidad_cambios(antes, df["DEPARTAMENTO"]),
        "Alinea la variable con los 22 departamentos oficiales.",
    )

    antes = df["MUNICIPIO"].copy()
    df["MUNICIPIO"] = df["MUNICIPIO"].map(
        lambda valor: aplicar_mapa_categorias(valor, MAPA_MUNICIPIOS)
    ).astype("string")
    df.loc[es_capital, "MUNICIPIO"] = "GUATEMALA"
    registrar(
        "MUNICIPIO",
        "Zonas capitalinas, nombres históricos/extendidos y errores tipográficos",
        "Asignar GUATEMALA a las zonas capitalinas y aplicar equivalencias documentadas",
        _cantidad_cambios(antes, df["MUNICIPIO"]),
        "Permite validar municipio-departamento sin perder la zona derivada.",
    )

    # 4. Categorías y texto libre. Las modalidades de PLAN no se fusionan.
    df = limpiar_columnas_texto(df, COLUMNAS_TEXTO_LIBRE, quitar_tildes=False)
    for columna in COLUMNAS_CATEGORICAS:
        antes = df[columna].copy()
        df[columna] = df[columna].map(
            lambda valor: limpiar_valor_texto(valor, quitar_tildes=True)
        ).astype("string")
        cambios = _cantidad_cambios(antes, df[columna])
        if cambios:
            registrar(
                columna,
                "Tildes o representación textual no uniforme",
                "Normalizar a mayúsculas sin tildes y conservar categorías semánticamente distintas",
                cambios,
                "Evita categorías duplicadas por escritura sin perder diferencias de modalidad.",
            )

    # 5. Validar dominio municipal después de las equivalencias.
    municipio_invalido = pd.Series(
        [
            pd.notna(municipio)
            and pd.notna(departamento)
            and not catalogos.es_municipio_valido(municipio, departamento)
            for municipio, departamento in zip(df["MUNICIPIO"], df["DEPARTAMENTO"])
        ],
        index=df.index,
    )
    if municipio_invalido.any():
        df.loc[municipio_invalido, "MUNICIPIO"] = pd.NA
    registrar(
        "MUNICIPIO",
        "Valores restantes fuera del catálogo oficial después de equivalencias",
        "Convertir a NA únicamente los valores sin correspondencia oficial",
        int(municipio_invalido.sum()),
        "Evita inventar municipios; los casos sin equivalencia quedan explícitamente faltantes.",
    )

    # 6. Tipos consistentes y revisión conservadora de duplicados.
    for columna in df.columns:
        df[columna] = df[columna].astype("string")

    duplicados_revisados = encontrar_duplicados_parciales(df)
    df = aplicar_decisiones_duplicados(df, duplicados_revisados)
    registrar(
        "TODAS",
        "Posibles duplicados parciales por nombre, dirección o teléfono",
        "Revisar cada par y aplicar solo decisiones explícitas",
        int(len(duplicados_revisados)),
        "No se elimina ningún candidato únicamente por similitud de cadenas.",
    )

    columnas_salida = [
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
    df = df[columnas_salida]
    transformaciones_df = pd.DataFrame(transformaciones)
    return ResultadoLimpieza(df, transformaciones_df, duplicados_revisados)
