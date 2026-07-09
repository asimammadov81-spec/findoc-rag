"""
LLMClient - OpenAI ile cavab generasiyasi

LLM + RAG konseptleri:
  - System prompt : LLM-in rolu ve qaydalar
  - User prompt   : kontekst + sual
  - Temperature   : 0 = deterministik, 1 = yaradici
  - Max tokens    : cavab uzunlugu limiti
  - Fallback      : API yoxdursa mock cavab
"""

import os

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


SYSTEM_PROMPT = """Sen maliyye audit mutexessisisen.
Sana verilmis sened kontekstine esasen suallara Azerbaycan dilinde cavab ver.
Kontekstde olmayan melumati uydurmaq olmaz - bele hallarda "Senetlerde bu melumat yoxdur" de.
Cavablar qisa, deqiq ve professional olmalidir."""


class LLMClient:
    """OpenAI GPT ile maliyye sual-cavab."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 500,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        api_key = os.getenv("OPENAI_API_KEY")

        if OPENAI_AVAILABLE and api_key:
            self.client = OpenAI(api_key=api_key)
            self.mode = "openai"
            print(f"[LLM] OpenAI rejimi: {model}")
        else:
            self.client = None
            self.mode = "mock"
            print("[LLM] Mock rejimi (OPENAI_API_KEY yoxdur)")

    def answer(self, question: str, context: str) -> str:
        """Kontekst + sual -> LLM cavabi."""
        if self.mode == "openai":
            return self._openai_answer(question, context)
        else:
            return self._mock_answer(question, context)

    def _openai_answer(self, question: str, context: str) -> str:
        user_prompt = (
            f"Asagidaki maliyye senedleri kontekstine bax:\n\n"
            f"{context}\n\n"
            f"Sual: {question}"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    def _mock_answer(self, question: str, context: str) -> str:
        """API olmadan test ucun saxta cavab."""
        lines = [ln.strip() for ln in context.split("\n") if ln.strip()]
        excerpt = lines[0] if lines else "..."
        return (
            f"[MOCK CAVAB] Sual: '{question}'\n"
            f"Kontekstden: '{excerpt}'\n"
            f"Real cavab ucun OPENAI_API_KEY tenzimleyin."
        )

    @property
    def is_real(self) -> bool:
        return self.mode == "openai"
