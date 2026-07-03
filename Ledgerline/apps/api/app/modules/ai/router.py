from fastapi import APIRouter

from app.core.ai_config import load_ai_config

router = APIRouter()


@router.get("/status")
async def ai_status() -> dict[str, str]:
    config = load_ai_config()
    return {
        "module": "ai",
        "status": "scaffolded",
        "llm_provider": config.active_provider,
        "embedding_provider": config.embedding.provider,
        "embedding_model": config.embedding.model,
        "agent_runtime": config.agent.runtime,
    }
