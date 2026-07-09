# FinDoc RAG — Layihə Tərəqqisi

## Layihə yeri
```
C:\Users\asima\PycharmProjects\PythonProject~\Projects\findoc_rag
```

## Virtual Environment
PyCharm terminalında `(.venv)` görünməlidir — aktivdir.

---

## Tamamlanan Günlər

### Gun 1 + Gun 2 — OOP + Fayl Parserlər ✅
```
src/models/financial_document.py   — ABC, Summarizable Protocol
src/models/invoice.py              — Invoice sinifi
src/models/audit_report.py         — AuditReport, AuditFinding
src/processors/document_processor.py
src/processors/pdf_parser.py
src/processors/excel_parser.py
tests/test_models.py               — 16 test PASSED
```

### Gun 3 — Docker ✅
```
Dockerfile, docker-compose.yml, .dockerignore, requirements.txt, main.py
```

### Gun 4 — RAG + ChromaDB ✅
```
src/rag/embedder.py, vector_store.py, pipeline.py
tests/test_rag.py
```
Demo: "risk tapintilari" → AUD-2026-Q1 (47% oxsarliq) ✅

### Gun 5 — FastAPI + GPT-4o-mini ✅
```
src/api/app.py, routes.py, schemas.py
src/llm/client.py
tests/test_api.py
```
Demo: Swagger UI-da real GPT-4o-mini cavabi alindi ✅
API: http://localhost:8000/docs

### Gun 6 — GitHub Actions CI/CD ✅
```
.github/workflows/ci.yml   — test + lint + docker build
pyproject.toml             — pytest + ruff konfiqurasiyasi
.gitignore                 — chroma_db, .venv, .env xaric
```
CI axini:
  1. Push/PR → GitHub Actions bashlayir
  2. 3 Python versiyasinda test (3.11, 3.12, 3.13)
  3. Ruff ile kod keyfiyyeti yoxlamasi
  4. Docker image qurulmasi

---

## Növbəti Addım — Gun 7: Tam İnteqrasiya + Demo

**Hədəf:** Hər seyi birlesdir, son demo hazirla

**Planlaşdırılan:**
- README.md — layihe tesviri, qurulum, istifade
- GitHub-a yukle (git init, commit, push)
- Son test — butun testler birlikde
- Demo skript — tam uc-uca axin

---

## Qurashdirilmish Kitabxanalar
```bash
pip install pymupdf openpyxl pytest chromadb sentence-transformers
pip install fastapi uvicorn pydantic openai httpx ruff
```

## Fayl Kopyalama Metodu
PowerShell Copy-Item komandasi ile (manuel copy-paste etme)
