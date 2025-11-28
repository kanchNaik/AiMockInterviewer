# core/gpt.py
"""
Public LLM façade used across the application.

Other code (like your FastAPI routers) should do:

    from ..core import gpt

and then call:

    await gpt.chat(...)
    await gpt.score_with_metrics(...)
    await gpt.score_answer(...)

Provider is selected via env var MODEL_CLIENT_NAME:

    MODEL_CLIENT_NAME = "openai" | "llama" | "mistral"

Defaults to "openai".
"""

import os
from typing import List, Dict, Any

from .baseclient import BaseLLMClient
from .gpt import OpenAIClient
#from .gpt_llama import LlamaClient
#from .gpt_mistral import MistralClient


def _build_client() -> BaseLLMClient:
    name = os.getenv("MODEL_CLIENT_NAME", "openai").lower()

    if name == "openai":
        return OpenAIClient()
    # if name == "llama":
    #     return LlamaClient()
    # if name == "mistral":
    #     return MistralClient()

    raise RuntimeError(
        f"Unknown MODEL_CLIENT_NAME '{name}'. Supported values: openai, llama, mistral."
    )


# Single global client used by the module-level helpers below
_client: BaseLLMClient = _build_client()


async def chat(messages: List[Dict[str, str]]) -> str:
    """Provider-agnostic chat interface."""
    return await _client.chat(messages)


async def score_with_metrics(question: str, answer: str) -> Dict[str, Any]:
    """Provider-agnostic metrics scoring interface."""
    return await _client.score_with_metrics(question, answer)


async def score_answer(question: str, answer: str) -> int:
    """Provider-agnostic overall integer score 0..10."""
    return await _client.score_answer(question, answer)
