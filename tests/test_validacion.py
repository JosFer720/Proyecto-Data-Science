from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.validadores import cargar_csv_para_validacion, ejecutar_validaciones


ROOT = Path(__file__).resolve().parents[1]
RUTA_CANDIDATO = ROOT / "data" / "processed" / "establecimientos_limpios_candidato.csv"

NOMBRES_PRUEBAS = [
    "Duplicados exactos",
    "Espacios en textos",
    "Formato de teléfonos",
    "Geografía oficial",
    "Esquema y tipos",
    "Categorías equivalentes",
    "Valores inválidos diagnosticados",
]


@pytest.fixture(scope="module")
def candidato() -> pd.DataFrame:
    return cargar_csv_para_validacion(RUTA_CANDIDATO)


def _resultados_por_nombre(df: pd.DataFrame):
    return {resultado.prueba: resultado for resultado in ejecutar_validaciones(df)}


@pytest.mark.parametrize("nombre_prueba", NOMBRES_PRUEBAS)
def test_candidato_supera_cada_validacion(candidato: pd.DataFrame, nombre_prueba: str):
    resultados = _resultados_por_nombre(candidato)
    assert list(resultados) == NOMBRES_PRUEBAS
    resultado = resultados[nombre_prueba]
    assert resultado.aprobada, (
        f"{resultado.prueba}: {resultado.errores} errores; "
        f"ejemplos={resultado.ejemplos}"
    )
    assert resultado.errores == 0


def _duplicar_fila(df: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([df, df.iloc[[0]]], ignore_index=True)


def _agregar_espacio(df: pd.DataFrame) -> pd.DataFrame:
    alterado = df.copy()
    alterado.at[0, "ESTABLECIMIENTO"] = f" {alterado.at[0, 'ESTABLECIMIENTO']}"
    return alterado


def _invalidar_telefono(df: pd.DataFrame) -> pd.DataFrame:
    alterado = df.copy()
    alterado.at[0, "TELEFONO"] = "123"
    return alterado


def _invalidar_geografia(df: pd.DataFrame) -> pd.DataFrame:
    alterado = df.copy()
    alterado.at[0, "DEPARTAMENTO"] = "DEPARTAMENTO INEXISTENTE"
    return alterado


def _romper_esquema(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns="ZONA_CAPITAL")


def _duplicar_categoria_por_escritura(df: pd.DataFrame) -> pd.DataFrame:
    alterado = df.copy()
    indice = alterado.index[alterado["SECTOR"].eq("OFICIAL")][0]
    alterado.at[indice, "SECTOR"] = "oficial"
    return alterado


def _agregar_valor_fuera_de_dominio(df: pd.DataFrame) -> pd.DataFrame:
    alterado = df.copy()
    alterado.at[0, "PLAN"] = "PLAN INEXISTENTE"
    return alterado


@pytest.mark.parametrize(
    ("nombre_prueba", "mutacion"),
    [
        ("Duplicados exactos", _duplicar_fila),
        ("Espacios en textos", _agregar_espacio),
        ("Formato de teléfonos", _invalidar_telefono),
        ("Geografía oficial", _invalidar_geografia),
        ("Esquema y tipos", _romper_esquema),
        ("Categorías equivalentes", _duplicar_categoria_por_escritura),
        ("Valores inválidos diagnosticados", _agregar_valor_fuera_de_dominio),
    ],
)
def test_cada_validacion_detecta_un_error_y_muestra_ejemplos(
    candidato: pd.DataFrame,
    nombre_prueba: str,
    mutacion,
):
    resultado = _resultados_por_nombre(mutacion(candidato))[nombre_prueba]
    assert not resultado.aprobada
    assert resultado.errores > 0
    assert resultado.ejemplos
