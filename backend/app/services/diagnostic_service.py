"""Service layer for diagnostic workflows."""

from __future__ import annotations

from datetime import datetime, timezone

from app.db.database import get_connection
from app.db.models import QueryLogRecord
from app.rag.rag_engine import RAGEngine
from app.schemas.query import DiagnosticResponse, QuestionRequest

class DiagnosticService:
    """Coordinates retrieval and answer generation for technician questions."""

    def __init__(self) -> None:
        self.rag_engine = RAGEngine()

    def run_query(self, payload: QuestionRequest) -> DiagnosticResponse:
        """Run a grounded diagnostic query and persist a log entry."""

        response = self.rag_engine.answer_question(payload)
        self._log_query(
            QueryLogRecord(
                question=payload.question,
                asset_id=payload.asset_id,
                answer=response.answer,
                grounded=response.grounded,
                confidence=response.confidence,
                source_count=len(response.sources),
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        return response

    def _log_query(self, record: QueryLogRecord) -> None:
        """Persist the query result to the local SQLite log store."""

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO query_logs (
                    question,
                    asset_id,
                    answer,
                    grounded,
                    confidence,
                    source_count,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.question,
                    record.asset_id,
                    record.answer,
                    int(record.grounded),
                    record.confidence,
                    record.source_count,
                    record.created_at,
                ),
            )
