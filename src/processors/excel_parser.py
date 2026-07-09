"""
ExcelParser - Excel (.xlsx) faylından Invoice cixarir
Kitabxana: openpyxl - pip install openpyxl
"""

from datetime import date

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from src.models.financial_document import DocumentType
from src.models.invoice import Invoice, InvoiceStatus

from .document_processor import DocumentProcessor, ProcessorError

COLUMN_MAP = {
    "sened id": "doc_id",
    "ad": "title",
    "satici": "vendor_name",
    "meblegi": "amount",
    "valyuta": "currency",
    "son tarix": "due_date",
    "status": "status",
    "invoice id": "doc_id",
    "title": "title",
    "vendor": "vendor_name",
    "amount": "amount",
    "currency": "currency",
    "due date": "due_date",
}


class ExcelParser(DocumentProcessor):
    """
    Excel faylından Invoice siyahisi oxuyur.

    Istifade:
        with ExcelParser("fakturalar.xlsx") as parser:
            invoices = parser.parse_all()
    """

    def supported_extensions(self) -> list[str]:
        return [".xlsx", ".xls"]

    def extract_text(self) -> str:
        rows = self._read_rows()
        return "\n".join(str(row) for row in rows)

    def parse(self) -> Invoice:
        invoices = self.parse_all()
        if not invoices:
            raise ProcessorError("Excel faylinda hec bir Invoice tapilmadi")
        return invoices[0]

    def parse_all(self) -> list[Invoice]:
        self.validate_extension()

        if not OPENPYXL_AVAILABLE:
            raise ProcessorError(
                "openpyxl qurashdirilmayib. "
                "Terminalda: pip install openpyxl"
            )

        rows = self._read_rows()
        if len(rows) < 2:
            raise ProcessorError("Excel faylinda bashliq + en az 1 data setri olmalidir")

        headers = [str(h).strip().lower() for h in rows[0]]
        invoices = []

        for row_idx, row in enumerate(rows[1:], start=2):
            try:
                invoice = self._row_to_invoice(headers, row, row_idx)
                invoices.append(invoice)
            except Exception as e:
                print(f"[ExcelParser] Setir {row_idx} atlandi: {e}")
                continue

        return invoices

    def _read_rows(self) -> list[tuple]:
        wb = openpyxl.load_workbook(str(self.file_path), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        return rows

    def _row_to_invoice(self, headers: list[str], row: tuple, row_idx: int) -> Invoice:
        data = {}
        for col_idx, header in enumerate(headers):
            field_name = COLUMN_MAP.get(header)
            if field_name and col_idx < len(row):
                data[field_name] = row[col_idx]

        doc_id = str(data.get("doc_id") or f"EXC-{row_idx:04d}")
        title = str(data.get("title") or f"Excel Invoice {doc_id}")
        vendor = str(data.get("vendor_name") or "Namelum")
        currency = str(data.get("currency") or "AZN")

        try:
            amount = float(data.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0

        raw_due = data.get("due_date")
        due_date = raw_due if isinstance(raw_due, date) else date.today()

        raw_status = str(data.get("status") or "draft").lower()
        status_map = {s.value: s for s in InvoiceStatus}
        status = status_map.get(raw_status, InvoiceStatus.DRAFT)

        return Invoice(
            doc_id=doc_id,
            title=title,
            created_date=date.today(),
            doc_type=DocumentType.INVOICE,
            vendor_name=vendor,
            amount=amount,
            currency=currency,
            due_date=due_date,
            status=status,
            tags=["excel-import"],
        )
