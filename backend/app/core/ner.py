"""
Very light job-domain NER / slot-filling.
* If spaCy is installed it uses the English model
* Otherwise it falls back to GPT function-calling for zero-shot extraction
"""

from typing import Dict, Optional
import re, os

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

# ---------- 2) fallback to GPT JSON mode ----------
import json, openai
from ..core.ModelIntegrations import gpt   # re-use the same AsyncOpenAI client

async def _gpt_extract(text: str) -> Dict[str, Optional[str]]:
    function_def = {
        "name": "extract_job_params",
        "description": "Pull company, level, role from user request",
        "parameters": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "nullable": True},
                "level":   {"type": "string", "nullable": True},
                "role":    {"type": "string", "nullable": True},
            },
            "required": [],
        },
    }
    resp = await gpt.client.chat.completions.create(
        model=gpt.MODEL,
        messages=[{"role": "user", "content": text}],
        functions=[function_def],
        function_call={"name": "extract_job_params"},
    )
    return json.loads(resp.choices[0].message.function_call.arguments)

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
    # if still gaps, ask GPT
    if not all(data.values()):
        gpt_data = await _gpt_extract(text)
        data = {k: data[k] or gpt_data.get(k) for k in ["company", "level", "role"]}
    return data
