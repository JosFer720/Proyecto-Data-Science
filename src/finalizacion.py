from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from src import catalogos
from src.validadores import (
    COLUMNAS_REQUERIDAS,
    ResultadoValidacion,
    cargar_csv_para_validacion,
    ejecutar_validaciones,
)


VERSION_DATASET = "v1.0.0"
FECHA_EXTRACCION = "2026-07-18"
FUENTE_DATOS = "MINEDUC, Buscador de establecimientos educativos"
NOMBRE_CSV_FINAL = "establecimientos_clean.csv"

CAMPOS_CODEBOOK = (
    "Variable",
    "Descripción",
    "Tipo de dato",
    "Dominio permitido",
    "Valores posibles",
    "Tratamiento aplicado",
    "Variables derivadas",
    "Fecha de extracción",
    "Fuente",
    "Versión del conjunto limpio",
)


def sha256_archivo(ruta: str | Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def preparar_dataset_final(df_candidato: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el candidato en el orden contractual, sin corregir datos en silencio."""
    resultados = ejecutar_validaciones(df_candidato)
    fallos = [resultado for resultado in resultados if not resultado.aprobada]
    if fallos:
        detalle = "; ".join(
            f"{resultado.prueba}: {resultado.errores}, ejemplos={resultado.ejemplos}"
            for resultado in fallos
        )
        raise ValueError(f"No se puede preparar un candidato inválido: {detalle}")

    final = df_candidato.loc[:, COLUMNAS_REQUERIDAS].copy()
    final = final.sort_values("CODIGO", kind="mergesort").reset_index(drop=True)
    for columna in final.columns:
        final[columna] = final[columna].astype("string")
    return final


def exportar_dataset_final(
    ruta_candidato: str | Path,
    ruta_salida: str | Path,
) -> tuple[pd.DataFrame, str, list[ResultadoValidacion]]:
    """Valida, ordena, escribe y relee el único CSV limpio final."""
    candidato = cargar_csv_para_validacion(ruta_candidato)
    final = preparar_dataset_final(candidato)
    salida = Path(ruta_salida)
    if salida.name != NOMBRE_CSV_FINAL:
        raise ValueError(f"El CSV final debe llamarse {NOMBRE_CSV_FINAL}")
    salida.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(
        salida,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        na_rep="",
    )

    recargado = cargar_csv_para_validacion(salida)
    resultados = ejecutar_validaciones(recargado)
    fallos = [resultado for resultado in resultados if not resultado.aprobada]
    if fallos:
        salida.unlink(missing_ok=True)
        raise ValueError(f"La recarga del CSV final falló: {fallos}")
    pd.testing.assert_frame_equal(final, recargado)
    return recargado, sha256_archivo(salida), resultados


def variables_documentadas_codebook(ruta: str | Path) -> list[str]:
    patron = re.compile(r"^\|\s*`([^`]+)`\s*\|")
    seccion = Path(ruta).read_text(encoding="utf-8").split("## Diccionario de variables", 1)[1]
    seccion = seccion.split("\n## ", 1)[0]
    return [
        coincidencia.group(1)
        for linea in seccion.splitlines()
        if (coincidencia := patron.match(linea))
    ]


def validar_codebook(ruta: str | Path, columnas: list[str]) -> None:
    """Comprueba cobertura, nueve campos y metadatos del diccionario final."""
    texto = Path(ruta).read_text(encoding="utf-8")
    documentadas = variables_documentadas_codebook(ruta)
    if documentadas != columnas:
        raise ValueError(
            f"Codebook/CSV no coinciden: documentadas={documentadas}; CSV={columnas}"
        )
    cabecera = next(
        (linea for linea in texto.splitlines() if linea.startswith("| Variable |")),
        "",
    )
    campos = [campo.strip() for campo in cabecera.strip("|").split("|")]
    if tuple(campos) != CAMPOS_CODEBOOK:
        raise ValueError(f"Campos del codebook inválidos: {campos}")
    seccion = texto.split("## Diccionario de variables", 1)[1].split("\n## ", 1)[0]
    for linea in seccion.splitlines():
        if re.match(r"^\|\s*`[^`]+`\s*\|", linea):
            celdas = [celda.strip() for celda in linea.strip("|").split("|")]
            if len(celdas) != len(CAMPOS_CODEBOOK) or any(not celda for celda in celdas):
                raise ValueError(f"Entrada incompleta del codebook: {linea}")
            if celdas[7] != FECHA_EXTRACCION or celdas[9] != f"`{VERSION_DATASET}`":
                raise ValueError(f"Metadatos inconsistentes en {celdas[0]}")
    if "MINEDUC" not in texto or "Buscador de establecimientos" not in texto:
        raise ValueError("El codebook no identifica completamente la fuente MINEDUC.")


def validar_invariantes_finales(df: pd.DataFrame) -> None:
    if df.shape != (11868, 18):
        raise ValueError(f"Dimensión final inesperada: {df.shape}")
    if df.isna().all(axis=1).any():
        raise ValueError("El conjunto contiene filas completamente vacías.")
    if not df["CODIGO"].is_unique:
        raise ValueError("CODIGO no es único.")
    if df["CODIGO"].tolist() != sorted(df["CODIGO"].tolist()):
        raise ValueError("Las filas no están ordenadas determinísticamente por CODIGO.")
    cobertura = set(df["DEPARTAMENTO"].dropna())
    if cobertura != set(catalogos.DEPARTAMENTOS_OFICIALES):
        raise ValueError(f"Cobertura departamental inesperada: {sorted(cobertura)}")
    if df.columns.duplicated().any() or any(
        columna.startswith("Unnamed:") for columna in df.columns
    ):
        raise ValueError("El esquema contiene columnas duplicadas o auxiliares.")
