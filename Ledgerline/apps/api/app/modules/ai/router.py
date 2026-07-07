from fastapi import APIRouter, Body, Query

from app.core.ai_config import load_ai_config
from app.modules.ai.agent_runtime import AgentRequest, LedgerlineAgentRuntime
from app.modules.ai.schemas import (
    AiStatusResponse,
    ChatRequest,
    ChatResponse,
    ContextSummary,
)
from app.modules.ai.context_assembler import context_assembler

router = APIRouter()

_runtime = LedgerlineAgentRuntime()


@router.get("/status", response_model=AiStatusResponse)
async def ai_status() -> AiStatusResponse:
    config = load_ai_config()
    available_models = [m.id for m in config.active_llm.models]
    return AiStatusResponse(
        module="ai",
        status="active",
        llm_provider=config.active_provider,
        embedding_provider=config.embedding.provider,
        embedding_model=config.embedding.model,
        agent_runtime=config.agent.runtime,
        available_models=available_models,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest = Body(description="Chat request"),
) -> ChatResponse:
    agent_request = AgentRequest(
        user_message=request.message,
        workspace_id=request.workspace_id,
        include_context=request.include_context,
        model=request.model,
    )
    
    response = await _runtime.run(agent_request)
    
    return ChatResponse(
        content=response.content,
        timestamp=response.timestamp,
        model=response.model,
        runtime=response.runtime,
        context_used=response.context_used,
    )


@router.post("/chat/signal")
async def chat_signal(
    strategy: str = Query(description="Strategy name"),
    symbol: str = Query(description="Trading symbol"),
    market: str = Query(description="Market type"),
    interval: str = Query(description="Time interval"),
) -> ChatResponse:
    from app.modules.ai.prompt_builder import prompt_builder
    from app.modules.ai.providers import ChatMessage
    
    messages = prompt_builder.build_signal_prompt(strategy, symbol, market, interval)
    agent_request = AgentRequest(
        user_message=f"Analyze {strategy} signal for {symbol}",
        include_context=True,
    )
    
    response = await _runtime.run(agent_request)
    
    return ChatResponse(
        content=response.content,
        timestamp=response.timestamp,
        model=response.model,
        runtime=response.runtime,
        context_used=True,
    )


@router.post("/chat/portfolio")
async def chat_portfolio() -> ChatResponse:
    agent_request = AgentRequest(
        user_message="Analyze my portfolio",
        include_context=True,
    )
    
    response = await _runtime.run(agent_request)
    
    return ChatResponse(
        content=response.content,
        timestamp=response.timestamp,
        model=response.model,
        runtime=response.runtime,
        context_used=True,
    )


@router.get("/context", response_model=ContextSummary)
async def get_context() -> ContextSummary:
    ctx = context_assembler.assemble_trading_context()
    return ContextSummary(
        positions_count=ctx["positions_count"],
        total_value=ctx["total_value"],
        recent_trades_count=ctx["recent_trades_count"],
        watchlist_count=0,
    )
