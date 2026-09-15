"""
Two layers of validation:

1. Deterministic rules (fast, free, no external calls):
   - required fields present / non-empty
   - regex format checks (dates, emails, IDs, etc.)

2. AI-based rules (for anything that needs judgement or cross-field
   reasoning, e.g. "signature date can't be before the form date",
   "if employment_status is Employed, employer_name is required"):
   - only called if `ai_rules` are configured, so simple use cases
     never need an API key.
"""
import json
import re
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def run_deterministic_checks(data: dict, rules: dict) -> list:
    """
    data: {"fields": {...}} or {"raw_text": "..."}
    rules: parsed rules.yaml content
    Returns a list of issue strings (empty if all pass).
    """
    issues = []
    fields = data.get("fields") or {}
    raw_text = data.get("raw_text") or ""

    # Required fields: works for acroform (field lookup) and flat/scanned
    # (falls back to searching for "Label:" style patterns in raw_text)
    for field_name in rules.get("required_fields", []):
        if fields:
            value = fields.get(field_name)
            if not value or str(value).strip() == "":
                issues.append(f"Missing required field: '{field_name}'")
        else:
            pattern = rf"{re.escape(field_name)}\s*[:\-]\s*(\S.*)"
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if not match or not match.group(1).strip():
                issues.append(f"Missing required field: '{field_name}'")

    # Regex format checks
    for field_name, pattern in rules.get("field_patterns", {}).items():
        value = None
        if fields:
            value = fields.get(field_name)
        else:
            m = re.search(rf"{re.escape(field_name)}\s*[:\-]\s*(\S.*)", raw_text, re.IGNORECASE)
            value = m.group(1).strip() if m else None

        if value and not re.match(pattern, str(value)):
            issues.append(f"Field '{field_name}' has invalid format: '{value}'")

    return issues


def run_ai_checks(data: dict, ai_rules: list, model: str = "claude-sonnet-4-6") -> list:
    """
    ai_rules: list of plain-English rule strings, e.g.
        ["Signature date must not be earlier than the form date",
         "If employment_status is 'Employed', employer_name must be filled in"]
    Returns a list of issue strings found by the model.
    """
    if not ai_rules:
        return []

    content_desc = data.get("fields") or {"raw_text": data.get("raw_text", "")}

    prompt = f"""You are validating a completed form against a set of rules.

Extracted form content:
{json.dumps(content_desc, indent=2, default=str)}

Rules to check:
{json.dumps(ai_rules, indent=2)}

For each rule, check whether the form content violates it.
Respond with ONLY valid JSON, no other text, in this exact shape:
{{"issues": ["description of violation 1", "description of violation 2"]}}
If there are no violations, return {{"issues": []}}."""

    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(text)
        return parsed.get("issues", [])
    except json.JSONDecodeError:
        return [f"AI validation returned unparseable output: {text[:200]}"]
