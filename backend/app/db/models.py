"""Database-facing record models."""

from dataclasses import dataclass


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
