"""
Qwen HF Endpoint Client
- Uses HF text generation API
- Implements new high-level methods
"""

import os
import httpx
from typing import Dict, List, Any, Optional

from .baseclient import BaseLLMClient, SCORER_SYS, sanitize_metrics


class QwenClient(BaseLLMClient):
    def __init__(self):
        self.endpoint = os.getenv("QWEN_ENDPOINT", "")
        self.api_key = os.getenv("QWEN_API_KEY", "")

        if not self.endpoint:
            raise RuntimeError("QWEN_ENDPOINT is not set")
        if not self.api_key:
            raise RuntimeError("QWEN_API_KEY is not set")

    # =========================================================
    # INTERNAL: raw HF text generation call
    # =========================================================
    async def _generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.7,
                "max_new_tokens": 200
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        if isinstance(data, list):
            return data[0].get("generated_text", "").strip()
        return data.get("generated_text", "").strip()

    # =========================================================
    # INTERNAL CHAT — simply flatten messages
    # =========================================================
    async def _chat(self, messages: List[Dict[str, str]]) -> str:
        text = ""
        for m in messages:
            text += f"[{m['role'].upper()}]\n{m['content']}\n\n"
        text += "[ASSISTANT]\n"
        return await self._generate(text)

    # =========================================================
    # PUBLIC: FIRST QUESTION
    # =========================================================
    async def generate_first_question(self, meta: dict, history: List[Dict[str, str]], rag_matches: Optional[List[Dict[str, str]]] = None):
        rag_context = ""
        if rag_matches:
            examples = rag_matches[:5]  # limit size
            lines = []

            for i, ex in enumerate(examples, start=1):
                q = (ex.get("question") or "").strip()
                tags = (ex.get("tags") or "").strip()
                if q:
                    lines.append(f"{i}. {q}  (Tags: {tags})")

            if lines:
                rag_context = (
                    "Here are reference interview questions retrieved from your knowledge base. "
                    "Use them ONLY to guide theme, difficulty, and style. DO NOT repeat them verbatim:\n"
                    + "\n".join(lines) +
                    "\n\n"
                )
                
        prompt = f"{rag_context}" + f"""
        You are an expert interviewer.

        Generate ONE strong first interview question.
        - No explanation
        - No intro
        - No multi-part questions

        Company: {meta.get('company')}
        Role: {meta.get('role')}
        Seniority: {meta.get('seniority')}
        Context: {meta.get('context')}
        """
        return await self._generate(prompt)

    # =========================================================
    # PUBLIC: FEEDBACK + NEXT
    # =========================================================
    async def evaluate_answer_and_followup(self, question: str, answer: str, history: List[Dict[str, str]]):
        prompt = f"""
Evaluate the candidate's answer in 2–3 sentences.

Then write:
NEXT: <next_question>

Question: {question}
Answer: {answer}

Output Format:
<feedback>
NEXT: <next question>
"""
        raw = await self._generate(prompt)

        if "NEXT:" in raw:
            fb, nq = raw.split("NEXT:", 1)
        else:
            fb, nq = raw, "Interview finished."

        return {
            "feedback": fb.strip(),
            "next_question": nq.strip()
        }

    # =========================================================
    # SCORING
    # =========================================================
    async def score_with_metrics(self, question: str, answer: str) -> Dict[str, Any]:
        prompt = f"{SCORER_SYS}\n\nQuestion: {question}\n\nAnswer: {answer}\n\nReturn ONLY JSON."
        raw = await self._generate(prompt)
        return sanitize_metrics(raw)
