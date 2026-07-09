"""
API Testleri - Gun 5 (son versiya)

Problem: TestClient lifespan-i her zaman isledir, real RAGPipeline + LLM yaradilir.
Heall: Test ucun mock lifespan ile tamamilə yeni FastAPI app yarat.
Bu yanaşma ile:
  - Hec bir model yuklenmir
  - ChromaDB-ye muraciet edilmir
  - OpenAI API cagrilmır
"""

from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

import src.api.routes as routes_module
from src.api.routes import router

MOCK_QUERY_RESULT = [
    {
        "id": "AUD-001",
        "text": "Audit Hesabati: Test\n  Auditor: Test\n  Umumi risk: HIGH",
        "metadata": {"doc_type": "audit_report", "title": "Test Audit"},
        "distance": 0.3,
    }
]


@pytest.fixture
def client():
    """
    Her test ucun:
      - _documents temizle
      - Mock pipeline ve llm ile yeni app yarat (real model yuklenmir)
      - TestClient-i mock lifespan ile islet
    """
    routes_module._documents.clear()

    mock_pipeline = MagicMock()
    mock_pipeline.document_count = 0
    mock_pipeline.query.return_value = MOCK_QUERY_RESULT

    mock_llm = MagicMock()
    mock_llm.model = "mock-model"
    mock_llm.answer.return_value = "Mock LLM cavabi"

    @asynccontextmanager
    async def mock_lifespan(app):
        # Real RAGPipeline ve LLMClient yox — birbasda mock
        app.state.pipeline = mock_pipeline
        app.state.llm = mock_llm
        yield

    app = FastAPI(title="Test App", lifespan=mock_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api/v1")

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, mock_pipeline

    routes_module._documents.clear()


class TestHealthEndpoint:
    def test_health_ok(self, client):
        c, pipeline = client
        pipeline.document_count = 2
        resp = c.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["document_count"] == 2


class TestDocumentEndpoints:
    def test_create_invoice_success(self, client):
        c, pipeline = client
        resp = c.post("/api/v1/documents/invoice", json={
            "doc_id": "INV-001",
            "title": "Test Faktura",
            "vendor_name": "TestCo",
            "amount": 1000.0,
            "due_date": "2026-12-31",
            "created_date": "2026-01-01",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["doc_id"] == "INV-001"
        assert data["doc_type"] == "invoice"
        pipeline.add.assert_called_once()

    def test_create_invoice_duplicate(self, client):
        c, _ = client
        body = {
            "doc_id": "INV-DUP",
            "title": "Duplicate Test",
            "vendor_name": "Co",
            "amount": 100.0,
            "due_date": "2026-12-31",
            "created_date": "2026-01-01",
        }
        c.post("/api/v1/documents/invoice", json=body)
        resp = c.post("/api/v1/documents/invoice", json=body)
        assert resp.status_code == 409

    def test_create_invoice_invalid_amount(self, client):
        c, _ = client
        resp = c.post("/api/v1/documents/invoice", json={
            "doc_id": "INV-BAD",
            "title": "Bad Invoice",
            "vendor_name": "Co",
            "amount": -50.0,
            "due_date": "2026-12-31",
            "created_date": "2026-01-01",
        })
        assert resp.status_code == 422

    def test_create_audit_success(self, client):
        c, pipeline = client
        resp = c.post("/api/v1/documents/audit", json={
            "doc_id": "AUD-001",
            "title": "Test Audit Hesabati",
            "auditor_name": "Leyla Hesenova",
            "audit_period_start": "2025-01-01",
            "audit_period_end": "2025-12-31",
            "created_date": "2026-01-01",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["doc_type"] == "audit_report"
        pipeline.add.assert_called_once()

    def test_list_documents_empty(self, client):
        c, _ = client
        resp = c.get("/api/v1/documents")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_documents_after_add(self, client):
        c, _ = client
        c.post("/api/v1/documents/invoice", json={
            "doc_id": "INV-LIST",
            "title": "List Test",
            "vendor_name": "Co",
            "amount": 500.0,
            "due_date": "2026-12-31",
            "created_date": "2026-01-01",
        })
        resp = c.get("/api/v1/documents")
        assert resp.json()["total"] == 1


class TestQueryEndpoint:
    def test_query_no_documents(self, client):
        c, pipeline = client
        pipeline.document_count = 0
        resp = c.post("/api/v1/query", json={"question": "bank problemi nedir?"})
        assert resp.status_code == 404

    def test_query_returns_answer(self, client):
        c, pipeline = client
        pipeline.document_count = 1
        resp = c.post("/api/v1/query", json={
            "question": "audit tapintisi nedir?",
            "n_results": 1,
            "use_llm": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["doc_id"] == "AUD-001"
        assert data["answer"] == "Mock LLM cavabi"

    def test_query_similarity_calculated(self, client):
        c, pipeline = client
        pipeline.document_count = 1
        resp = c.post("/api/v1/query", json={"question": "risk?"})
        data = resp.json()
        assert data["sources"][0]["similarity"] == 70.0

    def test_query_llm_called(self, client):
        c, pipeline = client
        pipeline.document_count = 1
        resp = c.post("/api/v1/query", json={
            "question": "risk tapintisi?",
            "use_llm": True,
        })
        assert resp.status_code == 200
        assert resp.json()["answer"] == "Mock LLM cavabi"
