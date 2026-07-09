"""
schemas.py - API request/response modelləri

Pydantic konseptleri:
  - BaseModel   : avtomatik validasiya + JSON serialization
  - Field()     : default deyər, acıqlama, min/max
  - model_config: konfiqurasiya (json schema nümunəsi)
  - Tip iyerarxiyası: Request -> Response
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

# ==========================================
# REQUEST modelləri (gələn məlumat)
# ==========================================

class InvoiceCreateRequest(BaseModel):
    """POST /documents/invoice ucun gelen data."""
    doc_id: str = Field(..., description="Unikal ID", example="INV-2026-001")
    title: str = Field(..., min_length=3, example="IT Xidmetleri")
    vendor_name: str = Field(..., example="TechCo MMC")
    amount: float = Field(..., gt=0, description="Meblegi musbat olmalidir")
    currency: str = Field(default="AZN", example="AZN")
    due_date: date = Field(..., example="2026-02-15")
    created_date: date = Field(default_factory=date.today)
    tags: list[str] = Field(default_factory=list)


class AuditReportCreateRequest(BaseModel):
    """POST /documents/audit ucun gelen data."""
    doc_id: str = Field(..., example="AUD-2026-Q1")
    title: str = Field(..., min_length=3, example="Q1 Maliyye Auditi")
    auditor_name: str = Field(..., example="Leyla Hesenova")
    audit_period_start: date = Field(..., example="2025-01-01")
    audit_period_end: date = Field(..., example="2025-12-31")
    created_date: date = Field(default_factory=date.today)
    tags: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """POST /query ucun gelen data."""
    question: str = Field(
        ...,
        min_length=3,
        example="Bank uzlesdirmesinde hansi problemler var?"
    )
    n_results: int = Field(default=3, ge=1, le=10)
    doc_type: Optional[str] = Field(
        default=None,
        example="audit_report",
        description="'invoice' ve ya 'audit_report' (istege bagli)"
    )
    use_llm: bool = Field(
        default=True,
        description="LLM ile cavab generasiya edilsinmi?"
    )


# ==========================================
# RESPONSE modelləri (gonderilen məlumat)
# ==========================================

class DocumentResponse(BaseModel):
    """Tek senedin cavabi."""
    doc_id: str
    doc_type: str
    title: str
    created_date: date
    summary: str

    model_config = {"from_attributes": True}


class SearchResult(BaseModel):
    """Bir axtaris neticesi."""
    doc_id: str
    title: str
    doc_type: str
    similarity: float = Field(description="0-100% arasi oxsarliq")
    excerpt: str = Field(description="Senedin xulasesinden parcasi")


class QueryResponse(BaseModel):
    """POST /query cavabi."""
    question: str
    answer: str
    sources: list[SearchResult]
    model_used: Optional[str] = None


class DocumentListResponse(BaseModel):
    """GET /documents cavabi."""
    total: int
    documents: list[DocumentResponse]


class StatusResponse(BaseModel):
    """GET /health cavabi."""
    status: str
    document_count: int
    version: str = "1.0.0"
