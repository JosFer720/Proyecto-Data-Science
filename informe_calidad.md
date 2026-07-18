# Informe de Calidad de Datos

## Antes / Después

| Métrica | Antes | Después |
|---|---|---|
| Registros | 11,891. 11,868 sin contar las 23 filas 100% vacías. | |
| Variables | 17 | |
| Valores faltantes (# y %) | `DIRECTOR` 1,755 (14.76%). `TELEFONO` 969 (8.15%). `SUPERVISOR` 559 (4.70%). `DISTRITO` 556 (4.68%). `DIRECCION` 99 (0.83%). `ESTABLECIMIENTO` 28 (0.24%). El resto de columnas 23 (0.19%), correspondientes a las filas vacías. | |
| Variables con NA | Las 17 variables tienen al menos un faltante. | |
| Duplicados exactos | 22. Todas son las filas 100% vacías. 0 duplicados reales excluyéndolas. | |
| Posibles duplicados (parciales) | N/A, se detecta en Fase 4 con técnica de similitud. | |
| Variables con formato inconsistente | `TELEFONO`: 201 valores no puramente numéricos, longitudes de 2 a 30 caracteres cuando lo esperable son 8 dígitos. | |
| Variables con tipo incorrecto | Ninguna tipada aún, todo el CSV se lee como texto. `CODIGO` no es numérico por diseño, formato `NN-NN-NNNN-NN` correcto. | |
| Categorías inconsistentes | `DEPARTAMENTO` incluye `CIUDAD CAPITAL` en 2,161 filas, fuera del catálogo oficial de 22 departamentos. `MUNICIPIO` tiene 2,362 filas fuera de dominio, con zonas como `ZONA 1` y `ZONA 7` en vez de municipio, y variantes de escritura como `SAN MIGUEL USPANTAN` vs `USPANTAN`. `DEPARTAMENTO` y `DEPARTAMENTAL` no coinciden en 6,095 filas. `PLAN` tiene categorías de "semipresencial" posiblemente solapadas. | |
| Errores corregidos | N/A, se acumula durante la limpieza en Fase 4. | |
