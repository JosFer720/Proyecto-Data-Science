from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src import catalogos
from src.diagnostico import SENTINELAS_FALTANTES, mascara_faltantes
from src.duplicados import encontrar_duplicados_parciales
from src.limpieza_texto import es_valor_faltante, normalizar_texto
from src.pipeline_limpieza import MAPA_MUNICIPIOS
from src.validadores import (
    COLUMNAS_REQUERIDAS,
    es_departamental_consistente,
    es_distrito_valido,
    es_telefono_valido,
    es_texto_residual_invalido,
)


@dataclass(frozen=True)
class MetricasCalidad:
    registros: int
    variables: int
    faltantes: int
    celdas: int
    porcentaje_faltantes: float
    variables_con_na: tuple[str, ...]
    duplicados_exactos: int
    posibles_duplicados_pares: int
    posibles_duplicados_registros: int
    variables_formato_inconsistente: tuple[str, ...]
    variables_tipo_incorrecto: tuple[str, ...]
    categorias_inconsistentes: int


@dataclass(frozen=True)
class ResultadoComparacion:
    antes: MetricasCalidad
    despues: MetricasCalidad
    faltantes_despues_comparables: int
    celdas_despues_comparables: int
    porcentaje_despues_comparable: float
    correcciones: dict[str, int]


def _filas_reales(df: pd.DataFrame) -> pd.DataFrame:
    filas_vacias = df.apply(mascara_faltantes).all(axis=1)
    return df.loc[~filas_vacias].reset_index(drop=True)


def _resumen_faltantes(df: pd.DataFrame) -> tuple[int, int, float, tuple[str, ...]]:
    conteos = {columna: int(mascara_faltantes(df[columna]).sum()) for columna in df}
    faltantes = sum(conteos.values())
    celdas = int(df.shape[0] * df.shape[1])
    variables = tuple(columna for columna, total in conteos.items() if total > 0)
    porcentaje = round(faltantes / celdas * 100, 2) if celdas else 0.0
    return faltantes, celdas, porcentaje, variables


def _variables_formato_inconsistente(df: pd.DataFrame) -> tuple[str, ...]:
    reales = _filas_reales(df)
    problemas = []

    if "DISTRITO" in reales and (~reales["DISTRITO"].map(es_distrito_valido)).any():
        problemas.append("DISTRITO")

    if "DIRECCION" in reales:
        direccion_invalida = reales["DIRECCION"].map(
            lambda valor: pd.notna(valor)
            and (es_valor_faltante(valor) or es_texto_residual_invalido(valor))
        )
        if direccion_invalida.any():
            problemas.append("DIRECCION")

    if "TELEFONO" in reales:
        telefono_no_faltante = ~mascara_faltantes(reales["TELEFONO"])
        if (telefono_no_faltante & ~reales["TELEFONO"].map(es_telefono_valido)).any():
            problemas.append("TELEFONO")

    if "DIRECTOR" in reales:
        director_invalido = reales["DIRECTOR"].map(
            lambda valor: pd.notna(valor)
            and (es_valor_faltante(valor) or es_texto_residual_invalido(valor))
        )
        prefijo_decorativo = reales["DIRECTOR"].fillna("").str.match(
            r"^-{2,}\s*\w", na=False
        )
        if (director_invalido | prefijo_decorativo).any():
            problemas.append("DIRECTOR")

    if "DEPARTAMENTAL" in reales:
        departamental_no_canonica = reales["DEPARTAMENTAL"].dropna().map(
            lambda valor: normalizar_texto(valor) != normalizar_texto(valor, quitar_tildes=True)
        )
        if departamental_no_canonica.any():
            problemas.append("DEPARTAMENTAL")

    return tuple(problemas)


def _variables_tipo_incorrecto(df: pd.DataFrame) -> tuple[str, ...]:
    return tuple(
        columna
        for columna in df.columns
        if not isinstance(df[columna].dtype, pd.StringDtype)
    )


def _categorias_inconsistentes(df: pd.DataFrame, *, estado_crudo: bool) -> int:
    total = 0
    if "DEPARTAMENTO" in df:
        departamentos = {
            normalizar_texto(valor)
            for valor in df["DEPARTAMENTO"].dropna().unique()
        }
        total += int("CIUDAD CAPITAL" in departamentos)

    if "MUNICIPIO" in df and estado_crudo:
        observados = {
            normalizar_texto(valor, quitar_tildes=True)
            for valor in df["MUNICIPIO"].dropna().unique()
        }
        total += len(observados & set(MAPA_MUNICIPIOS))
    return total


def _metricas(df: pd.DataFrame, *, estado_crudo: bool) -> MetricasCalidad:
    faltantes, celdas, porcentaje, variables_na = _resumen_faltantes(df)
    reales = _filas_reales(df)
    pares = encontrar_duplicados_parciales(reales)
    registros = set(pares["indice_1"]) | set(pares["indice_2"])
    return MetricasCalidad(
        registros=int(df.shape[0]),
        variables=int(df.shape[1]),
        faltantes=faltantes,
        celdas=celdas,
        porcentaje_faltantes=porcentaje,
        variables_con_na=variables_na,
        duplicados_exactos=int(df.duplicated().sum()),
        posibles_duplicados_pares=int(len(pares)),
        posibles_duplicados_registros=int(len(registros)),
        variables_formato_inconsistente=_variables_formato_inconsistente(df),
        variables_tipo_incorrecto=_variables_tipo_incorrecto(df),
        categorias_inconsistentes=_categorias_inconsistentes(
            df, estado_crudo=estado_crudo
        ),
    )


def _afectados(
    transformaciones: pd.DataFrame,
    variable: str,
    problema_contiene: str,
) -> int:
    mascara = transformaciones["Variable"].eq(variable) & transformaciones[
        "Problema detectado"
    ].str.contains(problema_contiene, case=False, regex=False, na=False)
    valores = pd.to_numeric(
        transformaciones.loc[mascara, "Registros afectados"], errors="coerce"
    ).fillna(0)
    return int(valores.sum())


def _puntuacion_convertida_a_na(raw: pd.DataFrame) -> int:
    reales = _filas_reales(raw)
    total = 0
    for columna in ["DIRECCION", "SUPERVISOR", "DIRECTOR"]:
        normalizada = reales[columna].fillna("").map(normalizar_texto)
        solo_puntuacion = normalizada.str.fullmatch(r"[\W_]+", na=False)
        marcador_previamente_reconocido = normalizada.isin(
            SENTINELAS_FALTANTES
        ) | normalizada.str.fullmatch(r"-+", na=False)
        total += int((solo_puntuacion & ~marcador_previamente_reconocido).sum())
    return total


def _resumen_correcciones(
    raw: pd.DataFrame, transformaciones: pd.DataFrame
) -> dict[str, int]:
    return {
        "Filas estructurales eliminadas": _afectados(
            transformaciones, "TODAS", "Filas separadoras"
        ),
        "Distritos incompletos convertidos a NA": _afectados(
            transformaciones, "DISTRITO", "Formato inconsistente"
        ),
        "Teléfonos reformateados o invalidados": _afectados(
            transformaciones, "TELEFONO", "Formato inconsistente"
        ),
        "Valores de puntuación convertidos a NA": _puntuacion_convertida_a_na(raw),
        "Prefijos decorativos corregidos": _afectados(
            transformaciones, "DIRECTOR", "Puntuación decorativa"
        ),
        "Departamentos normalizados": _afectados(
            transformaciones, "DEPARTAMENTO", "CIUDAD CAPITAL"
        ),
        "Municipios normalizados": _afectados(
            transformaciones, "MUNICIPIO", "Zonas capitalinas"
        ),
        "Zonas capitalinas preservadas": _afectados(
            transformaciones, "ZONA_CAPITAL", "zona de la capital"
        ),
        "Valores de PLAN normalizados": _afectados(
            transformaciones, "PLAN", "Tildes"
        ),
        "Valores de DEPARTAMENTAL normalizados": _afectados(
            transformaciones, "DEPARTAMENTAL", "Tildes"
        ),
    }


def calcular_comparacion_calidad(
    raw: pd.DataFrame,
    candidato: pd.DataFrame,
    transformaciones: pd.DataFrame,
) -> ResultadoComparacion:
    antes = _metricas(raw, estado_crudo=True)
    despues = _metricas(candidato, estado_crudo=False)
    columnas_originales = [col for col in COLUMNAS_REQUERIDAS if col != "ZONA_CAPITAL"]
    comparable = candidato[columnas_originales]
    faltantes, celdas, porcentaje, _ = _resumen_faltantes(comparable)
    return ResultadoComparacion(
        antes=antes,
        despues=despues,
        faltantes_despues_comparables=faltantes,
        celdas_despues_comparables=celdas,
        porcentaje_despues_comparable=porcentaje,
        correcciones=_resumen_correcciones(raw, transformaciones),
    )


def resumen_decisiones_duplicados(revisiones: pd.DataFrame) -> dict[str, int]:
    decisiones = revisiones["decision"].astype("string").str.upper().value_counts()
    return {
        "conservados": int(decisiones.get("CONSERVAR", 0)),
        "corregidos": int(decisiones.get("CORREGIR", 0)),
        "fusionados": int(decisiones.get("FUSIONAR", 0)),
        "eliminados": int(decisiones.get("ELIMINAR", 0)),
    }


def _lista_variables(valores: tuple[str, ...]) -> str:
    return ", ".join(valores) if valores else "Ninguna"


def _resumen_correcciones_texto(correcciones: dict[str, int]) -> str:
    return "; ".join(f"{nombre}: {total:,}" for nombre, total in correcciones.items())


def tabla_comparativa(resultado: ResultadoComparacion) -> pd.DataFrame:
    antes, despues = resultado.antes, resultado.despues
    filas = [
        ("Registros", f"{antes.registros:,}", f"{despues.registros:,}"),
        ("Variables", str(antes.variables), str(despues.variables)),
        (
            "Valores faltantes",
            f"{antes.faltantes:,} de {antes.celdas:,} ({antes.porcentaje_faltantes:.2f} %)",
            f"{despues.faltantes:,} de {despues.celdas:,} ({despues.porcentaje_faltantes:.2f} %)",
        ),
        (
            "Variables con NA",
            f"{len(antes.variables_con_na)} ({_lista_variables(antes.variables_con_na)})",
            f"{len(despues.variables_con_na)} ({_lista_variables(despues.variables_con_na)})",
        ),
        ("Duplicados exactos", str(antes.duplicados_exactos), str(despues.duplicados_exactos)),
        (
            "Posibles duplicados",
            f"{antes.posibles_duplicados_pares:,} pares / {antes.posibles_duplicados_registros:,} registros",
            f"{despues.posibles_duplicados_pares:,} pares / {despues.posibles_duplicados_registros:,} registros",
        ),
        (
            "Variables con formato inconsistente",
            f"{len(antes.variables_formato_inconsistente)} ({_lista_variables(antes.variables_formato_inconsistente)})",
            f"{len(despues.variables_formato_inconsistente)} ({_lista_variables(despues.variables_formato_inconsistente)})",
        ),
        (
            "Variables con tipo incorrecto",
            f"{len(antes.variables_tipo_incorrecto)} ({_lista_variables(antes.variables_tipo_incorrecto)})",
            f"{len(despues.variables_tipo_incorrecto)} ({_lista_variables(despues.variables_tipo_incorrecto)})",
        ),
        (
            "Categorías inconsistentes",
            str(antes.categorias_inconsistentes),
            str(despues.categorias_inconsistentes),
        ),
        (
            "Errores corregidos",
            "0 (estado previo)",
            _resumen_correcciones_texto(resultado.correcciones),
        ),
    ]
    return pd.DataFrame(filas, columns=["Métrica", "Antes", "Después (candidato)"])
