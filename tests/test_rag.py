"""
RAG Testleri - Gun 4

Isletmek:
    pytest tests/test_rag.py -v
"""

from datetime import date

import pytest

from src.models.audit_report import AuditReport, RiskLevel
from src.models.financial_document import DocumentType
from src.models.invoice import Invoice, InvoiceStatus
from src.rag.pipeline import RAGPipeline


@pytest.fixture
def sample_invoice():
    return Invoice(
        doc_id="INV-TEST-001",
        title="IT Xidmetleri",
        created_date=date(2026, 1, 1),
        doc_type=DocumentType.INVOICE,
        vendor_name="TechCo",
        amount=5000.0,
        due_date=date(2026, 2, 1),
    )


@pytest.fixture
def sample_audit():
    rep = AuditReport(
        doc_id="AUD-TEST-001",
        title="Q1 Audit Hesabati",
        created_date=date(2026, 1, 1),
        doc_type=DocumentType.AUDIT_REPORT,
        auditor_name="Test Auditor",
        audit_period_start=date(2025, 1, 1),
        audit_period_end=date(2025, 12, 31),
    )
    rep.add_finding("F-001", "Bank uzlesdirmesi gec aparilmisdir", RiskLevel.HIGH)
    return rep


@pytest.fixture
def pipeline(tmp_path):
    """Her test ucun temiz pipeline yarat (tmp_path = müveqqeti qovluq)."""
    p = RAGPipeline(persist_dir=str(tmp_path / "chroma_test"))
    return p


class TestRAGPipeline:
    def test_add_and_count(self, pipeline, sample_invoice, sample_audit):
        assert pipeline.document_count == 0
        pipeline.add(sample_invoice)
        assert pipeline.document_count == 1
        pipeline.add(sample_audit)
        assert pipeline.document_count == 2

    def test_query_returns_results(self, pipeline, sample_invoice, sample_audit):
        pipeline.add_many([sample_invoice, sample_audit])
        results = pipeline.query("bank uzlesdirmesi", n_results=2)
        assert len(results) > 0
        assert "id" in results[0]
        assert "distance" in results[0]

    def test_query_audit_closer_to_audit_question(
        self, pipeline, sample_invoice, sample_audit
    ):
        pipeline.add_many([sample_invoice, sample_audit])
        results = pipeline.query("audit tapintisi risk", n_results=2)
        # En oxsar sened audit_report olmalidir
        assert results[0]["id"] == "AUD-TEST-001"

    def test_query_invoice_closer_to_invoice_question(
        self, pipeline, sample_invoice, sample_audit
    ):
        pipeline.add_many([sample_invoice, sample_audit])
        results = pipeline.query("faktura satici meblegi", n_results=2)
        assert results[0]["id"] == "INV-TEST-001"

    def test_query_with_context_returns_string(self, pipeline, sample_audit):
        pipeline.add(sample_audit)
        context = pipeline.query_with_context("risk tapintilari", n_results=1)
        assert isinstance(context, str)
        assert "AUD-TEST-001" in context

    def test_reset_clears_all(self, pipeline, sample_invoice):
        pipeline.add(sample_invoice)
        assert pipeline.document_count == 1
        pipeline.reset()
        assert pipeline.document_count == 0
