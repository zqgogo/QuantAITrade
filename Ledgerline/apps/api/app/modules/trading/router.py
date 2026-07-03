from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def trading_status() -> dict[str, str]:
    return {"module": "trading", "status": "scaffolded"}

