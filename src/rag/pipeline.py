"""
RAGPipeline - Tam RAG axini

RAG nedir?
  Retrieval Augmented Generation:
  1. RETRIEVAL : sual verilir -> oxsar senedler tapilir
  2. AUGMENTED : tapilan senedler kontekst kimi istifade edilir
  3. GENERATION: kontekst + sual -> cavab (LLM ile)

Bu faylda:
  - Addim 1 ve 2 tam implement edilib
  - Addim 3 ucun kontekst hazirlanir (LLM Gün 5-de)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models.financial_document import FinancialDocument

from .embedder import Embedder
from .vector_store import VectorStore


class RAGPipeline:
    """
    Maliyye sened bazasi uzerinde sual-cavab sistemi.

    Istifade:
        pipeline = RAGPipeline()
        pipeline.add(invoice1)
        pipeline.add(audit_report1)

        results = pipeline.query("bank uzlesdirmesi problemi")
        for r in results:
            print(r["id"], r["distance"])
    """

    def __init__(self, persist_dir: str = "./chroma_db"):
        print("[RAGPipeline] Bashlayir...")
        self.embedder = Embedder()
        self.store = VectorStore(persist_dir=persist_dir)
        print(f"[RAGPipeline] Hazirdir. Bazada {self.store.count()} sened var.")

    def add(self, doc: FinancialDocument) -> None:
        """Tek sened elave et."""
        self.store.add_document(doc, self.embedder)

    def add_many(self, docs: List[FinancialDocument]) -> None:
        """Bir nece sened elave et."""
        self.store.add_documents(docs, self.embedder)

    def query(
        self,
        question: str,
        n_results: int = 3,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Suala oxsar sened tap.

        Args:
            question : "bank uzlesdirmesi hansi senetlerde var?"
            n_results: nece netice qaytarilsin
            doc_type : "invoice" / "audit_report" (istege bagli filter)

        Qaytarir:
            [{"id", "text", "metadata", "distance"}]
            distance: 0 = eyni, 1 = tam fərqli
        """
        print(f"\n[RAG] Sorgu: '{question}'")
        results = self.store.search(
            query=question,
            embedder=self.embedder,
            n_results=n_results,
            doc_type=doc_type,
        )
        return results

    def query_with_context(self, question: str, n_results: int = 3) -> str:
        """
        Sual ver, oxsar sened tap, LLM ucun kontekst hazirla.
        (Gün 5-de LLM caği buraya elave edilecek)
        """
        results = self.query(question, n_results=n_results)

        if not results:
            return "Bazada uygun sened tapilmadi."

        # Kontekst formatla
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"--- Sened {i} (ID: {r['id']}, Oxsarliq: {1 - r['distance']:.0%}) ---\n"
                f"{r['text']}"
            )

        context = "\n\n".join(context_parts)

        # Gün 5-de bu hissede LLM cagrilacaq:
        # answer = llm.generate(prompt=f"Kontekst:\n{context}\n\nSual: {question}")
        # return answer

        return f"TAPILAN KONTEKST:\n\n{context}\n\n[Gün 5-de LLM cavabi burada olacaq]"

    @property
    def document_count(self) -> int:
        return self.store.count()

    def reset(self) -> None:
        """Bazani sifirla (test ucun)."""
        self.store.reset()
