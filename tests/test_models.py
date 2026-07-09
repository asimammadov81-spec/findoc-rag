"""
Testler - Gun 1 + Gun 2

pytest ile islet:
    pytest tests/ -v
"""

from datetime import date

import pytest

from src.models.audit_report import AuditReport, RiskLevel
from src.models.financial_document import DocumentType, FinancialDocument, Summarizable
from src.models.invoice import Invoice, InvoiceStatus

# ==========================================
# Gun 1 - Model testleri
# ==========================================

class TestAbstractBase:
    def test_cannot_instantiate_abstract_class(self):
        """FinancialDocument birbasda yaradila bilmez."""
        with pytest.raises(TypeError):
            FinancialDocument(
                doc_id="X",
                title="Test",
                created_date=date.today(),
                doc_type=DocumentType.INVOICE,
            )

    def test_invoice_is_summarizable(self):
        """Invoice Summarizable Protocol-unu temin edir."""
        inv = Invoice(
            doc_id="INV-001",
            title="Test",
            created_date=date.today(),
            doc_type=DocumentType.INVOICE,
            vendor_name="ABC",
            amount=100.0,
        )
        assert isinstance(inv, Summarizable)

    def test_audit_report_is_summarizable(self):
        rep = AuditReport(
            doc_id="AUD-001",
            title="Q1 Audit",
            created_date=date.today(),
            doc_type=DocumentType.AUDIT_REPORT,
            auditor_name="Ali",
        )
        assert isinstance(rep, Summarizable)


class TestInvoice:
    def setup_method(self):
        self.inv = Invoice(
            doc_id="INV-TEST-001",
            title="Xidmet Fakturasi",
            created_date=date(2026, 1, 1),
            doc_type=DocumentType.INVOICE,
            vendor_name="TechCo",
            amount=0.0,
            currency="AZN",
            due_date=date(2026, 2, 1),
        )

    def test_validate_passes(self):
        self.inv.amount = 500.0
        assert self.inv.validate() is True

    def test_validate_fails_no_vendor(self):
        self.inv.vendor_name = ""
        self.inv.amount = 100.0
        assert self.inv.validate() is False

    def test_validate_fails_zero_amount(self):
        assert self.inv.validate() is False

    def test_add_line_item_updates_amount(self):
        self.inv.add_line_item("Konsaltinq", qty=10, unit_price=50.0)
        self.inv.add_line_item("Texniki Destek", qty=5, unit_price=30.0)
        assert self.inv.amount == 650.0
        assert len(self.inv.line_items) == 2

    def test_to_dict_keys(self):
        d = self.inv.to_dict()
        assert "doc_id" in d
        assert "vendor_name" in d
        assert "line_items" in d

    def test_tags(self):
        self.inv.add_tag("odenilmeli")
        self.inv.add_tag("odenilmeli")  # duplicate - elave olunmamali
        assert self.inv.tags.count("odenilmeli") == 1
        assert self.inv.has_tag("odenilmeli") is True

    def test_age_days(self):
        assert self.inv.age_days > 0

    def test_str_repr(self):
        assert "INV-TEST-001" in str(self.inv)
        assert "Invoice" in repr(self.inv)


class TestAuditReport:
    def setup_method(self):
        self.rep = AuditReport(
            doc_id="AUD-2026-01",
            title="Illik Audit",
            created_date=date(2026, 1, 1),
            doc_type=DocumentType.AUDIT_REPORT,
            auditor_name="Leyla Hesenova",
            audit_period_start=date(2025, 1, 1),
            audit_period_end=date(2025, 12, 31),
        )

    def test_validate_passes(self):
        assert self.rep.validate() is True

    def test_validate_fails_no_auditor(self):
        self.rep.auditor_name = ""
        assert self.rep.validate() is False

    def test_add_finding_updates_risk(self):
        self.rep.add_finding("F-001", "Nezaret zeifliyi", RiskLevel.HIGH)
        self.rep.add_finding("F-002", "Sened noxsani", RiskLevel.MEDIUM)
        assert self.rep.overall_risk == RiskLevel.HIGH
        assert len(self.rep.findings) == 2

    def test_findings_by_risk(self):
        self.rep.add_finding("F-001", "Kritik tapinti", RiskLevel.CRITICAL)
        self.rep.add_finding("F-002", "Orta tapinti", RiskLevel.MEDIUM)
        critical = self.rep.findings_by_risk(RiskLevel.CRITICAL)
        assert len(critical) == 1

    def test_to_dict_contains_findings(self):
        self.rep.add_finding("F-001", "Test tapintisi", RiskLevel.LOW)
        d = self.rep.to_dict()
        assert len(d["findings"]) == 1
        assert d["findings"][0]["finding_id"] == "F-001"
