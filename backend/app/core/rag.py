import asyncio
import json
import os
import re
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover - optional dependency during tests
    genai = None

try:
    from pinecone import Pinecone  # type: ignore
except ImportError:  # pragma: no cover - optional dependency during tests
    Pinecone = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:  # pragma: no cover - optional dependency during tests
    SentenceTransformer = None


class RagConfigError(RuntimeError):
    """Raised when the pipeline is missing a required dependency or secret."""


PINECONE_DEFAULT_API_KEY = "pcsk_3F9eV3_D1QAZpq2i7hvw4QqEG2yDrJSuKhjDrCqBAeAQFCS6ExTsCsoa3YV4zEhgyyXSHF"
PINECONE_DEFAULT_INDEX = "ai-mock-interview-questions"
GEMINI_DEFAULT_API_KEY = "AIzaSyDOFayV5Os2vj_izABkBUuOizaat6rbTZg"
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"


class RagPipeline:
    """Encapsulates metadata extraction + embedding + Pinecone search."""

    def __init__(self) -> None:
        self._pinecone_api_key = (
            os.getenv("RAG_PINECONE_API_KEY")
            or os.getenv("PINECONE_API_KEY")
            or PINECONE_DEFAULT_API_KEY
        )
        self._pinecone_index_name = os.getenv("RAG_PINECONE_INDEX", PINECONE_DEFAULT_INDEX)
        self._embed_model_name = os.getenv("RAG_EMBED_MODEL", "all-MiniLM-L6-v2")
        self._gemini_api_key = os.getenv("GEMINI_API_KEY") or GEMINI_DEFAULT_API_KEY
        self._gemini_model_name = os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)

        self._pinecone_client = None
        self._pinecone_index = None
        self._embed_model = None
        self._gemini_model = None

    # ---- Internal helpers -------------------------------------------------

    def _ensure_pinecone_index(self):
        if not self._pinecone_api_key:
            raise RagConfigError("PINECONE_API_KEY (or RAG_PINECONE_API_KEY) is not configured.")
        if Pinecone is None:
            raise RagConfigError("pinecone package is not installed. Add 'pinecone-client' to requirements.")
        if self._pinecone_index is None:
            self._pinecone_client = Pinecone(api_key=self._pinecone_api_key)
            self._pinecone_index = self._pinecone_client.Index(self._pinecone_index_name)
        return self._pinecone_index

    def _ensure_embed_model(self):
        if SentenceTransformer is None:
            raise RagConfigError("sentence-transformers package is missing.")
        if self._embed_model is None:
            self._embed_model = SentenceTransformer(self._embed_model_name)
        return self._embed_model

    def _ensure_gemini_model(self):
        if not self._gemini_api_key or genai is None:
            return None
        if self._gemini_model is None:
            genai.configure(api_key=self._gemini_api_key)
            self._gemini_model = genai.GenerativeModel(self._gemini_model_name)
        return self._gemini_model

    # ---- Metadata helpers -------------------------------------------------

    def _canonicalize_metadata(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
        if not metadata:
            return {}
        mapping = {}
        company = metadata.get("company") or metadata.get("Company")
        role = metadata.get("role") or metadata.get("Role")
        round_number = (
            metadata.get("round_number")
            or metadata.get("roundNumber")
            or metadata.get("Round Number")
            or metadata.get("RoundNumber")
        )
        if company:
            mapping["company"] = str(company).strip()
        if role:
            mapping["role"] = str(role).strip()
        if round_number:
            mapping["round_number"] = str(round_number).strip()
        return mapping

    def _normalize_metadata(self, metadata: Dict[str, str]) -> Dict[str, Optional[str]]:
        norm: Dict[str, Optional[str]] = {"company": None, "role": None, "round_number": None}

        if metadata.get("company"):
            norm["company"] = metadata["company"].strip()

        if metadata.get("role"):
            norm["role"] = metadata["role"].strip().title()

        round_value = metadata.get("round_number")
        if round_value:
            val = round_value.strip()
            norm["round_number"] = val if val.lower().startswith("round") else f"Round {val}"

        return norm

    def _build_filter(self, metadata: Dict[str, Optional[str]]) -> Optional[Dict[str, Any]]:
        and_clauses: List[Dict[str, Any]] = []
        if metadata.get("company"):
            and_clauses.append({"Company": {"$eq": metadata["company"]}})
        if metadata.get("role"):
            and_clauses.append({"Role": {"$eq": metadata["role"]}})
        if metadata.get("round_number"):
            and_clauses.append({"Round Number": {"$eq": metadata["round_number"]}})
        return {"$and": and_clauses} if and_clauses else None

    def _build_query_string(self, user_query: str, metadata: Dict[str, Optional[str]]) -> str:
        role = metadata.get("role")
        round_number = metadata.get("round_number")
        if role or round_number:
            round_part = f" {round_number}" if round_number else ""
            return f"interview questions for {role or ''}{round_part}".strip()
        return user_query.strip()

    # ---- External calls ---------------------------------------------------

    async def _encode(self, text: str) -> List[float]:
        model = self._ensure_embed_model()
        return await asyncio.to_thread(lambda: model.encode(text).tolist())

    async def _pinecone_query(self, vector: List[float], top_k: int, metadata_filter: Optional[Dict[str, Any]]):
        index = self._ensure_pinecone_index()

        def _query():
            return index.query(vector=vector, top_k=top_k, include_metadata=True, filter=metadata_filter)

        return await asyncio.to_thread(_query)

    async def _extract_metadata(self, query: str) -> Dict[str, str]:
        model = self._ensure_gemini_model()
        if model is None:
            return {}

        prompt = f"""
Extract the following information from the sentence below:

Sentence: \"{query}\"

Return a JSON object with:
- Company
- Role
- Round Number

Format:
{{
  "Company": "...",
  "Role": "...",
  "Round Number": "..."
}}
"""

        def _run():
            response = model.generate_content(prompt)
            text = (getattr(response, "text", None) or "").strip()
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return {}
            try:
                payload = json.loads(match.group())
            except json.JSONDecodeError:
                return {}
            return {
                "company": payload.get("Company"),
                "role": payload.get("Role"),
                "round_number": payload.get("Round Number"),
            }

        return await asyncio.to_thread(_run)

    # ---- Public API -------------------------------------------------------

    async def search(
        self,
        *,
        user_query: str,
        top_k: int = 5,
        provided_metadata: Optional[Dict[str, Any]] = None,
        skip_gemini: bool = False,
    ) -> Dict[str, Any]:
        if not user_query or not user_query.strip():
            raise ValueError("query must not be empty")

        sanitized_top_k = max(1, min(top_k, 25))

        provided = self._canonicalize_metadata(provided_metadata)

        extracted = {}
        if not skip_gemini:
            extracted = await self._extract_metadata(user_query)

        merged = {**extracted, **provided}
        normalized = self._normalize_metadata(merged)

        query_string = self._build_query_string(user_query, normalized)
        vector = await self._encode(query_string)

        metadata_filter = self._build_filter(normalized)
        response = await self._pinecone_query(vector, sanitized_top_k, metadata_filter)
        matches = (response.get("matches") if isinstance(response, dict) else getattr(response, "matches", [])) or []

        if not matches and metadata_filter:
            response = await self._pinecone_query(vector, sanitized_top_k, None)
            matches = (response.get("matches") if isinstance(response, dict) else getattr(response, "matches", [])) or []

        results = []
        for match in matches:
            if isinstance(match, dict):
                metadata = (match.get("metadata") or {}) if isinstance(match.get("metadata"), dict) else {}
                score = match.get("score")
                match_id = match.get("id")
            else:
                metadata = getattr(match, "metadata", {}) or {}
                score = getattr(match, "score", None)
                match_id = getattr(match, "id", None)

            text = metadata.get("text") or metadata.get("Topic Questions") or ""
            results.append(
                {
                    "id": match_id or "",
                    "score": float(score) if score is not None else None,
                    "question": text,
                    "metadata": metadata,
                }
            )

        return {
            "query": query_string,
            "metadata": normalized,
            "matches": results,
        }


_pipeline: Optional[RagPipeline] = None


def get_pipeline() -> RagPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RagPipeline()
    return _pipeline
