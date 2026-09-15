"""
CLI usage:
    python main.py --input path/to/form.pdf --rules examples/rules.yaml
    python main.py --input path/to/folder/ --rules examples/rules.yaml --output report.json
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

from pdf_form_analyzer import analyze_pdf


def load_rules(rules_path: str) -> dict:
    with open(rules_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Analyze whether PDF forms are completed correctly.")
    parser.add_argument("--input", required=True, help="PDF file or folder of PDFs")
    parser.add_argument("--rules", required=True, help="Path to rules.yaml")
    parser.add_argument("--output", help="Optional path to write JSON report")
    args = parser.parse_args()

    rules = load_rules(args.rules)
    input_path = Path(args.input)

    pdf_paths = [input_path] if input_path.is_file() else sorted(input_path.glob("*.pdf"))
    if not pdf_paths:
        print(f"No PDFs found at {args.input}", file=sys.stderr)
        sys.exit(1)

    results = [analyze_pdf(str(p), rules) for p in pdf_paths]

    for r in results:
        status = "PASS" if r["valid"] else "FAIL"
        print(f"[{status}] {r['file']} (detected as: {r['detected_type']})")
        for issue in r["issues"]:
            print(f"   - {issue}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
