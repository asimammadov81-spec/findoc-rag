"""
routes.py - API endpoint-leri

FastAPI konseptleri:
  - APIRouter    : route qrupu
  - @router.post : POST endpoint
  - @router.get  : GET endpoint
  - Request      : app.state-e catmaq ucun
  - HTTPException: xeta cavabi (404, 422...)
  - Depends()    : dependency injection
"""

from datetime import date

from fastapi import APIRouter, HTTPException, Request

from src.models.audit_report import AuditReport
from src.models.financial_document import DocumentType
from src.models.invoice import Invoice, InvoiceStatus

from .schemas import (
    AuditReportCreateRequest,
    DocumentListResponse,
    DocumentResponse,
    InvoiceCreateRequest,
    QueryRequest,
    QueryResponse,
    SearchResult,
    StatusResponse,
)

router = APIRouter()

# Saxlanan senedler (sadə in-memory siyahı — Gun 6-da DB-ye kecilerek)
_documents: dict = {}


# ==========================================
# GET /health — sistem vəziyyəti
# ==========================================
@router.get("/health", response_model=StatusResponse)
async def health_check(request: Request):
    """API işlək olub olmadığını yoxla."""
    pipeline = request.app.state.pipeline
    return StatusResponse(
        status="ok",
        document_count=pipeline.document_count,
    )


# ==========================================
# POST /documents/invoice — faktura əlavə et
# ==========================================
@router.post("/documents/invoice", response_model=DocumentResponse, status_code=201)
async def create_invoice(body: InvoiceCreateRequest, request: Request):
    """
    Yeni faktura yarat ve RAG bazasina elave et.
    Body avtomatik Pydantic ile validasiya edilir.
    """
    if body.doc_id in _documents:
        raise HTTPException(status_code=409, detail=f"{body.doc_id} artiq movcuddur")

    invoice = Invoice(
        doc_id=body.doc_id,
        title=body.title,
        created_date=body.created_date,
        doc_type=DocumentType.INVOICE,
        vendor_name=body.vendor_name,
        amount=body.amount,
        currency=body.currency,
        due_date=body.due_date,
        tags=body.tags,
    )

    if not invoice.validate():
        raise HTTPException(status_code=422, detail="Faktura validasiyadan kecmedi")

    pipeline = request.app.state.pipeline
    pipeline.add(invoice)
    _documents[body.doc_id] = invoice

    return DocumentResponse(
        doc_id=invoice.doc_id,
        doc_type=invoice.doc_type.value,
        title=invoice.title,
        created_date=invoice.created_date,
        summary=invoice.summary(),
    )


# ==========================================
# POST /documents/audit — audit hesabatı əlavə et
# ==========================================
@router.post("/documents/audit", response_model=DocumentResponse, status_code=201)
async def create_audit_report(body: AuditReportCreateRequest, request: Request):
    """Yeni audit hesabati yarat ve RAG bazasina elave et."""
    if body.doc_id in _documents:
        raise HTTPException(status_code=409, detail=f"{body.doc_id} artiq movcuddur")

    report = AuditReport(
        doc_id=body.doc_id,
        title=body.title,
        created_date=body.created_date,
        doc_type=DocumentType.AUDIT_REPORT,
        auditor_name=body.auditor_name,
        audit_period_start=body.audit_period_start,
        audit_period_end=body.audit_period_end,
        tags=body.tags,
    )

    if not report.validate():
        raise HTTPException(status_code=422, detail="Audit hesabati validasiyadan kecmedi")

    pipeline = request.app.state.pipeline
    pipeline.add(report)
    _documents[body.doc_id] = report

    return DocumentResponse(
        doc_id=report.doc_id,
        doc_type=report.doc_type.value,
        title=report.title,
        created_date=report.created_date,
        summary=report.summary(),
    )


# ==========================================
# GET /documents — sənəd siyahısı
# ==========================================
@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """Bazadaki butun sənədleri qaytarır."""
    docs = [
        DocumentResponse(
            doc_id=doc.doc_id,
            doc_type=doc.doc_type.value,
            title=doc.title,
            created_date=doc.created_date,
            summary=doc.summary(),
        )
        for doc in _documents.values()
    ]
    return DocumentListResponse(total=len(docs), documents=docs)


# ==========================================
# POST /query — sual ver, cavab al
# ==========================================
@router.post("/query", response_model=QueryResponse)
async def query_documents(body: QueryRequest, request: Request):
    """
    RAG ile oxsar sened tap, LLM ile cavab generasiya et.

    Axin:
      1. question -> embedding
      2. ChromaDB-de oxsar sened axtar
      3. LLM-e kontekst + sual gonder
      4. Cavabi qaytir
    """
    pipeline = request.app.state.pipeline
    llm = request.app.state.llm

    if pipeline.document_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Bazada sened yoxdur. Evvel /documents/invoice ve ya /documents/audit-a POST edin."
        )

    # 1-2: RAG axtarisi
    results = pipeline.query(
        question=body.question,
        n_results=body.n_results,
        doc_type=body.doc_type,
    )

    if not results:
        raise HTTPException(status_code=404, detail="Uygun sened tapilmadi")

    # 3: Kontekst hazirla
    context = "\n\n".join(r["text"] for r in results)

    # 4: LLM cavabi
    if body.use_llm:
        answer = llm.answer(question=body.question, context=context)
    else:
        answer = context

    # Response formatla
    sources = [
        SearchResult(
            doc_id=r["id"],
            title=r["metadata"].get("title", r["id"]),
            doc_type=r["metadata"].get("doc_type", ""),
            similarity=round((1 - r["distance"]) * 100, 1),
            excerpt=r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
        )
        for r in results
    ]

    return QueryResponse(
        question=body.question,
        answer=answer,
        sources=sources,
        model_used=llm.model if body.use_llm else None,
    )
