from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src import catalogos
from src.diagnostico import SENTINELAS_FALTANTES
from src.limpieza_texto import (
    PATRON_CODIGO,
    PATRON_DISTRITO,
    PATRON_TELEFONO,
    normalizar_texto,
)


COLUMNAS_REQUERIDAS = [
    "CODIGO",
    "DISTRITO",
    "DEPARTAMENTO",
    "MUNICIPIO",
    "ZONA_CAPITAL",
    "ESTABLECIMIENTO",
    "DIRECCION",
    "TELEFONO",
    "SUPERVISOR",
    "DIRECTOR",
    "NIVEL",
    "SECTOR",
    "AREA",
    "STATUS",
    "MODALIDAD",
    "JORNADA",
    "PLAN",
    "DEPARTAMENTAL",
]

COLUMNAS_TEXTO_LIBRE = ["ESTABLECIMIENTO", "DIRECCION", "SUPERVISOR", "DIRECTOR"]
COLUMNAS_CATEGORICAS = [
    "DEPARTAMENTO",
    "MUNICIPIO",
    "ZONA_CAPITAL",
    "NIVEL",
    "SECTOR",
    "AREA",
    "STATUS",
    "MODALIDAD",
    "JORNADA",
    "PLAN",
    "DEPARTAMENTAL",
]
COLUMNAS_NO_NULAS = {
    "CODIGO",
    "DEPARTAMENTO",
    "MUNICIPIO",
    "NIVEL",
    "SECTOR",
    "AREA",
    "STATUS",
    "MODALIDAD",
    "JORNADA",
    "PLAN",
    "DEPARTAMENTAL",
}

PLANES_VALIDOS = {
    "A DISTANCIA",
    "DIARIO(REGULAR)",
    "DOMINICAL",
    "FIN DE SEMANA",
    "INTERCALADO",
    "IRREGULAR",
    "MIXTO",
    "SABATINO",
    "SEMIPRESENCIAL",
    "SEMIPRESENCIAL (DOS DIAS A LA SEMANA)",
    "SEMIPRESENCIAL (FIN DE SEMANA)",
    "SEMIPRESENCIAL (UN DIA A LA SEMANA)",
    "VIRTUAL A DISTANCIA",
}

DEPARTAMENTALES_VALIDAS = (
    set(catalogos.DEPARTAMENTOS_OFICIALES)
    - {"GUATEMALA"}
    | {
        "GUATEMALA NORTE",
        "GUATEMALA OCCIDENTE",
        "GUATEMALA ORIENTE",
        "GUATEMALA SUR",
        "QUICHE NORTE",
    }
)

DOMINIOS_CATEGORICOS = {
    "DEPARTAMENTO": set(catalogos.DEPARTAMENTOS_OFICIALES),
    "NIVEL": {"DIVERSIFICADO"},
    "SECTOR": {"OFICIAL", "PRIVADO", "COOPERATIVA", "MUNICIPAL"},
    "AREA": {"URBANA", "RURAL", "SIN ESPECIFICAR"},
    "STATUS": {
        "ABIERTA",
        "CERRADA TEMPORALMENTE",
        "CERRADA DEFINITIVAMENTE",
        "TEMPORAL TITULOS",
        "TEMPORAL NOMBRAMIENTO",
    },
    "MODALIDAD": {"MONOLINGUE", "BILINGUE"},
    "JORNADA": {
        "MATUTINA",
        "VESPERTINA",
        "NOCTURNA",
        "DOBLE",
        "INTERMEDIA",
        "SIN JORNADA",
    },
    "PLAN": PLANES_VALIDOS,
    "DEPARTAMENTAL": DEPARTAMENTALES_VALIDAS,
}


@dataclass(frozen=True)
class ResultadoValidacion:
    prueba: str
    aprobada: bool
    errores: int
    detalle: str
    ejemplos: tuple[dict[str, object], ...] = ()

    @property
    def estado(self) -> str:
        return "APROBADO" if self.aprobada else "FALLIDO"


def cargar_csv_para_validacion(path: str | Path) -> pd.DataFrame:
    """Carga texto sin ocultar marcadores literales como N/A o NULL."""
    df = pd.read_csv(path, dtype="string", keep_default_na=False)
    return df.mask(df.eq("")).astype("string")


def es_codigo_valido(valor: object) -> bool:
    return pd.isna(valor) or bool(PATRON_CODIGO.fullmatch(str(valor)))


def es_distrito_valido(valor: object) -> bool:
    return pd.isna(valor) or bool(PATRON_DISTRITO.fullmatch(str(valor)))


def es_telefono_valido(valor: object) -> bool:
    if pd.isna(valor):
        return True
    telefonos = str(valor).split(" / ")
    return bool(telefonos) and all(PATRON_TELEFONO.fullmatch(tel) for tel in telefonos)


def tiene_espacios_extra(valor: object) -> bool:
    if pd.isna(valor):
        return False
    texto = str(valor)
    return texto != texto.strip() or bool(re.search(r"\s{2,}", texto))


def es_texto_residual_invalido(valor: object) -> bool:
    if pd.isna(valor):
        return False
    texto = str(valor).strip()
    return bool(re.fullmatch(r"[\W_]+", texto)) or bool(
        re.match(r"^-{2,}\s*\w", texto)
    )


def es_departamental_consistente(departamento: object, departamental: object) -> bool:
    if pd.isna(departamento) or pd.isna(departamental):
        return True
    depto = catalogos.normalizar_nombre_geografico(str(departamento))
    direccion = catalogos.normalizar_nombre_geografico(str(departamental))
    return direccion == depto or direccion.startswith(f"{depto} ")


def _valor_serializable(valor: object) -> object:
    return None if pd.isna(valor) else valor


def _ejemplos_celdas(
    df: pd.DataFrame,
    hallazgos: list[tuple[int, str, str]],
    max_ejemplos: int,
) -> tuple[dict[str, object], ...]:
    ejemplos = []
    for indice, variable, regla in hallazgos[:max_ejemplos]:
        ejemplos.append(
            {
                "indice": int(indice),
                "codigo": _valor_serializable(df.at[indice, "CODIGO"])
                if "CODIGO" in df
                else None,
                "variable": variable,
                "valor": _valor_serializable(df.at[indice, variable]),
                "regla": regla,
            }
        )
    return tuple(ejemplos)


def _resultado(
    prueba: str,
    errores: int,
    detalle: str,
    ejemplos: tuple[dict[str, object], ...] = (),
) -> ResultadoValidacion:
    return ResultadoValidacion(prueba, errores == 0, int(errores), detalle, ejemplos)


def _validar_duplicados(df: pd.DataFrame, max_ejemplos: int) -> ResultadoValidacion:
    repetidos = df.duplicated(keep=False)
    errores = int(df.duplicated().sum())
    columnas = [col for col in ["CODIGO", "ESTABLECIMIENTO", "DIRECCION"] if col in df]
    ejemplos = tuple(
        {"indice": int(indice), **{col: _valor_serializable(df.at[indice, col]) for col in columnas}}
        for indice in df.index[repetidos][:max_ejemplos]
    )
    return _resultado(
        "Duplicados exactos",
        errores,
        "No deben existir filas idénticas en todas las variables.",
        ejemplos,
    )


def _validar_espacios(df: pd.DataFrame, max_ejemplos: int) -> ResultadoValidacion:
    hallazgos = []
    for columna in df.select_dtypes(include=["object", "string"]).columns:
        for indice in df.index[df[columna].map(tiene_espacios_extra)]:
            hallazgos.append((indice, columna, "espacios extremos o múltiples"))
    return _resultado(
        "Espacios en textos",
        len(hallazgos),
        "Los textos no deben tener espacios al inicio, al final ni secuencias múltiples.",
        _ejemplos_celdas(df, hallazgos, max_ejemplos),
    )


def _validar_telefonos(df: pd.DataFrame, max_ejemplos: int) -> ResultadoValidacion:
    if "TELEFONO" not in df:
        return _resultado("Formato de teléfonos", 1, "Falta la columna TELEFONO.")
    invalidos = ~df["TELEFONO"].map(es_telefono_valido)
    hallazgos = [
        (indice, "TELEFONO", "uno o más números de 8 dígitos separados por ' / '")
        for indice in df.index[invalidos]
    ]
    return _resultado(
        "Formato de teléfonos",
        len(hallazgos),
        "Cada teléfono debe tener 8 dígitos, iniciar entre 2 y 7, o ser NA.",
        _ejemplos_celdas(df, hallazgos, max_ejemplos),
    )


def _validar_geografia(df: pd.DataFrame, max_ejemplos: int) -> ResultadoValidacion:
    requeridas = {"DEPARTAMENTO", "MUNICIPIO"}
    if not requeridas.issubset(df.columns):
        ausentes = sorted(requeridas - set(df.columns))
        return _resultado(
            "Geografía oficial",
            len(ausentes),
            f"Faltan columnas geográficas: {', '.join(ausentes)}.",
        )
    hallazgos = []
    for indice, fila in df[["DEPARTAMENTO", "MUNICIPIO"]].iterrows():
        departamento, municipio = fila["DEPARTAMENTO"], fila["MUNICIPIO"]
        if pd.isna(departamento) or not catalogos.es_departamento_valido(departamento):
            hallazgos.append((indice, "DEPARTAMENTO", "departamento oficial no nulo"))
        if (
            pd.isna(municipio)
            or pd.isna(departamento)
            or not catalogos.es_municipio_valido(municipio, departamento)
        ):
            hallazgos.append((indice, "MUNICIPIO", "municipio oficial del departamento"))
    return _resultado(
        "Geografía oficial",
        len(hallazgos),
        "Departamento y municipio deben pertenecer al catálogo y ser consistentes entre sí.",
        _ejemplos_celdas(df, hallazgos, max_ejemplos),
    )


def _validar_esquema_tipos(df: pd.DataFrame, max_ejemplos: int) -> ResultadoValidacion:
    problemas = []
    ausentes = [col for col in COLUMNAS_REQUERIDAS if col not in df]
    extras = [col for col in df.columns if col not in COLUMNAS_REQUERIDAS]
    if list(df.columns) != COLUMNAS_REQUERIDAS:
        problemas.append(
            {
                "regla": "columnas y orden esperados",
                "ausentes": ausentes,
                "extras": extras,
                "orden_observado": list(df.columns),
            }
        )
    for columna in df.columns:
        if columna in COLUMNAS_REQUERIDAS and not isinstance(df[columna].dtype, pd.StringDtype):
            problemas.append(
                {
                    "variable": columna,
                    "regla": "tipo string",
                    "tipo_observado": str(df[columna].dtype),
                }
            )
    return _resultado(
        "Esquema y tipos",
        len(problemas),
        "El candidato debe contener las 18 columnas esperadas, en orden y con tipo string.",
        tuple(problemas[:max_ejemplos]),
    )


def _clave_categoria(valor: object) -> str:
    texto = normalizar_texto(valor, quitar_tildes=True)
    return re.sub(r"[\W_]+", " ", texto).strip()


def _validar_categorias_equivalentes(
    df: pd.DataFrame, max_ejemplos: int
) -> ResultadoValidacion:
    problemas = []
    for columna in COLUMNAS_CATEGORICAS:
        if columna not in df:
            continue
        grupos: dict[str, set[str]] = {}
        for valor in df[columna].dropna().unique():
            grupos.setdefault(_clave_categoria(valor), set()).add(str(valor))
        for clave, variantes in grupos.items():
            if len(variantes) > 1:
                problemas.append(
                    {"variable": columna, "clave_normalizada": clave, "variantes": sorted(variantes)}
                )
    return _resultado(
        "Categorías equivalentes",
        len(problemas),
        "No deben coexistir categorías que solo difieran en tildes, mayúsculas, espacios o puntuación.",
        tuple(problemas[:max_ejemplos]),
    )


def _validar_valores_invalidos(df: pd.DataFrame, max_ejemplos: int) -> ResultadoValidacion:
    hallazgos: list[tuple[int, str, str]] = []
    if "CODIGO" in df:
        codigo_invalido = df["CODIGO"].isna() | ~df["CODIGO"].map(es_codigo_valido)
        codigo_repetido = df["CODIGO"].notna() & df["CODIGO"].duplicated(keep=False)
        for indice in df.index[codigo_invalido | codigo_repetido]:
            hallazgos.append((indice, "CODIGO", "código válido, no nulo y único"))
    if "DISTRITO" in df:
        for indice in df.index[~df["DISTRITO"].map(es_distrito_valido)]:
            hallazgos.append((indice, "DISTRITO", "distrito válido o NA"))

    for columna in df.select_dtypes(include=["object", "string"]).columns:
        for indice, valor in df[columna].dropna().items():
            normalizado = normalizar_texto(valor)
            if normalizado in SENTINELAS_FALTANTES or (
                columna in COLUMNAS_TEXTO_LIBRE and es_texto_residual_invalido(valor)
            ):
                hallazgos.append((indice, columna, "sin centinelas ni puntuación residual"))

    for columna, dominio in DOMINIOS_CATEGORICOS.items():
        if columna not in df:
            continue
        invalidos = ~df[columna].isin(dominio)
        if columna not in COLUMNAS_NO_NULAS:
            invalidos &= df[columna].notna()
        for indice in df.index[invalidos]:
            hallazgos.append((indice, columna, "valor dentro del dominio documentado"))

    for columna in COLUMNAS_NO_NULAS:
        if columna in df:
            for indice in df.index[df[columna].isna()]:
                hallazgos.append((indice, columna, "valor obligatorio no nulo"))

    if "ZONA_CAPITAL" in df:
        zona_invalida = df["ZONA_CAPITAL"].notna() & ~df["ZONA_CAPITAL"].str.fullmatch(
            r"ZONA (?:[1-9]|1\d|2[0-5])", na=False
        )
        zona_inconsistente = df["ZONA_CAPITAL"].notna() & (
            df["DEPARTAMENTO"].ne("GUATEMALA") | df["MUNICIPIO"].ne("GUATEMALA")
        )
        for indice in df.index[zona_invalida | zona_inconsistente]:
            hallazgos.append((indice, "ZONA_CAPITAL", "zona 1-25 asociada a Guatemala"))

    if {"DEPARTAMENTO", "DEPARTAMENTAL"}.issubset(df.columns):
        for indice, (departamento, departamental) in enumerate(
            zip(df["DEPARTAMENTO"], df["DEPARTAMENTAL"])
        ):
            if not es_departamental_consistente(departamento, departamental):
                hallazgos.append(
                    (df.index[indice], "DEPARTAMENTAL", "dirección departamental consistente")
                )

    return _resultado(
        "Valores inválidos diagnosticados",
        len(hallazgos),
        "Códigos, distritos, dominios, faltantes obligatorios y relaciones deben cumplir las reglas documentadas.",
        _ejemplos_celdas(df, hallazgos, max_ejemplos),
    )


def ejecutar_validaciones(
    df: pd.DataFrame, *, max_ejemplos: int = 5
) -> list[ResultadoValidacion]:
    """Ejecuta, en orden, las siete comprobaciones exigidas por el proyecto."""
    if max_ejemplos < 0:
        raise ValueError("max_ejemplos debe ser mayor o igual a cero")
    validaciones = [
        _validar_duplicados,
        _validar_espacios,
        _validar_telefonos,
        _validar_geografia,
        _validar_esquema_tipos,
        _validar_categorias_equivalentes,
        _validar_valores_invalidos,
    ]
    return [validacion(df, max_ejemplos) for validacion in validaciones]


def resumen_validaciones(resultados: list[ResultadoValidacion]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Prueba": resultado.prueba,
                "Estado": resultado.estado,
                "Errores": resultado.errores,
                "Detalle": resultado.detalle,
            }
            for resultado in resultados
        ]
    )


def contar_errores_calidad(df: pd.DataFrame) -> dict[str, int]:
    """Conserva el resumen usado por la limpieza y amplía su cobertura."""
    columnas_texto = list(df.select_dtypes(include=["object", "string"]).columns)
    errores_espacios = sum(
        int(df[columna].map(tiene_espacios_extra).sum()) for columna in columnas_texto
    )
    errores_texto_residual = sum(
        int(df[columna].map(es_texto_residual_invalido).sum())
        for columna in COLUMNAS_TEXTO_LIBRE
        if columna in df
    )
    return {
        "duplicados_exactos": int(df.duplicated().sum()),
        "espacios_extra": errores_espacios,
        "textos_residuales_invalidos": errores_texto_residual,
        "telefonos_invalidos": int((~df["TELEFONO"].map(es_telefono_valido)).sum()),
        "codigos_invalidos": int((~df["CODIGO"].map(es_codigo_valido)).sum()),
        "distritos_invalidos": int((~df["DISTRITO"].map(es_distrito_valido)).sum()),
        "departamentos_invalidos": int(
            (
                df["DEPARTAMENTO"].notna()
                & ~df["DEPARTAMENTO"].map(catalogos.es_departamento_valido)
            ).sum()
        ),
        "municipios_invalidos": int(
            sum(
                not catalogos.es_municipio_valido(municipio, departamento)
                for municipio, departamento in zip(df["MUNICIPIO"], df["DEPARTAMENTO"])
                if pd.notna(municipio) and pd.notna(departamento)
            )
        ),
        "relaciones_departamentales_invalidas": int(
            sum(
                not es_departamental_consistente(departamento, departamental)
                for departamento, departamental in zip(
                    df["DEPARTAMENTO"], df["DEPARTAMENTAL"]
                )
            )
        ),
        "columnas_requeridas_ausentes": int(
            len(set(COLUMNAS_REQUERIDAS) - set(df.columns))
        ),
    }
