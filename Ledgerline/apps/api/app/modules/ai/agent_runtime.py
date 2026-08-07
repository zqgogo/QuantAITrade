from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.ai_config import AgentConfig, AiConfig, load_ai_config
from app.modules.ai.prompt_builder import prompt_builder


@dataclass(frozen=True)
class AgentRequest:
    user_message: str
    workspace_id: int | None = None
    include_context: bool = True
    model: Optional[str] = None


@dataclass(frozen=True)
class AgentResponse:
    content: str
    runtime: str
    model: str
    timestamp: datetime
    context_used: bool


class AgentRuntime(ABC):
    @abstractmethod
    async def run(self, request: AgentRequest) -> AgentResponse:
        raise NotImplementedError


class LedgerlineAgentRuntime(AgentRuntime):
    def __init__(self) -> None:
        self.config = load_ai_config()
        self._llm_provider = None
    
    def _get_llm_provider(self):
        if self._llm_provider is None:
            from app.modules.ai.providers import build_llm_provider
            
            self._llm_provider = build_llm_provider(self.config.active_llm)
        return self._llm_provider
    
    async def run(self, request: AgentRequest) -> AgentResponse:
        messages = prompt_builder.build_prompt(
            request.user_message,
            include_context=request.include_context,
        )
        
        model_name = request.model or self.config.active_llm.default_model
        
        from app.modules.ai.providers import ChatMessage, MockLlmProvider
        
        chat_messages = [ChatMessage(role=m["role"], content=m["content"]) for m in messages]
        
        try:
            provider = self._get_llm_provider()
            response_text = await provider.complete(chat_messages)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("LLM call failed (%s), falling back to Mock: %s", type(e).__name__, str(e)[:200])
            mock_provider = MockLlmProvider(self.config.active_llm)
            response_text = await mock_provider.complete(chat_messages)
            response_text = f"_{response_text}_\n\n---\n⚠️ *Real LLM unavailable ({type(e).__name__}), shown from fallback.*"
        
        return AgentResponse(
            content=response_text,
            runtime="ledgerline",
            model=model_name,
            timestamp=datetime.now(),
            context_used=request.include_context,
        )


class PiCodingAgentRuntime(AgentRuntime):
    async def run(self, request: AgentRequest) -> AgentResponse:
        raise NotImplementedError("Pi-coding-agent adapter is reserved but not wired yet.")


def build_agent_runtime(config: AgentConfig) -> AgentRuntime:
    if config.runtime == "ledgerline":
        return LedgerlineAgentRuntime()
    if config.runtime == "pi_coding_agent":
        return PiCodingAgentRuntime()
    raise ValueError(f"Unsupported agent runtime: {config.runtime}")
