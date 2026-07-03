from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def ai_status() -> dict[str, str]:
    return {"module": "ai", "status": "scaffolded"}

