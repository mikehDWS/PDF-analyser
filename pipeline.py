from .detector import classify_pdf
from .extractors import extract
from .validators import run_deterministic_checks, run_ai_checks


def analyze_pdf(pdf_path: str, rules: dict) -> dict:
    """
    rules shape (see examples/rules.yaml):
        required_fields: [list of field/label names]
        field_patterns: {field_name: regex}
        ai_rules: [plain-English rule strings]

    Returns:
        {
          "file": pdf_path,
          "detected_type": "acroform" | "flat" | "scanned",
          "valid": bool,
          "issues": [str, ...]
        }
    """
    pdf_type = classify_pdf(pdf_path)
    data = extract(pdf_path, pdf_type)

    issues = []
    issues += run_deterministic_checks(data, rules)
    issues += run_ai_checks(data, rules.get("ai_rules", []))

    return {
        "file": pdf_path,
        "detected_type": pdf_type,
        "valid": len(issues) == 0,
        "issues": issues,
    }
