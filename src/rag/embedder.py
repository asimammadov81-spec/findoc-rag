"""
Embedder - metn -> vektor cevirme

RAG konseptleri:
  - Embedding: metni reqemli vektora cevirmek
  - sentence-transformers: her cumle/paragraf ucun vektor yaradir
  - Oxsar metinler oxsar vektorlara malikdir
  - Bu vektorlar ChromaDB-de saxlanilir ve axtalanir

Kitabxana: pip install sentence-transformers
Model: all-MiniLM-L6-v2 (kicik, suretle isleyir)
"""

from typing import List

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False


class Embedder:
    """
    Metni vektor seklinde temsil edir.

    Istifade:
        embedder = Embedder()
        vector = embedder.embed("Bank hesabi uzlesdirmesi aparilmayib")
        # [0.12, -0.34, 0.87, ...]  <- 384 ededden ibaret vektor
    """

    # Default model - yungul ve suretle
    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = DEFAULT_MODEL):
        if not ST_AVAILABLE:
            raise ImportError(
                "sentence-transformers qurashdirilmayib.\n"
                "Terminalda: pip install sentence-transformers"
            )
        print(f"[Embedder] Model yuklenir: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print("[Embedder] Hazirdir.")

    def embed(self, text: str) -> List[float]:
        """
        Bir metni vektora cevir.
        Qaytarir: 384 elementli float siyahisi
        """
        vector = self.model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Bir nece metni eyni anda vektora cevir (daha sureli).
        """
        vectors = self.model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()

    @property
    def dimension(self) -> int:
        """Vektor olcusu (all-MiniLM-L6-v2 ucun 384)."""
        return self.model.get_sentence_embedding_dimension()
