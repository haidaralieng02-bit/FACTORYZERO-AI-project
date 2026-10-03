from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DEMO_DIR = DATA_DIR / "demo"
DOCUMENTS_DIR = DATA_DIR / "documents"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
MODEL_NAME = "openai/gpt-oss-120b"
TOP_K = 3
MAX_FILE_MB = 10
MAX_RETRIES = 2
LLM_TIMEOUT = 45.0


def get_groq_api_key():
    """Read the Groq secret without ever exposing it."""
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "").strip()
