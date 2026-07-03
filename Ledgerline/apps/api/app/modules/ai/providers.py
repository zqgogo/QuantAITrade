from abc import ABC, abstractmethod
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.core.ai_config import EmbeddingConfig, LlmProviderConfig


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class LlmProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[ChatMessage]) -> str:
        raise NotImplementedError


class OpenAICompatibleLlmProvider(LlmProvider):
    def __init__(self, config: LlmProviderConfig) -> None:
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    async def complete(self, messages: list[ChatMessage]) -> str:
        response = await self.client.chat.completions.create(
            model=self.config.default_model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content or ""


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        self._model = None

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from FlagEmbedding import BGEM3FlagModel

            use_fp16 = self.config.device != "cpu"
            self._model = BGEM3FlagModel(self.config.model, use_fp16=use_fp16)

        output = self._model.encode(texts, return_dense=True)
        return output["dense_vecs"].tolist()


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key or "", base_url=config.base_url)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(model=self.config.model, input=texts)
        return [item.embedding for item in response.data]


def build_llm_provider(config: LlmProviderConfig) -> LlmProvider:
    return OpenAICompatibleLlmProvider(config)


def build_embedding_provider(config: EmbeddingConfig) -> EmbeddingProvider:
    if config.provider == "local":
        return LocalEmbeddingProvider(config)
    if config.provider in {"openai", "ollama", "custom"}:
        return OpenAICompatibleEmbeddingProvider(config)
    raise ValueError(f"Unsupported embedding provider: {config.provider}")
