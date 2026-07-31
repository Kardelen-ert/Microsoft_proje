"""Repository helpers for local SQLite persistence."""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import uuid

from app.db.database import get_connection
from app.db.models import TestCaseRecord


def utc_now() -> str:
    """Return a stable UTC ISO timestamp for persistence."""

    return datetime.now(UTC).isoformat()


class DocumentRepository:
    """Handles document and chunk persistence."""

    def clear_documents(self) -> None:
        """Remove all persisted source documents and their chunks."""

        with get_connection() as connection:
            connection.execute("DELETE FROM document_chunks")
            connection.execute("DELETE FROM documents")

    def create_document(self, file_path: str, title: str | None = None) -> int:
        """Insert or replace a document record and return its id."""

        path = Path(file_path)
        existing_id = self.get_document_id_by_path(str(path))
        with get_connection() as connection:
            if existing_id is not None:
                connection.execute(
                    """
                    UPDATE documents
                    SET title = ?, file_type = ?, status = ?, uploaded_at = ?
                    WHERE id = ?
                    """,
                    (
                        title or path.stem,
                        path.suffix.lower().lstrip(".") or "unknown",
                        "ready",
                        utc_now(),
                        existing_id,
                    ),
                )
                connection.execute(
                    "DELETE FROM document_chunks WHERE document_id = ?",
                    (existing_id,),
                )
                return existing_id

            cursor = connection.execute(
                """
                INSERT INTO documents (title, file_path, file_type, status, uploaded_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    title or path.stem,
                    str(path),
                    path.suffix.lower().lstrip(".") or "unknown",
                    "ready",
                    utc_now(),
                ),
            )
            return int(cursor.lastrowid)

    def get_document_id_by_path(self, file_path: str) -> int | None:
        """Return the document id for a persisted file path, if any."""

        with get_connection() as connection:
            row = connection.execute(
                "SELECT id FROM documents WHERE file_path = ?",
                (file_path,),
            ).fetchone()
        return int(row["id"]) if row else None

    def add_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        page_number: int | None = None,
        token_count: int | None = None,
        source_label: str | None = None,
        chunk_id: str | None = None,
    ) -> str:
        """Persist a single chunk row and return its identifier."""

        stored_chunk_id = chunk_id or str(uuid.uuid4())
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO document_chunks (
                    id, document_id, chunk_index, content, page_number,
                    token_count, source_label, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stored_chunk_id,
                    document_id,
                    chunk_index,
                    content,
                    page_number,
                    token_count,
                    source_label,
                    utc_now(),
                ),
            )
        return stored_chunk_id

    def count_documents(self) -> int:
        """Return how many documents are currently persisted."""

        with get_connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM documents"
            ).fetchone()
        return int(row["total"])

    def count_chunks(self) -> int:
        """Return how many chunks are currently persisted."""

        with get_connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM document_chunks"
            ).fetchone()
        return int(row["total"])

    def search_chunks_by_terms(self, terms: list[str], limit: int = 12) -> list[dict]:
        """Return chunk rows that lexically match one or more query terms."""

        normalized_terms = [term.strip().lower() for term in terms if term.strip()]
        if not normalized_terms:
            return []

        where_clause = " OR ".join(["LOWER(dc.content) LIKE ?" for _ in normalized_terms])
        params = [f"%{term}%" for term in normalized_terms]
        params.append(limit)

        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT dc.id, dc.content, dc.page_number, dc.chunk_index, d.title, d.file_path
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE {where_clause}
                ORDER BY LENGTH(dc.content) DESC, dc.page_number ASC, dc.chunk_index ASC
                LIMIT ?
                """,
                params,
            ).fetchall()

        return [
            {
                "chunk_id": str(row["id"]),
                "content": str(row["content"]),
                "page_number": int(row["page_number"] or 0),
                "chunk_index": int(row["chunk_index"] or 0),
                "document_name": Path(str(row["file_path"])).name or str(row["title"]),
            }
            for row in rows
        ]


class ChatRepository:
    """Handles lightweight chat session persistence."""

    def create_session(self) -> str:
        """Create a chat session and return its identifier."""

        session_id = str(uuid.uuid4())
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO chat_sessions (id, created_at) VALUES (?, ?)",
                (session_id, utc_now()),
            )
        return session_id

    def ensure_session(self, session_id: str | None) -> str:
        """Return a valid session id, creating one when needed."""

        if not session_id:
            return self.create_session()

        with get_connection() as connection:
            row = connection.execute(
                "SELECT id FROM chat_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if row:
                return session_id

            connection.execute(
                "INSERT INTO chat_sessions (id, created_at) VALUES (?, ?)",
                (session_id, utc_now()),
            )
        return session_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a chat message to an existing session."""

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, utc_now()),
            )


class QueryLogRepository:
    """Handles persisted diagnostic query logs."""

    def add_log(
        self,
        question: str,
        answer: str,
        grounded: bool,
        confidence: float,
        source_count: int,
        session_id: str | None = None,
        asset_id: str | None = None,
        latency_ms: int | None = None,
    ) -> None:
        """Persist a single query result."""

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO query_logs (
                    session_id, question, asset_id, answer,
                    grounded, confidence, source_count, latency_ms, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    question,
                    asset_id,
                    answer,
                    int(grounded),
                    confidence,
                    source_count,
                    latency_ms,
                    utc_now(),
                ),
            )


class TestRepository:
    """Handles saved evaluation cases and runs."""

    def create_test_case(
        self,
        question: str,
        expected_behavior: str,
        expected_answer: str | None = None,
        expected_keywords: str | None = None,
    ) -> int:
        """Persist a new test case and return its id."""

        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO test_cases (
                    question, expected_behavior, expected_answer,
                    expected_keywords, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    question,
                    expected_behavior,
                    expected_answer,
                    expected_keywords,
                    utc_now(),
                ),
            )
            return int(cursor.lastrowid)

    def add_test_run(
        self,
        test_case_id: int,
        actual_answer: str,
        grounded: bool,
        confidence: float,
        passed: bool,
        notes: str | None = None,
    ) -> int:
        """Persist a test run result and return its id."""

        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO test_runs (
                    test_case_id, actual_answer, grounded,
                    confidence, passed, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    test_case_id,
                    actual_answer,
                    int(grounded),
                    confidence,
                    int(passed),
                    notes,
                    utc_now(),
                ),
            )
            return int(cursor.lastrowid)

    def list_test_cases(self) -> list[TestCaseRecord]:
        """Return all saved test cases in creation order."""

        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, question, expected_behavior, expected_answer,
                       expected_keywords, created_at
                FROM test_cases
                ORDER BY id ASC
                """
            ).fetchall()

        return [
            TestCaseRecord(
                id=int(row["id"]),
                question=str(row["question"]),
                expected_behavior=str(row["expected_behavior"]),
                expected_answer=row["expected_answer"],
                expected_keywords=row["expected_keywords"],
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def get_test_case(self, test_case_id: int) -> TestCaseRecord | None:
        """Return one saved test case by id."""

        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, question, expected_behavior, expected_answer,
                       expected_keywords, created_at
                FROM test_cases
                WHERE id = ?
                """,
                (test_case_id,),
            ).fetchone()

        if row is None:
            return None

        return TestCaseRecord(
            id=int(row["id"]),
            question=str(row["question"]),
            expected_behavior=str(row["expected_behavior"]),
            expected_answer=row["expected_answer"],
            expected_keywords=row["expected_keywords"],
            created_at=str(row["created_at"]),
        )
