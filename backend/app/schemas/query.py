"""Request and response schemas for diagnostic endpoints."""

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Incoming technician question payload."""

    question: str = Field(..., min_length=5, description="Technician question")
    asset_id: str | None = Field(
        default=None,
        description="Optional vehicle, subsystem, or equipment identifier",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of source chunks to return",
    )


class SourceChunk(BaseModel):
    """Grounding metadata returned to the client."""

    document_name: str
    page_number: int
    chunk_text: str


class DiagnosticResponse(BaseModel):
    """Response returned from the diagnostic workflow."""

    answer: str
    grounded: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    warning: str | None = None
    sources: list[SourceChunk] = Field(default_factory=list)
