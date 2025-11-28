from fastapi import APIRouter, HTTPException

from ..core.rag import RagConfigError, get_pipeline
from ..schemas import RAGQueryPayload, RAGResponse

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", response_model=RAGResponse)
async def search_questions(payload: RAGQueryPayload) -> RAGResponse:
    pipeline = get_pipeline()
    try:
        result = await pipeline.search(
            user_query=payload.query,
            top_k=payload.top_k,
            provided_metadata=payload.metadata.dict(exclude_none=True) if payload.metadata else None,
            skip_gemini=payload.skip_gemini,
        )
    except RagConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # pragma: no cover - log and expose generic error
        print("[error] rag search failed:", exc)
        raise HTTPException(status_code=500, detail="RAG search failed")

    return RAGResponse(
        query=result.get("query", payload.query),
        metadata=result.get("metadata", {}),
        matches=result.get("matches", []),
    )
