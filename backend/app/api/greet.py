from fastapi import APIRouter
router = APIRouter()

@router.get("/welcome")
def welcome():
    return {
        "message": (
            "👋 Hi! Tell me what you’d like to practise.\n"
            "Example:  “Prep for Google L2 data-analytics”."
        )
    }
