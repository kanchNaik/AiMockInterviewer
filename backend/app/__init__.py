from fastapi import FastAPI
from .api.interview import router as interview_router
from .api.greet import router as greet_router
from .api.session import router as session_router

def create_app() -> FastAPI:
    app = FastAPI(title="LLM Mock Interviewer", version="0.1.0")
    app.include_router(interview_router, prefix="/interview", tags=["interview"])
    app.include_router(greet_router, tags=["misc"])
    app.include_router(session_router)
    return app
