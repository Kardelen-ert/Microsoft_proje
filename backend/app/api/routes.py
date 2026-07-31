"""FastAPI route definitions."""

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.documents import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentStatusResponse,
)
from app.schemas.query import DiagnosticResponse, QuestionRequest
from app.schemas.testing import (
    TestCaseCreateRequest,
    TestCaseResponse,
    TestRunRequest,
    TestRunResponse,
)
from app.services.diagnostic_service import DiagnosticService
from app.services.document_service import DocumentService
from app.services.test_service import TestService

router = APIRouter()


@lru_cache()
def get_diagnostic_service() -> DiagnosticService:
    """Create the shared diagnostic service once."""

    print("Yapay Zeka modelleri bellege yukleniyor...")
    return DiagnosticService()


@lru_cache()
def get_document_service() -> DocumentService:
    """Create the shared document service once."""

    return DocumentService()


@lru_cache()
def get_test_service() -> TestService:
    """Create the shared test service once."""

    return TestService(get_diagnostic_service())


@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple liveness endpoint."""

    return {"status": "ok"}


@router.post("/diagnostics/query", response_model=DiagnosticResponse)
def run_diagnostic_query(
    payload: QuestionRequest,
    service: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticResponse:
    """Accept a question and hand it to the diagnostic workflow."""

    try:
        return service.run_query(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/documents/ingest", response_model=DocumentIngestResponse)
def ingest_documents(
    payload: DocumentIngestRequest,
    service: DocumentService = Depends(get_document_service),
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
    service: DocumentService = Depends(get_document_service),
) -> DocumentStatusResponse:
    """Return current ingestion and vector store readiness information."""

    try:
        return service.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/tests/cases", response_model=TestCaseResponse)
def create_test_case(
    payload: TestCaseCreateRequest,
    service: TestService = Depends(get_test_service),
) -> TestCaseResponse:
    """Create a saved evaluation case for classroom testing."""

    try:
        return service.create_test_case(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tests/cases", response_model=list[TestCaseResponse])
def list_test_cases(
    service: TestService = Depends(get_test_service),
) -> list[TestCaseResponse]:
    """List all saved evaluation cases."""

    try:
        return service.list_test_cases()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/tests/cases/{test_case_id}/run", response_model=TestRunResponse)
def run_test_case(
    test_case_id: int,
    payload: TestRunRequest,
    service: TestService = Depends(get_test_service),
) -> TestRunResponse:
    """Execute one saved evaluation case against the current assistant."""

    try:
        return service.run_test_case(test_case_id=test_case_id, top_k=payload.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
