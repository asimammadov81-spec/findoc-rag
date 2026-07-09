"""
VectorStore - ChromaDB ile sened saxlama ve axtaris

RAG konseptleri:
  - Collection: ChromaDB-de sened qrupu (cədvəl kimisi)
  - Document : saxlanilan metin parcasi
  - Metadata : senedle bagli elave melumat (id, nov, tarix...)
  - Query    : oxsar sened axtar (cosine similarity)

Kitabxana: pip install chromadb
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from src.models.financial_document import FinancialDocument


class VectorStore:
    """
    Maliyye senedlerini vektor kimi saxlayir ve axtalayir.

    Istifade:
        store = VectorStore(persist_dir="./chroma_db")
        store.add_document(invoice)
        results = store.search("bank uzlesdirmesi", n_results=3)
    """

    COLLECTION_NAME = "financial_documents"

    def __init__(self, persist_dir: str = "./chroma_db"):
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb qurashdirilmayib.\n"
                "Terminalda: pip install chromadb"
            )
        # persist_dir: vektor bazasi disk-de saxlanilir
        # Proqram yeniden bashlayanda melumatlar qalir
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # oxsarliq olcusu
        )
        print(f"[VectorStore] Hazirdir. Sened sayi: {self.collection.count()}")

    def add_document(self, doc: FinancialDocument, embedder) -> None:
        """
        Bir senedi ChromaDB-ye elave et.
        - summary() metni embed edilir
        - metadata kimi to_dict() saxlanilir
        """
        text = doc.summary()
        vector = embedder.embed(text)
        metadata = {
            "doc_type": doc.doc_type.value,
            "title": doc.title,
            "created_date": doc.created_date.isoformat(),
        }
        self.collection.upsert(  # varsa yenile, yoxdursa elave et
            ids=[doc.doc_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata],
        )
        print(f"[VectorStore] Elave edildi: {doc.doc_id}")

    def add_documents(self, docs: List[FinancialDocument], embedder) -> None:
        """Bir nece senedi toplu elave et."""
        for doc in docs:
            self.add_document(doc, embedder)

    def search(
        self,
        query: str,
        embedder,
        n_results: int = 3,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sorguya en oxsar sened(ler)i tap.

        Args:
            query    : axtalanacaq metin
            embedder : sorgu vektora cevirilir
            n_results: nece sened qaytarilsin
            doc_type : "invoice" ve ya "audit_report" (filter)

        Qaytarir:
            [{"id": ..., "text": ..., "metadata": ..., "distance": ...}]
        """
        query_vector = embedder.embed(query)

        where = {"doc_type": doc_type} if doc_type else None

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(n_results, self.collection.count() or 1),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": round(results["distances"][0][i], 4),
            })
        return output

    def count(self) -> int:
        return self.collection.count()

    def delete_document(self, doc_id: str) -> None:
        self.collection.delete(ids=[doc_id])
        print(f"[VectorStore] Silindi: {doc_id}")

    def reset(self) -> None:
        """Butun sened koleksiyasini sil (test ucun)."""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print("[VectorStore] Koleksiya sifirlanди.")
