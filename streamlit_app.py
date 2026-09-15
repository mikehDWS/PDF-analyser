"""
Run locally:
    streamlit run streamlit_app.py

Deploy: push to GitHub, then connect the repo at https://share.streamlit.io
(Streamlit Cloud reads requirements.txt and packages.txt automatically —
no Dockerfile needed there.)
"""
import os
import tempfile
from pathlib import Path

import streamlit as st
import yaml

# Streamlit Cloud secrets don't auto-populate os.environ, but the
# anthropic client reads ANTHROPIC_API_KEY from there -- bridge it.
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

from pdf_form_analyzer import analyze_pdf  # noqa: E402 (must come after the secrets bridge)

RULES_PATH = Path(__file__).parent / "examples" / "rules.yaml"

st.set_page_config(page_title="Form Checker", page_icon="📋")


@st.cache_data
def load_rules():
    with open(RULES_PATH) as f:
        return yaml.safe_load(f)


st.title("Form Checker")
st.write("Upload a completed PDF form to check for missing fields, formatting errors, and rule violations.")

uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner("Checking form…"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            rules = load_rules()
            result = analyze_pdf(tmp_path, rules)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    st.caption(f"Read as: **{result['detected_type']}**")

    if result["valid"]:
        st.success(f"**{uploaded_file.name}** — complete, no issues found.")
    else:
        st.error(f"**{uploaded_file.name}** — needs attention:")
        for issue in result["issues"]:
            st.write(f"- {issue}")
