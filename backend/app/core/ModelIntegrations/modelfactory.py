"""
Provider façade — no chat exposed anymore.
"""

import os
from typing import List, Dict, Any

from .baseclient import BaseLLMClient
from .qwen import QwenClient
from .gpt import OpenAIClient


def _build_client() -> BaseLLMClient:
    name = os.getenv("MODEL_CLIENT_NAME", "qwen").lower()
    if name == "qwen":
        return QwenClient()

    raise RuntimeError(f"Unknown MODEL_CLIENT_NAME: {name}")


_client = _build_client()


async def generate_first_question(meta, history, rag_matches=None):
    return await _client.generate_first_question(meta, history)


async def evaluate_answer_and_followup(question, answer, history):
    return await _client.evaluate_answer_and_followup(question, answer, history)


# async def score_with_metrics(question, answer):
#     openaiclient = OpenAIClient()
#     return await openaiclient.score_with_metrics(question, answer)
