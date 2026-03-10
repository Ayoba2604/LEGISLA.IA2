from __future__ import annotations

import logging
import os
from typing import Any

from backend.app.config.settings import settings
from backend.app.core.text import hashed_embedding

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self._client = self._build_client()

    @property
    def active_backend(self) -> str:
        if self._client:
            return f"{self.provider}:{self.model_name}"
        return "hash"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._client:
            return self._client.embed_documents(texts)
        return [hashed_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if self._client:
            return self._client.embed_query(text)
        return hashed_embedding(text)

    def _build_client(self):
        if self.provider == "openai" and settings.openai_api_key:
            try:
                from langchain_openai import OpenAIEmbeddings

                return OpenAIEmbeddings(model=self.model_name, api_key=settings.openai_api_key)
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to initialize OpenAI embeddings, falling back to hash.",
                    extra={"extra_payload": {"error": str(exc)}},
                )
        return None


class ChatModelFactory:
    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.model_name = settings.llm_model
        self._configure_langsmith()

    def build_chat_model(self):
        if self.provider == "openai" and settings.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(model=self.model_name, temperature=0.1, api_key=settings.openai_api_key)
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to initialize ChatOpenAI.",
                    extra={"extra_payload": {"error": str(exc)}},
                )
                return None

        if self.provider == "groq" and settings.groq_api_key:
            try:
                from langchain_groq import ChatGroq

                return ChatGroq(model=self.model_name, temperature=0.1, groq_api_key=settings.groq_api_key)
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to initialize ChatGroq.",
                    extra={"extra_payload": {"error": str(exc)}},
                )
                return None

        return None

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "langgraph_enabled": settings.use_langgraph_agent,
            "langsmith_tracing": settings.langsmith_tracing,
        }

    @staticmethod
    def _configure_langsmith() -> None:
        if not settings.langsmith_tracing:
            return
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        if settings.langsmith_api_key:
            os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
            os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        if settings.langsmith_project:
            os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
            os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
