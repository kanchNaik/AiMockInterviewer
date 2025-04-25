from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from ..core import ner
from .interview import start as start_interview, StartPayload
from ..core.session import MemorySessionStore          # ← import the class

# ------------------------------------------------------------------
# create ONE in-memory store for the whole app
store = MemorySessionStore()
# ------------------------------------------------------------------

router = APIRouter(prefix="/session", tags=["session"])


class SessionReq(BaseModel):
    user_text: str
    session_id: str | None = None   # optional on POST


class SessionResp(BaseModel):
    session_id: str
    question: str


# ---------- 1) create -------------------------------------------------
@router.post("", response_model=SessionResp)
async def create(req: SessionReq):
    slots = await ner.extract(req.user_text)
    if not all(slots.values()):
        missing = ", ".join(k for k, v in slots.items() if v is None)
        raise HTTPException(422, f"Need: {missing}")

    start_payload = StartPayload(session_id=req.session_id, **slots)
    data = await start_interview(start_payload)
    return {"session_id": data["session_id"], "question": data["question"]}


# ---------- 2) patch / reset -----------------------------------------
@router.patch("/{sid}", response_model=SessionResp)
async def reset(
    req: SessionReq,
    sid: str = Path(..., description="Existing session to reset"),
):
    if sid not in store._store:          # type: ignore[attr-defined]
        raise HTTPException(404, "Unknown session_id")

    # wipe old chat & start fresh
    store._store.pop(sid)
    req.session_id = sid
    return await create(req)
