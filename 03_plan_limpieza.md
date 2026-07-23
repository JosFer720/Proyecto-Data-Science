# Plan de limpieza

Este documento se definió antes de generar el conjunto limpio candidato. Incluye las 17 variables originales, aunque algunas no necesitan una corrección sustantiva. Las reglas priorizan trazabilidad, conservación del significado y ausencia de inferencias no respaldadas por la fuente.

## Principios generales

- Los marcadores vacíos (`""`, `N/A`, `NULL`, guiones, puntos, `SIN DATO` y equivalentes) se convierten a un único valor faltante `NA`. Una cadena sin caracteres alfanuméricos también se considera ausencia, aunque combine signos y espacios.
- Los códigos y teléfonos se mantienen como texto para conservar ceros iniciales.
- Los textos se normalizan con Unicode NFKC, eliminación de caracteres invisibles, espacios extremos/múltiples y mayúsculas.
- Las tildes se conservan en nombres y direcciones. En categorías y geografía se comparan sin tildes para evitar falsos valores distintos.
- No se imputan nombres, direcciones, teléfonos ni responsables desconocidos.
- No se elimina ningún posible duplicado parcial solo por similitud. Cada par conserva una decisión y justificación.
- Toda transformación se resume en `data/processed/transformaciones.csv`.

## Reglas por variable

| Variable | Problema encontrado | Regla de corrección o “sin transformación” | Por qué funcionará | Riesgos y mitigación |
|---|---|---|---|---|
| `CODIGO` | 23 faltantes pertenecientes a filas totalmente vacías; los 11,868 valores reales cumplen `NN-NN-NNNN-NN`. | Eliminar únicamente las filas completamente vacías; validar el patrón y conservar como texto. | El código es el identificador oficial y no necesita recodificación. | Convertirlo a número eliminaría ceros; se conserva como `string`. |
| `DISTRITO` | Faltantes y tres representaciones: `NN-NNN`, `NN-NN-NNNN` y valores incompletos como `01-`. | Aceptar los dos patrones completos observados; convertir los incompletos a `NA`; conservar como texto. | Reconoce los dos formatos utilizados por la fuente sin inventar componentes. | Un código antiguo podría parecer incompleto; queda como `NA` y no se reconstruye sin fuente. |
| `DEPARTAMENTO` | `CIUDAD CAPITAL` aparece como entidad del buscador, pero no es uno de los 22 departamentos. | Normalizar escritura y reemplazar `CIUDAD CAPITAL` por `GUATEMALA`. | Alinea el campo con el catálogo oficial de 22 departamentos. | Se perdería la distinción de capital; se conserva mediante `ZONA_CAPITAL` y el municipio `GUATEMALA`. |
| `MUNICIPIO` | Las filas de capital contienen zonas; existen nombres históricos, extendidos o con errores y el catálogo anterior omitía cuatro municipios oficiales. | Completar el catálogo a 340 municipios; convertir zonas capitalinas a municipio `GUATEMALA`; aplicar un mapa explícito de equivalencias y validar municipio-departamento. | Todas las correcciones tienen destino oficial y la zona se conserva aparte. | Una equivalencia incorrecta alteraría geografía; el mapa queda visible en `src/pipeline_limpieza.py`. |
| `ESTABLECIMIENTO` | Faltantes residuales y variantes por tildes/espaciado; texto libre de alta cardinalidad. | Convertir centinelas a `NA`, normalizar Unicode, espacios y mayúsculas; conservar tildes y palabras. | Elimina diferencias cosméticas sin modificar el nombre institucional. | No se corrigen supuestas faltas ortográficas automáticamente; se usan solo para detectar candidatos duplicados. |
| `DIRECCION` | Faltantes, puntos usados como ausencia y formato libre. | Convertir centinelas a `NA`; normalizar Unicode, espacios y mayúsculas; no dividir ni geocodificar. | Produce representación consistente sin inventar componentes de dirección. | Direcciones equivalentes pueden seguir redactadas distinto; se evalúan mediante similitud. |
| `TELEFONO` | Faltantes, longitudes de 2–30 caracteres, teléfonos múltiples, letras y números incompletos. | Extraer únicamente secuencias completas de 8 dígitos que inicien entre 2 y 7; eliminar repetidos y separar múltiples teléfonos con ` / `; si no hay ninguno completo, usar `NA`. | Cumple el formato telefónico esperado y evita inferir dígitos. | Puede descartarse un teléfono histórico de 7 dígitos; se documenta como inválido en vez de completarlo arbitrariamente. |
| `SUPERVISOR` | Faltantes y variantes por tildes; texto libre. | Convertir centinelas a `NA`; normalizar Unicode, espacios y mayúsculas; conservar tildes. | Uniforma formato sin afirmar que dos nombres parecidos son la misma persona. | Permanecen variantes ortográficas legítimas; no se fusionan automáticamente. |
| `DIRECTOR` | Mayor cantidad de faltantes; además usa series de guiones, puntuación aislada y `SIN DATO`; un nombre contiene guiones decorativos iniciales. | Convertir centinelas y cadenas sin caracteres alfanuméricos a `NA`; retirar series de guiones antepuestas a un nombre y normalizar el resto. | Corrige la subestimación de faltantes y la puntuación innecesaria sin alterar el contenido del nombre. | No se imputan responsables ni se eliminan guiones internos legítimos. |
| `NIVEL` | Un único valor real esperado; los faltantes pertenecen a filas vacías. | Eliminar filas vacías, normalizar y validar que todos los registros sean `DIVERSIFICADO`. | Confirma el filtro solicitado por el proyecto. | Ninguno relevante; cualquier otro valor debe detener la validación. |
| `SECTOR` | Cuatro categorías válidas y faltantes estructurales. | Normalizar escritura y validar `OFICIAL`, `PRIVADO`, `COOPERATIVA`, `MUNICIPAL`. | Es un dominio estable y cerrado. | Una categoría nueva de la fuente requeriría actualizar el dominio, no descartarla silenciosamente. |
| `AREA` | Incluye `SIN ESPECIFICAR` en tres registros. | Conservar `URBANA`, `RURAL` y `SIN ESPECIFICAR`; normalizar escritura. | `SIN ESPECIFICAR` es una categoría informativa, no un faltante automático. | Tratarla como NA perdería la declaración explícita de la fuente. |
| `STATUS` | Cinco categorías válidas; `TEMPORAL TITULOS` y `TEMPORAL NOMBRAMIENTO` son estados específicos. | Normalizar escritura y conservar las cinco categorías. | Evita fusionar estados operativos con significados distintos. | Cambios futuros del catálogo requieren revisión del dominio. |
| `MODALIDAD` | Dos categorías válidas con posible diferencia de tildes. | Normalizar a `MONOLINGUE` y `BILINGUE`, sin tildes para comparación. | Mantiene el dominio observado y evita duplicados por acentuación. | La forma gráfica pierde tilde, pero no el significado. |
| `JORNADA` | Seis categorías válidas, incluida `SIN JORNADA`. | Normalizar escritura y conservar las seis categorías. | `SIN JORNADA` es una categoría declarada, no ausencia de dato. | No debe convertirse a NA porque cambiaría el significado de la fuente. |
| `PLAN` | Trece categorías; cuatro contienen “SEMIPRESENCIAL” pero describen frecuencias diferentes. | Normalizar espacios, mayúsculas y tildes para comparación; conservar las 13 categorías semánticamente distintas. | Evita la unificación incorrecta que perdería modalidad/frecuencia. | Podrían existir equivalencias administrativas no documentadas; se requiere fuente antes de fusionarlas. |
| `DEPARTAMENTAL` | 26 valores: departamentos, cuatro subregiones de Guatemala y `QUICHE NORTE`; diferencias de tildes respecto a `DEPARTAMENTO`. | Normalizar a mayúsculas sin tildes y validar relación permitida: igualdad o prefijo del departamento (`GUATEMALA NORTE`, `QUICHE NORTE`, etc.). | Reconoce que la Dirección Departamental es una división administrativa distinta. | Forzar igualdad eliminaría subregiones legítimas; se conserva el valor específico. |

## Variable derivada

| Variable | Cálculo | Utilidad | Riesgo |
|---|---|---|---|
| `ZONA_CAPITAL` | Copiar `MUNICIPIO` cuando el departamento original sea `CIUDAD CAPITAL` y el valor cumpla `ZONA N`; usar `NA` en los demás registros. | Conserva la zona después de normalizar departamento y municipio a `GUATEMALA`. | Solo representa zonas reportadas por la fuente; no se infiere a partir de direcciones. |

## Duplicados

- Los duplicados exactos se calculan sobre todas las columnas. Las 23 filas vacías se eliminan porque son separadores, no establecimientos.
- Los candidatos parciales se bloquean por departamento, municipio y prefijo del nombre, y también por teléfono dentro del mismo municipio.
- Se exige alta similitud del nombre y coincidencia de dirección o teléfono, además de la misma unidad registral (`NIVEL`, `SECTOR`, `AREA`, `STATUS`, `MODALIDAD`, `JORNADA`, `PLAN` y `DEPARTAMENTAL`).
- Cada candidato se documenta en `data/processed/duplicados_revisados.csv` con nivel de coincidencia, evidencia específica, decisión y justificación individual.
- Un código MINEDUC distinto se conserva como unidad registral distinta salvo confirmación expresa de la fuente que autorice fusionar o eliminar.
