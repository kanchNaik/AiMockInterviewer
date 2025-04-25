import uuid
from fastapi import APIRouter, HTTPException, Depends
from ..schemas import *
from ..core.session import MemorySessionStore, SessionStore
from ..core import gpt

router = APIRouter()
store: SessionStore = MemorySessionStore()      # 💡 swap later

SYSTEM_TMPL = (
    "You are an expert {role} interviewer (seniority: {seniority}). "
    "Ask ONE clear question at a time, getting harder if the candidate performs well."
)

def system_msg(role: str, seniority: str) -> dict:
    return {"role": "system", "content": SYSTEM_TMPL.format(role=role, seniority=seniority)}

# -------- routes --------
@router.post("/start", response_model=StartResponse)
async def start(payload: StartPayload):
    sid = payload.session_id or str(uuid.uuid4())
    store.new(sid, system_msg(payload.role, payload.seniority))

    # first question
    store.add(sid, {"role": "user", "content": "GENERATE"})
    question = await gpt.chat(store.get(sid))
    store.add(sid, {"role": "assistant", "content": question})
    return {"session_id": sid, "question": question}

@router.post("/answer", response_model=AnswerResponse)
async def answer(payload: AnswerPayload):
    hist = store.get(payload.session_id)
    if not hist:
        raise HTTPException(404, "Unknown session_id; call /start first")

    hist.append({"role": "user", "content": payload.text})
    hist.append({
        "role": "user",
        "content": (
            "Give brief feedback on my answer (≤3 sentences). "
            "Then say 'NEXT:' and ask the next question."
        ),
    })
    full = await gpt.chat(hist)
    hist.append({"role": "assistant", "content": full})

    if "NEXT:" in full:
        feedback, nxt = full.split("NEXT:", 1)
    else:
        feedback, nxt = full, "Interview finished."

    return {"feedback": feedback.strip(), "question": nxt.strip()}
