from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.interview import router as interview_router
from .api.greet import router as greet_router
from .api.session import router as session_router
from .api import auth
from .core.database import db
from .api import audio
from .api import resume


def create_app() -> FastAPI:
    app = FastAPI(title="LLM Mock Interviewer", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(interview_router, prefix="/interview", tags=["interview"])
    app.include_router(greet_router, tags=["misc"])
    app.include_router(session_router)
    app.include_router(auth.router)
    app.include_router(audio.router)
    app.include_router(resume.router, prefix="/api/resume")


    @app.on_event("startup")
    async def ensure_indexes():
        await db["users"].create_index("email", unique=True)
        await db["sessions"].create_index("userEmail")
        await db["turns"].create_index([("sessionId", 1), ("index", 1)], unique=True)

    return app