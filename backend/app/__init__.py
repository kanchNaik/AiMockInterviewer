from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.interview import router as interview_router
from .api.greet import router as greet_router
from .api.session import router as session_router

def create_app() -> FastAPI:
    app = FastAPI(title="LLM Mock Interviewer", version="0.1.0")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Allow React frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(interview_router, prefix="/interview", tags=["interview"])
    app.include_router(greet_router, tags=["misc"])
    app.include_router(session_router)

    return app
