"""Document ingestion helpers for local PDF management."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings
from app.core.constants import STATUS_FILE_NAME, SUPPORTED_DOCUMENT_SUFFIXES


@dataclass
class IngestedDocument:
    """Normalized metadata stored for each ingested document."""

    source_path: str
    stored_path: str
    file_name: str
    ingested_at: str
    chunk_count: int


@dataclass
class ChunkRecord:
    """Normalized chunk payload generated from PDF text."""

    chunk_id: str
    document_name: str
    page_number: int
    text: str
    char_count: int


@dataclass
class IngestionResult:
    """Returned after a successful local ingest run."""

    ingested_documents: list[IngestedDocument]
    rebuild_index: bool
    indexed_chunks: int
    parser_ready: bool


class LocalDocumentIngestionPipeline:
    """Copies local PDF files into the backend data area and writes a status manifest."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.status_file = settings.vector_store_dir / STATUS_FILE_NAME
        self.chunk_store_file = settings.vector_store_dir / "chunks.json"

    def ingest(self, file_paths: list[str], rebuild_index: bool) -> IngestionResult:
        """Validate, copy, and persist metadata for the given file paths."""

        self.settings.raw_pdfs_dir.mkdir(parents=True, exist_ok=True)
        self.settings.vector_store_dir.mkdir(parents=True, exist_ok=True)

        if rebuild_index:
            self._clear_existing_documents()

        ingested_documents: list[IngestedDocument] = []
        all_chunks: list[ChunkRecord] = []
        parser_ready = self._is_pdf_parser_available()
        for raw_path in file_paths:
            source_path = Path(raw_path).expanduser().resolve()
            self._validate_source_file(source_path)

            destination_path = self.settings.raw_pdfs_dir / source_path.name
            shutil.copy2(source_path, destination_path)
            document_chunks = self._extract_chunks(destination_path) if parser_ready else []
            all_chunks.extend(document_chunks)

            ingested_documents.append(
                IngestedDocument(
                    source_path=str(source_path),
                    stored_path=str(destination_path),
                    file_name=source_path.name,
                    ingested_at=datetime.now(timezone.utc).isoformat(),
                    chunk_count=len(document_chunks),
                )
            )

        manifest = {
            "rebuild_index": rebuild_index,
            "indexed_documents": len(ingested_documents),
            "indexed_chunks": len(all_chunks),
            "parser_ready": parser_ready,
            "documents": [asdict(item) for item in ingested_documents],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.status_file.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        self.chunk_store_file.write_text(
            json.dumps([asdict(chunk) for chunk in all_chunks], indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

        return IngestionResult(
            ingested_documents=ingested_documents,
            rebuild_index=rebuild_index,
            indexed_chunks=len(all_chunks),
            parser_ready=parser_ready,
        )

    def read_status(self) -> dict:
        """Return the current manifest, if it exists."""

        if not self.status_file.exists():
            return {
                "indexed_documents": 0,
                "indexed_chunks": 0,
                "parser_ready": self._is_pdf_parser_available(),
                "documents": [],
                "updated_at": None,
            }

        return json.loads(self.status_file.read_text(encoding="utf-8"))

    def _clear_existing_documents(self) -> None:
        """Remove previously copied PDFs and reset the status manifest."""

        for pdf_file in self.settings.raw_pdfs_dir.glob("*.pdf"):
            pdf_file.unlink()

        if self.status_file.exists():
            self.status_file.unlink()

        if self.chunk_store_file.exists():
            self.chunk_store_file.unlink()

    def _extract_chunks(self, pdf_path: Path) -> list[ChunkRecord]:
        """Extract text from a PDF and split it into overlapping chunks."""

        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        chunks: list[ChunkRecord] = []
        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue

            for chunk_index, chunk_text in enumerate(self._split_text(text), start=1):
                chunks.append(
                    ChunkRecord(
                        chunk_id=f"{pdf_path.stem}-p{page_index}-c{chunk_index}",
                        document_name=pdf_path.name,
                        page_number=page_index,
                        text=chunk_text,
                        char_count=len(chunk_text),
                    )
                )

        return chunks

    def _split_text(
        self,
        text: str,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> list[str]:
        """Split extracted text into overlapping character windows."""

        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(normalized)
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(normalized[start:end])
            if end >= text_length:
                break
            start = max(end - chunk_overlap, start + 1)

        return chunks

    def _is_pdf_parser_available(self) -> bool:
        """Check whether the optional PDF parser dependency is installed."""

        try:
            import pypdf  # noqa: F401
        except ImportError:
            return False
        return True

    def _validate_source_file(self, source_path: Path) -> None:
        """Check that the incoming file exists and is an allowed document type."""

        if not source_path.exists():
            raise FileNotFoundError(f"Document not found: {source_path}")

        if not source_path.is_file():
            raise ValueError(f"Path is not a file: {source_path}")

        if source_path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
            raise ValueError(
                f"Unsupported document type '{source_path.suffix}'. Only PDF is allowed."
            )
