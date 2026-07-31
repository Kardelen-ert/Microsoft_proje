"""Main grounded-answer orchestration logic."""

from __future__ import annotations

import re

from app.rag.foundry_client import FoundryLocalClient
from app.rag.retriever import SemanticRetriever
from app.schemas.query import DiagnosticResponse, QuestionRequest


class RAGEngine:
    """Coordinates retrieval and grounded answer generation."""

    weak_match_distance_threshold = 0.85

    def __init__(self) -> None:
        self.retriever = SemanticRetriever()
        self.foundry_client = FoundryLocalClient()

    def answer_question(self, payload: QuestionRequest) -> DiagnosticResponse:
        """Generate a grounded response from retrieved local chunks only."""

        retrieved_chunks = self.retriever.retrieve(payload.question, top_k=payload.top_k)
        if not retrieved_chunks:
            return DiagnosticResponse(
                answer="Dokumanlarda soruyu destekleyen yeterli kaynak bulunamadi.",
                grounded=False,
                confidence=0.0,
                warning="Kaynak bulunamadigi icin cevap uretilmedi.",
                sources=[],
            )

        top_distance = retrieved_chunks[0].score
        if top_distance > self.weak_match_distance_threshold:
            return DiagnosticResponse(
                answer="Dokumanlarda soruyu destekleyen yeterli kaynak bulunamadi.",
                grounded=False,
                confidence=0.0,
                warning="En yakin kaynaklar zayif eslestigi icin cevap uretilmedi.",
                sources=[],
            )

        sources = [item.source for item in retrieved_chunks]
        llm_answer = self._query_local_llm(payload.question, sources)
        if not llm_answer or not self._is_answer_grounded(llm_answer, sources):
            llm_answer = self._build_extractive_fallback_answer(sources)
            warning = (
                "Model cevabi baglama yeterince sadik bulunmadi; dogrudan kaynak ozeti gosterildi."
            )
        else:
            warning = None

        confidence = max(
            0.0,
            min(1.0, 1.0 - min(top_distance, 1.0) / 2.0 + min(len(sources), 3) * 0.1),
        )

        return DiagnosticResponse(
            answer=llm_answer,
            grounded=True,
            confidence=round(confidence, 2),
            warning=warning,
            sources=sources,
        )

    def _query_local_llm(self, question: str, sources: list) -> str | None:
        """Generate answer using the local Foundry-compatible endpoint."""

        if not sources:
            return None

        context = "\n\n".join(
            [
                f"Belge: {source.document_name} | Sayfa: {source.page_number}\n{source.chunk_text}"
                for source in sources
            ]
        )
        return self.foundry_client.generate_answer(question, context)

    def _build_extractive_fallback_answer(self, sources: list) -> str:
        """Build a deterministic answer without inventing unsupported facts."""

        lines = [
            "Kaynaklarda soruyla ilgili bulunan teknik bolumler ozetlenemedi; ilgili kisimlar asagidadir:"
        ]
        for source in sources:
            snippet = " ".join(source.chunk_text.split())[:220].strip()
            lines.append(f"- {source.document_name} sayfa {source.page_number}: {snippet}")
        return "\n".join(lines)

    def _is_answer_grounded(self, answer: str, sources: list) -> bool:
        """Apply a lightweight lexical grounding check to reduce hallucinated outputs."""

        answer_tokens = {
            self._normalize_token(token)
            for token in answer.replace("\n", " ").split()
            if len(self._normalize_token(token)) >= 4
        }
        answer_tokens.discard("")
        if not answer_tokens:
            return False

        context_text = " ".join(
            self._normalize_token(source.chunk_text.lower()) for source in sources
        )
        matched_token_count = sum(1 for token in answer_tokens if token in context_text)
        return matched_token_count >= max(1, len(answer_tokens) // 8)

    def _normalize_token(self, value: str) -> str:
        """Normalize text for a softer lexical grounding comparison."""

        return re.sub(r"[^\w\s]", "", value.lower()).strip()
