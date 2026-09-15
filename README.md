[README.md](https://github.com/user-attachments/files/32238878/README.md)
# PDF Form Analyzer

Checks whether PDF forms have been completed correctly. Handles three input types automatically:

- **Fillable PDFs (AcroForm)** — reads form field values directly
- **Flat PDFs** — printed/typed forms with no real fields, extracts text and matches labels
- **Scanned/photographed forms** — runs OCR first, then treats the result like a flat PDF

Validation runs in two layers:

1. **Deterministic checks** — required fields present, regex format checks (dates, emails, etc.). Fast, free, no external calls.
2. **AI checks** — plain-English rules for anything needing judgement or cross-field logic (e.g. "signature date can't be before the form date"). Uses the Anthropic API.

## Setup

```bash
pip install -r requirements.txt
```

OCR also needs system packages (not pip-installable):

```bash
# Debian/Ubuntu
sudo apt-get install poppler-utils tesseract-ocr

# macOS
brew install poppler tesseract
```

Set your Anthropic API key if you're using `ai_rules`:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
python main.py --input path/to/form.pdf --rules examples/rules.yaml
python main.py --input path/to/folder/ --rules examples/rules.yaml --output report.json
```

Or use it as a library:

```python
import yaml
from pdf_form_analyzer import analyze_pdf

rules = yaml.safe_load(open("examples/rules.yaml"))
result = analyze_pdf("form.pdf", rules)
print(result)
# {"file": "form.pdf", "detected_type": "acroform", "valid": False,
#  "issues": ["Missing required field: 'signature'"]}
```

## Configuring rules

See `examples/rules.yaml`:

```yaml
required_fields:
  - full_name
  - signature

field_patterns:
  email: '^[^@\s]+@[^@\s]+\.[^@\s]+$'

ai_rules:
  - "Signature date must not be earlier than the form date"
```

## Project structure

```
pdf_form_analyzer/
  detector.py     # classifies PDF as acroform / flat / scanned
  extractors.py   # one extractor per type
  validators.py   # deterministic + AI rule checking
  pipeline.py      # ties it together (analyze_pdf)
main.py            # CLI
streamlit_app.py    # Streamlit web app (deploy straight from GitHub)
webapp/            # FastAPI web app (needs Docker to deploy)
examples/rules.yaml
Dockerfile
packages.txt         # apt packages for Streamlit Cloud (poppler, tesseract)
render.yaml         # deploy config for Render (FastAPI route)
.github/workflows/ci.yml
```

## Running the web app

Two interfaces are included — pick whichever fits:

**Streamlit** (`streamlit_app.py`) — simplest to deploy straight from GitHub, no Dockerfile needed:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**FastAPI** (`webapp/app.py`) — more control over layout/behavior, needs Docker to deploy:

```bash
pip install -r requirements.txt
uvicorn webapp.app:app --reload
```

Either way, visit the local URL it prints, upload a PDF, and get a pass/fail result with a list of issues.

## Deploying the Streamlit app (recommended, easiest)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **New app**.
3. Pick this repo/branch, set the main file path to `streamlit_app.py`, click **Deploy**.
4. Streamlit Cloud reads `requirements.txt` for Python packages and `packages.txt` for the
   `poppler-utils`/`tesseract-ocr` system packages OCR needs — both are already in this repo.
5. If you're using `ai_rules`, add `ANTHROPIC_API_KEY` under the app's **Settings → Secrets** as:
   ```toml
   ANTHROPIC_API_KEY = "your_key_here"
   ```
6. Every push to the connected branch auto-redeploys.

## Deploying the FastAPI app

GitHub hosts your source and runs CI (`.github/workflows/ci.yml` builds and smoke-tests the
Docker image on every push) — but GitHub itself doesn't run a live backend. You need an actual
host for that. **Render** is the simplest free option and this repo is already set up for it:

1. Push this repo to GitHub.
2. On [render.com](https://render.com), choose **New → Blueprint**, and point it at your repo.
   Render reads `render.yaml` automatically and builds from the `Dockerfile`.
3. In the Render dashboard, add your `ANTHROPIC_API_KEY` as an environment variable (never commit
   it to the repo).
4. Every push to `main` will auto-redeploy.

Other hosts work the same way since everything's Dockerized — Railway and Fly.io both support
"deploy from a GitHub repo with a Dockerfile" with a similarly small config file swapped in for
`render.yaml`.
