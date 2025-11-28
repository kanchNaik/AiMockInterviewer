from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# ---- interview flow payloads / responses ----

class StartPayload(BaseModel):
    """
    Payload to initialize an interview session.
    - company/context are optional; used to craft a better first question.
    """
    session_id: Optional[str] = None
    role: str = "Data Scientist"
    seniority: str = "mid"
    company: Optional[str] = None
    context: Optional[str] = None

class StartResponse(BaseModel):
    session_id: str
    question: str

class AnswerPayload(BaseModel):
    session_id: str
    text: str

class AnswerResponse(BaseModel):
    feedback: str
    question: str
    score: Optional[int] = None  # 0..10

# save overall session score at end
class SaveScorePayload(BaseModel):
    scores: Optional[List[Dict]] = None  # [{index:int, question:str, score:Optional[int]}]
    overall: Optional[float] = None


# ---- RAG pipeline payloads ----

class RAGMetadata(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    round_number: Optional[str] = None


class RAGQueryPayload(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=25)
    metadata: Optional[RAGMetadata] = None
    skip_gemini: bool = False


class RAGMatch(BaseModel):
    id: str
    score: Optional[float] = None
    question: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    query: str
    metadata: RAGMetadata
    matches: List[RAGMatch]
