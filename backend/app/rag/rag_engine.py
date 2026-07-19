"""Main grounded-answer orchestration logic."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.rag.retriever import LocalKeywordRetriever
from app.schemas.query import DiagnosticResponse, QuestionRequest


class RAGEngine:
    """Coordinates retrieval and grounded answer generation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.retriever = LocalKeywordRetriever()

    def answer_question(self, payload: QuestionRequest) -> DiagnosticResponse:
        """Generate a grounded response from retrieved local chunks only."""

        retrieved_chunks = self.retriever.retrieve(payload.question, top_k=payload.top_k)
        if not retrieved_chunks:
            return DiagnosticResponse(
                answer=(
                    "Dokumanlarda soruyu destekleyen yeterli kaynak bulunamadi. "
                    "Guvenilir cevap uretilmedi."
                ),
                grounded=False,
                confidence=0.0,
                warning="Retrieval sonucu bos oldugu icin sistem tahmini cevap vermedi.",
                sources=[],
            )

        sources = [item.source for item in retrieved_chunks]
        llm_answer = self._query_local_llm(payload.question, sources)
        if llm_answer is None:
            llm_answer = self._build_extractive_fallback_answer(sources)

        top_score = retrieved_chunks[0].score if retrieved_chunks else 0.0
        grounded = bool(sources) and top_score > 0
        confidence = min(1.0, top_score + min(len(sources), 3) * 0.1)

        return DiagnosticResponse(
            answer=llm_answer,
            grounded=grounded,
            confidence=round(confidence, 2),
            warning=None if grounded else "Yanitta yeterli grounding saglanamadi.",
            sources=sources,
        )

    def _query_local_llm(self, question: str, sources: list) -> str | None:
        """Ask the local Foundry-compatible chat endpoint for a strictly grounded answer."""

        if not sources:
            return None

        context = "\n\n".join(
            [
                f"Belge: {source.document_name} | Sayfa: {source.page_number}\n{source.chunk_text}"
                for source in sources
            ]
        )
        prompt = (
            "Sadece verilen baglama dayanarak cevap ver. "
            "Baglamda yoksa bilmedigini soyle. Teknik olmayan tahmin uretme.\n\n"
            f"Soru: {question}\n\nBaglam:\n{context}"
        )
        body = {
            "model": self.settings.llm_model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
        request = Request(
            url=f"{self.settings.llm_base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

        choices = payload.get("choices", [])
        if not choices:
            return None

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        return None

    def _build_extractive_fallback_answer(self, sources: list) -> str:
        """Build a deterministic answer without inventing unsupported facts."""

        lines = [
            "Yerel LLM erisilemedigi icin dokumanlardan dogrudan alinan ilgili bolumler listeleniyor:"
        ]
        for source in sources:
            snippet = source.chunk_text[:280].strip()
            lines.append(
                f"- {source.document_name} sayfa {source.page_number}: {snippet}"
            )
        return "\n".join(lines)
