"""Database helpers for logging and local persistence."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core.config import get_settings


def initialize_database() -> Path:
    """Create the local SQLite database and required tables if needed."""

    settings = get_settings()
    settings.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(settings.sqlite_db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ready',
                uploaded_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                page_number INTEGER NULL,
                token_count INTEGER NULL,
                source_label TEXT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NULL,
                question TEXT NOT NULL,
                asset_id TEXT NULL,
                answer TEXT NOT NULL,
                grounded INTEGER NOT NULL,
                confidence REAL NOT NULL,
                source_count INTEGER NOT NULL,
                latency_ms INTEGER NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL
            )
            """
        )
        _ensure_query_log_columns(connection)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                expected_behavior TEXT NOT NULL,
                expected_answer TEXT NULL,
                expected_keywords TEXT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id INTEGER NOT NULL,
                actual_answer TEXT NOT NULL,
                grounded INTEGER NOT NULL,
                confidence REAL NOT NULL,
                passed INTEGER NOT NULL,
                notes TEXT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    return settings.sqlite_db_path


def _ensure_query_log_columns(connection: sqlite3.Connection) -> None:
    """Backfill columns added after the first project bootstrap."""

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(query_logs)").fetchall()
    }
    if "session_id" not in columns:
        connection.execute("ALTER TABLE query_logs ADD COLUMN session_id TEXT NULL")
    if "latency_ms" not in columns:
        connection.execute("ALTER TABLE query_logs ADD COLUMN latency_ms INTEGER NULL")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection for short-lived operations."""

    settings = get_settings()
    connection = sqlite3.connect(settings.sqlite_db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
