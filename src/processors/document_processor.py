"""
DocumentProcessor - Abstract processor sinifi
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from src.models.financial_document import FinancialDocument

T = TypeVar("T", bound=FinancialDocument)


class ProcessorError(Exception):
    """Processor xetalari ucun xususi exception."""
    pass


class DocumentProcessor(ABC, Generic[T]):
    """
    Butun fayl parserlerin baza sinifi.

    Istifade:
        with PdfProcessor("invoice.pdf") as proc:
            doc = proc.parse()
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._is_open = False

    def __enter__(self):
        if not self.file_path.exists():
            raise ProcessorError(f"Fayl tapilmadi: {self.file_path}")
        self._is_open = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._is_open = False
        return False

    @abstractmethod
    def parse(self) -> T:
        """Faylu oxu ve FinancialDocument-e cevir."""
        ...

    @abstractmethod
    def extract_text(self) -> str:
        """Fayldan xam metni cixar."""
        ...

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Bu processor hansi uzantilari destekleyir?"""
        ...

    def validate_extension(self) -> None:
        suffix = self.file_path.suffix.lower()
        if suffix not in self.supported_extensions():
            raise ProcessorError(
                f"Desteklenmeyen format: {suffix}. "
                f"Gozklenilen: {self.supported_extensions()}"
            )

    @property
    def file_size_kb(self) -> float:
        return self.file_path.stat().st_size / 1024 if self.file_path.exists() else 0.0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self.file_path.name!r})"
