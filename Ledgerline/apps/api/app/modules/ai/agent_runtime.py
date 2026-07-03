from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.ai_config import AgentConfig


@dataclass(frozen=True)
class AgentRequest:
    user_message: str
    workspace_id: int | None = None


@dataclass(frozen=True)
class AgentResponse:
    content: str
    runtime: str


class AgentRuntime(ABC):
    @abstractmethod
    async def run(self, request: AgentRequest) -> AgentResponse:
        raise NotImplementedError


class LedgerlineAgentRuntime(AgentRuntime):
    async def run(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(content="Ledgerline agent runtime scaffolded.", runtime="ledgerline")


class PiCodingAgentRuntime(AgentRuntime):
    async def run(self, request: AgentRequest) -> AgentResponse:
        raise NotImplementedError("Pi-coding-agent adapter is reserved but not wired yet.")


def build_agent_runtime(config: AgentConfig) -> AgentRuntime:
    if config.runtime == "ledgerline":
        return LedgerlineAgentRuntime()
    if config.runtime == "pi_coding_agent":
        return PiCodingAgentRuntime()
    raise ValueError(f"Unsupported agent runtime: {config.runtime}")
