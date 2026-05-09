"""Data models."""
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    file_path: str = ""
    chunk_index: int = 0
    content: str = ""
    tags: list[str] = Field(default_factory=list)
    created: str = ""

    def to_row(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "file_path": self.file_path,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "tags": ",".join(self.tags),
            "created": self.created,
        }


class SearchResult(BaseModel):
    score: float
    content: str
    title: str
    file: str
    tags: list[str] = Field(default_factory=list)


class IndexMeta(BaseModel):
    last_indexed: str = ""
    file_mtimes: dict[str, float] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    tag: str | None = None
