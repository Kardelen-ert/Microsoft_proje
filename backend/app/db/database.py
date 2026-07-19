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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                asset_id TEXT NULL,
                answer TEXT NOT NULL,
                grounded INTEGER NOT NULL,
                confidence REAL NOT NULL,
                source_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

    return settings.sqlite_db_path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection for short-lived operations."""

    settings = get_settings()
    connection = sqlite3.connect(settings.sqlite_db_path)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
