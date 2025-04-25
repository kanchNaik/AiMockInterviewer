from pydantic import BaseModel

class StartPayload(BaseModel):
    session_id: str | None = None
    role: str = "Data Scientist"
    seniority: str = "mid"

class StartResponse(BaseModel):
    session_id: str
    question: str

class AnswerPayload(BaseModel):
    session_id: str
    text: str

class AnswerResponse(BaseModel):
    feedback: str
    question: str
