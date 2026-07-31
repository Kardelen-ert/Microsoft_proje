"""Application configuration definitions."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from app.core.constants import DEFAULT_LOG_FILE_NAME, DEFAULT_SQLITE_FILE_NAME

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Filesystem-oriented application settings for the backend."""

    backend_root: Path
    raw_pdfs_dir: Path
    vector_store_dir: Path
    logs_dir: Path
    log_file: Path
    sqlite_db_path: Path
    llm_base_url: str
    llm_model_name: str
    embedding_model_name: str
    embedding_local_only: bool
    chroma_collection_name: str
    retrieval_top_k: int


def get_settings() -> Settings:
    """Build settings relative to the backend package root."""

    backend_root = Path(__file__).resolve().parents[2]
    return Settings(
        backend_root=backend_root,
        raw_pdfs_dir=backend_root / "data" / "raw_pdfs",
        vector_store_dir=backend_root / "data" / "vector_store",
        logs_dir=backend_root / "logs",
        log_file=backend_root / "logs" / DEFAULT_LOG_FILE_NAME,
        sqlite_db_path=backend_root / "data" / DEFAULT_SQLITE_FILE_NAME,
        llm_base_url=os.getenv("FOUNDRY_LOCAL_BASE_URL", "http://127.0.0.1:8000/v1"),
        llm_model_name=os.getenv("FOUNDRY_LOCAL_MODEL", "local-model"),
        embedding_model_name=os.getenv(
            "EMBEDDING_MODEL_NAME",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        embedding_local_only=os.getenv("EMBEDDING_LOCAL_ONLY", "true").lower() == "true",
        chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "rail_docs"),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "3")),
    )
