## Metadatos del dataset

- **Fecha de extracción:** 2026-07-18.
- **Fuente:** buscador de establecimientos educativos del MINEDUC, `http://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/`.
- **Parámetros de búsqueda:** `NIVEL ESCOLAR: DIVERSIFICADO`, consultado para los 22 departamentos oficiales de Guatemala más `CIUDAD CAPITAL` (entidad separada de `GUATEMALA` en el buscador).

## Diccionario de variables

| Variable | Descripción | Tipo de dato | Dominio permitido / valores posibles | Tratamiento aplicado en limpieza | Variables derivadas |
|---|---|---|---|---|---|
| `CODIGO` | Identificador único del establecimiento, asignado por el MINEDUC. | Texto, formato `NN-NN-NNNN-NN` (departamento, distrito, secuencia, nivel). Sin excepciones al formato en el crudo. | Único por establecimiento. 23 registros sin código, correspondientes a filas separadoras vacías de la consolidación por departamento. | | |
| `DISTRITO` | Código del distrito educativo al que pertenece el establecimiento. | Texto, mismo patrón de guiones que `CODIGO`. | 1,681 valores únicos. 556 faltantes. | | |
| `DEPARTAMENTO` | Departamento donde se ubica el establecimiento. | Texto categórico. | 22 departamentos oficiales de Guatemala. Catálogo en `src/catalogos.py`. Fuera de dominio: el crudo incluye `CIUDAD CAPITAL` en 2,161 filas, valor que el buscador MINEDUC usa para separar la ciudad capital de `GUATEMALA`. Debe unificarse con `GUATEMALA` en la limpieza. | | |
| `MUNICIPIO` | Municipio donde se ubica el establecimiento. | Texto categórico. | Debe pertenecer al departamento de la misma fila. Catálogo en `src/catalogos.py`, pendiente de verificación oficial en Fase 5c. Fuera de dominio: 2,362 filas traen zonas de la ciudad (`ZONA 1`, `ZONA 7`, etc.) en vez de un municipio, además de variantes de escritura de municipios reales (`SAN MIGUEL USPANTAN` vs `USPANTAN`, `SANTO TOMAS CHICHICASTENANGO` vs `CHICHICASTENANGO`). | | |
| `ESTABLECIMIENTO` | Nombre del centro educativo. | Texto libre. | 6,312 valores únicos. 28 faltantes. Sin normalizar mayúsculas, tildes ni espacios todavía. | | |
| `DIRECCION` | Dirección física del establecimiento. | Texto libre. | 7,439 valores únicos. 99 faltantes. Formato libre, sin estructura consistente. | | |
| `TELEFONO` | Teléfono(s) de contacto del establecimiento. | Texto. Se espera numérico de 8 dígitos, estándar en Guatemala. | 969 faltantes (8.15%). Formato inconsistente: 201 valores no puramente numéricos, con varios teléfonos concatenados con `-` o `/`, y longitudes observadas de 2 a 30 caracteres. | | |
| `SUPERVISOR` | Nombre del supervisor educativo asignado. | Texto libre. | 1,280 valores únicos. 559 faltantes. | | |
| `DIRECTOR` | Nombre del director del establecimiento. | Texto libre. | 5,520 valores únicos. 1,755 faltantes (14.76%), la variable con más faltantes. | | |
| `NIVEL` | Nivel escolar del establecimiento. | Texto categórico. | Un único valor esperado, `DIVERSIFICADO`, por el filtro de descarga. 23 faltantes. | | |
| `SECTOR` | Sector administrativo del establecimiento. | Texto categórico. | 4 categorías: `OFICIAL`, `PRIVADO`, `COOPERATIVA`, `MUNICIPAL`. 23 faltantes. | | |
| `AREA` | Área geográfica del establecimiento. | Texto categórico. | 3 categorías: `URBANA`, `RURAL`, `SIN ESPECIFICAR` (esta última en 3 filas). 23 faltantes. | | |
| `STATUS` | Estado operativo del establecimiento. | Texto categórico. | 5 categorías: `ABIERTA`, `CERRADA TEMPORALMENTE`, `CERRADA DEFINITIVAMENTE`, `TEMPORAL TITULOS`, `TEMPORAL NOMBRAMIENTO`. 23 faltantes. | | |
| `MODALIDAD` | Modalidad lingüística del establecimiento. | Texto categórico. | 2 categorías: `MONOLINGUE`, `BILINGUE`. 23 faltantes. | | |
| `JORNADA` | Jornada en la que opera el establecimiento. | Texto categórico. | 6 categorías: `MATUTINA`, `VESPERTINA`, `NOCTURNA`, `DOBLE`, `INTERMEDIA`, `SIN JORNADA`. 23 faltantes. | | |
| `PLAN` | Plan o modalidad de estudios. | Texto categórico. | 13 categorías observadas. Varias parecen variantes solapadas de "semipresencial": `SEMIPRESENCIAL`, `SEMIPRESENCIAL (FIN DE SEMANA)`, `SEMIPRESENCIAL (UN DÍA A LA SEMANA)`, `SEMIPRESENCIAL (DOS DÍAS A LA SEMANA)`. Candidato a unificar. 23 faltantes. | | |
| `DEPARTAMENTAL` | Dirección Departamental de Educación asociada. Subregión administrativa del MINEDUC, no siempre igual al departamento. | Texto categórico. | 26 valores únicos. Inconsistente con `DEPARTAMENTO` en 6,095 filas: trae subregiones (`GUATEMALA NORTE`, `GUATEMALA SUR`, `GUATEMALA ORIENTE`, `GUATEMALA OCCIDENTE`) y nombres con tilde (`QUICHÉ`, `SOLOLÁ`, `PETÉN`, `SACATEPÉQUEZ`, `SUCHITEPÉQUEZ`, `TOTONICAPÁN`) que no calzan con `DEPARTAMENTO`. Decisión de qué hacer con esta columna pendiente del Plan de limpieza en Fase 3. 23 faltantes. | | |
