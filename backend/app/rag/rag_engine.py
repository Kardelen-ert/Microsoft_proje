"""Main grounded-answer orchestration logic."""

from __future__ import annotations

import json

from app.core.config import get_settings
from app.rag.retriever import LocalVectorRetriever 
from app.schemas.query import DiagnosticResponse, QuestionRequest

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate

class RAGEngine:
    """Coordinates retrieval and grounded answer generation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.retriever = LocalVectorRetriever()
        
        # 1. Modeli sistem başlarken belleğe alıyoruz
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" 
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # device_map="auto" modeli otomatik olarak algıladığı en iyi GPU'ya atar.
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto"
        )
        
        # 2. Text-Generation Pipeline Kurulumu (Durdurma belirteçleri eklendi)
        pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=256,
            temperature=0.1, 
            do_sample=True,
            repetition_penalty=1.1,
            return_full_text=False,
            eos_token_id=self.tokenizer.eos_token_id, 
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        self.llm = HuggingFacePipeline(pipeline=pipe)
        
# 3. Raylı Sistemler Prompt Şablonu (Tamamen Türkçe yönlendirme)
        template = """<|system|>
Sen raylı sistemler arıza teşhisi konusunda uzman bir yapay zeka asistanısın. Teknisyenin sorusunu SADECE aşağıdaki bağlamı (context) kullanarak ve KESİNLİKLE TÜRKÇE dilinde yanıtla. Kendi bilgini ekleme. Eğer bağlamda sorunun cevabı yoksa, sadece "Bu konuda dokümanlarda bilgi bulamadım." de.</s>
<|user|>
Bağlam:
{context}

Soru: {question}</s>
<|assistant|>
"""
        self.prompt = PromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm

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
        
        # Yerel in-memory modelimizi çağırıyoruz
        llm_answer = self._query_local_llm(payload.question, sources)
        
        # LLM'de bellek hatası vs. olursa fallback sistemi devreye girecek
        if llm_answer is None:
            llm_answer = self._build_extractive_fallback_answer(sources)

        top_score = retrieved_chunks[0].score if retrieved_chunks else 1.0 
        grounded = bool(sources) and top_score < 1.0 
        confidence = max(0.0, min(1.0, 1.0 - (top_score / 2.0) + min(len(sources), 3) * 0.1))

        return DiagnosticResponse(
            answer=llm_answer,
            grounded=grounded,
            confidence=round(confidence, 2),
            warning=None if grounded else "Yanitta yeterli grounding saglanamadi.",
            sources=sources,
        )

    def _query_local_llm(self, question: str, sources: list) -> str | None:
        """Generate answer using local HuggingFace model dynamically."""

        if not sources:
            return None

        # ChromaDB'den gelen parçaları tek bir metin bloğunda birleştiriyoruz
        context = "\n\n".join(
            [
                f"Belge: {source.document_name} | Sayfa: {source.page_number}\n{source.chunk_text}"
                for source in sources
            ]
        )
        
        try:
            # Hazırladığımız LangChain chain'ini tetikliyoruz
            response = self.chain.invoke({
                "context": context,
                "question": question
            })
            
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            # Model patlarsa sessizce None dönüp fallback'in çalışmasını sağlıyoruz
            print(f"LLM Uretim Hatasi: {e}")
            return None
            
        return None

    def _build_extractive_fallback_answer(self, sources: list) -> str:
        """Build a deterministic answer without inventing unsupported facts."""

        lines = [
            "Yerel LLM yanit uretemedigi icin dokumanlardan dogrudan alinan ilgili bolumler listeleniyor:"
        ]
        for source in sources:
            snippet = source.chunk_text[:280].strip()
            lines.append(
                f"- {source.document_name} sayfa {source.page_number}: {snippet}"
            )
        return "\n".join(lines)