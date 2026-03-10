from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalFilters(BaseModel):
    source_types: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    tribunal: str | None = None
    uf: str | None = None
    ramo_direito: str | None = None
    owner_user_id: str | None = None
    only_official: bool = False
    only_user_documents: bool = False


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 6
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
