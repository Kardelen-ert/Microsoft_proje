"""Semantic retrieval logic backed by ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.core.config import get_settings
from app.db.repositories import DocumentRepository
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import ChromaVectorStore
from app.schemas.query import SourceChunk


@dataclass
class RetrievedChunk:
    """Internal chunk with retrieval score."""

    source: SourceChunk
    score: float


class SemanticRetriever:
    """Retrieves relevant document chunks from the local ChromaDB vector store."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self.vector_store = ChromaVectorStore()
        self.document_repository = DocumentRepository()

    def retrieve(self, question: str, top_k: int = 3) -> list[RetrievedChunk]:
        """Return the top matching chunks using semantic vector similarity."""

        final_top_k = top_k or self.settings.retrieval_top_k
        normalized_question = self._normalize_text(question)
        results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        try:
            query_embedding = self.embedding_service.embed_query(question)
            results = self.vector_store.similarity_search(
                query_embedding=query_embedding,
                top_k=final_top_k,
            )
        except RuntimeError:
            pass

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        scored_chunks: list[RetrievedChunk] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            scored_chunks.append(
                RetrievedChunk(
                    source=SourceChunk(
                        document_name=metadata.get("document_name", "Bilinmiyor"),
                        page_number=int(metadata.get("page_number", 0)),
                        chunk_text=document,
                    ),
                    score=float(distance),
                )
            )

        lexical_terms = self._extract_search_terms(question)
        lexical_rows = self.document_repository.search_chunks_by_terms(
            lexical_terms,
            limit=max(final_top_k * 4, 12),
        )
        ranked_lexical_rows = sorted(
            lexical_rows,
            key=lambda row: self._lexical_score(
                question=normalized_question,
                content=self._normalize_text(row["content"]),
                page_number=int(row["page_number"]),
            ),
            reverse=True,
        )
        existing_chunk_ids = {
            f"{item.source.document_name}:{item.source.page_number}:{item.source.chunk_text}"
            for item in scored_chunks
        }
        for row in ranked_lexical_rows:
            dedupe_key = f"{row['document_name']}:{row['page_number']}:{row['content']}"
            if dedupe_key in existing_chunk_ids:
                continue
            lexical_score = self._lexical_score(
                question=normalized_question,
                content=self._normalize_text(row["content"]),
                page_number=int(row["page_number"]),
            )
            if lexical_score <= 0:
                continue
            scored_chunks.append(
                RetrievedChunk(
                    source=SourceChunk(
                        document_name=row["document_name"],
                        page_number=int(row["page_number"]),
                        chunk_text=row["content"],
                    ),
                    score=max(0.01, 0.35 - min(0.30, lexical_score / 20)),
                )
            )

        scored_chunks.sort(key=lambda item: item.score)
        return scored_chunks[:final_top_k]

    def _extract_search_terms(self, question: str) -> list[str]:
        """Build simple lexical terms from the user question for keyword fallback."""

        cleaned = re.sub(r"[^\w\s]", " ", question.lower())
        tokens = [token for token in cleaned.split() if len(token) >= 4]
        phrases: list[str] = []
        if len(tokens) >= 2:
            phrases.extend(
                [" ".join(tokens[index : index + 2]) for index in range(len(tokens) - 1)]
            )
        return list(dict.fromkeys(phrases + tokens))

    def _lexical_score(self, question: str, content: str, page_number: int) -> float:
        """Score lexical matches to favor true topic chunks over tables of contents."""

        score = 0.0
        question_tokens = [token for token in question.split() if len(token) >= 4]
        bigrams = [
            " ".join(question_tokens[index : index + 2])
            for index in range(len(question_tokens) - 1)
        ]

        for phrase in bigrams:
            if phrase and phrase in content:
                score += 6.0

        for token in question_tokens:
            if token in content:
                score += 1.5

        if "icindekiler" in content:
            score -= 6.0
        if "ogrenme faaliyeti" in content:
            score -= 2.5
        if content.count("...") >= 2:
            score -= 3.0
        if page_number <= 3:
            score -= 1.0

        return score

    def _normalize_text(self, value: str) -> str:
        """Normalize Turkish text for simple lexical comparison."""

        lowered = value.lower()
        translation = str.maketrans(
            {
                "ç": "c",
                "ğ": "g",
                "ı": "i",
                "İ": "i",
                "ö": "o",
                "ş": "s",
                "ü": "u",
            }
        )
        normalized = lowered.translate(translation)
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", normalized)).strip()
