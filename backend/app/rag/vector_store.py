"""ChromaDB persistence helpers."""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings


class ChromaVectorStore:
    """Wrapper around a persistent Chroma collection."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=str(settings.vector_store_dir))
        self.collection: Collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name
        )

    def add_chunks(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """Insert or update chunk records in Chroma."""

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def reset_collection(self) -> None:
        """Delete and recreate the active collection."""

        collection_name = self.collection.name
        self.client.delete_collection(collection_name)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def similarity_search(self, query_embedding: list[float], top_k: int) -> dict:
        """Query the collection by vector similarity."""

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
