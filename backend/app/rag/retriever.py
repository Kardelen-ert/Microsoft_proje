"""Local retrieval logic based on ingested chunk metadata."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.constants import CHUNK_STORE_FILE_NAME
from app.schemas.query import SourceChunk


@dataclass
class RetrievedChunk:
    """Internal chunk with retrieval score."""

    source: SourceChunk
    score: float


class LocalKeywordRetriever:
    """Simple offline retriever over locally persisted chunk metadata."""

    def __init__(self) -> None:
        settings = get_settings()
        self.chunk_store_path = settings.vector_store_dir / CHUNK_STORE_FILE_NAME

    def retrieve(self, question: str, top_k: int = 3) -> list[RetrievedChunk]:
        """Return the top matching chunks using keyword overlap scoring."""

        chunks = self._load_chunks()
        if not chunks:
            return []

        query_terms = self._tokenize(question)
        scored_chunks: list[RetrievedChunk] = []

        for item in chunks:
            chunk_text = item.get("text", "")
            chunk_terms = self._tokenize(chunk_text)
            overlap = query_terms.intersection(chunk_terms)
            if not overlap:
                continue

            score = len(overlap) / max(len(query_terms), 1)
            scored_chunks.append(
                RetrievedChunk(
                    source=SourceChunk(
                        document_name=item["document_name"],
                        page_number=item["page_number"],
                        chunk_text=chunk_text,
                    ),
                    score=score,
                )
            )

        scored_chunks.sort(key=lambda item: item.score, reverse=True)
        return scored_chunks[:top_k]

    def _load_chunks(self) -> list[dict]:
        """Load stored chunk metadata from disk."""

        if not self.chunk_store_path.exists():
            return []

        return json.loads(self.chunk_store_path.read_text(encoding="utf-8"))

    def _tokenize(self, text: str) -> set[str]:
        """Normalize text into a set of retrieval tokens."""

        return {token for token in re.findall(r"\w+", text.lower()) if len(token) > 2}
