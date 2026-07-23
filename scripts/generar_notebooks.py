from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def markdown(texto: str):
    return nbf.v4.new_markdown_cell(texto.strip())


def codigo(texto: str):
    return nbf.v4.new_code_cell(texto.strip())


def guardar(nombre: str, celdas: list) -> None:
    notebook = nbf.v4.new_notebook(
        cells=celdas,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
    )
    nbf.write(notebook, NOTEBOOKS / nombre)


SETUP = r"""
from pathlib import Path
import sys

import pandas as pd

ROOT = Path.cwd().resolve()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
if not (ROOT / "data" / "raw" / "establecimientos_raw.csv").exists():
    raise FileNotFoundError("Ejecute el notebook desde la raíz del repositorio o desde notebooks/.")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 40)
"""


guardar(
    "01_obtencion.ipynb",
    [
        markdown(
            """
# Obtención y consolidación de datos

## Resumen

- **Fuente:** [Buscador de establecimientos educativos del MINEDUC](https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/).
- **Filtro:** `NIVEL ESCOLAR = DIVERSIFICADO`.
- **Cobertura:** 22 departamentos; el buscador consulta `CIUDAD CAPITAL` por separado de `GUATEMALA`.
- **Fecha de extracción:** 2026-07-18.

Los archivos por consulta fueron descargados manualmente debido a las protecciones del sitio. El CSV consolidado comprometido en el repositorio es el ancla inmutable del análisis. Este notebook verifica su estructura, cobertura, filtro y huella SHA-256, y genera un manifiesto reproducible.
"""
        ),
        markdown("## Configuración"),
        codigo(SETUP + "\nfrom src import catalogos, scraping"),
        markdown("## Carga del CSV crudo"),
        codigo(
            """
RUTA_RAW = ROOT / "data" / "raw" / "establecimientos_raw.csv"
RUTA_MANIFIESTO = ROOT / "data" / "raw" / "manifiesto_fuentes.csv"

df_raw = pd.read_csv(RUTA_RAW, dtype="string", keep_default_na=False)
print(f"Filas: {df_raw.shape[0]:,}")
print(f"Columnas: {df_raw.shape[1]}")
df_raw.head()
"""
        ),
        markdown("## Verificación de esquema, nivel y cobertura"),
        codigo(
            """
COLUMNAS_ESPERADAS = [
    "CODIGO", "DISTRITO", "DEPARTAMENTO", "MUNICIPIO", "ESTABLECIMIENTO",
    "DIRECCION", "TELEFONO", "SUPERVISOR", "DIRECTOR", "NIVEL", "SECTOR",
    "AREA", "STATUS", "MODALIDAD", "JORNADA", "PLAN", "DEPARTAMENTAL",
]
assert list(df_raw.columns) == COLUMNAS_ESPERADAS

filas_con_datos = df_raw[df_raw["CODIGO"].str.strip().ne("")]
assert filas_con_datos["NIVEL"].eq("DIVERSIFICADO").all()

departamentos_presentes = set(filas_con_datos["DEPARTAMENTO"].str.strip().str.upper())
faltantes = set(catalogos.DEPARTAMENTOS_OFICIALES) - departamentos_presentes
extras = departamentos_presentes - set(catalogos.DEPARTAMENTOS_OFICIALES)

print("Departamentos oficiales ausentes:", faltantes or "ninguno")
print("Consulta adicional del buscador:", extras)
filas_con_datos["DEPARTAMENTO"].value_counts()
"""
        ),
        markdown("## Verificación reproducible de la unión"),
        codigo(
            """
import tempfile

filas_vacias = df_raw.apply(lambda serie: serie.str.strip().eq("")).all(axis=1)
posiciones_separadores = df_raw.index[filas_vacias].tolist()
assert len(posiciones_separadores) == 23

bloques = []
inicio = 0
for fin in posiciones_separadores:
    bloques.append(df_raw.loc[inicio:fin].reset_index(drop=True))
    inicio = fin + 1

with tempfile.TemporaryDirectory() as directorio_temporal:
    rutas_bloques = []
    for numero, bloque in enumerate(bloques, start=1):
        ruta = Path(directorio_temporal) / f"consulta_{numero:02d}.csv"
        bloque.to_csv(ruta, index=False, lineterminator="\n")
        rutas_bloques.append(ruta)

    reconstruido = scraping.unir_csvs(rutas_bloques)

pd.testing.assert_frame_equal(df_raw, reconstruido, check_dtype=False)
print("Bloques unidos:", len(bloques))
print("La unión reproduce exactamente las 11,891 filas del CSV crudo.")
"""
        ),
        markdown("## Manifiesto y huella de integridad"),
        codigo(
            """
manifiesto = scraping.crear_manifiesto_consolidado(RUTA_RAW, "2026-07-18")
manifiesto.to_csv(RUTA_MANIFIESTO, index=False, lineterminator="\n")

print("SHA-256:", scraping.sha256_archivo(RUTA_RAW))
print("Registros documentados:", int(manifiesto["registros"].sum()))
manifiesto
"""
        ),
        markdown(
            """
## Nota de reproducibilidad

`src/scraping.py` contiene funciones para descargar una consulta y unir una lista de CSV con el mismo esquema. La descarga histórica exacta no puede repetirse desde una fuente viva; por eso la fecha y el hash fijan el CSV crudo utilizado. A partir de este archivo, todo el diagnóstico y la limpieza sí deben reproducirse de extremo a extremo.
"""
        ),
    ],
)


guardar(
    "02_diagnostico.ipynb",
    [
        markdown(
            """
# Diagnóstico inicial de calidad

## Resumen

Este notebook evalúa el CSV crudo sin modificarlo. Revisa estructura, tipos, faltantes semánticos, cardinalidad, duplicados, dominios, formatos y relaciones entre variables. Los resultados constituyen la línea base del informe Antes/Después.
"""
        ),
        markdown("## Configuración y datos"),
        codigo(SETUP + "\nfrom src import catalogos, diagnostico, validadores"),
        codigo(
            """
RUTA_RAW = ROOT / "data" / "raw" / "establecimientos_raw.csv"
df = pd.read_csv(RUTA_RAW, dtype="string", keep_default_na=False)
print(f"Registros: {df.shape[0]:,} | Variables: {df.shape[1]}")
"""
        ),
        markdown("## 1. Registros, variables y tipos"),
        codigo("diagnostico.resumen_tipos(df)"),
        markdown(
            "Los identificadores, teléfonos, categorías y textos deben conservarse como texto. Leerlos como números eliminaría ceros iniciales y no aportaría operaciones numéricas válidas."
        ),
        markdown("## 2. Faltantes por variable y total"),
        codigo("diagnostico.resumen_faltantes(df)"),
        codigo("diagnostico.resumen_faltantes_total(df)"),
        markdown(
            "El conteo incluye `NA`, cadenas vacías, puntos, `SIN DATO` y cadenas formadas únicamente por guiones. Esto evita subestimar especialmente los faltantes de `DIRECTOR`."
        ),
        markdown("## 3. Valores únicos"),
        codigo("diagnostico.contar_unicos(df)"),
        markdown("## 4. Duplicados exactos y filas estructurales"),
        codigo(
            """
filas_totalmente_vacias = df.apply(diagnostico.mascara_faltantes).all(axis=1)
print("Filas totalmente vacías:", int(filas_totalmente_vacias.sum()))
print("Duplicados exactos:", diagnostico.contar_duplicados_exactos(df))
print(
    "Duplicados exactos excluyendo filas vacías:",
    diagnostico.contar_duplicados_exactos(df.loc[~filas_totalmente_vacias]),
)
"""
        ),
        markdown("## 5. Dominios geográficos"),
        codigo(
            """
departamentos_invalidos = df.loc[
    df["DEPARTAMENTO"].str.strip().ne("")
    & ~df["DEPARTAMENTO"].map(catalogos.es_departamento_valido),
    "DEPARTAMENTO",
].value_counts()
print("Departamento fuera del catálogo:")
departamentos_invalidos
"""
        ),
        codigo(
            """
filas_geograficas = df[
    df["DEPARTAMENTO"].str.strip().ne("") & df["MUNICIPIO"].str.strip().ne("")
].copy()
municipio_valido = filas_geograficas.apply(
    lambda fila: catalogos.es_municipio_valido(
        fila["MUNICIPIO"], fila["DEPARTAMENTO"]
    ),
    axis=1,
)
municipios_fuera_dominio = filas_geograficas.loc[~municipio_valido, "MUNICIPIO"]
print("Filas fuera del catálogo antes de equivalencias:", int((~municipio_valido).sum()))
municipios_fuera_dominio.value_counts().head(30)
"""
        ),
        markdown(
            "Las zonas capitalinas no son municipios. Los municipios oficiales `SIPACATE`, `LA LIBERTAD`, `SANTA BARBARA` y `PETATAN` sí están incluidos en el catálogo corregido y ya no se cuentan como inválidos."
        ),
        markdown("## 6. Formatos de texto e identificadores"),
        codigo("diagnostico.resumen_formato_texto(df)"),
        codigo("diagnostico.resumen_patrones_identificadores(df)"),
        codigo(
            """
telefonos = df["TELEFONO"].mask(diagnostico.mascara_faltantes(df["TELEFONO"]))
telefonos_no_estandar = telefonos.notna() & ~telefonos.str.fullmatch(r"[2-7]\\d{7}", na=False)
print("Teléfonos no vacíos fuera del formato único de 8 dígitos:", int(telefonos_no_estandar.sum()))
telefonos[telefonos_no_estandar].value_counts().head(20)
"""
        ),
        markdown("## 7. Consistencia entre variables"),
        codigo(
            """
comparables = df[
    df["DEPARTAMENTO"].str.strip().ne("")
    & df["DEPARTAMENTAL"].str.strip().ne("")
].copy()
depto_para_regla = comparables["DEPARTAMENTO"].replace("CIUDAD CAPITAL", "GUATEMALA")
relacion_valida = [
    validadores.es_departamental_consistente(depto, direccion)
    for depto, direccion in zip(depto_para_regla, comparables["DEPARTAMENTAL"])
]
print("Diferencias literales DEPARTAMENTO/DEPARTAMENTAL:", int(
    comparables["DEPARTAMENTO"].ne(comparables["DEPARTAMENTAL"]).sum()
))
print("Relaciones administrativas no permitidas:", int((~pd.Series(relacion_valida)).sum()))
"""
        ),
        markdown(
            "Una diferencia literal no implica contradicción: `GUATEMALA NORTE` o `QUICHE NORTE` son direcciones departamentales válidas. La limpieza normaliza tildes y conserva estas subregiones."
        ),
        markdown("## 8. Resumen de problemas para las 17 variables"),
        codigo(
            """
resumen_problemas = pd.DataFrame(
    [
        ("CODIGO", "Formato válido en registros reales; faltantes solo en filas vacías."),
        ("DISTRITO", "Faltantes y valores incompletos; coexisten dos formatos completos."),
        ("DEPARTAMENTO", "CIUDAD CAPITAL está fuera del catálogo de 22 departamentos."),
        ("MUNICIPIO", "Zonas capitalinas y variantes de nombres; validar contra 340 municipios."),
        ("ESTABLECIMIENTO", "Faltantes residuales y variantes por tildes; texto libre."),
        ("DIRECCION", "Faltantes, puntos como ausencia y redacción libre."),
        ("TELEFONO", "Faltantes, múltiples números, letras y longitudes inconsistentes."),
        ("SUPERVISOR", "Faltantes y variantes ortográficas; texto libre."),
        ("DIRECTOR", "Faltantes subestimados por guiones, puntos y SIN DATO."),
        ("NIVEL", "Un único valor real: DIVERSIFICADO; faltantes estructurales."),
        ("SECTOR", "Cuatro categorías válidas; faltantes estructurales."),
        ("AREA", "Tres categorías; SIN ESPECIFICAR es valor explícito."),
        ("STATUS", "Cinco estados válidos con significados diferentes."),
        ("MODALIDAD", "Dos categorías; normalizar diferencias de acentuación."),
        ("JORNADA", "Seis categorías; SIN JORNADA es categoría, no NA."),
        ("PLAN", "Trece categorías; las modalidades semipresenciales no son equivalentes."),
        ("DEPARTAMENTAL", "26 direcciones, incluidas subregiones y diferencias de tildes."),
    ],
    columns=["Variable", "Problema potencial de calidad"],
)
resumen_problemas
"""
        ),
        markdown(
            "## Conclusión\n\nEl CSV crudo es utilizable como fuente de limpieza, pero no debe analizarse directamente: contiene filas estructurales, faltantes codificados de varias maneras, formatos telefónicos/distritales inconsistentes y geografía que requiere equivalencias explícitas."
        ),
    ],
)


guardar(
    "04_limpieza.ipynb",
    [
        markdown(
            """
# Limpieza reproducible del conjunto de establecimientos

## Resumen

Este notebook aplica las reglas aprobadas en `03_plan_limpieza.md`. Produce un conjunto candidato para validación, el registro completo de transformaciones y la revisión caso por caso de posibles duplicados parciales. Ningún candidato parcial se elimina automáticamente.
"""
        ),
        markdown("## Configuración"),
        codigo(
            SETUP
            + "\nfrom src import catalogos, diagnostico, scraping, validadores"
            + "\nfrom src.duplicados import encontrar_duplicados_parciales"
            + "\nfrom src.pipeline_limpieza import limpiar_establecimientos"
        ),
        markdown("## Carga del conjunto crudo"),
        codigo(
            """
RUTA_RAW = ROOT / "data" / "raw" / "establecimientos_raw.csv"
RUTA_CANDIDATO = ROOT / "data" / "processed" / "establecimientos_limpios_candidato.csv"
RUTA_TRANSFORMACIONES = ROOT / "data" / "processed" / "transformaciones.csv"
RUTA_DUPLICADOS = ROOT / "data" / "processed" / "duplicados_revisados.csv"

df_raw = pd.read_csv(RUTA_RAW, dtype="string", keep_default_na=False)
print("Dimensión cruda:", df_raw.shape)
diagnostico.resumen_faltantes_total(df_raw)
"""
        ),
        markdown("## Línea base de posibles duplicados"),
        codigo(
            """
filas_vacias_raw = df_raw.apply(diagnostico.mascara_faltantes).all(axis=1)
df_raw_real = df_raw.loc[~filas_vacias_raw].reset_index(drop=True)
duplicados_parciales_antes = encontrar_duplicados_parciales(df_raw_real)
registros_candidatos_antes = set(duplicados_parciales_antes["indice_1"]) | set(
    duplicados_parciales_antes["indice_2"]
)
print("Pares candidatos Antes:", len(duplicados_parciales_antes))
print("Registros involucrados Antes:", len(registros_candidatos_antes))
"""
        ),
        markdown("## Aplicación determinista de las reglas"),
        codigo(
            """
resultado = limpiar_establecimientos(df_raw)
df_limpio = resultado.datos
transformaciones = resultado.transformaciones
duplicados_revisados = resultado.duplicados_revisados

print("Dimensión candidata:", df_limpio.shape)
print("Transformaciones documentadas:", len(transformaciones))
print("Pares parciales revisados:", len(duplicados_revisados))
"""
        ),
        markdown("## Registro de transformaciones"),
        codigo("transformaciones"),
        markdown("## Revisión conservadora de duplicados parciales"),
        codigo(
            """
print(duplicados_revisados["decision"].value_counts(dropna=False))
registros_candidatos_despues = set(duplicados_revisados["indice_1"]) | set(
    duplicados_revisados["indice_2"]
)
print("Registros involucrados Después:", len(registros_candidatos_despues))
duplicados_revisados.head(20)
"""
        ),
        markdown(
            "Los pares se conservan porque poseen códigos MINEDUC diferentes. El archivo registra similitudes, campos diferentes, decisión y justificación para cada caso; una fusión futura requeriría confirmación de la fuente."
        ),
        markdown("## Comprobaciones de calidad del candidato"),
        codigo(
            """
errores = validadores.contar_errores_calidad(df_limpio)
errores
"""
        ),
        codigo(
            """
assert all(valor == 0 for valor in errores.values()), errores
assert df_limpio["CODIGO"].is_unique
assert df_limpio["NIVEL"].eq("DIVERSIFICADO").all()
assert set(df_limpio["DEPARTAMENTO"].dropna()) == set(catalogos.DEPARTAMENTOS_OFICIALES)
print("Comprobaciones internas aprobadas.")
"""
        ),
        markdown("## Comparación preliminar de calidad"),
        codigo(
            """
comparacion_faltantes = pd.DataFrame(
    {
        "Antes": diagnostico.resumen_faltantes_total(df_raw),
        "Después_candidato": diagnostico.resumen_faltantes_total(df_limpio),
    }
)
comparacion_faltantes
"""
        ),
        markdown("## Exportación de artefactos"),
        codigo(
            """
RUTA_CANDIDATO.parent.mkdir(parents=True, exist_ok=True)
RUTA_TRANSFORMACIONES.parent.mkdir(parents=True, exist_ok=True)

df_limpio.to_csv(RUTA_CANDIDATO, index=False, lineterminator="\n")
transformaciones.to_csv(RUTA_TRANSFORMACIONES, index=False, lineterminator="\n")
duplicados_revisados.to_csv(RUTA_DUPLICADOS, index=False, lineterminator="\n")

print("Candidato:", RUTA_CANDIDATO.relative_to(ROOT))
print("SHA-256 candidato:", scraping.sha256_archivo(RUTA_CANDIDATO))
print("Transformaciones:", RUTA_TRANSFORMACIONES.relative_to(ROOT))
print("Duplicados revisados:", RUTA_DUPLICADOS.relative_to(ROOT))
"""
        ),
        markdown(
            """
## Resultado

El conjunto candidato conserva una fila por código oficial, añade `ZONA_CAPITAL`, normaliza geografía y formatos, representa las ausencias con `NA` y supera las comprobaciones internas. La validación independiente y la exportación del CSV final pertenecen a las fases siguientes.
"""
        ),
    ],
)


guardar(
    "05_validacion.ipynb",
    [
        markdown(
            """
# Validación automática del conjunto candidato

Este notebook ejecuta las siete comprobaciones de calidad exigidas sobre el CSV candidato. Todas las reglas provienen de `src/validadores.py`, la misma implementación utilizada por `pytest`, y cada fallo incluye cantidad, explicación y ejemplos suficientes para corregirlo.
"""
        ),
        markdown("## Configuración y carga reproducible"),
        codigo(
            SETUP
            + "\nfrom src.validadores import ("
            + "\n    cargar_csv_para_validacion,"
            + "\n    ejecutar_validaciones,"
            + "\n    resumen_validaciones,"
            + "\n)"
            + "\nfrom src.metricas_calidad import ("
            + "\n    calcular_comparacion_calidad,"
            + "\n    resumen_decisiones_duplicados,"
            + "\n    tabla_comparativa,"
            + "\n)"
        ),
        codigo(
            """
RUTA_CANDIDATO = ROOT / "data" / "processed" / "establecimientos_limpios_candidato.csv"
df_candidato = cargar_csv_para_validacion(RUTA_CANDIDATO)

print(f"Registros: {df_candidato.shape[0]:,}")
print(f"Variables: {df_candidato.shape[1]}")
df_candidato.head()
"""
        ),
        markdown("## Ejecución de las siete validaciones"),
        codigo(
            """
resultados = ejecutar_validaciones(df_candidato, max_ejemplos=5)
resumen = resumen_validaciones(resultados)
resumen
"""
        ),
        markdown(
            """
Las pruebas comprueban, en orden: duplicados exactos; espacios en textos; teléfonos; geografía oficial; esquema y tipos; categorías equivalentes por escritura; y valores inválidos identificados durante el diagnóstico.
"""
        ),
        markdown("## Detalle de fallos y ejemplos"),
        codigo(
            """
fallos = [resultado for resultado in resultados if not resultado.aprobada]
if not fallos:
    print("No se encontraron fallos; las siete validaciones fueron aprobadas.")
else:
    for resultado in fallos:
        print(f"\\n{resultado.prueba}: {resultado.errores} error(es)")
        print(resultado.detalle)
        print(pd.DataFrame(resultado.ejemplos).to_string(index=False))
"""
        ),
        markdown("## Comprobación inequívoca del resultado"),
        codigo(
            """
assert len(resultados) == 7, "Deben ejecutarse exactamente siete validaciones."
assert all(resultado.aprobada for resultado in resultados), {
    resultado.prueba: resultado.ejemplos for resultado in fallos
}
assert resumen["Errores"].sum() == 0

print("VALIDACIÓN APROBADA: 7 de 7 pruebas superadas con cero errores.")
"""
        ),
        markdown("## Esquema validado"),
        codigo(
            """
pd.DataFrame(
    {
        "Variable": df_candidato.columns,
        "Tipo observado": [str(tipo) for tipo in df_candidato.dtypes],
        "Valores faltantes": [int(df_candidato[col].isna().sum()) for col in df_candidato],
        "Valores únicos": [int(df_candidato[col].nunique(dropna=True)) for col in df_candidato],
    }
)
"""
        ),
        markdown("## Informe reproducible de calidad Antes/Después"),
        codigo(
            """
RUTA_RAW = ROOT / "data" / "raw" / "establecimientos_raw.csv"
RUTA_TRANSFORMACIONES = ROOT / "data" / "processed" / "transformaciones.csv"
RUTA_DUPLICADOS = ROOT / "data" / "processed" / "duplicados_revisados.csv"

df_raw = pd.read_csv(RUTA_RAW, dtype="string", keep_default_na=False)
transformaciones = pd.read_csv(RUTA_TRANSFORMACIONES, dtype="string")
duplicados_revisados = pd.read_csv(RUTA_DUPLICADOS, dtype="string")

comparacion = calcular_comparacion_calidad(
    df_raw, df_candidato, transformaciones
)
tabla_calidad = tabla_comparativa(comparacion)
tabla_calidad
"""
        ),
        markdown("### Comparación equivalente de valores faltantes"),
        codigo(
            """
pd.DataFrame(
    [
        {
            "Comparación": "Todas las variables de cada estado",
            "Antes": f"{comparacion.antes.faltantes:,} / {comparacion.antes.celdas:,} ({comparacion.antes.porcentaje_faltantes:.2f} %)",
            "Después": f"{comparacion.despues.faltantes:,} / {comparacion.despues.celdas:,} ({comparacion.despues.porcentaje_faltantes:.2f} %)",
        },
        {
            "Comparación": "Solo las 17 variables originales",
            "Antes": f"{comparacion.antes.faltantes:,} / {comparacion.antes.celdas:,} ({comparacion.antes.porcentaje_faltantes:.2f} %)",
            "Después": f"{comparacion.faltantes_despues_comparables:,} / {comparacion.celdas_despues_comparables:,} ({comparacion.porcentaje_despues_comparable:.2f} %)",
        },
    ]
)
"""
        ),
        markdown("### Decisiones sobre posibles duplicados"),
        codigo(
            """
decisiones_duplicados = resumen_decisiones_duplicados(duplicados_revisados)
pd.DataFrame(
    decisiones_duplicados.items(), columns=["Decisión", "Pares candidatos"]
)
"""
        ),
        markdown("### Resumen de correcciones"),
        codigo(
            """
pd.DataFrame(
    comparacion.correcciones.items(),
    columns=["Tipo de corrección", "Registros afectados"],
)
"""
        ),
        markdown("### Comprobación reproducible del informe"),
        codigo(
            """
assert tabla_calidad.shape == (10, 3)
assert (comparacion.antes.registros, comparacion.despues.registros) == (11891, 11868)
assert (comparacion.antes.faltantes, comparacion.despues.faltantes) == (4645, 14148)
assert comparacion.faltantes_despues_comparables == 4441
assert (comparacion.antes.duplicados_exactos, comparacion.despues.duplicados_exactos) == (22, 0)
assert (
    comparacion.antes.posibles_duplicados_pares,
    comparacion.despues.posibles_duplicados_pares,
) == (769, 781)
assert decisiones_duplicados == {
    "conservados": 781,
    "corregidos": 0,
    "fusionados": 0,
    "eliminados": 0,
}
assert all(resultado.aprobada for resultado in resultados)

print("INFORME REPRODUCIDO: 10 métricas Antes/Después confirmadas.")
"""
        ),
        markdown(
            """
## Resultado

El conjunto candidato supera las siete reglas automáticas y la comparación reproducible confirma las diez métricas Antes/Después. Este resultado no renombra ni exporta todavía el CSV final.
"""
        ),
    ],
)


print("Notebooks generados:")
for path in sorted(NOTEBOOKS.glob("*.ipynb")):
    print(path.relative_to(ROOT))
