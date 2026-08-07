from fastapi import APIRouter, Body, HTTPException, Query
from sqlalchemy import func, select

from app.core.ai_config import load_ai_config
from app.db.session import TradingSessionLocal
from app.modules.ai.agent_runtime import AgentRequest, LedgerlineAgentRuntime
from app.modules.ai.models import ChatMessage as ChatMessageModel
from app.modules.ai.models import ChatSession
from app.modules.ai.schemas import (
    AiStatusResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionDetailResponse,
    ChatSessionListResponse,
    ChatSessionResponse,
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


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions() -> ChatSessionListResponse:
    db = TradingSessionLocal()
    try:
        rows = db.execute(
            select(
                ChatSession,
                func.count(ChatMessageModel.id).label("message_count"),
            )
            .outerjoin(ChatMessageModel)
            .group_by(ChatSession.id)
            .order_by(ChatSession.updated_at.desc())
        ).all()
        sessions = [
            ChatSessionResponse(
                id=s.id,
                title=s.title,
                workspace_id=s.workspace_id,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=count,
            )
            for s, count in rows
        ]
        return ChatSessionListResponse(sessions=sessions)
    finally:
        db.close()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(title: str = Body(..., embed=True)) -> ChatSessionResponse:
    db = TradingSessionLocal()
    try:
        session = ChatSession(title=title[:200])
        db.add(session)
        db.commit()
        db.refresh(session)
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            workspace_id=session.workspace_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0,
        )
    finally:
        db.close()


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_session(session_id: int) -> ChatSessionDetailResponse:
    db = TradingSessionLocal()
    try:
        session = db.get(ChatSession, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        messages = (
            db.query(ChatMessageModel)
            .filter(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
            .all()
        )
        return ChatSessionDetailResponse(
            id=session.id,
            title=session.title,
            workspace_id=session.workspace_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at,
                }
                for m in messages
            ],
        )
    finally:
        db.close()


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int) -> dict:
    db = TradingSessionLocal()
    try:
        session = db.get(ChatSession, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        db.delete(session)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest = Body(description="Chat request"),
) -> ChatResponse:
    from datetime import datetime
    db = TradingSessionLocal()
    try:
        if request.session_id:
            session = db.get(ChatSession, request.session_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            title = request.message[:60] if request.message else "New chat"
            session = ChatSession(title=title)
            db.add(session)
            db.commit()
            db.refresh(session)

        user_msg = ChatMessageModel(
            session_id=session.id,
            role="user",
            content=request.message,
        )
        db.add(user_msg)

        agent_request = AgentRequest(
            user_message=request.message,
            workspace_id=request.workspace_id,
            include_context=request.include_context,
            model=request.model,
        )

        try:
            response = await _runtime.run(agent_request)
            ai_content = response.content
        except Exception as e:
            ai_content = f"[AI Error] {type(e).__name__}: {e}"

        ai_msg = ChatMessageModel(
            session_id=session.id,
            role="assistant",
            content=ai_content,
        )
        db.add(ai_msg)
        db.commit()

        return ChatResponse(
            content=ai_content,
            timestamp=datetime.utcnow(),
            model=request.model or "unknown",
            runtime="ledgerline",
            context_used=request.include_context,
            session_id=session.id,
        )
    finally:
        db.close()


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
