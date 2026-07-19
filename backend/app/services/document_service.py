"""Service layer for document ingestion workflows."""

from app.core.config import get_settings
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

    def ingest_documents(self, payload: DocumentIngestRequest) -> DocumentIngestResponse:
        """Accept document paths and run the local ingestion pipeline."""

        result = self.pipeline.ingest(
            file_paths=payload.file_paths,
            rebuild_index=payload.rebuild_index,
        )

        message = "Dokumanlar backend/data/raw_pdfs altina kopyalandi ve durum manifesti guncellendi."
        if result.rebuild_index:
            message = (
                "Index yeniden kurulum modunda dokumanlar kopyalandi ve onceki ingest durumu sifirlandi."
            )
        if not result.parser_ready:
            message = (
                "Dokumanlar kopyalandi ancak PDF parser bagimliligi eksik oldugu icin chunk uretilemedi. "
                "pypdf kuruldugunda ayni endpoint gercek metin chunk'lari da yazacak."
            )

        return DocumentIngestResponse(
            accepted=True,
            queued_files=len(result.ingested_documents),
            indexed_chunks=result.indexed_chunks,
            parser_ready=result.parser_ready,
            message=message,
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
            vector_store_ready=manifest.get("indexed_chunks", 0) > 0,
            parser_ready=manifest.get("parser_ready", False),
            last_ingested_files=last_ingested_files,
            status_message=(
                "Durum bilgisi ingestion manifestinden okunuyor. Sonraki adimda bu veri "
                "vektor store ve veritabani metrikleriyle genisletilecek."
            ),
        )
