"""Client adapter for Foundry Local compatible chat completions."""

from __future__ import annotations

import httpx

from app.core.config import get_settings


class FoundryLocalClient:
    """Calls the local OpenAI-compatible chat endpoint."""

    insufficient_context_marker = "YETERSIZ_BAGLAM"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model_name = settings.llm_model_name

    def generate_answer(self, question: str, context: str) -> str | None:
        """Generate a grounded answer using only provided context."""

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sen teknik bir RAG asistanisin. "
                        "Yalnizca kullaniciya verilen BAGLAM metnindeki bilgilerle cevap ver. "
                        "Baglamda gecmeyen hicbir bilgiyi ekleme, tahmin yapma, genelleme yapma. "
                        "Eger baglam soruyu net karsilamiyorsa yalnizca "
                        f"'{self.insufficient_context_marker}' yaz. "
                        "Cevap verirsen kisa, teknik ve dogrudan cevap ver. "
                        "Metni oldugu gibi kopyalama; baglamdaki bilgiyi 2 ila 4 cumlede acik ve duzgun bicimde yeniden ifade et. "
                        "Eger soru adim veya neden listesi istiyorsa en fazla 3 maddelik kisa liste kullan."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Kurallar:\n"
                        "1. Yalnizca BAGLAM bilgisini kullan.\n"
                        "2. Baglam disi bilgi ekleme.\n"
                        "3. Cevabi kisa ozetle; dogrudan paragraf kopyalama yapma.\n"
                        "4. Teknik terimleri koru ama gereksiz tekrar yapma.\n"
                        f"5. Yetersizse yalnizca {self.insufficient_context_marker} yaz.\n\n"
                        f"Soru: {question}\n\nBAGLAM:\n{context}"
                    ),
                },
            ],
            "temperature": 0.0,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(f"{self.base_url}/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return None

        try:
            answer = data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

        if not answer or self.insufficient_context_marker in answer:
            return None
        return answer
