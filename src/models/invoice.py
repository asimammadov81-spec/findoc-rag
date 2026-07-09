"""
Invoice - FinancialDocument-in konkret alt sinifi
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from .financial_document import DocumentType, FinancialDocument


class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class Invoice(FinancialDocument):
    """Faktura senedi."""

    vendor_name: str = ""
    amount: float = 0.0
    currency: str = "AZN"
    due_date: date = field(default_factory=date.today)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    line_items: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.doc_type = DocumentType.INVOICE

    def summary(self) -> str:
        return (
            f"Faktura: {self.title}\n"
            f"  Satici : {self.vendor_name}\n"
            f"  Meblegi: {self.amount:,.2f} {self.currency}\n"
            f"  Status : {self.status.value}\n"
            f"  Son tarix: {self.due_date}"
        )

    def validate(self) -> bool:
        errors = []
        if not self.vendor_name:
            errors.append("vendor_name bosdur")
        if self.amount <= 0:
            errors.append(f"amount musbet olmalidir ({self.amount})")
        if self.due_date < self.created_date:
            errors.append("due_date, created_date-den evvel ola bilmez")
        if errors:
            print(f"[Validate] {self.doc_id} - xetalar: {errors}")
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type.value,
            "title": self.title,
            "created_date": self.created_date.isoformat(),
            "vendor_name": self.vendor_name,
            "amount": self.amount,
            "currency": self.currency,
            "due_date": self.due_date.isoformat(),
            "status": self.status.value,
            "tags": self.tags,
            "line_items": self.line_items,
        }

    @property
    def is_overdue(self) -> bool:
        return self.due_date < date.today() and self.status != InvoiceStatus.PAID

    def add_line_item(self, description: str, qty: float, unit_price: float) -> None:
        self.line_items.append({
            "description": description,
            "qty": qty,
            "unit_price": unit_price,
            "total": qty * unit_price,
        })
        self.amount = sum(item["total"] for item in self.line_items)
