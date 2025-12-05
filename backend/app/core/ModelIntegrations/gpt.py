"""
Updated OpenAI client for new high-level architecture.
"""

import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from .baseclient import BaseLLMClient, SCORER_SYS, sanitize_metrics


class OpenAIClient(BaseLLMClient):

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
    # HIGH-LEVEL: First Question
    # ------------------------------------------------------
    async def generate_first_question(self, meta: dict, history: List[Dict[str, str]], rag_matches: Optional[List[Dict[str, str]]] = None):

        # NEW FIX — CLEAN HISTORY
        clean_history = [
            m for m in history
            if isinstance(m, dict) and isinstance(m.get("content"), str) and "role" in m
        ]

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


        system_prompt = (
            f"You are an expert {meta.get('role')} interviewer (seniority: {meta.get('seniority')}). "
            "Ask ONE clear, concise question at a time. Increase difficulty gradually if the candidate performs well."
        )

        prompt = (
            f"{rag_context}"
            "Generate the FIRST interview question only.\n"
            f"Company: {meta.get('company')}\n"
            f"Role: {meta.get('role')}\n"
            f"Seniority: {meta.get('seniority')}\n"
            f"Context: {meta.get('context')}\n\n"
            "Rules:\n"
            "- One single question\n"
            "- No explanation\n"
            "- No multi-part questions\n"
            "- Use User Context to understand user data"
        )

        msgs = [{"role": "system", "content": system_prompt}]
        msgs += clean_history
        msgs.append({"role": "user", "content": prompt})
        print("Prompt sent to Qwen Model", msgs)
        return await self._chat(msgs)


    # ------------------------------------------------------
    # HIGH-LEVEL: Feedback + Next
    # ------------------------------------------------------
    async def evaluate_answer_and_followup(self, question: str, answer: str, history: List[Dict[str, str]]):
        clean_history = [
            m for m in history
            if isinstance(m, dict) and isinstance(m.get("content"), str) and "role" in m
        ]

        msgs = clean_history.copy()
        msgs.append({"role": "user", "content": answer})
        msgs.append({
            "role": "user",
            "content": (
                "Evaluate my answer in ≤3 sentences.\n"
                "Then write 'NEXT:' followed by the next question."
            )
        })

        raw = await self._chat(msgs)

        if "NEXT:" in raw:
            fb, nq = raw.split("NEXT:", 1)
        else:
            fb, nq = raw, "Interview finished."

        return {
            "feedback": fb.strip(),
            "next_question": nq.strip()
        }

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
        return sanitize_metrics(raw)
