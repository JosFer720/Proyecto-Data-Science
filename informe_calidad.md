# Informe de calidad de datos

## Comparación Antes/Después

La columna Después corresponde al conjunto limpio final `v1.0.0`. Sus valores coinciden con el candidato validado porque el checkpoint final no aprobó correcciones de contenido; únicamente fijó el orden por `CODIGO`. Las cifras están confirmadas mediante `src/metricas_calidad.py` y se reproducen en `notebooks/05_validacion.ipynb` y `notebooks/06_dataset_final.ipynb`.

| Métrica | Antes | Después (`v1.0.0`) |
|---|---|---|
| Registros | 11,891 filas, incluidas 23 filas completamente vacías. | 11,868 filas; se eliminaron únicamente las 23 filas estructurales vacías. |
| Variables | 17 variables. | 18 variables; se agregó `ZONA_CAPITAL` para no perder la zona al normalizar Ciudad Capital. |
| Valores faltantes (# y %) | 4,645 de 202,147 celdas (2.30 %), incluyendo vacíos, `SIN DATO` y cadenas formadas únicamente por signos o espacios. | 14,148 de 213,624 celdas (6.62 %). La variable derivada aporta 9,707 NA estructurales; excluyéndola son 4,441 de 201,756 celdas (2.20 %). |
| Variables con NA | 17, porque las 23 filas vacías afectan todas las columnas. Excluyendo esas filas, 6 variables contienen faltantes reales. | 7: `DISTRITO`, `ZONA_CAPITAL`, `ESTABLECIMIENTO`, `DIRECCION`, `TELEFONO`, `SUPERVISOR` y `DIRECTOR`. |
| Duplicados exactos | 22 repeticiones contadas por pandas; corresponden a 23 filas vacías idénticas. No hay duplicados exactos entre las filas con código. | 0. |
| Posibles duplicados | 769 pares candidatos que afectan 1,372 registros, usando bloqueo, similitud de nombre y coincidencia de dirección/teléfono. | 781 pares que afectan 1,386 registros. Los 781 se conservaron porque sus códigos MINEDUC son distintos; cada decisión está documentada. El aumento se debe a la normalización que permite detectar 12 pares adicionales. |
| Variables con formato inconsistente | 5: `DISTRITO`, `DIRECCION`, `TELEFONO`, `DIRECTOR` y `DEPARTAMENTAL`. | 0 según las reglas implementadas para espacios, identificadores, teléfonos y relación administrativa. |
| Variables con tipo incorrecto | 0. Las 17 variables son identificadores, categorías o texto y deben leerse como `string`, no como números. | 0. Las 18 variables se exportan como texto; los códigos y teléfonos conservan ceros iniciales. |
| Categorías inconsistentes | 16 variantes explícitas que requerían equivalencia: `CIUDAD CAPITAL` y 15 nombres municipales históricos, extendidos o erróneos. Las zonas capitalinas estaban además colocadas en `MUNICIPIO`. | 0 variantes conocidas sin resolver. Los municipios pasan el catálogo de 340 municipios y las modalidades semipresenciales se conservan separadas porque no son equivalentes. |
| Errores corregidos | 0; es el estado previo a las transformaciones. | Resumen: 23 filas vacías eliminadas; 70 distritos incompletos convertidos a NA; 258 teléfonos reformateados o invalidados; 9 valores formados solo por puntuación convertidos a NA; 1 prefijo decorativo corregido; 2,161 departamentos y 2,339 municipios normalizados; 2,161 zonas preservadas; 505 valores de `PLAN` y 2,026 de `DEPARTAMENTAL` normalizados. |

## Interpretación por métrica

### Registros

La reducción de 23 filas no elimina establecimientos: esas filas estaban vacías en las 17 variables y funcionaban como separadores de los archivos consolidados. Se conservan los 11,868 códigos MINEDUC únicos.

### Variables

La variable adicional evita una pérdida de información. En el crudo, `CIUDAD CAPITAL` no era un departamento oficial y `MUNICIPIO` contenía la zona. En el candidato, departamento y municipio se normalizan a `GUATEMALA`, mientras `ZONA_CAPITAL` conserva el valor `ZONA N`.

### Valores faltantes

El conteo preliminar de 4,219 celdas subestimaba las ausencias porque ignoraba puntos, `SIN DATO` y numerosas cadenas de signos. La revisión reproducible amplió el criterio a cualquier cadena sin caracteres alfanuméricos; el conteo confirmado es 4,645. El porcentaje bruto posterior aumenta por dos razones legítimas:

1. Se hacen explícitos como `NA` teléfonos y distritos incompletos que antes parecían texto válido.
2. `ZONA_CAPITAL` solo aplica a 2,161 registros y por diseño es `NA` en los otros 9,707.

Al comparar únicamente las 17 variables originales después de retirar las filas vacías, el candidato contiene 4,441 faltantes (2.20 %). No se imputaron datos sin evidencia.

### Duplicados

Las 22 repeticiones exactas desaparecen al quitar las filas estructurales. Para duplicados parciales se usa el mismo algoritmo antes y después: bloqueo geográfico, alta similitud de nombre, dirección o teléfono y coincidencia de los atributos que definen la unidad registral. La normalización descubre 12 pares adicionales. De los 781 pares candidatos, 781 quedaron conservados y 0 corregidos, fusionados o eliminados, porque un código oficial diferente no debe fusionarse sin confirmación de MINEDUC.

### Formatos, dominios y categorías

Los teléfonos admiten uno o más números completos de ocho dígitos separados por ` / `. Los distritos admiten los dos patrones completos observados. El catálogo contiene 22 departamentos y 340 municipios; todas las relaciones municipio-departamento del candidato son válidas. Las direcciones departamentales conservan subregiones legítimas como `GUATEMALA NORTE` y `QUICHE NORTE`.

Las 13 categorías de `PLAN` no se fusionaron: `SEMIPRESENCIAL`, `SEMIPRESENCIAL (FIN DE SEMANA)` y las frecuencias de uno o dos días representan modalidades distintas.

### Errores corregidos

Las correcciones se presentan por tipo de transformación y no como una suma total. Una misma fila o celda puede participar en varias normalizaciones, por lo que agregarlas produciría doble conteo. Los valores se obtienen del registro de transformaciones y se comprueban contra el candidato.

## Trazabilidad

- Reglas previas: `03_plan_limpieza.md`.
- Código reutilizable: `src/diagnostico.py`, `src/catalogos.py`, `src/limpieza_texto.py`, `src/duplicados.py`, `src/validadores.py`, `src/metricas_calidad.py` y `src/pipeline_limpieza.py`.
- Reproducción de las siete validaciones y las diez métricas: `notebooks/05_validacion.ipynb`.
- Transformaciones: `data/processed/transformaciones.csv`.
- Revisión caso por caso: `data/processed/duplicados_revisados.csv`.
- Candidato limpio: `data/processed/establecimientos_limpios_candidato.csv`.
- Dataset final validado: `data/processed/establecimientos_clean.csv` (11,868 × 18; SHA-256 `429468cb07a6e31aeb2a1d27611b0d82952a5c909f2b6a454fc03b12a1ec5b49`).
