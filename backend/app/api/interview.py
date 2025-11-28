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

router = APIRouter()

SYSTEM_TMPL = (
    "You are an expert {role} interviewer (seniority: {seniority}). "
    "Ask ONE clear, concise question at a time. Increase difficulty gradually "
    "if the candidate performs well."
)

def system_msg(role: str, seniority: str) -> dict:
    return {"role": "system", "content": SYSTEM_TMPL.format(role=role, seniority=seniority)}

# ---- avoid hangs ----
DEFAULT_TIMEOUT = 30  # seconds
async def _with_timeout(coro, fallback, label: str, timeout=DEFAULT_TIMEOUT):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except Exception as e:
        print(f"[warn] {label} failed or timed out:", e)
        return fallback

@router.post("/start", response_model=StartResponse)
async def start(payload: StartPayload):
    sid = payload.session_id or str(uuid.uuid4())
    store.new(sid, system_msg(payload.role, payload.seniority))

    first_prompt = (
        "Generate the FIRST interview question only.\n"
        f"Company: {payload.company or 'generic'}\n"
        f"Role: {payload.role}\n"
        f"Seniority/Level: {payload.seniority or 'unspecified'}\n"
        f"Candidate brief (optional): {payload.context or 'n/a'}\n\n"
        "Rules:\n"
        "- Return a single well-formed question, no preamble, no explanation.\n"
        "- Keep it relevant to the company/role/level and any brief above.\n"
        "- Avoid multi-part questions; one focused question."
    )

    store.add(sid, {"role": "user", "content": first_prompt})
    question = await _with_timeout(
        modelfactory.chat(store.get(sid)),
        fallback="Tell me about a recent data project you’re proud of and your role in it.",
        label="modelfactory.chat(first question)",
    )
    store.add(sid, {"role": "assistant", "content": question})

    return {"session_id": sid, "question": question}

@router.post("/answer", response_model=AnswerResponse)
async def answer(payload: AnswerPayload):
    hist = store.get(payload.session_id)
    if not hist:
        raise HTTPException(status_code=404, detail="Unknown session_id; call /start first")

    last_question = next((m["content"] for m in reversed(hist) if m["role"] == "assistant"), "") or ""

    # user answer + ask for feedback & next Q
    hist.append({"role": "user", "content": payload.text})
    hist.append({
        "role": "user",
        "content": (
            "Evaluate my answer briefly in ≤3 sentences (focus on correctness, clarity, completeness). "
            "Then write 'NEXT:' followed by the single next question."
        ),
    })

    full = await _with_timeout(
        modelfactory.chat(hist),
        fallback="Good start. Consider adding specific metrics next time.\n\nNEXT: What are your favorite data quality checks and why?",
        label="modelfactory.chat(feedback+next)",
    )
    hist.append({"role": "assistant", "content": full})

    if "NEXT:" in full:
        feedback, nxt = full.split("NEXT:", 1)
    else:
        feedback, nxt = full, "Interview finished."

    # NEW: detailed metrics (and overall)
    metrics = await _with_timeout(
        modelfactory.score_with_metrics(last_question, payload.text),
        fallback={"technical_correctness": None, "clarity": None, "completeness": None, "tone": None,
                  "overall": None, "flags": {}, "notes": ""},
        label="modelfactory.score_with_metrics",
    )
    overall = None if (metrics.get("overall") is None) else float(metrics.get("overall"))
    score_for_field = int(round(overall)) if (overall is not None) else None

    # persist
    try:
        idx = await db["turns"].count_documents({"sessionId": payload.session_id})
        await db["turns"].insert_one({
            "sessionId": payload.session_id,
            "index": idx,
            "question": last_question,
            "userAnswer": payload.text,
            "feedback": feedback.strip(),
            "score": score_for_field,
            "metrics": metrics,             # <-- SAVE METRICS
            "createdAt": datetime.utcnow(),
        })
    except Exception as e:
        print("[warn] turn insert failed:", e)

    return {"feedback": feedback.strip(), "question": nxt.strip(), "score": score_for_field}

@router.post("/session/{session_id}/score")
async def save_session_score(session_id: str, payload: SaveScorePayload):
    if payload.scores:
        for row in payload.scores:
            try:
                idx = int(row.get("index", -1))
            except Exception:
                idx = -1
            if idx >= 0 and row.get("score") is not None:
                try:
                    await db["turns"].update_one(
                        {"sessionId": session_id, "index": idx},
                        {"$set": {"score": int(row["score"])}},
                    )
                except Exception as e:
                    print("[warn] turn score update failed:", e)

    try:
        await db["sessions"].update_one(
            {"sessionId": session_id},
            {"$set": {"overallScore": payload.overall, "updatedAt": datetime.utcnow()}},
        )
    except Exception as e:
        print("[warn] session overall score save failed:", e)

    return {"ok": True, "overall": payload.overall}
