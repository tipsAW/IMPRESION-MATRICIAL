# -*- coding: utf-8 -*-
"""
Módulo para procesar y unir comprobantes 2 por hoja (A4 o Carta).
Funciona tanto con múltiples PDFs como con un solo PDF de 50+ páginas.
"""

import io
from typing import List, Tuple, Union
try:
    import pymupdf as fitz
except ImportError:
    import fitz

# Medidas en puntos tipográficos (1 pulgada = 72 pt)
TAMANOS = {
    "A4": (595.276, 841.890),     # 210 x 297 mm
    "Carta": (612.000, 792.000),  # 8.5 x 11 pulgadas
}

MARGEN_DEFECTO = 6


def fin_contenido(pagina, margen=MARGEN_DEFECTO) -> float:
    """Detecta la coordenada Y más baja con contenido real (texto, gráficos, tablas)."""
    y_fin = 0.0
    try:
        for _tipo, rect in pagina.get_bboxlog():
            y_fin = max(y_fin, fitz.Rect(rect).y1)
    except Exception:
        for b in pagina.get_text("blocks"):
            y_fin = max(y_fin, b[3])
        for d in pagina.get_drawings():
            y_fin = max(y_fin, d["rect"].y1)

    if y_fin <= 0.0:
        return pagina.rect.height
    return min(pagina.rect.height, y_fin + margen)


def procesar_comprobantes(
    fuentes: List[Union[str, bytes, io.BytesIO]],
    tamano_papel: str = "A4",
    linea_corte: bool = True,
    centrar: bool = True,
    margen_extra: float = 6.0
) -> Tuple[bytes, int, int]:
    """
    Toma una lista de PDFs (rutas o bytes) y genera un PDF en memoria
    con 2 comprobantes por hoja.
    
    Retorna:
        (pdf_bytes, total_comprobantes, total_hojas)
    """
    ancho_hoja, alto_hoja = TAMANOS.get(tamano_papel, TAMANOS["A4"])
    alto_slot = alto_hoja / 2.0

    salida = fitz.open()
    docs_abiertos = []
    paginas = []

    try:
        # 1. Extraer todas las páginas de todos los documentos en orden
        for f in fuentes:
            if isinstance(f, (bytes, bytearray)):
                doc = fitz.open(stream=f, filetype="pdf")
            elif isinstance(f, io.BytesIO):
                doc = fitz.open(stream=f.getvalue(), filetype="pdf")
            else:
                doc = fitz.open(f)
            docs_abiertos.append(doc)

            for pag in doc:
                paginas.append((doc, pag))

        total_comprobantes = len(paginas)
        if total_comprobantes == 0:
            salida.close()
            return b"", 0, 0

        # 2. Agrupar de 2 en 2 en cada nueva hoja
        for i in range(0, total_comprobantes, 2):
            hoja = salida.new_page(width=ancho_hoja, height=alto_hoja)

            # Dibujar línea divisoria central si se solicitó
            if linea_corte:
                shape = hoja.new_shape()
                # Línea punteada en el medio exacto
                shape.draw_line(fitz.Point(15, alto_slot), fitz.Point(ancho_hoja - 15, alto_slot))
                shape.finish(
                    color=(0.75, 0.75, 0.75),   # Gris suave
                    width=0.75,
                    dashes="[4 3] 0"            # Punteada
                )
                shape.commit()

            for slot in (0, 1):  # 0 = Superior, 1 = Inferior
                idx = i + slot
                if idx >= total_comprobantes:
                    break

                doc_orig, pag_orig = paginas[idx]

                # Recortar hasta donde termina el contenido real
                y_fin = fin_contenido(pag_orig, margen=margen_extra)
                recorte = fitz.Rect(0, 0, pag_orig.rect.width, y_fin)

                w, h = recorte.width, recorte.height

                # Escalar proporcionalmente si excede el tamaño del slot
                esc = 1.0
                if h > (alto_slot - 4):
                    esc = min(esc, (alto_slot - 4) / h)
                if w > (ancho_hoja - 4):
                    esc = min(esc, (ancho_hoja - 4) / w)

                w *= esc
                h *= esc

                # Posición Y base
                y_base = 0.0 if slot == 0 else alto_slot
                # Centrar verticalmente en el slot
                y0 = y_base + max(0.0, (alto_slot - h) / 2.0)

                # Centrar horizontalmente si aplica
                if centrar:
                    x0 = max(0.0, (ancho_hoja - w) / 2.0)
                else:
                    x0 = 0.0

                destino_rect = fitz.Rect(x0, y0, x0 + w, y0 + h)
                hoja.show_pdf_page(destino_rect, doc_orig, pag_orig.number, clip=recorte)

        # Generar buffer PDF comprimido
        pdf_bytes = salida.tobytes(garbage=4, deflate=True)
        total_hojas = salida.page_count
        return pdf_bytes, total_comprobantes, total_hojas

    finally:
        salida.close()
        for d in docs_abiertos:
            d.close()


def obtener_preview_png(pdf_bytes: bytes, dpi: int = 130) -> bytes:
    """Devuelve los bytes de la primera hoja generada en formato PNG para vista previa."""
    if not pdf_bytes:
        return b""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count == 0:
            return b""
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")
    finally:
        doc.close()
