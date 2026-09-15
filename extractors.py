"""
One extractor per PDF type. Each returns a common shape:
    {"fields": {name: value, ...}, "raw_text": str}

For acroform PDFs, `fields` comes straight from the widgets.
For flat/scanned PDFs, `fields` is empty (no field structure exists) --
the rule engine works off `raw_text` and regex/label matching instead.
"""
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract


def extract_acroform(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    fields = {}
    for page in doc:
        for widget in page.widgets() or []:
            fields[widget.field_name] = widget.field_value
    doc.close()
    return {"fields": fields, "raw_text": None}


def extract_flat_text(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return {"fields": {}, "raw_text": text}


def extract_via_ocr(pdf_path: str, dpi: int = 300) -> dict:
    pages = convert_from_path(pdf_path, dpi=dpi)
    text = "\n".join(pytesseract.image_to_string(page) for page in pages)
    return {"fields": {}, "raw_text": text}


EXTRACTORS = {
    "acroform": extract_acroform,
    "flat": extract_flat_text,
    "scanned": extract_via_ocr,
}


def extract(pdf_path: str, pdf_type: str) -> dict:
    return EXTRACTORS[pdf_type](pdf_path)
