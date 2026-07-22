"""Local retrieval logic based on ingested chunk metadata."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.schemas.query import SourceChunk

# 1. ADIM: Yeni eklediğimiz LangChain ve Chroma kütüphaneleri
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

@dataclass
class RetrievedChunk:
    """Internal chunk with retrieval score."""

    source: SourceChunk
    score: float


# Sınıfımızın adını Vektör Araması yaptığımızı belli etmek için değiştirdik
class LocalVectorRetriever:
    """Retrieves relevant document chunks from the local ChromaDB vector store."""

    def __init__(self) -> None:
        settings = get_settings()
        
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # ingestion.py ile aynı klasör ve koleksiyon adını kullanıyoruz
        chroma_db_dir = settings.vector_store_dir / "chroma_db"
        
        self.vector_store = Chroma(
            collection_name="railway_diagnostics",
            persist_directory=str(chroma_db_dir),
            embedding_function=self.embeddings
        )

    def retrieve(self, question: str, top_k: int = 3) -> list[RetrievedChunk]:
        """Return the top matching chunks using vector similarity scoring."""

        # Vektör veritabanında arama yapıp hem metinleri hem de benzerlik mesafe skorlarını alıyoruz
        # ChromaDB'de mesafe (distance) skoru döner, yani skor ne kadar küçükse metin o kadar benzerdir.
        results = self.vector_store.similarity_search_with_score(question, k=top_k)
        
        if not results:
            return []

        scored_chunks: list[RetrievedChunk] = []

        for doc, score in results:
            scored_chunks.append(
                RetrievedChunk(
                    source=SourceChunk(
                        # ingestion.py'de metadata içine kaydettiğimiz verileri çekiyoruz
                        document_name=doc.metadata.get("document_name", "Bilinmiyor"),
                        page_number=doc.metadata.get("page_number", 0),
                        chunk_text=doc.page_content,
                    ),
                    score=float(score),
                )
            )

        # Chroma'da skor bir mesafe olduğu için, en düşük mesafeli (en iyi) olanı en başa koyuyoruz
        scored_chunks.sort(key=lambda item: item.score, reverse=False)
        return scored_chunks