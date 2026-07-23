from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.validadores import COLUMNAS_REQUERIDAS


ENTRADA = ROOT / "codebook.md"
SALIDA = ROOT / "codebook.pdf"


def _inline(texto: str) -> str:
    texto = re.sub(r"\[([^]]+)]\(([^)]+)\)", r"\1 (\2)", texto)
    partes = re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", texto)
    salida = []
    for parte in partes:
        if parte.startswith("`") and parte.endswith("`"):
            salida.append(f'<font name="Courier">{html.escape(parte[1:-1])}</font>')
        elif parte.startswith("**") and parte.endswith("**"):
            salida.append(f"<b>{html.escape(parte[2:-2])}</b>")
        else:
            salida.append(html.escape(parte))
    return "".join(salida)


def _filas_tabla(lineas: list[str]) -> list[list[str]]:
    filas = []
    for linea in lineas:
        celdas = [celda.strip() for celda in linea.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", celda) for celda in celdas):
            continue
        filas.append(celdas)
    return filas


def _pie(canvas, documento) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#52606d"))
    canvas.drawCentredString(
        landscape(A4)[0] / 2,
        7 * mm,
        f"Libro de códigos · v1.0.0 · página {documento.page}",
    )
    canvas.restoreState()


def _construir_historia() -> list[object]:
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle("TituloAzul", parent=estilos["Title"], textColor=colors.HexColor("#0747a6"), fontName="Helvetica-Bold", fontSize=22, leading=26, spaceAfter=12))
    estilos.add(ParagraphStyle("H2Azul", parent=estilos["Heading2"], textColor=colors.HexColor("#0052cc"), fontName="Helvetica-Bold", fontSize=15, leading=18, spaceBefore=12, spaceAfter=7, keepWithNext=True))
    estilos.add(ParagraphStyle("H3Azul", parent=estilos["Heading3"], textColor=colors.HexColor("#0065ff"), fontName="Helvetica-Bold", fontSize=11.5, leading=14, spaceBefore=8, spaceAfter=4, keepWithNext=True))
    estilos.add(ParagraphStyle("Cuerpo", parent=estilos["BodyText"], fontName="Helvetica", fontSize=8.7, leading=11.5, spaceAfter=5, allowWidows=0, allowOrphans=0))
    estilos.add(ParagraphStyle("Campo", parent=estilos["BodyText"], fontName="Helvetica", fontSize=8.1, leading=10.3, leftIndent=4 * mm, firstLineIndent=-4 * mm, spaceAfter=2))
    estilos.add(ParagraphStyle("Tabla", parent=estilos["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9))

    lineas = ENTRADA.read_text(encoding="utf-8").splitlines()
    historia: list[object] = []
    i = 0
    primera_tabla = True
    while i < len(lineas):
        linea = lineas[i].strip()
        if not linea:
            historia.append(Spacer(1, 2.5 * mm))
            i += 1
            continue
        if linea.startswith("|"):
            bloque = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                bloque.append(lineas[i].strip())
                i += 1
            filas = _filas_tabla(bloque)
            if primera_tabla and len(filas[0]) == 10:
                campos = filas[0]
                for numero, fila in enumerate(filas[1:], start=1):
                    elementos = [Paragraph(_inline(fila[0].strip("`")), estilos["H3Azul"])]
                    for campo, valor in zip(campos[1:], fila[1:]):
                        elementos.append(
                            Paragraph(f"<b>{html.escape(campo)}:</b> {_inline(valor)}", estilos["Campo"])
                        )
                    historia.append(KeepTogether(elementos))
                    if numero % 3 == 0:
                        historia.append(PageBreak())
                primera_tabla = False
            else:
                datos = [[Paragraph(_inline(celda), estilos["Tabla"]) for celda in fila] for fila in filas]
                anchos = [landscape(A4)[0] * proporcion for proporcion in ([0.14, 0.14, 0.12, 0.52] if len(filas[0]) == 4 else [0.2] * len(filas[0]))]
                tabla = Table(datos, colWidths=anchos, repeatRows=1, hAlign="LEFT")
                tabla.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0747a6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c4ce")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
                ]))
                historia.append(tabla)
            continue
        if linea.startswith("# "):
            historia.append(Paragraph(_inline(linea[2:]), estilos["TituloAzul"]))
        elif linea.startswith("## "):
            historia.append(Paragraph(_inline(linea[3:]), estilos["H2Azul"]))
        elif linea.startswith("### "):
            historia.append(Paragraph(_inline(linea[4:]), estilos["H3Azul"]))
        elif linea.startswith("- "):
            historia.append(Paragraph(f"• {_inline(linea[2:])}", estilos["Cuerpo"]))
        else:
            historia.append(Paragraph(_inline(linea), estilos["Cuerpo"]))
        i += 1
    return historia


def main() -> None:
    documento = SimpleDocTemplate(
        str(SALIDA),
        pagesize=landscape(A4),
        rightMargin=11 * mm,
        leftMargin=11 * mm,
        topMargin=13 * mm,
        bottomMargin=14 * mm,
        title="Libro de códigos — establecimientos educativos",
        author="Equipo CC3084",
    )
    documento.build(_construir_historia(), onFirstPage=_pie, onLaterPages=_pie)
    if SALIDA.stat().st_size < 10_000:
        raise RuntimeError("El PDF generado está vacío o incompleto.")
    lector = PdfReader(SALIDA)
    textos = [(pagina.extract_text() or "").strip() for pagina in lector.pages]
    if not textos or any(len(texto) < 40 for texto in textos):
        raise RuntimeError("El PDF contiene una página vacía o sin texto extraíble.")
    texto_completo = "\n".join(textos)
    faltantes = [variable for variable in COLUMNAS_REQUERIDAS if variable not in texto_completo]
    faltantes.extend(valor for valor in ("v1.0.0", "2026-07-18", "MINEDUC") if valor not in texto_completo)
    for campo in ("Descripción", "Tipo de dato", "Dominio permitido", "Valores posibles", "Tratamiento aplicado", "Variables derivadas", "Fecha de extracción", "Fuente", "Versión del conjunto limpio"):
        if texto_completo.count(campo) < len(COLUMNAS_REQUERIDAS):
            faltantes.append(campo)
    if faltantes:
        raise RuntimeError(f"Contenido ausente del PDF: {faltantes}")
    print(f"PDF generado: {SALIDA.relative_to(ROOT)} ({SALIDA.stat().st_size:,} bytes; {len(lector.pages)} páginas; texto verificado)")


if __name__ == "__main__":
    main()
