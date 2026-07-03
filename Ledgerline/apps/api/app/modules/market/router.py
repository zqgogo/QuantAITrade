from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def market_status() -> dict[str, str]:
    return {"module": "market", "status": "scaffolded"}

