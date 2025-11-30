from typing import List, Dict, Any

from .baseclient import BaseLLMClient, SCORER_SYS, sanitize_metrics


class LlamaClient(BaseLLMClient):
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        print(messages)

    async def score_with_metrics(self, question: str, answer: str) -> Dict[str, Any]:
        return {}