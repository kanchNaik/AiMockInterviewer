"""
Updated OpenAI client for new high-level architecture.
"""

import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import json


SCORER_SYS = """You are a strict interviewer for data roles (Data Scientist, Data Engineer,
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

class OpenAIClient():

    def __init__(self):
        api = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not api:
            raise RuntimeError("OPENAI_API_KEY not set")

        self.client = AsyncOpenAI(api_key=api)

    # ------------------------------------------------------
    # INTERNAL CHAT — old implementation moved here
    # ------------------------------------------------------
    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return (resp.choices[0].message.content or "").strip()

     # ------------------------------------------------------
    # SCORING
    # ------------------------------------------------------
    async def score_with_metrics(self, question: str, answer: str) -> Dict[str, Any]:
        user = f"Question: {question}\n\nAnswer: {answer}\nReturn ONLY JSON."
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SCORER_SYS},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        raw = (resp.choices[0].message.content or "").strip()
        print("raw scores", raw)
        return self.sanitize_metrics(raw)

    # ======================================================================
    # JSON SANITIZER — SAME AS BEFORE
    # ======================================================================
    def sanitize_metrics(self, raw_json: str) -> Dict[str, Any]:
        try:
            obj = json.loads(raw_json)
        except Exception:
            obj = {}

        def _num(v, d=0.0):
            try:
                x = float(v)
            except Exception:
                x = d
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

        # Hard caps
        f = metrics["flags"]
        if f["gibberish"] or f["off_topic"] or f["dont_know"] or f["policy_violation"]:
            metrics["overall"] = 0.0

        # Round
        for k in ("technical_correctness", "clarity", "completeness", "tone", "overall"):
            metrics[k] = round(float(metrics[k]), 1)
        
        print("sanitized", metrics)

        return metrics
