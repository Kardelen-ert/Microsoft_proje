"""FastAPI route definitions."""

from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.documents import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentStatusResponse,
)
from app.schemas.query import DiagnosticResponse, QuestionRequest
from app.services.document_service import DocumentService
from app.services.diagnostic_service import DiagnosticService

router = APIRouter()

# --- BAĞIMLILIKLAR (DEPENDENCIES) VE CACHE ---

@lru_cache()
def get_diagnostic_service() -> DiagnosticService:
    """DiagnosticService'in sadece bir kez belleğe alınmasını sağlar."""
    print("Yapay Zeka modelleri belleğe yükleniyor...")
    return DiagnosticService()

@lru_cache()
def get_document_service() -> DocumentService:
    """DocumentService'in sadece bir kez belleğe alınmasını sağlar."""
    return DocumentService()

# --- ENDPOINT'LER ---

@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple liveness endpoint."""
    return {"status": "ok"}


@router.post("/diagnostics/query", response_model=DiagnosticResponse)
def run_diagnostic_query(
    payload: QuestionRequest,
    # Servisi globalden almak yerine Depends ile çağırıyoruz
    service: DiagnosticService = Depends(get_diagnostic_service)
) -> DiagnosticResponse:
    """Accept a technician question and hand it to the service layer."""
    try:
        return service.run_query(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/documents/ingest", response_model=DocumentIngestResponse)
def ingest_documents(
    payload: DocumentIngestRequest,
    service: DocumentService = Depends(get_document_service)
) -> DocumentIngestResponse:
    """Accept document paths and pass them to the document service."""
    try:
        return service.ingest_documents(payload)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/documents/status", response_model=DocumentStatusResponse)
def get_document_status(
    service: DocumentService = Depends(get_document_service)
) -> DocumentStatusResponse:
    """Return current ingestion and vector store readiness information."""
    try:
        return service.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc