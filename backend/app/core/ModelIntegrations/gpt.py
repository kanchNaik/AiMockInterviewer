# core/gpt/openai_client.py
"""
OpenAI-based backend for LLM providers (AsyncOpenAI).
"""

import os
from typing import List, Dict, Any

from openai import AsyncOpenAI

from .baseclient import BaseLLMClient, SCORER_SYS, sanitize_metrics


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        return (resp.choices[0].message.content or "").strip()

    async def score_with_metrics(self, question: str, answer: str) -> Dict[str, Any]:
        user = f"""Question: {question}

Answer: {answer}

Return ONLY the JSON described above."""
        resp = await self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": SCORER_SYS},
                {"role": "user", "content": user},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        return sanitize_metrics(raw)
