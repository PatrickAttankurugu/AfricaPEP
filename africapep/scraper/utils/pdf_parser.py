"""PDF extraction pipeline: pdfplumber -> OCR fallback via PyMuPDF + pytesseract."""
import io
from pathlib import Path

import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import structlog

log = structlog.get_logger()

OCR_THRESHOLD = 100  # avg chars per page below which OCR kicks in


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF. Uses pdfplumber first, falls back to OCR."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    text = _try_pdfplumber(str(path))

    # Check quality: if too few chars, fall back to OCR
    pages = text.split("\f") if "\f" in text else [text]
    avg_chars = sum(len(p) for p in pages) / max(len(pages), 1)

    if avg_chars < OCR_THRESHOLD:
        log.info("pdf_ocr_fallback", path=pdf_path, avg_chars=round(avg_chars))
        text = _try_ocr(str(path))

    return text


def _try_pdfplumber(path: str) -> str:
    """Extract text using pdfplumber (best for structured PDFs)."""
    try:
        with pdfplumber.open(path) as pdf:
            pages = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)
            return "\f".join(pages)
    except Exception as e:
        log.warning("pdfplumber_failed", path=path, error=str(e))
        return ""


def _try_ocr(path: str) -> str:
    """OCR fallback using PyMuPDF for rendering + pytesseract for recognition."""
    try:
        doc = fitz.open(path)
        pages_text = []
        for page_num, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            page_text = pytesseract.image_to_string(img)
            pages_text.append(page_text)
            log.debug("ocr_page_done", page=page_num, chars=len(page_text))
        doc.close()
        return "\f".join(pages_text)
    except Exception as e:
        log.error("ocr_failed", path=path, error=str(e))
        return ""


def extract_tables_from_pdf(pdf_path: str) -> list[list[list[str]]]:
    """Extract tables from PDF using pdfplumber."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    tables = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables() or []
                tables.extend(page_tables)
    except Exception as e:
        log.warning("table_extraction_failed", path=pdf_path, error=str(e))

    return tables
