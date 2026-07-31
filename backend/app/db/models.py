"""Database-facing record models."""

from dataclasses import dataclass


@dataclass
class DocumentRecord:
    """Application-level shape of an ingested source document."""

    id: int
    title: str
    file_path: str
    file_type: str
    status: str
    uploaded_at: str


@dataclass
class DocumentChunkRecord:
    """Application-level shape of a persisted document chunk."""

    id: str
    document_id: int
    chunk_index: int
    content: str
    page_number: int | None
    token_count: int | None
    source_label: str | None
    created_at: str


@dataclass
class ChatSessionRecord:
    """Application-level shape of a chat session."""

    id: str
    created_at: str


@dataclass
class ChatMessageRecord:
    """Application-level shape of a chat message."""

    id: int
    session_id: str
    role: str
    content: str
    created_at: str


@dataclass
class QueryLogRecord:
    """Application-level shape of a persisted diagnostic query."""

    question: str
    asset_id: str | None
    answer: str
    grounded: bool
    confidence: float
    source_count: int
    created_at: str
    session_id: str | None = None
    latency_ms: int | None = None


@dataclass
class TestCaseRecord:
    """Application-level shape of a saved evaluation case."""

    id: int
    question: str
    expected_behavior: str
    expected_answer: str | None
    expected_keywords: str | None
    created_at: str


@dataclass
class TestRunRecord:
    """Application-level shape of a test run result."""

    id: int
    test_case_id: int
    actual_answer: str
    grounded: bool
    confidence: float
    passed: bool
    notes: str | None
    created_at: str
