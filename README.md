# Proyecto 1 — Obtención y Limpieza de Datos

Pipeline reproducible para obtener, diagnosticar y limpiar los registros de establecimientos educativos de nivel diversificado publicados por el MINEDUC de Guatemala.

## Estado actual

- Obtención y diagnóstico inicial implementados.
- Plan de limpieza documentado para las 17 variables originales.
- Limpieza reproducible implementada.
- Conjunto limpio **candidato** disponible para validación independiente.
- Registro de transformaciones y revisión de duplicados parciales generados.
- Pendiente: pruebas automáticas independientes, versión final del codebook, PDF y exportación del único CSV final.

El candidato no debe renombrarse todavía como `establecimientos_clean.csv`; ese nombre se reserva para el archivo que supere la validación final.

## Fuente y alcance

- Fuente: `https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/`
- Filtro: `NIVEL ESCOLAR = DIVERSIFICADO`
- Fecha de extracción: 2026-07-18
- Cobertura: 22 departamentos; el buscador consulta `CIUDAD CAPITAL` por separado.
- CSV crudo: 11,891 filas y 17 variables.
- CSV candidato: 11,868 filas y 18 variables.

## Estructura relevante

```text
data/
├── raw/
│   ├── establecimientos_raw.csv
│   └── manifiesto_fuentes.csv
└── processed/
    ├── establecimientos_limpios_candidato.csv
    ├── duplicados_revisados.csv
    └── transformaciones.csv
notebooks/
├── 01_obtencion.ipynb
├── 02_diagnostico.ipynb
└── 04_limpieza.ipynb
src/
├── catalogos.py
├── diagnostico.py
├── duplicados.py
├── limpieza_texto.py
├── pipeline_limpieza.py
├── scraping.py
└── validadores.py
03_plan_limpieza.md
codebook.md
informe_calidad.md
```

## Preparación del entorno

Con `uv`:

```bash
uv venv .venv
UV_CACHE_DIR=/tmp/uv-cache uv pip install --python .venv/bin/python -r requirements.txt
```

También puede utilizarse `python -m venv` y `pip install -r requirements.txt`.

## Orden de ejecución

Ejecutar desde la raíz del repositorio:

```bash
.venv/bin/python -m jupyter nbconvert --execute --to notebook --inplace notebooks/01_obtencion.ipynb
.venv/bin/python -m jupyter nbconvert --execute --to notebook --inplace notebooks/02_diagnostico.ipynb
.venv/bin/python -m jupyter nbconvert --execute --to notebook --inplace notebooks/04_limpieza.ipynb
```

El primer notebook valida el CSV crudo y actualiza su manifiesto. El segundo reproduce el diagnóstico. El tercero regenera el candidato limpio y los dos archivos de trazabilidad.

## Decisiones importantes

- Las filas totalmente vacías se eliminan durante la limpieza, no durante la obtención.
- Los códigos y teléfonos se mantienen como texto.
- Los marcadores `SIN DATO`, puntos y cadenas de guiones se consideran faltantes.
- `CIUDAD CAPITAL` se normaliza a departamento y municipio `GUATEMALA`; la zona se conserva en `ZONA_CAPITAL`.
- El catálogo contiene los 340 municipios oficiales.
- Las modalidades semipresenciales de `PLAN` no se fusionan porque describen frecuencias diferentes.
- Los posibles duplicados no se eliminan automáticamente. Cada par conserva decisión y justificación en `duplicados_revisados.csv`.
- Las cadenas formadas únicamente por puntuación se representan como `NA`; la validación impide que reaparezcan en los textos libres.

## Trazabilidad

- `03_plan_limpieza.md`: reglas definidas antes de transformar.
- `transformaciones.csv`: resumen cuantitativo de cada transformación.
- `duplicados_revisados.csv`: revisión de cada par candidato.
- `codebook.md`: definición, dominio y tratamiento de cada variable.
- `informe_calidad.md`: comparación cuantitativa Antes/Después.


