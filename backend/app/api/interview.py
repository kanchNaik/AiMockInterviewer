# interview.py
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException

from ..schemas import (
    StartPayload, StartResponse,
    AnswerPayload, AnswerResponse,
    SaveScorePayload
)
from ..core.state import store
from ..core.ModelIntegrations import modelfactory
from ..core.database import db
from ..core.utilities import ragpipeline
from ..core.ModelIntegrations.gpt import OpenAIClient

router = APIRouter()



DEFAULT_TIMEOUT = 30
async def _with_timeout(coro, fallback, label: str):
    try:
        return await asyncio.wait_for(coro, timeout=DEFAULT_TIMEOUT)
    except Exception as e:
        print(f"[warn] {label} failed:", e)
        return fallback

# ============================================================
# START
# ============================================================
@router.post("/start", response_model=StartResponse)
async def start(payload: StartPayload):
    sid = payload.session_id or str(uuid.uuid4())

    print("Start Interview Payload:", payload)
    meta = {
        "company": payload.company,
        "role": payload.role,
        "seniority": payload.seniority,
        "context": payload.context,
    }

    # initialize session history
    store.new(sid, [])

    rag_cntx = ragpipeline.run_full_pipeline(payload.company, payload.role, payload.seniority)
    question = await _with_timeout(
        modelfactory.generate_first_question(meta, store.get(sid), rag_cntx),
        fallback="Tell me about a recent project you're proud of.",
        label="first_question"
    )

    store.add(sid, {"role": "assistant", "content": question})

    return {"session_id": sid, "question": question}

# ============================================================
# ANSWER
# ============================================================
@router.post("/answer", response_model=AnswerResponse)
async def answer(payload: AnswerPayload):
    hist = store.get(payload.session_id)
    if not hist:
        raise HTTPException(404, "Unknown session_id")

    last_question = next((m["content"] for m in reversed(hist) if m["role"] == "assistant"), "")

    hist.append({"role": "user", "content": payload.text})

    eval_result = await _with_timeout(
        modelfactory.evaluate_answer_and_followup(last_question, payload.text, hist),
        fallback={
            "feedback": "Good attempt. Try adding more detail next time.",
            "next_question": "What is your favorite data quality check?"
        },
        label="feedback+next"
    )

    feedback = eval_result["feedback"]
    nxt = eval_result["next_question"]
    print("next question log", nxt)

    hist.append({"role": "assistant", "content": feedback})
    hist.append({"role": "assistant", "content": nxt})
    openaiclient = OpenAIClient()

    metrics = await _with_timeout(
        openaiclient.score_with_metrics(last_question, payload.text),
        fallback={"overall": None},
        label="metrics"
    )

    overall = metrics.get("overall")
    score_for_field = int(round(overall)) if overall is not None else None

    # persist
    idx = await db["turns"].count_documents({"sessionId": payload.session_id})
    await db["turns"].insert_one({
        "sessionId": payload.session_id,
        "index": idx,
        "question": last_question,
        "userAnswer": payload.text,
        "feedback": feedback,
        "score": score_for_field,
        "metrics": metrics,
        "createdAt": datetime.utcnow(),
    })

    return {
        "feedback": feedback,
        "question": nxt,
        "score": score_for_field
    }
