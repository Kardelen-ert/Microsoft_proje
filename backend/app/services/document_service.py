"""Service layer for document ingestion workflows."""

from app.core.config import get_settings
from app.db.repositories import DocumentRepository
from app.rag.ingestion import LocalDocumentIngestionPipeline
from app.schemas.documents import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentStatusResponse,
)


class DocumentService:
    """Coordinates document ingestion and exposes status to the API layer."""

    def __init__(self) -> None:
        self.pipeline = LocalDocumentIngestionPipeline(get_settings())
        self.document_repository = DocumentRepository()

    def ingest_documents(self, payload: DocumentIngestRequest) -> DocumentIngestResponse:
        """Accept document paths and run the local ingestion pipeline."""

        result = self.pipeline.ingest(
            file_paths=payload.file_paths,
            rebuild_index=payload.rebuild_index,
        )

        return DocumentIngestResponse(
            accepted=True,
            queued_files=len(result.ingested_documents),
            indexed_chunks=result.indexed_chunks,
            parser_ready=result.parser_ready,
            message=(
                "Dokumanlar ChromaDB'ye basariyla yazildi."
                if result.parser_ready
                else "Dokumanlar kopyalandi ancak parser hazir olmadigi icin indexlenemedi."
            ),
        )

    def get_status(self) -> DocumentStatusResponse:
        """Return the current ingestion status from the manifest."""

        manifest = self.pipeline.read_status()
        documents = manifest.get("documents", [])
        last_ingested_files = [item["file_name"] for item in documents]

        return DocumentStatusResponse(
            total_documents=len(documents),
            indexed_documents=manifest.get("indexed_documents", 0),
            indexed_chunks=manifest.get("indexed_chunks", 0),
            sqlite_documents=self.document_repository.count_documents(),
            sqlite_chunks=self.document_repository.count_chunks(),
            vector_store_ready=manifest.get("indexed_chunks", 0) > 0,
            parser_ready=manifest.get("parser_ready", False),
            last_ingested_files=last_ingested_files,
            status_message=(
                "Durum bilgisi ingestion manifestinden okunuyor. Sonraki adimda bu veri "
                "vektor store ve veritabani metrikleriyle genisletilecek."
            ),
        )
