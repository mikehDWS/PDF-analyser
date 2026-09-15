"""
Minimal web app around pdf_form_analyzer.

Run locally:
    uvicorn webapp.app:app --reload

Then visit http://localhost:8000
"""
import shutil
import tempfile
from pathlib import Path

import yaml
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pdf_form_analyzer import analyze_pdf

BASE_DIR = Path(__file__).resolve().parent
RULES_PATH = BASE_DIR.parent / "examples" / "rules.yaml"

app = FastAPI(title="PDF Form Analyzer")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def load_rules() -> dict:
    with open(RULES_PATH) as f:
        return yaml.safe_load(f)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result": None})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, file: UploadFile = File(...)):
    rules = load_rules()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = analyze_pdf(tmp_path, rules)
        result["file"] = file.filename  # show the original name, not the temp path
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return templates.TemplateResponse("index.html", {"request": request, "result": result})


@app.get("/health")
async def health():
    return {"status": "ok"}
