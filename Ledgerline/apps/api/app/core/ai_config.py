import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import settings


class ModelOption(BaseModel):
    id: str
    name: str


class LlmProviderConfig(BaseModel):
    name: str
    base_url: str
    api_key: str
    api_mode: str = "chat_completions"
    models: list[ModelOption]
    default_model: str
    temperature: float = 0.2
    max_tokens: int = 1200


class EmbeddingConfig(BaseModel):
    provider: Literal["local", "openai", "ollama", "custom"] = "local"
    model: str = "BAAI/bge-m3"
    base_url: str | None = None
    api_key: str | None = None
    device: str = "auto"
    dimensions: int = 1024
    normalize: bool = True


class VectorStoreConfig(BaseModel):
    provider: Literal["chromadb", "memory"] = "chromadb"
    path: str = "./var/chroma"
    collection_prefix: str = "ledgerline"


class AgentConfig(BaseModel):
    runtime: Literal["ledgerline", "pi_coding_agent"] = "ledgerline"
    available_runtimes: list[str] = Field(default_factory=lambda: ["ledgerline", "pi_coding_agent"])
    allow_trade_execution: bool = False
    max_tool_calls: int = 6


class AiConfig(BaseModel):
    providers: dict[str, LlmProviderConfig]
    active_provider: str = "ollama"
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)

    @property
    def active_llm(self) -> LlmProviderConfig:
        return self.providers[self.active_provider]


def _config_root() -> Path:
    api_root = Path(__file__).resolve().parents[2]
    return (api_root / settings.config_dir).resolve()


def get_ai_config_path() -> Path:
    root = _config_root()
    private_path = root / settings.llm_config_file
    if private_path.exists():
        return private_path
    return root / settings.llm_demo_config_file


def load_ai_config() -> AiConfig:
    path = get_ai_config_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    return AiConfig.model_validate(data)
