"""Document ingestion helpers for local document management with vector indexing."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.core.constants import CHUNK_STORE_FILE_NAME, STATUS_FILE_NAME, SUPPORTED_DOCUMENT_SUFFIXES
from app.db.repositories import DocumentRepository
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import ChromaVectorStore


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
    """Normalized chunk payload generated from source text."""

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
    """Copies local files into the backend data area and indexes chunks in ChromaDB."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.status_file = settings.vector_store_dir / STATUS_FILE_NAME
        self.chunk_store_file = settings.vector_store_dir / CHUNK_STORE_FILE_NAME
        self.document_repository = DocumentRepository()
        self.embedding_service = EmbeddingService()
        self.vector_store = ChromaVectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
        )

    def ingest(self, file_paths: list[str], rebuild_index: bool) -> IngestionResult:
        """Validate, copy, persist metadata for the given file paths, and store vectors."""

        self.settings.raw_pdfs_dir.mkdir(parents=True, exist_ok=True)
        self.settings.vector_store_dir.mkdir(parents=True, exist_ok=True)

        if rebuild_index:
            self._clear_existing_documents()

        ingested_documents: list[IngestedDocument] = []
        all_chunks: list[ChunkRecord] = []
        parser_ready = self._is_pdf_parser_available()
        embeddings_ready = self.embedding_service.is_available()

        for raw_path in file_paths:
            source_path = Path(raw_path).expanduser().resolve()
            self._validate_source_file(source_path)

            destination_path = self.settings.raw_pdfs_dir / source_path.name
            if source_path != destination_path:
                shutil.copy2(source_path, destination_path)
            document_chunks = (
                self._extract_chunks(destination_path, parser_ready=parser_ready)
                if self._can_extract_text(destination_path, parser_ready=parser_ready)
                else []
            )
            all_chunks.extend(document_chunks)
            self._persist_document(destination_path, document_chunks)

            ingested_documents.append(
                IngestedDocument(
                    source_path=str(source_path),
                    stored_path=str(destination_path),
                    file_name=source_path.name,
                    ingested_at=datetime.now(timezone.utc).isoformat(),
                    chunk_count=len(document_chunks),
                )
            )

        if all_chunks and embeddings_ready:
            ids = [chunk.chunk_id for chunk in all_chunks]
            documents = [chunk.text for chunk in all_chunks]
            metadatas = [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_name": chunk.document_name,
                    "page_number": chunk.page_number,
                }
                for chunk in all_chunks
            ]
            embeddings = self.embedding_service.embed_documents(documents)
            self.vector_store.add_chunks(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

        manifest = {
            "rebuild_index": rebuild_index,
            "indexed_documents": len(ingested_documents),
            "indexed_chunks": len(all_chunks),
            "parser_ready": parser_ready and embeddings_ready,
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
            parser_ready=parser_ready and embeddings_ready,
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
        """Remove previously copied PDFs, reset the status manifest, and clear ChromaDB."""

        for stored_file in self.settings.raw_pdfs_dir.iterdir():
            if stored_file.is_file():
                stored_file.unlink()

        if self.status_file.exists():
            self.status_file.unlink()

        if self.chunk_store_file.exists():
            self.chunk_store_file.unlink()

        self.document_repository.clear_documents()

        try:
            self.vector_store.reset_collection()
        except Exception:
            pass

    def _persist_document(self, pdf_path: Path, chunks: list[ChunkRecord]) -> None:
        """Store document metadata and chunk rows in SQLite."""

        document_id = self.document_repository.create_document(
            file_path=str(pdf_path),
            title=pdf_path.stem,
        )

        for chunk_index, chunk in enumerate(chunks, start=1):
            self.document_repository.add_chunk(
                document_id=document_id,
                chunk_index=chunk_index,
                content=chunk.text,
                page_number=chunk.page_number,
                token_count=chunk.char_count,
                source_label=f"{chunk.document_name} - Page {chunk.page_number}",
                chunk_id=chunk.chunk_id,
            )

    def _extract_chunks(self, source_path: Path, parser_ready: bool) -> list[ChunkRecord]:
        """Extract text from a supported source file and split it into chunks."""

        suffix = source_path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf_chunks(source_path)
        if suffix in {".md", ".txt"}:
            return self._extract_text_chunks(source_path)
        if not parser_ready:
            return []
        return []

    def _extract_pdf_chunks(self, pdf_path: Path) -> list[ChunkRecord]:
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

    def _extract_text_chunks(self, text_path: Path) -> list[ChunkRecord]:
        """Extract chunks from a markdown or plain-text source."""

        text = text_path.read_text(encoding="utf-8").strip()
        if not text:
            return []

        chunks: list[ChunkRecord] = []
        for chunk_index, chunk_text in enumerate(self._split_text(text), start=1):
            chunks.append(
                ChunkRecord(
                    chunk_id=f"{text_path.stem}-p1-c{chunk_index}",
                    document_name=text_path.name,
                    page_number=1,
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

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return splitter.split_text(normalized)

    def _is_pdf_parser_available(self) -> bool:
        """Check whether the optional PDF parser dependency is installed."""

        try:
            import pypdf  # noqa: F401
        except ImportError:
            return False
        return True

    def _can_extract_text(self, source_path: Path, parser_ready: bool) -> bool:
        """Return whether a given file can be parsed in the current environment."""

        suffix = source_path.suffix.lower()
        if suffix in {".md", ".txt"}:
            return True
        if suffix == ".pdf":
            return parser_ready
        return False

    def _validate_source_file(self, source_path: Path) -> None:
        """Check that the incoming file exists and is an allowed document type."""

        if not source_path.exists():
            raise FileNotFoundError(f"Document not found: {source_path}")

        if not source_path.is_file():
            raise ValueError(f"Path is not a file: {source_path}")

        if source_path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
            raise ValueError(
                f"Unsupported document type '{source_path.suffix}'. Allowed types: "
                f"{', '.join(sorted(SUPPORTED_DOCUMENT_SUFFIXES))}."
            )
