"""
Very light job-domain NER / slot-filling.
* If spaCy is installed it uses the English model
* Otherwise it falls back to GPT function-calling for zero-shot extraction
"""

from typing import Dict, Optional
import asyncio
import json
import os
import re

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None

from .rag import GEMINI_DEFAULT_API_KEY, GEMINI_DEFAULT_MODEL

# ---------- 1) spaCy first ----------
try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    _nlp = None

COMPANY_PAT  = re.compile(r"\b(?:at|for)\s+([A-Z][A-Za-z0-9& ]+)", re.I)
LEVEL_PAT    = re.compile(r"\b(level|l|lvl)\s*([0-9]+)\b", re.I)
ROLE_PAT     = re.compile(r"\b(data (?:analyst|analytics?|scientist|engineer))\b", re.I)

def _regex_extract(text: str) -> Dict[str, Optional[str]]:
    company = LEVEL_PAT.sub("", text)  # crude cleanup before company regex
    company_m = COMPANY_PAT.search(company)
    level_m   = LEVEL_PAT.search(text)
    role_m    = ROLE_PAT.search(text.lower())

    return {
        "company":  company_m.group(1).strip() if company_m else None,
        "level":    level_m.group(2) if level_m else None,
        "role":     role_m.group(1).title() if role_m else None,
    }

_LLM_SYSTEM_PROMPT = (
    "Extract the company, level, and data role from the user's request. "
    "Return ONLY JSON using keys company, level, role. Use null when unknown."
)

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or GEMINI_DEFAULT_API_KEY
_GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
_gemini_model = None


def _ensure_gemini_model():
    global _gemini_model
    if genai is None:
        raise RuntimeError("google-generativeai is not installed.")
    if not _GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    if _gemini_model is None:
        genai.configure(api_key=_GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(_GEMINI_MODEL_NAME)
    return _gemini_model


async def _llm_extract(text: str) -> Dict[str, Optional[str]]:
    if genai is None:
        return {"company": None, "level": None, "role": None}
    model = _ensure_gemini_model()
    prompt = f"{_LLM_SYSTEM_PROMPT}\n\nSentence: \"{text}\""

    def _run():
        resp = model.generate_content(prompt)
        return getattr(resp, "text", "") or ""

    try:
        raw = await asyncio.to_thread(_run)
        payload = json.loads(raw)
    except Exception:
        return {"company": None, "level": None, "role": None}

    return {
        "company": payload.get("company"),
        "level": payload.get("level"),
        "role": payload.get("role"),
    }

# ---------- public helper ----------
async def extract(text: str) -> Dict[str, Optional[str]]:
    data = _regex_extract(text)
    if all(data.values()):
        return data
    # try spaCy NER for company if available
    if _nlp is not None and not data["company"]:
        ents = _nlp(text).ents
        for e in ents:
            if e.label_ == "ORG":
                data["company"] = e.text
                break
    # if still gaps, fall back to LLM
    if not all(data.values()):
        llm_data = await _llm_extract(text)
        data = {k: data[k] or llm_data.get(k) for k in ["company", "level", "role"]}
    return data
