"""
Classifies a PDF as one of:
  - "acroform": has real, fillable form fields
  - "flat":     has extractable text but no form fields (printed/typed form)
  - "scanned":  little/no extractable text -> needs OCR

This drives which extractor the pipeline uses.
"""
from pypdf import PdfReader
import pdfplumber

MIN_TEXT_CHARS_FOR_FLAT = 50  # below this, assume it's an image/scan


def classify_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()

    if fields and len(fields) > 0:
        return "acroform"

    text_length = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text_length += len(text.strip())
            if text_length >= MIN_TEXT_CHARS_FOR_FLAT:
                return "flat"

    return "scanned"
