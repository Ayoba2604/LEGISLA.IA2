from __future__ import annotations

import logging
import math
import os
from typing import Any

from backend.app.config.settings import settings
from backend.app.core.text import hashed_embedding

logger = logging.getLogger(__name__)
DEFAULT_EMBEDDING_DIMENSIONS = 256


def _normalize_embedding(vector: list[float]) -> list[float]:
    if not vector:
        return []
    normalized = [float(item) for item in vector]
    norm = math.sqrt(sum(item * item for item in normalized)) or 1.0
    return [item / norm for item in normalized]


class _GoogleEmbeddingsAdapter:
    def __init__(self, *, model_name: str, google_api_key: str, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        self.dimensions = dimensions
        self._client = GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=google_api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts, output_dimensionality=self.dimensions)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text, output_dimensionality=self.dimensions)


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
            return [_normalize_embedding(vector) for vector in self._client.embed_documents(texts)]
        return [hashed_embedding(text, dimensions=DEFAULT_EMBEDDING_DIMENSIONS) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if self._client:
            return _normalize_embedding(self._client.embed_query(text))
        return hashed_embedding(text, dimensions=DEFAULT_EMBEDDING_DIMENSIONS)

    def _build_client(self):
        if self.provider == "openai" and settings.openai_api_key:
            try:
                from langchain_openai import OpenAIEmbeddings

                return OpenAIEmbeddings(
                    model=self.model_name,
                    api_key=settings.openai_api_key,
                    dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
                )
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to initialize OpenAI embeddings, falling back to hash.",
                    extra={"extra_payload": {"error": str(exc)}},
                )
        if self.provider in {"google", "gemini"} and settings.google_api_key:
            try:
                return _GoogleEmbeddingsAdapter(
                    model_name=self.model_name,
                    google_api_key=settings.google_api_key,
                    dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
                )
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to initialize Google/Gemini embeddings, falling back to hash.",
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

        if self.provider in {"google", "gemini"} and settings.google_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                return ChatGoogleGenerativeAI(
                    model=self.model_name,
                    temperature=0.1,
                    google_api_key=settings.google_api_key,
                )
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to initialize ChatGoogleGenerativeAI.",
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
