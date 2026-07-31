"""Embedding utilities for semantic retrieval."""

from __future__ import annotations

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


class EmbeddingService:
    """Creates normalized embeddings for documents and queries."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.embedding_model_name
        self.local_only = settings.embedding_local_only
        self._model: SentenceTransformer | None = None

    def is_available(self) -> bool:
        """Return whether the embedding model can be loaded in the current environment."""

        try:
            self._get_model()
        except RuntimeError:
            return False
        return True

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple chunks for vector store indexing."""

        vectors = self._get_model().encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single question for semantic search."""

        vector = self._get_model().encode([text], normalize_embeddings=True)[0]
        return vector.tolist()

    def _get_model(self) -> SentenceTransformer:
        """Lazily load the embedding model and keep the app offline-safe."""

        if self._model is not None:
            return self._model

        try:
            self._model = SentenceTransformer(
                self.model_name,
                local_files_only=self.local_only,
            )
        except Exception as exc:
            mode = "local cache only" if self.local_only else "download-enabled"
            raise RuntimeError(
                f"Embedding model could not be loaded in {mode} mode: {self.model_name}"
            ) from exc

        return self._model
