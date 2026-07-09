"""
FinancialDocument - Abstract Base Class (ABC)

OOP konsepdleri:
  - ABC (Abstract Base Class) - birbasda obyekt yaratmaq olmaz
  - @abstractmethod - alt siniflerde MECBURI override edilmeli metodlar
  - Protocol - duck typing ucun struktural tip yoxlamasi
  - @property - getter/setter
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Protocol, runtime_checkable


# ==========================================
# 1. Enum - sened novu
# ==========================================
class DocumentType(Enum):
    INVOICE = "invoice"
    AUDIT_REPORT = "audit_report"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"


# ==========================================
# 2. Protocol - duck typing interfeysi
# ==========================================
@runtime_checkable
class Summarizable(Protocol):
    """Xulase vere bilen her hansi obyekt."""
    def summary(self) -> str: ...
    def validate(self) -> bool: ...


# ==========================================
# 3. Abstract Base Class
# ==========================================
@dataclass
class FinancialDocument(ABC):
    """
    Butun maliyye senedlerinin abstract baza sinifi.
    Birbasda: FinancialDocument(...) -> TypeError!
    """
    doc_id: str
    title: str
    created_date: date
    doc_type: DocumentType
    tags: list[str] = field(default_factory=list)

    # Abstract metodlar
    @abstractmethod
    def summary(self) -> str:
        """Alt sinif xulasesini qaytarmalidur."""
        ...

    @abstractmethod
    def validate(self) -> bool:
        """Alt sinif validasiya mentigini yazmalidur."""
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        """Senedi lugete cevir (JSON/DB ucun)."""
        ...

    # Konkret (umumi) metodlar
    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    @property
    def age_days(self) -> int:
        """Senedin nece gunluk oldugu."""
        return (date.today() - self.created_date).days

    def __str__(self) -> str:
        return f"[{self.doc_type.value.upper()}] {self.title} ({self.doc_id})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.doc_id!r}, title={self.title!r})"
