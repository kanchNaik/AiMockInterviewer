"""
Qwen HF Endpoint Client
- Uses HF text generation API
- Implements new high-level methods
"""

import os
import re
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
    async def _generate(self, prompt: str, max_tokens: int = 500, stop_sequences: List[str] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        print("Qwen Prompt: ", prompt)
        # Default stop sequences - order matters! Most specific first
        if stop_sequences is None:
            stop_sequences = ["Answer:", "\n\nAnswer", "\nAnswer:", "\n\n", "\n1.", "\n2.", "\n3.", "<|im_end|>"]

        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.7,
                "max_new_tokens": max_tokens,
                "top_p": 0.9,
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        generated = ""
        if isinstance(data, list):
            generated = data[0].get("generated_text", "").strip()
        else:
            generated = data.get("generated_text", "").strip()
        
        # POST-PROCESSING: Remove the prompt if it's still in the output
        if prompt in generated:
            generated = generated.replace(prompt, "").strip()
        
        # Apply stop sequences manually - stop at first occurrence
        if stop_sequences:
            for stop_seq in stop_sequences:
                if stop_seq in generated:
                    generated = generated.split(stop_seq)[0].strip()
                    break  # Stop at first match
        
        # Extract only the first meaningful line/question
        lines = [line.strip() for line in generated.split("\n") if line.strip()]
        if lines:
            first_line = lines[0]
            # Remove common numbering patterns
            first_line = re.sub(r'^\d+[\.)]\s*', '', first_line)
            first_line = re.sub(r'^Question\s*\d*[\.:)]*\s*', '', first_line, flags=re.IGNORECASE)
            first_line = re.sub(r'^Q\d*[\.:)]\s*', '', first_line, flags=re.IGNORECASE)
            return first_line.strip()
        
        return generated

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
                
        # IMPROVED PROMPT - more explicit about single question output
        prompt = f"""{rag_context}You are an expert interviewer.

Generate ONE interview question based on:
Company: {meta.get('company')}
Role: {meta.get('role')}
Seniority: {meta.get('seniority')}
Context: {meta.get('context')}

Rules:
- Output ONLY the question
- No numbering
- No explanation
- No multiple questions
- No answers

Question:"""

        # Use shorter max_tokens for questions to prevent rambling
        return await self._generate(
            prompt, 
            max_tokens=100,  # Short limit to reduce multi-question output
            stop_sequences=["Answer:", "\n\nAnswer", "\nAnswer:", "\n\n", "\nQuestion", "\n1.", "\n2.", "\nContext:"]
        )

    # =========================================================
    # PUBLIC: FEEDBACK + NEXT
    # =========================================================
    async def evaluate_answer_and_followup(self, question: str, answer: str, history: List[Dict[str, str]]):
        prompt = f"""Evaluate this interview answer in 2-3 sentences, then generate the next question.

Question: {question}
Answer: {answer}

Format:
FEEDBACK: <your evaluation>
NEXT: <next question>

Output:
FEEDBACK:"""

        # Allow generous tokens for feedback + question
        raw = await self._generate(
            prompt, 
            max_tokens=600,  # Generous limit for feedback + next question
            stop_sequences=["\n\n\n"]  # Minimal stops to allow complete response
        )

        if "NEXT:" in raw:
            fb, nq = raw.split("NEXT:", 1)
        else:
            fb, nq = raw, "Interview finished."

        return {
            "feedback": fb.replace("FEEDBACK:", "").strip(),
            "next_question": nq.strip()
        }

    # =========================================================
    # SCORING
    # =========================================================
    async def score_with_metrics(self, question: str, answer: str) -> Dict[str, Any]:
        prompt = f"{SCORER_SYS}\n\nQuestion: {question}\n\nAnswer: {answer}\n\nReturn ONLY JSON."
        
        # Use high token limit for complete JSON generation
        raw = await self._generate(
            prompt, 
            max_tokens=1500,  # High limit to avoid JSON truncation
            stop_sequences=[]  # No stop sequences - let JSON complete
        )
        
        return sanitize_metrics(raw)
