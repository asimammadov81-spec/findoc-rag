"""
PdfParser - PDF faylından Invoice/AuditReport cixarir
Kitabxana: PyMuPDF (fitz) - pip install pymupdf
"""

import re
from datetime import date, datetime
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from src.models.audit_report import AuditFinding, AuditReport, RiskLevel
from src.models.financial_document import DocumentType
from src.models.invoice import Invoice, InvoiceStatus

from .document_processor import DocumentProcessor, ProcessorError


class PdfParser(DocumentProcessor):
    """
    PDF faylından maliyye senedi cixarir.

    Istifade:
        with PdfParser("faktura.pdf") as parser:
            invoice = parser.parse()
            print(invoice.summary())
    """

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def extract_text(self) -> str:
        if not PYMUPDF_AVAILABLE:
            raise ProcessorError(
                "PyMuPDF qurashdirilmayib. "
                "Terminalda: pip install pymupdf"
            )
        text_parts = []
        try:
            doc = fitz.open(str(self.file_path))
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
        except Exception as e:
            raise ProcessorError(f"PDF oxuma xetasi: {e}") from e
        return "\n".join(text_parts)

    def parse(self) -> Invoice | AuditReport:
        self.validate_extension()
        text = self.extract_text()
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["invoice", "faktura", "invoys"]):
            return self._parse_as_invoice(text)
        elif any(kw in text_lower for kw in ["audit", "hesabat", "report"]):
            return self._parse_as_audit_report(text)
        else:
            return self._parse_as_invoice(text)

    def _parse_as_invoice(self, text: str) -> Invoice:
        doc_id = self._extract_pattern(text, r"(?:invoice|faktura)\s*[#]?\s*(\w+)", "INV-UNKNOWN")
        vendor = self._extract_pattern(text, r"(?:vendor|satici|from)[:\s]+([^\n]+)", "Namelum Satici")
        amount = self._extract_amount(text)
        due_date = self._extract_date(text, r"(?:due|son tarix)[:\s]+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})")

        return Invoice(
            doc_id=doc_id,
            title=f"Faktura {doc_id}",
            created_date=date.today(),
            doc_type=DocumentType.INVOICE,
            vendor_name=vendor.strip(),
            amount=amount,
            due_date=due_date or date.today(),
            status=InvoiceStatus.DRAFT,
            tags=["pdf-import"],
        )

    def _parse_as_audit_report(self, text: str) -> AuditReport:
        doc_id = self._extract_pattern(text, r"(?:report|hesabat)\s*[#]?\s*(\w+)", "AUD-UNKNOWN")
        auditor = self._extract_pattern(text, r"(?:auditor|mufettis)[:\s]+([^\n]+)", "Namelum Auditor")

        report = AuditReport(
            doc_id=doc_id,
            title=f"Audit Hesabati {doc_id}",
            created_date=date.today(),
            doc_type=DocumentType.AUDIT_REPORT,
            auditor_name=auditor.strip(),
            tags=["pdf-import"],
        )

        finding_matches = re.findall(
            r"(?:finding|tapinti)[:\s]+([^\n]+)", text, re.IGNORECASE
        )
        for i, desc in enumerate(finding_matches, 1):
            report.add_finding(
                finding_id=f"F-{i:03d}",
                description=desc.strip(),
                risk_level=RiskLevel.MEDIUM,
            )
        return report

    @staticmethod
    def _extract_pattern(text: str, pattern: str, default: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else default

    @staticmethod
    def _extract_amount(text: str) -> float:
        match = re.search(r"(?:total|cemi|meblegi)[:\s]*([0-9,. ]+)", text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "").replace(" ", "")
            try:
                return float(raw)
            except ValueError:
                pass
        return 0.0

    @staticmethod
    def _extract_date(text: str, pattern: str) -> date | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1)
            for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%y"):
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    continue
        return None
