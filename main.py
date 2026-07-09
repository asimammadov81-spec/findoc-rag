"""
main.py - FinDoc RAG Demo (Gun 3 + Gun 4)
"""

from datetime import date
from src.models.invoice import Invoice, InvoiceStatus
from src.models.audit_report import AuditReport, RiskLevel
from src.models.financial_document import DocumentType


def demo_invoice():
    print("=" * 50)
    print("DEMO: Invoice yaradilir")
    print("=" * 50)
    inv = Invoice(
        doc_id="INV-2026-001",
        title="IT Xidmetleri Fakturasi",
        created_date=date(2026, 1, 15),
        doc_type=DocumentType.INVOICE,
        vendor_name="TechSolutions MMC",
        currency="AZN",
        due_date=date(2026, 2, 15),
    )
    inv.add_line_item("Server icaresi", qty=1, unit_price=2500.0)
    inv.add_line_item("Texniki destek", qty=10, unit_price=150.0)
    inv.add_line_item("Lisenziya", qty=5, unit_price=200.0)
    inv.add_tag("IT")
    print(inv.summary())
    print(f"Validasiya: {inv.validate()}")
    return inv


def demo_audit_report():
    print("\n" + "=" * 50)
    print("DEMO: AuditReport yaradilir")
    print("=" * 50)
    report = AuditReport(
        doc_id="AUD-2026-Q1",
        title="2026 I Rub Maliyye Auditi",
        created_date=date(2026, 1, 1),
        doc_type=DocumentType.AUDIT_REPORT,
        auditor_name="Leyla Hesenova",
        audit_period_start=date(2025, 10, 1),
        audit_period_end=date(2025, 12, 31),
    )
    report.add_finding("F-001", "Bank uzlesdirmesi vaxtinda aparilmayib",
                       RiskLevel.HIGH, "Ayda bir defe uzlesdirme aparmaq")
    report.add_finding("F-002", "Kicik xercler ucun tesdiq yoxdur",
                       RiskLevel.MEDIUM)
    report.add_finding("F-003", "Inventar siyahisi yenilenmeyib",
                       RiskLevel.LOW)
    print(report.summary())
    print(f"Validasiya: {report.validate()}")
    return report


def demo_rag(invoice, audit_report):
    print("\n" + "=" * 50)
    print("DEMO: RAG Pipeline (Gun 4)")
    print("=" * 50)

    try:
        from src.rag.pipeline import RAGPipeline

        pipeline = RAGPipeline(persist_dir="./chroma_db")
        pipeline.reset()  # temiz bashla

        # Sened elave et
        pipeline.add_many([invoice, audit_report])
        print(f"Bazadaki sened sayi: {pipeline.document_count}")

        # Sorgu 1
        print("\n--- Sorgu 1: 'bank uzlesdirmesi problemi' ---")
        results = pipeline.query("bank uzlesdirmesi problemi", n_results=2)
        for r in results:
            print(f"  [{r['id']}] oxsarliq: {1 - r['distance']:.0%}")

        # Sorgu 2
        print("\n--- Sorgu 2: 'faktura meblegi satici' ---")
        results = pipeline.query("faktura meblegi satici", n_results=2)
        for r in results:
            print(f"  [{r['id']}] oxsarliq: {1 - r['distance']:.0%}")

        # Kontekst ile
        print("\n--- Kontekst ile sorgu ---")
        context = pipeline.query_with_context("risk tapintilari", n_results=1)
        print(context)

    except ImportError as e:
        print(f"RAG demo ucun: pip install chromadb sentence-transformers\n({e})")


if __name__ == "__main__":
    print("\nFinDoc RAG - Demo\n")
    inv = demo_invoice()
    rep = demo_audit_report()
    demo_rag(inv, rep)
    print("\n" + "=" * 50)
    print("Demo ugurla tamamlandi!")
    print("=" * 50)
