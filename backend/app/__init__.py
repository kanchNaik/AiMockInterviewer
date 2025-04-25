from fastapi import FastAPI
from .api.interview import router as interview_router

def create_app() -> FastAPI:
    app = FastAPI(title="LLM Mock Interviewer", version="0.1.0")
    app.include_router(interview_router, prefix="/interview", tags=["interview"])
    return app
