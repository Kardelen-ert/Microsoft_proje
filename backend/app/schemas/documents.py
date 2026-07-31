"""Request and response schemas for document ingestion endpoints."""

from pydantic import BaseModel, Field


class DocumentIngestRequest(BaseModel):
    """Payload used to start a document ingestion job."""

    file_paths: list[str] = Field(
        ...,
        min_length=1,
        description="One or more local PDF paths to ingest into the vector store",
    )
    rebuild_index: bool = Field(
        default=False,
        description="Whether to rebuild the vector index from scratch",
    )


class DocumentIngestResponse(BaseModel):
    """Response returned after an ingest request is accepted."""

    accepted: bool
    queued_files: int = Field(..., ge=0)
    indexed_chunks: int = Field(..., ge=0)
    parser_ready: bool
    message: str


class DocumentStatusResponse(BaseModel):
    """Current document ingestion status."""

    total_documents: int = Field(..., ge=0)
    indexed_documents: int = Field(..., ge=0)
    indexed_chunks: int = Field(..., ge=0)
    sqlite_documents: int = Field(..., ge=0)
    sqlite_chunks: int = Field(..., ge=0)
    vector_store_ready: bool
    parser_ready: bool
    last_ingested_files: list[str] = Field(default_factory=list)
    status_message: str
