from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.metricas_calidad import (
    ResultadoComparacion,
    calcular_comparacion_calidad,
    resumen_decisiones_duplicados,
    tabla_comparativa,
)
from src.validadores import cargar_csv_para_validacion


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def comparacion() -> ResultadoComparacion:
    raw = pd.read_csv(
        ROOT / "data" / "raw" / "establecimientos_raw.csv",
        dtype="string",
        keep_default_na=False,
    )
    candidato = cargar_csv_para_validacion(
        ROOT / "data" / "processed" / "establecimientos_limpios_candidato.csv"
    )
    transformaciones = pd.read_csv(
        ROOT / "data" / "processed" / "transformaciones.csv", dtype="string"
    )
    return calcular_comparacion_calidad(raw, candidato, transformaciones)


def test_dimensiones_y_faltantes_antes_despues(comparacion: ResultadoComparacion):
    assert (comparacion.antes.registros, comparacion.despues.registros) == (11891, 11868)
    assert (comparacion.antes.variables, comparacion.despues.variables) == (17, 18)
    assert (comparacion.antes.faltantes, comparacion.despues.faltantes) == (4645, 14148)
    assert (comparacion.antes.celdas, comparacion.despues.celdas) == (202147, 213624)
    assert (
        comparacion.antes.porcentaje_faltantes,
        comparacion.despues.porcentaje_faltantes,
    ) == (2.30, 6.62)
    assert comparacion.faltantes_despues_comparables == 4441
    assert comparacion.celdas_despues_comparables == 201756
    assert comparacion.porcentaje_despues_comparable == 2.20
    assert len(comparacion.antes.variables_con_na) == 17
    assert comparacion.despues.variables_con_na == (
        "DISTRITO",
        "ZONA_CAPITAL",
        "ESTABLECIMIENTO",
        "DIRECCION",
        "TELEFONO",
        "SUPERVISOR",
        "DIRECTOR",
    )


def test_duplicados_exactos_y_parciales(comparacion: ResultadoComparacion):
    assert (comparacion.antes.duplicados_exactos, comparacion.despues.duplicados_exactos) == (22, 0)
    assert (
        comparacion.antes.posibles_duplicados_pares,
        comparacion.antes.posibles_duplicados_registros,
    ) == (769, 1372)
    assert (
        comparacion.despues.posibles_duplicados_pares,
        comparacion.despues.posibles_duplicados_registros,
    ) == (781, 1386)


def test_formatos_tipos_y_categorias(comparacion: ResultadoComparacion):
    assert comparacion.antes.variables_formato_inconsistente == (
        "DISTRITO",
        "DIRECCION",
        "TELEFONO",
        "DIRECTOR",
        "DEPARTAMENTAL",
    )
    assert comparacion.despues.variables_formato_inconsistente == ()
    assert comparacion.antes.variables_tipo_incorrecto == ()
    assert comparacion.despues.variables_tipo_incorrecto == ()
    assert (comparacion.antes.categorias_inconsistentes, comparacion.despues.categorias_inconsistentes) == (16, 0)


def test_correcciones_se_reportan_por_tipo_sin_total_agregado(
    comparacion: ResultadoComparacion,
):
    assert comparacion.correcciones == {
        "Filas estructurales eliminadas": 23,
        "Distritos incompletos convertidos a NA": 70,
        "Teléfonos reformateados o invalidados": 258,
        "Valores de puntuación convertidos a NA": 9,
        "Prefijos decorativos corregidos": 1,
        "Departamentos normalizados": 2161,
        "Municipios normalizados": 2339,
        "Zonas capitalinas preservadas": 2161,
        "Valores de PLAN normalizados": 505,
        "Valores de DEPARTAMENTAL normalizados": 2026,
    }


def test_tabla_contiene_las_diez_metricas_exigidas(comparacion: ResultadoComparacion):
    tabla = tabla_comparativa(comparacion)
    assert tabla.shape == (10, 3)
    assert tabla["Métrica"].tolist() == [
        "Registros",
        "Variables",
        "Valores faltantes",
        "Variables con NA",
        "Duplicados exactos",
        "Posibles duplicados",
        "Variables con formato inconsistente",
        "Variables con tipo incorrecto",
        "Categorías inconsistentes",
        "Errores corregidos",
    ]


def test_decisiones_de_duplicados_estan_desglosadas():
    revisiones = pd.read_csv(
        ROOT / "data" / "processed" / "duplicados_revisados.csv", dtype="string"
    )
    assert resumen_decisiones_duplicados(revisiones) == {
        "conservados": 781,
        "corregidos": 0,
        "fusionados": 0,
        "eliminados": 0,
    }
