# Proyecto 1 — Obtención y Limpieza de Datos

Pipeline reproducible de CC3084 para obtener, diagnosticar, limpiar y validar los registros de establecimientos educativos de nivel diversificado publicados por el Ministerio de Educación de Guatemala (MINEDUC).

## Entrega final

- **Fuente:** [Buscador de establecimientos educativos del MINEDUC](https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/).
- **Fecha de extracción:** 2026-07-18.
- **Versión:** `v1.0.0`.
- **Salida única:** `data/processed/establecimientos_clean.csv`.
- **Dimensión:** 11,868 filas y 18 columnas (17 originales y `ZONA_CAPITAL`).
- **Cobertura:** los 22 departamentos de Guatemala.
- **SHA-256 final:** `429468cb07a6e31aeb2a1d27611b0d82952a5c909f2b6a454fc03b12a1ec5b49`.
- **Resultado:** 7 de 7 validaciones aprobadas con cero errores.

El CSV crudo contiene 11,891 filas y 17 variables. El pipeline retira únicamente 23 filas separadoras completamente vacías. El candidato conserva 11,868 códigos únicos; el checkpoint final no aprobó correcciones adicionales de contenido y lo ordena establemente por `CODIGO` antes de exportarlo.

## Estructura

```text
data/
├── raw/
│   ├── establecimientos_raw.csv
│   └── manifiesto_fuentes.csv
└── processed/
    ├── establecimientos_limpios_candidato.csv
    ├── establecimientos_clean.csv
    ├── duplicados_revisados.csv
    └── transformaciones.csv
notebooks/
├── 01_obtencion.ipynb
├── 02_diagnostico.ipynb
├── 04_limpieza.ipynb
├── 05_validacion.ipynb
└── 06_dataset_final.ipynb
scripts/
├── generar_notebooks.py
└── generar_codebook_pdf.py
src/                         # obtención, limpieza, catálogos, métricas y validación
tests/                       # pruebas de calidad, métricas y entrega final
03_plan_limpieza.md
codebook.md
codebook.pdf
informe_calidad.md
requirements.txt
```

## Requisitos e instalación

La entrega fue verificada con Python 3.14.2. Desde la raíz:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

`requirements.txt` fija las versiones utilizadas, incluida WeasyPrint para el PDF. No se requieren rutas absolutas ni variables locales.

## Ejecución reproducible

Ejecute en este orden desde la raíz:

1. Obtención/consolidación:

   ```bash
   .venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/01_obtencion.ipynb
   ```

2. Diagnóstico:

   ```bash
   .venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/02_diagnostico.ipynb
   ```

3. Revise las decisiones previas en `03_plan_limpieza.md`.

4. Limpieza y regeneración del candidato/trazabilidad:

   ```bash
   .venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/04_limpieza.ipynb
   ```

5. Pruebas y validación independiente:

   ```bash
   .venv/bin/python -m pytest -q
   .venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/05_validacion.ipynb
   ```

6. Dataset final:

   ```bash
   .venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/06_dataset_final.ipynb
   ```

7. PDF del libro de códigos:

   ```bash
   .venv/bin/python scripts/generar_codebook_pdf.py
   ```

8. Comprobación de la huella:

   ```bash
   shasum -a 256 data/processed/establecimientos_clean.csv
   ```

La carga correcta del CSV debe conservar todos los campos como texto:

```python
from src.validadores import cargar_csv_para_validacion

df = cargar_csv_para_validacion("data/processed/establecimientos_clean.csv")
```

Un CSV no almacena tipos semánticos: el cargador aplica explícitamente `string`, mantiene códigos/teléfonos y convierte solo campos vacíos a `NA`.

## Siete validaciones finales

Las pruebas fallan con ejemplos concretos cuando encuentran:

1. duplicados exactos;
2. espacios externos o múltiples;
3. teléfonos fuera del formato documentado;
4. departamentos/municipios ajenos al catálogo o relaciones inválidas;
5. columnas, orden o tipos semánticos incorrectos;
6. categorías duplicadas únicamente por escritura;
7. valores inválidos detectados en el diagnóstico.

La suite también comprueba 22 departamentos, catálogo 22/340, unicidad de `CODIGO`, ausencia de filas vacías, columnas duplicadas o `Unnamed:`, orden determinista, correspondencia exacta con el codebook, nueve campos por variable, versión y repetibilidad del hash.

## Decisiones y limitaciones

- Los códigos, distritos y teléfonos permanecen como texto; no se infieren dígitos.
- Los faltantes se escriben como campos vacíos y se cargan como `pd.NA` mediante el cargador del proyecto.
- `CIUDAD CAPITAL` se normaliza a departamento/municipio `GUATEMALA`; su zona original se conserva en `ZONA_CAPITAL`.
- Los catálogos contienen 22 departamentos, 340 municipios y su relación.
- Las 13 categorías de `PLAN`, incluidas cuatro variantes semipresenciales con frecuencias distintas, no se fusionan.
- Los 781 pares de posibles duplicados se conservaron: tienen códigos MINEDUC diferentes y no existe confirmación de fuente para fusionarlos. El detalle estable, similitud, decisión y justificación está en `duplicados_revisados.csv`; resultado: 781 conservados, 0 corregidos, 0 fusionados y 0 eliminados.
- El hash de referencia `0364f39e…` no coincide con el candidato presente. La huella recalculada del candidato es `a337c876…`; el hash final indicado arriba corresponde a los bytes realmente entregados después del ordenamiento determinista.
- La extracción histórica exacta no puede repetirse contra una fuente viva; el CSV crudo, manifiesto, fecha y hash fijan la entrada. Desde esa entrada, el flujo sí es reproducible.


