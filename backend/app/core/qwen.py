# qwen.py
"""
LLM wrapper that talks to a Hugging Face inference endpoint hosting the fine-tuned
Qwen model. Provides the same async helpers used elsewhere in the backend:
- chat(messages) -> str
- score_answer(question, answer) -> int (overall)
- score_with_metrics(question, answer) -> dict (detailed metrics JSON)
"""

import json
import os
from typing import Any, Dict, List

import httpx

HF_ENDPOINT = os.getenv(
    "LLM_ENDPOINT",
    "https://qgwj48ky9i7zjuzj.us-east-1.aws.endpoints.huggingface.cloud",
)
HF_API_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
CHAT_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "512"))


class LLMConfigError(RuntimeError):
    """Raised when the Hugging Face endpoint is misconfigured."""


def _build_headers() -> Dict[str, str]:
    if not HF_API_TOKEN:
        raise LLMConfigError("HF_API_TOKEN or HUGGINGFACE_API_KEY must be configured.")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HF_API_TOKEN}",
    }


def _format_chat_prompt(messages: List[Dict[str, str]]) -> str:
    """Convert OpenAI-style chat messages into a simple text prompt."""
    lines: List[str] = []
    role_map = {"system": "System", "assistant": "Assistant", "user": "User"}

    for msg in messages:
        role = role_map.get(msg.get("role", "").lower(), "User")
        content = (msg.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")

    lines.append("Assistant:")
    return "\n".join(lines)


def _extract_generated_text(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return str(first.get("generated_text") or first.get("text") or "")
        return str(first)
    if isinstance(payload, dict):
        if "generated_text" in payload:
            return str(payload["generated_text"])
        if "text" in payload:
            return str(payload["text"])
    return ""


async def _invoke_llm(prompt: str, *, temperature: float, max_new_tokens: int) -> str:
    if not HF_ENDPOINT:
        raise LLMConfigError("LLM_ENDPOINT is not configured.")

    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": max(0.0, temperature),
            "max_new_tokens": max(1, max_new_tokens),
            "return_full_text": False,
            "do_sample": temperature > 0,
        },
        "options": {"wait_for_model": True},
    }

    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(HF_ENDPOINT, headers=_build_headers(), json=payload)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - network failure path
        detail = exc.response.text[:500]
        raise RuntimeError(f"LLM request failed: {detail}") from exc

    data = response.json()
    text = _extract_generated_text(data).strip()
    if not text:
        raise RuntimeError("LLM response did not include generated_text.")
    return text


async def chat(messages: List[Dict[str, str]]) -> str:
    prompt = _format_chat_prompt(messages)
    return await _invoke_llm(prompt, temperature=0.7, max_new_tokens=CHAT_MAX_NEW_TOKENS)


# ---- Metrics scoring ----
_SCORER_SYS = """You are a strict interviewer for data roles (Data Scientist, Data Engineer,
Machine Learning Engineer, Data Analyst). You must return ONLY a single JSON object.
Never add prose.

Scoring rubric (each 0–10):
- technical_correctness: factual accuracy, correct methods/terms, mistake-free reasoning.
- clarity: structure, concise explanations, easy to follow.
- completeness: covers key points the question expects (depth over fluff).
- tone: professional and confident (neutral English).

Overall:
- overall = round((0.5*technical_correctness + 0.25*completeness + 0.2*clarity + 0.05*tone), 1)
- Clamp each metric to [0,10].

Flags (booleans):
- gibberish: true if the answer is incoherent, meaningless, or spammy.
- off_topic: true if answer ignores the question’s technical subject.
- dont_know: true if the answer explicitly admits not knowing OR gives no info.
- policy_violation: true if unsafe or disallowed content.

Hard caps:
- If gibberish OR off_topic OR dont_know -> set overall=0 (do not exceed 0).
- If policy_violation -> set overall=0.

Return JSON with:
{
  "technical_correctness": <0-10>,
  "clarity": <0-10>,
  "completeness": <0-10>,
  "tone": <0-10>,
  "overall": <0-10>,
  "flags": { "gibberish": <bool>, "off_topic": <bool>, "dont_know": <bool>, "policy_violation": <bool> },
  "notes": "<one short sentence explaining the main reason for the score>"
}
"""


async def score_with_metrics(question: str, answer: str) -> Dict[str, Any]:
    user = f"""Question: {question}

Answer: {answer}

Return ONLY the JSON described above."""
    prompt = f"System: {_SCORER_SYS.strip()}\nUser: {user.strip()}\nAssistant:"
    raw = await _invoke_llm(prompt, temperature=0.0, max_new_tokens=300)

    # Parse & sanitize
    try:
        obj = json.loads(raw)
    except Exception:
        obj = {}

    def _num(v, default=0.0):
        try:
            x = float(v)
        except Exception:
            x = default
        return max(0.0, min(10.0, x))

    metrics = {
        "technical_correctness": _num(obj.get("technical_correctness")),
        "clarity": _num(obj.get("clarity")),
        "completeness": _num(obj.get("completeness")),
        "tone": _num(obj.get("tone")),
        "overall": _num(obj.get("overall")),
        "flags": {
            "gibberish": bool(obj.get("flags", {}).get("gibberish", False)),
            "off_topic": bool(obj.get("flags", {}).get("off_topic", False)),
            "dont_know": bool(obj.get("flags", {}).get("dont_know", False)),
            "policy_violation": bool(obj.get("flags", {}).get("policy_violation", False)),
        },
        "notes": (obj.get("notes") or "").strip()[:300],
    }

    # Apply hard caps (your latest rule: any of these -> overall = 0)
    f = metrics["flags"]
    if f["gibberish"] or f["off_topic"] or f["dont_know"] or f["policy_violation"]:
        metrics["overall"] = 0.0

    # round to 1 decimal
    for k in ("technical_correctness", "clarity", "completeness", "tone", "overall"):
        metrics[k] = round(float(metrics[k]), 1)

    return metrics


async def score_answer(question: str, answer: str) -> int:
    """Convenience wrapper that returns just the overall integer 0..10."""
    m = await score_with_metrics(question, answer)
    return int(round(m.get("overall", 0)))
