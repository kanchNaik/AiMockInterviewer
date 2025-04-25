"""
LLM wrapper compatible with openai-python v1.x
"""

import os
from typing import List, Dict
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


async def chat(messages: List[Dict[str, str]]) -> str:
    """
    messages -> single assistant string
    """
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()
