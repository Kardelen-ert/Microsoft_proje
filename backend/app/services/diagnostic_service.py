"""Service layer for diagnostic workflows."""

from __future__ import annotations

from time import perf_counter

from app.db.repositories import ChatRepository, QueryLogRepository
from app.rag.rag_engine import RAGEngine
from app.schemas.query import DiagnosticResponse, QuestionRequest


class DiagnosticService:
    """Coordinates retrieval and answer generation for technician questions."""

    def __init__(self) -> None:
        self.rag_engine = RAGEngine()
        self.chat_repository = ChatRepository()
        self.query_log_repository = QueryLogRepository()

    def run_query(self, payload: QuestionRequest) -> DiagnosticResponse:
        """Run a grounded diagnostic query and persist a log entry."""

        session_id = self.chat_repository.ensure_session(payload.session_id)
        self.chat_repository.add_message(session_id, "user", payload.question)

        started_at = perf_counter()
        response = self.rag_engine.answer_question(payload)
        latency_ms = int((perf_counter() - started_at) * 1000)

        self.chat_repository.add_message(session_id, "assistant", response.answer)
        self.query_log_repository.add_log(
            question=payload.question,
            asset_id=payload.asset_id,
            answer=response.answer,
            grounded=response.grounded,
            confidence=response.confidence,
            source_count=len(response.sources),
            session_id=session_id,
            latency_ms=latency_ms,
        )

        return DiagnosticResponse(
            answer=response.answer,
            grounded=response.grounded,
            confidence=response.confidence,
            session_id=session_id,
            warning=response.warning,
            sources=response.sources,
        )
