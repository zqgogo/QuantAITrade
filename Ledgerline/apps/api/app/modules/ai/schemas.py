from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(description="Message role: system, user, assistant")
    content: str = Field(description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(description="User message")
    workspace_id: Optional[int] = Field(None, description="Workspace ID for context")
    include_context: bool = Field(True, description="Whether to include trading context")
    model: Optional[str] = Field(None, description="Override default model")


class ChatResponse(BaseModel):
    content: str = Field(description="AI response content")
    timestamp: datetime = Field(description="Response timestamp")
    model: str = Field(description="Model used")
    runtime: str = Field(description="Agent runtime")
    context_used: bool = Field(description="Whether context was used")


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
