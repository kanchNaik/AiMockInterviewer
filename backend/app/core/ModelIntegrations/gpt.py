"""
Updated OpenAI client for new high-level architecture.
"""

import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI


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

