from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import catalogos
from src.finalizacion import (
    VERSION_DATASET,
    exportar_dataset_final,
    sha256_archivo,
    validar_codebook,
    validar_invariantes_finales,
)
from src.validadores import COLUMNAS_REQUERIDAS, cargar_csv_para_validacion


ROOT = Path(__file__).resolve().parents[1]
RUTA_CANDIDATO = ROOT / "data" / "processed" / "establecimientos_limpios_candidato.csv"
RUTA_FINAL = ROOT / "data" / "processed" / "establecimientos_clean.csv"


def test_catalogos_tienen_22_departamentos_y_340_municipios():
    assert len(catalogos.DEPARTAMENTOS_OFICIALES) == 22
    assert sum(map(len, catalogos.MUNICIPIOS_POR_DEPARTAMENTO.values())) == 340


def test_csv_final_cumple_invariantes_y_esquema():
    final = cargar_csv_para_validacion(RUTA_FINAL)
    validar_invariantes_finales(final)
    assert list(final.columns) == COLUMNAS_REQUERIDAS
    assert all(isinstance(tipo, pd.StringDtype) for tipo in final.dtypes)


def test_codebook_documenta_columnas_y_nueve_campos():
    final = cargar_csv_para_validacion(RUTA_FINAL)
    validar_codebook(ROOT / "codebook.md", list(final.columns))


def test_exportacion_y_hash_son_deterministas(tmp_path: Path):
    primera = tmp_path / "primera" / "establecimientos_clean.csv"
    segunda = tmp_path / "segunda" / "establecimientos_clean.csv"
    df_1, hash_1, _ = exportar_dataset_final(RUTA_CANDIDATO, primera)
    df_2, hash_2, _ = exportar_dataset_final(RUTA_CANDIDATO, segunda)
    assert hash_1 == hash_2 == sha256_archivo(RUTA_FINAL)
    pd.testing.assert_frame_equal(df_1, df_2)


def test_version_final_es_consistente_en_documentacion():
    assert VERSION_DATASET == "v1.0.0"
    for nombre in ("README.md", "codebook.md"):
        texto = (ROOT / nombre).read_text(encoding="utf-8")
        assert VERSION_DATASET in texto, f"Falta {VERSION_DATASET} en {nombre}"


def test_no_existen_csv_finales_ambiguos():
    finales = sorted(
        ruta.name
        for ruta in (ROOT / "data" / "processed").glob("*.csv")
        if "clean" in ruta.stem.lower() or "final" in ruta.stem.lower()
    )
    assert finales == ["establecimientos_clean.csv"]
