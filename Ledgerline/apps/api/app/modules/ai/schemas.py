from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(description="Message role: system, user, assistant")
    content: str = Field(description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(description="User message")
    session_id: Optional[int] = Field(None, description="Session ID (creates new if omitted)")
    workspace_id: Optional[int] = Field(None, description="Workspace ID for context")
    include_context: bool = Field(True, description="Whether to include trading context")
    model: Optional[str] = Field(None, description="Override default model")


class ChatResponse(BaseModel):
    content: str = Field(description="AI response content")
    timestamp: datetime = Field(description="Response timestamp")
    model: str = Field(description="Model used")
    runtime: str = Field(description="Agent runtime")
    context_used: bool = Field(description="Whether context was used")
    session_id: Optional[int] = Field(None, description="Session ID")


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    workspace_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSessionResponse]


class ChatMessageRecord(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ChatSessionDetailResponse(BaseModel):
    id: int
    title: str
    workspace_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageRecord]


class ChatHistoryItem(BaseModel):
    id: str = Field(description="Message ID")
    role: str = Field(description="Message role")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(description="Message timestamp")


class ChatHistoryResponse(BaseModel):
    messages: List[ChatHistoryItem] = Field(description="Chat history")


class ContextSummary(BaseModel):
    positions_count: int = Field(description="Number of open positions")
    total_value: float = Field(description="Total portfolio value")
    recent_trades_count: int = Field(description="Number of recent trades")
    watchlist_count: int = Field(description="Number of watchlist items")


class AiStatusResponse(BaseModel):
    module: str = Field(description="Module name")
    status: str = Field(description="Module status")
    llm_provider: str = Field(description="Active LLM provider")
    embedding_provider: str = Field(description="Embedding provider")
    embedding_model: str = Field(description="Embedding model")
    agent_runtime: str = Field(description="Agent runtime")
    available_models: List[str] = Field(description="Available models")
