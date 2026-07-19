"""FastAPI route definitions."""

from fastapi import APIRouter, HTTPException

from app.schemas.documents import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentStatusResponse,
)
from app.schemas.query import DiagnosticResponse, QuestionRequest
from app.services.document_service import DocumentService
from app.services.diagnostic_service import DiagnosticService

router = APIRouter()
diagnostic_service = DiagnosticService()
document_service = DocumentService()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple liveness endpoint."""

    return {"status": "ok"}


@router.post("/diagnostics/query", response_model=DiagnosticResponse)
def run_diagnostic_query(payload: QuestionRequest) -> DiagnosticResponse:
    """Accept a technician question and hand it to the service layer."""

    try:
        return diagnostic_service.run_query(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/documents/ingest", response_model=DocumentIngestResponse)
def ingest_documents(payload: DocumentIngestRequest) -> DocumentIngestResponse:
    """Accept document paths and pass them to the document service."""

    try:
        return document_service.ingest_documents(payload)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/documents/status", response_model=DocumentStatusResponse)
def get_document_status() -> DocumentStatusResponse:
    """Return current ingestion and vector store readiness information."""

    try:
        return document_service.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
