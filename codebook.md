# Libro de códigos

## Metadatos del conjunto

- **Fuente:** [Buscador de establecimientos educativos del MINEDUC](https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/).
- **Fecha de extracción:** 2026-07-18.
- **Filtro:** `NIVEL ESCOLAR = DIVERSIFICADO`.
- **Cobertura:** los 22 departamentos; el buscador consultó `CIUDAD CAPITAL` como entidad separada de `GUATEMALA`.
- **Versión final:** `v1.0.0`.
- **CSV crudo:** `data/raw/establecimientos_raw.csv`, 11,891 filas y 17 variables.
- **SHA-256 crudo:** `bbc1fa3b26b2509a22d547dc81dfa3b8bbc470f33c26b210de5b448d8d1a1d1c`.
- **CSV limpio candidato:** `data/processed/establecimientos_limpios_candidato.csv`, 11,868 filas y 18 variables.
- **SHA-256 del candidato:** `a337c8761a3d4636b4ba2f4584d91d4f9525c0ab2f145c96d4cb7a965168ff97`.
- **CSV limpio final:** `data/processed/establecimientos_clean.csv`, 11,868 filas y 18 variables, ordenadas establemente por `CODIGO`.
- **SHA-256 final:** `429468cb07a6e31aeb2a1d27611b0d82952a5c909f2b6a454fc03b12a1ec5b49`.
- **Discrepancia de referencia:** el hash `0364f39e…` incluido en la planificación no corresponde a los bytes del candidato presente. La huella real del candidato se recalculó arriba; el hash final se calcula después de ordenar y escribir el archivo final.
- **Catálogo geográfico:** Instituto Nacional de Estadística (INE), 22 departamentos y 340 municipios; implementado y citado en `src/catalogos.py`.

## Diccionario de variables

La columna “Valores posibles” describe el conjunto final. `NA` significa que la fuente no proporcionó un valor válido; no representa texto literal. En todos los campos, “MINEDUC” se refiere al Buscador de establecimientos educativos indicado en los metadatos.

| Variable | Descripción | Tipo de dato | Dominio permitido | Valores posibles | Tratamiento aplicado | Variables derivadas | Fecha de extracción | Fuente | Versión del conjunto limpio |
|---|---|---|---|---|---|---|---|---|---|
| `CODIGO` | Identificador oficial del establecimiento asignado por MINEDUC. | Texto (`string`) | Patrón `NN-NN-NNNN-NN`; no nulo; único. | 11,868 códigos únicos. | Se conservaron ceros y guiones; se validó el patrón. Las 23 ausencias pertenecían a filas estructurales eliminadas. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `DISTRITO` | Código del distrito educativo. | Texto (`string`) | `NN-NNN`, `NN-NN-NNNN` o `NA`. | 1,678 códigos válidos observados; 603 registros `NA`. | Se conservaron los dos formatos completos usados por la fuente; 70 valores incompletos como `01-` pasaron a `NA`. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `DEPARTAMENTO` | Departamento oficial donde se ubica el establecimiento. | Texto categórico (`string`) | Los 22 departamentos definidos en `src/catalogos.py`; no nulo. | 22 departamentos. | Se normalizó escritura y `CIUDAD CAPITAL` se convirtió a `GUATEMALA` en 2,161 registros. | Origina `ZONA_CAPITAL` junto con `MUNICIPIO`. | 2026-07-18 | MINEDUC + catálogo INE | `v1.0.0` |
| `MUNICIPIO` | Municipio oficial correspondiente al departamento. | Texto categórico (`string`) | Uno de los 340 municipios y perteneciente al departamento de la fila; no nulo. | 330 municipios presentes, validados contra `src/catalogos.py`. | Las zonas capitalinas se asignaron al municipio `GUATEMALA`; se aplicaron 15 equivalencias documentadas de nombres históricos, extendidos o erróneos. | Origina `ZONA_CAPITAL` cuando la consulta original fue `CIUDAD CAPITAL`. | 2026-07-18 | MINEDUC + catálogo INE | `v1.0.0` |
| `ZONA_CAPITAL` | Zona reportada por el buscador para establecimientos de Ciudad de Guatemala. | Texto categórico (`string`) | `ZONA 1` a `ZONA 25` cuando fue informada, o `NA`. | 22 zonas observadas; 2,161 registros informados y 9,707 `NA`. | Se derivó antes de convertir departamento y municipio a `GUATEMALA`; no se infirió desde direcciones. | Variable derivada de `DEPARTAMENTO` y `MUNICIPIO` originales. | 2026-07-18 | Derivada de MINEDUC | `v1.0.0` |
| `ESTABLECIMIENTO` | Nombre del centro educativo. | Texto (`string`) | Texto normalizado o `NA`. | 6,312 valores no nulos observados; 5 registros `NA`. | Se unificaron Unicode, mayúsculas y espacios; se conservaron tildes y palabras. No se corrigieron nombres por similitud. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `DIRECCION` | Dirección física informada por el establecimiento. | Texto (`string`) | Texto normalizado o `NA`. | 7,431 valores distintos no nulos; 89 registros `NA`. | Los valores formados solo por puntuación pasaron a `NA`; se normalizaron Unicode, mayúsculas y espacios sin geocodificar. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `TELEFONO` | Uno o más teléfonos de contacto. | Texto (`string`) | Cada número cumple `[2-7]NNNNNNN`; múltiples números se separan con ` / `; puede ser `NA`. | 1 o más números de 8 dígitos; 1,063 registros `NA`. | Se extrajeron solo números completos, se eliminaron repeticiones dentro de la celda y no se infirieron dígitos faltantes. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `SUPERVISOR` | Nombre del supervisor educativo informado. | Texto (`string`) | Texto normalizado o `NA`. | 1,279 valores distintos no nulos; 539 registros `NA`. | Los valores sin caracteres alfanuméricos pasaron a `NA`; se normalizaron Unicode, mayúsculas y espacios, conservando las tildes. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `DIRECTOR` | Nombre del director informado. | Texto (`string`) | Texto normalizado o `NA`. | 5,489 valores distintos no nulos; 2,142 registros `NA`. | `SIN DATO` y valores formados solo por puntuación se convirtieron a `NA`; se retiró un prefijo decorativo de guiones sin modificar el nombre. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `NIVEL` | Nivel escolar de la consulta. | Texto categórico (`string`) | `DIVERSIFICADO`; no nulo. | `DIVERSIFICADO`. | Se verificó el filtro después de eliminar las filas vacías. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `SECTOR` | Sector administrativo del establecimiento. | Texto categórico (`string`) | `OFICIAL`, `PRIVADO`, `COOPERATIVA`, `MUNICIPAL`; no nulo. | 4 categorías. | Se normalizaron Unicode, mayúsculas y espacios; no fue necesario unificar categorías. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `AREA` | Área geográfica declarada por la fuente. | Texto categórico (`string`) | `URBANA`, `RURAL`, `SIN ESPECIFICAR`; no nulo. | 3 categorías. | Se conservó `SIN ESPECIFICAR` como categoría explícita, no como faltante. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `STATUS` | Estado operativo del establecimiento. | Texto categórico (`string`) | `ABIERTA`, `CERRADA TEMPORALMENTE`, `CERRADA DEFINITIVAMENTE`, `TEMPORAL TITULOS`, `TEMPORAL NOMBRAMIENTO`; no nulo. | 5 categorías. | Se normalizó el formato y se conservaron todos los estados semánticamente distintos. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `MODALIDAD` | Modalidad lingüística del establecimiento. | Texto categórico (`string`) | `MONOLINGUE`, `BILINGUE`; no nulo. | 2 categorías. | Se normalizó a mayúsculas sin tildes para evitar variantes de escritura. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `JORNADA` | Jornada en la que opera el registro educativo. | Texto categórico (`string`) | `MATUTINA`, `VESPERTINA`, `NOCTURNA`, `DOBLE`, `INTERMEDIA`, `SIN JORNADA`; no nulo. | 6 categorías. | Se conservó `SIN JORNADA` como categoría declarada, no como faltante. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `PLAN` | Plan o modalidad temporal de estudios. | Texto categórico (`string`) | Las 13 categorías observadas y documentadas; no nulo. | `DIARIO(REGULAR)`, `FIN DE SEMANA`, cuatro modalidades semipresenciales diferenciadas y otras siete categorías. | Se normalizaron 505 valores con tildes; no se fusionaron las modalidades semipresenciales porque expresan frecuencias distintas. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |
| `DEPARTAMENTAL` | Dirección Departamental de Educación responsable; puede ser una subregión. | Texto categórico (`string`) | 26 valores observados, incluidos `GUATEMALA NORTE/SUR/ORIENTE/OCCIDENTE` y `QUICHE NORTE`; no nulo. | 26 categorías. | Se normalizaron 2,026 valores con tildes. Se validó igualdad con el departamento o prefijo administrativo permitido, sin eliminar subregiones. | No aplica. | 2026-07-18 | MINEDUC | `v1.0.0` |

## Reglas de identidad y duplicados

- `CODIGO` es la clave de la unidad registral y es único en el conjunto final.
- Dos filas con nombre, dirección o teléfono similares no se fusionan si poseen códigos MINEDUC diferentes sin confirmación explícita de la fuente.
- Los 781 pares candidatos quedaron documentados individualmente en `data/processed/duplicados_revisados.csv`; todos se conservaron en esta versión.
- Las 23 filas completamente vacías del CSV crudo se eliminaron porque eran separadores sin establecimiento asociado.

## Anexo de reglas de validación

Las reglas se ejecutan desde `src/validadores.py` y se verifican con `pytest`, `05_validacion.ipynb` y `06_dataset_final.ipynb`. El conjunto final supera las siete comprobaciones con cero errores.

| Variable | Tipo esperado | Nulabilidad | Regla automática principal |
|---|---|---|---|
| `CODIGO` | `string` | No permite `NA` | Patrón `NN-NN-NNNN-NN`, valor único y sin duplicados. |
| `DISTRITO` | `string` | Permite `NA` | Patrón `NN-NNN` o `NN-NN-NNNN` cuando está informado. |
| `DEPARTAMENTO` | `string` | No permite `NA` | Pertenece al catálogo de 22 departamentos. |
| `MUNICIPIO` | `string` | No permite `NA` | Pertenece al catálogo de 340 municipios y al departamento de la fila. |
| `ZONA_CAPITAL` | `string` | Permite `NA` | Patrón `ZONA 1` a `ZONA 25`; si existe, departamento y municipio deben ser `GUATEMALA`. |
| `ESTABLECIMIENTO` | `string` | Permite `NA` | Sin espacios extremos/múltiples, centinelas literales ni puntuación residual. |
| `DIRECCION` | `string` | Permite `NA` | Sin espacios extremos/múltiples, centinelas literales ni puntuación residual. |
| `TELEFONO` | `string` | Permite `NA` | Uno o más números de ocho dígitos iniciados entre 2 y 7, separados por ` / `. |
| `SUPERVISOR` | `string` | Permite `NA` | Sin espacios extremos/múltiples, centinelas literales ni puntuación residual. |
| `DIRECTOR` | `string` | Permite `NA` | Sin espacios extremos/múltiples, centinelas literales ni puntuación residual. |
| `NIVEL` | `string` | No permite `NA` | Únicamente `DIVERSIFICADO`. |
| `SECTOR` | `string` | No permite `NA` | Una de las cuatro categorías documentadas. |
| `AREA` | `string` | No permite `NA` | `URBANA`, `RURAL` o `SIN ESPECIFICAR`. |
| `STATUS` | `string` | No permite `NA` | Uno de los cinco estados documentados. |
| `MODALIDAD` | `string` | No permite `NA` | `MONOLINGUE` o `BILINGUE`. |
| `JORNADA` | `string` | No permite `NA` | Una de las seis jornadas documentadas. |
| `PLAN` | `string` | No permite `NA` | Una de las trece categorías documentadas, sin fusionar frecuencias semipresenciales. |
| `DEPARTAMENTAL` | `string` | No permite `NA` | Una de las 26 direcciones permitidas y consistente con `DEPARTAMENTO`. |

Además del esquema por variable, la suite comprueba duplicados exactos y categorías equivalentes que solo difieran en mayúsculas, tildes, espacios o puntuación. Cada fallo reporta hasta cinco ejemplos con índice, código, variable, valor y regla incumplida.

## Historial de contribuciones verificable

La atribución se limita a evidencia del historial Git y al estado actual del árbol; no se infieren autores para trabajo sin commit.

- **Persona A — JosFer720:** estructura, entorno, obtención, diagnóstico inicial y metadatos del dataset, según los commits `1a626aa`, `f6df659`, `faaa03c` y `8053846`.
- **Persona B — Joel Jaquez:** planificación, pipeline de limpieza, candidato, trazabilidad de transformaciones/duplicados y automatización inicial de notebooks, según los commits entre `dfdf0e2` y `99b8711`.
- **Persona C — Jose Galindo (Home):** correcciones residuales, validaciones automáticas e informe reproducible Antes/Después, según `51c1dd2`, `dfad986` y `05c0333`.
- **Persona D:** trabajo actual aún no atribuido por commit: esquema y exportador final, pruebas de entrega, edición final de este libro, PDF, `06_dataset_final.ipynb`, CSV `v1.0.0` y actualización final del README. No se inventa un nombre personal para esta contribución.
